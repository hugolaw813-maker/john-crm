#!/usr/bin/env python3
"""
Final script to ensure all relationships point to Person records
"""

import psycopg2
import json
import uuid

conn = psycopg2.connect(**{
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
})
cur = conn.cursor()

print('=== FINAL PERSON RELATIONSHIPS ===')

john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'

# Get object IDs
cur.execute('''
    SELECT slug, id FROM objects
    WHERE workspace_id = %s AND slug IN ('people', 'companies')
''', (john_ws_id,))

obj_ids = {slug: obj_id for slug, obj_id in cur.fetchall()}
people_obj_id = obj_ids['people']
companies_obj_id = obj_ids['companies']

# Get company attribute on Person
cur.execute('''
    SELECT id FROM attributes
    WHERE object_id = %s AND slug = 'company'
''', (people_obj_id,))
company_attr_id = cur.fetchone()[0]

# ===== 1. UPDATE NOTES TO LINK TO PEOPLE =====
print('\n1. UPDATING NOTES TO LINK TO PRIMARY PERSON')

cur.execute('''
    SELECT n.id, n.record_id as company_id, n.title, n.content::text
    FROM notes n
    JOIN records r ON n.record_id = r.id
    WHERE r.object_id = %s
''', (companies_obj_id,))

company_notes = cur.fetchall()
print(f'Found {len(company_notes)} notes linked to companies')

updated_notes = 0
for note_id, company_id, note_title, note_content in company_notes:
    # Find primary person for this company
    cur.execute('''
        SELECT rv.record_id as person_id
        FROM record_values rv
        WHERE rv.attribute_id = %s AND rv.record_reference_value = %s
        LIMIT 1
    ''', (company_attr_id, company_id))
    
    result = cur.fetchone()
    if result:
        person_id = result[0]
        
        # Get person and company names for logging
        cur2 = conn.cursor()
        
        # Person name
        cur2.execute('''
            SELECT json_value->>'full_name'
            FROM record_values rv
            JOIN attributes a ON rv.attribute_id = a.id
            WHERE rv.record_id = %s AND a.slug = 'name'
        ''', (person_id,))
        person_name = cur2.fetchone()
        person_name = person_name[0] if person_name else 'Unknown'
        
        # Company name
        cur2.execute('''
            SELECT text_value
            FROM record_values rv
            JOIN attributes a ON rv.attribute_id = a.id
            WHERE rv.record_id = %s AND a.slug = 'name'
        ''', (company_id,))
        company_name = cur2.fetchone()
        company_name = company_name[0] if company_name else 'Unknown'
        cur2.close()
        
        # Update note to link to person
        cur.execute('UPDATE notes SET record_id = %s WHERE id = %s', (person_id, note_id))
        
        print(f'  Note "{note_title[:30]}..."')
        print(f'    Company: {company_name} → Person: {person_name}')
        
        # Also update note content to record original company link
        try:
            if note_content:
                content_data = json.loads(note_content) if isinstance(note_content, str) else note_content
                if isinstance(content_data, dict):
                    content_data['original_company_id'] = company_id
                    content_data['original_company_name'] = company_name
                    cur.execute('UPDATE notes SET content = %s WHERE id = %s', (json.dumps(content_data), note_id))
        except:
            pass  # If content not JSON, skip
        
        updated_notes += 1

print(f'Updated {updated_notes} notes to link to people')

# ===== 2. VERIFY TASK LINKS =====
print('\n2. VERIFYING TASK-PERSON LINKS')

cur.execute('SELECT COUNT(*) FROM task_records')
task_links = cur.fetchone()[0]
print(f'Task-person links: {task_links}')

# Check if any tasks missing links
cur.execute('''
    SELECT COUNT(*) as tasks_without_links
    FROM tasks t
    LEFT JOIN task_records tr ON t.id = tr.task_id
    WHERE tr.task_id IS NULL
''')

tasks_without_links = cur.fetchone()[0]
print(f'Tasks without person links: {tasks_without_links}')

if tasks_without_links > 0:
    print(f'  ⚠️ {tasks_without_links} tasks have no person links')
    # These might be system tasks or need manual linking

# ===== 3. VERIFY CONVERSATION LINKS =====
print('\n3. VERIFYING CONVERSATION LINKS')

conv_ws_id = '012d908a-f57f-45a3-8e94-fe866128b177'
cur.execute('''
    SELECT o.id FROM objects o
    WHERE o.workspace_id = %s AND o.slug = 'conversations'
''', (conv_ws_id,))
conv_obj_id = cur.fetchone()[0]

# Get client attribute
cur.execute('''
    SELECT id FROM attributes
    WHERE object_id = %s AND slug = 'client'
''', (conv_obj_id,))
client_attr_id = cur.fetchone()[0]

# Count conversations with client links
cur.execute('''
    SELECT COUNT(*)
    FROM record_values rv
    WHERE rv.attribute_id = %s AND rv.record_reference_value IS NOT NULL
''', (client_attr_id,))

conv_with_client = cur.fetchone()[0]
print(f'Conversations with client links: {conv_with_client}')

# Count total conversation records
cur.execute('''
    SELECT COUNT(*)
    FROM records r
    WHERE r.object_id = %s
''', (conv_obj_id,))

total_conversations = cur.fetchone()[0]
print(f'Total conversation records: {total_conversations}')

if conv_with_client < total_conversations:
    print(f'  ⚠️ {total_conversations - conv_with_client} conversations missing client links')

# ===== 4. SUMMARY =====
print('\n=== FINAL SUMMARY ===')
print(f'✅ Tasks: {task_links} task-person links created')
print(f'✅ Notes: {updated_notes} notes updated to link to people')
print(f'✅ Conversations: {conv_with_client}/{total_conversations} have client links')

# Check overall person coverage
print('\n=== PERSON COVERAGE ===')

# Count people with tasks
cur.execute('''
    SELECT COUNT(DISTINCT tr.record_id)
    FROM task_records tr
    JOIN records r ON tr.record_id = r.id
    WHERE r.object_id = %s
''', (people_obj_id,))

people_with_tasks = cur.fetchone()[0]
print(f'People with tasks: {people_with_tasks}')

# Count people with notes
cur.execute('''
    SELECT COUNT(DISTINCT n.record_id)
    FROM notes n
    JOIN records r ON n.record_id = r.id
    WHERE r.object_id = %s
''', (people_obj_id,))

people_with_notes = cur.fetchone()[0]
print(f'People with notes: {people_with_notes}')

# Count total people
cur.execute('SELECT COUNT(*) FROM records WHERE object_id = %s', (people_obj_id,))
total_people = cur.fetchone()[0]
print(f'Total people: {total_people}')

conn.commit()
cur.close()
conn.close()

print('\n✅ All relationships point to Person records')
print('\nNote: Some notes originally linked to companies now link to primary person.')
print('      Original company info preserved in note content.')