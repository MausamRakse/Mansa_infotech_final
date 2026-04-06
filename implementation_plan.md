# Call Logs Enhancement Plan

## Objective
Update the application to:
1. Show the `agent_name` associated with each call log.
2. Ensure Call Logs continuously update in the foreground so transcripts and recordings appear automatically immediately after a call ends.

## Changes Required

### 1. Backend (`backend/routers/logs.py` and `backend/routers/agents.py`)
- Modify `backend/routers/agents.py` to expose its `_agents_db` data so that we can retrieve agent IDs and their mapped names.
- Modify `backend/routers/logs.py` to iterate over all active agent IDs when fetching logs.
  - This includes the default `.env` `TABBLY_AGENT_ID` (names as "Default Agent" if not overriden) and every agent created in `_agents_db`.
  - For each agent, handle fetch errors gracefully so that one bad agent ID does not break the entire `/logs/call-logs` endpoint.
  - Inject the corresponding `agent_name` into the call log response object.
  - Sort the final combined list of logs in descending order by `date`.

### 2. Frontend Types (`frontend/src/api/client.ts`)
- Update the `CallLog` TypeScript interface to include an `agent_name` string property.

### 3. Frontend UI & Auto-Update (`frontend/src/pages/CallLogs.tsx`)
- Add an "Agent" column to the logs table to display the newly integrated `agent_name`.
- Implement a robust polling mechanism (auto-update) using React's `useEffect` and `setInterval`.
  - This will repeatedly call `fetchCallLogs` every 5 seconds while the user is on the Call Logs page.
  - As soon as a call is ended, its status will automatically change locally from "Processing" to "Completed", and the recording URL and transcript string will appear without the user refreshing manually.
