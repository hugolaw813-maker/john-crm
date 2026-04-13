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

# Get deals object and stage attribute
cur.execute('''
    SELECT a.id
    FROM attributes a
    JOIN objects o ON a.object_id = o.id
    WHERE o.workspace_id = %s AND o.slug = 'deals' AND a.slug = 'stage'
''', (john_ws_id,))

stage_attr_id = cur.fetchone()[0]

# Get statuses for this attribute
cur.execute('''
    SELECT id, title, color, sort_order
    FROM statuses
    WHERE attribute_id = %s
    ORDER BY sort_order
''', (stage_attr_id,))

print('Statuses for deals stage attribute:')
for status_id, title, color, sort_order in cur.fetchall():
    print(f'  {status_id}: {title} (color: {color}, order: {sort_order})')

# Check which GUIDs are in the data
cur.execute('''
    SELECT DISTINCT rv.text_value
    FROM record_values rv
    WHERE rv.attribute_id = %s
''', (stage_attr_id,))

print('\nGUIDs found in deal records:')
for guid in cur.fetchall():
    guid = guid[0]
    print(f'  {guid}')
    
    # Check if this matches any status ID
    cur2 = conn.cursor()
    cur2.execute('SELECT title FROM statuses WHERE id = %s', (guid,))
    match = cur2.fetchone()
    if match:
        print(f'    → Matches status: {match[0]}')
    cur2.close()

# Also check expected_close_date values
print('\nChecking expected_close_date values:')
cur.execute('''
    SELECT a.id
    FROM attributes a
    JOIN objects o ON a.object_id = o.id
    WHERE o.workspace_id = %s AND o.slug = 'deals' AND a.slug = 'expected_close_date'
''', (john_ws_id,))

date_attr_id = cur.fetchone()[0]

cur.execute('''
    SELECT COUNT(*),
           COUNT(CASE WHEN rv.date_value IS NOT NULL THEN 1 END) as has_date,
           MIN(rv.date_value),
           MAX(rv.date_value)
    FROM record_values rv
    WHERE rv.attribute_id = %s
''', (date_attr_id,))

total, has_date, min_date, max_date = cur.fetchone()
print(f'Total: {total}, Has date: {has_date}')
if has_date > 0:
    print(f'Date range: {min_date} to {max_date}')

cur.close()
conn.close()