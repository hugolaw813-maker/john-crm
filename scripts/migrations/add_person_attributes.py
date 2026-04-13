#!/usr/bin/env python3
"""
Add Type and Household attributes to Person object
"""

import psycopg2
import json
import uuid

PG_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
}

def add_person_attributes():
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    # Get Person object in John's workspace
    john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'
    
    cur.execute('''
        SELECT o.id, o.slug, o.singular_name, o.plural_name
        FROM objects o
        WHERE o.workspace_id = %s AND o.slug = 'people'
    ''', (john_ws_id,))
    
    person_obj = cur.fetchone()
    if not person_obj:
        print('ERROR: Person object not found in John\'s workspace')
        return
    
    person_id, slug, singular, plural = person_obj
    print(f'Person object: {singular} ({plural})')
    print(f'Object ID: {person_id}')
    
    # Check current attributes
    cur.execute('''
        SELECT slug, title, type
        FROM attributes
        WHERE object_id = %s
        ORDER BY slug
    ''', (person_id,))
    
    print('\nCurrent attributes:')
    existing_slugs = []
    for attr_slug, attr_title, attr_type in cur.fetchall():
        print(f'  {attr_slug}: {attr_title} ({attr_type})')
        existing_slugs.append(attr_slug)
    
    # 1. Add Type attribute (select)
    if 'type' in existing_slugs:
        print('\nType attribute already exists')
    else:
        type_attr_id = str(uuid.uuid4())
        type_config = {
            'options': [
                {'value': 'client', 'label': 'Client'},
                {'value': 'agent', 'label': 'Agent'},
                {'value': 'cio', 'label': 'CIO'},
                {'value': 'bni', 'label': 'BNI'},
                {'value': 'professional', 'label': 'Professional'},
                {'value': 'contact', 'label': 'Contact'}
            ]
        }
        
        cur.execute('''
            INSERT INTO attributes (id, object_id, slug, title, type, is_required, config, sort_order)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            type_attr_id,
            person_id,
            'type',
            'Type',
            'select',
            False,
            json.dumps(type_config),
            100  # Sort order (after name/email/phone)
        ))
        
        print(f'\n✅ Added Type attribute with {len(type_config["options"])} options')
    
    # 2. Add Household attribute (record_reference to Company)
    if 'household' in existing_slugs:
        print('\nHousehold attribute already exists')
    else:
        household_attr_id = str(uuid.uuid4())
        
        # Get Company object ID in same workspace
        cur.execute('''
            SELECT id FROM objects
            WHERE workspace_id = %s AND slug = 'companies'
        ''', (john_ws_id,))
        
        company_obj = cur.fetchone()
        if not company_obj:
            print('ERROR: Company object not found in workspace')
            return
        
        company_obj_id = company_obj[0]
        
        household_config = {
            'target_object_id': company_obj_id,
            'allow_multiple': False,
            'required': False
        }
        
        cur.execute('''
            INSERT INTO attributes (id, object_id, slug, title, type, is_required, config, sort_order)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            household_attr_id,
            person_id,
            'household',
            'Household',
            'record_reference',
            False,
            json.dumps(household_config),
            150  # Sort order
        ))
        
        print(f'✅ Added Household attribute (references Company object)')
    
    # 3. Also consider adding a household field to Company object if needed
    # (e.g., "Is Household" boolean or "Household Members" collection)
    
    # Verify additions
    print('\n=== VERIFYING ADDITIONS ===')
    cur.execute('''
        SELECT slug, title, type, config::text
        FROM attributes
        WHERE object_id = %s AND slug IN ('type', 'household')
    ''', (person_id,))
    
    for attr_slug, attr_title, attr_type, config in cur.fetchall():
        print(f'{attr_slug}: {attr_title} ({attr_type})')
        if config:
            try:
                config_data = json.loads(config)
                print(f'  Config: {config_data}')
            except:
                print(f'  Config: {config}')
    
    if 'type' in existing_slugs:
        print('\n⚠️ Type attribute already existed - checking if options are correct')
        # Could update existing attribute if options are wrong
    
    if 'household' in existing_slugs:
        print('\n⚠️ Household attribute already existed')
    
    conn.commit()
    cur.close()
    conn.close()
    
    print('\n✅ Done! Attributes added to Person object')

if __name__ == '__main__':
    add_person_attributes()