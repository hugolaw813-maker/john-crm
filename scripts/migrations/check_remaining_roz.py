#!/usr/bin/env python3
"""
Check for any remaining Rozzano spelling
"""

import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    user='jcw_l',
    database='openclaw'
)
cur = conn.cursor()

print('=== CHECKING FOR REMAINING ROZZANO SPELLING ===')

# 1. Person names
name_attr_id = '8b15f836-3184-4ab6-ae75-25e14efb324e'
cur.execute('''
    SELECT COUNT(*) FROM record_values 
    WHERE attribute_id = %s AND json_value::text ILIKE '%rozzano%'
''', (name_attr_id,))
person_wrong = cur.fetchone()[0]
print(f'Person names with Rozzano: {person_wrong}')

# 2. Person emails
email_attr_id = 'd4e8cd8a-72df-45a9-8a77-21ae14999a82'
cur.execute('''
    SELECT COUNT(*) FROM record_values 
    WHERE attribute_id = %s AND json_value::text ILIKE '%rozzano%'
''', (email_attr_id,))
email_wrong = cur.fetchone()[0]
print(f'Person emails with Rozzano: {email_wrong}')

# 3. Company names
company_name_attr_id = '423a6ea6-1f64-439c-9c78-9a17942eed30'
cur.execute('''
    SELECT COUNT(*) FROM record_values 
    WHERE attribute_id = %s AND text_value ILIKE '%rozzano%'
''', (company_name_attr_id,))
company_wrong = cur.fetchone()[0]
print(f'Company names with Rozzano: {company_wrong}')

# 4. Company domains
company_domains_attr_id = '237ff677-e6c3-4abe-b83b-6ae70bc2acf8'
cur.execute('''
    SELECT COUNT(*) FROM record_values 
    WHERE attribute_id = %s AND json_value::text ILIKE '%rozzano%'
''', (company_domains_attr_id,))
domains_wrong = cur.fetchone()[0]
print(f'Company domains with Rozzano: {domains_wrong}')

# 5. Notes
cur.execute("SELECT COUNT(*) FROM notes WHERE title ILIKE '%roz%' OR content::text ILIKE '%roz%'")
notes_wrong = cur.fetchone()[0]
print(f'Notes with Rozzano: {notes_wrong}')

# 6. Conversation summaries/details
conv_obj_id = '9e4c7c56-c61d-4ee0-8e8b-c62771bec655'
# Get summary and details attribute IDs
cur.execute('''
    SELECT slug, id FROM attributes 
    WHERE object_id = %s AND slug IN ('summary', 'details')
''', (conv_obj_id,))

conv_wrong = 0
for slug, attr_id in cur.fetchall():
    cur.execute('''
        SELECT COUNT(*) FROM record_values 
        WHERE attribute_id = %s AND text_value ILIKE '%roz%'
    ''', (attr_id,))
    count = cur.fetchone()[0]
    conv_wrong += count
    print(f'Conversation {slug} with Rozzano: {count}')

print(f'\nTotal remaining Rozzano instances: {person_wrong + email_wrong + company_wrong + domains_wrong + notes_wrong + conv_wrong}')

# Show any remaining instances
if person_wrong > 0:
    print('\nPerson names with Rozzano:')
    cur.execute('''
        SELECT record_id, json_value->>'full_name'
        FROM record_values 
        WHERE attribute_id = %s AND json_value::text ILIKE '%rozzano%'
    ''', (name_attr_id,))
    for rec_id, name in cur.fetchall():
        print(f'  {rec_id}: {name}')

if notes_wrong > 0:
    print('\nNotes with Rozzano:')
    cur.execute("SELECT id, title FROM notes WHERE title ILIKE '%roz%' OR content::text ILIKE '%roz%'")
    for note_id, title in cur.fetchall():
        print(f'  {note_id}: {title}')

cur.close()
conn.close()

print('\n✅ Check complete')