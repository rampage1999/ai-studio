"""
Editor Agent — improves clarity, pacing, tone; fixes grammar and continuity.
"""

from openai import AsyncOpenAI

SYSTEM_PROMPT = """You are the Editor Agent — a sharp-eyed creative editor.

Your expertise:
- Improving clarity, pacing, and tone
- Fixing grammar, spelling, and punctuation
- Checking narrative continuity and consistency
- Suggesting structural improvements
- Maintaining the project's voice while polishing

Be constructive. Point out what works AND what could improve.
When editing, show the original and your suggested revision clearly."""


class EditorAgent:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    async def execute(self, task: str, project_name: str, messages: list[dict]) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": task},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content or ""
