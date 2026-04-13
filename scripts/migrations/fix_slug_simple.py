#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    user='jcw_l',
    database='openclaw'
)
cur = conn.cursor()

print('=== FIXING DEALS SLUG ===')

# Update John's Workspace
john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'
cur.execute('''
    UPDATE objects
    SET slug = 'tasks'
    WHERE workspace_id = %s AND slug = 'deals'
    RETURNING slug, singular_name, plural_name
''', (john_ws_id,))

result = cur.fetchone()
if result:
    print(f"John's Workspace: Updated 'deals' → 'tasks'")
    print(f"  Object: {result[1]} ({result[2]})")
else:
    print("John's Workspace: No 'deals' object found")

# Update My Workspace  
my_ws_id = '709eeba3-da92-46ff-aeec-3415c62c5fdf'
cur.execute('''
    UPDATE objects
    SET slug = 'tasks'
    WHERE workspace_id = %s AND slug = 'deals'
    RETURNING slug, singular_name, plural_name
''', (my_ws_id,))

result = cur.fetchone()
if result:
    print(f"My Workspace: Updated 'deals' → 'tasks'")
    print(f"  Object: {result[1]} ({result[2]})")
else:
    print("My Workspace: No 'deals' object found")

# Verify
print('\n=== VERIFICATION ===')
for ws_id, ws_name in [(john_ws_id, "John's Workspace"), (my_ws_id, "My Workspace")]:
    cur.execute('''
        SELECT slug, singular_name, plural_name
        FROM objects
        WHERE workspace_id = %s AND (slug = 'tasks' OR slug = 'deals')
    ''', (ws_id,))
    
    objs = cur.fetchall()
    print(f'\n{ws_name}:')
    for slug, singular, plural in objs:
        print(f'  {slug}: {singular} ({plural})')

conn.commit()
cur.close()
conn.close()

print('\n✅ Done! Slug updated from "deals" to "tasks"')