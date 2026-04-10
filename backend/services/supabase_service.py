import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("SUPABASE_DB_URL")

def get_db_connection():
    return psycopg2.connect(DB_URL)

def add_agent_mapping(agent_id: str, user_id: str):
    """Maps a Tabbly agent_id to a Supabase user_id."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO public.agent_mappings (agent_id, user_id) VALUES (%s, %s)",
            (agent_id, user_id)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()

def get_user_agent_ids(user_id: str):
    """Fetches all Tabbly agent_ids mapped to a specific user_id."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT agent_id FROM public.agent_mappings WHERE user_id = %s",
            (user_id,)
        )
        return [row[0] for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

def delete_agent_mapping(agent_id: str):
    """Deletes mapping when an agent is deleted."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "DELETE FROM public.agent_mappings WHERE agent_id = %s",
            (agent_id,)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()
