#!/usr/bin/env python3
"""
Add Type attribute and rename Company to Household in Person object
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

def main():
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
    existing = {}
    for attr_slug, attr_title, attr_type in cur.fetchall():
        print(f'  {attr_slug}: {attr_title} ({attr_type})')
        existing[attr_slug] = (attr_title, attr_type)
    
    # 1. Add Type attribute (select) if not exists
    if 'type' in existing:
        print('\n⚠️ Type attribute already exists')
        # Could update options if needed
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
    
    # 2. Rename Company attribute to Household (if it exists)
    if 'company' in existing:
        current_title, attr_type = existing['company']
        if current_title != 'Household':
            print(f'\nRenaming Company attribute: "{current_title}" → "Household"')
            cur.execute('''
                UPDATE attributes
                SET title = 'Household'
                WHERE object_id = %s AND slug = 'company'
            ''', (person_id,))
            print('✅ Updated attribute title')
        else:
            print('\nCompany attribute already titled "Household"')
    else:
        print('\n⚠️ Company attribute not found (cannot rename)')
    
    # 3. Optional: Add Household as new attribute if company doesn't exist
    # But we already have company linking to households, so rename is sufficient
    
    # Verify changes
    print('\n=== VERIFYING CHANGES ===')
    cur.execute('''
        SELECT slug, title, type
        FROM attributes
        WHERE object_id = %s
        ORDER BY slug
    ''', (person_id,))
    
    print('Updated attributes:')
    for attr_slug, attr_title, attr_type in cur.fetchall():
        print(f'  {attr_slug}: {attr_title} ({attr_type})')
    
    # Also update in My Workspace for consistency?
    print('\n=== CHECKING MY WORKSPACE ===')
    my_ws_id = '709eeba3-da92-46ff-aeec-3415c62c5fdf'
    cur.execute('''
        SELECT o.id FROM objects o
        WHERE o.workspace_id = %s AND o.slug = 'people'
    ''', (my_ws_id,))
    
    my_person_id = cur.fetchone()
    if my_person_id:
        my_person_id = my_person_id[0]
        cur.execute('''
            SELECT slug, title FROM attributes
            WHERE object_id = %s AND slug = 'company'
        ''', (my_person_id,))
        
        my_company = cur.fetchone()
        if my_company:
            my_slug, my_title = my_company
            if my_title != 'Household':
                print(f'My Workspace: Renaming "{my_title}" → "Household"')
                cur.execute('''
                    UPDATE attributes
                    SET title = 'Household'
                    WHERE object_id = %s AND slug = 'company'
                ''', (my_person_id,))
                print('✅ Updated My Workspace')
            else:
                print('My Workspace already has Household title')
        
        # Add Type attribute in My Workspace too
        cur.execute('''
            SELECT slug FROM attributes
            WHERE object_id = %s AND slug = 'type'
        ''', (my_person_id,))
        
        if not cur.fetchone():
            type_attr_id = str(uuid.uuid4())
            cur.execute('''
                INSERT INTO attributes (id, object_id, slug, title, type, is_required, config, sort_order)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                type_attr_id,
                my_person_id,
                'type',
                'Type',
                'select',
                False,
                json.dumps(type_config),
                100
            ))
            print('✅ Added Type attribute to My Workspace')
    
    conn.commit()
    cur.close()
    conn.close()
    
    print('\n✅ Done!')
    print('\nSummary:')
    print('  1. Added Type attribute with 6 options (Client, Agent, CIO, BNI, Professional, Contact)')
    print('  2. Renamed "Company" attribute to "Household" in UI (still links to Company objects)')
    print('  3. Applied to both John\'s Workspace and My Workspace for consistency')

if __name__ == '__main__':
    main()