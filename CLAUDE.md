# 用戶級規則（所有專案共用）

## Session Handoff Config
- Agent ID: Pro CC
- Notes folder: Claude 工作區
- Other Agents: Mini CC
- Private budget: 1500 chars
- Shared budget: 1000 chars

## Session Handoff — 開始時的強制動作

- SessionStart hook 會自動從 Apple Notes「Claude 工作區」抓取最新 Session Handoff 筆記內容注入 context
- **在第一句回覆的開頭，必須附上 hook 注入的 handoff 內容摘要**（3-5 bullet points），再回應用戶的第一句話
- 如果 hook 回傳「ℹ️ 沒有 Session Handoff 筆記」，則跳過摘要，直接回應用戶

## 跨專案行為規則

### Agent 派工規則
- 派任何 agent（pm/designer/engineer/qa）做專案任務前，**先讀該專案的 AGENTS.md** 取得技術棧、skills、context 路徑
- AGENTS.md 位置慣例：`/Users/fredchu/Documents/For_Claude/company/<project>/AGENTS.md` 或專案原始碼根目錄
- 把 AGENTS.md 的內容帶進 agent invoke 的 prompt，確保 agent 有足夠 context
- 如果專案沒有 AGENTS.md，在 prompt 中提供基本資訊（專案路徑、技術棧、相關檔案）

### Marketing 流程規則
- 處理任何專案的行銷任務時，**先讀 `/Users/fredchu/Documents/For_Claude/company/_shared/marketing-playbook.md`**（流程和 brand voice）
- 再讀對應專案的 `marketing-memory.md`（位置：`/Users/fredchu/Documents/For_Claude/company/<project>/marketing-memory.md`）
- 按 playbook 流程跟用戶互動，invoke marketing skills

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

