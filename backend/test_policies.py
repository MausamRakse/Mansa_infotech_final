import psycopg2

DB_URL = "postgresql://postgres:%40Convexa_123@db.kkmftbhqfmgaixqnwked.supabase.co:5432/postgres"
conn = psycopg2.connect(DB_URL)
cur = conn.cursor()
cur.execute("SELECT polname, polcmd, polqual FROM pg_policy WHERE polrelid = 'agent_mappings'::regclass;")
for row in cur.fetchall():
    print(row)
conn.close()
