---
name: legacy-distill
version: 1.0.0
description: |
  強模型遺產蒸餾儀式。當主力模型即將退役、有特別強大的模型短暫可用、或每季定期，
  把該模型的判斷力外化成弱模型可執行的持久資產：失敗歸因 → 判斷外化（觸發詞→機械
  動作）→ 校準測驗（同構變體）→ 戰略判讀 → 開放觀察 → fresh-context 對抗審查 →
  雙向路由閉環。源自 2026-07-11~13 Fable 5 退役實跑（wiki:
  model-succession-judgment-externalization）。觸發語：「遺產蒸餾」「跑一次遺產蒸餾」
  「模型要退役了」「新的強模型出現了，跑一遍 Fable 流程」「最後一天用 X 模型，留下遺產」
  "legacy distill"、"model succession ritual"。不適用於：分析用戶自己的歷史
  （用 session-mirror）、單純模型評測（用 model-fit-scout / benchmark-models）。
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Agent
  - Skill
mutating: true
---

# Legacy Distill — 強模型遺產蒸餾儀式

## Contract

跑完一輪後保證：(1) 該模型任期內的判斷力缺口有歸因分析與機械補償協議；(2) 校準測驗
可施測且不被常載 context 洩題（leak_check 通過）；(3) 每個新產物可被 MEMORY.md 或
CLAUDE.md 發現，且產物宣稱更新/接續的 governance、references、wiki 目標檔有指回
（linkage_check 通過；範圍=其目標 pattern 可參照到的檔，語意方向不判、fail-closed）；
(4) 全部產物經過「目標讀者等級」fresh-context 對抗審查，blocker 清零；(5) 用戶策略層
拿到當期判讀與羅盤之外的開放觀察。

核心原理（一句話）：模型間能力差距在「明確指令執行」上最小、在「開放判斷」上最大，
所以遺產的正確形態是把判斷外化成「觸發詞 → 機械動作」——規則的失效點在「讀者評估
這條適不適用」那一步，觸發器設計就是把那一步消掉。

## 觸發情境（三選一，開跑前確認）

| 情境 | 重點差異 |
|------|---------|
| 主力模型即將退役 | 全流程；Phase 4/5 由退役模型本人執筆（它對用戶的累積判讀最深） |
| 強模型短暫可用（新旗艦試用、限時額度） | 全流程壓縮；優先 Phase 1-3（缺口補償）與 Phase 5（它看得到現任看不到的連結） |
| 定期保養（每季，跟 career-direction 季度回顧同節奏） | 只跑 Phase 1 增量歸因 + Phase 3 補題 + Phase 6 審查；羅盤僅過時才更新 |

## Phases

### Phase 0：定位盤點（deterministic）

```bash
python3 scripts/linkage_check.py --inventory
```

列出：錨定文件清單與最後更新日、governance 檔清單、上次蒸餾日期（找
`references/*playbook*` 與 wiki `model-succession-*` 的最新 timeline entry）、
MEMORY.md 行數餘裕。人工確認觸發情境屬於上表哪一種，決定要跑的 Phase 子集。

### Phase 1：失敗歸因（Explore agent，very thorough）

派 Explore agent 掃 `company/_shared/lessons/` 全部 + memory `feedback_*` 檔（上次
蒸餾日期之後的為主，首跑全掃）。每個失敗案例回答一個問題：**判斷力型**（更強模型會
自己避開；換弱模型會重演）還是**資訊型**（缺環境知識，讀了 memory 就能避開）？
產出四段：A 判斷力型清單（失敗+缺的判斷）、B 資訊型清單、C 高頻缺口模式排序（附案例
佐證）、D「現有規則假設讀者高判斷力」的寫法清單（例外靠自由心證、關鍵詞未定義、
判準分散多檔、要求自發反事實推演）。存 `company/_shared/lessons/YYYY-MM-DD-failure-mode-capability-attribution.md`。

### Phase 2：判斷外化（主 session 執筆）

把 Phase 1 的 C/D 段寫成（或增量更新）補償手冊：每個高頻缺口一條「觸發詞 → 機械動作」
——看到觸發詞就做動作，禁止「評估這次需不需要」。既有手冊
`references/post-fable-playbook-2026-07.md` 是格式範本與第一版；增量跑時直接更新它
（🟡 級留痕）。若升級天花板、驗證模式等規則語意有變 → 🔴，diff 給用戶核准。

