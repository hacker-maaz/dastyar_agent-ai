#!/bin/bash

AI_SERVER_HOME="$HOME/ai-server"

PYTHON="$AI_SERVER_HOME/.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
    PYTHON="python3"
fi

if [ -n "$1" ]; then
    PLAN_TASK="$*"
else
    echo
    echo "===== AI PLAN (preview only — nothing will be run) ====="
    echo
    echo "What do you want a plan for?"
    read PLAN_TASK
fi

cd "$AI_SERVER_HOME" || exit 1

# NOTE: `ai plan` only ever runs the Planner Agent. It never triggers
# Feature/Review/Documentation, even if the plan mentions them — it's
# a preview. To actually execute, run the same task through
# `ai feature "..."` instead.
"$PYTHON" -m agents.orchestrator plan "$PLAN_TASK"
