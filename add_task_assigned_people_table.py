#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(host='localhost', port=5433, user='jcw_l', database='openclaw')
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS task_assigned_records (
  task_id text NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  record_id text NOT NULL REFERENCES records(id) ON DELETE CASCADE
)
""")
cur.execute("CREATE INDEX IF NOT EXISTS task_assigned_records_task_id_idx ON task_assigned_records(task_id)")
cur.execute("CREATE INDEX IF NOT EXISTS task_assigned_records_record_id_idx ON task_assigned_records(record_id)")
conn.commit()
cur.close()
conn.close()
print('created task_assigned_records')
