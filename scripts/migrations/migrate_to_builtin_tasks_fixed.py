#!/usr/bin/env python3
"""
Migrate 11 deal records to built-in tasks table (fixed)
"""

import psycopg2
import json
import uuid
from datetime import datetime

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    user='jcw_l',
    database='openclaw'
)
cur = conn.cursor()

print('=== MIGRATING DEALS TO BUILT-IN TASKS ===')

john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'
my_ws_id = '709eeba3-da92-46ff-aeec-3415c62c5fdf'

# Get deals object and attributes (John's workspace)
cur.execute('''
    SELECT o.id
    FROM objects o
    WHERE o.workspace_id = %s AND o.slug = 'deals'
''', (john_ws_id,))

deals_obj_id = cur.fetchone()[0]

# Get attribute IDs
cur.execute('''
    SELECT slug, id FROM attributes
    WHERE object_id = %s AND slug IN ('name', 'stage', 'expected_close_date')
''', (deals_obj_id,))

attrs = {slug: attr_id for slug, attr_id in cur.fetchall()}
print(f'Attribute IDs: {attrs}')

# Get status mappings
stage_attr_id = attrs['stage']
cur.execute('SELECT id, title FROM statuses WHERE attribute_id = %s', (stage_attr_id,))
status_map = {status_id: title for status_id, title in cur.fetchall()}
print(f'Status map: {status_map}')

# Get current user (John) - first user in users table
cur.execute('SELECT id FROM users ORDER BY created_at LIMIT 1')
user_id = cur.fetchone()[0]
print(f'Current user ID: {user_id}')

# Get all deal records
cur.execute('''
    SELECT r.id, r.created_at
    FROM records r
    WHERE r.object_id = %s
    ORDER BY r.created_at
''', (deals_obj_id,))

deal_records = cur.fetchall()
print(f'Found {len(deal_records)} deal records')

# Migrate each record
migrated = 0
for deal_record_id, created_at in deal_records:
    print(f'\nProcessing deal record {deal_record_id}')
    
    # Get values for this record
    values = {}
    for slug, attr_id in attrs.items():
        cur.execute('''
            SELECT text_value, number_value, json_value, date_value, record_id as ref_id
            FROM record_values
            WHERE record_id = %s AND attribute_id = %s
        ''', (deal_record_id, attr_id))
        
        result = cur.fetchone()
        if result:
            text_val, num_val, json_val, date_val, ref_id = result
            if text_val is not None:
                values[slug] = text_val
            elif date_val is not None:
                values[slug] = date_val
            elif ref_id is not None:
                values[slug] = ref_id
    
    print(f'  Values: {values}')
    
    # Prepare task data
    content = values.get('name', 'Unnamed task')
    
    # Determine if completed
    is_completed = False
    completed_at = None
    stage_guid = values.get('stage')
    if stage_guid and stage_guid in status_map:
        status_title = status_map[stage_guid]
        if status_title == 'Won':
            is_completed = True
            completed_at = created_at
    
    deadline = values.get('expected_close_date')
    
    # Create task ID
    task_id = str(uuid.uuid4())
    
    # Insert into tasks table
    try:
        cur.execute('''
            INSERT INTO tasks (id, content, deadline, is_completed, completed_at, workspace_id, created_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            task_id,
            content,
            deadline,
            is_completed,
            completed_at,
            john_ws_id,  # workspace_id
            user_id,
            created_at
        ))
        
        print(f'  Created task: "{content[:50]}..."')
        print(f'    Completed: {is_completed}, Deadline: {deadline}')
        
        migrated += 1
    except Exception as e:
        print(f'  ERROR creating task: {e}')

# Also check My Workspace (should be empty or same data)
print('\n=== CHECKING MY WORKSPACE ===')
cur.execute('SELECT COUNT(*) FROM records WHERE object_id = (SELECT id FROM objects WHERE workspace_id = %s AND slug = \'deals\')', (my_ws_id,))
my_count = cur.fetchone()[0]
print(f'My Workspace has {my_count} deal records')

conn.commit()
cur.close()
conn.close()

print(f'\n✅ Migrated {migrated} records to built-in tasks table')
print(f'\nTasks table now has:')
cur2 = conn.cursor()
cur2.execute('SELECT COUNT(*) FROM tasks')
total_tasks = cur2.fetchone()[0]
cur2.execute('SELECT COUNT(*) FROM tasks WHERE is_completed = true')
completed_tasks = cur2.fetchone()[0]
cur2.close()

print(f'  Total tasks: {total_tasks}')
print(f'  Completed: {completed_tasks}')
print(f'  Pending: {total_tasks - completed_tasks}')

print('\nNext:')
print('1. Deal records still exist in "Deals" object (11 records)')
print('2. Tasks are now in built-in Tasks system (top sidebar)')
print('3. You can delete the "Deals" records if desired')