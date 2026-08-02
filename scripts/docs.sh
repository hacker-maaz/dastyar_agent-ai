#!/bin/bash

AI_SERVER_HOME="$HOME/ai-server"

PYTHON="$AI_SERVER_HOME/.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
    PYTHON="python3"
fi

if [ -n "$1" ]; then
    DOCS_TASK="$*"
else
    DOCS_TASK="Update project documentation based on recent work"
fi

cd "$AI_SERVER_HOME" || exit 1

"$PYTHON" -m agents.orchestrator docs "$DOCS_TASK"
