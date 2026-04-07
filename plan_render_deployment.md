# Render Single-Service Deployment Plan

## Objective
To host both the React (`frontend`) and FastAPI (`backend`) inside the **exact same Web Service** on Render.com, eliminating the need for two separate services.

## The Architecture
Instead of running a Node.js server and a Python server simultaneously, we utilize **FastAPI** as the master server. 
During the build process, we compile the React Code into raw HTML/JS/CSS files. Then, we configure FastAPI to natively serve those raw files directly to the user's browser, while independently keeping its API endpoints active on the `/api` route. 

## What Has Already Been Implemented
1. **API Prefixing**: FastAPI's internal code (`main.py`) has been shifted so that its endpoints now securely exist at `/api/agents`, `/api/logs`, etc. The UI's `client.ts` file now aims directly at these `/api` prefixes, preventing route collisions.
2. **Static Routing**: `main.py` is configured to dynamically mount `./frontend/dist/` directly onto its base web path.
3. **The Master Build Script**: A `build.sh` file sits in the root directory. This script automates compiling the Frontend via `npm` and then installing the Backend via `pip` sequentially.

## Your Final Steps on Render.com
To launch this live, go to Render, click "New Web Service", link your GitHub, and fill out exactly these settings:

1. **Environment:** `Python 3`
2. **Root Directory:** *(leave completely blank)*
3. **Build Command:** 
   ```bash
   bash build.sh
   ```
4. **Start Command:**
   ```bash
   cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

Because everything is hard-wired in the codebase, applying those dashboard settings will launch your full-stack app seamlessly!
