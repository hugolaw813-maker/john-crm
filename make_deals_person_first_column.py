#!/usr/bin/env python3
import psycopg2

WS_ID = '2d46eec2-03d1-4f93-9b96-356ec7afa757'  # John's Workspace

conn = psycopg2.connect(dbname='openclaw', user='jcw_l', host='/tmp')
cur = conn.cursor()

# Find Deals object
cur.execute("SELECT id FROM objects WHERE workspace_id = %s AND slug = 'deals'", (WS_ID,))
row = cur.fetchone()
if not row:
    raise SystemExit('Deals object not found')
object_id = row[0]
print('deals object:', object_id)

# Reorder object attributes so Person is first
cur.execute("""
SELECT slug
FROM attributes
WHERE object_id = %s
ORDER BY sort_order, created_at, slug
""", (object_id,))
ordered_slugs = [r[0] for r in cur.fetchall()]
if 'associated_people' not in ordered_slugs:
    raise SystemExit('associated_people not found')
new_order = ['associated_people'] + [slug for slug in ordered_slugs if slug != 'associated_people']
for idx, slug in enumerate(new_order):
    cur.execute(
        "UPDATE attributes SET sort_order = %s WHERE object_id = %s AND slug = %s",
        (idx, object_id, slug),
    )

print('\nNew attribute order:')
cur.execute("SELECT slug, title, sort_order FROM attributes WHERE object_id = %s ORDER BY sort_order, created_at, slug", (object_id,))
for r in cur.fetchall():
    print(r)

# Reorder saved list/view columns so Person is visibly first in Deals table
cur.execute("SELECT id, name FROM lists WHERE object_id = %s ORDER BY created_at", (object_id,))
lists = cur.fetchall()
print('\nLists found:', lists)

for list_id, list_name in lists:
    cur.execute("SELECT slug FROM list_attributes WHERE list_id = %s ORDER BY sort_order, slug", (list_id,))
    list_slugs = [r[0] for r in cur.fetchall()]
    if not list_slugs:
        continue
    if 'associated_people' in list_slugs:
        reordered = ['associated_people'] + [slug for slug in list_slugs if slug != 'associated_people']
        for idx, slug in enumerate(reordered):
            cur.execute(
                "UPDATE list_attributes SET sort_order = %s WHERE list_id = %s AND slug = %s",
                (idx, list_id, slug),
            )
        print(f'Updated list order for {list_name}: {reordered}')

conn.commit()
cur.close()
conn.close()
print('\ndone')
