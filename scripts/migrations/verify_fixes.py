#!/usr/bin/env python3
"""
Verify all Razzano fixes are correct
"""

import psycopg2

PG_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
}

def verify_fixes():
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    print('=== VERIFYING RAZZANO SPELLING FIXES ===')
    
    # 1. Check Person records
    print('\n1. PERSON RECORDS:')
    name_attr_id = '8b15f836-3184-4ab6-ae75-25e14efb324e'
    cur.execute('''
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN json_value::text ILIKE '%razzano%' THEN 1 END) as correct_spelling,
               COUNT(CASE WHEN json_value::text ILIKE '%rozzano%' THEN 1 END) as wrong_spelling
        FROM record_values 
        WHERE attribute_id = %s
    ''', (name_attr_id,))
    
    total, correct, wrong = cur.fetchone()
    print(f'   Total name records: {total}')
    print(f'   Correct spelling (Razzano): {correct}')
    print(f'   Wrong spelling (Rozzano): {wrong}')
    
    if wrong > 0:
        cur.execute('''
            SELECT record_id, json_value->>'full_name'
            FROM record_values 
            WHERE attribute_id = %s AND json_value::text ILIKE '%rozzano%'
        ''', (name_attr_id,))
        print('   Wrong records:')
        for rec_id, name in cur.fetchall():
            print(f'     {rec_id}: {name}')
    
    # Check Michael Razzano specifically
    cur.execute('''
        SELECT json_value->>'full_name', json_value->>'first_name', json_value->>'last_name'
        FROM record_values 
        WHERE attribute_id = %s AND json_value::text ILIKE '%michael%'
    ''', (name_attr_id,))
    
    print('\n   Michael Razzano records:')
    for full, first, last in cur.fetchall():
        print(f'     {full} (first: {first}, last: {last})')
    
    # 2. Check Company records
    print('\n2. COMPANY RECORDS:')
    company_obj_id = 'ff428b0d-3f1f-4b9e-a718-337fec03850f'
    cur.execute('''
        SELECT id FROM attributes 
        WHERE object_id = %s AND slug = 'name'
    ''', (company_obj_id,))
    
    result = cur.fetchone()
    if result:
        company_name_attr_id = result[0]
        cur.execute('''
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN text_value ILIKE '%razzano%' THEN 1 END) as correct_spelling,
                   COUNT(CASE WHEN text_value ILIKE '%rozzano%' THEN 1 END) as wrong_spelling
            FROM record_values 
            WHERE attribute_id = %s
        ''', (company_name_attr_id,))
        
        total, correct, wrong = cur.fetchone()
        print(f'   Total company name records: {total}')
        print(f'   Correct spelling (Razzano): {correct}')
        print(f'   Wrong spelling (Rozzano): {wrong}')
        
        if wrong > 0:
            cur.execute('''
                SELECT record_id, text_value
                FROM record_values 
                WHERE attribute_id = %s AND text_value ILIKE '%rozzano%'
            ''', (company_name_attr_id,))
            print('   Wrong company records:')
            for rec_id, name in cur.fetchall():
                print(f'     {rec_id}: {name}')
    
    # 3. Check Notes
    print('\n3. NOTES:')
    cur.execute("SELECT COUNT(*) FROM notes WHERE title ILIKE '%roz%' OR content::text ILIKE '%roz%'")
    wrong_notes = cur.fetchone()[0]
    print(f'   Notes with Rozzano spelling: {wrong_notes}')
    
    if wrong_notes > 0:
        cur.execute("SELECT id, title FROM notes WHERE title ILIKE '%roz%' OR content::text ILIKE '%roz%'")
        print('   Wrong notes:')
        for note_id, title in cur.fetchall():
            print(f'     {note_id}: {title}')
    
    # 4. Check Conversation records
    print('\n4. CONVERSATION RECORDS:')
    conv_obj_id = '9e4c7c56-c61d-4ee0-8e8b-c62771bec655'
    
    # Get conversation attribute IDs
    cur.execute('''
        SELECT slug, id FROM attributes 
        WHERE object_id = %s AND slug IN ('summary', 'details')
    ''', (conv_obj_id,))
    
    for slug, attr_id in cur.fetchall():
        cur.execute('''
            SELECT COUNT(*)
            FROM record_values 
            WHERE attribute_id = %s AND text_value ILIKE '%roz%'
        ''', (attr_id,))
        
        wrong_count = cur.fetchone()[0]
        print(f'   Conversation {slug} with Rozzano: {wrong_count}')
        
        if wrong_count > 0:
            cur.execute('''
                SELECT record_id, text_value
                FROM record_values 
                WHERE attribute_id = %s AND text_value ILIKE '%roz%'
            ''', (attr_id,))
            for rec_id, text in cur.fetchall():
                print(f'     {rec_id}: {text[:100]}...')
    
    cur.close()
    conn.close()
    
    print('\n=== SUMMARY ===')
    if wrong > 0 or wrong_notes > 0:
        print('❌ Some Rozzano spelling still needs fixing')
    else:
        print('✅ All Rozzano spelling has been corrected to Razzano')

if __name__ == '__main__':
    verify_fixes()