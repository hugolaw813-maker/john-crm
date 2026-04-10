#!/usr/bin/env python3
import psycopg2
import uuid
import re

WS_ID = '2d46eec2-03d1-4f93-9b96-356ec7afa757'

def norm(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', (s or '').lower())

conn = psycopg2.connect(dbname='openclaw', user='jcw_l', host='/tmp')
cur = conn.cursor()

# Object ids
cur.execute("SELECT id FROM objects WHERE workspace_id = %s AND slug = 'companies'", (WS_ID,))
companies_obj_id = cur.fetchone()[0]
cur.execute("SELECT id FROM objects WHERE workspace_id = %s AND slug = 'people'", (WS_ID,))
people_obj_id = cur.fetchone()[0]

# Rename Companies object -> Groups
cur.execute("UPDATE objects SET singular_name = 'Group', plural_name = 'Groups' WHERE id = %s", (companies_obj_id,))
print('Renamed object Companies -> Groups')

# Attributes
cur.execute("SELECT id FROM attributes WHERE object_id = %s AND slug = 'name'", (companies_obj_id,))
companies_name_attr_id = cur.fetchone()[0]
cur.execute("UPDATE attributes SET title = 'Group' WHERE id = %s", (companies_name_attr_id,))
print('Renamed companies.name title -> Group')

cur.execute("SELECT id FROM attributes WHERE object_id = %s AND slug = 'company'", (people_obj_id,))
people_company_attr_id = cur.fetchone()[0]
cur.execute("UPDATE attributes SET title = 'Group' WHERE id = %s", (people_company_attr_id,))
print('Renamed people.company title -> Group')

cur.execute("SELECT id FROM attributes WHERE object_id = %s AND slug = 'household'", (people_obj_id,))
people_household_attr_id = cur.fetchone()[0]
cur.execute("UPDATE attributes SET title = 'Group' WHERE id = %s", (people_household_attr_id,))
print('Renamed people.household title -> Group')

# Update saved list titles where relevant
cur.execute("UPDATE list_attributes SET title = 'Group' WHERE slug = 'name' AND list_id IN (SELECT id FROM lists WHERE object_id = %s)", (companies_obj_id,))
cur.execute("UPDATE list_attributes SET title = 'Group' WHERE slug = 'company' AND list_id IN (SELECT id FROM lists WHERE object_id = %s)", (people_obj_id,))
cur.execute("UPDATE list_attributes SET title = 'Group' WHERE slug = 'household' AND list_id IN (SELECT id FROM lists WHERE object_id = %s)", (people_obj_id,))

# Load existing groups
cur.execute('''
SELECT r.id, COALESCE(rv.text_value, rv.json_value->>'full_name') AS name
FROM records r
JOIN record_values rv ON rv.record_id = r.id
JOIN attributes a ON a.id = rv.attribute_id
WHERE r.object_id = %s AND a.id = %s
''', (companies_obj_id, companies_name_attr_id))
groups = cur.fetchall()
group_by_norm = {norm(name): (rid, name) for rid, name in groups if name}
print(f'Loaded {len(group_by_norm)} existing groups')

# Find people household text values
cur.execute('''
SELECT id, record_id, text_value
FROM record_values
WHERE attribute_id = %s AND text_value IS NOT NULL AND text_value <> ''
''', (people_household_attr_id,))
household_rows = cur.fetchall()
print(f'Found {len(household_rows)} People.household text rows')

created = 0
linked = 0
for row_id, person_record_id, household_text in household_rows:
    key = norm(household_text)
    match = group_by_norm.get(key)

    if not match:
        matches = []
        for gkey, info in group_by_norm.items():
            if key and (key in gkey or gkey in key):
                matches.append(info)
        if len(matches) == 1:
            match = matches[0]

    if not match:
        new_group_id = str(uuid.uuid4())
        cur.execute("INSERT INTO records (id, object_id) VALUES (%s, %s)", (new_group_id, companies_obj_id))
        cur.execute(
            "INSERT INTO record_values (id, record_id, attribute_id, text_value, sort_order) VALUES (%s, %s, %s, %s, 0)",
            (str(uuid.uuid4()), new_group_id, companies_name_attr_id, household_text),
        )
        match = (new_group_id, household_text)
        group_by_norm[key] = match
        created += 1
        print(f'Created Group: {household_text}')

    group_id, group_name = match

    # if people.company relation missing, create it
    cur.execute('''
    SELECT 1 FROM record_values
    WHERE record_id = %s AND attribute_id = %s AND referenced_record_id = %s
    ''', (person_record_id, people_company_attr_id, group_id))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO record_values (id, record_id, attribute_id, referenced_record_id, sort_order) VALUES (%s, %s, %s, %s, 0)",
            (str(uuid.uuid4()), person_record_id, people_company_attr_id, group_id),
        )
        linked += 1
        print(f'Linked person {person_record_id} -> Group {group_name}')

print(f'Created groups: {created}')
print(f'Linked people to groups: {linked}')

conn.commit()
cur.close()
conn.close()
print('done')
