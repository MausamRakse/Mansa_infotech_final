from middleware.auth import supabase

def add_agent_mapping(agent_id: str, user_id: str, cal_api_key: str = "", cal_event_type_id: str = ""):
    """Maps a Tabbly agent_id to a Supabase user_id with optional config."""
    try:
        data = {
            "agent_id": agent_id, 
            "user_id": user_id,
            "cal_api_key": cal_api_key,
            "cal_event_type_id": cal_event_type_id,
            "meeting_enabled": True
        }
        supabase.table('agent_mappings').insert(data).execute()
    except Exception as e:
        if "PGRST204" in str(e) or "column" in str(e).lower():
            print("\n⚠️ DATABASE SCHEMA MISMATCH: Please run the SQL to add 'cal_api_key' columns to 'agent_mappings'.")
            # Fallback: Insert only basic mapping
            supabase.table('agent_mappings').insert({"agent_id": agent_id, "user_id": user_id}).execute()
        else:
            print(f"Error mapping agent: {e}")
            raise

def get_user_agent_mappings(user_id: str):
    """Fetches full mapping objects for a specific user."""
    try:
        response = supabase.table('agent_mappings').select('*').eq('user_id', user_id).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching agent mappings: {e}")
        return []

def get_user_agent_ids(user_id: str):
    """Fetches just the Tabbly agent_ids mapped to a specific user_id."""
    try:
        response = supabase.table('agent_mappings').select('agent_id').eq('user_id', user_id).execute()
        return [row['agent_id'] for row in response.data]
    except Exception as e:
        print(f"Error fetching agent ids: {e}")
        return []

def update_agent_mapping(agent_id: str, user_id: str, cal_api_key: str = None, cal_event_type_id: str = None, meeting_enabled: bool = None):
    """Updates meta-config for an agent mapping."""
    try:
        data = {}
        if cal_api_key is not None: data["cal_api_key"] = cal_api_key
        if cal_event_type_id is not None: data["cal_event_type_id"] = cal_event_type_id
        if meeting_enabled is not None: data["meeting_enabled"] = meeting_enabled
        
        if data:
            supabase.table('agent_mappings').update(data).eq('agent_id', agent_id).eq('user_id', user_id).execute()
    except Exception as e:
        if "PGRST204" in str(e) or "column" in str(e).lower():
            print("\n⚠️ DATABASE SCHEMA MISMATCH: Update skipped for secondary columns. Please add 'cal_api_key' to your table.")
        else:
            print(f"Error updating agent mapping: {e}")
            raise

def delete_agent_mapping(agent_id: str):
    """Deletes mapping when an agent is deleted."""
    try:
        supabase.table('agent_mappings').delete().eq('agent_id', agent_id).execute()
    except Exception as e:
        print(f"Error deleting agent mapping: {e}")
        raise

def log_meeting(user_id: str, agent_id: str, call_id: str, status: str, 
                extracted_email: str = None, meeting_topic: str = None, 
                is_interested: bool = None, error_reason: str = None):
    """Logs the outcome of a meeting booking attempt."""
    try:
        data = {
            "user_id": user_id,
            "agent_id": str(agent_id),
            "call_id": str(call_id),
            "status": status,
            "extracted_email": extracted_email,
            "meeting_topic": meeting_topic,
            "is_interested": is_interested,
            "error_reason": error_reason
        }
        supabase.table('meeting_logs').insert(data).execute()
        print(f"📝 Meeting log saved: {status} for Call {call_id}")
    except Exception as e:
        print(f"⚠️ Error logging meeting: {e}")

def get_meeting_logs(user_id: str):
    """Fetches meeting logs for the user."""
    try:
        response = supabase.table('meeting_logs').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching meeting logs: {e}")
        return []

