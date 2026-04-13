#!/usr/bin/env python3
"""
Phase 2: Create Conversations workspace and object, migrate conversations data
"""

import psycopg2
import uuid
import json
from datetime import datetime

# Configuration
PG_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
}

# Existing user ID
USER_ID = 'mtTk9exShWSRNJwjnbdCIfKQrFpMxPBR'

# Existing object IDs from John's Workspace
JOHN_WS_ID = '2d46eec2-03d1-4f93-9b96-356ec7afa757'
PERSON_OBJ_ID = '139d9239-39bb-49ca-99fe-18cbbb25ce55'
COMPANY_OBJ_ID = 'ff428b0d-3f1f-4b9e-a718-337fec03850f'

def connect_db():
    """Connect to PostgreSQL database"""
    return psycopg2.connect(**PG_CONFIG)

def create_conversations_workspace(pg_conn):
    """Create Conversations workspace if it doesn't exist"""
    cur = pg_conn.cursor()
    
    # Check if conversations workspace exists
    cur.execute("SELECT id, name, slug FROM workspaces WHERE slug = 'conversations' OR name ILIKE '%conversation%'")
    existing = cur.fetchone()
    
    if existing:
        ws_id, ws_name, ws_slug = existing
        print(f"Using existing workspace: {ws_name} (slug: {ws_slug}, id: {ws_id})")
        return ws_id
    
    # Create new workspace
    ws_id = str(uuid.uuid4())
    ws_name = "Conversations"
    ws_slug = "conversations"
    
    print(f"Creating new workspace: {ws_name}...")
    cur.execute('''
        INSERT INTO workspaces (id, name, slug, settings, created_at, updated_at)
        VALUES (%s, %s, %s, %s, NOW(), NOW())
    ''', (ws_id, ws_name, ws_slug, '{}'))
    
    # Add user as workspace member
    cur.execute('''
        INSERT INTO workspace_members (id, workspace_id, user_id, role, created_at)
        VALUES (%s, %s, %s, %s, NOW())
    ''', (str(uuid.uuid4()), ws_id, USER_ID, 'admin'))
    
    pg_conn.commit()
    print(f"Created workspace: {ws_name} (id: {ws_id})")
    return ws_id

