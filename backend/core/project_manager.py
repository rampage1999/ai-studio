"""
Project Manager — the heart of the Project Bible system.

Every AI Studio project has a structured "Bible" that stores all
creative data: characters, locations, chapters, timeline, art, etc.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

DATA_DIR = os.environ.get("STUDIO_DATA_DIR", "./projects")


def _project_path(project_name: str) -> Path:
    return Path(DATA_DIR) / project_name


def _bible_path(project_name: str) -> Path:
    return _project_path(project_name) / "bible.json"


# ──────────────────────────────────────────
#  Project CRUD
# ──────────────────────────────────────────


def create_project(name: str, title: str, genre: str, tone: str = "") -> dict:
    """Create a new project with an empty Bible."""
    path = _project_path(name)
    if path.exists():
        raise FileExistsError(f"Project '{name}' already exists at {path}")

    path.mkdir(parents=True, exist_ok=True)

    bible = {
        "title": title,
        "genre": genre,
        "tone": tone,
        "created": datetime.utcnow().isoformat(),
        "updated": datetime.utcnow().isoformat(),
        "overview": "",
        "story_outline": [],
        "chapters": [],
        "characters": [],
        "locations": [],
        "timeline": [],
        "themes_and_tone": {},
        "world_rules": [],
        "art_prompts": [],
        "generated_images": [],
        "comfyui_settings": {},
        "blender_assets": [],
        "notes": [],
        "version_history": [],
    }

    # Create subdirectories
    for sub in ("chapters", "characters", "locations", "images", "notes"):
        (path / sub).mkdir(exist_ok=True)

    _write_bible(name, bible)
    return bible


def load_project(name: str) -> dict:
    """Load a project Bible from disk."""
    path = _bible_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Project '{name}' not found at {path}")
    with open(path) as f:
        return json.load(f)


def save_project(name: str, bible: dict) -> dict:
    """Save an updated project Bible."""
    bible["updated"] = datetime.utcnow().isoformat()
    _write_bible(name, bible)
    return bible


def _write_bible(name: str, bible: dict) -> None:
    path = _bible_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(bible, f, indent=2, default=str)


def list_projects() -> list[dict]:
    """List all projects with basic info (no full Bible)."""
    data_dir = Path(DATA_DIR)
    if not data_dir.exists():
        return []
    projects = []
    for item in sorted(data_dir.iterdir()):
        bible_file = item / "bible.json"
        if bible_file.exists():
            try:
                with open(bible_file) as f:
                    bible = json.load(f)
                projects.append({
                    "name": item.name,
                    "title": bible.get("title", item.name),
                    "genre": bible.get("genre", ""),
                    "tone": bible.get("tone", ""),
                    "updated": bible.get("updated", ""),
                    "chapter_count": len(bible.get("chapters", [])),
                    "character_count": len(bible.get("characters", [])),
                })
            except Exception:
                projects.append({"name": item.name, "title": item.name, "error": True})
    return projects


def delete_project(name: str) -> None:
    """Delete an entire project directory."""
    import shutil
    path = _project_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Project '{name}' not found")
    shutil.rmtree(path)


# ──────────────────────────────────────────
#  Bible Section Helpers
# ──────────────────────────────────────────


def add_chapter(project_name: str, chapter: dict) -> dict:
    bible = load_project(project_name)
    chapter.setdefault("id", _next_id(bible["chapters"]))
    chapter.setdefault("created", datetime.utcnow().isoformat())
    chapter.setdefault("content", "")
    bible["chapters"].append(chapter)
    _add_to_version_history(bible, f"Added chapter: {chapter.get('title', 'Untitled')}")
    return save_project(project_name, bible)


def update_chapter(project_name: str, chapter_id: str, updates: dict) -> dict:
    bible = load_project(project_name)
    for ch in bible["chapters"]:
        if ch.get("id") == chapter_id:
            ch.update(updates)
            ch["updated"] = datetime.utcnow().isoformat()
            _add_to_version_history(bible, f"Updated chapter: {ch.get('title', chapter_id)}")
            return save_project(project_name, bible)
    raise ValueError(f"Chapter '{chapter_id}' not found")


def add_character(project_name: str, character: dict) -> dict:
    bible = load_project(project_name)
    character.setdefault("id", _next_id(bible["characters"]))
    bible["characters"].append(character)
    _add_to_version_history(bible, f"Added character: {character.get('name', 'Untitled')}")
    return save_project(project_name, bible)


def add_location(project_name: str, location: dict) -> dict:
    bible = load_project(project_name)
    location.setdefault("id", _next_id(bible["locations"]))
    bible["locations"].append(location)
    return save_project(project_name, bible)


def set_overview(project_name: str, overview: str) -> dict:
    bible = load_project(project_name)
    bible["overview"] = overview
    _add_to_version_history(bible, "Updated overview")
    return save_project(project_name, bible)


# ──────────────────────────────────────────
#  Internals
# ──────────────────────────────────────────


def _next_id(items: list[dict]) -> str:
    return str(max((int(it.get("id", 0)) for it in items), default=0) + 1)


def _add_to_version_history(bible: dict, description: str) -> None:
    bible.setdefault("version_history", []).append({
        "timestamp": datetime.utcnow().isoformat(),
        "description": description,
    })
