"""
AI Driven Creative Studio — FastAPI Backend Entry Point.

Run with:
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(
    title="AI Driven Creative Studio",
    description="A modular, local-first AI-powered studio for writing, art generation, comics, animation, and film production.",
    version="0.1.0",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure data directory exists
data_dir = os.environ.get("STUDIO_DATA_DIR", "./projects")
Path(data_dir).mkdir(parents=True, exist_ok=True)

# Register routes
from backend.api.routes import router
app.include_router(router)


@app.on_event("startup")
async def startup():
    print(f"  Studio data directory: {data_dir}")
    print(f"  API docs: http://localhost:8000/docs")
