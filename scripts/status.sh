#!/bin/bash

AI_HOME="$HOME/ai-server"

echo
echo "========== AI SERVER STATUS =========="
echo

# Workspace
if [ -d "$AI_HOME" ]; then
    echo "Workspace : OK"
else
    echo "Workspace : Missing"
fi

# Memory
if [ -d "$AI_HOME/memory" ]; then
    echo "Memory    : OK"
else
    echo "Memory    : Missing"
fi

# Prompts
if [ -d "$AI_HOME/prompts" ]; then
    echo "Prompts   : OK"
else
    echo "Prompts   : Missing"
fi

# Scripts
if [ -d "$AI_HOME/scripts" ]; then
    echo "Scripts   : OK"
else
    echo "Scripts   : Missing"
fi

# Gemini
if command -v gemini >/dev/null 2>&1; then
    echo "Gemini    : Installed"
else
    echo "Gemini    : Not Found"
fi

# OpenCode
if command -v opencode >/dev/null 2>&1; then
    echo "OpenCode  : Installed"
else
    echo "OpenCode  : Not Found"
fi

# Git
if command -v git >/dev/null 2>&1; then
    echo "Git        : Installed"
else
    echo "Git        : Not Found"
fi

# tmux
if command -v tmux >/dev/null 2>&1; then
    echo "tmux       : Installed"
else
    echo "tmux       : Not Found"
fi

echo
echo "======================================"
