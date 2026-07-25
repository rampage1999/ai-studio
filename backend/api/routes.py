"""
API Routes — endpoints for the AI Studio frontend.
"""

import json
import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.core.project_manager import (
    create_project,
    load_project,
    save_project,
    list_projects,
    delete_project,
    add_chapter,
    update_chapter,
    add_character,
    add_location,
    set_overview,
)
from backend.core.agent_router import AgentRouter

router = APIRouter(prefix="/api")

# Lazy-init router
_agent_router: Optional[AgentRouter] = None


def get_router():
    global _agent_router
    if _agent_router is None:
        _agent_router = AgentRouter(
            api_key=os.environ.get("OPENAI_API_KEY", ""),
            base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        )
    return _agent_router


# ──────────────────────────────────────────
#  Request/Response models
# ──────────────────────────────────────────


class CreateProjectRequest(BaseModel):
    name: str
    title: str
    genre: str
    tone: str = ""


class ChatRequest(BaseModel):
    message: str
    project_name: str = "__none__"
    messages: list[dict] = []


class ChapterCreateRequest(BaseModel):
    title: str
    content: str = ""


class ChapterUpdateRequest(BaseModel):
    content: Optional[str] = None
    title: Optional[str] = None


class CharacterCreateRequest(BaseModel):
    name: str
    description: str = ""
    role: str = ""


class LocationCreateRequest(BaseModel):
    name: str
    description: str = ""


# ──────────────────────────────────────────
#  Routes
# ──────────────────────────────────────────


@router.get("/projects")
async def api_list_projects():
    """List all projects."""
    return {"projects": list_projects()}


@router.post("/projects")
async def api_create_project(req: CreateProjectRequest):
    """Create a new project."""
    try:
        bible = create_project(req.name, req.title, req.genre, req.tone)
        return {"success": True, "project": req.name, "bible": bible}
    except FileExistsError as e:
        raise HTTPException(409, str(e))


@router.get("/projects/{name}")
async def api_get_project(name: str):
    """Get a project's full Bible."""
    try:
        bible = load_project(name)
        return {"success": True, "project": name, "bible": bible}
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))


@router.delete("/projects/{name}")
async def api_delete_project(name: str):
    """Delete a project."""
    try:
        delete_project(name)
        return {"success": True}
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))


@router.post("/projects/{name}/overview")
async def api_set_overview(name: str, data: dict):
    """Set the project overview."""
    try:
        bible = set_overview(name, data.get("overview", ""))
        return {"success": True, "bible": bible}
    except FileNotFoundError:
        raise HTTPException(404)


@router.post("/projects/{name}/chapters")
async def api_add_chapter(name: str, req: ChapterCreateRequest):
    """Add a chapter to a project."""
    try:
        bible = add_chapter(name, {"title": req.title, "content": req.content})
        chapter = bible["chapters"][-1] if bible["chapters"] else {}
        return {"success": True, "chapter": chapter}
    except FileNotFoundError:
        raise HTTPException(404)


@router.patch("/projects/{name}/chapters/{chapter_id}")
async def api_update_chapter(name: str, chapter_id: str, req: ChapterUpdateRequest):
    """Update a chapter's content or title."""
    updates = {k: v for k, v in req.dict(exclude_unset=True).items() if v is not None}
    try:
        bible = update_chapter(name, chapter_id, updates)
        return {"success": True, "bible": bible}
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(404, str(e))


@router.post("/projects/{name}/characters")
async def api_add_character(name: str, req: CharacterCreateRequest):
    """Add a character to a project."""
    try:
        bible = add_character(name, {"name": req.name, "description": req.description, "role": req.role})
        char = bible["characters"][-1] if bible["characters"] else {}
        return {"success": True, "character": char}
    except FileNotFoundError:
        raise HTTPException(404)


@router.post("/projects/{name}/locations")
async def api_add_location(name: str, req: LocationCreateRequest):
    """Add a location to a project."""
    try:
        bible = add_location(name, {"name": req.name, "description": req.description})
        loc = bible["locations"][-1] if bible["locations"] else {}
        return {"success": True, "location": loc}
    except FileNotFoundError:
        raise HTTPException(404)


@router.post("/chat")
async def api_chat(req: ChatRequest):
    """Send a message to the Director agent."""
    router = get_router()
    response = await router.chat(req.message, req.project_name, req.messages)
    return {"response": response}


@router.get("/health")
async def health():
    return {"status": "ok", "service": "ai-studio"}
