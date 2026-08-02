import subprocess

from models.base_provider import BaseProvider
from core.config import ConfigManager


class GeminiProviderCLI(BaseProvider):
    """
    Gemini CLI provider.
    Uses the locally authenticated Gemini CLI instead of the API.

    NOTE: no longer used by ModelRouter (see models/gemini_provider_sdk.py).
    The Gemini CLI is a full agentic tool with its own tool-calling loop
    and retry/backoff, so a single call here can fan out into several
    real API requests. Kept only for cases where you deliberately want
    CLI behavior (e.g. interactive debugging), not for orchestrator use.

    FIX: this previously never told the CLI which model to use, so it
    silently ignored GEMINI_MODEL in config/server.conf and used
    whichever model the CLI defaults to.
    """

    def __init__(self):
        self.config = ConfigManager()

    def generate(self, prompt: str) -> str:

        model = self.config.get("GEMINI_MODEL", "gemini-2.5-pro")

        result = subprocess.run(
            [
                "gemini",
                "-p",
                prompt,
                "--model",
                model,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr)

        return result.stdout.strip()
