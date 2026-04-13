#!/usr/bin/env python3
"""
Migration script from old SQLite CRM to new PostgreSQL OpenClaw CRM
"""

import sqlite3
import psycopg2
import uuid
import json
from datetime import datetime

# Configuration
OLD_DB_PATH = '/home/jcw_l/.openclaw/workspace-sarah/secure-crm/data/crm.db'
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'jcw_l',
    'database': 'openclaw'
}

# Target workspace and objects (from earlier queries)
TARGET_WORKSPACE_ID = 'd96be209-824d-4e5f-9394-3c1dc45c75d0'
TARGET_USER_ID = 'L20c4CHnqMpHB9EuAU6oBC67I99sMnLC'

# Object IDs in target workspace
PERSON_OBJ_ID = 'c06b3fcd-e6d9-47f0-8e64-90c70b75881a'
COMPANY_OBJ_ID = '2e7dcc10-3a23-4eb3-8b25-b11cc4db1631'
DEAL_OBJ_ID = 'eac298db-1c00-46d5-96d6-411aa0b907f0'

# Attribute IDs (will be populated from database)
PERSON_ATTRS = {}
COMPANY_ATTRS = {}
DEAL_ATTRS = {}

# Mappings for reference between old and new IDs
OLD_TO_NEW_PERSON = {}  # old client_id -> new record_id
OLD_TO_NEW_COMPANY = {} # old household_id -> new record_id

