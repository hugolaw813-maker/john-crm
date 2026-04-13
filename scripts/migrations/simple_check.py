#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    user='jcw_l',
    database='openclaw'
)
cur = conn.cursor()

john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'

# Get all objects in John's workspace
cur.execute('''
    SELECT slug, singular_name, plural_name
    FROM objects
    WHERE workspace_id = %s
    ORDER BY slug
''', (john_ws_id,))

print('Objects in John\'s Workspace:')
for slug, singular, plural in cur.fetchall():
    print(f'  {slug}: {singular} ({plural})')
    
    # Check if this is tasks/deals
    if 'task' in singular.lower() or 'deal' in singular.lower():
        print(f'    ^ This is the tasks/deals object!')

# Specifically check deals slug
cur.execute('''
    SELECT slug, singular_name, plural_name
    FROM objects
    WHERE workspace_id = %s AND slug = 'deals'
''', (john_ws_id,))

result = cur.fetchone()
if result:
    slug, singular, plural = result
    print(f'\nDeals object (slug=deals): {singular} ({plural})')
    
    # Check what the sidebar would show
    print(f'  Sidebar would show: "{plural}"')
    print(f'  Singular form: "{singular}"')
    
    if singular == 'Task' and plural == 'Tasks' and slug == 'deals':
        print('\n⚠️ CONFLICT: Object is named Task/Tasks but slug is "deals"')
        print('  Sidebar shows: "Tasks" (from plural_name)')
        print('  But URLs use: /deals (from slug)')
        print('  This could be confusing!')
else:
    print('\nNo object with slug "deals" found')

cur.close()
conn.close()