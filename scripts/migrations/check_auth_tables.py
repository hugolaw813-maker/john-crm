#!/usr/bin/env python3
"""
Check authentication tables and users
"""

import psycopg2

PG_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'jcw_l',
    'database': 'openclaw'
}

def check_tables():
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    print('=== DATABASE TABLES ===')
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    
    tables = [row[0] for row in cur.fetchall()]
    for table in tables:
        print(f'  {table}')
    
    # Check for auth-related tables
    auth_tables = [t for t in tables if 'auth' in t.lower() or 'user' in t.lower() or 'session' in t.lower()]
    print('\n=== AUTH-RELATED TABLES ===')
    for table in auth_tables:
        print(f'\n{table}:')
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' ORDER BY ordinal_position")
        cols = [row[0] for row in cur.fetchall()]
        print(f'  Columns: {cols}')
        
        # Show row count
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f'  Row count: {count}')
        
        # Show sample data
        if count > 0:
            cur.execute(f"SELECT * FROM {table} LIMIT 3")
            rows = cur.fetchall()
            for i, row in enumerate(rows):
                print(f'  Row {i}:')
                for col, val in zip(cols, row):
                    if 'password' not in col.lower() and 'token' not in col.lower():
                        print(f'    {col}: {val}')
    
    # Specifically check for users table
    if 'users' in tables:
        print('\n=== USERS TABLE DETAIL ===')
        cur.execute("SELECT id, email, name, created_at FROM users ORDER BY created_at")
        users = cur.fetchall()
        print(f'Total users: {len(users)}')
        for user_id, email, name, created_at in users:
            print(f'  {email} ({name}) - ID: {user_id}, Created: {created_at}')
    
    # Check workspace_members for user associations
    print('\n=== WORKSPACE MEMBERS ===')
    cur.execute('''
        SELECT wm.user_id, wm.role, w.name as workspace_name, u.email, u.name
        FROM workspace_members wm
        JOIN workspaces w ON wm.workspace_id = w.id
        LEFT JOIN users u ON wm.user_id = u.id
        ORDER BY w.name, wm.role
    ''')
    
    members = cur.fetchall()
    print(f'Total workspace memberships: {len(members)}')
    for user_id, role, workspace_name, email, name in members:
        print(f'  {workspace_name}: {email or user_id} ({name}) - {role}')
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    check_tables()