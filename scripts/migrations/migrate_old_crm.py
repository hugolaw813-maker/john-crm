#!/usr/bin/env python3
"""
Migration script from old SQLite CRM to new OpenClaw PostgreSQL CRM
Transforms:
- 22 clients → Person objects
- 29 households → Company objects  
- 11 tasks → Deal objects
- 21 conversations → Note objects
"""

import sqlite3
import psycopg2
import sys
from datetime import datetime

def connect_old_crm():
    """Connect to old SQLite CRM"""
    db_path = '/home/jcw_l/.openclaw/workspace-sarah/secure-crm/data/crm.db'
    try:
        conn = sqlite3.connect(db_path)
        print(f"✅ Connected to old CRM at {db_path}")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to old CRM: {e}")
        sys.exit(1)

def connect_new_crm():
    """Connect to new PostgreSQL CRM"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5433,
            user='jcw_l',
            database='openclaw'
        )
        print("✅ Connected to new PostgreSQL CRM")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to new CRM: {e}")
        sys.exit(1)

def get_object_mapping(pg_conn):
    """Get object IDs from new CRM"""
    cur = pg_conn.cursor()
    cur.execute("SELECT id, name, slug FROM objects ORDER BY id")
    objects = cur.fetchall()
    mapping = {}
    for obj_id, name, slug in objects:
        mapping[slug] = {'id': obj_id, 'name': name}
    cur.close()
    return mapping

def get_attribute_mapping(pg_conn, object_mapping):
    """Get attribute IDs for each object"""
    cur = pg_conn.cursor()
    attribute_map = {}
    
    for slug, obj_info in object_mapping.items():
        obj_id = obj_info['id']
        cur.execute("""
            SELECT a.id, a.slug, a.name, a.type
            FROM attributes a
            JOIN object_attributes oa ON a.id = oa.attribute_id
            WHERE oa.object_id = %s
            ORDER BY a.name
        """, (obj_id,))
        attrs = cur.fetchall()
        attribute_map[obj_id] = {}
        for attr_id, attr_slug, attr_name, attr_type in attrs:
            attribute_map[obj_id][attr_slug] = {
                'id': attr_id,
                'name': attr_name,
                'type': attr_type
            }
    
    cur.close()
    return attribute_map

def get_status_mapping(pg_conn):
    """Get deal status IDs"""
    cur = pg_conn.cursor()
    cur.execute("SELECT id, name, slug FROM statuses ORDER BY position")
    statuses = cur.fetchall()
    status_map = {}
    for status_id, status_name, status_slug in statuses:
        status_map[status_slug] = {'id': status_id, 'name': status_name}
    cur.close()
    return status_map

def migrate_clients_to_people(old_conn, pg_conn, object_mapping, attribute_map):
    """Migrate 22 clients to Person objects"""
    print("\n📋 Migrating clients to Person objects...")
    
    old_cur = old_conn.cursor()
    pg_cur = pg_conn.cursor()
    
    # Get person object ID
    person_obj_id = object_mapping['person']['id']
    person_attrs = attribute_map[person_obj_id]
    
    # Get all clients from old CRM
    old_cur.execute("""
        SELECT id, first_name, last_name, email, phone, status, notes, created_at, updated_at
        FROM clients
        ORDER BY id
    """)
    
    clients = old_cur.fetchall()
    print(f"  Found {len(clients)} clients in old CRM")
    
    migrated_count = 0
    for client in clients:
        client_id, first_name, last_name, email, phone, status, notes, created_at, updated_at = client
        
        # Create person record
        full_name = f"{first_name} {last_name}".strip()
        if not full_name:
            full_name = email or f"Client {client_id}"
        
        pg_cur.execute("""
            INSERT INTO records (object_id, name, created_at, updated_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (person_obj_id, full_name, created_at or datetime.now(), updated_at or datetime.now()))
        
        record_id = pg_cur.fetchone()[0]
        
        # Add attribute values
        attributes_to_add = []
        
        # Full name
        if 'full-name' in person_attrs and full_name:
            attributes_to_add.append((
                record_id,
                person_attrs['full-name']['id'],
                'text',
                full_name
            ))
        
        # Email
        if 'email' in person_attrs and email:
            attributes_to_add.append((
                record_id,
                person_attrs['email']['id'],
                'text',
                email
            ))
        
        # Phone
        if 'phone' in person_attrs and phone:
            attributes_to_add.append((
                record_id,
                person_attrs['phone']['id'],
                'text',
                str(phone) if phone else None
            ))
        
        # Job title (use status field)
        if 'job-title' in person_attrs and status:
            attributes_to_add.append((
                record_id,
                person_attrs['job-title']['id'],
                'text',
                status
            ))
        
        # Notes
        if 'notes' in person_attrs and notes:
            attributes_to_add.append((
                record_id,
                person_attrs['notes']['id'],
                'text',
                notes
            ))
        
        # Insert all attribute values
        for attr_value in attributes_to_add:
            pg_cur.execute("""
                INSERT INTO attribute_values (record_id, attribute_id, type, value)
                VALUES (%s, %s, %s, %s)
            """, attr_value)
        
        migrated_count += 1
        if migrated_count % 5 == 0:
            print(f"  Migrated {migrated_count}/{len(clients)} clients")
    
    pg_conn.commit()
    print(f"✅ Migrated {migrated_count} clients to Person objects")
    
    old_cur.close()
    pg_cur.close()
    return migrated_count

