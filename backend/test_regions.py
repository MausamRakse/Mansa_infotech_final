import psycopg2

regions = [
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1",
    "ap-south-1", "ap-southeast-1", "ap-southeast-2", "ap-northeast-1", "ap-northeast-2",
    "sa-east-1", "ca-central-1"
]

password = "%40Convexa_123"
project_ref = "kkmftbhqfmgaixqnwked"

for reg in regions:
    url = f"postgresql://postgres.{project_ref}:{password}@aws-0-{reg}.pooler.supabase.com:6543/postgres"
    try:
        conn = psycopg2.connect(url, connect_timeout=3)
        print(f"SUCCESS region is: {reg}")
        conn.close()
        break
    except Exception as e:
        if "Tenant or user not found" not in str(e):
            print(f"Region {reg} failed with different error: {e}")
