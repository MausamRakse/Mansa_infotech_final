import psycopg2

# Correct Supabase pooler format: 
# postgresql://[user].[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres

# The user is 'postgres'
# The project ref is 'kkmftbhqfmgaixqnwked'
# Password is '@Convexa_123' (which is %40Convexa_123)

pooler_url = "postgresql://postgres.kkmftbhqfmgaixqnwked:%40Convexa_123@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

print("Connecting to pooler...")
try:
    conn = psycopg2.connect(pooler_url)
    print("Success!!!")
    conn.close()
except Exception as e:
    print("Error:", e)

