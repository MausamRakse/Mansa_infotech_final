import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import agents, calls, logs, campaigns

app = FastAPI(title="convexa.ai")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prefix all real API routes with /api so they don't clash with React's client-side router
app.include_router(agents.router, prefix="/api")
app.include_router(calls.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(campaigns.router, prefix="/api")

# Serve the static React build inside the unified server
frontend_dist = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../frontend/dist")

# Only mount if dist exists (e.g., after building for Production)
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        # Fallback to index.html for React Router
        return FileResponse(os.path.join(frontend_dist, "index.html"))
