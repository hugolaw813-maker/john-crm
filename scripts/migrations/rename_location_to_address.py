#!/usr/bin/env python3
"""
Rename Location attribute to Address in Person object
"""

import psycopg2

PG_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
}

def rename():
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    print('=== RENAMING LOCATION → ADDRESS ===')
    
    # 1. John's Workspace
    john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'
    
    cur.execute('''
        SELECT a.id, a.title
        FROM attributes a
        JOIN objects o ON a.object_id = o.id
        WHERE o.workspace_id = %s AND o.slug = 'people' AND a.slug = 'location'
    ''', (john_ws_id,))
    
    john_attr = cur.fetchone()
    if john_attr:
        attr_id, current_title = john_attr
        print(f'John\'s Workspace: Found location attribute "{current_title}"')
        
        if current_title != 'Address':
            cur.execute('UPDATE attributes SET title = %s WHERE id = %s', ('Address', attr_id))
            print(f'  ✅ Renamed to "Address"')
        else:
            print('  Already named "Address"')
    else:
        print('John\'s Workspace: Location attribute not found')
    
    # 2. My Workspace
    my_ws_id = '709eeba3-da92-46ff-aeec-3415c62c5fdf'
    
    cur.execute('''
        SELECT a.id, a.title
        FROM attributes a
        JOIN objects o ON a.object_id = o.id
        WHERE o.workspace_id = %s AND o.slug = 'people' AND a.slug = 'location'
    ''', (my_ws_id,))
    
    my_attr = cur.fetchone()
    if my_attr:
        attr_id, current_title = my_attr
        print(f'My Workspace: Found location attribute "{current_title}"')
        
        if current_title != 'Address':
            cur.execute('UPDATE attributes SET title = %s WHERE id = %s', ('Address', attr_id))
            print(f'  ✅ Renamed to "Address"')
        else:
            print('  Already named "Address"')
    else:
        print('My Workspace: Location attribute not found')
    
    # Verify changes
    print('\n=== VERIFICATION ===')
    for ws_id, ws_name in [(john_ws_id, "John's Workspace"), (my_ws_id, "My Workspace")]:
        cur.execute('''
            SELECT a.slug, a.title, a.type
            FROM attributes a
            JOIN objects o ON a.object_id = o.id
            WHERE o.workspace_id = %s AND o.slug = 'people'
            ORDER BY a.slug
        ''', (ws_id,))
        
        print(f'\n{ws_name} Person attributes:')
        for slug, title, attr_type in cur.fetchall():
            print(f'  {slug}: {title} ({attr_type})')
    
    # Check if there are any location values in records
    print('\n=== CHECKING FOR LOCATION DATA ===')
    # First get location attribute IDs
    location_attrs = []
    for ws_id in [john_ws_id, my_ws_id]:
        cur.execute('''
            SELECT a.id
            FROM attributes a
            JOIN objects o ON a.object_id = o.id
            WHERE o.workspace_id = %s AND o.slug = 'people' AND a.slug = 'location'
        ''', (ws_id,))
        result = cur.fetchone()
        if result:
            location_attrs.append(result[0])
    
    for attr_id in location_attrs:
        cur.execute('SELECT COUNT(*) FROM record_values WHERE attribute_id = %s', (attr_id,))
        count = cur.fetchone()[0]
        print(f'Location attribute {attr_id}: {count} values stored')
        
        if count > 0:
            cur.execute('''
                SELECT rv.text_value, rv.json_value
                FROM record_values rv
                WHERE rv.attribute_id = %s
                LIMIT 3
            ''', (attr_id,))
            print(f'  Sample values:')
            for text_val, json_val in cur.fetchall():
                if text_val:
                    print(f'    Text: {text_val}')
                if json_val:
                    print(f'    JSON: {json_val}')
    
    conn.commit()
    cur.close()
    conn.close()
    
    print('\n✅ Done! Location renamed to Address in both workspaces')

if __name__ == '__main__':
    rename()