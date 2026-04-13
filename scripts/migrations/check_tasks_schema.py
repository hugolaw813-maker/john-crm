#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    user='jcw_l',
    database='openclaw'
)
cur = conn.cursor()

# Check tasks table schema
cur.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'tasks'
    ORDER BY ordinal_position
""")

print('tasks table columns:')
for col_name, data_type, is_nullable in cur.fetchall():
    print(f'  {col_name}: {data_type} (nullable: {is_nullable})')

# Check what workspace_id should be
cur.execute('SELECT id FROM workspaces WHERE name = %s', ("John's Workspace",))
john_ws = cur.fetchone()
if john_ws:
    print(f'\nJohn\'s Workspace ID: {john_ws[0]}')

cur.close()
conn.close()