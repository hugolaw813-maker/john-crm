#!/usr/bin/env python3
"""
Fix Person name attribute JSON structure to match expected format:
Change {given_name, family_name, full_name} → {first_name, last_name, full_name}
"""

import psycopg2
import json

PG_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
}

def fix_person_names():
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    person_obj_id = '139d9239-39bb-49ca-99fe-18cbbb25ce55'
    
    # Get name attribute ID
    cur.execute('''
        SELECT id FROM attributes 
        WHERE object_id = %s AND slug = 'name'
    ''', (person_obj_id,))
    
    name_attr_id = cur.fetchone()[0]
    print(f'Name attribute ID: {name_attr_id}')
    
    # Get all name values
    cur.execute('''
        SELECT rv.id, rv.json_value
        FROM record_values rv
        WHERE rv.attribute_id = %s
    ''', (name_attr_id,))
    
    updates = []
    for rv_id, json_val in cur.fetchall():
        if json_val and isinstance(json_val, dict):
            # Check if it has given_name/family_name
            if 'given_name' in json_val or 'family_name' in json_val:
                # Transform to first_name/last_name
                new_json = {
                    'first_name': json_val.get('given_name', ''),
                    'last_name': json_val.get('family_name', ''),
                    'full_name': json_val.get('full_name', '')
                }
                # Ensure full_name exists
                if not new_json['full_name']:
                    new_json['full_name'] = f"{new_json['first_name']} {new_json['last_name']}".strip()
                
                updates.append((rv_id, new_json))
    
    print(f'Found {len(updates)} name records to fix')
    
    # Apply updates
    fixed_count = 0
    for rv_id, new_json in updates:
        cur.execute('''
            UPDATE record_values
            SET json_value = %s
            WHERE id = %s
        ''', (json.dumps(new_json), rv_id))
        fixed_count += 1
    
    conn.commit()
    print(f'Fixed {fixed_count} name records')
    
    # Verify fixes
    print('\nVerifying fixes...')
    cur.execute('''
        SELECT json_value->>'first_name', json_value->>'last_name', json_value->>'full_name'
        FROM record_values
        WHERE attribute_id = %s
        LIMIT 5
    ''', (name_attr_id,))
    
    print('Sample fixed names:')
    for first, last, full in cur.fetchall():
        print(f'  {first} {last} ({full})')
    
    # Check if any still have wrong keys
    cur.execute('''
        SELECT COUNT(*) 
        FROM record_values 
        WHERE attribute_id = %s 
        AND (json_value::text LIKE '%given_name%' OR json_value::text LIKE '%family_name%')
    ''', (name_attr_id,))
    
    remaining_wrong = cur.fetchone()[0]
    print(f'Remaining records with wrong keys: {remaining_wrong}')
    
    cur.close()
    conn.close()
    
    return fixed_count

def check_email_phone_format():
    """Check if email/phone formats need fixing"""
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    person_obj_id = '139d9239-39bb-49ca-99fe-18cbbb25ce55'
    
    # Get attribute IDs
    cur.execute('''
        SELECT slug, id, type FROM attributes 
        WHERE object_id = %s AND slug IN ('email_addresses', 'phone_numbers')
    ''', (person_obj_id,))
    
    attrs = cur.fetchall()
    print('\nChecking email/phone formats...')
    
    for slug, attr_id, attr_type in attrs:
        cur.execute('''
            SELECT COUNT(*)
            FROM record_values
            WHERE attribute_id = %s AND json_value IS NOT NULL
        ''', (attr_id,))
        
        json_count = cur.fetchone()[0]
        
        cur.execute('''
            SELECT COUNT(*)
            FROM record_values
            WHERE attribute_id = %s AND text_value IS NOT NULL
        ''', (attr_id,))
        
        text_count = cur.fetchone()[0]
        
        print(f'{slug} ({attr_type}): JSON values={json_count}, Text values={text_count}')
    
    cur.close()
    conn.close()

def main():
    print('=== FIXING PERSON NAME ATTRIBUTES ===')
    print('Changing given_name/family_name → first_name/last_name')
    
    fixed = fix_person_names()
    check_email_phone_format()
    
    print(f'\n✅ Fixed {fixed} person name records')
    print('\n🌐 Test in CRM:')
    print('   1. Log in at http://172.31.153.173:3001')
    print('   2. Go to People workspace')
    print('   3. Check if names now display correctly')
    print('   4. Try searching for client names')

if __name__ == '__main__':
    main()