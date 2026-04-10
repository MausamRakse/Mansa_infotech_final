import psycopg2
import os

DB_URL = "postgresql://postgres:%40Convexa_123@db.kkmftbhqfmgaixqnwked.supabase.co:5432/postgres"
try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    tables = cur.fetchall()
    print("Tables:", tables)
    conn.close()
except Exception as e:
    print("Error:", e)
