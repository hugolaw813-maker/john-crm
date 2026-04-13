#!/usr/bin/env python3
"""
Rename Primary Location to Address in Company object
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
    
    print('=== RENAMING PRIMARY LOCATION → ADDRESS IN COMPANY ===')
    
    # 1. John's Workspace
    john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'
    
    cur.execute('''
        SELECT a.id, a.title
        FROM attributes a
        JOIN objects o ON a.object_id = o.id
        WHERE o.workspace_id = %s AND o.slug = 'companies' AND a.slug = 'primary_location'
    ''', (john_ws_id,))
    
    john_attr = cur.fetchone()
    if john_attr:
        attr_id, current_title = john_attr
        print(f'John\'s Workspace: Found primary_location attribute "{current_title}"')
        
        if current_title != 'Address':
            cur.execute('UPDATE attributes SET title = %s WHERE id = %s', ('Address', attr_id))
            print(f'  ✅ Renamed to "Address"')
        else:
            print('  Already named "Address"')
    else:
        print('John\'s Workspace: primary_location attribute not found')
    
    # 2. My Workspace
    my_ws_id = '709eeba3-da92-46ff-aeec-3415c62c5fdf'
    
    cur.execute('''
        SELECT a.id, a.title
        FROM attributes a
        JOIN objects o ON a.object_id = o.id
        WHERE o.workspace_id = %s AND o.slug = 'companies' AND a.slug = 'primary_location'
    ''', (my_ws_id,))
    
    my_attr = cur.fetchone()
    if my_attr:
        attr_id, current_title = my_attr
        print(f'My Workspace: Found primary_location attribute "{current_title}"')
        
        if current_title != 'Address':
            cur.execute('UPDATE attributes SET title = %s WHERE id = %s', ('Address', attr_id))
            print(f'  ✅ Renamed to "Address"')
        else:
            print('  Already named "Address"')
    else:
        print('My Workspace: primary_location attribute not found')
    
    # Verify changes
    print('\n=== VERIFICATION ===')
    for ws_id, ws_name in [(john_ws_id, "John's Workspace"), (my_ws_id, "My Workspace")]:
        cur.execute('''
            SELECT a.slug, a.title, a.type
            FROM attributes a
            JOIN objects o ON a.object_id = o.id
            WHERE o.workspace_id = %s AND o.slug = 'companies'
            ORDER BY a.slug
        ''', (ws_id,))
        
        print(f'\n{ws_name} Company attributes:')
        for slug, title, attr_type in cur.fetchall():
            print(f'  {slug}: {title} ({attr_type})')
    
    conn.commit()
    cur.close()
    conn.close()
    
    print('\n✅ Done! Primary Location renamed to Address in Company objects')

if __name__ == '__main__':
    rename()