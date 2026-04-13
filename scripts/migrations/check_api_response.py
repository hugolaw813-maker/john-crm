#!/usr/bin/env python3
"""
Simulate the tasks API response to see if linkedRecords are included
"""

import psycopg2

conn = psycopg2.connect(**{
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    database='openclaw'
})
cur = conn.cursor()

print('=== SIMULATING TASKS API RESPONSE ===')

john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'

# 1. Get tasks (simulating listTasks)
cur.execute('''
    SELECT id, content, deadline, is_completed, completed_at, created_by, created_at
    FROM tasks
    WHERE workspace_id = %s
    ORDER BY deadline DESC NULLS LAST, created_at DESC
    LIMIT 5
''', (john_ws_id,))

task_rows = cur.fetchall()
print(f'Found {len(task_rows)} tasks')

# 2. Get task_records for these tasks
task_ids = [row[0] for row in task_rows]
if task_ids:
    placeholders = ','.join(['%s'] * len(task_ids))
    cur.execute(f'''
        SELECT tr.task_id, tr.record_id
        FROM task_records tr
        WHERE tr.task_id IN ({placeholders})
    ''', task_ids)
    
    task_records = cur.fetchall()
    print(f'Task_records for these tasks: {len(task_records)}')
    
    # Group by task_id
    records_by_task = {}
    for task_id, record_id in task_records:
        if task_id not in records_by_task:
            records_by_task[task_id] = []
        records_by_task[task_id].append(record_id)
    
    # 3. Get display names for all unique record_ids
    all_record_ids = list(set([record_id for _, record_id in task_records]))
    print(f'Unique record IDs: {all_record_ids}')
    
    if all_record_ids:
        # Get record -> object mapping
        placeholders = ','.join(['%s'] * len(all_record_ids))
        cur.execute(f'''
            SELECT r.id, r.object_id, o.slug, o.singular_name
            FROM records r
            JOIN objects o ON r.object_id = o.id
            WHERE r.id IN ({placeholders})
        ''', all_record_ids)
        
        record_info = {row[0]: (row[1], row[2], row[3]) for row in cur.fetchall()}
        
        # Get name attributes for these objects
        object_ids = list(set([info[0] for info in record_info.values()]))
        placeholders = ','.join(['%s'] * len(object_ids))
        cur.execute(f'''
            SELECT a.id, a.object_id, a.type
            FROM attributes a
            WHERE a.object_id IN ({placeholders}) AND (a.slug = 'name' OR a.type = 'personal_name')
        ''', object_ids)
        
        name_attrs = {row[1]: (row[0], row[2]) for row in cur.fetchall()}
        
        # Get name values
        name_attr_ids = [attr[0] for attr in name_attrs.values()]
        if name_attr_ids:
            placeholders2 = ','.join(['%s'] * len(name_attr_ids))
            placeholders3 = ','.join(['%s'] * len(all_record_ids))
            cur.execute(f'''
                SELECT rv.record_id, rv.text_value, rv.json_value
                FROM record_values rv
                WHERE rv.attribute_id IN ({placeholders2}) AND rv.record_id IN ({placeholders3})
            ''', name_attr_ids + all_record_ids)
            
            name_values = {}
            for record_id, text_val, json_val in cur.fetchall():
                name_values[record_id] = (text_val, json_val)
        
        # Build display names
        display_map = {}
        for record_id in all_record_ids:
            if record_id in record_info:
                obj_id, slug, singular = record_info[record_id]
                display_name = 'Unknown'
                if record_id in name_values:
                    text_val, json_val = name_values[record_id]
                    if json_val and isinstance(json_val, dict) and 'full_name' in json_val:
                        display_name = json_val['full_name']
                    elif text_val:
                        display_name = text_val
                
                display_map[record_id] = {
                    'displayName': display_name,
                    'objectSlug': slug,
                    'objectName': singular
                }
        
        print('\nDisplay names:')
        for record_id, info in display_map.items():
            print(f'  {record_id}: {info["displayName"]} ({info["objectSlug"]})')
        
        # 4. Build enriched tasks
        print('\nEnriched tasks:')
        for task_row in task_rows:
            task_id = task_row[0]
            content = task_row[1]
            linked_records = records_by_task.get(task_id, [])
            print(f'\nTask: {content[:40]}...')
            print(f'  Linked records: {len(linked_records)}')
            for record_id in linked_records:
                if record_id in display_map:
                    info = display_map[record_id]
                    print(f'    - {info["displayName"]} ({info["objectSlug"]})')

cur.close()
conn.close()

print('\n=== CONCLUSION ===')
print('If display names are found, UI should show them in "Record" column.')
print('If UI still doesn\'t show, check:')
print('  1. Browser cache (refresh page)')
print('  2. API endpoint /api/v1/tasks returns linkedRecords')
print('  3. Column visibility (maybe hidden on small screens)')