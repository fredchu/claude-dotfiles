---
name: apple-notes
description: "Manages Apple Notes via MCP tools. Use when the user mentions 筆記, notes, 記一下, 進度, 做到哪了, or wants to save/search/read/update/organize notes in Apple Notes. Also triggers on Session Handoff and any operation targeting the 'Claude 工作區' folder. Does NOT handle: Reminders/待辦 (use rem-cli), calendar/行程 (use ical-cli)."
---

# Apple Notes — MCP 操作規則

## Gotchas (Read First)

1. **所有我產生的內容一律放「Claude 工作區」資料夾** — 不碰用戶其他資料夾，除非明確要求
2. **create-note 無法指定資料夾** — 必須先 create，再用 move-note 搬到「Claude 工作區」
3. **格式用 HTML**（`format: "html"`）— Apple Notes 不渲染 markdown
4. **update-note 是全量覆寫** — 必須先 get-note-content 讀取現有內容，合併後再寫回
5. **搜尋先用用戶原話** — 搜不到再 list-folders 看結構，最後才擴展關鍵字
6. **密碼保護的筆記無法存取** — 遇到時告知用戶

## 建立筆記的標準流程

```
1. mcp__apple-notes__create-note
   - title: "筆記標題"
   - body: "<h1>標題</h1><p>內容</p>"
   - format: "html"

2. mcp__apple-notes__move-note
   - title: "筆記標題"
   - folder: "Claude 工作區"
```

永遠兩步走，不可省略 move-note。

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
| `batch-move-notes` | 批次搬移 |
| `batch-delete-notes` | 批次刪除 |

## HTML 格式範例

```html
<h1>主標題</h1>
<h2>段落標題</h2>
<p>一般段落文字</p>
<ul>
  <li>項目一</li>
  <li>項目二</li>
</ul>
<b>粗體</b>、<i>斜體</i>
```

不要用 markdown 語法（`#`、`**`、`-`），Apple Notes 不會渲染。

## Checklist 讀取（進階）

MCP API 無法讀取 checklist 打勾狀態（AppleScript 限制）。如需讀取：
- 工具腳本：`/Users/fredchu/Documents/For_Claude/scripts/parse_checklist_v2.py`
- Python 環境：`/tmp/notes_parse/`（含 protobuf 套件）
- 執行：`/tmp/notes_parse/bin/python /Users/fredchu/Documents/For_Claude/scripts/parse_checklist_v2.py`
