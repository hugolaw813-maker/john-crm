#!/usr/bin/env python3
"""
Check current relationships for tasks, notes, conversations
"""

import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    user='jcw_l',
    database='openclaw'
)
cur = conn.cursor()

print('=== CURRENT RELATIONSHIPS ANALYSIS ===')

# 1. Check built-in tasks table relationships
print('\n1. BUILT-IN TASKS TABLE STRUCTURE:')
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'tasks'
    ORDER BY ordinal_position
""")

task_cols = []
for col_name, data_type in cur.fetchall():
    print(f'  {col_name}: {data_type}')
    task_cols.append(col_name)

# Check for any relationship columns
relationship_cols = [c for c in task_cols if 'person' in c.lower() or 'user' in c.lower() or 'record' in c.lower()]
print(f'\nPossible relationship columns: {relationship_cols}')

# Check task_records table (seen earlier)
print('\n2. TASK_RECORDS TABLE (links tasks to records):')
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'task_records'
    ORDER BY ordinal_position
""")

for col_name, data_type in cur.fetchall():
    print(f'  {col_name}: {data_type}')

cur.execute('SELECT * FROM task_records LIMIT 5')
print('\nSample task_records:')
for row in cur.fetchall():
    print(f'  {row}')

# 3. Check notes table relationships
print('\n3. NOTES TABLE STRUCTURE:')
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'notes'
    ORDER BY ordinal_position
""")

for col_name, data_type in cur.fetchall():
    print(f'  {col_name}: {data_type}')

# Check record_id column in notes (likely links to person/company)
cur.execute("""
    SELECT n.record_id, o.singular_name, COUNT(*) as count
    FROM notes n
    JOIN records r ON n.record_id = r.id
    JOIN objects o ON r.object_id = o.id
    GROUP BY n.record_id, o.singular_name
    ORDER BY count DESC
    LIMIT 10
""")

print('\nNotes linked to objects:')
for record_id, object_type, count in cur.fetchall():
    print(f'  {record_id}: {object_type} ({count} notes)')

# 4. Check conversation records relationships
print('\n4. CONVERSATION RECORDS (Conversations workspace):')
conv_ws_id = '012d908a-f57f-45a3-8e94-fe866128b177'
cur.execute('''
    SELECT o.id, o.slug, o.singular_name
    FROM objects o
    WHERE o.workspace_id = %s
''', (conv_ws_id,))

conv_objects = cur.fetchall()
for obj_id, slug, singular in conv_objects:
    print(f'\nObject: {singular} (slug: {slug})')
    
    # Get attributes for this object
    cur2 = conn.cursor()
    cur2.execute('''
        SELECT slug, title, type
        FROM attributes
        WHERE object_id = %s
        ORDER BY slug
    ''', (obj_id,))
    
    for attr_slug, attr_title, attr_type in cur2.fetchall():
        print(f'  {attr_slug}: {attr_title} ({attr_type})')
    cur2.close()

# 5. Check our migrated tasks
print('\n5. MIGRATED TASKS (from deals):')
cur.execute('SELECT COUNT(*) FROM tasks')
total_tasks = cur.fetchone()[0]
print(f'Total tasks: {total_tasks}')

# Check if any have linked records
cur.execute('SELECT COUNT(*) FROM task_records')
task_links = cur.fetchone()[0]
print(f'Task-record links: {task_links}')

# 6. Check deals object (original) for relationships
print('\n6. DEALS OBJECT RELATIONSHIPS:')
john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'
cur.execute('''
    SELECT a.slug, a.title, a.type
    FROM attributes a
    JOIN objects o ON a.object_id = o.id
    WHERE o.workspace_id = %s AND o.slug = 'deals'
    AND a.type IN ('record_reference', 'actor_reference')
    ORDER BY a.slug
''', (john_ws_id,))

print('Deals relationship attributes:')
for slug, title, attr_type in cur.fetchall():
    print(f'  {slug}: {title} ({attr_type})')

cur.close()
conn.close()

print('\n=== ANALYSIS ===')
print('Tasks can link to records via task_records table')
print('Notes link to records via record_id column')
print('Conversations have client and household reference fields')
print('Need to ensure all link back to Person records')