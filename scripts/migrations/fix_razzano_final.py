#!/usr/bin/env python3
"""
Final script to fix Razzano spelling in all Person and Company records
"""

import psycopg2
import json

PG_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
}

def fix_all_razzano():
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
    
    company_name_attr_row = cur.fetchone()
    if company_name_attr_row:
        company_name_attr_id = company_name_attr_row[1]
    else:
        print('ERROR: Could not find company name attribute')
        return
    
    # ===== 1. FIX PERSON RECORDS =====
    print('\n=== FIXING PERSON RECORDS ===')
    
    # Get all person records with name and email
    cur.execute('''
        SELECT r.id,
               (SELECT json_value FROM record_values WHERE record_id = r.id AND attribute_id = %s) as name,
               (SELECT json_value FROM record_values WHERE record_id = r.id AND attribute_id = %s) as email
        FROM records r
        WHERE r.object_id = %s
    ''', (person_attrs['name'], person_attrs['email_addresses'], person_obj_id))
    
    person_updates = []
    for rec_id, name_data, email_data in cur.fetchall():
        if not name_data:
            continue
            
        # Check if name contains wrong spelling
        name_str = json.dumps(name_data) if isinstance(name_data, dict) else str(name_data)
        if 'Rozzano' in name_str or 'rozzano' in name_str.lower():
            print(f'\nFound person record {rec_id}:')
            print(f'  Current name: {name_data}')
            print(f'  Current email: {email_data}')
            
            # Fix name
            if isinstance(name_data, dict):
                new_name = name_data.copy()
                # Update fields
                if 'first_name' in new_name:
                    new_name['first_name'] = new_name['first_name'].replace('Rozzano', 'Razzano').replace('rozzano', 'razzano')
                if 'last_name' in new_name:
                    new_name['last_name'] = new_name['last_name'].replace('Rozzano', 'Razzano').replace('rozzano', 'razzano')
                if 'full_name' in new_name:
                    new_name['full_name'] = new_name['full_name'].replace('Rozzano', 'Razzano').replace('rozzano', 'razzano')
                
                # Special case: "Rozzano Household" → "Michael Razzano"
                if name_data.get('full_name') == 'Rozzano Household':
                    new_name = {
                        'first_name': 'Michael',
                        'last_name': 'Razzano',
                        'full_name': 'Michael Razzano'
                    }
                    print('  Special case: Changing household name to individual Michael Razzano')
                
                # Special case: "Michael Rozzano and Henry Rozzano"
                if 'Michael Rozzano' in name_data.get('full_name', ''):
                    new_name = {
                        'first_name': 'Michael and Henry',
                        'last_name': 'Razzano',
                        'full_name': 'Michael Razzano and Henry Razzano'
                    }
                    print('  Special case: Fixing combined Michael & Henry record')
                
                person_updates.append(('name', rec_id, person_attrs['name'], json.dumps(new_name)))
                print(f'  New name: {new_name}')
            
            # Fix email
            if email_data and isinstance(email_data, list):
                new_email = []
                for email_entry in email_data:
                    if isinstance(email_entry, dict) and 'email_address' in email_entry:
                        old_email = email_entry['email_address']
                        new_email_addr = old_email.replace('rozzano', 'razzano').replace('Rozzano', 'Razzano')
                        new_entry = email_entry.copy()
                        new_entry['email_address'] = new_email_addr
                        new_email.append(new_entry)
                        print(f'  Email: {old_email} → {new_email_addr}')
                    else:
                        new_email.append(email_entry)
                person_updates.append(('email', rec_id, person_attrs['email_addresses'], json.dumps(new_email)))
    
    # Apply person updates
    for update_type, rec_id, attr_id, new_value in person_updates:
        cur.execute('''
            UPDATE record_values
            SET json_value = %s
            WHERE record_id = %s AND attribute_id = %s
        ''', (new_value, rec_id, attr_id))
        print(f'  Applied {update_type} update for record {rec_id}')
    
    # ===== 2. FIX COMPANY RECORDS =====
    print('\n=== FIXING COMPANY RECORDS ===')
    
    # Get all company records with name
    cur.execute('''
        SELECT r.id,
               (SELECT text_value FROM record_values WHERE record_id = r.id AND attribute_id = %s) as name
        FROM records r
        WHERE r.object_id = %s
    ''', (company_name_attr_id, company_obj_id))
    
    company_updates = []
    for rec_id, company_name in cur.fetchall():
        if not company_name:
            continue
            
        if 'Rozzano' in company_name or 'rozzano' in company_name.lower():
            print(f'\nFound company record {rec_id}:')
            print(f'  Current name: {company_name}')
            
            new_name = company_name.replace('Rozzano', 'Razzano').replace('rozzano', 'razzano')
            company_updates.append((rec_id, company_name_attr_id, new_name))
            print(f'  New name: {new_name}')
            
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
                ''', (rec_id, domains_attr_id))
                
                domains_row = cur.fetchone()
                if domains_row:
                    domains_rv_id, domains_json = domains_row
                    if domains_json and isinstance(domains_json, list):
                        new_domains = []
                        for domain in domains_json:
                            if isinstance(domain, str):
                                new_domain = domain.replace('rozzano', 'razzano').replace('Rozzano', 'Razzano')
                                new_domains.append(new_domain)
                            else:
                                new_domains.append(domain)
                        cur.execute('''
                            UPDATE record_values
                            SET json_value = %s
                            WHERE id = %s
                        ''', (json.dumps(new_domains), domains_rv_id))
                        print(f'  Updated domains to: {new_domains}')
    
    # Apply company name updates
    for rec_id, attr_id, new_name in company_updates:
        cur.execute('''
            UPDATE record_values
            SET text_value = %s
            WHERE record_id = %s AND attribute_id = %s
        ''', (new_name, rec_id, attr_id))
        print(f'  Applied company name update for record {rec_id}')
    
    # ===== 3. FIX CONVERSATION REFERENCES (Optional) =====
    print('\n=== NOTE: Conversation titles ===')
    print('Conversation records may still contain old spelling in titles.')
    print('To fix them, run a separate update on the notes table.')
    print('Let me know if you want those updated as well.')
    
    conn.commit()
    cur.close()
    conn.close()
    
    print('\n✅ ALL FIXES APPLIED')
    print(f'Updated {len(person_updates)} person records')
    print(f'Updated {len(company_updates)} company records')
    print('\nChanges include:')
    print('  • \"Rozzano Household\" → \"Michael Razzano\" (Person)')
    print('  • \"Michael Rozzano and Henry Rozzano\" → \"Michael Razzano and Henry Razzano\" (Person)')
    print('  • All other \"Rozzano\" spellings corrected to \"Razzano\"')
    print('  • Email addresses updated with correct spelling')

if __name__ == '__main__':
    fix_all_razzano()