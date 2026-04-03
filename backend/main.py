from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import agents, calls, logs

app = FastAPI(title="Voice AI Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router)
app.include_router(calls.router)
app.include_router(logs.router)
