import psycopg2
import os

DB_URL = "postgresql://postgres:%40Convexa_123@db.kkmftbhqfmgaixqnwked.supabase.co:5432/postgres"
try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT id, email FROM public.profiles")
    profiles = cur.fetchall()
    print("Profiles:", profiles)
    
    cur.execute("SELECT id, email FROM auth.users")
    users = cur.fetchall()
    print("Auth Users:", users)
    
    conn.close()
except Exception as e:
    print("Error:", e)
