from pathlib import Path

from agents.base_agent import BaseAgent
from agents.memory_manager import format_shared_memory
from core.project_files import read_files
from models.model_router import ModelRouter

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class PlannerAgent(BaseAgent):

    # Hard cap regardless of what the model returns — keeps prompt
    # size and cost bounded even if the scout call misbehaves.
    MAX_SCOUT_FILES = 5

    def __init__(self):
        self.router = ModelRouter()

    def _scout_files(self, task, project_structure):
        """
        A small, cheap fallback call: asks which files (if any) are
        worth actually reading for this task. Only called when the
        cheap heuristic in memory_manager.py (literal filename match)
        already came up empty — e.g. "fix the login bug" names no
        file, so there's nothing for that heuristic to match.

        Safety: the model's suggestions are validated against the
        REAL file listing before anything is read. A hallucinated or
        modified path is silently dropped, never trusted as-is.
        """
        if not project_structure or not project_structure.strip():
            return []

        scout_prompt = (PROMPTS_DIR / "planner_scout.md").read_text()

        full_prompt = f"""
{scout_prompt}

Task:
{task}

Project File Structure:
{project_structure}
"""

        try:
            response = self.router.generate(full_prompt, agent="planner")
        except Exception:
            # A failed scout call shouldn't block planning entirely —
            # just fall back to planning without extra file content.
            return []

        response = (response or "").strip()

        if not response or response.upper() == "NONE":
            return []

        listed_paths = {
            line.strip()
            for line in project_structure.splitlines()
            if line.strip() and not line.strip().startswith("...")
        }

        candidates = [line.strip() for line in response.splitlines() if line.strip()]
        valid = [p for p in candidates if p in listed_paths]

        return valid[: self.MAX_SCOUT_FILES]

    def run(self, command, task, context):

        prompt = (PROMPTS_DIR / "planner.md").read_text()

        # Fast path: the cheap heuristic already found something (task
        # literally named a file) — no need to spend a second call
        # rediscovering it.
        if not context.get("relevant_file_contents"):
            project_structure = context.get("project_structure", "")
            scouted_paths = self._scout_files(task, project_structure)
            if scouted_paths:
                context["relevant_file_contents"] = read_files(scouted_paths)

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
            agent="planner",
        )
