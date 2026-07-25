"""
Agent Router — routes user requests to the right agent.
"""

from typing import Any

from backend.agents.director import DirectorAgent
from backend.agents.writer import WriterAgent
from backend.agents.editor import EditorAgent
from backend.agents.lore import LoreAgent


class AgentRouter:
    """Routes tasks to the appropriate agent based on intent."""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.director = DirectorAgent(api_key, base_url, model)
        self.writer = WriterAgent(api_key, base_url, model)
        self.editor = EditorAgent(api_key, base_url, model)
        self.lore = LoreAgent(api_key, base_url, model)

    async def chat(self, message: str, project_name: str, messages: list[dict]) -> str:
        """
        Process a user message through the Director agent.
        The Director decides which sub-agent(s) to call.
        """
        return await self.director.process(
            message=message,
            project_name=project_name,
            messages=messages,
            agents={
                "writer": self.writer,
                "editor": self.editor,
                "lore": self.lore,
            },
        )
