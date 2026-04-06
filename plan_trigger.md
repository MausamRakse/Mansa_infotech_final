# Logic Upgrade Plan: Auto-Saving Transcripts & Recordings for Specific Agents

## 1. Ensuring Specific Agent Usage during Call Trigger
**Problem:** Currently, if a user clicks on a newly created agent and clicks "Trigger Call", they might experience unexpected behavior. If the agent ID is not numeric or fails to parse, the system silently falls back to the default `TABBLY_AGENT_ID` environments variable, bypassing the selected agent.
**Solution:** 
- In `backend/services/tabbly.py` -> `trigger_call`, we will update the logic to explicitly check if the `agent_id` is a default UI mock agent (e.g., `"default-1"`). If so, we use the `TABBLY_AGENT_ID`. If not, we enforce using the exact `agent_id` provided. If it is invalid, we will throw a clear exception to prevent silently calling with the wrong agent.

## 2. Auto-fetching Transcripts and Recordings (`fetch_call_data.py` integration)
**Problem:** `fetch_call_data.py` is a standalone script that only fetches logs for `TABBLY_AGENT_ID`, ignoring any new agents you create. You want this feature built directly into the dashboard and updated for *all* agents whenever a call ends.
**Solution:** 
- Merge the save-to-disk functionality of `fetch_call_data.py` directly into the backend dashboard's `logs.py`. 
- Since the frontend polls `/logs/call-logs` automatically, we will inspect the data structure on each pull. 
- If a log contains a `transcript` or `call_recording_url`, the backend will check the local `transcripts/` or `recordings/` directories using your predefined filename structure (`call_{id}_{called_to}_{created_at}`).
- If the files do not exist locally, the backend will automatically download and save the text file and mp3 file seamlessly in the background without needing to run `fetch_call_data.py` manually.

By doing this, any specific agent engaged in a call will have its results tracked, and its respective transcription/audio files downloaded locally to the directories instantly upon call completion.
