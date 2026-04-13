#!/usr/bin/env python3
"""
Check how deals are linked to people via associated_people
"""

import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    user='jcw_l',
    database='openclaw'
)
cur = conn.cursor()

john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'

print('=== DEAL-PERSON RELATIONSHIPS ===')

# Get deals object
cur.execute('''
    SELECT o.id
    FROM objects o
    WHERE o.workspace_id = %s AND o.slug = 'deals'
''', (john_ws_id,))
deals_obj_id = cur.fetchone()[0]

# Get associated_people attribute
cur.execute('''
    SELECT id FROM attributes
    WHERE object_id = %s AND slug = 'associated_people'
''', (deals_obj_id,))
associated_people_attr_id = cur.fetchone()[0]

print(f'Deals object ID: {deals_obj_id}')
print(f'Associated people attribute ID: {associated_people_attr_id}')

# Get all deals with their associated people
cur.execute('''
    SELECT rv.record_id as deal_id, rv.record_reference_value as person_id
    FROM record_values rv
    WHERE rv.attribute_id = %s AND rv.record_reference_value IS NOT NULL
''', (associated_people_attr_id,))

deal_person_links = cur.fetchall()
print(f'\nFound {len(deal_person_links)} deal-person links')

# Group by deal
from collections import defaultdict
deals_to_people = defaultdict(list)
people_to_deals = defaultdict(list)

for deal_id, person_id in deal_person_links:
    deals_to_people[deal_id].append(person_id)
    people_to_deals[person_id].append(deal_id)

print(f'\nDeals with linked people: {len(deals_to_people)}')
for deal_id, person_ids in list(deals_to_people.items())[:5]:
    print(f'Deal {deal_id}: {len(person_ids)} people')

# Get person names for sample
print('\nSample person details:')
for person_id in list(people_to_deals.keys())[:5]:
    # Get person name
    cur2 = conn.cursor()
    cur2.execute('''
        SELECT json_value->>'full_name'
        FROM record_values rv
        JOIN attributes a ON rv.attribute_id = a.id
        JOIN records r ON rv.record_id = r.id
        JOIN objects o ON r.object_id = o.id
        WHERE r.id = %s AND a.slug = 'name' AND o.slug = 'people'
    ''', (person_id,))
    
    name_result = cur2.fetchone()
    name = name_result[0] if name_result else 'Unknown'
    
    deal_count = len(people_to_deals[person_id])
    print(f'Person {person_id}: {name} (linked to {deal_count} deals)')
    cur2.close()

# Now check which tasks correspond to which deals
# We need to map deal records to tasks
print('\n=== TASK-DEAL MAPPING ===')
# Tasks were created from deal records. Need to find mapping.
# Look at task content vs deal name

# Get all deals with names
cur.execute('''
    SELECT r.id, rv.text_value
    FROM records r
    JOIN record_values rv ON r.id = rv.record_id
    JOIN attributes a ON rv.attribute_id = a.id
    WHERE r.object_id = %s AND a.slug = 'name'
''', (deals_obj_id,))

deal_names = {deal_id: name for deal_id, name in cur.fetchall()}
print(f'Deals with names: {len(deal_names)}')

# Get all tasks
cur.execute('''
    SELECT id, content
    FROM tasks
    ORDER BY created_at
''')

task_names = {task_id: content for task_id, content in cur.fetchall()}
print(f'Tasks: {len(task_names)}')

# Try to match by name
print('\nTrying to match tasks to deals by name:')
matches = []
for task_id, task_content in task_names.items():
    for deal_id, deal_name in deal_names.items():
        if deal_name and deal_name in task_content:
            matches.append((task_id, deal_id, task_content, deal_name))
            print(f'  Task "{task_content[:30]}..." → Deal "{deal_name}"')
            break

print(f'\nFound {len(matches)} matches')

cur.close()
conn.close()

print('\n=== PLAN ===')
print('1. Use deal-person links to find which people are associated with each deal')
print('2. Use task-deal name matching to map tasks to deals')
print('3. Create task_records entries linking tasks to people')
print('4. Also need to check notes and conversations')