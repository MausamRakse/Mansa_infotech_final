from middleware.auth import supabase

def add_agent_mapping(agent_id: str, user_id: str):
    """Maps a Tabbly agent_id to a Supabase user_id via REST API."""
    try:
        response = supabase.table('agent_mappings').insert({"agent_id": agent_id, "user_id": user_id}).execute()
    except Exception as e:
        print(f"Error mapping agent: {e}")
        raise

def get_user_agent_ids(user_id: str):
    """Fetches all Tabbly agent_ids mapped to a specific user_id via REST API."""
    try:
        response = supabase.table('agent_mappings').select('agent_id').eq('user_id', user_id).execute()
        return [row['agent_id'] for row in response.data]
    except Exception as e:
        print(f"Error fetching agent ids: {e}")
        raise

def delete_agent_mapping(agent_id: str):
    """Deletes mapping when an agent is deleted via REST API."""
    try:
        response = supabase.table('agent_mappings').delete().eq('agent_id', agent_id).execute()
    except Exception as e:
        print(f"Error deleting agent mapping: {e}")
        raise

