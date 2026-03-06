---
name: handoff
description: 把當前 session 的工作狀態寫入 Apple Notes「Claude 工作區」。用戶說「收工」「bye」「結束」「handoff」時觸發。三階記憶系統：Active（短期）→ Archive（中期）→ 記憶庫（長期）。
---

# Session Handoff v2 — 三階記憶系統

## 架構

```
Session 結束
    ↓
[短期] Session Handoff — Active ← Hook 每次啟動讀取
    ↓ 舊內容 prepend 到
[中期] Session Handoff — Archive ← 完整歷史，保留最近 5 條
    ↓ 定期 consolidation
[長期] 記憶庫/ + MEMORY.md ← 提煉後的通用知識
```

## 流程

### Phase 1: Archive（保存舊 Active）

1. 用 `mcp__apple-notes__search-notes` 搜尋 `Session Handoff — Active`
2. 如果找到，讀取其內容（`mcp__apple-notes__get-note-content`）
3. 搜尋 `Session Handoff — Archive`
   - 存在 → 用 `mcp__apple-notes__update-note` 把舊 Active 內容 prepend 到 Archive 頂部（加日期分隔線）
   - 不存在 → 用 `mcp__apple-notes__create-note` 建立 Archive，內容為舊 Active，再 `move-note` 到「Claude 工作區」
4. 記錄 Archive 中最舊條目的日期，供 Phase 3 判斷

### Phase 2: Write（覆寫 Active）

1. 回顧本次 session 的對話，整理 handoff 內容
2. 用 `mcp__apple-notes__update-note` 覆寫 Active 筆記
   - 如果 Active 不存在（首次），用 `create-note` + `move-note` 到「Claude 工作區」
3. 多專案合併在同一則 Active 筆記，用 `<h2>` 分隔

### Phase 3: Weekly Consolidation（Archive >= 5 條時觸發）

檢查 Archive 中的條目數量。如果 Archive 累積 >= 5 條：

1. **產出週報** → 寫入 `記憶庫/情景記憶/MMDD-週報-W{週數}.md`
   - 格式：各專案本週做了什麼、重要決策、未解問題

2. **提煉模式** → 掃描整週 Archive，偵測：
   - 重複出現的問題 → 建議寫入 `強制規則/` 或更新 MEMORY.md
   - 多次使用的工作模式 → 建議寫入 `語義記憶/`
   - 重要的單次事件 → 建議寫入 `情景記憶/`

3. **清理 Archive** → 移除已 consolidate 的條目，只保留最近 5 條

Consolidation 只「建議」，需用戶確認後才寫入。輸出格式：
```
週報已寫入：記憶庫/情景記憶/0305-週報-W10.md

記憶沉澱建議：
- [語義] XXX 已連續 3 個 session 調整，建議寫入語義記憶
- [強制] YYY — 已踩坑 2 次，建議寫入強制規則
要執行嗎？(y/n/選擇性執行)
```

### Phase 4: Spot Check（即時偵測）

即使未觸發 Consolidation，如果當次 session 有明確教訓或值得沉澱的模式（踩坑、新最佳實踐），即時建議寫入記憶庫。有明確教訓就建議，不需要等到重複出現。

## Active 筆記內容格式

字元預算：2000 字元以內。HTML 格式（format: "html"）。

優先級排序：
- **必寫 (~70%)**：待續工作、已知問題
- **應寫 (~25%)**：本次完成、關鍵檔案（3-5 個）
- **選寫**：環境狀態

多專案用 `<h2>` 分隔，合併在同一則筆記。

```html
<h1>Session Handoff — Active</h1>
<p><i>更新時間：2026/03/05</i></p>

<h2>特助系統</h2>
<h3>待續工作</h3>
<ul><li>...</li></ul>
<h3>已知問題</h3>
<ul><li>...</li></ul>
<h3>本次完成</h3>
<ul><li>...</li></ul>

<h2>VerbatimFlow</h2>
...
```

## Archive 條目格式

每個條目以 `<h3>` 日期標題 + `<hr>` 分隔：

```html
<h3>2026/03/05 — 特助系統, VerbatimFlow</h3>
<p>[壓縮版 handoff 內容]</p>
<hr>
<h3>2026/03/04 — VerbatimFlow</h3>
<p>[壓縮版 handoff 內容]</p>
<hr>
```

## 規則

- 不可以「還沒做什麼事」為由跳過 — 即使只做了 briefing，也要寫
- 寫完 handoff 後，回覆用戶確認已寫入
- Active 筆記標題固定為 `Session Handoff — Active`，不加日期
- Archive 筆記標題固定為 `Session Handoff — Archive`
- 多專案合併在同一則 Active，不再每個專案各寫一則
