#!/usr/bin/env python3
"""
Link tasks, notes, and conversations to Person records
"""

import psycopg2
import uuid

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    user='jcw_l',
    database='openclaw'
)
cur = conn.cursor()

print('=== LINKING EVERYTHING TO PEOPLE ===')

john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'

# ===== 1. LINK TASKS TO PEOPLE =====
print('\n1. LINKING TASKS TO PEOPLE')

# Get Person object in John's workspace
cur.execute('''
    SELECT o.id
    FROM objects o
    WHERE o.workspace_id = %s AND o.slug = 'people'
''', (john_ws_id,))
people_obj_id = cur.fetchone()[0]
print(f'People object ID: {people_obj_id}')

# Get Deals object and associated_people attribute
cur.execute('''
    SELECT o.id
    FROM objects o
    WHERE o.workspace_id = %s AND o.slug = 'deals'
''', (john_ws_id,))
deals_obj_id = cur.fetchone()[0]

cur.execute('''
    SELECT id FROM attributes
    WHERE object_id = %s AND slug = 'associated_people'
''', (deals_obj_id,))
associated_people_attr_id = cur.fetchone()[0]

# Get deal-person links
cur.execute('''
    SELECT rv.record_id as deal_id, rv.record_reference_value as person_id
    FROM record_values rv
    WHERE rv.attribute_id = %s AND rv.record_reference_value IS NOT NULL
''', (associated_people_attr_id,))

deal_person_links = cur.fetchall()
print(f'Found {len(deal_person_links)} deal-person links')

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
            break

print(f'Matched {len(task_deal_matches)} tasks to deals')

# Create task_records entries for each task-person link
task_records_created = 0
for task_id, deal_id, deal_name in task_deal_matches:
    # Find people linked to this deal
    person_ids = [pid for did, pid in deal_person_links if did == deal_id]
    
    for person_id in person_ids:
        # Check if link already exists
        cur.execute('''
            SELECT COUNT(*) FROM task_records
            WHERE task_id = %s AND record_id = %s
        ''', (task_id, person_id))
        
        if cur.fetchone()[0] == 0:
            # Create new link
            tr_id = str(uuid.uuid4())
            cur.execute('''
                INSERT INTO task_records (id, task_id, record_id, created_at)
                VALUES (%s, %s, %s, NOW())
            ''', (tr_id, task_id, person_id))
            task_records_created += 1
            
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

print(f'Created {task_records_created} task-person links')

# ===== 2. CHECK NOTES LINK TO PEOPLE =====
print('\n2. CHECKING NOTES LINK TO PEOPLE')

# Check which objects notes are linked to
cur.execute('''
    SELECT o.singular_name, COUNT(*) as count
    FROM notes n
    JOIN records r ON n.record_id = r.id
    JOIN objects o ON r.object_id = o.id
    GROUP BY o.singular_name
    ORDER BY count DESC
''')

print('Notes linked to objects:')
for object_type, count in cur.fetchall():
    print(f'  {object_type}: {count} notes')

# Count notes linked to People vs Companies
cur.execute('''
    SELECT 
        SUM(CASE WHEN o.slug = 'people' THEN 1 ELSE 0 END) as people_notes,
        SUM(CASE WHEN o.slug = 'companies' THEN 1 ELSE 0 END) as company_notes
    FROM notes n
    JOIN records r ON n.record_id = r.id
    JOIN objects o ON r.object_id = o.id
    WHERE o.workspace_id = %s
''', (john_ws_id,))

people_notes, company_notes = cur.fetchone()
print(f'\nNotes linked to People: {people_notes or 0}')
print(f'Notes linked to Companies: {company_notes or 0}')

# If notes are linked to companies (households), we might want to link them to primary person
# For now, just note the status

# ===== 3. CHECK CONVERSATIONS LINK TO PEOPLE =====
print('\n3. CHECKING CONVERSATIONS LINK TO PEOPLE')

conv_ws_id = '012d908a-f57f-45a3-8e94-fe866128b177'

# Get Conversation object
cur.execute('''
    SELECT o.id
    FROM objects o
    WHERE o.workspace_id = %s AND o.slug = 'conversations'
''', (conv_ws_id,))
conv_obj_id = cur.fetchone()[0]

# Get client attribute (should link to Person)
cur.execute('''
    SELECT id, title FROM attributes
    WHERE object_id = %s AND slug = 'client'
''', (conv_obj_id,))

client_attr = cur.fetchone()
if client_attr:
    client_attr_id, client_title = client_attr
    print(f'Conversation client attribute: {client_title} (id: {client_attr_id})')
    
    # Count conversations with client links
    cur.execute('''
        SELECT COUNT(*)
        FROM record_values rv
        WHERE rv.attribute_id = %s AND rv.record_reference_value IS NOT NULL
    ''', (client_attr_id,))
    
    conv_with_client = cur.fetchone()[0]
    print(f'Conversations with client link: {conv_with_client}')
else:
    print('No client attribute found in Conversation object')

# ===== 4. SUMMARY =====
print('\n=== SUMMARY ===')
print(f'Task-person links created: {task_records_created}')
print(f'Notes linked to People: {people_notes or 0}')
print(f'Notes linked to Companies: {company_notes or 0}')

if company_notes and company_notes > 0:
    print('\n⚠️ Some notes are linked to Companies (households) instead of People.')
    print('  Should we link these to primary household members?')

conn.commit()
cur.close()
conn.close()

print('\n✅ Person relationships established')
print('\nNext: Check if notes linked to companies should be linked to primary person')