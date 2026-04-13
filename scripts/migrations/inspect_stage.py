#!/usr/bin/env python3
"""
Inspect stage attribute config
"""

import psycopg2
import json

PG_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
}

def inspect():
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'
    
    # Get deals object ID
    cur.execute('''
        SELECT o.id FROM objects o
        WHERE o.workspace_id = %s AND o.slug = 'deals'
    ''', (john_ws_id,))
    
    deals_id = cur.fetchone()[0]
    
    # Get stage attribute config
    cur.execute('''
        SELECT slug, title, type, config
        FROM attributes
        WHERE object_id = %s AND slug = 'stage'
    ''', (deals_id,))
    
    stage_slug, stage_title, stage_type, stage_config = cur.fetchone()
    print(f'Stage attribute: {stage_title} ({stage_type})')
    print(f'Config: {stage_config}')
    
    if stage_config:
        config = stage_config
        print('\nParsed config:')
        if isinstance(config, dict):
            for key, value in config.items():
                print(f'  {key}: {value}')
        else:
            print(f'  Raw: {config}')
    
    # Check if there's a status_options table or similar
    print('\n=== CHECKING STATUS OPTIONS ===')
    # Look for status_options in config
    if stage_config and isinstance(stage_config, dict) and 'options' in stage_config:
        options = stage_config['options']
        print(f'Status options: {options}')
    
    # Also check if there's a separate status_options table
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%status%'")
    tables = cur.fetchall()
    print('\nStatus-related tables:')
    for table in tables:
        print(f'  {table[0]}')
    
    # Check attribute_type_options table if exists
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'attribute_type_options'
    """)
    cols = cur.fetchall()
    if cols:
        print('\nattribute_type_options columns:')
        for col in cols:
            print(f'  {col[0]}')
        
        # Query for stage options
        cur.execute('''
            SELECT id, value, label, color
            FROM attribute_type_options
            WHERE attribute_id = (SELECT id FROM attributes WHERE object_id = %s AND slug = 'stage')
        ''', (deals_id,))
        
        print('\nStage options:')
        for opt_id, value, label, color in cur.fetchall():
            print(f'  {opt_id}: {label} (value: {value}, color: {color})')
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    inspect()