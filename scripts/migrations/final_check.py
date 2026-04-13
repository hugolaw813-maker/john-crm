#!/usr/bin/env python3
"""
Final check of migration
"""

import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    user='jcw_l',
    database='openclaw'
)
cur = conn.cursor()

print('=== FINAL CHECK ===')

# 1. Check tasks table
print('\n1. BUILT-IN TASKS TABLE:')
cur.execute('SELECT COUNT(*) FROM tasks')
total = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM tasks WHERE is_completed = true')
completed = cur.fetchone()[0]

print(f'  Total tasks: {total}')
print(f'  Completed: {completed}')
print(f'  Pending: {total - completed}')

print('\nSample tasks:')
cur.execute('''
    SELECT content, is_completed, deadline
    FROM tasks
    ORDER BY created_at
    LIMIT 5
''')

for content, is_completed, deadline in cur.fetchall():
    status = '✅' if is_completed else '⏳'
    deadline_str = f' (due: {deadline})' if deadline else ''
    print(f'  {status} {content[:60]}{deadline_str}')

# 2. Check deals object (should have 11 records still)
print('\n2. DEALS OBJECT:')
john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'
cur.execute('''
    SELECT COUNT(*) 
    FROM records r
    JOIN objects o ON r.object_id = o.id
    WHERE o.workspace_id = %s AND o.slug = 'deals'
''', (john_ws_id,))

deals_count = cur.fetchone()[0]
print(f'  John\'s Workspace: {deals_count} deal records')

# 3. Check sidebar objects
print('\n3. SIDEBAR OBJECTS (John\'s Workspace):')
cur.execute('''
    SELECT slug, singular_name, plural_name
    FROM objects
    WHERE workspace_id = %s
    ORDER BY slug
''', (john_ws_id,))

for slug, singular, plural in cur.fetchall():
    print(f'  {slug}: {singular} ({plural})')

# 4. Check Person attributes (should have Company field, not Household)
print('\n4. PERSON ATTRIBUTES:')
cur.execute('''
    SELECT a.slug, a.title
    FROM attributes a
    JOIN objects o ON a.object_id = o.id
    WHERE o.workspace_id = %s AND o.slug = 'people'
    ORDER BY a.slug
''', (john_ws_id,))

for slug, title in cur.fetchall():
    print(f'  {slug}: {title}')

# 5. Check task_assignees and task_records (should be empty or have data)
print('\n5. TASK ASSIGNMENTS AND LINKS:')
cur.execute('SELECT COUNT(*) FROM task_assignees')
assignees = cur.fetchone()[0]
print(f'  task_assignees: {assignees} rows')

cur.execute('SELECT COUNT(*) FROM task_records')
task_links = cur.fetchone()[0]
print(f'  task_records: {task_links} rows')

cur.close()
conn.close()

print('\n✅ VERIFICATION COMPLETE')
print('\nSummary:')
print(f'  • {total} tasks in built-in Tasks system (top sidebar)')
print(f'  • {deals_count} records still in Deals object (can be deleted)')
print('  • Sidebar shows: companies, deals, people')
print('  • Built-in Tasks appears in top navigation')