#!/usr/bin/env python3
"""
Explore current Deals and check for Tasks
"""

import psycopg2

PG_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
}

def explore():
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    print('=== CURRENT WORKSPACES ===')
    cur.execute('SELECT id, name, slug FROM workspaces ORDER BY name')
    for ws_id, name, slug in cur.fetchall():
        print(f'  {name} (slug: {slug}, id: {ws_id})')
    
    print('\n=== OBJECTS BY WORKSPACE ===')
    cur.execute('''
        SELECT w.name as workspace_name, o.slug, o.singular_name, o.plural_name
        FROM objects o
        JOIN workspaces w ON o.workspace_id = w.id
        ORDER BY w.name, o.slug
    ''')
    for ws_name, slug, singular, plural in cur.fetchall():
        print(f'  {ws_name}: {singular} ({plural}) - slug: {slug}')
    
    print('\n=== DEALS OBJECT DETAILS ===')
    # Find Deals object
    cur.execute('''
        SELECT o.id, o.workspace_id, w.name, o.slug, o.singular_name, o.plural_name
        FROM objects o
        JOIN workspaces w ON o.workspace_id = w.id
        WHERE o.slug = 'deals' OR o.plural_name = 'Deals'
    ''')
    
    deals_obj = cur.fetchone()
    if deals_obj:
        deals_id, ws_id, ws_name, slug, singular, plural = deals_obj
        print(f'Deals object: {singular} ({plural}) in {ws_name}')
        print(f'  Object ID: {deals_id}')
        print(f'  Workspace ID: {ws_id}')
        
        # Get attributes for Deals
        cur.execute('''
            SELECT slug, title, type, config::text
            FROM attributes
            WHERE object_id = %s
            ORDER BY slug
        ''', (deals_id,))
        print('  Attributes:')
        for attr_slug, title, attr_type, config in cur.fetchall():
            print(f'    {slug}: {title} ({attr_type})')
    
    print('\n=== CHECKING FOR TASKS ===')
    cur.execute('''
        SELECT w.name, o.slug, o.singular_name, o.plural_name
        FROM objects o
        JOIN workspaces w ON o.workspace_id = w.id
        WHERE o.slug ILIKE '%task%' 
           OR o.singular_name ILIKE '%task%'
           OR o.plural_name ILIKE '%task%'
    ''')
    
    tasks = cur.fetchall()
    if tasks:
        print('Found task-like objects:')
        for ws_name, slug, singular, plural in tasks:
            print(f'  {ws_name}: {singular} ({plural})')
    else:
        print('No task-like objects found')
    
    print('\n=== DEALS RECORDS COUNT ===')
    if deals_obj:
        deals_id = deals_obj[0]
        cur.execute('SELECT COUNT(*) FROM records WHERE object_id = %s', (deals_id,))
        count = cur.fetchone()[0]
        print(f'Deals records: {count}')
        
        # Sample records
        cur.execute('''
            SELECT r.id, rv.text_value as title
            FROM records r
            LEFT JOIN record_values rv ON r.id = rv.record_id
            LEFT JOIN attributes a ON rv.attribute_id = a.id
            WHERE r.object_id = %s AND a.slug = 'name'
            LIMIT 5
        ''', (deals_id,))
        print('Sample deals:')
        for rec_id, title in cur.fetchall():
            print(f'  {rec_id}: {title}')
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    explore()