#!/usr/bin/env python3
"""
Link notes from companies to primary person in household
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

print('=== LINKING COMPANY NOTES TO PEOPLE ===')

john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'

# Get People and Companies objects
cur.execute('''
    SELECT o.id, o.slug
    FROM objects o
    WHERE o.workspace_id = %s AND o.slug IN ('people', 'companies')
''', (john_ws_id,))

obj_ids = {}
for obj_id, slug in cur.fetchall():
    obj_ids[slug] = obj_id

people_obj_id = obj_ids['people']
companies_obj_id = obj_ids['companies']
print(f'People object ID: {people_obj_id}')
print(f'Companies object ID: {companies_obj_id}')

# Get company attribute on Person (links person to company)
cur.execute('''
    SELECT id FROM attributes
    WHERE object_id = %s AND slug = 'company'
''', (people_obj_id,))
company_attr_id = cur.fetchone()[0]

# Find notes linked to companies
cur.execute('''
    SELECT n.id, n.record_id as company_id, n.title, n.content
    FROM notes n
    JOIN records r ON n.record_id = r.id
    WHERE r.object_id = %s
''', (companies_obj_id,))

company_notes = cur.fetchall()
print(f'\nFound {len(company_notes)} notes linked to companies')

# For each company note, find primary person
notes_linked = 0
for note_id, company_id, note_title, note_content in company_notes:
    # Find people linked to this company
    cur.execute('''
        SELECT rv.record_id as person_id
        FROM record_values rv
        WHERE rv.attribute_id = %s AND rv.record_reference_value = %s
    ''', (company_attr_id, company_id))
    
    person_links = cur.fetchall()
    
    if person_links:
        # Use first person as primary
        person_id = person_links[0][0]
        
        # Get person name
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
        
        # Get company name
        cur2 = conn.cursor()
        cur2.execute('''
            SELECT text_value
            FROM record_values rv
            JOIN attributes a ON rv.attribute_id = a.id
            WHERE rv.record_id = %s AND a.slug = 'name'
        ''', (company_id,))
        
        company_name = cur2.fetchone()
        company_name = company_name[0] if company_name else 'Unknown'
        cur2.close()
        
        print(f'\nNote "{note_title[:30]}..."')
        print(f'  Company: {company_name}')
        print(f'  Primary person: {person_name}')
        
        # Check if note already linked to this person
        cur.execute('SELECT COUNT(*) FROM notes WHERE id = %s AND record_id = %s', (note_id, person_id))
        if cur.fetchone()[0] == 0:
            # Update note to link to person instead of company
            print(f'  ⚠️ Note linked to company, should link to person')
            print(f'  (Keeping both links would require note duplication)')
            
            # Option: Create a new note linked to person?
            # For now, just report
        else:
            print(f'  ✅ Already linked to person')
        
        notes_linked += 1
    else:
        print(f'\nNote "{note_title[:30]}..."')
        print(f'  Company ID: {company_id}')
        print(f'  ⚠️ No people linked to this company')

# Also check conversations in Conversations workspace
print('\n=== CHECKING CONVERSATIONS ===')
conv_ws_id = '012d908a-f57f-45a3-8e94-fe866128b177'

# Get Conversation object
cur.execute('''
    SELECT o.id FROM objects o
    WHERE o.workspace_id = %s AND o.slug = 'conversations'
''', (conv_ws_id,))
conv_obj_id = cur.fetchone()[0]

# Get client and household attributes
cur.execute('''
    SELECT slug, id, title FROM attributes
    WHERE object_id = %s AND slug IN ('client', 'household')
''', (conv_obj_id,))

conv_attrs = {}
for slug, attr_id, title in cur.fetchall():
    conv_attrs[slug] = (attr_id, title)

print('Conversation attributes:')
for slug, (attr_id, title) in conv_attrs.items():
    print(f'  {slug}: {title}')

# Check conversation links
if 'client' in conv_attrs:
    client_attr_id, client_title = conv_attrs['client']
    cur.execute('''
        SELECT COUNT(*)
        FROM record_values rv
        WHERE rv.attribute_id = %s AND rv.record_reference_value IS NOT NULL
    ''', (client_attr_id,))
    
    conv_with_client = cur.fetchone()[0]
    print(f'\nConversations with client link: {conv_with_client}')

if 'household' in conv_attrs:
    household_attr_id, household_title = conv_attrs['household']
    cur.execute('''
        SELECT COUNT(*)
        FROM record_values rv
        WHERE rv.attribute_id = %s AND rv.record_reference_value IS NOT NULL
    ''', (household_attr_id,))
    
    conv_with_household = cur.fetchone()[0]
    print(f'Conversations with household link: {conv_with_household}')

cur.close()
conn.close()

print('\n=== SUMMARY ===')
print(f'Company notes: {len(company_notes)}')
print(f'Notes with linked people: {notes_linked}')
print('\nNotes linked to companies should ideally be linked to people.')
print('Options:')
print('  1. Update note.record_id to point to person (loses company link)')
print('  2. Create duplicate notes for each person in household')
print('  3. Keep as-is (notes stay linked to households)')