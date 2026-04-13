#!/usr/bin/env python3
"""
Check lists table for saved views
"""

import psycopg2
import json

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    user='jcw_l',
    database='openclaw'
)
cur = conn.cursor()

print('=== LISTS TABLE ===')
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'lists'
    ORDER BY ordinal_position
""")

print('Columns:')
for col_name, data_type in cur.fetchall():
    print(f'  {col_name}: {data_type}')

# Get all lists
print('\n=== ALL LISTS ===')
cur.execute('''
    SELECT id, name, slug, object_id, created_at, created_by
    FROM lists
    ORDER BY created_at
''')

for list_id, name, slug, object_id, created_at, created_by in cur.fetchall():
    print(f'\nList: {name} (slug: {slug})')
    print(f'  ID: {list_id}')
    print(f'  Object ID: {object_id}')
    print(f'  Created by: {created_by}')
    print(f'  Created at: {created_at}')

# Get list_attributes for these lists
print('\n=== LIST ATTRIBUTES (columns) ===')
cur.execute('''
    SELECT la.list_id, la.attribute_id, la.sort_order, la.width, a.slug, a.title
    FROM list_attributes la
    JOIN attributes a ON la.attribute_id = a.id
    ORDER BY la.list_id, la.sort_order
''')

current_list = None
for list_id, attr_id, sort_order, width, attr_slug, attr_title in cur.fetchall():
    if list_id != current_list:
        print(f'\nList {list_id} columns:')
        current_list = list_id
    print(f'  {sort_order}: {attr_slug} ({attr_title}) width: {width}')

# Check for lists for People and Tasks objects
john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'
print(f'\n=== LISTS FOR OBJECTS IN JOHN\'S WORKSPACE ===')

# Get People object
cur.execute('''
    SELECT id FROM objects
    WHERE workspace_id = %s AND slug = 'people'
''', (john_ws_id,))
people_obj_id = cur.fetchone()[0]

# Get Tasks object (built-in? or deals? Let's check deals)
cur.execute('''
    SELECT id FROM objects
    WHERE workspace_id = %s AND slug = 'deals'
''', (john_ws_id,))
deals_obj_id = cur.fetchone()[0]

print(f'People object ID: {people_obj_id}')
print(f'Deals object ID: {deals_obj_id}')

# Check lists for People
cur.execute('SELECT id, name, slug FROM lists WHERE object_id = %s', (people_obj_id,))
people_lists = cur.fetchall()
print(f'\nLists for People object: {len(people_lists)}')
for list_id, name, slug in people_lists:
    print(f'  {name} (slug: {slug})')

# Check lists for Deals
cur.execute('SELECT id, name, slug FROM lists WHERE object_id = %s', (deals_obj_id,))
deals_lists = cur.fetchall()
print(f'\nLists for Deals object: {len(deals_lists)}')
for list_id, name, slug in deals_lists:
    print(f'  {name} (slug: {slug})')

cur.close()
conn.close()