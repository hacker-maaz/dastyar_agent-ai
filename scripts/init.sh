#!/bin/bash

echo
echo "===== AI PROJECT INITIALIZATION ====="
echo

# Verify Git repository
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "✓ Git repository detected."
else
    echo "✗ This is not a Git repository."
    exit 1
fi

# Check for AGENTS.md
if [ -f "AGENTS.md" ]; then
    echo "✓ AGENTS.md found."
else
    echo "✗ AGENTS.md missing."
fi

# Ensure memory directory exists
mkdir -p "$HOME/ai-server/memory"

echo
echo "Project initialized successfully."
