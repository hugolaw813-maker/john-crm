#!/usr/bin/env python3
"""
Examine the 11 task records in our custom object
"""

import psycopg2
import json

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    user='jcw_l',
    database='openclaw'
)
cur = conn.cursor()

john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'

# Get the tasks object (our custom object, slug='tasks' after rename)
cur.execute('''
    SELECT id FROM objects
    WHERE workspace_id = %s AND slug = 'tasks'
''', (john_ws_id,))

tasks_obj_id = cur.fetchone()[0]
print(f'Custom Tasks object ID: {tasks_obj_id}')

# Get all records in this object
cur.execute('''
    SELECT id, created_at FROM records
    WHERE object_id = %s
    ORDER BY created_at
''', (tasks_obj_id,))

record_ids = [row[0] for row in cur.fetchall()]
print(f'Found {len(record_ids)} records')

# Get attribute IDs for this object
cur.execute('''
    SELECT slug, id, type FROM attributes
    WHERE object_id = %s
    ORDER BY slug
''', (tasks_obj_id,))

attrs = {}
for slug, attr_id, attr_type in cur.fetchall():
    attrs[slug] = (attr_id, attr_type)

print('\nAttributes:')
for slug, (attr_id, attr_type) in attrs.items():
    print(f'  {slug}: {attr_type} (id: {attr_id})')

# Examine first 3 records in detail
print('\n=== SAMPLE RECORDS (first 3) ===')
for i, record_id in enumerate(record_ids[:3]):
    print(f'\nRecord {record_id}:')
    
    # Get all values for this record
    cur.execute('''
        SELECT a.slug, a.type, 
               rv.text_value, rv.number_value, rv.json_value, rv.date_value, rv.record_id as ref_id
        FROM record_values rv
        JOIN attributes a ON rv.attribute_id = a.id
        WHERE rv.record_id = %s
        ORDER BY a.slug
    ''', (record_id,))
    
    for slug, attr_type, text_val, num_val, json_val, date_val, ref_id in cur.fetchall():
        value = None
        if text_val is not None:
            value = f'text: {text_val}'
        elif num_val is not None:
            value = f'number: {num_val}'
        elif json_val is not None:
            value = f'json: {json_val}'
        elif date_val is not None:
            value = f'date: {date_val}'
        elif ref_id is not None:
            value = f'ref: {ref_id}'
        
        print(f'  {slug}: {value}')

# Check what stage values exist
print('\n=== STAGE/STATUS DISTRIBUTION ===')
if 'stage' in attrs:
    stage_attr_id = attrs['stage'][0]
    cur.execute('''
        SELECT rv.text_value, COUNT(*)
        FROM record_values rv
        WHERE rv.attribute_id = %s
        GROUP BY rv.text_value
        ORDER BY COUNT(*) DESC
    ''', (stage_attr_id,))
    
    for stage, count in cur.fetchall():
        print(f'  {stage}: {count}')

# Check value field distribution
print('\n=== VALUE FIELD ===')
if 'value' in attrs:
    value_attr_id = attrs['value'][0]
    cur.execute('''
        SELECT MIN(rv.number_value), MAX(rv.number_value), AVG(rv.number_value)
        FROM record_values rv
        WHERE rv.attribute_id = %s AND rv.number_value IS NOT NULL
    ''', (value_attr_id,))
    
    min_val, max_val, avg_val = cur.fetchone()
    print(f'  Min: {min_val}, Max: {max_val}, Avg: {avg_val}')

cur.close()
conn.close()

print('\n=== ANALYSIS ===')
print('These records have:')
print('  • name (text) - task title')
print('  • stage (text) - status (Todo, In Progress, etc.)')
print('  • value (number) - currency amount')
print('  • expected_close_date (date) - due date')
print('  • company (reference) - linked company')
print('  • associated_people (reference) - linked people')
print('  • owner (actor_reference) - assigned user')
print('\nBuilt-in tasks have:')
print('  • content (text) - task description')
print('  • deadline (date) - due date')
print('  • is_completed (boolean) - done status')
print('  • assignees (users)')
print('  • linked_records (references)')
print('\nMapping would lose: stage pipeline, value amount, specific owner field')