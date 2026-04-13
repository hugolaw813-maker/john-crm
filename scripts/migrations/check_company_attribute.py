#!/usr/bin/env python3
"""
Check company attribute config on Person object
"""

import psycopg2
import json

PG_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
}

def check():
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    # Get Person object in John's workspace
    john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'
    
    cur.execute('''
        SELECT o.id FROM objects o
        WHERE o.workspace_id = %s AND o.slug = 'people'
    ''', (john_ws_id,))
    
    person_id = cur.fetchone()[0]
    
    # Get company attribute details
    cur.execute('''
        SELECT slug, title, type, config, is_required
        FROM attributes
        WHERE object_id = %s AND slug = 'company'
    ''', (person_id,))
    
    attr = cur.fetchone()
    if attr:
        slug, title, attr_type, config, is_required = attr
        print(f'Company attribute: {title} ({attr_type})')
        print(f'Required: {is_required}')
        print(f'Config: {config}')
        
        if config:
            try:
                if isinstance(config, dict):
                    config_data = config
                else:
                    config_data = json.loads(config)
                print('Parsed config:')
                for key, value in config_data.items():
                    print(f'  {key}: {value}')
            except:
                print(f'Raw config: {config}')
    
    # Check if type attribute exists
    cur.execute('''
        SELECT slug, title, type FROM attributes
        WHERE object_id = %s AND slug = 'type'
    ''', (person_id,))
    
    type_attr = cur.fetchone()
    if type_attr:
        print(f'\nType attribute already exists: {type_attr}')
    else:
        print('\nType attribute does not exist')
    
    # Check if household attribute exists
    cur.execute('''
        SELECT slug, title, type FROM attributes
        WHERE object_id = %s AND slug = 'household'
    ''', (person_id,))
    
    household_attr = cur.fetchone()
    if household_attr:
        print(f'\nHousehold attribute already exists: {household_attr}')
    else:
        print('\nHousehold attribute does not exist')
    
    # Check actual data: how many people linked to companies?
    cur.execute('''
        SELECT COUNT(DISTINCT rv.record_id)
        FROM record_values rv
        JOIN attributes a ON rv.attribute_id = a.id
        WHERE a.object_id = %s AND a.slug = 'company'
        AND rv.record_id IS NOT NULL
    ''', (person_id,))
    
    linked_count = cur.fetchone()[0]
    print(f'\nPeople linked to companies: {linked_count}')
    
    # Sample links
    cur.execute('''
        SELECT rv.record_id as person_id, rv.record_reference_value as company_id
        FROM record_values rv
        JOIN attributes a ON rv.attribute_id = a.id
        WHERE a.object_id = %s AND a.slug = 'company'
        AND rv.record_reference_value IS NOT NULL
        LIMIT 5
    ''', (person_id,))
    
    print('\nSample person→company links:')
    for person_id, company_id in cur.fetchall():
        print(f'  Person {person_id} → Company {company_id}')
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    check()