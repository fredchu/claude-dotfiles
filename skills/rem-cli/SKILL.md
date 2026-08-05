---
name: rem
description: 管理 macOS Reminders。處理「提醒我 XXX」「記一下 XXX」等中文自然語言指令，支援 briefing 待辦整合。當用戶提及提醒事項、待辦、Reminders、或要建立/查詢/完成/刪除提醒時使用。
---

# rem — macOS Reminders CLI

## 環境

- 路徑：`/Users/fredchu/bin/rem`（不在 PATH，所有指令必須用完整路徑）
- 解析輸出時用 `-o json`，顯示給用戶時用預設 table
- 環境變數：`NO_COLOR=1`（避免 ANSI 碼干擾 JSON 解析）

## 非互動規則

| 情境 | 規則 |
|------|------|
| delete | 必須加 `--force`（非互動環境無法確認） |
| list-mgmt delete | 必須加 `--force` |
| add / update | 禁用 `-i`（interactive mode） |
| 搬移 list | update 不支援改 list → 必須 delete --force + add 重建 |
| 確認動作 | 刪除前先 show 該項目，告知用戶內容，再執行 |

## List 智能路由

用戶沒指定 list 時，根據內容關鍵詞自動判斷目標 list：

| 關鍵詞特徵 | 目標 List |
|-----------|----------|
| 投資/股票/選擇權/ETF/財報/持倉/殖利率/配息 | Investing |
| 程式/code/bug/deploy/PR/skill/app/API | dev |
| 煮/食譜/買菜/超市/料理 | Cooking |
| 掃地/洗衣/倒垃圾/拖地/吸塵/換床單 | 例行家事 |
| 拍照/底片/暗房/沖片/相機 | 攝影暗房 |
| 遊戲/PS5/Switch/Steam/Xbox | Video Games |
| 家人名字/家庭事務/爸媽/小孩 | Family |
| 書/讀/閱讀 | 書 |
| 以上都不符合 | 雜 |

現有 lists（供比對）：Family, Investing, 雜, 例行家事, dev, 攝影暗房, Work, 書, Gadgets, Cooking, Video Games

## dev List 前綴 Convention

dev list 使用前綴分組，模擬 Reminders app 的段落結構（EventKit API 不支援 sections/subtasks）。

**新增 dev items 時必須加前綴：**

| 前綴 | 代表 | 範例 |
|------|------|------|
| MK | MumbleKey 功能 | MK 術語自動學習 |
| MKA | MumbleKey Agent | MKA Release manager |
| MKP | MumbleKey 平台 | MKP Android client |
| VF | VerbatimFlow | VF 實測 2B-6bit |
| CC | Claude Code 工具 | CC loop 實驗 |
| DC | Discord Bot | DC 修長訊息分段發送 |
| EA | Earnings Autopilot | EA 移植逐字稿流程 |

**格式**：`{前綴} {項目名稱}`（前綴和名稱之間用空格分隔）

**搜尋特定群組**：`rem search "MK " --list "dev" --incomplete`

**分組顯示**：讀取 dev list 後，用前綴分組呈現給用戶，而不是扁平列表。

**排序 dev list**：用戶說「排序」「整理 dev list」「排一下」時，用 JXA 腳本按前綴分組排序。

排序方法（JXA `move({to: list})` 會移到 list 末尾）：
1. `rem list --list "dev" --incomplete -o json` 取得所有項目
2. 按前綴排序：MK → MKA → MKP → VF → EA → CC → DC → 無前綴（同前綴內按名稱字母序）
3. 按排好的順序依次 `move({to: devList})` → 先 move 的排前面

```javascript
// /tmp/sort_dev.js — 排序 dev list 的 JXA 腳本模板
const app = Application("Reminders");
const devList = app.lists.whose({name: "dev"})[0];
const sortedNames = ["MK item1", "MK item2", "MKA item1", ...]; // Python 產生
for (let i = 0; i < sortedNames.length; i++) {
    try {
        const rems = devList.reminders.whose({name: sortedNames[i], completed: false});
        if (rems.length > 0) rems[0].move({to: devList});
    } catch(e) {}
}
```

Python 排序邏輯：
```python
prefix_order = {"MK": 0, "MKA": 1, "MKP": 2, "VF": 3, "EA": 4, "CC": 5, "DC": 6}
def sort_key(item):
    name = item["name"]
    for prefix in sorted(prefix_order.keys(), key=len, reverse=True):  # longest first
        if name.startswith(prefix + " "):
            return (prefix_order[prefix], name)
    return (99, name)
```

注意：longest prefix first 避免 MK 吃掉 MKA/MKP。

## 指令速查

```
/Users/fredchu/bin/rem add "title" --list "X" --due "tomorrow" --priority high --notes "N"
/Users/fredchu/bin/rem list --list "X" --incomplete -o json
/Users/fredchu/bin/rem show <id> -o json
/Users/fredchu/bin/rem update <id> --name "new" --due "next mon" --priority medium --notes "N"
/Users/fredchu/bin/rem delete <id> --force
/Users/fredchu/bin/rem complete <id>
/Users/fredchu/bin/rem uncomplete <id>
/Users/fredchu/bin/rem search "query" --list "X" --incomplete -o json
/Users/fredchu/bin/rem overdue -o json
/Users/fredchu/bin/rem upcoming --days N -o json
/Users/fredchu/bin/rem stats -o json
/Users/fredchu/bin/rem lists --count -o json
/Users/fredchu/bin/rem list-mgmt create "name"
/Users/fredchu/bin/rem list-mgmt delete "name" --force
/Users/fredchu/bin/rem list-mgmt rename "old" "new"
/Users/fredchu/bin/rem flag <id>
/Users/fredchu/bin/rem unflag <id>
```

Short ID：UUID 前 8 碼，任何唯一前綴皆可匹配。

## 中文自然語言處理

### 「提醒我 XXX」→ rem add
從語句解析 title + due date，路由到正確 list。

### 「記一下 XXX」→ 判斷 todo vs info
- 有動作/deadline → rem add（待辦）
- 純資訊/筆記 → 存 Apple Notes「Claude 工作區」

### 「briefing」→ 待辦部分
```
/Users/fredchu/bin/rem overdue -o json
/Users/fredchu/bin/rem upcoming --days 1 -o json
```

### 中文時間詞 → --due 值

| 用戶說 | --due 值 |
|--------|---------|
| 明天 | tomorrow |
| 後天 | "in 2 days" |
| 大後天 | "in 3 days" |
| 下週一 | "next monday" |
| 下週五下午三點 | "next friday at 3pm" |
| 月底 | 當月最後一天 ISO 格式 |
| X 小時後 | "in X hours" |
| 今天下午五點 | "today at 5pm" |
| 下個月 | "next month" |
| 今天下班前 | eod |
| 這週五前 | "next friday" 或本週五 ISO |

完整日期語法見 [references/dates.md](references/dates.md)。

## JSON 輸出結構

`rem list -o json` 回傳陣列，每個項目：
```json
{
  "id": "AB12CD34",
  "name": "title",
  "list_name": "dev",
  "due_date": "2026-03-06T09:00:00+08:00",
  "notes": "",
  "priority": 0,
  "priority_label": "none",
  "flagged": false,
  "completed": false
}
```

## 限制

- 無 tags、subtasks、recurrence（EventKit 不支援）
- `--flagged` 篩選較慢（~3-4s，走 JXA fallback）
- update 不能跨 list 搬移，需 delete + add

完整 flag 參考見 [references/commands.md](references/commands.md)。
