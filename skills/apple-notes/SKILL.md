---
name: apple-notes
description: "Manages Apple Notes via MCP tools. Use when the user mentions 筆記, notes, 記一下, 進度, 做到哪了, or wants to save/search/read/update/organize notes in Apple Notes. Also triggers on Session Handoff and any operation targeting the 'Claude 工作區' folder. Does NOT handle: Reminders/待辦 (use rem-cli), calendar/行程 (use ical-cli)."
---

# Apple Notes — MCP 操作規則

## Gotchas (Read First)

1. **所有我產生的內容一律放「Claude 工作區」資料夾** — 不碰用戶其他資料夾，除非明確要求
2. **建立筆記用 AppleScript**（不用 MCP create-note，因為 title 參數會標題重複）
3. **格式用 HTML** — Apple Notes 不渲染 markdown
4. **update-note 是全量覆寫** — 必須先 get-note-content 讀取現有內容，合併後再寫回
5. **搜尋先用用戶原話** — 搜不到再 list-folders 看結構，最後才擴展關鍵字
6. **密碼保護的筆記無法存取** — 遇到時告知用戶

## macOS 26 HTML 格式規則（必遵守）

macOS 26 Notes.app 會自動加 font-size: 11px。`<h2>`/`<h3>` 在 iPhone 上會變小字。

| 格式 | HTML |
|------|------|
| 筆記標題 | `<h1>...</h1>` |
| 段落標題 | `<div><span style="font-size: 18px"><b>...</b></span></div>` |
| 內文 | `<div>...</div>`（不加 font-size） |
| 清單 | `<ul><li>...</li></ul>` 或 `<ol><li>...</li></ol>` |
| 空行 | `<div><br></div>` |

**禁止**：`<h2>`/`<h3>`、`<p>`、font-size 19px+

## 建立筆記的標準流程

```applescript
-- 用 AppleScript 建立（避免 MCP create-note 標題重複）
tell application "Notes"
    tell account "iCloud"
        make new note at folder "Claude 工作區" with properties {body:"<h1>標題</h1><div>內容</div>"}
    end tell
end tell
```

讀取/搜尋/更新用 MCP 工具即可。更新用 `update-note`（format: "html"），HTML 遵守上述格式規則。

## 更新筆記的標準流程

```
1. mcp__apple-notes__get-note-content  →  讀取現有內容
2. 合併/修改內容
3. mcp__apple-notes__update-note
   - title: "筆記標題"
   - body: "完整的新內容（HTML）"
   - format: "html"
```

## 搜尋筆記

```
1. mcp__apple-notes__search-notes
   - query: "用戶的原話關鍵字"

2. 搜不到 → mcp__apple-notes__list-folders 看結構
3. 還是找不到 → 擴展同義詞再搜
```

## 常用工具速查

| 工具 | 用途 |
|------|------|
| `create-note` | 建立筆記（需搭配 move-note） |
| `search-notes` | 搜尋筆記（title + content） |
| `get-note-content` | 讀取筆記內容 |
| `get-note-details` | 取得 metadata（建立/修改時間） |
| `update-note` | 覆寫筆記內容（先讀再寫） |
| `delete-note` | 刪除筆記（移到 Recently Deleted） |
| `move-note` | 搬移筆記到指定資料夾 |
| `list-notes` | 列出所有筆記或特定資料夾內的 |
| `list-folders` | 列出所有資料夾 |
| `create-folder` | 建立新資料夾 |
| `get-note-markdown` | 取得 markdown 格式（checklist 自動標 `[x]`/`[ ]`） |
| `get-checklist-state` | 讀取 checklist 勾選狀態（需 Full Disk Access） |
| `batch-move-notes` | 批次搬移 |
| `batch-delete-notes` | 批次刪除 |

## HTML 格式範例

```html
<h1>筆記標題</h1>
<div><i>日期或副標題</i></div>
<div><br></div>
<div><span style="font-size: 18px"><b>段落標題</b></span></div>
<div>一般內文</div>
<div><b>粗體</b>、<i>斜體</i></div>
<ul>
  <li>無序清單項目</li>
</ul>
<ol>
  <li>有序清單項目</li>
</ol>
```

不要用 markdown 語法（`#`、`**`、`-`），Apple Notes 不會渲染。
詳細規則見 memory：`feedback_apple_notes_html_formatting.md`

## Checklist 讀取

MCP 已原生支援 checklist 狀態讀取（v1.2.19+，需 Full Disk Access）：

```
1. mcp__apple-notes__get-checklist-state  →  返回每項的 done/undone
   - noteTitle: "筆記標題"

2. mcp__apple-notes__get-note-markdown    →  自動標註 [x]/[ ]
   - noteTitle: "筆記標題"
```

如 MCP host 未授予 Full Disk Access，會優雅降級（checklist 項目不含勾選狀態）。

備用方案（不需 Full Disk Access）：
- Python 腳本：`/Users/fredchu/Documents/For_Claude/scripts/parse_checklist_v2.py`
- 執行：`/tmp/notes_parse/bin/python /Users/fredchu/Documents/For_Claude/scripts/parse_checklist_v2.py`
