#!/usr/bin/env python3
"""
Verify task-person links and check if UI would display them
"""

import psycopg2

conn = psycopg2.connect(**{
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
})
cur = conn.cursor()

print('=== VERIFYING TASK-PERSON LINKS ===')

# 1. Check task_records
cur.execute('SELECT COUNT(*) FROM task_records')
total_links = cur.fetchone()[0]
print(f'Total task_records: {total_links}')

# Get sample with details
cur.execute('''
    SELECT tr.task_id, tr.record_id, t.content
    FROM task_records tr
    JOIN tasks t ON tr.task_id = t.id
    LIMIT 5
''')

print('\nSample task_records:')
for task_id, record_id, content in cur.fetchall():
    print(f'  Task: {content[:40]}...')
    print(f'    Record ID: {record_id}')

# 2. Verify records exist and are People records
cur.execute('''
    SELECT tr.record_id, o.slug, o.singular_name
    FROM task_records tr
    JOIN records r ON tr.record_id = r.id
    JOIN objects o ON r.object_id = o.id
    LIMIT 5
''')

print('\nRecord types:')
for record_id, slug, singular in cur.fetchall():
    print(f'  {record_id}: {singular} (slug: {slug})')

# 3. Check if records have name values
cur.execute('''
    SELECT DISTINCT tr.record_id, rv.text_value, rv.json_value
    FROM task_records tr
    LEFT JOIN record_values rv ON tr.record_id = rv.record_id
    LEFT JOIN attributes a ON rv.attribute_id = a.id AND a.slug = 'name'
    WHERE rv.record_id IS NOT NULL
    LIMIT 5
''')

print('\nRecord name values:')
for record_id, text_val, json_val in cur.fetchall():
    print(f'  {record_id}: text={text_val}, json={json_val}')

# 4. Check deal-person associations to see distribution
john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'
cur.execute('SELECT id FROM objects WHERE workspace_id = %s AND slug = \'deals\'', (john_ws_id,))
deals_obj_id = cur.fetchone()[0]

cur.execute('SELECT id FROM attributes WHERE object_id = %s AND slug = \'associated_people\'', (deals_obj_id,))
associated_people_attr_id = cur.fetchone()[0]

cur.execute('''
    SELECT rv.record_id as deal_id, rv.referenced_record_id as person_id
    FROM record_values rv
    WHERE rv.attribute_id = %s AND rv.referenced_record_id IS NOT NULL
''', (associated_people_attr_id,))

deal_person_links = cur.fetchall()
print(f'\nDeal-person links: {len(deal_person_links)}')

# Count unique people
people_ids = set(pid for _, pid in deal_person_links)
print(f'Unique people in deals: {len(people_ids)}')

# Get person names
for person_id in list(people_ids)[:5]:
    cur.execute('''
        SELECT json_value->>'full_name'
        FROM record_values rv
        JOIN attributes a ON rv.attribute_id = a.id
        WHERE rv.record_id = %s AND a.slug = 'name'
    ''', (person_id,))
    name = cur.fetchone()
    name = name[0] if name else 'Unknown'
    print(f'  {person_id}: {name}')

# 5. Check if tasks API would return linkedRecords
# Simulate the enrichTasks logic: get all task_records for our tasks
cur.execute('SELECT id FROM tasks LIMIT 3')
task_ids = [row[0] for row in cur.fetchall()]
if task_ids:
    placeholders = ','.join(['%s'] * len(task_ids))
    cur.execute(f'''
        SELECT tr.task_id, tr.record_id
        FROM task_records tr
        WHERE tr.task_id IN ({placeholders})
    ''', task_ids)
    
    print(f'\nTask_records for first 3 tasks:')
    for task_id, record_id in cur.fetchall():
        print(f'  Task {task_id}: record {record_id}')

# 6. Check workspace consistency
print('\nWorkspace check:')
cur.execute('SELECT DISTINCT workspace_id FROM tasks')
workspace_ids = [row[0] for row in cur.fetchall()]
print(f'Task workspaces: {workspace_ids}')

cur.execute('SELECT id, name FROM workspaces WHERE id = ANY(%s)', (workspace_ids,))
for ws_id, ws_name in cur.fetchall():
    print(f'  {ws_id}: {ws_name}')

cur.close()
conn.close()

print('\n=== ANALYSIS ===')
print('If task_records exist and records have names, UI should show linked records.')
print('Check the Tasks page in CRM to see if "Record" column shows person names.')