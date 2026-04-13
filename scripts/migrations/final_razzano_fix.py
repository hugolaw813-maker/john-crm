#!/usr/bin/env python3
"""
Final fix for all remaining Rozzano spelling
"""

import psycopg2
import json

PG_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
}

def fix_all():
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    print('=== FINAL RAZZANO SPELLING FIX ===')
    
    # Attribute IDs (from previous query)
    person_name_attr_id = '8b15f836-3184-4ab6-ae75-25e14efb324e'
    person_email_attr_id = 'd4e8cd8a-72df-45a9-8a77-21ae14999a82'
    company_name_attr_id = '423a6ea6-1f64-439c-9c78-9a17942eed30'
    
    # 1. Fix any remaining person names
    print('\n1. Checking person names...')
    cur.execute('''
        SELECT id, record_id, json_value
        FROM record_values 
        WHERE attribute_id = %s AND json_value::text ILIKE '%rozzano%'
    ''', (person_name_attr_id,))
    
    for rv_id, rec_id, name_data in cur.fetchall():
        if isinstance(name_data, dict):
            new_name = name_data.copy()
            if 'first_name' in new_name:
                new_name['first_name'] = new_name['first_name'].replace('Rozzano', 'Razzano').replace('rozzano', 'razzano')
            if 'last_name' in new_name:
                new_name['last_name'] = new_name['last_name'].replace('Rozzano', 'Razzano').replace('rozzano', 'razzano')
            if 'full_name' in new_name:
                new_name['full_name'] = new_name['full_name'].replace('Rozzano', 'Razzano').replace('rozzano', 'razzano')
            
            if new_name != name_data:
                cur.execute('''
                    UPDATE record_values
                    SET json_value = %s
                    WHERE id = %s
                ''', (json.dumps(new_name), rv_id))
                print(f'   Fixed person name: {name_data.get("full_name")} → {new_name.get("full_name")}')
    
    # 2. Fix person emails
    print('\n2. Checking person emails...')
    cur.execute('''
        SELECT id, record_id, json_value
        FROM record_values 
        WHERE attribute_id = %s AND json_value::text ILIKE '%rozzano%'
    ''', (person_email_attr_id,))
    
    for rv_id, rec_id, email_data in cur.fetchall():
        if isinstance(email_data, list):
            new_email = []
            changed = False
            for email_entry in email_data:
                if isinstance(email_entry, dict) and 'email_address' in email_entry:
                    old_email = email_entry['email_address']
                    new_email_addr = old_email.replace('rozzano', 'razzano').replace('Rozzano', 'Razzano')
                    if new_email_addr != old_email:
                        changed = True
                        new_entry = email_entry.copy()
                        new_entry['email_address'] = new_email_addr
                        new_email.append(new_entry)
                        print(f'   Fixed email: {old_email} → {new_email_addr}')
                    else:
                        new_email.append(email_entry)
                else:
                    new_email.append(email_entry)
            
            if changed:
                cur.execute('''
                    UPDATE record_values
                    SET json_value = %s
                    WHERE id = %s
                ''', (json.dumps(new_email), rv_id))
    
    # 3. Fix company names
    print('\n3. Checking company names...')
    cur.execute('''
        SELECT id, record_id, text_value
        FROM record_values 
        WHERE attribute_id = %s AND text_value ILIKE '%rozzano%'
    ''', (company_name_attr_id,))
    
    for rv_id, rec_id, company_name in cur.fetchall():
        new_name = company_name.replace('Rozzano', 'Razzano').replace('rozzano', 'razzano')
        if new_name != company_name:
            cur.execute('''
                UPDATE record_values
                SET text_value = %s
                WHERE id = %s
            ''', (new_name, rv_id))
            print(f'   Fixed company name: {company_name} → {new_name}')
    
    # 4. Fix company domains
    company_domains_attr_id = '237ff677-e6c3-4abe-b83b-6ae70bc2acf8'
    cur.execute('''
        SELECT id, record_id, json_value
        FROM record_values 
        WHERE attribute_id = %s AND json_value::text ILIKE '%rozzano%'
    ''', (company_domains_attr_id,))
    
    print('\n4. Checking company domains...')
    for rv_id, rec_id, domains_data in cur.fetchall():
        if isinstance(domains_data, list):
            new_domains = []
            changed = False
            for domain in domains_data:
                if isinstance(domain, str):
                    new_domain = domain.replace('rozzano', 'razzano').replace('Rozzano', 'Razzano')
                    if new_domain != domain:
                        changed = True
                        print(f'   Fixed domain: {domain} → {new_domain}')
                        new_domains.append(new_domain)
                    else:
                        new_domains.append(domain)
                else:
                    new_domains.append(domain)
            
            if changed:
                cur.execute('''
                    UPDATE record_values
                    SET json_value = %s
                    WHERE id = %s
                ''', (json.dumps(new_domains), rv_id))
    
    # 5. Fix notes
    print('\n5. Fixing notes...')
    cur.execute("SELECT id, title, content FROM notes WHERE title ILIKE '%roz%' OR content::text ILIKE '%roz%'")
    
    for note_id, title, content in cur.fetchall():
        # Fix title
        new_title = title.replace('Rozzano', 'Razzano').replace('rozzano', 'razzano')
        if new_title != title:
            cur.execute('UPDATE notes SET title = %s WHERE id = %s', (new_title, note_id))
            print(f'   Fixed note title: {title} → {new_title}')
        
        # Fix content if it's a dict
        if content and isinstance(content, dict):
            # Simple string replacement in dict
            import json
            content_str = json.dumps(content)
            if 'Rozzano' in content_str or 'rozzano' in content_str:
                new_content_str = content_str.replace('Rozzano', 'Razzano').replace('rozzano', 'razzano')
                new_content = json.loads(new_content_str)
                cur.execute('UPDATE notes SET content = %s WHERE id = %s', (json.dumps(new_content), note_id))
                print(f'   Fixed note content')
    
    # 6. Fix conversation records
    print('\n6. Fixing conversation records...')
    conv_obj_id = '9e4c7c56-c61d-4ee0-8e8b-c62771bec655'
    
    # Get conversation attribute IDs
    cur.execute('''
        SELECT slug, id FROM attributes 
        WHERE object_id = %s AND slug IN ('summary', 'details')
    ''', (conv_obj_id,))
    
    for slug, attr_id in cur.fetchall():
        cur.execute('''
            SELECT id, record_id, text_value
            FROM record_values 
            WHERE attribute_id = %s AND text_value ILIKE '%rozzano%'
        ''', (attr_id,))
        
        for rv_id, rec_id, text_val in cur.fetchall():
            new_text = text_val.replace('Rozzano', 'Razzano').replace('rozzano', 'razzano')
            if new_text != text_val:
                cur.execute('''
                    UPDATE record_values
                    SET text_value = %s
                    WHERE id = %s
                ''', (new_text, rv_id))
                print(f'   Fixed conversation {slug}: {text_val[:50]}...')
    
    conn.commit()
    cur.close()
    conn.close()
    
    print('\n✅ All fixes applied')

if __name__ == '__main__':
    fix_all()