def create_conversation_object(pg_conn, workspace_id):
    """Create Conversation object with custom attributes"""
    cur = pg_conn.cursor()
    
    # Check if conversation object already exists
    cur.execute('''
        SELECT id, slug, singular_name, plural_name
        FROM objects
        WHERE workspace_id = %s AND slug = 'conversations'
    ''', (workspace_id,))
    
    existing = cur.fetchone()
    if existing:
        obj_id, obj_slug, singular, plural = existing
        print(f"Using existing object: {singular} ({plural}) - slug: {obj_slug}, id: {obj_id}")
        # Fetch existing attributes
        cur.execute('SELECT id, slug FROM attributes WHERE object_id = %s', (obj_id,))
        attribute_ids = {slug: attr_id for attr_id, slug in cur.fetchall()}
        return obj_id, attribute_ids
    
    # Create new object
    obj_id = str(uuid.uuid4())
    print(f"Creating Conversation object...")
    
    cur.execute('''
        INSERT INTO objects (id, workspace_id, slug, singular_name, plural_name, icon, is_system, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
    ''', (obj_id, workspace_id, 'conversations', 'Conversation', 'Conversations', 'message-square', False))
    
    # Create attributes
    attributes = [
        # Summary (text)
        {
            'slug': 'summary',
            'title': 'Summary',
            'type': 'text',
            'is_required': True,
            'config': {}
        },
        # Type (select)
        {
            'slug': 'type',
            'title': 'Type',
            'type': 'select',
            'is_required': False,
            'config': {
                'options': [
                    {'value': 'call', 'label': 'Call'},
                    {'value': 'meeting', 'label': 'Meeting'},
                    {'value': 'email', 'label': 'Email'},
                    {'value': 'note', 'label': 'Note'},
                    {'value': 'follow-up', 'label': 'Follow-up'}
                ]
            }
        },
        # Date (date)
        {
            'slug': 'date',
            'title': 'Date',
            'type': 'date',
            'is_required': True,
            'config': {}
        },
        # Details (text)
        {
            'slug': 'details',
            'title': 'Details',
            'type': 'text',
            'is_required': False,
            'config': {}
        },
        # Status (select)
        {
            'slug': 'status',
            'title': 'Status',
            'type': 'select',
            'is_required': False,
            'config': {
                'options': [
                    {'value': 'pending', 'label': 'Pending'},
                    {'value': 'completed', 'label': 'Completed'},
                    {'value': 'follow-up', 'label': 'Follow-up Required'},
                    {'value': 'cancelled', 'label': 'Cancelled'}
                ]
            }
        },
        # Duration (number)
        {
            'slug': 'duration_minutes',
            'title': 'Duration (minutes)',
            'type': 'number',
            'is_required': False,
            'config': {}
        },
        # Follow-up Date (date)
        {
            'slug': 'follow_up_date',
            'title': 'Follow-up Date',
            'type': 'date',
            'is_required': False,
            'config': {}
        },
        # Household (record reference to Company)
        {
            'slug': 'household',
            'title': 'Household',
            'type': 'record_reference',
            'is_required': False,
            'config': {'targetObjectSlug': 'companies'}
        },
        # Client (record reference to Person)
        {
            'slug': 'client',
            'title': 'Client',
            'type': 'record_reference',
            'is_required': False,
            'config': {'targetObjectSlug': 'people'}
        }
    ]
    
    attribute_ids = {}
    for i, attr in enumerate(attributes):
        attr_id = str(uuid.uuid4())
        attribute_ids[attr['slug']] = attr_id
        
        cur.execute('''
            INSERT INTO attributes (id, object_id, slug, title, type, config, is_system, is_required, is_unique, is_multiselect, sort_order, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ''', (
            attr_id, obj_id, attr['slug'], attr['title'], attr['type'],
            json.dumps(attr['config']), False, attr['is_required'], False, False, i
        ))
        
        print(f"  Created attribute: {attr['title']} ({attr['type']})")
    
    pg_conn.commit()
    print(f"Created Conversation object with {len(attributes)} attributes")
    return obj_id, attribute_ids

def get_notes_data(pg_conn):
    """Extract conversations data from notes table"""
    cur = pg_conn.cursor()
    
    # Get all notes with their associated records
    cur.execute('''
        SELECT n.id, n.record_id, n.title, n.content, n.created_at,
               o.singular_name as record_type
        FROM notes n
        JOIN records r ON n.record_id = r.id
        JOIN objects o ON r.object_id = o.id
        WHERE o.singular_name IN ('Person', 'Company')
        ORDER BY n.created_at
    ''')
    
    notes = []
    for row in cur.fetchall():
        note_id, record_id, title, content_json, created_at, record_type = row
        
        # Parse content JSON (could be dict from JSONB or string)
        if content_json is None:
            content = {}
        elif isinstance(content_json, dict):
            content = content_json
        else:
            try:
                content = json.loads(content_json)
            except:
                content = {}
        
        notes.append({
            'note_id': note_id,
            'record_id': record_id,
            'record_type': record_type,
            'title': title,
            'type': content.get('type', 'conversation'),
            'details': content.get('details', ''),
            'status': content.get('status', ''),
            'duration_minutes': content.get('duration_minutes'),
            'follow_up_date': content.get('follow_up_date'),
            'created_at': created_at
        })
    
    cur.close()
    return notes

