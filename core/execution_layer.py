import json
import os
import subprocess
from pathlib import Path

from core.config import ConfigManager


class OpenCodeExecutor:
    """
    Execution Layer for Dastyar.

    Deliberately NOT a BaseProvider / ModelRouter entry. OpenCode does
    not reason on Dastyar's behalf — it acts. Feature Agent hands this
    class a task description and a project directory; this class
    invokes `opencode run --format json`, parses OpenCode's own JSONL
    event stream, and returns a structured result (files touched,
    summary, success/failure) instead of a raw text blob.

    NOTE on success/failure: OpenCode has a known issue where the final
    `step_finish` event can be dropped even on a successful run
    (upstream issue #26855). So this class treats the process exit
    code as the source of truth for success/failure, and uses the
    event stream only to build up the summary/files-touched detail —
    never as the pass/fail signal itself.
    """

    DEFAULT_MODEL = "opencode/deepseek-v4-flash-free"
    DEFAULT_TIMEOUT = 600  # seconds

    def __init__(self):
        self.config = ConfigManager()

    def _project_dir(self):
        configured = self.config.get("ACTIVE_PROJECT_PATH")

        if configured:
            # Defensive: core/config.py does NOT expand shell variables
            # (it just strips quotes), so a value like
            # "$HOME/ai-server/projects/k-V4" would otherwise come
            # through completely unexpanded and literal. Expand here so
            # that gotcha can't silently break this specific path.
            return os.path.expanduser(os.path.expandvars(configured))

        # Fallback: matches what's documented in memory/progress.md
        return str(Path.home() / "ai-server" / "projects" / "k-V4")

    def execute(self, task: str, project_dir: str = None, model: str = None) -> dict:

        project_dir = project_dir or self._project_dir()
        model = model or self.config.get("OPENCODE_MODEL", self.DEFAULT_MODEL)

        try:
            result = subprocess.run(
                [
                    "opencode",
                    "run",
                    "--format", "json",
                    "--dir", project_dir,
                    "--model", model,
                    task,
                ],
                capture_output=True,
                text=True,
                timeout=self.DEFAULT_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            return {
                "status": "failed",
                "reason": (
                    f"OpenCode did not finish within {self.DEFAULT_TIMEOUT}s. "
                    f"This can happen if it's waiting on an interactive "
                    f"permission prompt with no terminal attached — check "
                    f"whether the task requires a tool action (e.g. bash) "
                    f"that isn't pre-approved for this agent."
                ),
                "files_touched": [],
                "summary": "",
            }
        except FileNotFoundError:
            return {
                "status": "failed",
                "reason": "`opencode` command not found on PATH.",
                "files_touched": [],
                "summary": "",
            }

        files_touched = []
        text_parts = []
        error_messages = []

        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue

            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                # OpenCode occasionally writes non-JSON noise to stdout
                # alongside the event stream; skip lines that aren't
                # valid JSON rather than failing the whole parse.
                continue

            etype = event.get("type")

            if etype == "tool_use":
                part = event.get("part", {}) or {}
                tool = part.get("tool")
                state = part.get("state", {}) or {}
                tool_input = state.get("input", {}) or {}

                if tool in ("write", "edit"):
                    path = tool_input.get("filePath") or tool_input.get("path")
                    if path:
                        files_touched.append(path)

            elif etype == "text":
                text = (event.get("part", {}) or {}).get("text")
                if text:
                    text_parts.append(text)

            elif etype == "error":
                message = (event.get("error", {}) or {}).get("data", {}).get(
                    "message", "unknown error"
                )
                error_messages.append(message)

        files_touched = list(dict.fromkeys(files_touched))  # de-dupe, keep order
        summary = "\n".join(text_parts).strip()

        if result.returncode != 0 or error_messages:
            reason = "; ".join(error_messages) or result.stderr.strip() or (
                f"opencode exited with code {result.returncode}"
            )
            return {
                "status": "failed",
                "reason": reason,
                "files_touched": files_touched,
                "summary": summary,
            }

        return {
            "status": "ok",
            "reason": None,
            "files_touched": files_touched,
            "summary": summary or "(OpenCode reported no text summary)",
        }
