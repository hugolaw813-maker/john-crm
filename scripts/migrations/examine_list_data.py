#!/usr/bin/env python3
"""
Examine list and list_attributes data
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

# Get all lists with their attributes
print('=== ALL LISTS WITH COLUMNS ===')
cur.execute('''
    SELECT l.id, l.name, l.slug, l.object_id, o.singular_name, o.plural_name
    FROM lists l
    JOIN objects o ON l.object_id = o.id
    ORDER BY l.created_at
''')

for list_id, list_name, list_slug, object_id, obj_singular, obj_plural in cur.fetchall():
    print(f'\nList: {list_name} (slug: {list_slug})')
    print(f'  Object: {obj_singular} ({obj_plural})')
    print(f'  List ID: {list_id}')
    
    # Get columns for this list
    cur2 = conn.cursor()
    cur2.execute('''
        SELECT slug, title, type, sort_order, config::text
        FROM list_attributes
        WHERE list_id = %s
        ORDER BY sort_order
    ''', (list_id,))
    
    columns = cur2.fetchall()
    print(f'  Columns ({len(columns)}):')
    for slug, title, col_type, sort_order, config_json in columns:
        config_str = f', config: {config_json}' if config_json else ''
        print(f'    {sort_order}: {slug} ({title}) - {col_type}{config_str}')
    
    cur2.close()

# Check what lists exist for People and Deals objects
john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'
print(f'\n=== CHECKING LISTS FOR OBJECTS IN JOHN\'S WORKSPACE ===')

# Get People object
cur.execute('''
    SELECT id, singular_name, plural_name
    FROM objects
    WHERE workspace_id = %s AND slug = 'people'
''', (john_ws_id,))
people_obj = cur.fetchone()
if people_obj:
    people_obj_id, people_singular, people_plural = people_obj
    print(f'\nPeople object: {people_singular} ({people_plural}) ID: {people_obj_id}')
    
    cur.execute('SELECT id, name, slug FROM lists WHERE object_id = %s', (people_obj_id,))
    people_lists = cur.fetchall()
    print(f'Lists for People: {len(people_lists)}')
    for list_id, list_name, list_slug in people_lists:
        print(f'  {list_name} (slug: {list_slug})')

# Get Deals object
cur.execute('''
    SELECT id, singular_name, plural_name
    FROM objects
    WHERE workspace_id = %s AND slug = 'deals'
''', (john_ws_id,))
deals_obj = cur.fetchone()
if deals_obj:
    deals_obj_id, deals_singular, deals_plural = deals_obj
    print(f'\nDeals object: {deals_singular} ({deals_plural}) ID: {deals_obj_id}')
    
    cur.execute('SELECT id, name, slug FROM lists WHERE object_id = %s', (deals_obj_id,))
    deals_lists = cur.fetchall()
    print(f'Lists for Deals: {len(deals_lists)}')
    for list_id, list_name, list_slug in deals_lists:
        print(f'  {list_name} (slug: {list_slug})')

# Get Companies object
cur.execute('''
    SELECT id, singular_name, plural_name
    FROM objects
    WHERE workspace_id = %s AND slug = 'companies'
''', (john_ws_id,))
companies_obj = cur.fetchone()
if companies_obj:
    companies_obj_id, companies_singular, companies_plural = companies_obj
    print(f'\nCompanies object: {companies_singular} ({companies_plural}) ID: {companies_obj_id}')
    
    cur.execute('SELECT id, name, slug FROM lists WHERE object_id = %s', (companies_obj_id,))
    companies_lists = cur.fetchall()
    print(f'Lists for Companies: {len(companies_lists)}')
    for list_id, list_name, list_slug in companies_lists:
        print(f'  {list_name} (slug: {list_slug})')

cur.close()
conn.close()