def migrate_conversations_to_object(pg_conn, conv_obj_id, attribute_ids, notes_data):
    """Migrate notes data to Conversation records"""
    cur = pg_conn.cursor()
    
    # Get mapping of old record IDs to new workspace record IDs
    # We need to find the Person/Company records in the new workspace
    # For now, we'll link to the same records (they're in John's workspace)
    # The record_reference attributes should point to those records
    
    migrated_count = 0
    
    for note in notes_data:
        # Generate new conversation record ID
        conv_record_id = str(uuid.uuid4())
        
        # Use note creation date
        created_at = note['created_at']
        
        # Insert conversation record
        cur.execute('''
            INSERT INTO records (id, object_id, created_at, created_by, updated_at, sort_order)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (conv_record_id, conv_obj_id, created_at, USER_ID, created_at, migrated_count))
        
        # Insert attribute values
        
        # 1. Summary (text)
        if 'summary' in attribute_ids and note['title']:
            cur.execute('''
                INSERT INTO record_values 
                (id, record_id, attribute_id, text_value, created_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                str(uuid.uuid4()), conv_record_id, attribute_ids['summary'],
                note['title'], created_at, USER_ID
            ))
        
        # 2. Type (select)
        if 'type' in attribute_ids and note['type']:
            cur.execute('''
                INSERT INTO record_values 
                (id, record_id, attribute_id, text_value, created_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                str(uuid.uuid4()), conv_record_id, attribute_ids['type'],
                note['type'], created_at, USER_ID
            ))
        
        # 3. Date (date) - use created_at date
        if 'date' in attribute_ids and created_at:
            cur.execute('''
                INSERT INTO record_values 
                (id, record_id, attribute_id, date_value, created_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                str(uuid.uuid4()), conv_record_id, attribute_ids['date'],
                created_at.date(), created_at, USER_ID
            ))
        
        # 4. Details (text)
        if 'details' in attribute_ids and note['details']:
            cur.execute('''
                INSERT INTO record_values 
                (id, record_id, attribute_id, text_value, created_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                str(uuid.uuid4()), conv_record_id, attribute_ids['details'],
                note['details'][:1000] if note['details'] else '', created_at, USER_ID
            ))
        
        # 5. Status (select)
        if 'status' in attribute_ids and note['status']:
            cur.execute('''
                INSERT INTO record_values 
                (id, record_id, attribute_id, text_value, created_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                str(uuid.uuid4()), conv_record_id, attribute_ids['status'],
                note['status'], created_at, USER_ID
            ))
        
        # 6. Duration (number)
        if 'duration_minutes' in attribute_ids and note['duration_minutes']:
            cur.execute('''
                INSERT INTO record_values 
                (id, record_id, attribute_id, number_value, created_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                str(uuid.uuid4()), conv_record_id, attribute_ids['duration_minutes'],
                note['duration_minutes'], created_at, USER_ID
            ))
        
        # 7. Follow-up Date (date)
        if 'follow_up_date' in attribute_ids and note['follow_up_date']:
            try:
                follow_up = datetime.fromisoformat(note['follow_up_date'].replace('Z', '+00:00'))
                cur.execute('''
                    INSERT INTO record_values 
                    (id, record_id, attribute_id, date_value, created_at, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    str(uuid.uuid4()), conv_record_id, attribute_ids['follow_up_date'],
                    follow_up.date(), created_at, USER_ID
                ))
            except:
                pass
        
        # 8. Household (record reference) - if note is attached to a Company record
        if 'household' in attribute_ids and note['record_type'] == 'Company' and note['record_id']:
            # Find the Company record in John's workspace
            cur.execute('''
                SELECT id FROM records 
                WHERE id = %s AND object_id = %s
            ''', (note['record_id'], COMPANY_OBJ_ID))
            
            company_record = cur.fetchone()
            if company_record:
                cur.execute('''
                    INSERT INTO record_values 
                    (id, record_id, attribute_id, referenced_record_id, created_at, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    str(uuid.uuid4()), conv_record_id, attribute_ids['household'],
                    company_record[0], created_at, USER_ID
                ))
        
        # 9. Client (record reference) - if note is attached to a Person record
        if 'client' in attribute_ids and note['record_type'] == 'Person' and note['record_id']:
            # Find the Person record in John's workspace
            cur.execute('''
                SELECT id FROM records 
                WHERE id = %s AND object_id = %s
            ''', (note['record_id'], PERSON_OBJ_ID))
            
            person_record = cur.fetchone()
            if person_record:
                cur.execute('''
                    INSERT INTO record_values 
                    (id, record_id, attribute_id, referenced_record_id, created_at, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    str(uuid.uuid4()), conv_record_id, attribute_ids['client'],
                    person_record[0], created_at, USER_ID
                ))
        
        migrated_count += 1
        if migrated_count % 5 == 0:
            print(f"  Migrated {migrated_count}/{len(notes_data)} conversations")
    
    pg_conn.commit()
    return migrated_count

