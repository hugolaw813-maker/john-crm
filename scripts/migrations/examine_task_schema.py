#!/usr/bin/env python3
"""
Examine task and record_values schema
"""

import psycopg2

conn = psycopg2.connect(**{
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
})
cur = conn.cursor()

print('=== DATABASE SCHEMA EXAMINATION ===')

# 1. Check record_values table columns
print('\n1. record_values TABLE COLUMNS:')
cur.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'record_values'
    ORDER BY ordinal_position
""")

for col_name, data_type, nullable in cur.fetchall():
    print(f'  {col_name}: {data_type} (nullable: {nullable})')

# 2. Check task_records table
print('\n2. task_records TABLE COLUMNS:')
cur.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'task_records'
    ORDER BY ordinal_position
""")

for col_name, data_type, nullable in cur.fetchall():
    print(f'  {col_name}: {data_type} (nullable: {nullable})')

# 3. Check actual data in record_values for record_reference type
print('\n3. SAMPLE record_values DATA (record_reference type):')
cur.execute("""
    SELECT DISTINCT attribute_id
    FROM record_values
    WHERE json_value IS NOT NULL
    LIMIT 5
""")

sample_attrs = cur.fetchall()
print(f'Found {len(sample_attrs)} distinct attribute IDs')

# Check one sample to see structure
if sample_attrs:
    attr_id = sample_attrs[0][0]
    cur.execute('''
        SELECT json_value
        FROM record_values
        WHERE attribute_id = %s
        LIMIT 2
    ''', (attr_id,))
    
    print('\nSample JSON values:')
    for json_val in cur.fetchall():
        json_val = json_val[0]
        if json_val:
            print(f'  {type(json_val)}: {json_val}')

# 4. Check how record_reference attributes store data
print('\n4. RECORD_REFERENCE ATTRIBUTES:')
cur.execute("""
    SELECT a.slug, a.title, a.type, COUNT(rv.id) as value_count
    FROM attributes a
    LEFT JOIN record_values rv ON a.id = rv.attribute_id
    WHERE a.type = 'record_reference'
    GROUP BY a.id, a.slug, a.title, a.type
    ORDER BY value_count DESC
    LIMIT 5
""")

for slug, title, attr_type, count in cur.fetchall():
    print(f'  {slug} ({title}): {attr_type}, {count} values')

# 5. Check current task_records data
print('\n5. CURRENT task_records DATA:')
cur.execute('SELECT COUNT(*) FROM task_records')
count = cur.fetchone()[0]
print(f'Total task_records: {count}')

if count > 0:
    cur.execute('SELECT * FROM task_records LIMIT 3')
    for row in cur.fetchall():
        print(f'  {row}')

# 6. Check tasks table
print('\n6. TASKS TABLE SAMPLE:')
cur.execute('SELECT id, content, deadline, is_completed FROM tasks LIMIT 3')
for task_id, content, deadline, completed in cur.fetchall():
    print(f'  Task: {content[:40]}...')
    print(f'    ID: {task_id}')
    print(f'    Deadline: {deadline}')
    print(f'    Completed: {completed}')

cur.close()
conn.close()

print('\n=== ANALYSIS ===')
print('Need to understand how record_reference values are stored in record_values')
print('Check if json_value column contains the reference ID')