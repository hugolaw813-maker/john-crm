#!/usr/bin/env python3
"""
Revert all Task/Deal changes back to original state
"""

import psycopg2
import json

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    user='jcw_l',
    database='openclaw'
)
cur = conn.cursor()

print('=== REVERTING ALL TASK/DEAL CHANGES ===')

# Status label mapping (back to original)
STATUS_REVERT = {
    'Todo': 'Lead',
    'In Progress': 'Qualified', 
    'Review': 'Proposal',
    'Blocked': 'Negotiation',
    'Done': 'Won',
    'Cancelled': 'Lost'
}

# Attribute title mapping (back to original)
ATTR_REVERT = {
    'Status': 'Stage',
    'Due Date': 'Expected Close Date'
}

# 1. Revert object names and slugs
print('\n1. REVERTING OBJECT NAMES AND SLUGS')
workspaces = [
    ('2d46eec2-03d1-4f93-9b96-356ec7afa757', "John's Workspace"),
    ('709eeba3-da92-46ff-aeec-3415c62c5fdf', "My Workspace")
]

for ws_id, ws_name in workspaces:
    # Check current state
    cur.execute('''
        SELECT id, slug, singular_name, plural_name
        FROM objects
        WHERE workspace_id = %s AND (slug = 'tasks' OR slug = 'deals')
    ''', (ws_id,))
    
    objs = cur.fetchall()
    for obj_id, slug, singular, plural in objs:
        print(f'\n{ws_name}: {slug} = {singular} ({plural})')
        
        # Revert to Deals
        if singular == 'Task' and plural == 'Tasks':
            print(f'  Reverting: Task/Tasks → Deal/Deals')
            cur.execute('''
                UPDATE objects
                SET slug = 'deals',
                    singular_name = 'Deal',
                    plural_name = 'Deals'
                WHERE id = %s
            ''', (obj_id,))
            print(f'  ✅ Reverted to deals/Deal/Deals')
        elif singular == 'Deal' and plural == 'Deals':
            print(f'  Already Deal/Deals')
        else:
            print(f'  Unknown state')

# 2. Revert attribute titles
print('\n2. REVERTING ATTRIBUTE TITLES')
for ws_id, ws_name in workspaces:
    # Get deals object ID
    cur.execute('SELECT id FROM objects WHERE workspace_id = %s AND slug = \'deals\'', (ws_id,))
    result = cur.fetchone()
    if not result:
        continue
    
    deals_id = result[0]
    
    # Get attributes
    cur.execute('''
        SELECT id, slug, title
        FROM attributes
        WHERE object_id = %s AND slug IN ('stage', 'expected_close_date')
    ''', (deals_id,))
    
    for attr_id, attr_slug, title in cur.fetchall():
        original_title = ATTR_REVERT.get(title, title)
        if original_title != title:
            print(f'{ws_name} {attr_slug}: {title} → {original_title}')
            cur.execute('UPDATE attributes SET title = %s WHERE id = %s', (original_title, attr_id))

# 3. Revert status labels
print('\n3. REVERTING STATUS LABELS')
for ws_id, ws_name in workspaces:
    # Get deals object and stage attribute
    cur.execute('''
        SELECT a.id
        FROM attributes a
        JOIN objects o ON a.object_id = o.id
        WHERE o.workspace_id = %s AND o.slug = 'deals' AND a.slug = 'stage'
    ''', (ws_id,))
    
    result = cur.fetchone()
    if not result:
        continue
    
    stage_attr_id = result[0]
    
    # Get statuses
    cur.execute('''
        SELECT id, title
        FROM statuses
        WHERE attribute_id = %s
    ''', (stage_attr_id,))
    
    for status_id, title in cur.fetchall():
        original_title = STATUS_REVERT.get(title)
        if original_title and original_title != title:
            print(f'{ws_name} status: {title} → {original_title}')
            cur.execute('UPDATE statuses SET title = %s WHERE id = %s', (original_title, status_id))

# 4. Verify
print('\n4. VERIFICATION')
for ws_id, ws_name in workspaces:
    print(f'\n{ws_name}:')
    
    # Object
    cur.execute('''
        SELECT slug, singular_name, plural_name
        FROM objects
        WHERE workspace_id = %s AND slug = 'deals'
    ''', (ws_id,))
    
    obj = cur.fetchone()
    if obj:
        slug, singular, plural = obj
        print(f'  Object: {slug} = {singular} ({plural})')
    
    # Attributes
    if obj:
        deals_id = cur.execute('SELECT id FROM objects WHERE workspace_id = %s AND slug = \'deals\'', (ws_id,))
        deals_id = cur.fetchone()[0]
        cur.execute('''
            SELECT slug, title
            FROM attributes
            WHERE object_id = %s
            ORDER BY slug
        ''', (deals_id,))
        
        print('  Attributes:')
        for slug, title in cur.fetchall():
            print(f'    {slug}: {title}')

conn.commit()
cur.close()
conn.close()

print('\n✅ All Task/Deal changes reverted')
print('Object is now: deals/Deal/Deals with original labels')