#!/usr/bin/env python3
"""
Update 'deals' slug to 'tasks' for consistency with Task/Tasks naming
"""

import psycopg2

PG_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
}

def update():
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    print('=== UPDATING DEALS SLUG TO TASKS ===')
    
    # Get all workspaces
    cur.execute('SELECT id, name FROM workspaces ORDER BY name')
    workspaces = cur.fetchall()
    
    for ws_id, ws_name in workspaces:
        print(f'\n--- Checking {ws_name} ---')
        
        # Check if 'deals' object exists
        cur.execute('''
            SELECT id, slug, singular_name, plural_name
            FROM objects
            WHERE workspace_id = %s AND slug = 'deals'
        ''', (ws_id,))
        
        deals_obj = cur.fetchone()
        if deals_obj:
            obj_id, slug, singular, plural = deals_obj
            print(f'Found deals object: {singular} ({plural}), slug: {slug}')
            
            # Check if 'tasks' slug already exists
            cur.execute('''
                SELECT slug, singular_name, plural_name
                FROM objects
                WHERE workspace_id = %s AND slug = 'tasks'
            ''', (ws_id,))
            
            tasks_exists = cur.fetchone()
            if tasks_exists:
                print(f'⚠️ WARNING: "tasks" slug already exists: {tasks_exists}')
                print('  Cannot rename deals to tasks - slug conflict!')
            else:
                # Update slug from deals to tasks
                print(f'  Updating slug: "deals" → "tasks"')
                cur.execute('''
                    UPDATE objects
                    SET slug = 'tasks'
                    WHERE id = %s
                ''', (obj_id,))
                print(f'  ✅ Updated')
        
        # Also check if there are any other task/deal objects
        cur.execute('''
            SELECT slug, singular_name, plural_name
            FROM objects
            WHERE workspace_id = %s 
            AND (slug ILIKE '%task%' OR slug ILIKE '%deal%'
                 OR singular_name ILIKE '%task%' OR singular_name ILIKE '%deal%'
                 OR plural_name ILIKE '%task%' OR plural_name ILIKE '%deal%')
        ''', (ws_id,))
        
        all_related = cur.fetchall()
        if all_related:
            print(f'All related objects:')
            for slug, singular, plural in all_related:
                print(f'  {slug}: {singular} ({plural})')
    
    # Verify changes
    print('\n=== VERIFICATION ===')
    for ws_id, ws_name in workspaces:
        print(f'\n{ws_name}:')
        
        # Check tasks object
        cur.execute('''
            SELECT slug, singular_name, plural_name
            FROM objects
            WHERE workspace_id = %s AND (slug = 'tasks' OR slug = 'deals')
        ''', (ws_id,))
        
        objs = cur.fetchall()
        for slug, singular, plural in objs:
            print(f'  {slug}: {singular} ({plural})')
            
            if slug == 'tasks' and singular == 'Task' and plural == 'Tasks':
                print(f'    ✅ Correct: Tasks object with proper slug')
            elif slug == 'deals' and singular == 'Task' and plural == 'Tasks':
                print(f'    ⚠️  WARNING: Still has "deals" slug!')
            else:
                print(f'    ? Unknown state')
    
    conn.commit()
    cur.close()
    conn.close()
    
    print('\n✅ Done!')
    print('\nSummary:')
    print('  Changed object slug from "deals" to "tasks"')
    print('  Object display names remain: Task (singular), Tasks (plural)')
    print('  Sidebar now shows: "Tasks" (from plural_name)')
    print('  URLs will use: /tasks (from slug)')
    print('  No more confusion between display name and slug')

if __name__ == '__main__':
    update()