### Agent Teams 使用偏好
- 遇到適合使用 agent teams 的情境時，主動提議使用
- 適用場景：多個獨立子任務可並行、需要不同專長的 agent 協作、大型重構或跨模組修改
- Pro CC 和 Mini CC 都已啟用 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`

### Session 結束前檢查 wiki/ uncommitted（hard rule）

> 來源：2026-04-29 dual-axis token-maxing audit 🟡 #7 衍生 — 4/29 踩到 commit 46059e4 後 wiki metadata（_absorb_log / _index / _backlinks / _log）+ 4 新文章 + 4 既有文章修改全部沒 commit。`/wiki add` 流程已加 Step 5 自動 commit，但 ad-hoc 直接 Edit/Write wiki 檔案的場景不走 `/wiki add` 流程救不到，要 reflex 補。

#### 觸發時機
任何收尾動作前（`/handoff`、`bye`、`收工`、用戶說「結束」/「先到這裡」），**先跑** `git status For_Claude/wiki/` 檢查。

#### 處理規則
- **完全 clean**：直接進收尾流程
- **有 uncommitted（modified / untracked）**：列改動清單給用戶，問「要不要 commit 後再收工？」
  - 用戶說好 → 寫 narrative-rich commit message + commit
  - 用戶說「先別 commit」/「下次再說」 → 在 handoff 寫一條 pending 提醒，下次 session 先處理
- **發現異常檔案**（如 `wiki/.obsidian/` 漏 gitignore）→ 提議加 .gitignore，不要強行 commit

#### 不適用
- `/wiki add` 流程末尾已內建 Step 5 commit（不要重複）
- 用戶明確說「不要 commit wiki」→ 跳過該 session

### Fork 派工前 inject wiki context（半自動 reflex）

> 來源：2026-04-29 dual-axis token-maxing audit 🟡 #8 — 派 fork 時若任務跟 wiki 有 fit，主 session 跑 helper 撈相關 wiki path 加進 fork prompt，不要全靠 LLM 自律記得做。

#### 觸發條件（任一命中**可考慮**跑 helper）
- Fork 任務跟既知 wiki pattern 對位（實作某 pattern article 的具體 case）
- Fork 任務涉及多次踩過的 lesson（wiki/lessons 累積過）
- Fork 任務是 audit / brainstorm / 研究 — 需要 lens
- 用戶明確要求「帶 wiki context 給 fork」

#### 不觸發
- 純 codebase 探索 / 抓 file 結構
- 跑既知重構 / 補測試 / 範圍明確的 bug fix
- Fork 主題跟 wiki 無 fit（多數 implementation 工作）

#### 觸發時動作
1. 主 session 跑：`python3 /Users/fredchu/dev/wiki/scripts/inject_context.py "<topic>" --limit 5`
2. 拿 stdout 的 path list 貼進 fork prompt
3. fork prompt 寫一句：「Read these wiki articles for context before starting: <paths>」
4. 若 helper 回 WARN（無命中）→ 跳過 inject，照原計畫派 fork（不要硬塞無關 path）

#### 紀律
- 判斷 fit 是 LLM 自由心證 — **不確定就不 inject**
- 過度 inject = 浪費 token + distract fork
- helper script 失敗 → 跳過，不阻塞 fork 派遣

### 實驗結束後主動發起清理盤點（hard rule）

> 來源：2026-04-30 Breeze-ASR-26 MLX 實驗結束後堆 ~12GB 多路徑垃圾，要用戶主動問才開始清。實驗副產品散在 HF cache / Library Caches / Logs / .build / /tmp 多處，用戶很難主動列出來。詳見 `memory/feedback_experiment_cleanup_audit.md`。

#### 觸發時機
實驗 / spike / POC 收尾時（用戶說「完成」「結案」「OK 了」「這次就到這裡」），或對話自然轉向別的主題前，**主動**發起盤點，不等用戶問。一次實驗只觸發一次。

#### 盤點 + 處理
1. grep 全部相關產物（HF cache、`~/Documents/huggingface/`、`~/Library/Caches/<exp>/`、crash logs、`scripts/<exp>/.build/`、`/tmp/<exp>`、實驗目錄內 dead-end source files、**harness-side：跑中的 background shells 用 TaskStop 關 + `/private/tmp/claude-*/.../tasks/*.output` 已 exit 的直接刪**），估各項大小
2. 分類：**明確垃圾**（失敗路徑 cache / build artifacts / crash logs / 被取代的 baseline tool）vs **灰色地帶**（source weights / dead-code source files）
3. **Phase A**：直接執行明確垃圾刪除
4. **Phase B**：列灰色項目給用戶選（建議方向但讓用戶決定）
5. commit 變更（git rm dead source / 更新 README 寫一句「曾試過 X 但選 Y」），避免 commit history 含死路誤導未來

#### 不適用
- 持續進行中的工作（不是收尾）
- 純研究 / 讀檔，沒下載沒 build
- 用戶明確說「先放著」

### Codex 派工 reflex（hard rule）

> 來源：2026-04-29 dual-axis token-maxing audit 跨 subsystem 共通弱項第 1 條 — 「架構支援卻不用 = 比沒架構更糟糕」。

**動工前自問：「這是不是預設派 Codex 的觸發條件？」**

> 🤖 **dispatch-router（2026-06-17 上線，自動化此 reflex）**：UserPromptSubmit advisory hook 會自動偵測命中下列觸發條件的 prompt 並注入提示（`⚠️ dispatch-router: …`）；看到提示即走 `/dispatch` skill（派工單一入口：分類→生 packet→codex-or-local）。hook **只提示不自動派**，最終仍由我判斷。詳見 `memory/project_dispatch_router.md`。

#### 預設派 Codex（任一命中即派）
- 單檔實作 ≥ 100 行 deterministic 邏輯
- 範圍明確的 bug fix（已知檔案 + 已知 root cause + 修法已想清楚）
- 局部重構（callback → async/await、抽函式、rename 之類）
- 為單一函式補 unit test
- 已寫好 spec 的 implementation 工作（spec 在 docs/ 或 design 已 brainstorm 完）

#### 不派 Codex（保留 Claude 主 session）
- 探索性研究 / 多檔分析 / 架構決策
- 跨多 system 串接（Pro CC ↔ Mini CC ↔ NAS 之類）
- 需 LLM 判斷取捨（哪個方案好、命名、abstraction 層級）
- 互動式 debug / 邊查邊改

#### 例外
- 用戶明確要求「主 session 處理」→ override
- Codex 訂閱 quota 滿 → 先 fallback 本地 Coder-4bit（免費，見下），本地也不適合（需 LLM 判斷取捨 / MCP-heavy / 跨 system）才 fallback 主 session
- 不確定屬哪類 → 主 session（避免錯派浪費）

#### 派工指令
- **單一入口（推薦）**：`/dispatch` skill — 分類任務（rule-based classifier）→ 載入 AGENTS.md context → 生 packet → 呼叫 `codex-or-local`。把下列散落判斷收斂成一條路徑；advisory hook 提示後直接走這個
- 主路徑（底層）：`codex-dispatch` skill，直接呼叫
  `python3 ~/.claude/skills/codex-dispatch/scripts/codex_dispatch_role.py --task <task.md>`
- **quota 自動 fallback 路徑**：`~/bin/codex-or-local --task <task.md>` — 包 codex-dispatch，quota gate 拒派或 codex CLI 不在時自動轉本地 `Qwopus3.6-27B-Coder-4bit`（local-agent + omlx :8090）。其他 codex 失敗（policy violation / 真錯）會浮出不靜默轉。本地路徑不強制 write-scope → 主 session 事後 review diff。詳見 wiki `local-llm-routing` § Codex fallback
- task packet 必須明確指定 `MODE: worker|verifier|reviewer|synthesizer`、`WORKDIR`、`WRITE SCOPE`、`NON-GOALS`、`VERIFICATION`
- Codex wrapper 會固定使用 `--dangerously-bypass-approvals-and-sandbox`；安全性來自 task packet、git snapshot、policy.json、Pro CC review
- Legacy fallback：`codex-worker`（Agent 工具的 subagent_type）只作相容 shim，會轉呼叫 `codex-dispatch` skill；不要再直接使用舊 `codex exec --full-auto`
- 舊三層路由背景詳見：`memory/codex_dispatch.md`

#### Plan-driven worker task 的 NON-GOALS 紀律

> 來源：2026-04-30 MumbleKey Corrector deepening Phase 2.6 — Codex 在 WRITE SCOPE 內默默改了 plan 沒寫的東西（移除 widget/test target membership），混在大 commit 裡。policy.json 不報 violation 但 plan 對齊跑掉。

- 派 codex-dispatch worker mode 跑 plan-driven 多步任務時，NON-GOALS 必須**逐條列出 plan 沒寫到、即使在 WRITE SCOPE 內也不該動的東西**
- 任務完成後 **必看 git diff 逐 hunk 對 plan**，不只看 policy.json（policy.json 只擋 scope 外改動）
- 不適用：簡單一次性任務（補 typo、補 unit test、單檔 bug fix、verifier/reviewer/synthesizer mode）
- 觸發條件、寫法範例、Pro CC 後檢清單詳見：`For_Claude/company/_shared/references/codex-dispatch-non-goals-discipline.md`

### 產品設計哲學（永久，適用所有產品）
- 小而美、靈活，預設好用，但輕鬆高度客製化
- 像沙子慢慢變成使用者的形狀，愈用愈符合使用者，愈用愈離不開
- 預設就能用（零設定）、處處可調（每一層都開放給用戶改）
- 沒有「沙盒」和「正式」的區分 — 設定直接影響實際結果
- 不靠鎖定留住用戶，靠合身

### 用戶長期目標：開源回饋 + 內容分享 + 曝光規劃
- **開源**：在適當時機主動提醒——手邊做的東西能不能開源？
  - 動機：取之開源、回饋開源，同時建立個人作品集
  - 適用場景：完成工具/腳本/skill 且具通用價值時，引導思考開源可能性
- **分享**：在適當時機提醒並引導把做過的事記錄、分享出去
  - 形式：X 推文、blog 文章、電子報、或其他適合的管道
  - 我的角色：鼓勵、引導、甚至幫忙整理內容草稿
  - 核心想法：槓桿分享的力量，讓做過的事產生更大影響
- **曝光規劃**：主動提議具體的曝光行動，不只提醒、要幫忙規劃
  - 完成一個有展示價值的成果時 → 主動提議「這個可以發一篇 X/LinkedIn」並草擬內容
  - 累積多個成果時 → 提議系列內容或作品集整理
  - 核心邏輯（來自 Reid Hoffman）：*"Start demonstrating your engagement and knowledge with AI in ways that you're easily findable."*
  - 用戶的優勢素材：字幕 pipeline、AI 特助系統、agent teams 多機架構、CLAUDE.md 即樂譜的指揮家模式
- **時機掌握**：不要每次都提，挑有意義的節點（專案告一段落、工具穩定、有趣的學習心得）
