#!/usr/bin/env python3
"""
Quick check of Razzano spelling
"""

import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    user='jcw_l',
    database='openclaw'
)
cur = conn.cursor()

print('=== QUICK CHECK ===')

# 1. Person names with raz/roz
name_attr_id = '8b15f836-3184-4ab6-ae75-25e14efb324e'
try:
    cur.execute('''
        SELECT record_id, json_value->>'full_name'
        FROM record_values 
        WHERE attribute_id = %s 
        AND (json_value::text ILIKE '%raz%' OR json_value::text ILIKE '%roz%')
    ''', (name_attr_id,))
    
    print('Person names with raz/roz:')
    for rec_id, name in cur.fetchall():
        print(f'  {rec_id}: {name}')
except Exception as e:
    print(f'Error checking person names: {e}')

# 2. Company names with raz/roz
company_obj_id = 'ff428b0d-3f1f-4b9e-a718-337fec03850f'
try:
    cur.execute('''
        SELECT id FROM attributes 
        WHERE object_id = %s AND slug = 'name'
    ''', (company_obj_id,))
    
    row = cur.fetchone()
    if row:
        company_name_attr_id = row[0]
        cur.execute('''
            SELECT record_id, text_value
            FROM record_values 
            WHERE attribute_id = %s 
            AND (text_value ILIKE '%raz%' OR text_value ILIKE '%roz%')
        ''', (company_name_attr_id,))
        
        print('\nCompany names with raz/roz:')
        for rec_id, name in cur.fetchall():
            print(f'  {rec_id}: {name}')
    else:
        print('\nCould not find company name attribute')
except Exception as e:
    print(f'Error checking company names: {e}')

# 3. Notes with roz
try:
    cur.execute("SELECT id, title FROM notes WHERE title ILIKE '%roz%' OR content::text ILIKE '%roz%'")
    print('\nNotes with roz:')
    for note_id, title in cur.fetchall():
        print(f'  {note_id}: {title}')
except Exception as e:
    print(f'Error checking notes: {e}')

cur.close()
conn.close()

print('\n=== DONE ===')