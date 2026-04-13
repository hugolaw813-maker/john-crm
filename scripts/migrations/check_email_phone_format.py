#!/usr/bin/env python3
"""
Check email and phone format
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

john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'

# Get People object
cur.execute('''
    SELECT o.id
    FROM objects o
    WHERE o.workspace_id = %s AND o.slug = 'people'
''', (john_ws_id,))
people_obj_id = cur.fetchone()[0]

# Get email and phone attribute IDs
cur.execute('''
    SELECT slug, id FROM attributes
    WHERE object_id = %s AND slug IN ('email_addresses', 'phone_numbers')
''', (people_obj_id,))

attrs = {slug: attr_id for slug, attr_id in cur.fetchall()}
print(f'Attribute IDs: {attrs}')

# Check email format
if 'email_addresses' in attrs:
    email_attr_id = attrs['email_addresses']
    cur.execute('''
        SELECT json_value
        FROM record_values
        WHERE attribute_id = %s
        LIMIT 3
    ''', (email_attr_id,))
    
    print('\nEmail format samples:')
    for json_val in cur.fetchall():
        json_val = json_val[0]
        if json_val:
            if isinstance(json_val, dict):
                print(f'  Dict: {json_val}')
            elif isinstance(json_val, list):
                print(f'  Array: {json_val}')
            else:
                print(f'  Other: {json_val} (type: {type(json_val)})')

# Check phone format
if 'phone_numbers' in attrs:
    phone_attr_id = attrs['phone_numbers']
    cur.execute('''
        SELECT json_value
        FROM record_values
        WHERE attribute_id = %s
        LIMIT 3
    ''', (phone_attr_id,))
    
    print('\nPhone format samples:')
    for json_val in cur.fetchall():
        json_val = json_val[0]
        if json_val:
            if isinstance(json_val, dict):
                print(f'  Dict: {json_val}')
            elif isinstance(json_val, list):
                print(f'  Array: {json_val}')
            else:
                print(f'  Other: {json_val} (type: {type(json_val)})')

# Count how many records have email/phone
print('\n=== COUNTS ===')
if 'email_addresses' in attrs:
    cur.execute('SELECT COUNT(*) FROM record_values WHERE attribute_id = %s', (email_attr_id,))
    email_count = cur.fetchone()[0]
    print(f'Records with email: {email_count}')

if 'phone_numbers' in attrs:
    cur.execute('SELECT COUNT(*) FROM record_values WHERE attribute_id = %s', (phone_attr_id,))
    phone_count = cur.fetchone()[0]
    print(f'Records with phone: {phone_count}')

cur.close()
conn.close()

print('\n✅ Format check complete')
print('Email/Phone are stored as JSON arrays. May need conversion to simple text if UI doesn\'t display them properly.')