#!/usr/bin/env python3
"""
Revert Household back to Company in Person object
(Keep sidebar consistency - Companies tab should link to Company field)
"""

import psycopg2

PG_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
}

def revert():
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    print('=== REVERTING HOUSEHOLD → COMPANY ===')
    print('Changing Person attribute title from "Household" back to "Company"')
    
    # 1. John's Workspace
    john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'
    
    cur.execute('''
        SELECT a.id, a.title
        FROM attributes a
        JOIN objects o ON a.object_id = o.id
        WHERE o.workspace_id = %s AND o.slug = 'people' AND a.slug = 'company'
    ''', (john_ws_id,))
    
    john_attr = cur.fetchone()
    if john_attr:
        attr_id, current_title = john_attr
        print(f'John\'s Workspace: Found company attribute titled "{current_title}"')
        
        if current_title != 'Company':
            cur.execute('UPDATE attributes SET title = %s WHERE id = %s', ('Company', attr_id))
            print(f'  ✅ Reverted to "Company"')
        else:
            print('  Already "Company"')
    else:
        print('John\'s Workspace: Company attribute not found')
    
    # 2. My Workspace
    my_ws_id = '709eeba3-da92-46ff-aeec-3415c62c5fdf'
    
    cur.execute('''
        SELECT a.id, a.title
        FROM attributes a
        JOIN objects o ON a.object_id = o.id
        WHERE o.workspace_id = %s AND o.slug = 'people' AND a.slug = 'company'
    ''', (my_ws_id,))
    
    my_attr = cur.fetchone()
    if my_attr:
        attr_id, current_title = my_attr
        print(f'My Workspace: Found company attribute titled "{current_title}"')
        
        if current_title != 'Company':
            cur.execute('UPDATE attributes SET title = %s WHERE id = %s', ('Company', attr_id))
            print(f'  ✅ Reverted to "Company"')
        else:
            print('  Already "Company"')
    else:
        print('My Workspace: Company attribute not found')
    
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
    
    # Check Company object name (sidebar)
    print('\n=== SIDEBAR: COMPANY OBJECT NAME ===')
    for ws_id, ws_name in [(john_ws_id, "John's Workspace"), (my_ws_id, "My Workspace")]:
        cur.execute('''
            SELECT singular_name, plural_name
            FROM objects
            WHERE workspace_id = %s AND slug = 'companies'
        ''', (ws_id,))
        
        obj_name = cur.fetchone()
        if obj_name:
            singular, plural = obj_name
            print(f'{ws_name}: {singular} ({plural})')
            
            # Should we rename Company object to Household? Let's check what user wants
            # For now, keep as Company/Companies to match the attribute
    
    conn.commit()
    cur.close()
    conn.close()
    
    print('\n✅ Done! Person attribute reverted to "Company"')
    print('\nNote: Sidebar shows "Companies" tab (object plural name)')
    print('      Person field now shows "Company" (matching sidebar)')
    print('      Data links unchanged - still points to same household records')

if __name__ == '__main__':
    revert()