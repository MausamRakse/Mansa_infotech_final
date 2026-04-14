import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import agents, calls, logs, campaigns, users, webhooks

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
app.include_router(users.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")

# Serve the static React build inside the unified server
frontend_dist = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../frontend/dist")

if os.path.exists(frontend_dist):
    # Mount the assets directory specifically for faster serving
    assets_path = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
    
    # Catch-all route to serve the frontend for any other path (React Router support)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # If the file exists in dist, serve it (for favicon, manifest, etc.)
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        # Otherwise, fall back to index.html for CSR
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    @app.get("/")
    def read_root():
        return {"message": "API is running. Build the frontend to serve the dashboard."}
