"""
Lore Agent — maintains the Project Bible: characters, locations, timeline, continuity.
"""

from openai import AsyncOpenAI
import json

SYSTEM_PROMPT = """You are the Lore Agent — the keeper of the Project Bible.

Your job:
- Track characters, locations, timeline, and world rules
- Maintain narrative continuity across all chapters
- Extract and structure information from story content
- Suggest additions to the Bible when the story expands

When asked to extract info, return a JSON structure:
{
  "characters": [{"name": "...", "description": "...", "role": "..."}],
  "locations": [{"name": "...", "description": "..."}],
  "notes": "..."
}

When asked to track continuity, identify any inconsistencies found."""


class LoreAgent:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    async def execute(self, task: str, project_name: str, messages: list[dict]) -> str:
        content = task
        if project_name and project_name != "__none__":
            from backend.core.project_manager import load_project
            try:
                bible = load_project(project_name)
                context = f"Project: {bible.get('title', project_name)}\n"
                existing = {"characters": bible.get("characters", []), "locations": bible.get("locations", [])}
                context += "Existing Bible data: " + json.dumps(existing, indent=2)
                content = context + "\n\nTask: " + task
            except Exception:
                pass

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content or ""