def main():
    print("=== PHASE 2: CONVERSATIONS WORKSPACE SETUP ===")
    print(f"Started at: {datetime.now()}")
    
    pg_conn = connect_db()
    
    try:
        # Step 1: Create or get Conversations workspace
        conv_ws_id = create_conversations_workspace(pg_conn)
        
        # Step 2: Create Conversation object with attributes
        conv_obj_id, attribute_ids = create_conversation_object(pg_conn, conv_ws_id)
        
        # Step 3: Get notes data (existing conversations)
        print("\n📋 Extracting conversations from notes...")
        notes_data = get_notes_data(pg_conn)
        print(f"  Found {len(notes_data)} conversations in notes")
        
        # Step 4: Migrate to Conversation object
        print("\n🔄 Migrating to Conversation objects...")
        migrated_count = migrate_conversations_to_object(pg_conn, conv_obj_id, attribute_ids, notes_data)
        
        # Step 5: Verification
        print("\n✅ MIGRATION COMPLETE")
        print(f"   Migrated {migrated_count} conversations to dedicated Conversation objects")
        print(f"   Workspace: Conversations (id: {conv_ws_id})")
        print(f"   Object: Conversation (id: {conv_obj_id})")
        print(f"   Attributes: {len(attribute_ids)} custom fields")
        
        # Count total Conversation records
        cur = pg_conn.cursor()
        cur.execute('SELECT COUNT(*) FROM records WHERE object_id = %s', (conv_obj_id,))
        total_conversations = cur.fetchone()[0]
        print(f"   Total Conversation records: {total_conversations}")
        
        # Show sample
        cur.execute('''
            SELECT r.id, 
                   MAX(CASE WHEN a.slug = 'summary' THEN rv.text_value END) as summary,
                   MAX(CASE WHEN a.slug = 'type' THEN rv.text_value END) as type
            FROM records r
            LEFT JOIN record_values rv ON r.id = rv.record_id
            LEFT JOIN attributes a ON rv.attribute_id = a.id
            WHERE r.object_id = %s
            GROUP BY r.id
            ORDER BY r.created_at
            LIMIT 5
        ''', (conv_obj_id,))
        
        print("\n📋 Sample Conversation records:")
        for conv_id, summary, conv_type in cur.fetchall():
            summary_display = summary[:50] + '...' if summary and len(summary) > 50 else summary
            print(f"  - {summary_display} ({conv_type})")
        
        cur.close()
        
        print(f"\n🌐 Access in CRM:")
        print(f"   1. Log in at http://172.31.153.173:3001")
        print(f"   2. Switch to 'Conversations' workspace (top left dropdown)")
        print(f"   3. Click 'Conversations' in sidebar")
        print(f"   4. View all {migrated_count} conversations in table format")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        pg_conn.rollback()
    finally:
        pg_conn.close()
        print(f"\nFinished at: {datetime.now()}")

if __name__ == '__main__':
    main()