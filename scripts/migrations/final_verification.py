#!/usr/bin/env python3
"""
Final verification of all fixes
"""

import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    user='jcw_l',
    database='openclaw'
)
cur = conn.cursor()

john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'

print('=== FINAL VERIFICATION - JOHN\'S WORKSPACE ===')

print('\n1. OBJECTS (Sidebar Navigation):')
cur.execute('''
    SELECT slug, singular_name, plural_name
    FROM objects
    WHERE workspace_id = %s
    ORDER BY slug
''', (john_ws_id,))

for slug, singular, plural in cur.fetchall():
    print(f'  {slug}: {singular} ({plural})')
    
    # Check consistency
    if slug == singular.lower() + 's' or slug == plural.lower():
        print(f'    ✅ Slug matches display name')
    else:
        # Check common patterns
        if singular == 'Task' and plural == 'Tasks' and slug == 'tasks':
            print(f'    ✅ Tasks object - correct')
        elif singular == 'Person' and plural == 'People' and slug == 'people':
            print(f'    ✅ People object - correct (plural slug)')
        elif singular == 'Company' and plural == 'Companies' and slug == 'companies':
            print(f'    ✅ Companies object - correct (plural slug)')
        else:
            print(f'    ⚠️  Slug/name mismatch')

print('\n2. PERSON ATTRIBUTES:')
cur.execute('''
    SELECT a.slug, a.title, a.type
    FROM attributes a
    JOIN objects o ON a.object_id = o.id
    WHERE o.workspace_id = %s AND o.slug = 'people'
    ORDER BY a.slug
''', (john_ws_id,))

for slug, title, attr_type in cur.fetchall():
    print(f'  {slug}: {title} ({attr_type})')

print('\n3. TASK ATTRIBUTES (formerly Deals):')
cur.execute('''
    SELECT a.slug, a.title, a.type
    FROM attributes a
    JOIN objects o ON a.object_id = o.id
    WHERE o.workspace_id = %s AND o.slug = 'tasks'
    ORDER BY a.slug
''', (john_ws_id,))

for slug, title, attr_type in cur.fetchall():
    print(f'  {slug}: {title} ({attr_type})')

print('\n4. DATA COUNTS:')
# People count
cur.execute('''
    SELECT COUNT(*) FROM records r
    JOIN objects o ON r.object_id = o.id
    WHERE o.workspace_id = %s AND o.slug = 'people'
''', (john_ws_id,))
people = cur.fetchone()[0]

# Companies count
cur.execute('''
    SELECT COUNT(*) FROM records r
    JOIN objects o ON r.object_id = o.id
    WHERE o.workspace_id = %s AND o.slug = 'companies'
''', (john_ws_id,))
companies = cur.fetchone()[0]

# Tasks count
cur.execute('''
    SELECT COUNT(*) FROM records r
    JOIN objects o ON r.object_id = o.id
    WHERE o.workspace_id = %s AND o.slug = 'tasks'
''', (john_ws_id,))
tasks = cur.fetchone()[0]

print(f'  People: {people} clients')
print(f'  Companies/Households: {companies} records')
print(f'  Tasks: {tasks} items')

print('\n5. TYPE FIELD POPULATION:')
cur.execute('''
    SELECT COUNT(DISTINCT r.id) as total,
           COUNT(DISTINCT CASE WHEN rv.text_value = 'client' THEN r.id END) as clients
    FROM records r
    JOIN objects o ON r.object_id = o.id
    LEFT JOIN record_values rv ON r.id = rv.record_id
    LEFT JOIN attributes a ON rv.attribute_id = a.id AND a.slug = 'type'
    WHERE o.workspace_id = %s AND o.slug = 'people'
''', (john_ws_id,))

total, clients = cur.fetchone()
print(f'  Total people: {total}')
print(f'  Type = Client: {clients}')

cur.close()
conn.close()

print('\n✅ VERIFICATION COMPLETE')
print('\nExpected state:')
print('  • Sidebar: "Companies", "People", "Tasks"')
print('  • Person fields: "Company" (not "Household")')
print('  • Task fields: "Status" (not "Stage"), "Due Date" (not "Expected Close Date")')
print('  • All spelling: "Razzano" not "Rozzano"')
print('  • URLs: /companies, /people, /tasks')