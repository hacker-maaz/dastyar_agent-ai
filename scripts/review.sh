#!/bin/bash

AI_SERVER_HOME="$HOME/ai-server"

PYTHON="$AI_SERVER_HOME/.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
    PYTHON="python3"
fi

if [ -n "$1" ]; then
    REVIEW_TARGET="$*"
else
    echo
    echo "===== AI REVIEW ====="
    echo
    echo "What should be reviewed?"
    read REVIEW_TARGET
fi

cd "$AI_SERVER_HOME" || exit 1

"$PYTHON" -m agents.orchestrator review "$REVIEW_TARGET"
