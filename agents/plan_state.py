import json
from pathlib import Path

# Deliberately NOT in memory/ — that directory is reserved for
# Documentation Agent's verified, approved knowledge. A plan is a
# draft awaiting your approval, not verified project knowledge, so it
# lives in its own state/ directory instead.
STATE_DIR = Path(__file__).resolve().parent.parent / "state"
LAST_PLAN_FILE = STATE_DIR / "last_plan.json"


def save_last_plan(task: str, plan_text: str) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LAST_PLAN_FILE.write_text(
        json.dumps({"task": task, "plan": plan_text}, indent=2),
        encoding="utf-8",
    )


def load_last_plan():
    if not LAST_PLAN_FILE.exists():
        return None
    try:
        return json.loads(LAST_PLAN_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
