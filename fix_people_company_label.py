#!/usr/bin/env python3
import psycopg2

WS_ID = '2d46eec2-03d1-4f93-9b96-356ec7afa757'

conn = psycopg2.connect(dbname='openclaw', user='jcw_l', host='/tmp')
cur = conn.cursor()

cur.execute('''
UPDATE attributes a
SET title = 'Company'
FROM objects o
WHERE a.object_id = o.id
  AND o.workspace_id = %s
  AND o.slug = 'people'
  AND a.slug = 'company'
RETURNING a.id, a.title
''', (WS_ID,))
print(cur.fetchall())

cur.execute('''
UPDATE list_attributes la
SET title = 'Company'
FROM lists l
JOIN objects o ON o.id = l.object_id
WHERE la.list_id = l.id
  AND o.workspace_id = %s
  AND o.slug = 'people'
  AND la.slug = 'company'
RETURNING la.list_id, la.title
''', (WS_ID,))
print(cur.fetchall())

conn.commit()
cur.close()
conn.close()
print('done')
