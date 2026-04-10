#!/usr/bin/env python3
import psycopg2

WS_ID = '2d46eec2-03d1-4f93-9b96-356ec7afa757'

conn = psycopg2.connect(dbname='openclaw', user='jcw_l', host='/tmp')
cur = conn.cursor()

# --- Deals -> Projects ---
cur.execute("SELECT id FROM objects WHERE workspace_id = %s AND slug = 'deals'", (WS_ID,))
row = cur.fetchone()
if not row:
    raise SystemExit('Deals object not found')
projects_obj_id = row[0]

# Delete all records under deals/projects
cur.execute("DELETE FROM records WHERE object_id = %s", (projects_obj_id,))
print(f'Deleted deal/project records: {cur.rowcount}')

# Rename object + slug
cur.execute(
    "UPDATE objects SET slug = 'projects', singular_name = 'Project', plural_name = 'Projects' WHERE id = %s",
    (projects_obj_id,),
)
print('Renamed Deals -> Projects and slug deals -> projects')

# Rename saved lists
cur.execute(
    "UPDATE lists SET name = REPLACE(name, 'Deals', 'Projects'), slug = REPLACE(slug, 'deals', 'projects') WHERE object_id = %s",
    (projects_obj_id,),
)
print(f'Updated project list names/slugs: {cur.rowcount}')

# --- Groups cleanup (formerly companies object, slug still companies) ---
cur.execute("SELECT id FROM objects WHERE workspace_id = %s AND slug = 'companies'", (WS_ID,))
groups_obj_id = cur.fetchone()[0]

# Delete Domains field
cur.execute("SELECT id FROM attributes WHERE object_id = %s AND slug = 'domains'", (groups_obj_id,))
row = cur.fetchone()
if row:
    domains_attr_id = row[0]
    cur.execute("DELETE FROM attributes WHERE id = %s", (domains_attr_id,))
    print('Deleted Groups Domains field')
else:
    print('Groups Domains field not found')

# Rename Team -> Name (People list ref)
cur.execute("UPDATE attributes SET title = 'Name' WHERE object_id = %s AND slug = 'team'", (groups_obj_id,))
print(f'Renamed Groups team field to Name: {cur.rowcount}')

# Move team first in object ordering
cur.execute("SELECT slug FROM attributes WHERE object_id = %s ORDER BY sort_order, created_at, slug", (groups_obj_id,))
slugs = [r[0] for r in cur.fetchall()]
if 'team' in slugs:
    new_order = ['team'] + [s for s in slugs if s != 'team']
    for idx, slug in enumerate(new_order):
        cur.execute("UPDATE attributes SET sort_order = %s WHERE object_id = %s AND slug = %s", (idx, groups_obj_id, slug))
    print('Moved Groups team field to first position')

# Update saved Group list columns/titles
cur.execute("SELECT id, name FROM lists WHERE object_id = %s ORDER BY created_at", (groups_obj_id,))
for list_id, list_name in cur.fetchall():
    cur.execute("DELETE FROM list_attributes WHERE list_id = %s AND slug = 'domains'", (list_id,))
    cur.execute("UPDATE list_attributes SET title = 'Name' WHERE list_id = %s AND slug = 'team'", (list_id,))
    cur.execute("SELECT slug FROM list_attributes WHERE list_id = %s ORDER BY sort_order, slug", (list_id,))
    list_slugs = [r[0] for r in cur.fetchall()]
    if 'team' in list_slugs:
        reordered = ['team'] + [s for s in list_slugs if s != 'team']
        for idx, slug in enumerate(reordered):
            cur.execute("UPDATE list_attributes SET sort_order = %s WHERE list_id = %s AND slug = %s", (idx, list_id, slug))
        print(f'Updated Group list {list_name}: {reordered}')

conn.commit()
cur.close()
conn.close()
print('done')
