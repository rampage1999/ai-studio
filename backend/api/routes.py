"""
API Routes — endpoints for the AI Studio frontend.
"""

import json
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
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
from backend.agents.artist import list_models, generate_image

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


# ──────────────────────────────────────────
#  ComfyUI / Image Generation Routes
# ──────────────────────────────────────────


@router.get("/comfyui/models")
async def api_list_models():
    """List available ComfyUI checkpoints."""
    models = list_models()
    return {"models": models}


class GenerateRequest(BaseModel):
    prompt: str
    negative_prompt: str = ""
    model: str = "dreamShaper.safetensors"
    width: int = 1024
    height: int = 1024
    seed: int = -1
    steps: int = 25
    cfg: float = 7.0


@router.post("/projects/{name}/generate")
async def api_generate(name: str, req: GenerateRequest):
    """Generate an image via ComfyUI and save to project."""
    # Verify project exists first
    from backend.core.project_manager import load_project
    try:
        load_project(name)
    except FileNotFoundError:
        raise HTTPException(404, f"Project '{name}' not found")

    result = generate_image(
        prompt=req.prompt,
        negative_prompt=req.negative_prompt,
        model=req.model,
        width=req.width,
        height=req.height,
        seed=req.seed,
        steps=req.steps,
        cfg=req.cfg,
        project_name=name,
    )

    if "error" in result:
        raise HTTPException(500, detail=result["error"])

    # Update the project Bible with the generated image entry
    bible = load_project(name)
    bible.setdefault("generated_images", []).append(result["generated_images_entry"])
    from backend.core.project_manager import save_project
    save_project(name, bible)

    return {"success": True, "result": result}


@router.get("/projects/{name}/images/{filename:path}")
async def api_serve_image(name: str, filename: str):
    """Serve a generated image from a project's images directory."""
    data_dir = os.environ.get("STUDIO_DATA_DIR", "./projects")
    img_path = Path(data_dir) / name / "images" / filename

    if not img_path.exists():
        # Check in the _generated fallback
        img_path = Path(data_dir) / "_generated" / filename

    if not img_path.exists() or not img_path.is_file():
        raise HTTPException(404, f"Image '{filename}' not found")

    import mimetypes
    mime, _ = mimetypes.guess_type(str(img_path))
    return FileResponse(str(img_path), media_type=mime or "image/png")

