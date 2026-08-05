#!/bin/bash
# Fetch agent-specific + shared Session Handoff from the Obsidian vault「Agent 工作區」.
# Used by Claude Code SessionStart hook to inject handoff context automatically.
# This is the PRO CC version — reads handoff/Active/Pro CC.md + handoff/Shared/*.md.
# Cutover 2026-07-21 (Obsidian migration Phase 1); Apple Notes version backed up at
# fetch-handoff.sh.bak-applenotes-20260721.

HANDOFF_ROOT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/Agent 工作區/handoff"
CLI="$HOME/.claude/skills/session-handoff/scripts/handoff_cli.py"

if [ ! -f "$CLI" ]; then
    echo "ℹ️ handoff_cli.py 不存在（$CLI）— session-handoff skill 未安裝？"
    exit 0
fi

/usr/bin/python3 "$CLI" session-start \
    --root "$HANDOFF_ROOT" \
    --agent "Pro CC" \
    --active-budget 1800 \
    --shared-budget 1200 \
    2>>"$HOME/.claude/scripts/handoff-fetch.log"
