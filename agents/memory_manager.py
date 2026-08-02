import os
from pathlib import Path

from core.config import ConfigManager
from core.project_files import read_files, find_files_mentioned_in_text

EXCLUDE_DIRS = {
    ".git", ".gradle", "build", ".idea", "node_modules",
    ".venv", "__pycache__", ".ruff_cache",
}

MAX_FILES_LISTED = 400


class MemoryManager:
    """
    Loads three kinds of context for agents:

    1. Shared Memory — the hand-maintained .md files in memory/.

    2. Project Structure — a live file-tree snapshot of the actual
       project, generated fresh every run.

    3. Relevant File Contents — best-effort: if the task text
       literally names a file that exists in the project (e.g. "add a
       comment to MainActivity.kt"), that file's real current content
       is read and included, so Planner isn't reasoning about a file
       it's never actually seen. This is a guess made before anything
       has been touched — Review Agent gets a precise version of this
       instead, populated by the Orchestrator from OpenCode's own
       reported file list, not from this heuristic.
    """

    def __init__(self):
        self.memory_dir = Path(__file__).resolve().parent.parent / "memory"
        self.config = ConfigManager()

    def load(self, task: str = None) -> dict:
        context = {}

        if self.memory_dir.exists():
            for file in self.memory_dir.glob("*.md"):
                context[file.stem] = file.read_text(encoding="utf-8")

        project_structure = self._project_structure()
        context["project_structure"] = project_structure

        if task:
            matched_files = find_files_mentioned_in_text(task, project_structure)
            if matched_files:
                context["relevant_file_contents"] = read_files(
                    matched_files, self._project_dir()
                )

        return context

    def _project_dir(self) -> Path:
        configured = self.config.get("ACTIVE_PROJECT_PATH")

        if configured:
            return Path(os.path.expanduser(os.path.expandvars(configured)))

        return Path.home() / "ai-server" / "projects" / "k-V4"

    def _project_structure(self) -> str:
        project_dir = self._project_dir()

        if not project_dir.exists():
            return "(project directory not found — ACTIVE_PROJECT_PATH may be misconfigured)"

        lines = []

        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [
                d for d in dirs
                if d not in EXCLUDE_DIRS and not d.startswith(".")
            ]

            rel_root = Path(root).relative_to(project_dir)

            for f in sorted(files):
                rel_path = (rel_root / f) if str(rel_root) != "." else Path(f)
                lines.append(str(rel_path))

                if len(lines) >= MAX_FILES_LISTED:
                    lines.append("... (truncated — project has more files than shown)")
                    return "\n".join(lines)

        return "\n".join(lines) if lines else "(no files found in project directory)"


def format_shared_memory(context: dict) -> str:
    """
    Clean, readable markdown for a prompt instead of a raw Python
    dict dump.
    """
    skip_keys = {"command", "task", "previous_output", "workflow"}
    handled_separately = {"project_structure", "relevant_file_contents"}

    sections = []

    project_structure = context.get("project_structure")
    if project_structure:
        sections.append(f"## Project File Structure\n{project_structure}")

    relevant_file_contents = context.get("relevant_file_contents")
    if relevant_file_contents:
        sections.append(f"## Relevant File Contents\n{relevant_file_contents}")

    for key, value in context.items():
        if key in skip_keys or key in handled_separately:
            continue
        if not value or not str(value).strip():
            continue
        sections.append(f"## {key}\n{value}")

    return "\n\n".join(sections) if sections else "(no shared memory available yet)"
