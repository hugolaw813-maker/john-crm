#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(dbname='openclaw', user='jcw_l', host='/tmp')
cur = conn.cursor()

cur.execute('''
SELECT t.id, t.content, tr.record_id, o.slug, o.singular_name
FROM task_records tr
JOIN tasks t ON t.id = tr.task_id
JOIN records r ON r.id = tr.record_id
JOIN objects o ON o.id = r.object_id
ORDER BY t.created_at
LIMIT 20
''')
rows = cur.fetchall()
print('task -> record links:')
for row in rows:
    print(row)

cur.execute('''
SELECT rv.record_id,
       rv.json_value->>'full_name' AS full_name,
       rv.json_value->>'first_name' AS first_name,
       rv.json_value->>'last_name' AS last_name,
       rv.text_value
FROM record_values rv
JOIN attributes a ON a.id = rv.attribute_id
WHERE a.slug = 'name'
  AND rv.record_id IN (SELECT record_id FROM task_records)
ORDER BY rv.record_id
''')
print('\nperson name values:')
for row in cur.fetchall():
    print(row)

cur.close()
conn.close()
