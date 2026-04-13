#!/usr/bin/env python3
"""
Fix CRM data issues:
- Set company type based on old household status/coworker flag
- Create team links (company -> people)
- Ensure all data consistent
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

WORKSPACE_ID = 'd96be209-824d-4e5f-9394-3c1dc45c75d0'
USER_ID = 'L20c4CHnqMpHB9EuAU6oBC67I99sMnLC'

def connect_old():
    conn = sqlite3.connect(OLD_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def connect_new():
    return psycopg2.connect(**PG_CONFIG)

def get_attribute_ids(pg_cur):
    """Fetch attribute IDs needed for fixes."""
    # Get object IDs
    pg_cur.execute("SELECT id FROM objects WHERE slug = 'companies'")
    companies_obj_id = pg_cur.fetchone()[0]
    pg_cur.execute("SELECT id FROM objects WHERE slug = 'people'")
    people_obj_id = pg_cur.fetchone()[0]
    
    # Attribute slugs we need
    attrs = {}
    pg_cur.execute('''
        SELECT slug, id, object_id 
        FROM attributes 
        WHERE object_id IN (%s, %s) 
          AND slug IN ('type', 'team', 'status', 'coworker')
    ''', (companies_obj_id, people_obj_id))
    for slug, attr_id, obj_id in pg_cur.fetchall():
        attrs[slug] = attr_id
        print(f'  {slug}: {attr_id}')
    
    # Also get company attribute on people (record_reference)
    pg_cur.execute('''
        SELECT id FROM attributes 
        WHERE object_id = %s AND slug = 'company'
    ''', (people_obj_id,))
    row = pg_cur.fetchone()
    if row:
        attrs['company'] = row[0]
    
    return attrs, companies_obj_id, people_obj_id

def get_old_household_data(old_cur):
    """Get old household status and coworker flags."""
    old_cur.execute('SELECT id, display_name, status, coworker FROM households')
    houses = {}
    for row in old_cur.fetchall():
        houses[row['id']] = dict(row)
    return houses

def get_mappings(pg_cur):
    """Build mapping from old household/client IDs to new record IDs."""
    # We'll do name-based mapping as before
    pg_cur.execute('''
        SELECT r.id, v.text_value as name
        FROM records r
        JOIN objects o ON r.object_id = o.id AND o.slug = 'companies'
        JOIN record_values v ON r.id = v.record_id
        JOIN attributes a ON v.attribute_id = a.id AND a.slug = 'name'
    ''')
    name_to_company = {row[1]: row[0] for row in pg_cur.fetchall()}
    
    pg_cur.execute('''
        SELECT r.id, v.json_value->>'full_name' as full_name
        FROM records r
        JOIN objects o ON r.object_id = o.id AND o.slug = 'people'
        JOIN record_values v ON r.id = v.record_id
        JOIN attributes a ON v.attribute_id = a.id AND a.slug = 'name'
        WHERE v.json_value IS NOT NULL
    ''')
    name_to_person = {}
    for row in pg_cur.fetchall():
        if row[1]:
            name_to_person[row[1]] = row[0]
    
    return name_to_company, name_to_person

def fix_company_types(pg_cur, old_cur, attrs, name_to_company, old_houses):
    """Set company type based on old household status/coworker."""
    if 'type' not in attrs:
        print('⚠️ No type attribute found')
        return
    
    type_attr_id = attrs['type']
    updates = 0
    
    for old_id, house in old_houses.items():
        if house['display_name'] not in name_to_company:
            continue
        company_id = name_to_company[house['display_name']]
        
        # Determine type
        company_type = 'client'  # default
        if house.get('coworker') == 1:
            company_type = 'coworker'
        elif house.get('status'):
            # Map old status to type
            status = house['status'].lower()
            if status in ('lead', 'prospect'):
                company_type = 'lead'
            elif status in ('active', 'current'):
                company_type = 'client'
            elif status in ('inactive', 'past'):
                company_type = 'past'
            else:
                company_type = status
        
        # Check if type already set
        pg_cur.execute('''
            SELECT id FROM record_values 
            WHERE record_id = %s AND attribute_id = %s
        ''', (company_id, type_attr_id))
        existing = pg_cur.fetchone()
        
        if existing:
            # Update existing
            pg_cur.execute('''
                UPDATE record_values 
                SET text_value = %s, updated_at = %s
                WHERE id = %s
            ''', (company_type, datetime.now(), existing[0]))
        else:
            # Insert new
            pg_cur.execute('''
                INSERT INTO record_values 
                (id, record_id, attribute_id, text_value, created_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (str(uuid.uuid4()), company_id, type_attr_id, company_type,
                  datetime.now(), USER_ID))
        
        updates += 1
        if updates % 10 == 0:
            print(f'  Updated {updates} company types')
    
    print(f'✅ Set type for {updates} companies')

def create_team_links(pg_cur, old_cur, attrs, name_to_company, name_to_person):
    """Create team links (company -> people) from client_households."""
    if 'team' not in attrs:
        print('⚠️ No team attribute found')
        return
    
    team_attr_id = attrs['team']
    
    # Get client-household relationships
    old_cur.execute('''
        SELECT client_id, household_id 
        FROM client_households
    ''')
    relations = old_cur.fetchall()
    print(f'Found {len(relations)} client-household relationships')
    
    # Get old client names
    old_cur.execute('SELECT id, first_name, last_name FROM clients')
    clients = {row['id']: f"{row['first_name']} {row['last_name']}".strip() for row in old_cur.fetchall()}
    
    links_created = 0
    
    for client_id, household_id in relations:
        # Find company record
        old_cur.execute('SELECT display_name FROM households WHERE id = ?', (household_id,))
        house_row = old_cur.fetchone()
        if not house_row:
            continue
        house_name = house_row['display_name']
        if house_name not in name_to_company:
            continue
        company_id = name_to_company[house_name]
        
        # Find person record
        client_name = clients.get(client_id)
        if not client_name or client_name not in name_to_person:
            continue
        person_id = name_to_person[client_name]
        
        # Check if team link already exists
        pg_cur.execute('''
            SELECT id FROM record_values 
            WHERE record_id = %s AND attribute_id = %s AND referenced_record_id = %s
        ''', (company_id, team_attr_id, person_id))
        existing = pg_cur.fetchone()
        
        if not existing:
            pg_cur.execute('''
                INSERT INTO record_values 
                (id, record_id, attribute_id, referenced_record_id, created_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (str(uuid.uuid4()), company_id, team_attr_id, person_id,
                  datetime.now(), USER_ID))
            links_created += 1
    
    print(f'✅ Created {links_created} team links')

def main():
    print("=== Fixing CRM data ===")
    
    old_conn = connect_old()
    pg_conn = connect_new()
    pg_cur = pg_conn.cursor()
    old_cur = old_conn.cursor()
    
    # Get IDs
    attrs, companies_obj_id, people_obj_id = get_attribute_ids(pg_cur)
    print(f'Companies object: {companies_obj_id}, People object: {people_obj_id}')
    
    # Get mappings
    name_to_company, name_to_person = get_mappings(pg_cur)
    print(f'Mapped {len(name_to_company)} companies, {len(name_to_person)} people')
    
    # Get old household data
    old_houses = get_old_household_data(old_cur)
    
    # 1. Fix company types
    fix_company_types(pg_cur, old_cur, attrs, name_to_company, old_houses)
    
    # 2. Create team links
    create_team_links(pg_cur, old_cur, attrs, name_to_company, name_to_person)
    
    # 3. Ensure coworker company has proper type (already covered)
    
    pg_conn.commit()
    pg_cur.close()
    pg_conn.close()
    old_conn.close()
    
    print("✅ Fixes completed")

if __name__ == '__main__':
    main()