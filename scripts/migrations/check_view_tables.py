#!/usr/bin/env python3
"""
Check for view/table configuration tables
"""

import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    user='jcw_l',
    database='openclaw'
)
cur = conn.cursor()

# Get all tables
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name
""")

print('All tables:')
for table in cur.fetchall():
    table_name = table[0]
    print(f'  {table_name}')
    
    # Check for view/column related tables
    if 'view' in table_name.lower() or 'column' in table_name.lower() or 'config' in table_name.lower():
        print(f'    ^ Possible view/column config table!')
        cur2 = conn.cursor()
        cur2.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position")
        cols = [row[0] for row in cur2.fetchall()]
        print(f'    Columns: {cols}')
        cur2.close()

# Specifically check for view_definitions, table_views, etc.
print('\n=== SEARCHING FOR VIEW TABLES ===')
view_tables = ['view_definitions', 'table_views', 'record_views', 'object_views', 'user_views']
for table in view_tables:
    cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)", (table,))
    exists = cur.fetchone()[0]
    if exists:
        print(f'{table} exists!')
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' ORDER BY ordinal_position")
        cols = [row[0] for row in cur.fetchall()]
        print(f'  Columns: {cols}')

# Check list_entries table (might store saved views)
print('\n=== LIST_ENTRIES TABLE (potential saved views) ===')
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'list_entries' ORDER BY ordinal_position")
cols = [row[0] for row in cur.fetchall()]
print(f'Columns: {cols}')

cur.close()
conn.close()