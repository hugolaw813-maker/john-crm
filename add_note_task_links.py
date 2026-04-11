#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect('postgresql://jcw_l@localhost:5433/openclaw')
cur = conn.cursor()

statements = [
    "ALTER TABLE notes ADD COLUMN IF NOT EXISTS note_type text NOT NULL DEFAULT 'note'",
    "ALTER TABLE notes ADD COLUMN IF NOT EXISTS linked_task_id text",
    "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS source_note_id text",
]

for sql in statements:
    cur.execute(sql)
    print(sql)

conn.commit()
cur.close()
conn.close()
print('done')
