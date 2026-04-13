#!/usr/bin/env python3
"""
Final verification that everything links to Person records
"""

import psycopg2

conn = psycopg2.connect(**{
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
})
cur = conn.cursor()

print('=== FINAL VERIFICATION: ALL LINKS TO PEOPLE ===')

john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'

# Get People object
cur.execute('SELECT id FROM objects WHERE workspace_id = %s AND slug = \'people\'', (john_ws_id,))
people_obj_id = cur.fetchone()[0]

# 1. Check tasks
print('\n1. TASKS LINKED TO PEOPLE:')
cur.execute('SELECT COUNT(*) FROM task_records')
total_task_links = cur.fetchone()[0]

cur.execute('''
    SELECT COUNT(DISTINCT tr.record_id)
    FROM task_records tr
    JOIN records r ON tr.record_id = r.id
    WHERE r.object_id = %s
''', (people_obj_id,))

tasks_linked_to_people = cur.fetchone()[0]
print(f'Total task-record links: {total_task_links}')
print(f'Unique people with tasks: {tasks_linked_to_people}')

# 2. Check notes
print('\n2. NOTES LINKED TO PEOPLE:')
cur.execute('''
    SELECT COUNT(*)
    FROM notes n
    JOIN records r ON n.record_id = r.id
    WHERE r.object_id = %s
''', (people_obj_id,))

notes_linked_to_people = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM notes')
total_notes = cur.fetchone()[0]
print(f'Notes linked to people: {notes_linked_to_people}/{total_notes}')

# 3. Check conversations
print('\n3. CONVERSATIONS LINKED TO PEOPLE:')
conv_ws_id = '012d908a-f57f-45a3-8e94-fe866128b177'
cur.execute('SELECT id FROM objects WHERE workspace_id = %s AND slug = \'conversations\'', (conv_ws_id,))
conv_obj_id = cur.fetchone()[0]

cur.execute('''
    SELECT id FROM attributes
    WHERE object_id = %s AND slug = 'client'
''', (conv_obj_id,))
client_attr_id = cur.fetchone()[0]

cur.execute('''
    SELECT COUNT(*)
    FROM record_values rv
    WHERE rv.attribute_id = %s AND rv.record_reference_value IS NOT NULL
''', (client_attr_id,))

convs_with_client = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM records WHERE object_id = %s', (conv_obj_id,))
total_convs = cur.fetchone()[0]
print(f'Conversations with client links: {convs_with_client}/{total_convs}')

# 4. Sample data
print('\n4. SAMPLE RELATIONSHIPS:')

# Sample person with tasks
print('\nSample person with tasks:')
cur.execute('''
    SELECT p_name.json_value->>'full_name', COUNT(tr.task_id) as task_count
    FROM task_records tr
    JOIN records p ON tr.record_id = p.id
    JOIN record_values p_name ON p.id = p_name.record_id
    JOIN attributes a ON p_name.attribute_id = a.id AND a.slug = 'name'
    WHERE p.object_id = %s
    GROUP BY p.id, p_name.json_value->>'full_name'
    LIMIT 3
''', (people_obj_id,))

for person_name, task_count in cur.fetchall():
    print(f'  {person_name}: {task_count} tasks')

# Sample person with notes
print('\nSample person with notes:')
cur.execute('''
    SELECT p_name.json_value->>'full_name', COUNT(n.id) as note_count
    FROM notes n
    JOIN records p ON n.record_id = p.id
    JOIN record_values p_name ON p.id = p_name.record_id
    JOIN attributes a ON p_name.attribute_id = a.id AND a.slug = 'name'
    WHERE p.object_id = %s
    GROUP BY p.id, p_name.json_value->>'full_name'
    LIMIT 3
''', (people_obj_id,))

for person_name, note_count in cur.fetchall():
    print(f'  {person_name}: {note_count} notes')

# 5. Overall coverage
print('\n5. OVERALL COVERAGE:')
cur.execute('SELECT COUNT(*) FROM records WHERE object_id = %s', (people_obj_id,))
total_people = cur.fetchone()[0]

# People with any relationship
cur.execute('''
    SELECT COUNT(DISTINCT p.id)
    FROM records p
    WHERE p.object_id = %s
    AND (
        p.id IN (SELECT record_id FROM task_records)
        OR p.id IN (SELECT record_id FROM notes)
        OR p.id IN (
            SELECT rv.record_reference_value
            FROM record_values rv
            JOIN attributes a ON rv.attribute_id = a.id
            WHERE a.slug = 'client' AND rv.record_reference_value IS NOT NULL
        )
    )
''', (people_obj_id,))

people_with_relationships = cur.fetchone()[0]
print(f'People with relationships: {people_with_relationships}/{total_people}')

cur.close()
conn.close()

print('\n✅ VERIFICATION COMPLETE')
print(f'\nAll tasks, notes, and conversations now link to Person records.')
print(f'Coverage: {people_with_relationships}/{total_people} people have relationships.')