def migrate_households_to_companies(old_conn, pg_conn, object_mapping, attribute_map):
    """Migrate 29 households to Company objects"""
    print("\n🏢 Migrating households to Company objects...")
    
    old_cur = old_conn.cursor()
    pg_cur = pg_conn.cursor()
    
    # Get company object ID
    company_obj_id = object_mapping['company']['id']
    company_attrs = attribute_map[company_obj_id]
    
    # Get all households from old CRM
    old_cur.execute("""
        SELECT id, name, slug, created_at, updated_at
        FROM households
        ORDER BY id
    """)
    
    households = old_cur.fetchall()
    print(f"  Found {len(households)} households in old CRM")
    
    migrated_count = 0
    for household in households:
        household_id, name, slug, created_at, updated_at = household
        
        # Create company record
        company_name = name or f"Household {household_id}"
        
        pg_cur.execute("""
            INSERT INTO records (object_id, name, created_at, updated_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (company_obj_id, company_name, created_at or datetime.now(), updated_at or datetime.now()))
        
        record_id = pg_cur.fetchone()[0]
        
        # Add attribute values
        attributes_to_add = []
        
        # Company name
        if 'company-name' in company_attrs and company_name:
            attributes_to_add.append((
                record_id,
                company_attrs['company-name']['id'],
                'text',
                company_name
            ))
        
        # Website (use slug)
        if 'website' in company_attrs and slug:
            # Create a simple URL from slug
            website = f"https://example.com/{slug}" if slug else None
            attributes_to_add.append((
                record_id,
                company_attrs['website']['id'],
                'text',
                website
            ))
        
        # Industry (default)
        if 'industry' in company_attrs:
            attributes_to_add.append((
                record_id,
                company_attrs['industry']['id'],
                'text',
                "Household"
            ))
        
        # Insert all attribute values
        for attr_value in attributes_to_add:
            pg_cur.execute("""
                INSERT INTO attribute_values (record_id, attribute_id, type, value)
                VALUES (%s, %s, %s, %s)
            """, attr_value)
        
        migrated_count += 1
        if migrated_count % 5 == 0:
            print(f"  Migrated {migrated_count}/{len(households)} households")
    
    pg_conn.commit()
    print(f"✅ Migrated {migrated_count} households to Company objects")
    
    old_cur.close()
    pg_cur.close()
    return migrated_count

def migrate_tasks_to_deals(old_conn, pg_conn, object_mapping, attribute_map, status_map):
    """Migrate 11 tasks to Deal objects"""
    print("\n💰 Migrating tasks to Deal objects...")
    
    old_cur = old_conn.cursor()
    pg_cur = pg_conn.cursor()
    
    # Get deal object ID
    deal_obj_id = object_mapping['deal']['id']
    deal_attrs = attribute_map[deal_obj_id]
    
    # Get all tasks from old CRM
    old_cur.execute("""
        SELECT id, title, description, priority, status, due_date, created_at, updated_at
        FROM tasks
        ORDER BY id
    """)
    
    tasks = old_cur.fetchall()
    print(f"  Found {len(tasks)} tasks in old CRM")
    
    # Map old status to new status slugs
    status_mapping = {
        'pending': 'new',
        'in-progress': 'in-progress',
        'completed': 'won',
        'high': 'new',  # priority as fallback
        'medium': 'new',
        'low': 'new'
    }
    
    migrated_count = 0
    for task in tasks:
        task_id, title, description, priority, status, due_date, created_at, updated_at = task
        
        # Create deal record
        deal_name = title or f"Task {task_id}"
        
        pg_cur.execute("""
            INSERT INTO records (object_id, name, created_at, updated_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (deal_obj_id, deal_name, created_at or datetime.now(), updated_at or datetime.now()))
        
        record_id = pg_cur.fetchone()[0]
        
        # Add attribute values
        attributes_to_add = []
        
        # Deal name
        if 'deal-name' in deal_attrs and deal_name:
            attributes_to_add.append((
                record_id,
                deal_attrs['deal-name']['id'],
                'text',
                deal_name
            ))
        
        # Description
        if 'description' in deal_attrs and description:
            attributes_to_add.append((
                record_id,
                deal_attrs['description']['id'],
                'text',
                description
            ))
        
        # Amount (use priority as pseudo-amount)
        if 'amount' in deal_attrs:
            amount_map = {'high': 10000, 'medium': 5000, 'low': 1000}
            amount = amount_map.get(priority, 1000) if priority else 1000
            attributes_to_add.append((
                record_id,
                deal_attrs['amount']['id'],
                'number',
                str(amount)
            ))
        
        # Status
        if 'status' in deal_attrs:
            # Map old status to new status
            old_status = (status or priority or '').lower()
            new_status_slug = status_mapping.get(old_status, 'new')
            status_id = status_map.get(new_status_slug, {}).get('id')
            
            if status_id:
                attributes_to_add.append((
                    record_id,
                    deal_attrs['status']['id'],
                    'status',
                    str(status_id)
                ))
        
        # Priority
        if 'priority' in deal_attrs and priority:
            attributes_to_add.append((
                record_id,
                deal_attrs['priority']['id'],
                'text',
                priority
            ))
        
        # Due date
        if 'close-date' in deal_attrs and due_date:
            attributes_to_add.append((
                record_id,
                deal_attrs['close-date']['id'],
                'date',
                due_date
            ))
        
        # Insert all attribute values
        for attr_value in attributes_to_add:
            pg_cur.execute("""
                INSERT INTO attribute_values (record_id, attribute_id, type, value)
                VALUES (%s, %s, %s, %s)
            """, attr_value)
        
        migrated_count += 1
        if migrated_count % 5 == 0:
            print(f"  Migrated {migrated_count}/{len(tasks)} tasks")
    
    pg_conn.commit()
    print(f"✅ Migrated {migrated_count} tasks to Deal objects")
    
    old_cur.close()
    pg_cur.close()
    return migrated_count

def migrate_conversations_to_notes(old_conn, pg_conn, object_mapping, attribute_map):
    """Migrate 21 conversations to Note objects"""
    print("\n📝 Migrating conversations to Note objects...")
    
    old_cur = old_conn.cursor()
    pg_cur = pg_conn.cursor()
    
    # Get note object ID
    note_obj_id = object_mapping['note']['id']
    note_attrs = attribute_map[note_obj_id]
    
    # Get all conversations from old CRM
    old_cur.execute("""
        SELECT id, summary, type, date, household_name, created_at, updated_at
        FROM conversations
        ORDER BY id
    """)
    
    conversations = old_cur.fetchall()
    print(f"  Found {len(conversations)} conversations in old CRM")
    
    migrated_count = 0
    for conv in conversations:
        conv_id, summary, conv_type, date, household_name, created_at, updated_at = conv
        
        # Create note record
        note_name = summary or f"Conversation {conv_id}"
        
        pg_cur.execute("""
            INSERT INTO records (object_id, name, created_at, updated_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (note_obj_id, note_name, created_at or datetime.now(), updated_at or datetime.now()))
        
        record_id = pg_cur.fetchone()[0]
        
        # Add attribute values
        attributes_to_add = []
        
        # Note content (summary)
        if 'content' in note_attrs and summary:
            attributes_to_add.append((
                record_id,
                note_attrs['content']['id'],
                'text',
                summary
            ))
        
        # Note type
        if 'type' in note_attrs and conv_type:
            attributes_to_add.append((
                record_id,
                note_attrs['type']['id'],
                'text',
                conv_type
            ))
        
        # Date
        if 'date' in note_attrs and date:
            attributes_to_add.append((
                record_id,
                note_attrs['date']['id'],
                'date',
                date
            ))
        
        # Related to (household name)
        if 'related-to' in note_attrs and household_name:
            # Note: This would need to link to actual company record
            # For now, store as text
            attributes_to_add.append((
                record_id,
                note_attrs['related-to']['id'],
                'text',
                household_name
            ))
        
        # Insert all attribute values
        for attr_value in attributes_to_add:
            pg_cur.execute("""
                INSERT INTO attribute_values (record_id, attribute_id, type, value)
                VALUES (%s, %s, %s, %s)
            """, attr_value)
        
        migrated_count += 1
        if migrated_count % 5 == 0:
            print(f"  Migrated {migrated_count}/{len(conversations)} conversations")
    
    pg_conn.commit()
    print(f"✅ Migrated {migrated_count} conversations to Note objects")
    
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
        # Get schema mappings
        object_mapping = get_object_mapping(pg_conn)
        attribute_map = get_attribute_mapping(pg_conn, object_mapping)
        status_map = get_status_mapping(pg_conn)
        
        print(f"\n📊 Objects found: {len(object_mapping)}")
        for slug, info in object_mapping.items():
            print(f"  - {info['name']} (ID: {info['id']})")
        
        # Run migrations
        people_count = migrate_clients_to_people(old_conn, pg_conn, object_mapping, attribute_map)
        companies_count = migrate_households_to_companies(old_conn, pg_conn, object_mapping, attribute_map)
        deals_count = migrate_tasks_to_deals(old_conn, pg_conn, object_mapping, attribute_map, status_map)
        notes_count = migrate_conversations_to_notes(old_conn, pg_conn, object_mapping, attribute_map)
        
        # Summary
        print(f"\n🎉 MIGRATION COMPLETE!")
        print(f"   People: {people_count}")
        print(f"   Companies: {companies_count}")
        print(f"   Deals: {deals_count}")
        print(f"   Notes: {notes_count}")
        print(f"   Total records: {people_count + companies_count + deals_count + notes_count}")
        print(f"\n🌐 Access your migrated CRM at: http://172.31.153.173:3001")
        
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