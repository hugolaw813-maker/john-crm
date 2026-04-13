#!/usr/bin/env python3
"""
Populate Type field for existing Person records
Set all existing people as 'Client' (value: 'client')
"""

import psycopg2
import json
import uuid

PG_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
}

def populate():
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    # Get Person object in John's workspace
    john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'
    
    cur.execute('''
        SELECT o.id FROM objects o
        WHERE o.workspace_id = %s AND o.slug = 'people'
    ''', (john_ws_id,))
    
    person_id = cur.fetchone()[0]
    print(f'Person object ID: {person_id}')
    
    # Get Type attribute ID
    cur.execute('''
        SELECT id FROM attributes
        WHERE object_id = %s AND slug = 'type'
    ''', (person_id,))
    
    type_attr_id = cur.fetchone()[0]
    print(f'Type attribute ID: {type_attr_id}')
    
    # Get all person records
    cur.execute('''
        SELECT id FROM records
        WHERE object_id = %s
    ''', (person_id,))
    
    person_records = [row[0] for row in cur.fetchall()]
    print(f'Found {len(person_records)} person records')
    
    # Check which already have type value
    cur.execute('''
        SELECT rv.record_id
        FROM record_values rv
        WHERE rv.attribute_id = %s
    ''', (type_attr_id,))
    
    existing = [row[0] for row in cur.fetchall()]
    print(f'{len(existing)} records already have type value')
    
    # Set type = 'client' for all records missing it
    added = 0
    for record_id in person_records:
        if record_id not in existing:
            rv_id = str(uuid.uuid4())
            cur.execute('''
                INSERT INTO record_values (id, record_id, attribute_id, text_value)
                VALUES (%s, %s, %s, %s)
            ''', (rv_id, record_id, type_attr_id, 'client'))
            added += 1
    
    print(f'Added type="client" to {added} records')
    
    # Also do for My Workspace
    print('\n=== MY WORKSPACE ===')
    my_ws_id = '709eeba3-da92-46ff-aeec-3415c62c5fdf'
    
    cur.execute('''
        SELECT o.id FROM objects o
        WHERE o.workspace_id = %s AND o.slug = 'people'
    ''', (my_ws_id,))
    
    my_person_id = cur.fetchone()[0]
    
    cur.execute('''
        SELECT id FROM attributes
        WHERE object_id = %s AND slug = 'type'
    ''', (my_person_id,))
    
    my_type_attr_id = cur.fetchone()[0]
    
    cur.execute('''
        SELECT id FROM records
        WHERE object_id = %s
    ''', (my_person_id,))
    
    my_records = [row[0] for row in cur.fetchall()]
    print(f'My Workspace: {len(my_records)} person records')
    
    cur.execute('''
        SELECT rv.record_id
        FROM record_values rv
        WHERE rv.attribute_id = %s
    ''', (my_type_attr_id,))
    
    my_existing = [row[0] for row in cur.fetchall()]
    
    my_added = 0
    for record_id in my_records:
        if record_id not in my_existing:
            rv_id = str(uuid.uuid4())
            cur.execute('''
                INSERT INTO record_values (id, record_id, attribute_id, text_value)
                VALUES (%s, %s, %s, %s)
            ''', (rv_id, record_id, my_type_attr_id, 'client'))
            my_added += 1
    
    print(f'Added type="client" to {my_added} records in My Workspace')
    
    # Verify
    print('\n=== VERIFICATION ===')
    cur.execute('''
        SELECT COUNT(DISTINCT rv.record_id)
        FROM record_values rv
        WHERE rv.attribute_id = %s AND rv.text_value = 'client'
    ''', (type_attr_id,))
    
    john_count = cur.fetchone()[0]
    print(f'John\'s Workspace: {john_count} people set as Client')
    
    cur.execute('''
        SELECT COUNT(DISTINCT rv.record_id)
        FROM record_values rv
        WHERE rv.attribute_id = %s AND rv.text_value = 'client'
    ''', (my_type_attr_id,))
    
    my_count = cur.fetchone()[0]
    print(f'My Workspace: {my_count} people set as Client')
    
    # Show sample
    cur.execute('''
        SELECT r.id, rv.text_value as type, name_rv.json_value->>'full_name'
        FROM records r
        JOIN record_values rv ON r.id = rv.record_id AND rv.attribute_id = %s
        JOIN record_values name_rv ON r.id = name_rv.record_id
        JOIN attributes name_attr ON name_rv.attribute_id = name_attr.id
        WHERE r.object_id = %s AND name_attr.slug = 'name'
        LIMIT 5
    ''', (type_attr_id, person_id))
    
    print('\nSample records with type:')
    for rec_id, type_val, name in cur.fetchall():
        print(f'  {name}: {type_val}')
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f'\n✅ Total {added + my_added} type values added')
    print('All existing people set as Type = "Client"')

if __name__ == '__main__':
    populate()