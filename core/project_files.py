import os
from pathlib import Path

from core.config import ConfigManager

# Keeps injected file content small enough to not blow up prompt size
# or burn through the token-based free-tier quota (yes, that's a real
# tracked metric, not just request count — seen in the 429 errors
# earlier).
MAX_BYTES_PER_FILE = 8000
MAX_TOTAL_FILES = 15
MAX_TOTAL_BYTES = 40000


def _project_dir() -> Path:
    config = ConfigManager()
    configured = config.get("ACTIVE_PROJECT_PATH")
    if configured:
        return Path(os.path.expanduser(os.path.expandvars(configured)))
    return Path.home() / "ai-server" / "projects" / "k-V4"


def read_files(paths, project_dir=None) -> str:
    """
    Reads the given file paths (relative to project_dir, or absolute)
    and formats them as markdown code blocks, bounded in size.
    Silently skips files that can't be read rather than failing —
    missing/unreadable context shouldn't crash a whole agent run.
    """
    if not paths:
        return ""

    project_dir = project_dir or _project_dir()
    blocks = []
    total_bytes = 0

    for rel_path in paths[:MAX_TOTAL_FILES]:
        path = Path(rel_path)
        full_path = path if path.is_absolute() else project_dir / path

        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
        except (FileNotFoundError, IsADirectoryError, PermissionError, OSError):
            continue

        if len(content) > MAX_BYTES_PER_FILE:
            content = content[:MAX_BYTES_PER_FILE] + "\n... (truncated)"

        if total_bytes + len(content) > MAX_TOTAL_BYTES:
            blocks.append("... (remaining files omitted — total size limit reached)")
            break

        total_bytes += len(content)

        suffix = path.suffix.lstrip(".")
        blocks.append(f"### {rel_path}\n```{suffix}\n{content}\n```")

    return "\n\n".join(blocks)


def find_files_mentioned_in_text(text, project_structure_listing, max_matches=10):
    """
    Best-effort: returns project file paths whose basename is
    literally mentioned in the given text (e.g. a task description).

    Used at PLANNING time, before anything has actually been touched
    — so this is a guess, not ground truth. Review Agent doesn't use
    this function at all; it gets the exact files OpenCode reported
    touching, which is precise, not a guess.
    """
    if not text or not project_structure_listing:
        return []

    text_lower = text.lower()
    matches = []

    for line in project_structure_listing.splitlines():
        line = line.strip()
        if not line or line.startswith("..."):
            continue
        basename = Path(line).name.lower()
        if basename and basename in text_lower:
            matches.append(line)
            if len(matches) >= max_matches:
                break

    return matches
