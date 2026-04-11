#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect('postgresql://jcw_l@localhost:5433/openclaw')
cur = conn.cursor()

cur.execute("ALTER TABLE notes ADD COLUMN IF NOT EXISTS note_date timestamp")
cur.execute("UPDATE notes SET note_date = created_at WHERE note_date IS NULL")
cur.execute("ALTER TABLE notes ALTER COLUMN note_date SET DEFAULT now()")
cur.execute("ALTER TABLE notes ALTER COLUMN note_date SET NOT NULL")

conn.commit()
cur.close()
conn.close()
print('done')