### Phase 3：校準測驗補題（主 session 執筆 + deterministic gate）

Phase 1 若揭示新的判斷反射，往 `references/judgment-eval-set-*.md` 加題。**鐵則：
情境必用同構變體**（表面故事虛構、判斷結構不變、真實原型列出處）——受測 session 的
context 必然載著 MEMORY.md/CLAUDE.md，拿真實事故當題目=測記憶回想，無效。寫完跑：

```bash
python3 scripts/leak_check.py --eval-set <path>
```

它把每題情境段的關鍵詞比對常載 context（MEMORY.md、兩個 CLAUDE.md），高重疊即標
洩題，換皮重寫直到通過。

### Phase 4：戰略判讀（強模型執筆，先重讀錨定文件）

重讀全部錨定文件（career-direction、user-goals-and-philosophy、本體畫像 00+05、
交易框架），確認理解沒漂移後，更新或撰寫戰略羅盤（`references/strategic-compass-*.md`）：
課題清單（現狀/關鍵思考方向/癥結點/給後繼模型的指引）+ 思考模式清單 + 盲區誠實條款。
規則：**每個判讀指得出建立在哪份文件哪一句上，指不出來就不寫**。

### Phase 5：開放觀察（enlighten me — 強模型最不可替代的一步）

問自己：「羅盤之外，我還看到什麼用戶自己想不到的連結？」產出 3-5 條觀察，每條標
「討論邀請非結論」。用戶認領後存 `references/`，並附**後繼模型使用說明**：情境自然
觸及才接續（每條寫明觸發情境），勿主動轟炸；展開有結論後沉澱回錨定文件並回標。

### Phase 6：fresh-context 對抗審查（不可跳過——首跑抓到 2 個 blocker）

派**目標讀者等級**的 fresh-context agent（現制=sonnet）審查全部產物，維度：路徑與
章節號真實性（必實查）、觸發器可執行性（審查者讀兩遍還不確定怎麼做=finding）、與
governance 的規則衝突、eval 洩題模擬作答、弱模型會誤讀的模糊句。Blocker 全修，
🔴 級修法過用戶核准 gate。做的人不驗自己——審查者不得看到撰寫過程的推理。

### Phase 7：路由閉環（deterministic gate + 🔴 核准）

```bash
python3 scripts/linkage_check.py --check <新產物路徑...> --expect-claims <補償手冊路徑>
```

驗證：每個新產物被 MEMORY.md 或 CLAUDE.md 指到（可發現性）；新產物宣稱「更新/接續」
的目標檔（governance stem、`.md` 檔名、[[wiki]] 參照）有指回新產物（防單向失聯的
版本分裂，01-diagnosis §2）。每個產物必報 claims_found，列入 --expect-claims 的產物
零宣稱=違規（防 fail-open）。缺線就補：MEMORY.md
索引（🟢）、governance 補充行與 CLAUDE.md 觸發段（🔴，diff 過用戶）。最後明確
pathspec commit（禁 `git add -A`）、用戶說 push 才 push、`/wiki add` 吸收、
session-handoff 交接。

## Output

- `company/_shared/lessons/YYYY-MM-DD-failure-mode-capability-attribution.md`（Phase 1）
- `company/_shared/references/`：補償手冊 / eval set / 羅盤 / 觀察（Phase 2-5，新建或更新）
- memory 指針檔 + MEMORY.md 索引行（Phase 7）
- CLAUDE.md / governance 路由行（Phase 7，僅經用戶核准）
- git commits（明確 pathspec）；wiki 文章（經 /wiki add）

## Anti-Patterns（皆為 2026-07 首跑實際踩過或攔下）

- ❌ 拿真實歷史事故直接當測驗情境（常載 context 結構性洩題；同構變體才測得到遷移）
- ❌ 新檔宣稱升級舊規則但舊檔不指回（舊路由讀者永遠看到舊版；linkage_check 就是為此存在）
- ❌ 產物寫完就宣稱完成（首跑被 fresh-context 審查抓到 2 blocker + 「宣稱 15 題實為 16 題」）
- ❌ 補償寫成「原則」而非「觸發詞→機械動作」（弱模型在適用性評估那步失守）
- ❌ 策略判讀不引錨定文件（自由發揮會偏移用戶既定方向）
- ❌ 把 Phase 5 觀察寫成結論並主動轟炸（它們是討論邀請，情境觸及才接續）
