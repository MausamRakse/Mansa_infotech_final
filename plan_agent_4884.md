# Mapping Agent 4884 Plan

## Request
Connect Agent ID **4884** to both "Support Hub" and "Outreach Campaigns" templates, and display this agent's logs natively as "Support Hub".

## Execution Steps

### 1. Update Environment Variables (`backend/.env`)
- We will modify the `.env` file to set `TABBLY_AGENT_ID=4884`.
- *Why:* The system relies on this fallback environment variable to establish the "old" connection. By plugging `4884` directly into `.env`, both `default-1` (Support Hub card) and `default-2` (Outreach Campaigns card) will seamlessly adopt this Tabbly ID. 

### 2. Verify Call Logic Processing (`backend/services/tabbly.py`)
- We previously formulated explicit logic stating that any request starting with `default-` will bind directly to `TABBLY_AGENT_ID`. No code changes are required here, meaning both cards will correctly funnel into agent `4884`.

### 3. Verify Log Identification (`backend/routers/logs.py`)
- In `backend/routers/logs.py`, the `DEFAULT_AGENT_ID` reads straight from the environment variable. It is currently configured to label every call associated with `TABBLY_AGENT_ID` as "Support Hub".
- Therefore, the logs fetched for agent `4884` (regardless of whether you clicked Support Hub or Outreach Campaigns to initiate it) will seamlessly map to the "Support Hub" namesake.

By executing this simple `.env` swap, your entire dashboard will cleanly snap to agent `4884`.
