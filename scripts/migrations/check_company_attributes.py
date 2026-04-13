#!/usr/bin/env python3
"""
Check Company object attributes for location/address fields
"""

import psycopg2

PG_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
}

def check():
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'
    
    print('=== COMPANY OBJECT ATTRIBUTES ===')
    cur.execute('''
        SELECT a.slug, a.title, a.type
        FROM attributes a
        JOIN objects o ON a.object_id = o.id
        WHERE o.workspace_id = %s AND o.slug = 'companies'
        ORDER BY a.slug
    ''', (john_ws_id,))
    
    for slug, title, attr_type in cur.fetchall():
        print(f'  {slug}: {title} ({attr_type})')
    
    # Check for location/address fields
    print('\n=== CHECKING FOR LOCATION/ADDRESS FIELDS ===')
    cur.execute('''
        SELECT a.slug, a.title, a.type
        FROM attributes a
        JOIN objects o ON a.object_id = o.id
        WHERE o.workspace_id = %s AND o.slug = 'companies'
        AND (a.slug ILIKE '%location%' OR a.title ILIKE '%location%' OR a.slug ILIKE '%address%' OR a.title ILIKE '%address%')
    ''', (john_ws_id,))
    
    location_fields = cur.fetchall()
    if location_fields:
        print('Found location/address fields:')
        for slug, title, attr_type in location_fields:
            print(f'  {slug}: {title} ({attr_type})')
    else:
        print('No location/address fields found')
    
    # Check primary_location specifically
    print('\n=== PRIMARY_LOCATION ATTRIBUTE ===')
    cur.execute('''
        SELECT a.id, a.title, a.type, a.config::text
        FROM attributes a
        JOIN objects o ON a.object_id = o.id
        WHERE o.workspace_id = %s AND o.slug = 'companies' AND a.slug = 'primary_location'
    ''', (john_ws_id,))
    
    primary_loc = cur.fetchone()
    if primary_loc:
        attr_id, title, attr_type, config = primary_loc
        print(f'primary_location: {title} ({attr_type})')
        print(f'Config: {config}')
        
        # Check if it should be renamed
        if title != 'Address' and title != 'Primary Address':
            print(f'\nShould rename "{title}" → "Address" or "Primary Address"?')
    
    # Check if there are any values in primary_location
    if primary_loc:
        attr_id = primary_loc[0]
        cur.execute('SELECT COUNT(*) FROM record_values WHERE attribute_id = %s', (attr_id,))
        count = cur.fetchone()[0]
        print(f'\nprimary_location has {count} values stored')
        
        if count > 0:
            cur.execute('''
                SELECT rv.text_value, rv.json_value
                FROM record_values rv
                WHERE rv.attribute_id = %s
                LIMIT 3
            ''', (attr_id,))
            print('Sample values:')
            for text_val, json_val in cur.fetchall():
                if text_val:
                    print(f'  Text: {text_val}')
                if json_val:
                    print(f'  JSON: {json_val}')
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    check()