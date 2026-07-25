"""
Director Agent — the user's primary interface. Delegates to other agents.
"""

import json
from typing import Any

from openai import AsyncOpenAI

SYSTEM_PROMPT = """You are the Studio Director — a creative project manager and AI agent orchestrator.

Your role:
- You are the user's primary interface for the AI Studio.
- The user talks to YOU, and you decide which specialist agents to call.
- You maintain the high-level creative vision.

You have access to these specialist agents:
- **Writer** — writes chapters, scenes, dialogue, expands outlines into prose
- **Editor** — improves clarity, pacing, tone; fixes grammar and continuity
- **Lore** — updates the Project Bible with characters, locations, timelines, and notes

Your workflow:
1. Understand what the user wants
2. Decide which agent(s) to invoke
3. Return the results to the user

When you need to call an agent, respond with a JSON block:
{
  "agent": "writer|editor|lore",
  "task": "detailed instructions for the agent"
}

Then after receiving the agent's output, present it to the user naturally.

If the user's request doesn't need an agent (simple questions, status checks, etc.),
just respond conversationally.

Always keep the project's creative vision consistent. Speak like a confident director
who knows their team's strengths."""


class DirectorAgent:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    async def process(
        self,
        message: str,
        project_name: str,
        messages: list[dict],
        agents: dict[str, Any],
    ) -> str:
        """Process a user message, potentially delegating to sub-agents."""

        # Build conversation for the director
        sys_msg = SYSTEM_PROMPT
        if project_name and project_name != "__none__":
            from backend.core.project_manager import load_project
            try:
                bible = load_project(project_name)
                sys_msg += f"\n\nCurrent project: {bible.get('title', project_name)}\nGenre: {bible.get('genre', '')}\nTone: {bible.get('tone', '')}\n"
            except Exception:
                pass

        chat_messages = [{"role": "system", "content": sys_msg}]
        for m in messages[-20:]:  # Last 20 messages for context
            chat_messages.append(m)
        chat_messages.append({"role": "user", "content": message})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=chat_messages,
            temperature=0.7,
        )

        content = response.choices[0].message.content or ""

        # Check if director delegated to an agent
        import re
        agent_match = re.search(r'\{\s*"agent"\s*:\s*"(\w+)"\s*,\s*"task"\s*:\s*"((?:[^"\\]|\\.)*)"\s*\}', content, re.DOTALL)
        if agent_match:
            agent_name = agent_match.group(1)
            task = agent_match.group(2)
            agent = agents.get(agent_name)
            if agent:
                result = await agent.execute(task, project_name, messages)
                return f"[Director delegated to **{agent_name.title()}**]\n\n{result}"

        return content
