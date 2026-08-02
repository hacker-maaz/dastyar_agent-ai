#!/bin/bash

AI_SERVER_HOME="$HOME/ai-server"

PYTHON="$AI_SERVER_HOME/.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
    PYTHON="python3"
fi

if [ -n "$1" ]; then
    # e.g. `ai feature find and fix bugs` — no re-prompt, runs the
    # full Planner -> [selected agent] -> Review -> Documentation
    # pipeline in one go.
    FEATURE="$*"
else
    echo
    echo "===== NEW FEATURE ====="
    echo
    echo "Describe the feature you want to implement:"
    read FEATURE
fi

cd "$AI_SERVER_HOME" || exit 1

"$PYTHON" -m agents.orchestrator feature "$FEATURE"
