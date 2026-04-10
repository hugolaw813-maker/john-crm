#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(dbname='openclaw', user='jcw_l', host='/tmp')
cur = conn.cursor()

WS_ID = '2d46eec2-03d1-4f93-9b96-356ec7afa757'

# find deals object + associated_people attr
cur.execute("SELECT id FROM objects WHERE workspace_id = %s AND slug = 'deals'", (WS_ID,))
deals_object_id = cur.fetchone()[0]
cur.execute("SELECT id FROM attributes WHERE object_id = %s AND slug = 'associated_people'", (deals_object_id,))
assoc_attr_id = cur.fetchone()[0]

# get deal names
cur.execute('''
SELECT r.id, rv.text_value
FROM records r
JOIN record_values rv ON rv.record_id = r.id
JOIN attributes a ON a.id = rv.attribute_id
WHERE r.object_id = %s AND a.slug = 'name'
''', (deals_object_id,))
deal_names = {deal_id: name for deal_id, name in cur.fetchall()}

# get deal->person references
cur.execute('''
SELECT rv.record_id, rv.referenced_record_id
FROM record_values rv
WHERE rv.attribute_id = %s AND rv.referenced_record_id IS NOT NULL
''', (assoc_attr_id,))
deal_person = cur.fetchall()

# map tasks by content
cur.execute("SELECT id, content FROM tasks WHERE workspace_id = %s ORDER BY created_at", (WS_ID,))
tasks = cur.fetchall()

# clear existing links and rebuild from deal associations
cur.execute("DELETE FROM task_records WHERE task_id IN (SELECT id FROM tasks WHERE workspace_id = %s)", (WS_ID,))

inserted = 0
for task_id, content in tasks:
    matched_deal_id = None
    for deal_id, deal_name in deal_names.items():
        if deal_name and content == deal_name:
            matched_deal_id = deal_id
            break
    if not matched_deal_id:
        for deal_id, deal_name in deal_names.items():
            if deal_name and deal_name in content:
                matched_deal_id = deal_id
                break
    if not matched_deal_id:
        print('no deal match:', content)
        continue

    people = [pid for did, pid in deal_person if did == matched_deal_id]
    for person_id in people:
        cur.execute(
            "INSERT INTO task_records (task_id, record_id) VALUES (%s, %s)",
            (task_id, person_id),
        )
        inserted += 1
        print('linked', content, '->', person_id)

conn.commit()
print('inserted links:', inserted)
cur.close()
conn.close()
