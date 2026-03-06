---
name: earnings-setup
description: 設定財報追蹤自動化。從 CSV 清單出發，查詢財報日期，建行事曆事件，建立 cron 輪詢排程。觸發詞：「設定財報追蹤」「earnings setup」「加股票到追蹤清單」「追蹤財報」
---

# Earnings Setup — 財報追蹤自動化設定

## 檔案路徑

- 腳本目錄: `/Users/fredchu/Documents/For_Claude/scripts/earnings-autopilot/`
- Ticker 清單: `/Users/fredchu/Documents/For_Claude/inbox/earnings/tickers.csv`
- 狀態目錄: `/Users/fredchu/Documents/For_Claude/scripts/earnings-autopilot/state/`
- ical CLI: `/Users/fredchu/bin/ical`

## 流程

### Step 1: 讀取 Ticker 清單

```bash
cat /Users/fredchu/Documents/For_Claude/inbox/earnings/tickers.csv
```

解析 CSV（逗號分隔），取得所有 ticker symbols。
如果用戶指定特定 ticker，只處理那些。

### Step 2: 查詢財報日期

對每支 ticker 執行：

```bash
python3 /Users/fredchu/Documents/For_Claude/scripts/earnings-autopilot/fetch_earnings_date.py TICKER
```

收集結果，分類：
- **可排程**（60 天內）
- **太遠**（> 60 天）— 列出但不自動排程
- **查詢失敗** — 列出供用戶處理

向用戶報告結果表格，確認要排程哪些。

### Step 3: 建行事曆事件

對確認的 ticker，用 ical CLI 建事件：

```bash
/Users/fredchu/bin/ical add --title "NVDA 盤後財報" --date "2026-05-28" --calendar "個人" --allday
```

- 標題格式：`{TICKER} {盤前/盤後/未知} 財報`
- 時間：如果知道 AMC/BMO 就標註，否則標「未知」
- 全天事件

### Step 4: 建立 Cron 輪詢排程

```bash
/Users/fredchu/Documents/For_Claude/scripts/earnings-autopilot/cron_manager.sh add TICKER Q{N}_{YEAR} YYYY-MM-DD
```

### Step 5: 建立狀態檔

確認 `state/{TICKER}_{QUARTER}.json` 已建立（poll_transcript.sh 會自動建立）。

### Step 6: 報告

向用戶彙整報告：
- 已排程的 ticker + 財報日期 + cron 排程
- 太遠的 ticker（建議下次再設定）
- 失敗的 ticker

## 注意事項

- 距離 > 60 天的 ticker 列出並詢問用戶，不自動排程
- yfinance 需要安裝：`pip install yfinance`
- 每次只處理下一次財報，不排程更遠的未來
