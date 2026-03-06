---
name: earnings-status
description: 查看財報逐字稿追蹤狀態。觸發詞：「財報進度」「哪些逐字稿還沒出」「earnings status」「追蹤狀態」
---

# Earnings Status — 財報追蹤狀態查詢

## 檔案路徑

- 狀態目錄: `/Users/fredchu/Documents/For_Claude/scripts/earnings-autopilot/state/`
- Cron 管理: `/Users/fredchu/Documents/For_Claude/scripts/earnings-autopilot/cron_manager.sh`

## 流程

### Step 1: 讀取所有狀態檔

```bash
ls /Users/fredchu/Documents/For_Claude/scripts/earnings-autopilot/state/*.json 2>/dev/null
```

對每個 JSON 檔讀取並彙整。

### Step 2: 列出活躍 Cron

```bash
/Users/fredchu/Documents/For_Claude/scripts/earnings-autopilot/cron_manager.sh list
```

### Step 3: 彙整報表

按狀態分類顯示：

**已完成 (done)**
| Ticker | Quarter | 財報日 | 完成時間 | 輸出檔 |

**輪詢中 (polling)**
| Ticker | Quarter | 財報日 | 已輪詢次數 | 上次輪詢 | Cron 排程 |

**已下載待翻譯 (downloaded)**
| Ticker | Quarter | 英文檔 |

**超時 (timeout)**
| Ticker | Quarter | 財報日 | 建議操作 |

**尚未設定**
列出 tickers.csv 中有但沒有狀態檔的 ticker。

### Step 4: 建議操作

- 超時的 ticker：建議手動搜尋逐字稿
- 已下載但未翻譯：建議執行 `/earnings-process`
- 輪詢次數過多：提醒用戶該 ticker 的逐字稿可能尚未發布

## 輸出格式

使用表格和 emoji 讓狀態一目了然。
