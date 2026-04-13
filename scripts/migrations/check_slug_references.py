#!/usr/bin/env python3
"""
Check for references to 'deals' slug in attribute configs
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
    
    print('=== CHECKING FOR "DEALS" SLUG REFERENCES ===')
    
    # Get all attributes with config
    cur.execute('''
        SELECT a.id, a.slug, a.title, a.type, a.config::text, o.singular_name, w.name
        FROM attributes a
        JOIN objects o ON a.object_id = o.id
        JOIN workspaces w ON o.workspace_id = w.id
        WHERE a.config IS NOT NULL
    ''')
    
    deals_references = []
    for attr_id, attr_slug, attr_title, attr_type, config_json, obj_name, ws_name in cur.fetchall():
        if config_json:
            try:
                config = json.loads(config_json)
                # Check if config contains 'deals' string
                config_str = str(config).lower()
                if 'deals' in config_str:
                    deals_references.append({
                        'workspace': ws_name,
                        'object': obj_name,
                        'attribute': f'{attr_slug} ({attr_title})',
                        'config': config
                    })
            except:
                pass
    
    if deals_references:
        print(f'Found {len(deals_references)} attributes referencing "deals":')
        for ref in deals_references:
            print(f'\n{ref["workspace"]} → {ref["object"]} → {ref["attribute"]}')
            print(f'Config: {ref["config"]}')
    else:
        print('No attributes found referencing "deals" slug')
    
    # Check specifically for targetObjectSlug references
    print('\n=== CHECKING targetObjectSlug REFERENCES ===')
    cur.execute('''
        SELECT a.id, a.slug, a.title, a.type, a.config::text, o.singular_name, w.name
        FROM attributes a
        JOIN objects o ON a.object_id = o.id
        JOIN workspaces w ON o.workspace_id = w.id
        WHERE a.config::text LIKE '%targetObjectSlug%'
    ''')
    
    target_refs = cur.fetchall()
    if target_refs:
        print(f'Found {len(target_refs)} attributes with targetObjectSlug:')
        for attr_id, attr_slug, attr_title, attr_type, config_json, obj_name, ws_name in target_refs:
            print(f'\n{ws_name} → {obj_name} → {attr_slug} ({attr_title})')
            try:
                config = json.loads(config_json)
                print(f'Config: {config}')
            except:
                print(f'Config (raw): {config_json}')
    else:
        print('No targetObjectSlug references found')
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    check()