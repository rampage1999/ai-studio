# AI-Driven Creative Studio

A modular, local-first AI-powered studio for writing, art generation, comics, animation, and film production. Powered by a multi-agent LLM backend with a discord-director orchestrator pattern.

## Architecture

```
ai-studio/
├── backend/              # FastAPI Python backend
│   ├── agents/           # AI Agents: Director, Writer, Editor, Lore
│   │   ├── director.py   # Orchestrator — routes tasks to specialists
│   │   ├── writer.py     # Creative writing, chapters, dialogue
│   │   ├── editor.py     # Polish, grammar, continuity
│   │   └── lore.py       # Project Bible keeper
│   ├── api/routes.py     # REST endpoints
│   ├── core/
│   │   ├── project_manager.py  # Bible CRUD
│   │   └── agent_router.py     # Routes to agents
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
npm run dev
```

Then open `http://localhost:5173` in your browser.

## Configuration

Edit `.env`:

| Variable | Description | Default |
|---|---|---|
| `OPENAI_API_KEY` | API key for LLM provider | — |
| `OPENAI_BASE_URL` | LLM endpoint URL | `http://192.168.10.121:7900/v1` |
| `OPENAI_MODEL` | Model name | `deepseek-v4-flash` |
| `STUDIO_DATA_DIR` | Project storage directory | `./projects` |

## API

- `GET /api/health` — Health check
- `GET /api/projects` — List projects
- `POST /api/projects` — Create project
- `GET /api/projects/{name}` — Get project Bible
- `POST /api/projects/{name}/chapters` — Add chapter
- `POST /api/projects/{name}/characters` — Add character
- `POST /api/projects/{name}/locations` — Add location
- `POST /api/chat` — Chat with Director agent

Full API docs at `http://localhost:8800/docs` when running.
