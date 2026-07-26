# AI-Driven Creative Studio

A modular, local-first AI-powered studio for writing, art generation, comics, animation, and film production. Powered by a multi-agent LLM backend with a Director orchestrator pattern.

## Architecture

```
ai-studio/
├── backend/              # FastAPI Python backend
│   ├── agents/           # AI Agents: Director, Writer, Editor, Lore, Artist
│   │   ├── director.py   # Orchestrator — routes tasks to specialists
│   │   ├── writer.py     # Creative writing, chapters, dialogue
│   │   ├── editor.py     # Polish, grammar, continuity
│   │   ├── lore.py       # Project Bible keeper
│   │   └── artist.py     # ComfyUI image generation
│   ├── api/routes.py     # REST endpoints
│   ├── core/
│   │   ├── project_manager.py  # Bible CRUD
│   │   ├── agent_router.py     # Routes to agents
│   │   └── exporter.py         # Markdown, PDF, EPUB export
│   └── main.py           # Entry point
├── frontend/             # Vite + React UI
│   └── src/
│       ├── App.jsx       # Main app with all views
│       ├── App.css       # Dark-themed Sith styling
│       └── api.js        # Backend API client
├── projects/             # Local project Bibles (gitignored)
├── .env                  # Local config (gitignored)
└── requirements.txt
```

## Quick Start

### Backend

```bash
cd ai-studio
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Edit .env with your LLM endpoint
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8800
```

### Frontend

```bash
cd frontend
npm install
npm run build         # Production build
# OR for development:
npm run dev           # Dev server at localhost:5173
```

Then open `http://localhost:5173` (dev) or navigate to `/studio/` through nginx (production).

## Configuration

Edit `.env`:

| Variable | Description | Default |
|---|---|---|
| `OPENAI_API_KEY` | API key for LLM provider | — |
| `OPENAI_BASE_URL` | LLM endpoint URL | `http://192.168.10.121:7900/v1` |
| `OPENAI_MODEL` | Model name | `deepseek-v4-flash` |
| `STUDIO_DATA_DIR` | Project storage directory | `./projects` |
| `COMFY_BASE_URL` | ComfyUI endpoint | `http://192.168.10.121/comfy` |

## Features

### Project Bible
Every project has a structured "Bible" that stores all creative data:
- **Overview** — Story summary and high-level vision
- **Story Outline** — Numbered plot points to guide chapter writing
- **World Rules** — Established constraints and logic of your universe
- **Characters** — Bios, roles, descriptions, and optional AI-generated portraits
- **Locations** — Settings and environments with descriptions
- **Timeline** — Chronological events tracking key story moments
- **Chapters** — Full chapter content with inline editing
- **Generated Images** — Gallery of all ComfyUI art created for the project
- **Art Presets** — Reusable style templates for fast image generation

### Director Chat
The primary interface for creative assistance. The Director agent orchestrates four specialist sub-agents:
- **Writer** — Writes chapters, scenes, dialogue, expands outlines into prose
- **Editor** — Improves clarity, pacing, tone; fixes grammar and continuity
- **Lore** — Updates the Project Bible with characters, locations, timelines, and notes
- **Artist** — Generates images, character portraits, scene art using ComfyUI

### Write Next Chapter
One-click agentic chapter generation. Reads the entire Bible context (overview, outline, existing chapters, characters, world rules, locations) and uses the LLM to write and save the next chapter automatically. Access the button at the bottom of the Chapters tab.

### Art Generation
Generate images via ComfyUI on a remote GPU (RTX 5070 Ti). Supports:
- Custom prompts and negative prompts
- Model selection from available ComfyUI checkpoints
- Resolution, steps, and CFG controls
- Gallery view with lightbox fullscreen
- Character portrait generation (one-click from character cards)

### Art Style Presets
Save and reuse art configurations:
- **Save** current settings (model, size, steps, CFG, negative prompt) with a name and optional prompt suffix
- **Apply** a preset from the dropdown menu in the art controls row
- **Apply** from preset cards shown below the gallery
- **Delete** unwanted presets

### Export
Export complete projects in three formats:
- **Markdown (.md)** — Full text with metadata
- **PDF** — Typeset document with title page, table of contents, and embedded images
- **EPUB** — E-book format with chapter navigation and image gallery

## API

### Project Management
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/projects` | List all projects |
| `POST` | `/api/projects` | Create a new project |
| `GET` | `/api/projects/{name}` | Get project Bible |
| `DELETE` | `/api/projects/{name}` | Delete a project |

### Bible Sections
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/projects/{name}/overview` | Set overview |
| `POST` | `/api/projects/{name}/outline` | Add story outline point |
| `DELETE` | `/api/projects/{name}/outline/{index}` | Delete outline point |
| `POST` | `/api/projects/{name}/rules` | Add world rule |
| `DELETE` | `/api/projects/{name}/rules/{index}` | Delete world rule |
| `POST` | `/api/projects/{name}/timeline` | Add timeline entry |
| `DELETE` | `/api/projects/{name}/timeline/{entry_id}` | Delete timeline entry |

### Characters
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/projects/{name}/characters` | Add character |
| `DELETE` | `/api/projects/{name}/characters/{id}` | Delete character |
| `POST` | `/api/projects/{name}/characters/{id}/portrait` | Generate character portrait via ComfyUI |

### Chapters
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/projects/{name}/chapters` | Add chapter |
| `PATCH` | `/api/projects/{name}/chapters/{id}` | Update chapter (inline editing) |
| `POST` | `/api/projects/{name}/chapters/generate` | Auto-generate next chapter from Bible context |

### Art
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/comfyui/models` | List available ComfyUI models |
| `POST` | `/api/projects/{name}/generate` | Generate image via ComfyUI |
| `GET` | `/api/projects/{name}/images/{filename}` | Serve generated image |
| `POST` | `/api/projects/{name}/presets` | Save art style preset |
| `DELETE` | `/api/projects/{name}/presets/{id}` | Delete art style preset |

### Director Chat
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Chat with Director agent |

### Export
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/projects/{name}/export/markdown` | Export as Markdown |
| `GET` | `/api/projects/{name}/export/pdf` | Export as PDF |
| `GET` | `/api/projects/{name}/export/epub` | Export as EPUB |

Full API docs at `http://localhost:8800/docs` when running.
