#!/usr/bin/env python3
"""
Configure table views for People, Companies, and Deals objects
"""

import psycopg2
import json
import uuid

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    user='jcw_l',
    database='openclaw'
)
cur = conn.cursor()

print('=== CONFIGURING TABLE VIEWS ===')

john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'

# Get current user (John)
cur.execute('SELECT id FROM users ORDER BY created_at LIMIT 1')
user_id = cur.fetchone()[0]
print(f'Current user ID: {user_id}')

def configure_object_views(object_slug, view_name, column_slugs):
    """Configure views for an object"""
    print(f'\n--- Configuring {object_slug} views ---')
    
    # Get object
    cur.execute('''
        SELECT id, singular_name, plural_name
        FROM objects
        WHERE workspace_id = %s AND slug = %s
    ''', (john_ws_id, object_slug))
    
    obj = cur.fetchone()
    if not obj:
        print(f'  Object {object_slug} not found')
        return
    
    obj_id, singular, plural = obj
    print(f'  Object: {singular} ({plural}) ID: {obj_id}')
    
    # Get existing lists
    cur.execute('SELECT id, name, slug FROM lists WHERE object_id = %s', (obj_id,))
    existing_lists = cur.fetchall()
    print(f'  Existing lists: {len(existing_lists)}')
    
    # Create or update default view
    default_list_id = None
    default_list_name = f'All {plural}'
    
    for list_id, list_name, list_slug in existing_lists:
        if list_slug == 'all':
            default_list_id = list_id
            print(f'  Found existing "all" list: {list_name} (id: {list_id})')
            break
    
    if not default_list_id:
        # Create new default list
        default_list_id = str(uuid.uuid4())
        cur.execute('''
            INSERT INTO lists (id, object_id, name, slug, created_by)
            VALUES (%s, %s, %s, %s, %s)
        ''', (default_list_id, obj_id, default_list_name, 'all', user_id))
        print(f'  Created new "all" list: {default_list_name}')
    
    # Clear existing list_attributes
    cur.execute('DELETE FROM list_attributes WHERE list_id = %s', (default_list_id,))
    print(f'  Cleared existing columns')
    
    # Get attributes for this object
    cur.execute('''
        SELECT slug, title, type, config
        FROM attributes
        WHERE object_id = %s
        ORDER BY slug
    ''', (obj_id,))
    
    all_attrs = {slug: (title, attr_type, config) for slug, title, attr_type, config in cur.fetchall()}
    print(f'  Available attributes: {list(all_attrs.keys())}')
    
    # Add columns to list
    sort_order = 0
    for slug in column_slugs:
        if slug in all_attrs:
            title, attr_type, config = all_attrs[slug]
            list_attr_id = str(uuid.uuid4())
            cur.execute('''
                INSERT INTO list_attributes (id, list_id, slug, title, type, config, sort_order)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (list_attr_id, default_list_id, slug, title, attr_type, json.dumps(config) if config else '{}', sort_order))
            print(f'  Added column: {slug} ({title})')
            sort_order += 1
        else:
            print(f'  WARNING: Attribute {slug} not found in object')
    
    # Also add ID column at the end (system column)
    list_attr_id = str(uuid.uuid4())
    cur.execute('''
        INSERT INTO list_attributes (id, list_id, slug, title, type, config, sort_order)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', (list_attr_id, default_list_id, 'id', 'ID', 'text', '{}', sort_order))
    print(f'  Added system column: id (ID)')

# Configure People view
people_columns = [
    'name',        # Name (personal_name)
    'type',        # Type (select)
    'company',     # Company (record_reference to households)
    'email_addresses',  # Email (email_address)
    'phone_numbers',    # Phone (phone_number)  
    'location',    # Address (location - renamed to Address)
    'job_title'    # Job Title (text)
]
configure_object_views('people', 'All People', people_columns)

# Configure Companies view  
companies_columns = [
    'name',        # Name (text)
    'domains',     # Domains (text_array)
    'location',    # Address (primary_location - renamed to Address)
    'description'  # Description (text)
]
configure_object_views('companies', 'All Companies', companies_columns)

# Configure Deals view (even though should be empty)
deals_columns = [
    'name',                  # Name (text)
    'stage',                 # Stage (select)
    'expected_close_date',   # Expected Close Date (date)
    'value',                 # Value (currency)
    'company',               # Company (record_reference)
    'owner',                 # Owner (actor_reference)
    'associated_people'      # Associated People (record_reference)
]
configure_object_views('deals', 'All Deals', deals_columns)

# Verify configurations
print('\n=== VERIFICATION ===')
for object_slug in ['people', 'companies', 'deals']:
    print(f'\n{object_slug.upper()}:')
    
    cur.execute('''
        SELECT l.id, l.name, COUNT(la.id) as column_count
        FROM lists l
        JOIN objects o ON l.object_id = o.id
        LEFT JOIN list_attributes la ON l.id = la.list_id
        WHERE o.workspace_id = %s AND o.slug = %s
        GROUP BY l.id, l.name
    ''', (john_ws_id, object_slug))
    
    for list_id, list_name, column_count in cur.fetchall():
        print(f'  {list_name}: {column_count} columns')
        
        # Show columns
        cur2 = conn.cursor()
        cur2.execute('''
            SELECT slug, title, type
            FROM list_attributes
            WHERE list_id = %s
            ORDER BY sort_order
        ''', (list_id,))
        
        for slug, title, col_type in cur2.fetchall():
            print(f'    {slug}: {title} ({col_type})')
        cur2.close()

conn.commit()
cur.close()
conn.close()

print('\n✅ Table views configured')
print('\nSummary:')
print('  • People view: Name, Type, Company, Email, Phone, Address, Job Title')
print('  • Companies view: Name, Domains, Address, Description')
print('  • Deals view: Name, Stage, Expected Close Date, Value, Company, Owner, Associated People')
print('\nNote: Email/Phone may show as JSON arrays if format needs fixing')