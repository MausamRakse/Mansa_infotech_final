import os
import sys
from dotenv import load_dotenv

# Add parent directory to path to import services
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services import supabase_service

def test_mapping():
    load_dotenv()
    test_agent_id = "test_agent_123"
    test_user_id = "00000000-0000-0000-0000-000000000000" # Dummy UUID
    
    print(f"Testing mapping with Agent: {test_agent_id}, User: {test_user_id}...")
    try:
        supabase_service.add_agent_mapping(test_agent_id, test_user_id)
        print("Success!")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_mapping()
