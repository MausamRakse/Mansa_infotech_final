import psycopg2

pooler_url = "postgresql://postgres.kkmftbhqfmgaixqnwked:%40Convexa_123@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"

print("Connecting to ap-south-1 pooler...")
try:
    conn = psycopg2.connect(pooler_url)
    print("Success ap-south-1 !!!")
    conn.close()
except Exception as e:
    print("Error:", e)

