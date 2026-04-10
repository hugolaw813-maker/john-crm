#!/usr/bin/env python3
import psycopg2
conn = psycopg2.connect(dbname='openclaw', user='jcw_l', host='/tmp')
cur = conn.cursor()
cur.execute("""
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'list_attributes'
ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(r)
cur.close(); conn.close()
