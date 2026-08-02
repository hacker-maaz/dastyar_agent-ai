from pathlib import Path

from agents.base_agent import BaseAgent
from agents.memory_manager import format_shared_memory
from models.model_router import ModelRouter

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class ReviewAgent(BaseAgent):

    def __init__(self):
        self.router = ModelRouter()

    def run(self, command, task, context):

        prompt = (PROMPTS_DIR / "review.md").read_text()

        full_prompt = f"""
{prompt}

Command:
{command}

Task:
{task}

Shared Memory:
{format_shared_memory(context)}

Previous Agent Output:
{context.get("previous_output", "")}
"""

        return self.router.generate(
            full_prompt,
            agent="review",
        )
