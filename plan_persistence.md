# Stateless Tabbly Architecture Plan

## The Objective
You want to completely eliminate backend memory (`_agents_db`) so that your FastAPI server acts purely as a stateless proxy. This means when you restart the system, it will automatically pull all created agents straight from Tabbly, ensuring that everything is always perfectly in sync and never disappears.

## The Strategy: "Stateless Proxy"

### Step 1: Remove Temporary Memory
We will delete the `_agents_db = {}` dictionary inside `backend/routers/agents.py`. The backend will no longer attempt to save or manage agents internally. 

### Step 2: Implement Tabbly Fetch Routine
We will update the `GET /agents/` endpoint so that instead of returning a backend memory object, it makes an immediate REST API request directly to Tabbly's servers (e.g. `GET or POST to Tabbly's List Agents endpoint`) using your `TABBLY_API_KEY`. 

### Step 3: Passthrough Execution
- **List/Get**: Dashboard calls `GET /agents/` -> Backend proxies the call to Tabbly -> Returns true list of agents.
- **Update**: Dashboard calls `POST /agents/update-agent` -> Backend hits Tabbly's `POST https://tabbly.io/api/update-agent` natively (which we already wired!).
- **Delete**: Dashboard calls `POST /agents/delete-agent` -> Backend hits Tabbly's `POST https://tabbly.io/api/delete-agent` natively (which we already wired!).

### Result
Once this is implemented, you could restart your backend 1,000 times a day and it would not matter. The system will hold zero memory natively and instead pull the freshest list of your created agents straight from Tabbly every time you load the page!
