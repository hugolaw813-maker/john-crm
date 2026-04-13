#!/usr/bin/env python3
"""
Fix remaining Rozzano spelling in notes and conversation records
"""

import psycopg2
import json

PG_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
}

def fix_notes():
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    # Find notes with Rozzano
    cur.execute("SELECT id, title, content FROM notes WHERE title ILIKE '%roz%' OR content::text ILIKE '%roz%'")
    notes = cur.fetchall()
    
    print(f'Found {len(notes)} notes with Rozzano')
    
    for note_id, title, content in notes:
        print(f'\nNote {note_id}:')
        print(f'  Title: {title}')
        
        # Fix title
        new_title = title.replace('Rozzano', 'Razzano').replace('rozzano', 'razzano')
        if new_title != title:
            cur.execute("UPDATE notes SET title = %s WHERE id = %s", (new_title, note_id))
            print(f'  Updated title: {new_title}')
        
        # Fix content (JSON)
        if content and isinstance(content, dict):
            new_content = content.copy()
            changed = False
            
            # Check all string values in the dict
            def replace_in_dict(d):
                changed = False
                for k, v in d.items():
                    if isinstance(v, str):
                        new_v = v.replace('Rozzano', 'Razzano').replace('rozzano', 'razzano')
                        if new_v != v:
                            d[k] = new_v
                            changed = True
                    elif isinstance(v, dict):
                        if replace_in_dict(v):
                            changed = True
                    elif isinstance(v, list):
                        for i, item in enumerate(v):
                            if isinstance(item, str):
                                new_item = item.replace('Rozzano', 'Razzano').replace('rozzano', 'razzano')
                                if new_item != item:
                                    v[i] = new_item
                                    changed = True
                            elif isinstance(item, dict):
                                if replace_in_dict(item):
                                    changed = True
                return changed
            
            if replace_in_dict(new_content):
                cur.execute("UPDATE notes SET content = %s WHERE id = %s", (json.dumps(new_content), note_id))
                print(f'  Updated content')
    
    # Fix conversation records (Conversations workspace)
    conv_obj_id = '9e4c7c56-c61d-4ee0-8e8b-c62771bec655'
    
    # Get conversation attribute IDs
    cur.execute('''
        SELECT slug, id FROM attributes 
        WHERE object_id = %s AND slug IN ('summary', 'details', 'title')
    ''', (conv_obj_id,))
    
    attr_map = {row[0]: row[1] for row in cur.fetchall()}
    print(f'\nConversation attributes: {attr_map}')
    
    for attr_slug, attr_id in attr_map.items():
        # For text attributes
        cur.execute('''
            SELECT rv.id, rv.record_id, rv.text_value
            FROM record_values rv
            WHERE rv.attribute_id = %s
            AND rv.text_value ILIKE '%roz%'
        ''', (attr_id,))
        
        rows = cur.fetchall()
        print(f'\nFound {len(rows)} conversation {attr_slug} records with Rozzano')
        
        for rv_id, rec_id, text_val in rows:
            new_text = text_val.replace('Rozzano', 'Razzano').replace('rozzano', 'razzano')
            if new_text != text_val:
                cur.execute('''
                    UPDATE record_values
                    SET text_value = %s
                    WHERE id = %s
                ''', (new_text, rv_id))
                print(f'  Updated record {rec_id}: {text_val[:50]}... → {new_text[:50]}...')
    
    conn.commit()
    cur.close()
    conn.close()
    
    print('\n✅ All remaining Rozzano spelling fixed')

if __name__ == '__main__':
    fix_notes()