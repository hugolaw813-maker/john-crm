#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(host='localhost', port=5433, user='jcw_l', database='openclaw')
cur = conn.cursor()
cur.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS priority text NOT NULL DEFAULT 'medium';")
conn.commit()
cur.close()
conn.close()
print('added tasks.priority')
