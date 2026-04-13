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

cur.execute("""
SELECT a.id
FROM attributes a
WHERE a.object_id = %s AND a.slug = 'name'
""", (people_obj_id,))
name_attr_id = cur.fetchone()[0]

print('Ordered by full_name text ASC:')
cur.execute("""
SELECT r.id,
       rv.json_value->>'full_name' AS full_name,
       rv.json_value->>'first_name' AS first_name,
       rv.json_value->>'last_name' AS last_name
FROM records r
JOIN record_values rv ON rv.record_id = r.id
WHERE r.object_id = %s AND rv.attribute_id = %s
ORDER BY COALESCE(rv.json_value->>'full_name', CONCAT_WS(' ', rv.json_value->>'first_name', rv.json_value->>'last_name')) ASC
LIMIT 30
""", (people_obj_id, name_attr_id))
for row in cur.fetchall():
    print(row)

print('\nOrdered by last_name, first_name ASC:')
cur.execute("""
SELECT r.id,
       rv.json_value->>'full_name' AS full_name,
       rv.json_value->>'first_name' AS first_name,
       rv.json_value->>'last_name' AS last_name
FROM records r
JOIN record_values rv ON rv.record_id = r.id
WHERE r.object_id = %s AND rv.attribute_id = %s
ORDER BY COALESCE(rv.json_value->>'last_name','') ASC,
         COALESCE(rv.json_value->>'first_name','') ASC
LIMIT 30
""", (people_obj_id, name_attr_id))
for row in cur.fetchall():
    print(row)

cur.close()
conn.close()
