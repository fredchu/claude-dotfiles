# 用戶級規則（所有專案共用）

## Session Handoff — 開始時的強制動作

- SessionStart hook 會自動從 Apple Notes「Claude 工作區」抓取最新 Session Handoff 筆記內容注入 context
- **在第一句回覆的開頭，必須附上 hook 注入的 handoff 內容摘要**（3-5 bullet points），再回應用戶的第一句話
- 如果 hook 回傳「ℹ️ 沒有 Session Handoff 筆記」，則跳過摘要，直接回應用戶

## 跨專案行為規則

### 搜尋原則
- 搜尋 Apple Notes、Gmail 或任何資料時，**先用用戶的原話搜**，不要自行替換同義詞
- 搜不到再 list-folders 看結構
- 最後才擴展其他關鍵字
- 教訓：用戶說「雜事」，我搜了「待辦/TODO/要做」，結果全部搜不到

### 工具查找原則
- 判斷工具是否安裝時，**先查自己的記憶和筆記**，不要直接跑 `which`
- `which` 只搜 PATH，找不到≠沒裝 → 用 `find` / `mdfind` 搜更廣範圍
- 確認真的沒裝才去找替代方案或重新安裝
- 教訓：MEMORY.md 寫了「rem CLI：已安裝」，卻直接信 `which rem` 的結果說未安裝
- rem CLI 安裝位置：`/Users/fredchu/bin/rem`（不在預設 PATH）

### Apple Notes 規則
- 專屬資料夾：「Claude 工作區」— 所有我產生的內容都放這裡
- 不碰用戶其他資料夾的筆記，除非用戶明確要求編輯
- 寫入格式：使用 HTML（format: "html"），不用 markdown — Apple Notes 不渲染 markdown
- create-note 不支援指定資料夾，必須先建立再用 move-note 搬到「Claude 工作區」

### 用戶長期目標：開源回饋 + 內容分享
- **開源**：在適當時機主動提醒——手邊做的東西能不能開源？
  - 動機：取之開源、回饋開源，同時建立個人作品集
  - 適用場景：完成工具/腳本/skill 且具通用價值時，引導思考開源可能性
- **分享**：在適當時機提醒並引導把做過的事記錄、分享出去
  - 形式：X 推文、blog 文章、電子報、或其他適合的管道
  - 我的角色：鼓勵、引導、甚至幫忙整理內容草稿
  - 核心想法：槓桿分享的力量，讓做過的事產生更大影響
- **時機掌握**：不要每次都提，挑有意義的節點（專案告一段落、工具穩定、有趣的學習心得）
