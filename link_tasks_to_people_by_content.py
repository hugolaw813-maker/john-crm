#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(dbname='openclaw', user='jcw_l', host='/tmp')
cur = conn.cursor()

# load people
cur.execute('''
SELECT r.id, COALESCE(rv.json_value->>'full_name', CONCAT_WS(' ', rv.json_value->>'first_name', rv.json_value->>'last_name')) AS full_name
FROM records r
JOIN objects o ON o.id = r.object_id
JOIN record_values rv ON rv.record_id = r.id
JOIN attributes a ON a.id = rv.attribute_id
WHERE o.slug = 'people' AND a.slug = 'name'
''')
people = [(rid, name) for rid, name in cur.fetchall() if name]

aliases = {
    'Dottie': 'Dorothy Vanderpyl',
    'Jessica': 'Jessica Lee',
    'Jahborn Riley': 'Jahborn Riley',
    'Michael Razzano': 'Michael Razzano',
    'Matthew Chan': 'Matthew Chan',
    'Lynn Oetting': 'Richard W. Oetting',
    'BNI': 'BNI Network',
}
name_to_id = {name: rid for rid, name in people}

cur.execute('SELECT id, content FROM tasks ORDER BY created_at')
tasks = cur.fetchall()

# clear links and rebuild by content matching
cur.execute('DELETE FROM task_records WHERE task_id IN (SELECT id FROM tasks)')
inserted = 0
for task_id, content in tasks:
    matched = None
    # exact/contains by full people names
    for rid, full_name in people:
        if full_name and full_name in content:
            matched = rid
            break
    # alias fallback
    if not matched:
        for key, mapped_name in aliases.items():
            if key in content and mapped_name in name_to_id:
                matched = name_to_id[mapped_name]
                break
    if matched:
        cur.execute('INSERT INTO task_records (task_id, record_id) VALUES (%s, %s)', (task_id, matched))
        inserted += 1
        print('linked:', content, '->', matched)
    else:
        print('unmatched:', content)

conn.commit()
print('inserted:', inserted)
cur.close()
conn.close()
