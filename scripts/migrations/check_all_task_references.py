#!/usr/bin/env python3
"""
Check ALL task-related references in database
"""

import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    user='jcw_l',
    database='openclaw'
)
cur = conn.cursor()

print('=== COMPLETE TASK/DEAL CHECK ===')

# 1. Check ALL objects in ALL workspaces
print('\n1. ALL OBJECTS ACROSS ALL WORKSPACES:')
cur.execute('''
    SELECT w.name, o.slug, o.singular_name, o.plural_name
    FROM objects o
    JOIN workspaces w ON o.workspace_id = w.id
    ORDER BY w.name, o.slug
''')

for ws_name, slug, singular, plural in cur.fetchall():
    print(f'  {ws_name}: {slug} = {singular} ({plural})')

# 2. Check for any 'task' tables (system tables)
print('\n2. SYSTEM TABLES WITH "TASK" IN NAME:')
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name ILIKE '%task%'
    ORDER BY table_name
""")

for table in cur.fetchall():
    print(f'  {table[0]}')
    
    # Show columns for task-related tables
    cur2 = conn.cursor()
    cur2.execute(f"""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = '{table[0]}'
        ORDER BY ordinal_position
    """)
    cols = cur2.fetchall()
    print(f'    Columns: {[c[0] for c in cols]}')
    cur2.close()

# 3. Check if there's a separate 'tasks' object we missed
print('\n3. SEARCHING FOR SEPARATE TASKS OBJECT:')
cur.execute('''
    SELECT w.name, o.slug, o.singular_name, o.plural_name, o.is_system
    FROM objects o
    JOIN workspaces w ON o.workspace_id = w.id
    WHERE o.slug ILIKE '%task%' 
       OR o.singular_name ILIKE '%task%'
       OR o.plural_name ILIKE '%task%'
    ORDER BY w.name, o.slug
''')

found = False
for ws_name, slug, singular, plural, is_system in cur.fetchall():
    print(f'  {ws_name}: {slug} = {singular} ({plural}) - System: {is_system}')
    found = True

if not found:
    print('  No separate tasks object found')

# 4. Check for any 'deal' references still
print('\n4. ANY "DEAL" REFERENCES LEFT:')
cur.execute('''
    SELECT w.name, o.slug, o.singular_name, o.plural_name
    FROM objects o
    JOIN workspaces w ON o.workspace_id = w.id
    WHERE o.slug ILIKE '%deal%'
       OR o.singular_name ILIKE '%deal%'
       OR o.plural_name ILIKE '%deal%'
    ORDER BY w.name, o.slug
''')

for ws_name, slug, singular, plural in cur.fetchall():
    print(f'  {ws_name}: {slug} = {singular} ({plural})')

# 5. Check task_assignees and task_records tables (seen earlier)
print('\n5. TASK_ASSIGNEES TABLE CONTENT:')
cur.execute('SELECT COUNT(*) FROM task_assignees')
count = cur.fetchone()[0]
print(f'  task_assignees rows: {count}')

cur.execute('SELECT * FROM task_assignees LIMIT 3')
for row in cur.fetchall():
    print(f'  Sample: {row}')

print('\n6. TASK_RECORDS TABLE CONTENT:')
cur.execute('SELECT COUNT(*) FROM task_records')
count = cur.fetchone()[0]
print(f'  task_records rows: {count}')

cur.execute('SELECT * FROM task_records LIMIT 3')
for row in cur.fetchall():
    print(f'  Sample: {row}')

# 7. Check tasks table (if exists)
print('\n7. TASKS TABLE (IF EXISTS):')
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'tasks'
    ORDER BY ordinal_position
""")

cols = cur.fetchall()
if cols:
    print(f'  tasks table columns: {[c[0] for c in cols]}')
    
    cur.execute('SELECT COUNT(*) FROM tasks')
    count = cur.fetchone()[0]
    print(f'  tasks rows: {count}')
    
    cur.execute('SELECT * FROM tasks LIMIT 3')
    for row in cur.fetchall():
        print(f'  Sample: {row}')
else:
    print('  No tasks table found')

cur.close()
conn.close()

print('\n=== ANALYSIS ===')
print('If there\'s a separate "Tasks" section in sidebar, it might be:')
print('1. A system-wide tasks view (aggregates from multiple objects)')
print('2. A built-in feature separate from custom objects')
print('3. Or referring to the "tasks" object we just renamed')
print('\nWe need to see what the UI actually shows.')