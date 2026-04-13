#!/usr/bin/env python3
"""
Migrate SQLite tasks to PostgreSQL built‑in tasks table.
"""

import sqlite3
import psycopg2
import uuid
import json
from datetime import datetime

OLD_DB_PATH = '/home/jcw_l/.openclaw/workspace-sarah/secure-crm/data/crm.db'
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'jcw_l',
    'database': 'openclaw'
}

# IDs from earlier migration
WORKSPACE_ID = 'd96be209-824d-4e5f-9394-3c1dc45c75d0'
USER_ID = 'L20c4CHnqMpHB9EuAU6oBC67I99sMnLC'  # John

def connect_old():
    conn = sqlite3.connect(OLD_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def connect_new():
    return psycopg2.connect(**PG_CONFIG)

def get_name_mappings(pg_conn):
    """Build mapping from old household/client IDs to new record IDs by matching names."""
    pg_cur = pg_conn.cursor()
    
    # Map household name -> company record ID
    pg_cur.execute('''
        SELECT r.id, v.text_value
        FROM records r
        JOIN record_values v ON r.id = v.record_id
        WHERE r.object_id = (SELECT id FROM objects WHERE slug = 'companies')
          AND v.attribute_id = (SELECT id FROM attributes WHERE slug = 'name' AND object_id = r.object_id)
    ''')
    company_map = {}
    for rec_id, name in pg_cur.fetchall():
        company_map[name] = rec_id
    
    # Map client name -> person record ID (personal_name attribute)
    pg_cur.execute('''
        SELECT r.id, v.json_value->>'full_name' as full_name
        FROM records r
        JOIN record_values v ON r.id = v.record_id
        WHERE r.object_id = (SELECT id FROM objects WHERE slug = 'people')
          AND v.attribute_id = (SELECT id FROM attributes WHERE slug = 'name' AND object_id = r.object_id)
          AND v.json_value IS NOT NULL
    ''')
    person_map = {}
    for rec_id, full_name in pg_cur.fetchall():
        if full_name:
            person_map[full_name] = rec_id
    
    pg_cur.close()
    return company_map, person_map

def migrate():
    print("=== Migrating tasks to built‑in tasks table ===")
    old_conn = connect_old()
    pg_conn = connect_new()
    pg_cur = pg_conn.cursor()
    
    # Get name mappings
    company_map, person_map = get_name_mappings(pg_conn)
    print(f"  Loaded {len(company_map)} companies, {len(person_map)} people for linking")
    
    # Get all tasks from SQLite
    old_cur = old_conn.cursor()
    old_cur.execute('''
        SELECT id, household_id, client_id, title, description, priority, status, due_date,
               completed_date, assigned_to, created_at, updated_at
        FROM tasks
        ORDER BY id
    ''')
    tasks = old_cur.fetchall()
    print(f"  Found {len(tasks)} tasks in SQLite")
    
    migrated = 0
    linked = 0
    
    for task in tasks:
        task_id = str(uuid.uuid4())
        old_id = task['id']
        household_id = task['household_id']
        client_id = task['client_id']
        title = task['title']
        description = task['description'] or ''
        priority = task['priority'] or 'medium'
        status = task['status']
        due_date = task['due_date']
        completed_date = task['completed_date']
        assigned_to = task['assigned_to']
        created_at = task['created_at']
        updated_at = task['updated_at']
        
        # Determine is_completed and completed_at
        is_completed = status.lower() == 'completed'
        completed_at = None
        if is_completed and completed_date:
            try:
                completed_at = datetime.fromisoformat(completed_date.replace('Z', '+00:00'))
            except:
                pass
        
        # Parse due_date
        deadline = None
        if due_date:
            try:
                deadline = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            except:
                pass
        
        # Parse created_at
        try:
            created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00')) if created_at else datetime.now()
        except:
            created_dt = datetime.now()
        
        # Insert into tasks table
        pg_cur.execute('''
            INSERT INTO tasks (id, content, source_note_id, deadline, priority, is_completed,
                               completed_at, workspace_id, created_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (task_id, title, None, deadline, priority, is_completed, completed_at,
              WORKSPACE_ID, USER_ID, created_dt))
        
        # Link to record(s)
        record_ids = []
        
        # Find company record by household_id
        if household_id:
            old_cur.execute('SELECT display_name FROM households WHERE id = ?', (household_id,))
            household = old_cur.fetchone()
            if household and household['display_name'] in company_map:
                record_ids.append(company_map[household['display_name']])
        
        # Find person record by client_id
        if client_id:
            old_cur.execute('SELECT first_name, last_name FROM clients WHERE id = ?', (client_id,))
            client = old_cur.fetchone()
            if client:
                full_name = f"{client['first_name']} {client['last_name']}".strip()
                if full_name in person_map:
                    record_ids.append(person_map[full_name])
        
        # Insert task_records links
        for rec_id in record_ids:
            pg_cur.execute('INSERT INTO task_records (task_id, record_id) VALUES (%s, %s) ON CONFLICT DO NOTHING',
                          (task_id, rec_id))
            linked += 1
        
        # Assign task to user (if assigned_to matches John)
        # For now assign to the workspace admin (USER_ID)
        pg_cur.execute('INSERT INTO task_assignees (task_id, user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING',
                      (task_id, USER_ID))
        
        migrated += 1
        if migrated % 5 == 0:
            print(f"  Migrated {migrated}/{len(tasks)} tasks")
    
    pg_conn.commit()
    pg_cur.close()
    pg_conn.close()
    old_conn.close()
    
    print(f"✅ Migrated {migrated} tasks to built‑in tasks table")
    print(f"   Created {linked} task‑record links")
    print(f"🌐 Tasks will appear in the Tasks page at http://172.31.153.173:3001/tasks")

if __name__ == '__main__':
    migrate()