#!/usr/bin/env python3
"""
Fix Razzano spelling and correct Michael Razzano's name
"""

import psycopg2
import json

PG_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
}

def fix_spelling():
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    # Object IDs
    person_obj_id = '139d9239-39bb-49ca-99fe-18cbbb25ce55'
    company_obj_id = 'ff428b0d-3f1f-4b9e-a718-337fec03850f'
    
    # Get attribute IDs
    cur.execute('''
        SELECT slug, id FROM attributes 
        WHERE object_id = %s AND slug IN ('name', 'email_addresses')
    ''', (person_obj_id,))
    
    person_attrs = {row[0]: row[1] for row in cur.fetchall()}
    print(f'Person attribute IDs: {person_attrs}')
    
    cur.execute('''
        SELECT slug, id FROM attributes 
        WHERE object_id = %s AND slug = 'name'
    ''', (company_obj_id,))
    
    company_name_attr_id = cur.fetchone()[0]
    print(f'Company name attribute ID: {company_name_attr_id}')
    
    # 1. Fix Person: Rozzano Household → Michael Razzano
    print('\n=== FIXING PERSON: Rozzano Household → Michael Razzano ===')
    
    # Find person with email rozzano-household@example.com
    cur.execute('''
        SELECT rv.record_id, rv.json_value
        FROM record_values rv
        WHERE rv.attribute_id = %s
        AND rv.json_value::text LIKE '%rozzano-household@example.com%'
    ''', (person_attrs['email_addresses'],))
    
    person_email_rows = cur.fetchall()
    if not person_email_rows:
        print('Could not find person with email rozzano-household@example.com')
        # Try finding by name
        cur.execute('''
            SELECT rv.record_id, rv.json_value
            FROM record_values rv
            WHERE rv.attribute_id = %s
            AND rv.json_value::text LIKE '%Rozzano Household%'
        ''', (person_attrs['name'],))
        person_email_rows = cur.fetchall()
    
    for record_id, email_json in person_email_rows:
        print(f'Found person record: {record_id}')
        print(f'  Current email: {email_json}')
        
        # Update name
        cur.execute('''
            SELECT id, json_value
            FROM record_values
            WHERE record_id = %s AND attribute_id = %s
        ''', (record_id, person_attrs['name']))
        
        name_row = cur.fetchone()
        if name_row:
            name_rv_id, name_json = name_row
            new_name = {
                'first_name': 'Michael',
                'last_name': 'Razzano',
                'full_name': 'Michael Razzano'
            }
            cur.execute('''
                UPDATE record_values
                SET json_value = %s
                WHERE id = %s
            ''', (json.dumps(new_name), name_rv_id))
            print(f'  Updated name to: {new_name}')
        
        # Update email
        new_email = [{
            'email_address': 'michael-razzano@example.com',
            'email_address_type': 'work'
        }]
        cur.execute('''
            UPDATE record_values
            SET json_value = %s
            WHERE record_id = %s AND attribute_id = %s
        ''', (json.dumps(new_email), record_id, person_attrs['email_addresses']))
        print(f'  Updated email to: {new_email}')
    
    # 2. Fix Person: Michael Rozzano and Henry Rozzano → Michael Razzano and Henry Razzano
    print('\n=== FIXING PERSON: Michael Rozzano and Henry Rozzano ===')
    
    # Find by email michael-rozzano-and-henry-rozzano@example.com
    cur.execute('''
        SELECT rv.record_id, rv.json_value
        FROM record_values rv
        WHERE rv.attribute_id = %s
        AND rv.json_value::text LIKE '%michael-rozzano-and-henry-rozzano@example.com%'
    ''', (person_attrs['email_addresses'],))
    
    for record_id, email_json in cur.fetchall():
        print(f'Found combined person record: {record_id}')
        print(f'  Current email: {email_json}')
        
        # Update name - keep as combined but fix spelling
        cur.execute('''
            SELECT id, json_value
            FROM record_values
            WHERE record_id = %s AND attribute_id = %s
        ''', (record_id, person_attrs['name']))
        
        name_row = cur.fetchone()
        if name_row:
            name_rv_id, name_json = name_row
            new_name = {
                'first_name': 'Michael and Henry',
                'last_name': 'Razzano',
                'full_name': 'Michael Razzano and Henry Razzano'
            }
            cur.execute('''
                UPDATE record_values
                SET json_value = %s
                WHERE id = %s
            ''', (json.dumps(new_name), name_rv_id))
            print(f'  Updated name to: {new_name}')
        
        # Update email spelling
        new_email = [{
            'email_address': 'michael-razzano-and-henry-razzano@example.com',
            'email_address_type': 'work'
        }]
        cur.execute('''
            UPDATE record_values
            SET json_value = %s
            WHERE record_id = %s AND attribute_id = %s
        ''', (json.dumps(new_email), record_id, person_attrs['email_addresses']))
        print(f'  Updated email to: {new_email}')
    
    # 3. Fix Company: Rozzano Household → Razzano Household
    print('\n=== FIXING COMPANY: Rozzano Household → Razzano Household ===')
    
    cur.execute('''
        SELECT rv.id, rv.record_id, rv.text_value
        FROM record_values rv
        WHERE rv.attribute_id = %s
        AND rv.text_value ILIKE '%roz%'
    ''', (company_name_attr_id,))
    
    for rv_id, record_id, company_name in cur.fetchall():
        print(f'Found company record: {record_id}')
        print(f'  Current name: {company_name}')
        
        # Fix spelling
        new_name = company_name.replace('Rozzano', 'Razzano').replace('rozzano', 'razzano')
        cur.execute('''
            UPDATE record_values
            SET text_value = %s
            WHERE id = %s
        ''', (new_name, rv_id))
        print(f'  Updated to: {new_name}')
        
        # Also fix domains attribute if exists
        cur.execute('''
            SELECT id FROM attributes 
            WHERE object_id = %s AND slug = 'domains'
        ''', (company_obj_id,))
        
        domains_attr = cur.fetchone()
        if domains_attr:
            domains_attr_id = domains_attr[0]
            cur.execute('''
                SELECT id, json_value
                FROM record_values
                WHERE record_id = %s AND attribute_id = %s
            ''', (record_id, domains_attr_id))
            
            domains_row = cur.fetchone()
            if domains_row:
                domains_rv_id, domains_json = domains_row
                if domains_json and isinstance(domains_json, list):
                    new_domains = []
                    for domain in domains_json:
                        if isinstance(domain, str):
                            new_domain = domain.replace('rozzano', 'razzano')
                            new_domains.append(new_domain)
                        else:
                            new_domains.append(domain)
                    cur.execute('''
                        UPDATE record_values
                        SET json_value = %s
                        WHERE id = %s
                    ''', (json.dumps(new_domains), domains_rv_id))
                    print(f'  Updated domains to: {new_domains}')
    
    # 4. Fix Conversation references
    print('\n=== FIXING CONVERSATION REFERENCES ===')
    # Update any conversation summaries/titles with wrong spelling
    # This would require updating the notes table or conversation records
    # For now, just note that conversation titles may still have old spelling
    # We can fix them separately if needed
    
    conn.commit()
    cur.close()
    conn.close()
    
    print('\n✅ Spelling fixes applied')
    print('\nSummary of changes:')
    print('  1. Person \"Rozzano Household\" → \"Michael Razzano\"')
    print('  2. Person \"Michael Rozzano and Henry Rozzano\" → \"Michael Razzano and Henry Razzano\"')
    print('  3. Company \"Rozzano Household\" → \"Razzano Household\"')
    print('  4. Emails updated with correct spelling')
    print('\nNote: Conversation titles may still contain old spelling.')
    print('      Let me know if you want those updated as well.')

if __name__ == '__main__':
    fix_spelling()