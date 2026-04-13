#!/usr/bin/env python3
"""
Check list_attributes table structure
"""

import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    user='jcw_l',
    database='openclaw'
)
cur = conn.cursor()

# Check list_attributes columns
print('=== LIST_ATTRIBUTES TABLE ===')
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'list_attributes'
    ORDER BY ordinal_position
""")

for col_name, data_type in cur.fetchall():
    print(f'  {col_name}: {data_type}')

# Check sample data
print('\n=== LIST_ATTRIBUTES DATA ===')
cur.execute('SELECT * FROM list_attributes LIMIT 10')
for row in cur.fetchall():
    print(f'  {row}')

# Also check if there's a column_attribute_id or similar
print('\n=== CHECKING FOR COLUMN CONFIG ===')
# Let's see all column names with "column" in them
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'list_attributes'
    AND column_name ILIKE '%column%'
    ORDER BY ordinal_position
""")

for col_name, data_type in cur.fetchall():
    print(f'  {col_name}: {data_type}')

cur.close()
conn.close()