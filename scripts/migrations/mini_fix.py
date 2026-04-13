#!/usr/bin/env python3
import psycopg2
import json

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    user='jcw_l',
    database='openclaw'
)
cur = conn.cursor()

print('Fixing remaining Rozzano spelling...')

# 1. Fix note title
cur.execute("UPDATE notes SET title = REPLACE(REPLACE(title, 'Rozzano', 'Razzano'), 'rozzano', 'razzano') WHERE title ILIKE '%roz%'")
print(f'Fixed {cur.rowcount} note titles')

# 2. Fix note content (JSON)
cur.execute("SELECT id, content FROM notes WHERE content::text ILIKE '%roz%'")
for note_id, content in cur.fetchall():
    if content and isinstance(content, dict):
        content_str = json.dumps(content)
        if 'Rozzano' in content_str or 'rozzano' in content_str:
            new_str = content_str.replace('Rozzano', 'Razzano').replace('rozzano', 'razzano')
            new_content = json.loads(new_str)
            cur.execute('UPDATE notes SET content = %s WHERE id = %s', (json.dumps(new_content), note_id))
            print(f'Fixed note {note_id} content')

# 3. Check person names (should already be fixed)
name_attr_id = '8b15f836-3184-4ab6-ae75-25e14efb324e'
cur.execute('''
    SELECT COUNT(*) FROM record_values 
    WHERE attribute_id = %s AND json_value::text ILIKE '%rozzano%'
''', (name_attr_id,))
wrong_person = cur.fetchone()[0]
print(f'Person names still wrong: {wrong_person}')

if wrong_person > 0:
    cur.execute('''
        SELECT id, json_value FROM record_values 
        WHERE attribute_id = %s AND json_value::text ILIKE '%rozzano%'
    ''', (name_attr_id,))
    for rv_id, name_data in cur.fetchall():
        if isinstance(name_data, dict):
            new_name = name_data.copy()
            for key in ['first_name', 'last_name', 'full_name']:
                if key in new_name and isinstance(new_name[key], str):
                    new_name[key] = new_name[key].replace('Rozzano', 'Razzano').replace('rozzano', 'razzano')
            cur.execute('UPDATE record_values SET json_value = %s WHERE id = %s', (json.dumps(new_name), rv_id))
            print(f'Fixed person name: {name_data.get("full_name")}')

# 4. Check company names
company_name_attr_id = '423a6ea6-1f64-439c-9c78-9a17942eed30'
cur.execute('''
    SELECT COUNT(*) FROM record_values 
    WHERE attribute_id = %s AND text_value ILIKE '%rozzano%'
''', (company_name_attr_id,))
wrong_company = cur.fetchone()[0]
print(f'Company names still wrong: {wrong_company}')

if wrong_company > 0:
    cur.execute('''
        SELECT id, text_value FROM record_values 
        WHERE attribute_id = %s AND text_value ILIKE '%rozzano%'
    ''', (company_name_attr_id,))
    for rv_id, name in cur.fetchall():
        new_name = name.replace('Rozzano', 'Razzano').replace('rozzano', 'razzano')
        cur.execute('UPDATE record_values SET text_value = %s WHERE id = %s', (new_name, rv_id))
        print(f'Fixed company name: {name}')

# 5. Conversation summaries/details
conv_obj_id = '9e4c7c56-c61d-4ee0-8e8b-c62771bec655'
cur.execute('''
    SELECT slug, id FROM attributes 
    WHERE object_id = %s AND slug IN ('summary', 'details')
''', (conv_obj_id,))
for slug, attr_id in cur.fetchall():
    cur.execute('''
        SELECT COUNT(*) FROM record_values 
        WHERE attribute_id = %s AND text_value ILIKE '%rozzano%'
    ''', (attr_id,))
    wrong = cur.fetchone()[0]
    print(f'Conversation {slug} still wrong: {wrong}')
    
    if wrong > 0:
        cur.execute('''
            UPDATE record_values
            SET text_value = REPLACE(REPLACE(text_value, 'Rozzano', 'Razzano'), 'rozzano', 'razzano')
            WHERE attribute_id = %s AND text_value ILIKE '%rozzano%'
        ''', (attr_id,))
        print(f'Fixed {cur.rowcount} conversation {slug} records')

conn.commit()
cur.close()
conn.close()
print('\n✅ Done')