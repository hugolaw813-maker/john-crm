#!/usr/bin/env python3
import psycopg2

WORKSPACES = [
    ('2d46eec2-03d1-4f93-9b96-356ec7afa757', "John's Workspace"),
]

conn = psycopg2.connect(dbname='openclaw', user='jcw_l', host='/tmp')
cur = conn.cursor()

for ws_id, ws_name in WORKSPACES:
    cur.execute(
        """
        UPDATE attributes a
        SET title = 'Person'
        FROM objects o
        WHERE a.object_id = o.id
          AND o.workspace_id = %s
          AND o.slug = 'deals'
          AND a.slug = 'associated_people'
        RETURNING a.id, a.slug, a.title
        """,
        (ws_id,),
    )
    rows = cur.fetchall()
    if rows:
        print(f"{ws_name}: updated {rows}")
    else:
        print(f"{ws_name}: no matching deals.associated_people attribute found")

conn.commit()
cur.close()
conn.close()
print('done')
