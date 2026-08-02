import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors

from models.base_provider import BaseProvider
from core.config import ConfigManager


class GeminiProvider(BaseProvider):
    """
    Gemini provider using the Google GenAI SDK.

    Makes a direct generate_content call — no CLI subprocess, no
    agentic tool-calling loop. This means one Dastyar agent call = at
    most a few real API requests (see retry logic below), not several
    caused by a wrapper CLI's own internal tool-use loop.

    Retry behavior: the SDK itself already retries transient errors a
    few times internally before raising. This class adds one more
    layer on top of that, for outages that outlast the SDK's own
    built-in retry window (roughly the first minute). It only retries
    errors that retrying can plausibly fix:

      - 5xx server errors (e.g. 503 "high demand") — always retried,
        since these are transient and unrelated to your quota.
      - 429 rate limits that are NOT a per-day quota exhaustion (e.g.
        a per-minute cap) — retried, since a short wait can help.
      - 429 errors that ARE a per-day quota exhaustion — never
        retried. Waiting seconds won't refill a daily allowance that
        resets at midnight Pacific; retrying here would just waste
        time and additional requests for no benefit.
    """

    MAX_RETRIES = 3
    RETRY_DELAYS = (5, 15, 30)  # seconds, one per retry attempt

    def __init__(self):
        load_dotenv()

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY not found in .env"
            )

        self.client = genai.Client(api_key=api_key)
        self.config = ConfigManager()

    def _is_daily_quota_exhaustion(self, exc) -> bool:
        # The daily-cap 429s we hit earlier specifically mention
        # "PerDay" in the quotaId — that's the one case where waiting
        # a few seconds/minutes is pointless.
        return "PerDay" in str(exc)

    def _is_retryable(self, exc) -> bool:
        if isinstance(exc, genai_errors.ServerError):
            return True

        if isinstance(exc, genai_errors.ClientError):
            message = str(exc)
            if "429" in message or "RESOURCE_EXHAUSTED" in message:
                return not self._is_daily_quota_exhaustion(exc)

        return False

    def generate(self, prompt: str) -> str:

        model = self.config.get(
            "GEMINI_MODEL",
            "gemini-2.5-flash",
        )

        last_exc = None

        for attempt in range(self.MAX_RETRIES + 1):

            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
                return response.text

            except Exception as exc:
                last_exc = exc

                if attempt >= self.MAX_RETRIES or not self._is_retryable(exc):
                    raise

                delay = self.RETRY_DELAYS[min(attempt, len(self.RETRY_DELAYS) - 1)]
                print(
                    f"  (Gemini request failed with a transient error, "
                    f"retrying in {delay}s — attempt {attempt + 1}/{self.MAX_RETRIES})"
                )
                time.sleep(delay)

        # Unreachable in practice — the loop always either returns or
        # raises — but keeps type-checkers/linters happy.
        raise last_exc
