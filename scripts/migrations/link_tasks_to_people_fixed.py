#!/usr/bin/env python3
"""
Properly link tasks to people using correct schema
"""

import psycopg2
import uuid

conn = psycopg2.connect(**{
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
})
cur = conn.cursor()

print('=== LINKING TASKS TO PEOPLE (FIXED) ===')

john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'

# Get People object
cur.execute('SELECT id FROM objects WHERE workspace_id = %s AND slug = \'people\'', (john_ws_id,))
people_obj_id = cur.fetchone()[0]

# Get Deals object and associated_people attribute
cur.execute('SELECT id FROM objects WHERE workspace_id = %s AND slug = \'deals\'', (john_ws_id,))
deals_obj_id = cur.fetchone()[0]

cur.execute('SELECT id FROM attributes WHERE object_id = %s AND slug = \'associated_people\'', (deals_obj_id,))
associated_people_attr_id = cur.fetchone()[0]

print(f'People object ID: {people_obj_id}')
print(f'Deals object ID: {deals_obj_id}')
print(f'Associated people attribute ID: {associated_people_attr_id}')

# Get deal-person links from record_values.referenced_record_id
cur.execute('''
    SELECT rv.record_id as deal_id, rv.referenced_record_id as person_id
    FROM record_values rv
    WHERE rv.attribute_id = %s AND rv.referenced_record_id IS NOT NULL
''', (associated_people_attr_id,))

deal_person_links = cur.fetchall()
print(f'\nFound {len(deal_person_links)} deal-person links')

# Get deal names
cur.execute('''
    SELECT r.id, rv.text_value
    FROM records r
    JOIN record_values rv ON r.id = rv.record_id
    JOIN attributes a ON rv.attribute_id = a.id
    WHERE r.object_id = %s AND a.slug = 'name'
''', (deals_obj_id,))

deal_names = {deal_id: name for deal_id, name in cur.fetchall()}
print(f'Deals with names: {len(deal_names)}')

# Get tasks
cur.execute('SELECT id, content FROM tasks ORDER BY created_at')
tasks = {task_id: content for task_id, content in cur.fetchall()}
print(f'Tasks: {len(tasks)}')

# Match tasks to deals by name
task_deal_matches = []
for task_id, task_content in tasks.items():
    for deal_id, deal_name in deal_names.items():
        if deal_name and deal_name in task_content:
            task_deal_matches.append((task_id, deal_id, deal_name))
            print(f'  Matched: "{task_content[:30]}..." → "{deal_name}"')
            break

print(f'\nMatched {len(task_deal_matches)} tasks to deals')

# Create task_records entries
task_records_created = 0
for task_id, deal_id, deal_name in task_deal_matches:
    # Find people linked to this deal
    person_ids = [pid for did, pid in deal_person_links if did == deal_id]
    
    for person_id in person_ids:
        # Check if link already exists
        cur.execute('SELECT COUNT(*) FROM task_records WHERE task_id = %s AND record_id = %s', (task_id, person_id))
        
        if cur.fetchone()[0] == 0:
            # Create new link
            # task_records has only task_id and record_id columns (no id column)
            try:
                cur.execute('INSERT INTO task_records (task_id, record_id) VALUES (%s, %s)', (task_id, person_id))
                
                # Get person name for logging
                cur2 = conn.cursor()
                cur2.execute('''
                    SELECT json_value->>'full_name'
                    FROM record_values rv
                    JOIN attributes a ON rv.attribute_id = a.id
                    WHERE rv.record_id = %s AND a.slug = 'name'
                ''', (person_id,))
                person_name = cur2.fetchone()
                person_name = person_name[0] if person_name else 'Unknown'
                cur2.close()
                
                print(f'  Linked task "{deal_name[:30]}..." → person "{person_name}"')
                task_records_created += 1
            except Exception as e:
                print(f'  Error linking {task_id} to {person_id}: {e}')
        else:
            print(f'  Link already exists for task {task_id} to person {person_id}')

print(f'\nCreated {task_records_created} task-person links')

# Verify
cur.execute('SELECT COUNT(*) FROM task_records')
total_links = cur.fetchone()[0]
print(f'Total task_records now: {total_links}')

if total_links > 0:
    print('\nSample task-person links:')
    cur.execute('''
        SELECT tr.task_id, tr.record_id, t.content, p_name.json_value->>'full_name'
        FROM task_records tr
        JOIN tasks t ON tr.task_id = t.id
        LEFT JOIN record_values p_name ON tr.record_id = p_name.record_id
        LEFT JOIN attributes a ON p_name.attribute_id = a.id AND a.slug = 'name'
        LIMIT 3
    ''')
    
    for task_id, person_id, task_content, person_name in cur.fetchall():
        print(f'  Task: {task_content[:30]}...')
        print(f'    Person: {person_name}')

conn.commit()
cur.close()
conn.close()

print('\n✅ Task-person links created successfully')
print('\nNow need to check if UI displays these links.')
print('The built-in Tasks UI may need modification to show associated people.')