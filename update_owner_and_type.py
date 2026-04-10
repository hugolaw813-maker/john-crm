#!/usr/bin/env python3
"""
Update Owner fields to point to People list and add Broker/Prospect to People Type.
"""

import psycopg2
import json

WS_ID = '2d46eec2-03d1-4f93-9b96-356ec7afa757'

conn = psycopg2.connect(dbname='openclaw', user='jcw_l', host='/tmp')
cur = conn.cursor()

# Get People object ID
cur.execute("SELECT id FROM objects WHERE workspace_id = %s AND slug = 'people'", (WS_ID,))
people_obj_id = cur.fetchone()[0]
print('People object ID:', people_obj_id)

# 1. Add Broker and Prospect to People Type options
cur.execute("""
    SELECT config FROM attributes
    WHERE object_id = %s AND slug = 'type'
""", (people_obj_id,))
row = cur.fetchone()
if row:
    cfg = row[0] or {}
    if not isinstance(cfg, dict):
        try:
            cfg = json.loads(cfg)
        except:
            cfg = {}
    options = cfg.get('options', [])
    existing_values = {opt['value'] for opt in options}
    for label, value in [('Broker', 'broker'), ('Prospect', 'prospect')]:
        if value not in existing_values:
            options.append({'label': label, 'value': value})
            print(f'Added {label} to People Type')
    cfg['options'] = options
    cur.execute("""
        UPDATE attributes SET config = %s
        WHERE object_id = %s AND slug = 'type'
    """, (json.dumps(cfg), people_obj_id))

# 2. Update Owner fields to record_reference pointing to People
cur.execute("""
    SELECT o.slug, a.id
    FROM objects o
    JOIN attributes a ON a.object_id = o.id
    WHERE o.workspace_id = %s AND a.slug = 'owner'
""", (WS_ID,))
for obj_slug, attr_id in cur.fetchall():
    print(f'Updating {obj_slug}.owner to record_reference')
    new_config = {'targetObjectId': str(people_obj_id)}
    cur.execute("""
        UPDATE attributes
        SET type = 'record_reference', config = %s
        WHERE id = %s
    """, (json.dumps(new_config), attr_id))
    # Update list_attributes as well
    cur.execute("""
        UPDATE list_attributes
        SET type = 'record_reference', config = %s
        WHERE slug = 'owner' AND list_id IN (
            SELECT id FROM lists WHERE object_id = (
                SELECT id FROM objects WHERE workspace_id = %s AND slug = %s
            )
        )
    """, (json.dumps(new_config), WS_ID, obj_slug))

conn.commit()
cur.close()
conn.close()
print('Done')
