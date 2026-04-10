import psycopg2

pooler_url = "postgresql://postgres.kkmftbhqfmgaixqnwked:%40Convexa_123@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

print("Connecting to pooler...")
try:
    conn = psycopg2.connect(pooler_url)
    print("Success!")
    conn.close()
except Exception as e:
    print("Error:", e)