def connect_old_crm():
    """Connect to old SQLite CRM"""
    print(f"Connecting to old CRM at {OLD_DB_PATH}...")
    conn = sqlite3.connect(OLD_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def connect_new_crm():
    """Connect to new PostgreSQL CRM"""
    print(f"Connecting to new PostgreSQL CRM...")
    conn = psycopg2.connect(**PG_CONFIG)
    return conn

def setup_attribute_mappings(pg_conn):
    """Get attribute IDs from new CRM"""
    global PERSON_ATTRS, COMPANY_ATTRS, DEAL_ATTRS
    
    cur = pg_conn.cursor()
    
    # Person attributes
    cur.execute('''
        SELECT id, slug, title, type 
        FROM attributes 
        WHERE object_id = %s 
        ORDER BY sort_order
    ''', (PERSON_OBJ_ID,))
    
    for attr_id, slug, title, atype in cur.fetchall():
        PERSON_ATTRS[slug] = {'id': attr_id, 'title': title, 'type': atype}
    
    # Company attributes  
    cur.execute('''
        SELECT id, slug, title, type 
        FROM attributes 
        WHERE object_id = %s 
        ORDER BY sort_order
    ''', (COMPANY_OBJ_ID,))
    
    for attr_id, slug, title, atype in cur.fetchall():
        COMPANY_ATTRS[slug] = {'id': attr_id, 'title': title, 'type': atype}
    
    # Deal attributes
    cur.execute('''
        SELECT id, slug, title, type 
        FROM attributes 
        WHERE object_id = %s 
        ORDER BY sort_order
    ''', (DEAL_OBJ_ID,))
    
    for attr_id, slug, title, atype in cur.fetchall():
        DEAL_ATTRS[slug] = {'id': attr_id, 'title': title, 'type': atype}
    
    cur.close()
    print(f"Loaded {len(PERSON_ATTRS)} person attributes, {len(COMPANY_ATTRS)} company attributes, {len(DEAL_ATTRS)} deal attributes")

def migrate_clients(old_conn, pg_conn):
    """Migrate 22 clients to Person records"""
    print("\n📋 Migrating clients to Person records...")
    
    old_cur = old_conn.cursor()
    pg_cur = pg_conn.cursor()
    
    # Get all clients from old CRM
    old_cur.execute('''
        SELECT id, first_name, last_name, email, phone, status, notes, created_at, updated_at
        FROM clients
        ORDER BY id
    ''')
    
    clients = old_cur.fetchall()
    print(f"  Found {len(clients)} clients in old CRM")
    
    migrated_count = 0
    
    for client in clients:
        client_id = client['id']
        first_name = client['first_name']
        last_name = client['last_name']
        email = client['email']
        phone = client['phone']
        status = client['status']
        notes = client['notes']
        created_at = client['created_at']
        updated_at = client['updated_at']
        
        # Create full name
        full_name = f"{first_name} {last_name}".strip()
        if not full_name:
            full_name = email or f"Client {client_id}"
        
        # Generate new record ID
        record_id = str(uuid.uuid4())
        
        # Parse dates
        try:
            created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00')) if created_at else datetime.now()
        except:
            created_dt = datetime.now()
            
        try:
            updated_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00')) if updated_at else created_dt
        except:
            updated_dt = created_dt
        
        # Insert record
        pg_cur.execute('''
            INSERT INTO records (id, object_id, created_at, created_by, updated_at, sort_order)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (record_id, PERSON_OBJ_ID, created_dt, TARGET_USER_ID, updated_dt, migrated_count))
        
        # Store mapping
        OLD_TO_NEW_PERSON[client_id] = record_id
        
        # Create attribute values
        
        # 1. Name (personal_name type)
        if 'name' in PERSON_ATTRS and full_name:
            name_value = json.dumps({
                'given_name': first_name or '',
                'family_name': last_name or '',
                'full_name': full_name
            })
            pg_cur.execute('''
                INSERT INTO record_values 
                (id, record_id, attribute_id, json_value, created_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                str(uuid.uuid4()), record_id, PERSON_ATTRS['name']['id'], 
                name_value, created_dt, TARGET_USER_ID
            ))
        
        # 2. Email (email_address type)
        if 'email_addresses' in PERSON_ATTRS and email:
            email_value = json.dumps([{
                'email_address': email,
                'email_address_type': 'work'
            }])
            pg_cur.execute('''
                INSERT INTO record_values 
                (id, record_id, attribute_id, json_value, created_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                str(uuid.uuid4()), record_id, PERSON_ATTRS['email_addresses']['id'],
                email_value, created_dt, TARGET_USER_ID
            ))
        
        # 3. Phone (phone_number type)
        if 'phone_numbers' in PERSON_ATTRS and phone:
            phone_value = json.dumps([{
                'phone_number': str(phone),
                'phone_number_type': 'work'
            }])
            pg_cur.execute('''
                INSERT INTO record_values 
                (id, record_id, attribute_id, json_value, created_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                str(uuid.uuid4()), record_id, PERSON_ATTRS['phone_numbers']['id'],
                phone_value, created_dt, TARGET_USER_ID
            ))
        
        # 4. Job Title (text type - use status field)
        if 'job_title' in PERSON_ATTRS and status:
            pg_cur.execute('''
                INSERT INTO record_values 
                (id, record_id, attribute_id, text_value, created_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                str(uuid.uuid4()), record_id, PERSON_ATTRS['job_title']['id'],
                status, created_dt, TARGET_USER_ID
            ))
        
        # 5. Description (text type - use notes field)
        if 'description' in PERSON_ATTRS and notes:
            pg_cur.execute('''
                INSERT INTO record_values 
                (id, record_id, attribute_id, text_value, created_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                str(uuid.uuid4()), record_id, PERSON_ATTRS['description']['id'],
                notes[:500] if notes else '', created_dt, TARGET_USER_ID
            ))
        
        migrated_count += 1
        if migrated_count % 5 == 0:
            print(f"  Migrated {migrated_count}/{len(clients)} clients")
    
    pg_conn.commit()
    print(f"✅ Migrated {migrated_count} clients to Person records")
    
    old_cur.close()
    pg_cur.close()
    return migrated_count

def migrate_households(old_conn, pg_conn):
    """Migrate 29 households to Company records"""
    print("\n🏢 Migrating households to Company records...")
    
    old_cur = old_conn.cursor()
    pg_cur = pg_conn.cursor()
    
    # Get all households from old CRM
    old_cur.execute('''
        SELECT id, slug, display_name, assigned_agent, coworker, status, created_at, updated_at
        FROM households
        ORDER BY id
    ''')
    
    households = old_cur.fetchall()
    print(f"  Found {len(households)} households in old CRM")
    
    migrated_count = 0
    
    for household in households:
        household_id = household['id']
        slug = household['slug']
        display_name = household['display_name']
        assigned_agent = household['assigned_agent']
        coworker = household['coworker']
        status = household['status']
        created_at = household['created_at']
        updated_at = household['updated_at']
        
        # Company name
        company_name = display_name or f"Household {household_id}"
        
        # Generate new record ID
        record_id = str(uuid.uuid4())
        
        # Parse dates
        try:
            created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00')) if created_at else datetime.now()
        except:
            created_dt = datetime.now()
            
        try:
            updated_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00')) if updated_at else created_dt
        except:
            updated_dt = created_dt
        
        # Insert record
        pg_cur.execute('''
            INSERT INTO records (id, object_id, created_at, created_by, updated_at, sort_order)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (record_id, COMPANY_OBJ_ID, created_dt, TARGET_USER_ID, updated_dt, migrated_count))
        
        # Store mapping
        OLD_TO_NEW_COMPANY[household_id] = record_id
        
        # Create attribute values
        
        # 1. Name (text type)
        if 'name' in COMPANY_ATTRS and company_name:
            pg_cur.execute('''
                INSERT INTO record_values 
                (id, record_id, attribute_id, text_value, created_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                str(uuid.uuid4()), record_id, COMPANY_ATTRS['name']['id'],
                company_name, created_dt, TARGET_USER_ID
            ))
        
        # 2. Domains (domain type - use slug)
        if 'domains' in COMPANY_ATTRS and slug:
            # Create domain from slug
            domain = f"{slug}.example.com" if slug else None
            if domain:
                domain_value = json.dumps([domain])
                pg_cur.execute('''
                    INSERT INTO record_values 
                    (id, record_id, attribute_id, json_value, created_at, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    str(uuid.uuid4()), record_id, COMPANY_ATTRS['domains']['id'],
                    domain_value, created_dt, TARGET_USER_ID
                ))
        
        # 3. Description (text type)
        if 'description' in COMPANY_ATTRS:
            description_parts = []
            if assigned_agent:
                description_parts.append(f"Agent: {assigned_agent}")
            if coworker:
                description_parts.append("Coworker household")
            if status:
                description_parts.append(f"Status: {status}")
            
            if description_parts:
                description = "; ".join(description_parts)
                pg_cur.execute('''
                    INSERT INTO record_values 
                    (id, record_id, attribute_id, text_value, created_at, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    str(uuid.uuid4()), record_id, COMPANY_ATTRS['description']['id'],
                    description, created_dt, TARGET_USER_ID
                ))
        
        # 4. Categories (select type - mark as household)
        if 'categories' in COMPANY_ATTRS:
            # Create a simple category value
            pg_cur.execute('''
                INSERT INTO record_values 
                (id, record_id, attribute_id, text_value, created_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                str(uuid.uuid4()), record_id, COMPANY_ATTRS['categories']['id'],
                'household', created_dt, TARGET_USER_ID
            ))
        
        migrated_count += 1
        if migrated_count % 5 == 0:
            print(f"  Migrated {migrated_count}/{len(households)} households")
    
    pg_conn.commit()
    print(f"✅ Migrated {migrated_count} households to Company records")
    
    old_cur.close()
    pg_cur.close()
    return migrated_count

def update_person_company_links(old_conn, pg_conn):
    """Update Person records with Company references based on client_households table"""
    print("\n🔗 Linking Persons to Companies...")
    
    old_cur = old_conn.cursor()
    pg_cur = pg_conn.cursor()
    
    # Get client-household relationships
    old_cur.execute('''
        SELECT client_id, household_id 
        FROM client_households
        WHERE client_id IN (SELECT id FROM clients)
    ''')
    
    relations = old_cur.fetchall()
    print(f"  Found {len(relations)} client-household relationships")
    
    linked_count = 0
    
    for client_id, household_id in relations:
        if client_id in OLD_TO_NEW_PERSON and household_id in OLD_TO_NEW_COMPANY:
            person_record_id = OLD_TO_NEW_PERSON[client_id]
            company_record_id = OLD_TO_NEW_COMPANY[household_id]
            
            # Update company attribute on person record
            if 'company' in PERSON_ATTRS:
                pg_cur.execute('''
                    INSERT INTO record_values 
                    (id, record_id, attribute_id, referenced_record_id, created_at, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    str(uuid.uuid4()), person_record_id, PERSON_ATTRS['company']['id'],
                    company_record_id, datetime.now(), TARGET_USER_ID
                ))
                
                linked_count += 1
    
    pg_conn.commit()
    print(f"✅ Linked {linked_count} Persons to Companies")
    
    old_cur.close()
    pg_cur.close()
    return linked_count

def migrate_conversations(old_conn, pg_conn):
    """Migrate 21 conversations to Notes attached to Person/Company records"""
    print("\n📝 Migrating conversations to Notes...")
    
    old_cur = old_conn.cursor()
    pg_cur = pg_conn.cursor()
    
    # Get all conversations from old CRM
    old_cur.execute('''
        SELECT id, household_id, client_id, type, summary, details, date, 
               duration_minutes, follow_up_date, status, created_at, updated_at
        FROM conversations
        ORDER BY date
    ''')
    
    conversations = old_cur.fetchall()
    print(f"  Found {len(conversations)} conversations in old CRM")
    
    migrated_count = 0
    
    for conv in conversations:
        conv_id = conv['id']
        household_id = conv['household_id']
        client_id = conv['client_id']
        conv_type = conv['type']
        summary = conv['summary']
        details = conv['details']
        date = conv['date']
        duration = conv['duration_minutes']
        follow_up = conv['follow_up_date']
        status = conv['status']
        created_at = conv['created_at']
        updated_at = conv['updated_at']
        
        # Determine which record to attach to (prefer person, then company)
        target_record_id = None
        
        if client_id and client_id in OLD_TO_NEW_PERSON:
            target_record_id = OLD_TO_NEW_PERSON[client_id]
        elif household_id and household_id in OLD_TO_NEW_COMPANY:
            target_record_id = OLD_TO_NEW_COMPANY[household_id]
        
        if not target_record_id:
            print(f"  Warning: Conversation {conv_id} has no valid client/household, skipping")
            continue
        
        # Create note title from summary
        note_title = summary or f"Conversation {conv_id}"
        if len(note_title) > 100:
            note_title = note_title[:97] + "..."
        
        # Create note content JSON
        note_content = {
            'type': conv_type or 'conversation',
            'details': details or '',
            'status': status or '',
            'duration_minutes': duration,
            'original_conversation_id': conv_id
        }
        if follow_up:
            note_content['follow_up_date'] = follow_up
        
        # Parse dates
        try:
            note_date = datetime.fromisoformat(date.replace('Z', '+00:00')) if date else datetime.now()
        except:
            note_date = datetime.now()
            
        try:
            created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00')) if created_at else note_date
        except:
            created_dt = note_date
        
        # Generate note ID
        note_id = str(uuid.uuid4())
        
        # Insert note
        pg_cur.execute('''
            INSERT INTO notes 
            (id, record_id, title, content, created_by, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (
            note_id, target_record_id, note_title, 
            json.dumps(note_content), TARGET_USER_ID, 
            created_dt, created_dt
        ))
        
        migrated_count += 1
        if migrated_count % 5 == 0:
            print(f"  Migrated {migrated_count}/{len(conversations)} conversations")
    
    pg_conn.commit()
    print(f"✅ Migrated {migrated_count} conversations to Notes")
    
    old_cur.close()
    pg_cur.close()
    return migrated_count

def migrate_tasks(old_conn, pg_conn):
    """Migrate 11 tasks to Deal records"""
    print("\n💰 Migrating tasks to Deal records...")
    
    old_cur = old_conn.cursor()
    pg_cur = pg_conn.cursor()
    
    # Get all tasks from old CRM
    old_cur.execute('''
        SELECT id, household_id, client_id, title, description, priority, status, 
               due_date, completed_date, assigned_to, created_at, updated_at
        FROM tasks
        ORDER BY due_date
    ''')
    
    tasks = old_cur.fetchall()
    print(f"  Found {len(tasks)} tasks in old CRM")
    
    # Map old status to deal stage
    status_to_stage = {
        'pending': 'Lead',
        'in-progress': 'Qualified', 
        'completed': 'Won',
        'high': 'Lead',  # priority as fallback
        'medium': 'Lead',
        'low': 'Lead'
    }
    
    migrated_count = 0
    
    for task in tasks:
        task_id = task['id']
        household_id = task['household_id']
        client_id = task['client_id']
        title = task['title']
        description = task['description']
        priority = task['priority']
        status = task['status']
        due_date = task['due_date']
        completed_date = task['completed_date']
        assigned_to = task['assigned_to']
        created_at = task['created_at']
        updated_at = task['updated_at']
        
        # Deal name
        deal_name = title or f"Task {task_id}"
        
        # Generate new record ID
        record_id = str(uuid.uuid4())
        
        # Parse dates
        try:
            created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00')) if created_at else datetime.now()
        except:
            created_dt = datetime.now()
            
        try:
            updated_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00')) if updated_at else created_dt
        except:
            updated_dt = created_dt
        
        # Insert record
        pg_cur.execute('''
            INSERT INTO records (id, object_id, created_at, created_by, updated_at, sort_order)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (record_id, DEAL_OBJ_ID, created_dt, TARGET_USER_ID, updated_dt, migrated_count))
        
        # Create attribute values
        
        # 1. Name (text type)
        if 'name' in DEAL_ATTRS and deal_name:
            pg_cur.execute('''
                INSERT INTO record_values 
                (id, record_id, attribute_id, text_value, created_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                str(uuid.uuid4()), record_id, DEAL_ATTRS['name']['id'],
                deal_name, created_dt, TARGET_USER_ID
            ))
        
        # 2. Description (will be added via notes or separate attribute)
        # Note: Deal doesn't have description attribute in standard schema
        
        # 3. Stage (status type - need to get status ID)
        if 'stage' in DEAL_ATTRS:
            # Get status ID for the mapped stage
            old_status = (status or priority or '').lower()
            stage_name = status_to_stage.get(old_status, 'Lead')
            
            # Find status ID for this stage
            pg_cur.execute('''
                SELECT id FROM statuses 
                WHERE attribute_id = %s AND title = %s
                LIMIT 1
            ''', (DEAL_ATTRS['stage']['id'], stage_name))
            
            status_row = pg_cur.fetchone()
            if status_row:
                status_id = status_row[0]
                pg_cur.execute('''
                    INSERT INTO record_values 
                    (id, record_id, attribute_id, text_value, created_at, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    str(uuid.uuid4()), record_id, DEAL_ATTRS['stage']['id'],
                    status_id, created_dt, TARGET_USER_ID
                ))
        
        # 4. Expected Close Date (date type - use due_date)
        if 'expected_close_date' in DEAL_ATTRS and due_date:
            try:
                due_dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                pg_cur.execute('''
                    INSERT INTO record_values 
                    (id, record_id, attribute_id, date_value, created_at, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    str(uuid.uuid4()), record_id, DEAL_ATTRS['expected_close_date']['id'],
                    due_dt.date(), created_dt, TARGET_USER_ID
                ))
            except:
                pass
        
        # 5. Company (record_reference type - link to household)
        if 'company' in DEAL_ATTRS and household_id and household_id in OLD_TO_NEW_COMPANY:
            company_record_id = OLD_TO_NEW_COMPANY[household_id]
            pg_cur.execute('''
                INSERT INTO record_values 
                (id, record_id, attribute_id, referenced_record_id, created_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                str(uuid.uuid4()), record_id, DEAL_ATTRS['company']['id'],
                company_record_id, created_dt, TARGET_USER_ID
            ))
        
        # 6. Associated People (record_reference type - link to client)
        if 'associated_people' in DEAL_ATTRS and client_id and client_id in OLD_TO_NEW_PERSON:
            person_record_id = OLD_TO_NEW_PERSON[client_id]
            pg_cur.execute('''
                INSERT INTO record_values 
                (id, record_id, attribute_id, referenced_record_id, created_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                str(uuid.uuid4()), record_id, DEAL_ATTRS['associated_people']['id'],
                person_record_id, created_dt, TARGET_USER_ID
            ))
        
        migrated_count += 1
        if migrated_count % 5 == 0:
            print(f"  Migrated {migrated_count}/{len(tasks)} tasks")
    
    pg_conn.commit()
    print(f"✅ Migrated {migrated_count} tasks to Deal records")
    
    old_cur.close()
    pg_cur.close()
    return migrated_count

def main():
    print("=== OPENCLAW CRM DATA MIGRATION ===")
    print(f"Started at: {datetime.now()}")
    
    # Connect to databases
    old_conn = connect_old_crm()
    pg_conn = connect_new_crm()
    
    try:
        # Setup attribute mappings
        setup_attribute_mappings(pg_conn)
        
        # Run migrations
        print("\n" + "="*60)
        
        # Phase 1: Core data
        people_count = migrate_clients(old_conn, pg_conn)
        companies_count = migrate_households(old_conn, pg_conn)
        
        # Phase 2: Relationships
        links_count = update_person_company_links(old_conn, pg_conn)
        
        # Phase 3: Activities
        conversations_count = migrate_conversations(old_conn, pg_conn)
        deals_count = migrate_tasks(old_conn, pg_conn)
        
        # Summary
        print("\n" + "="*60)
        print("🎉 MIGRATION COMPLETE!")
        print("="*60)
        print(f"   People: {people_count}")
        print(f"   Companies: {companies_count}")
        print(f"   Person-Company links: {links_count}")
        print(f"   Conversations (Notes): {conversations_count}")
        print(f"   Tasks (Deals): {deals_count}")
        print(f"   Total records: {people_count + companies_count + deals_count}")
        print(f"   Total notes: {conversations_count}")
        
        print(f"\n🌐 Access your migrated CRM at: http://172.31.153.173:3001")
        print("   Login and navigate to:")
        print("   - People: All 22 clients")
        print("   - Companies: All 29 households")
        print("   - Deals: All 11 tasks in pipeline")
        print("   - Notes: Click any person/company to see conversations")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        pg_conn.rollback()
    finally:
        old_conn.close()
        pg_conn.close()
        print(f"\nMigration finished at: {datetime.now()}")

if __name__ == '__main__':
    main()