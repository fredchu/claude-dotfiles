# claude-dotfiles

我的 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 設定檔 — skills、hooks、設定，以及一套三階記憶系統。

## 內容

```
CLAUDE.md              # 全域規則（每次 session 自動載入）
settings.json          # 權限、hooks、啟用的 plugins
scripts/               # Hook 腳本
  fetch-handoff.sh     # SessionStart hook：自動注入上次工作狀態
skills/                # 16 個自建 skill
  session-handoff/     # 三階記憶：Active → Archive → 長期記憶
  earnings-*           # 財報逐字稿自動化（設定/處理/狀態）
  apple-notes/         # Apple Notes（透過 MCP）
  ical-cli/            # Apple Calendar（透過本地 CLI）
  rem-cli/             # Apple Reminders（透過本地 CLI）
  subtitle-polisher/   # 中文字幕校正工具鏈
  taiwan-earnings-translator/  # 法證級財報翻譯
  forensic-transcript-translator/  # 含交叉審計
  corporate-forensic-auditor/      # 三階段企業審計
  convertible-arbitrage-auditor/   # 可轉債策略分析
  buddha-model/        # 高維辯證推理框架
  futu-indicator-coder/  # 富途/Moomoo 指標腳本
  notebooklm/          # Google NotebookLM 自動化
  zlibrary-to-notebooklm/  # （未納入版控 — 有自己的 .venv）
```

## 三階記憶系統

Claude Code 最大的痛點：每次開新 session 就失憶。我的解法：

**第一層 — Active**（Apple Notes，透過 SessionStart hook 自動注入）
- 每次結束 session 時，把工作狀態寫入 Apple Notes
- 下次 session 啟動時，hook 自動讀回 → 即時恢復上下文

**第二層 — Archive**（Apple Notes，滾動歷史）
- 舊的 Active 內容 prepend 到 Archive
- 累積 5 條後觸發 Weekly Consolidation

**第三層 — 長期記憶**（檔案系統 `記憶庫/` + `MEMORY.md`）
- 從 Archive 提煉出的通用模式和規則
- 永久保存

完整協議見 [`skills/session-handoff/SKILL.md`](skills/session-handoff/SKILL.md)。

## 跨專案知識共享

Claude Code 的 auto-memory 是專案隔離的。我的解法：

- **通用規則**（搜尋原則、工具查找、Apple Notes 慣例）→ `CLAUDE.md`（全域，每次載入）
- **專案專屬知識** → 各專案的 `MEMORY.md`（自動載入）
- **Session 接續** → Apple Notes（透過 MCP，任何專案都能存取）

## 前置需求

部分 skill 需要本地工具：

- [`ical`](https://github.com/phatblat/ical) — Apple Calendar CLI
- [`rem`](https://github.com/nicholasgasior/rem) — Apple Reminders CLI
- [Apple Notes MCP](https://github.com/Dhravya/apple-mcp) — Apple Notes MCP server

## 使用方式

這個 repo 主要作為參考。使用方式：

1. 瀏覽 skills 找靈感和模式
2. 把有用的複製到你自己的 `~/.claude/skills/`
3. 根據你的工作流調整 `CLAUDE.md` 規則

## License

MIT
