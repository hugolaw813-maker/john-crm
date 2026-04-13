#!/usr/bin/env python3
"""
Check current status of Tasks/Deals objects
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
    
    print('=== CHECKING TASKS/DEALS OBJECTS ===')
    
    # Check all workspaces
    cur.execute('SELECT id, name FROM workspaces ORDER BY name')
    workspaces = cur.fetchall()
    
    for ws_id, ws_name in workspaces:
        print(f'\n--- {ws_name} ({ws_id}) ---')
        
        # Get objects that might be tasks/deals
        cur.execute('''
            SELECT slug, singular_name, plural_name
            FROM objects
            WHERE workspace_id = %s
            AND (slug = 'deals' OR slug = 'tasks' 
                 OR singular_name ILIKE '%task%' OR singular_name ILIKE '%deal%'
                 OR plural_name ILIKE '%task%' OR plural_name ILIKE '%deal%')
            ORDER BY slug
        ''', (ws_id,))
        
        objects = cur.fetchall()
        if objects:
            for slug, singular, plural in objects:
                print(f'  Object: {singular} ({plural}) - slug: {slug}')
                
                # Count records
                cur2 = conn.cursor()
                cur2.execute('SELECT COUNT(*) FROM records WHERE object_id = (SELECT id FROM objects WHERE workspace_id = %s AND slug = %s)', (ws_id, slug))
                count = cur2.fetchone()[0]
                print(f'    Records: {count}')
                cur2.close()
        else:
            print('  No task/deal objects found')
    
    # Specifically check John's Workspace
    print('\n=== DETAILED CHECK - JOHN\'S WORKSPACE ===')
    john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'
    
    # Get the deals/tasks object
    cur.execute('''
        SELECT id, slug, singular_name, plural_name
        FROM objects
        WHERE workspace_id = %s AND slug = 'deals'
    ''', (john_ws_id,))
    
    obj = cur.fetchone()
    if obj:
        obj_id, slug, singular, plural = obj
        print(f'Object: {singular} ({plural})')
        print(f'Slug: {slug}')
        print(f'ID: {obj_id}')
        
        # Get attributes
        cur.execute('''
            SELECT slug, title, type
            FROM attributes
            WHERE object_id = %s
            ORDER BY slug
        ''', (obj_id,))
        
        print('\nAttributes:')
        for attr_slug, attr_title, attr_type in cur.fetchall():
            print(f'  {attr_slug}: {attr_title} ({attr_type})')
        
        # Check if slug matches expected name
        if singular == 'Task' and slug == 'deals':
            print(f'\n⚠️ WARNING: Object named "Task" but slug is "deals"')
            print('  This could cause confusion in URLs/sidebar')
            print('  Should we change slug from "deals" to "tasks"?')
        
        # Check statuses
        cur.execute('''
            SELECT a.id FROM attributes a
            WHERE a.object_id = %s AND a.slug = 'stage'
        ''', (obj_id,))
        
        stage_attr = cur.fetchone()
        if stage_attr:
            stage_attr_id = stage_attr[0]
            cur.execute('''
                SELECT title, color, sort_order
                FROM statuses
                WHERE attribute_id = %s
                ORDER BY sort_order
            ''', (stage_attr_id,))
            
            print('\nStatus options:')
            for title, color, sort_order in cur.fetchall():
                print(f'  {sort_order}: {title} (color: {color})')
    
    # Check if there's also a 'tasks' slug object
    cur.execute('''
        SELECT slug, singular_name, plural_name
        FROM objects
        WHERE workspace_id = %s AND slug = 'tasks'
    ''', (john_ws_id,))
    
    tasks_obj = cur.fetchone()
    if tasks_obj:
        print(f'\n⚠️ Found separate "tasks" object: {tasks_obj}')
    
    cur.close()
    conn.close()
    
    print('\n=== ANALYSIS ===')
    print('If sidebar shows "Deals" but records are tasks, the slug might still be "deals".')
    print('We renamed the object names but may need to update the slug too.')

if __name__ == '__main__':
    check()