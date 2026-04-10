import psycopg2

DB_URL = "postgresql://postgres:%40Convexa_123@db.kkmftbhqfmgaixqnwked.supabase.co:5432/postgres"

print("Disabling RLS on agent_mappings...")
try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("ALTER TABLE public.agent_mappings DISABLE ROW LEVEL SECURITY;")
    conn.commit()
    print("Success!")
    conn.close()
except Exception as e:
    print("Error:", e)

