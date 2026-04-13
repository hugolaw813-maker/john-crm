#!/usr/bin/env python3
"""
Check statuses table
"""

import psycopg2

PG_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
}

def check():
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    print('=== STATUSES TABLE ===')
    cur.execute('SELECT column_name FROM information_schema.columns WHERE table_name = \'statuses\' ORDER BY ordinal_position')
    cols = [row[0] for row in cur.fetchall()]
    print(f'Columns: {cols}')
    
    cur.execute('SELECT * FROM statuses')
    rows = cur.fetchall()
    print(f'\nTotal statuses: {len(rows)}')
    
    for row in rows:
        print(f'\nRow:')
        for i, col in enumerate(cols):
            print(f'  {col}: {row[i]}')
    
    # Check if there's a link to attributes
    print('\n=== CHECKING ATTRIBUTE STATUS LINKS ===')
    # Look for attribute_id in statuses
    if 'attribute_id' in cols:
        cur.execute('SELECT DISTINCT attribute_id FROM statuses')
        attr_ids = cur.fetchall()
        print(f'Attribute IDs in statuses: {attr_ids}')
        
        for attr_id in attr_ids:
            attr_id = attr_id[0]
            cur.execute('''
                SELECT a.slug, a.title, o.singular_name, w.name
                FROM attributes a
                JOIN objects o ON a.object_id = o.id
                JOIN workspaces w ON o.workspace_id = w.id
                WHERE a.id = %s
            ''', (attr_id,))
            attr_info = cur.fetchone()
            if attr_info:
                print(f'  Attribute {attr_id}: {attr_info}')
    
    # Check for status options for deals stage attribute
    john_ws_id = '2d46eec2-03d1-4f93-9b96-356ec7afa757'
    cur.execute('''
        SELECT a.id FROM attributes a
        JOIN objects o ON a.object_id = o.id
        WHERE o.workspace_id = %s AND a.slug = 'stage'
    ''', (john_ws_id,))
    
    stage_attr_id = cur.fetchone()
    if stage_attr_id:
        stage_attr_id = stage_attr_id[0]
        print(f'\nStage attribute ID: {stage_attr_id}')
        
        if 'attribute_id' in cols:
            cur.execute('SELECT id, name, color FROM statuses WHERE attribute_id = %s', (stage_attr_id,))
            statuses = cur.fetchall()
            print(f'Statuses for stage attribute:')
            for status_id, name, color in statuses:
                print(f'  {status_id}: {name} (color: {color})')
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    check()