"""
Writer Agent — writes chapters, scenes, dialogue, expands outlines into prose.
"""

from openai import AsyncOpenAI

SYSTEM_PROMPT = """You are the Writer Agent — a creative writer who brings stories to life.

Your expertise:
- Writing chapters, scenes, and dialogue
- Expanding outlines into full prose
- Maintaining consistent voice and tone
- Creating vivid descriptions and engaging narrative

When given a task, write compelling, high-quality creative content.
Match the project's genre, tone, and style.
Be specific and detailed — show, don't just tell."""


class WriterAgent:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    async def execute(self, task: str, project_name: str, messages: list[dict]) -> str:
        content = task
        if project_name and project_name != "__none__":
            from backend.core.project_manager import load_project
            try:
                bible = load_project(project_name)
                context = f"Project: {bible.get('title', project_name)}\nGenre: {bible.get('genre', '')}\nTone: {bible.get('tone', '')}\n\n"
                if bible.get("overview"):
                    context += f"Overview: {bible['overview']}\n\n"
                if bible.get("characters"):
                    context += "Characters:\n" + "\n".join(
                        f"- {c.get('name', '?')}: {c.get('description', '')[:100]}"
                        for c in bible["characters"]
                    ) + "\n\n"
                content = context + "Task: " + task
            except Exception:
                pass

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
            temperature=0.8,
        )
        return response.choices[0].message.content or ""
