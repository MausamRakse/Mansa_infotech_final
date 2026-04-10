import psycopg2

DB_URL = "postgresql://postgres:%40Convexa_123@db.kkmftbhqfmgaixqnwked.supabase.co:5432/postgres"

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()
cur.execute("SELECT relrowsecurity FROM pg_class WHERE relname = 'agent_mappings';")
res = cur.fetchone()
print("RLS Enabled:", res[0])
conn.close()
