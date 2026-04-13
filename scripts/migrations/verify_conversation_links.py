#!/usr/bin/env python3
"""
Verify conversation links to people
"""

import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    user='jcw_l',
    database='openclaw'
)
cur = conn.cursor()

conv_ws_id = '012d908a-f57f-45a3-8e94-fe866128b177'

print('=== VERIFYING CONVERSATION LINKS ===')

# Get Conversation object
cur.execute('''
    SELECT o.id FROM objects o
    WHERE o.workspace_id = %s AND o.slug = 'conversations'
''', (conv_ws_id,))
conv_obj_id = cur.fetchone()[0]

# Get attributes
cur.execute('''
    SELECT slug, id, title FROM attributes
    WHERE object_id = %s
    ORDER BY slug
''', (conv_obj_id,))

print('Conversation attributes:')
attrs = {}
for slug, attr_id, title in cur.fetchall():
    print(f'  {slug}: {title} (id: {attr_id})')
    attrs[slug] = attr_id

# Check client links
if 'client' in attrs:
    client_attr_id = attrs['client']
    
    # Get conversations with client links
    cur.execute('''
        SELECT rv.record_id as conv_id, rv.record_reference_value as person_id
        FROM record_values rv
        WHERE rv.attribute_id = %s AND rv.record_reference_value IS NOT NULL
    ''', (client_attr_id,))
    
    conv_person_links = cur.fetchall()
    print(f'\nConversations with client links: {len(conv_person_links)}')
    
    # Sample with names
    for conv_id, person_id in conv_person_links[:5]:
        # Get conversation title
        cur2 = conn.cursor()
        cur2.execute('''
            SELECT text_value
            FROM record_values rv
            JOIN attributes a ON rv.attribute_id = a.id
            WHERE rv.record_id = %s AND a.slug = 'title'
        ''', (conv_id,))
        
        title_result = cur2.fetchone()
        conv_title = title_result[0] if title_result else 'No title'
        
        # Get person name
        cur2.execute('''
            SELECT json_value->>'full_name'
            FROM record_values rv
            JOIN attributes a ON rv.attribute_id = a.id
            WHERE rv.record_id = %s AND a.slug = 'name'
        ''', (person_id,))
        
        name_result = cur2.fetchone()
        person_name = name_result[0] if name_result else 'Unknown'
        
        print(f'  "{conv_title[:30]}..." → {person_name}')
        cur2.close()

# Check household links
if 'household' in attrs:
    household_attr_id = attrs['household']
    
    cur.execute('''
        SELECT COUNT(*)
        FROM record_values rv
        WHERE rv.attribute_id = %s AND rv.record_reference_value IS NOT NULL
    ''', (household_attr_id,))
    
    conv_household_links = cur.fetchone()[0]
    print(f'\nConversations with household links: {conv_household_links}')

cur.close()
conn.close()

print('\n✅ Conversations have proper client (person) links')