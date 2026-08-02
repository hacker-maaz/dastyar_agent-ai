import re
from pathlib import Path

from agents.base_agent import BaseAgent
from agents.memory_manager import format_shared_memory
from models.model_router import ModelRouter

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
MEMORY_DIR = Path(__file__).resolve().parent.parent / "memory"

FILE_BLOCK_RE = re.compile(
    r"===FILE:\s*([\w.\-]+)===\n(.*?)\n===END===",
    re.DOTALL,
)


class DocumentationAgent(BaseAgent):

    def __init__(self):
        self.router = ModelRouter()

    def run(self, command, task, context):

        prompt = (PROMPTS_DIR / "docs.md").read_text()

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

        raw_output = self.router.generate(
            full_prompt,
            agent="documentation",
        )

        written_files = []

        for filename, content in FILE_BLOCK_RE.findall(raw_output):
            MEMORY_DIR.mkdir(parents=True, exist_ok=True)
            (MEMORY_DIR / filename).write_text(content.strip() + "\n", encoding="utf-8")
            written_files.append(filename)

        if not written_files:
            return (
                "Documentation Agent produced no file updates "
                "(no ===FILE: ...=== blocks found in its output)."
            )

        file_list = "\n".join(f"- {name}" for name in written_files)
        return f"Documentation done in files\n{file_list}"
