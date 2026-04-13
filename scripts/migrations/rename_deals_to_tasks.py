#!/usr/bin/env python3
"""
Rename Deals to Tasks, update statuses and attribute labels
"""

import psycopg2
import json

PG_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
}

# Configuration
DRY_RUN = False  # Set to False to apply changes

# Status title mapping (deal stages → task statuses)
STATUS_MAPPING = {
    'Lead': 'Todo',
    'Qualified': 'In Progress',
    'Proposal': 'Review',
    'Negotiation': 'Blocked',
    'Won': 'Done',
    'Lost': 'Cancelled'
}

# Attribute title updates
ATTRIBUTE_UPDATES = {
    'stage': 'Status',
    'expected_close_date': 'Due Date',
    # 'value': 'Priority',  # Keep as Value for now
    # 'associated_people': 'Assignees',  # Keep as Associated People
    # 'company': 'Project',  # Keep as Company
    # 'owner': 'Assignee',  # Keep as Owner
}

def rename_deals_to_tasks():
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    print('=== RENAMING DEALS TO TASKS ===')
    print(f'DRY RUN: {DRY_RUN}')
    
    # Get all deals objects
    cur.execute('''
        SELECT o.id, o.workspace_id, o.slug, o.singular_name, o.plural_name, w.name as workspace_name
        FROM objects o
        JOIN workspaces w ON o.workspace_id = w.id
        WHERE o.slug = 'deals'
        ORDER BY w.name
    ''')
    
    deals_objects = cur.fetchall()
    print(f'Found {len(deals_objects)} deals objects')
    
    for obj_id, ws_id, slug, singular, plural, ws_name in deals_objects:
        print(f'\n--- {ws_name}: {singular} ({plural}) ---')
        
        # 1. Rename object
        new_singular = 'Task' if singular == 'Deal' else singular.replace('Deal', 'Task')
        new_plural = 'Tasks' if plural == 'Deals' else plural.replace('Deals', 'Tasks')
        
        print(f'  Object rename: {singular} → {new_singular}')
        print(f'                {plural} → {new_plural}')
        
        if not DRY_RUN:
            cur.execute('''
                UPDATE objects
                SET singular_name = %s, plural_name = %s
                WHERE id = %s
            ''', (new_singular, new_plural, obj_id))
            print(f'  ✅ Updated object')
        
        # 2. Update attribute titles
        cur.execute('''
            SELECT id, slug, title, type
            FROM attributes
            WHERE object_id = %s
            ORDER BY slug
        ''', (obj_id,))
        
        attributes = cur.fetchall()
        print(f'  Found {len(attributes)} attributes')
        
        for attr_id, attr_slug, attr_title, attr_type in attributes:
            if attr_slug in ATTRIBUTE_UPDATES:
                new_title = ATTRIBUTE_UPDATES[attr_slug]
                if new_title != attr_title:
                    print(f'    {attr_slug}: {attr_title} → {new_title}')
                    if not DRY_RUN:
                        cur.execute('''
                            UPDATE attributes
                            SET title = %s
                            WHERE id = %s
                        ''', (new_title, attr_id))
                        print(f'      ✅ Updated')
        
        # 3. Update status titles for stage attribute
        stage_attr_id = None
        for attr_id, attr_slug, attr_title, attr_type in attributes:
            if attr_slug == 'stage':
                stage_attr_id = attr_id
                break
        
        if stage_attr_id:
            print(f'  Stage attribute ID: {stage_attr_id}')
            
            # Get current statuses
            cur.execute('''
                SELECT id, title, color, sort_order
                FROM statuses
                WHERE attribute_id = %s
                ORDER BY sort_order
            ''', (stage_attr_id,))
            
            statuses = cur.fetchall()
            print(f'  Found {len(statuses)} statuses')
            
            for status_id, status_title, color, sort_order in statuses:
                new_status_title = STATUS_MAPPING.get(status_title)
                if new_status_title and new_status_title != status_title:
                    print(f'    Status {sort_order}: {status_title} → {new_status_title}')
                    if not DRY_RUN:
                        cur.execute('''
                            UPDATE statuses
                            SET title = %s
                            WHERE id = %s
                        ''', (new_status_title, status_id))
                        print(f'      ✅ Updated')
        
        # 4. Update slug? (Optional - could break references)
        # We'll keep slug as 'deals' for now to avoid breaking references
        # If we want to change slug:
        # new_slug = 'tasks'
        # print(f'  Slug: {slug} → {new_slug}')
        # if not DRY_RUN:
        #     cur.execute('UPDATE objects SET slug = %s WHERE id = %s', (new_slug, obj_id))
    
    # 5. Also consider renaming workspace if needed
    # The workspace is named "John's Workspace" and "My Workspace", not "Deals"
    # So no need to rename workspace
    
    if not DRY_RUN:
        conn.commit()
        print('\n✅ All changes committed')
    else:
        print('\n⚠️ DRY RUN - no changes made')
        print('Set DRY_RUN = False to apply changes')
    
    # Show preview of changes
    print('\n=== PREVIEW OF CHANGES ===')
    print('Objects will be renamed:')
    for obj_id, ws_id, slug, singular, plural, ws_name in deals_objects:
        new_singular = 'Task' if singular == 'Deal' else singular.replace('Deal', 'Task')
        new_plural = 'Tasks' if plural == 'Deals' else plural.replace('Deals', 'Tasks')
        print(f'  {ws_name}: {singular} ({plural}) → {new_singular} ({new_plural})')
    
    print('\nAttribute titles will be updated:')
    for attr_slug, new_title in ATTRIBUTE_UPDATES.items():
        print(f'  {attr_slug} → {new_title}')
    
    print('\nStatus titles will be updated:')
    for old, new in STATUS_MAPPING.items():
        print(f'  {old} → {new}')
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    rename_deals_to_tasks()