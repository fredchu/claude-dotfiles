---
name: earnings-process
description: 手動觸發單支股票的財報逐字稿下載+翻譯+摘要。觸發詞：「翻譯 NVDA 財報」「處理逐字稿」「earnings process」「下載 TSLA 逐字稿」
---

# Earnings Process — 財報逐字稿處理

## 檔案路徑

- 腳本目錄: `/Users/fredchu/Documents/For_Claude/scripts/earnings-autopilot/`
- 翻譯腳本: `/Users/fredchu/Documents/For_Claude/scripts/earnings-autopilot/earnings_translate_v3.sh`
- 下載腳本: `/Users/fredchu/Documents/For_Claude/scripts/earnings-autopilot/download_transcript.py`
- 輸出目錄: `/Users/fredchu/Documents/For_Claude/inbox/earnings/{TICKER}/`
- 狀態目錄: `/Users/fredchu/Documents/For_Claude/scripts/earnings-autopilot/state/`

## 流程

### Step 1: 確認輸入

從用戶訊息中提取：
- **TICKER** — 股票代號（必要）
- **QUARTER** — 季度，如 Q1（可選，嘗試從日期推斷）
- **YEAR** — 年份（可選，預設今年）
- **URL** — Motley Fool 逐字稿 URL（可選）

### Step 2: 取得逐字稿

**情況 A：用戶提供 URL**
```bash
python3 /Users/fredchu/Documents/For_Claude/scripts/earnings-autopilot/download_transcript.py "URL" --ticker TICKER --quarter Q1 --year 2026
```

**情況 B：已有英文檔案**
檢查 `inbox/earnings/{TICKER}/` 是否已有英文逐字稿。

**情況 C：需要搜尋**
```bash
python3 /Users/fredchu/Documents/For_Claude/scripts/earnings-autopilot/download_transcript.py --search TICKER
```
列出搜尋結果，讓用戶確認 URL。

### Step 3: 翻譯

```bash
/Users/fredchu/Documents/For_Claude/scripts/earnings-autopilot/earnings_translate_v3.sh \
    "inbox/earnings/{TICKER}/{EN_FILE}" \
    --ticker TICKER --quarter Q1 --year 2026
```

這會自動執行：
1. 階段 A：會前研究摘要（含 web search）
2. 階段 B：智慧分段翻譯
3. 階段 C：合併 + 完整性驗證

### Step 4: 更新狀態

如果有狀態檔 `state/{TICKER}_{QUARTER}.json`，更新為 `done`。

### Step 5: 報告

向用戶回報：
- 輸出檔案路徑
- 完整性檢查結果（EN/ZH 段落數、輸出/輸入比）
- 翻譯耗時

## 注意事項

- 翻譯過程使用 `claude -p`，會消耗 Claude Pro/Max 額度
- 預估每份逐字稿約 15K-30K output tokens
- 可用 `--skip-research` 跳過研究摘要（省額度）
- 如果翻譯失敗，暫存目錄會保留供檢查
