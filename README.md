# claude-dotfiles

My [Claude Code](https://docs.anthropic.com/en/docs/claude-code) configuration — skills, hooks, settings, and a three-tier memory system.

## What's in here

```
CLAUDE.md              # Global rules (loaded every session)
settings.json          # Permissions, hooks, enabled plugins
scripts/               # Hook scripts
  fetch-handoff.sh     # SessionStart hook: injects last session state
skills/                # 16 custom skills
  session-handoff/     # Three-tier memory: Active → Archive → Long-term
  earnings-*           # Earnings call automation (setup/process/status)
  apple-notes/         # Apple Notes via MCP
  ical-cli/            # Apple Calendar via local CLI
  rem-cli/             # Apple Reminders via local CLI
  subtitle-polisher/   # Chinese subtitle correction pipeline
  taiwan-earnings-translator/  # Forensic-grade earnings translation
  forensic-transcript-translator/  # With cross-audit
  corporate-forensic-auditor/      # Tri-phasic corporate audit
  convertible-arbitrage-auditor/   # Convertible bond strategy
  buddha-model/        # Dialectical reasoning framework
  futu-indicator-coder/  # Futu/Moomoo indicator scripting
  notebooklm/          # Google NotebookLM automation
  zlibrary-to-notebooklm/  # (excluded from repo — has its own .venv)
```

## Three-tier memory system

The biggest pain with Claude Code: memory doesn't persist across sessions. My solution:

**Layer 1 — Active** (Apple Notes, auto-injected via SessionStart hook)
- Every session ends with a handoff note written to Apple Notes
- Next session starts by reading it back via hook → instant context restore

**Layer 2 — Archive** (Apple Notes, rolling history)
- Old Active content gets prepended to Archive
- Triggers weekly consolidation after 5 entries

**Layer 3 — Long-term** (filesystem `記憶庫/` + `MEMORY.md`)
- Distilled patterns and rules extracted from Archive
- Survives indefinitely

See [`skills/session-handoff/SKILL.md`](skills/session-handoff/SKILL.md) for the full protocol.

## Cross-project knowledge sharing

Claude Code's auto-memory is project-isolated. My workaround:

- **Universal rules** (search principles, tool lookup, Apple Notes conventions) → `CLAUDE.md` (global, always loaded)
- **Project-specific knowledge** → per-project `MEMORY.md` (auto-loaded)
- **Session continuity** → Apple Notes via MCP (accessible from any project)

## Prerequisites

Some skills depend on local tools:

- [`ical`](https://github.com/phatblat/ical) — Apple Calendar CLI
- [`rem`](https://github.com/nicholasgasior/rem) — Apple Reminders CLI
- [Apple Notes MCP](https://github.com/Dhravya/apple-mcp) — Apple Notes via MCP server

## Usage

This repo is meant as a reference. To use it:

1. Browse the skills for ideas and patterns
2. Copy what's useful to your own `~/.claude/skills/`
3. Adapt `CLAUDE.md` rules to your workflow

## License

MIT
