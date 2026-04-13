#!/usr/bin/env python3
"""
Verify Person attribute changes
"""

import psycopg2

PG_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
}

def verify():
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'
    
    print('=== PERSON ATTRIBUTES IN JOHN\'S WORKSPACE ===')
    cur.execute('''
        SELECT a.slug, a.title, a.type
        FROM attributes a
        JOIN objects o ON a.object_id = o.id
        WHERE o.workspace_id = %s AND o.slug = 'people'
        ORDER BY a.slug
    ''', (john_ws_id,))
    
    for slug, title, attr_type in cur.fetchall():
        print(f'  {slug}: {title} ({attr_type})')
    
    print('\n=== PERSON RECORDS WITH TYPE ===')
    cur.execute('''
        SELECT COUNT(DISTINCT r.id) as total,
               COUNT(DISTINCT CASE WHEN rv.text_value = 'client' THEN r.id END) as clients,
               COUNT(DISTINCT CASE WHEN rv.text_value IS NOT NULL AND rv.text_value != 'client' THEN r.id END) as other_types
        FROM records r
        JOIN objects o ON r.object_id = o.id
        LEFT JOIN record_values rv ON r.id = rv.record_id
        LEFT JOIN attributes a ON rv.attribute_id = a.id AND a.slug = 'type'
        WHERE o.workspace_id = %s AND o.slug = 'people'
    ''', (john_ws_id,))
    
    total, clients, other = cur.fetchone()
    print(f'Total people: {total}')
    print(f'Type = Client: {clients}')
    print(f'Other types: {other}')
    
    print('\n=== HOUSEHOLD LINKS ===')
    # Count people linked to companies (households)
    cur.execute('''
        SELECT COUNT(DISTINCT r.id)
        FROM records r
        JOIN objects o ON r.object_id = o.id
        JOIN record_values rv ON r.id = rv.record_id
        JOIN attributes a ON rv.attribute_id = a.id AND a.slug = 'company'
        WHERE o.workspace_id = %s AND o.slug = 'people'
        AND rv.record_id IS NOT NULL
    ''', (john_ws_id,))
    
    linked = cur.fetchone()[0]
    print(f'People linked to households: {linked}/{total}')
    
    print('\n=== SAMPLE PEOPLE WITH TYPE AND HOUSEHOLD ===')
    cur.execute('''
        SELECT 
            name_rv.json_value->>'full_name' as name,
            type_rv.text_value as type,
            household_rv.record_id as household_id,
            comp_name.text_value as household_name
        FROM records r
        JOIN record_values name_rv ON r.id = name_rv.record_id
        JOIN attributes name_attr ON name_rv.attribute_id = name_attr.id AND name_attr.slug = 'name'
        LEFT JOIN record_values type_rv ON r.id = type_rv.record_id
        LEFT JOIN attributes type_attr ON type_rv.attribute_id = type_attr.id AND type_attr.slug = 'type'
        LEFT JOIN record_values household_rv ON r.id = household_rv.record_id
        LEFT JOIN attributes household_attr ON household_rv.attribute_id = household_attr.id AND household_attr.slug = 'company'
        LEFT JOIN records comp ON household_rv.record_id = comp.id
        LEFT JOIN record_values comp_name ON comp.id = comp_name.record_id
        LEFT JOIN attributes comp_name_attr ON comp_name.attribute_id = comp_name_attr.id AND comp_name_attr.slug = 'name'
        WHERE r.object_id = (SELECT id FROM objects WHERE workspace_id = %s AND slug = 'people')
        LIMIT 10
    ''', (john_ws_id,))
    
    for name, type_val, household_id, household_name in cur.fetchall():
        household_display = f'{household_name} ({household_id})' if household_name else 'None'
        print(f'  {name}: Type={type_val}, Household={household_display}')
    
    print('\n=== COMPANY OBJECT (HOUSEHOLDS) ===')
    cur.execute('''
        SELECT COUNT(*) FROM records r
        JOIN objects o ON r.object_id = o.id
        WHERE o.workspace_id = %s AND o.slug = 'companies'
    ''', (john_ws_id,))
    
    companies = cur.fetchone()[0]
    print(f'Total company/household records: {companies}')
    
    # Sample company names
    cur.execute('''
        SELECT rv.text_value
        FROM records r
        JOIN objects o ON r.object_id = o.id
        JOIN record_values rv ON r.id = rv.record_id
        JOIN attributes a ON rv.attribute_id = a.id AND a.slug = 'name'
        WHERE o.workspace_id = %s AND o.slug = 'companies'
        LIMIT 5
    ''', (john_ws_id,))
    
    print('Sample households:')
    for name in cur.fetchall():
        print(f'  {name[0]}')
    
    cur.close()
    conn.close()
    
    print('\n✅ Verification complete')

if __name__ == '__main__':
    verify()