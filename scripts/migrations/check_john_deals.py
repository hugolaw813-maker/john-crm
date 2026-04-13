#!/usr/bin/env python3
"""
Check Deals in John's Workspace
"""

import psycopg2
import json

PG_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
}

def check_john_deals():
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'
    
    print('=== JOHN\'S WORKSPACE DEALS ===')
    
    # Get deals object in John's workspace
    cur.execute('''
        SELECT o.id, o.slug, o.singular_name, o.plural_name
        FROM objects o
        WHERE o.workspace_id = %s AND o.slug = 'deals'
    ''', (john_ws_id,))
    
    deals_obj = cur.fetchone()
    if not deals_obj:
        print('No deals object found in John\'s workspace')
        return
    
    deals_id, slug, singular, plural = deals_obj
    print(f'Deals object: {singular} ({plural})')
    print(f'Object ID: {deals_id}')
    
    # Get attributes
    cur.execute('''
        SELECT slug, title, type, config::text
        FROM attributes
        WHERE object_id = %s
        ORDER BY slug
    ''', (deals_id,))
    
    print('\nAttributes:')
    attrs = []
    for attr_slug, title, attr_type, config in cur.fetchall():
        print(f'  {attr_slug}: {title} ({attr_type})')
        attrs.append((attr_slug, title, attr_type, config))
    
    # Count records
    cur.execute('SELECT COUNT(*) FROM records WHERE object_id = %s', (deals_id,))
    count = cur.fetchone()[0]
    print(f'\nTotal deals records: {count}')
    
    if count > 0:
        # Get all deals with their values
        print('\nDeals records:')
        cur.execute('''
            SELECT r.id, r.created_at
            FROM records r
            WHERE r.object_id = %s
            ORDER BY r.created_at
        ''', (deals_id,))
        
        for rec_id, created_at in cur.fetchall():
            print(f'\nRecord {rec_id} (created: {created_at}):')
            
            # Get all values for this record
            cur2 = conn.cursor()
            cur2.execute('''
                SELECT a.slug, a.title, a.type, 
                       rv.text_value, rv.number_value, rv.json_value, rv.date_value
                FROM record_values rv
                JOIN attributes a ON rv.attribute_id = a.id
                WHERE rv.record_id = %s
                ORDER BY a.slug
            ''', (rec_id,))
            
            for attr_slug, title, attr_type, text_val, num_val, json_val, date_val in cur2.fetchall():
                value = None
                if text_val is not None:
                    value = text_val
                elif num_val is not None:
                    value = num_val
                elif json_val is not None:
                    value = json_val
                elif date_val is not None:
                    value = date_val
                
                print(f'  {attr_slug}: {value}')
            
            cur2.close()
    
    # Check if there are any task-related objects
    print('\n=== CHECKING FOR TASKS IN JOHN\'S WORKSPACE ===')
    cur.execute('''
        SELECT o.slug, o.singular_name, o.plural_name
        FROM objects o
        WHERE o.workspace_id = %s 
        AND (o.slug ILIKE '%task%' OR o.singular_name ILIKE '%task%' OR o.plural_name ILIKE '%task%')
    ''', (john_ws_id,))
    
    tasks = cur.fetchall()
    if tasks:
        print('Found task objects:')
        for slug, singular, plural in tasks:
            print(f'  {singular} ({plural}) - slug: {slug}')
    else:
        print('No task objects found')
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    check_john_deals()