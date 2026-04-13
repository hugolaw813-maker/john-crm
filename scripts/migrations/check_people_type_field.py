#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(host='localhost', port=5433, user='jcw_l', database='openclaw')
cur = conn.cursor()

ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'

cur.execute("""
SELECT o.id
FROM objects o
WHERE o.workspace_id = %s AND o.slug = 'people'
""", (ws_id,))
people_obj_id = cur.fetchone()[0]
print('people object:', people_obj_id)

cur.execute("""
SELECT id, slug, title, type, is_multiselect
FROM attributes
WHERE object_id = %s AND slug = 'type'
""", (people_obj_id,))
row = cur.fetchone()
print('type attribute:', row)
attr_id = row[0]

print('\noptions:')
cur.execute("""
SELECT id, title, color, sort_order
FROM select_options
WHERE attribute_id = %s
ORDER BY sort_order
""", (attr_id,))
opts = cur.fetchall()
for r in opts:
    print(r)

print('\ncurrent values sample:')
cur.execute("""
SELECT rv.record_id, rv.text_value
FROM record_values rv
WHERE rv.attribute_id = %s
LIMIT 10
""", (attr_id,))
vals = cur.fetchall()
for r in vals:
    print(r)

print('\ncount by value:')
cur.execute("""
SELECT text_value, count(*)
FROM record_values
WHERE attribute_id = %s
GROUP BY text_value
ORDER BY count(*) DESC
""", (attr_id,))
for r in cur.fetchall():
    print(r)

cur.close()
conn.close()
