#!/usr/bin/env python3
import psycopg2

WORKSPACES = [
    '2d46eec2-03d1-4f93-9b96-356ec7afa757',  # John's Workspace
    '4743688a-6be0-4f5e-a31e-6f0d8d504a9d',  # My Workspace (if present)
]

OPTIONS = [
    ('client', 'Client', '#3b82f6', 0),
    ('agent', 'Agent', '#8b5cf6', 1),
    ('cio', 'CIO', '#14b8a6', 2),
    ('bni', 'BNI', '#f59e0b', 3),
    ('professional', 'Professional', '#22c55e', 4),
    ('contact', 'Contact', '#6b7280', 5),
]

conn = psycopg2.connect(host='localhost', port=5433, user='jcw_l', database='openclaw')
cur = conn.cursor()

for ws_id in WORKSPACES:
    cur.execute("""
    SELECT a.id, o.slug
    FROM attributes a
    JOIN objects o ON a.object_id = o.id
    WHERE o.workspace_id = %s AND o.slug = 'people' AND a.slug = 'type'
    """, (ws_id,))
    row = cur.fetchone()
    if not row:
        print(f'skip workspace {ws_id}: people.type not found')
        continue

    attr_id, _ = row
    print(f'workspace {ws_id}: type attribute {attr_id}')

    for opt_id, title, color, sort_order in OPTIONS:
        cur.execute("""
        INSERT INTO select_options (id, attribute_id, title, color, sort_order)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
          attribute_id = EXCLUDED.attribute_id,
          title = EXCLUDED.title,
          color = EXCLUDED.color,
          sort_order = EXCLUDED.sort_order
        """, (opt_id, attr_id, title, color, sort_order))
        print(f'  upserted {opt_id} -> {title}')

conn.commit()
cur.close()
conn.close()

print('\nDone.')
