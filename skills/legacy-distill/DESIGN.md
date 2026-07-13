# legacy-distill deterministic scripts — 設計文件 v3

> 2026-07-13。v3：修 round 2 的 5 major + 2 minor（句子級關聯、編號縮寫解析、砍 wiki-link 目標、claims 計數契約、--expect-claims 子集驗證、inventory 路徑明列、overlap_raw 公式、CJK range）。
> 硬約束：Python 標準庫 only、繁體中文輸出、預設路徑可用 CLI 覆寫（一律 `expanduser()` + `resolve()`）、pytest 合成 fixture 可測。

## 0. 共通 CLI 契約

- `--json` 時所有輸出走 stdout；錯誤物件 schema `{"error": {"kind": "usage|parse|io", "message": str, "path": str|null}}`（exit 2 時亦輸出此 schema）。非 `--json` 時錯誤走 stderr。
- Exit code：`0` 通過／純資訊；`1` gate 未過（洩題／缺線）；`2` usage、解析或 IO 錯誤。
- 參數驗證（違反=exit 2）：`--min-verbatim ≥ 3`；`--overlap-threshold ∈ [0,1]`；`--check` 至少一路徑；模式 mutually exclusive + required。
- `--context`/`--claude-md`：append 語意，**給了任一個就完全取代預設清單**。
- **CJK 判定**：code point ∈ `[㐀-鿿]`（Ext-A + URO）∪ `[豈-﫿]`（相容表意）。假名/諺文不算 CJK 單位（會落入「其他字元」丟棄；本工作區語料為繁中+ASCII，明載此邊界）。

## 1. scripts/leak_check.py — 校準測驗洩題檢查器

### CLI

```
leak_check.py --eval-set <md路徑> [--context <路徑>]...
              [--min-verbatim 8] [--overlap-threshold 0.5] [--json]
```

預設 context 三檔：`~/.claude/projects/-Users-fredchu-Documents-For-Claude/memory/MEMORY.md`、`~/.claude/CLAUDE.md`、`/Users/fredchu/Documents/For_Claude/CLAUDE.md`。

### 解析 grammar

1. `splitlines()`（吃 LF/CRLF）。
2. 題目邊界：`^###\s` 起至下一個 `^###\s` 或 `^##\s`。
3. 欄位標籤 regex（允許 list/blockquote 前綴、半形/全形冒號）：`^\s*(?:[>*-]\s*)*\*\*(情境|誘答|正解|原型|出處)\*\*\s*[:：]`
4. 情境段 = 情境標籤行冒號後文字 + 後續行，直到下一個欄位標籤或題目邊界（情境內文以粗體開頭的一般段落不截斷；誘答/正解絕不併入）。
5. 零題目、或任一題缺「情境」或「誘答」標籤 → parse error（含題目標題）exit 2。

### 正規化與雙訊號（任一命中即洩題）

**正規化序列**：CJK 字元各一單位；連續 ASCII 英數段（lowercase）一單位；其餘丟棄。「10min timeout 先死、空等 6h」→ `[10min, timeout, 先, 死, 空, 等, 6h]`（7 單位）。

1. **逐字子串**：情境序列長度 = `--min-verbatim` 的滑動視窗，以連續子序列出現在任一 context 檔序列 → 洩題。報告命中視窗還原文字 + 來源檔。實作：單位間以不可能出現在單位內的分隔符 join 後做子字串搜尋。
2. **特徵詞重疊率**：
   - 題目 tokens `T`（set）= 情境序列的 CJK 3-gram ∪ 長度 ≥3 的 ASCII 單位。
   - 模板詞 = 出現在 ≥3 題的 `T` 中的 token；特徵集 `F = T − 模板詞`；`C` = 全部 context 檔聯集同法抽取（不剔模板）。
   - `overlap_filtered = |F ∩ C| / |F|`（`F=∅` → 0 + `"warning": "no_distinctive_tokens"`）；`overlap_raw = |T ∩ C| / |T|`（`T=∅` → 0）。
   - 判定：`overlap_filtered > threshold`（嚴格大於）。
   - JSON 與人讀輸出兩值並列（模板剔除效果可回查；「三題互貼同段洩題文字」由訊號 1 兜底，殘餘風險明載）。

### 輸出

- 人讀：逐題一行（題號/標題、判定、逐字命中數、filtered/raw、警告），末尾 `N/M 題洩題`。
- `--json`：`{"questions": [{"id","title","verbatim_hits":[{"text","context_file"}],"overlap_raw","overlap_filtered","warning","leaked"}], "leaked_count"}`。

## 2. scripts/linkage_check.py — 路由閉環檢查器

### CLI

```
linkage_check.py (--inventory | --check <產物路徑>...)
                 [--expect-claims <產物路徑>]...
                 [--memory-md <路徑>] [--claude-md <路徑>]...
                 [--workspace /Users/fredchu/Documents/For_Claude] [--json]
```

- 所有路徑 `expanduser()` + `Path.resolve()` 後比對。
- **`--expect-claims` 集合必須 ⊆ `--check` 集合**（resolve 後比對），否則 usage exit 2——防拼錯路徑讓該受保護的產物漏出 gate。

### --inventory（恆 exit 0；IO 錯誤 exit 2）

明列檢查對象（workspace 相對，除 memory 外）：

- 錨定文件八檔：`company/_shared/references/career-direction-ml-bci-2026-07.md`、`company/_shared/references/user-goals-and-philosophy.md`、`company/_shared/references/strategic-compass-2026-07.md`、`company/_shared/references/post-fable-playbook-2026-07.md`、`company/_shared/references/judgment-eval-set-2026-07.md`、`company/_shared/references/fable-five-observations-2026-07.md`、`本體畫像/00-核心身份.md`、`本體畫像/05-偏好與地雷.md`
- governance：glob `company/_shared/governance/*.md`
- timeline roots：`wiki/model-succession-*.md` + `company/_shared/references/*playbook*.md`，取 `- YYYY-MM-DD |` 行最大日期；無 → 「無紀錄（首跑）」
- MEMORY.md（預設 `~/.claude/projects/-Users-fredchu-Documents-For-Claude/memory/MEMORY.md`）行數 / 200

輸出：每檔存在與否 + mtime 日期；缺檔標示但不影響 exit code。

### --check（gate 模式）

**檢查 1 可發現性**：產物 basename（含/不含 `.md`）出現在 MEMORY.md 或任一 CLAUDE.md → 通過。

**檢查 2 雙向性**（v3：句子級關聯）：

- **關聯單位 = 句子**：先按行切，行內再按 `。！？；` 切。宣稱 = **同一句**內同時含宣稱動詞（`更新|接續|放寬|升格|取代|已被`）與 ≥1 個目標參照。（v2 的段落級會把「必須先讀 A.md、B.md」與兩句後的「→ 更新文件」誤關聯——真實 playbook §4 實測誤抓三個錨定檔，round 2 finding。）
- **目標參照 pattern（三種）**：
  1. 完整 governance stem：`0\d-[a-z][a-z-]+`，`.md` 後綴可選，可後接 `§`/空白/標點（命中「02-model-dispatch §5 的接續」）
  2. **編號縮寫**：`0\d(?=\s*§)`（命中「02 §6 已有此法…升格」）→ 以兩位數前綴對 governance glob 解析；同前綴多檔 → 違規報「縮寫歧義」
  3. 一般檔名：`[A-Za-z0-9._-]+\.md`
  - **不含 `[[wiki]]`**（v3 砍除：wiki 標題→檔名映射需讀 index，超出純字串工具範圍；wiki 圖健康本屬 /wiki lint 職責，「非目標」段已列）。
- **目標解析到檔案**：stem/縮寫 → `<workspace>/company/_shared/governance/`；一般檔名 → 依序搜 `company/_shared/governance/` → `company/_shared/references/` → memory 目錄（MEMORY.md 所在目錄）→ `wiki/`。候選數：0 → 違規「目標不存在」；1 → 檢查它；>1 → 全部檢查，**任一含回指即通過**（發現層 fail-closed、副本層寬鬆，明載）。
- **回指檢查**：目標檔內文含產物 basename 或 stem → 該 edge 通過。
- **計數契約（防 fail-open 指標失真）**：輸出兩個計數——`claim_sentences_found`（含宣稱動詞+目標的句子數）與 `target_edges`（(句子,解析目標) 對數，同句多目標=多 edge）。每個產物必報兩值；`--expect-claims` 的判準 = `target_edges ≥ 1`，零 → exit 1。每條宣稱附句子原文摘錄（人工稽核用）。
- **方向/否定不判**（fail-closed，v2 決策不變）：「不取代 X」「已被 X 取代」都觸發對 X 的回指檢查；誤抓=多查一條線，假違規由主 session 人工判讀豁免。

### 範圍對齊

雙向性目標範圍 = 上述 pattern 可參照的檔（governance + 四目錄可定位的 `.md`）。SKILL.md Contract (3) 與 Phase 7 已同步此範圍（wiki 參照不在內）。

## 3. 測試矩陣（test/，pytest，tmp_path，分支間 fixture 互不干擾）

leak_check：
- 逐字：純 CJK 命中／混合 `10min timeout 先死` 型命中／不足 min-verbatim 不命中／命中報告含 context 檔
- overlap：正命中（無逐字重疊）／恰等於閾值不洩題／`F=∅` warning／raw vs filtered 雙值
- 模板剔除：三題共用開場白（< min-verbatim 單位且不在 context，隔離訊號 1）
- 多 context（第二檔才命中）／`--context` 取代預設
- parser：list/blockquote 標籤、全形/半形冒號、CRLF、多行情境、情境內粗體不截斷、缺情境/缺誘答 exit 2、缺檔 exit 2 + error JSON
- 參數：threshold 1.5／min-verbatim 2 → exit 2；--json schema

linkage_check：
- 可發現＋回指 → 0；不可發現 → 1 + 明細
- 宣稱偵測：同句含 `.md`／同句 stem 無 `.md` + `§`（round-1 blocker 場景）／**編號縮寫 `02 §6`**（round-2 場景）／**動詞與目標不同句 → 不成宣稱**（真實 playbook §4 誤抓場景的合成重現）
- 目標不存在 → 1；存在無回指 → 1 + 指出補哪檔；縮寫歧義（兩檔同前綴）→ 1
- basename 多候選：兩目錄同名、僅一含回指 → 通過
- 零宣稱：無 expect → 通過但 `target_edges: 0` 顯式輸出；有 expect → 1
- `--expect-claims` 不在 `--check` 集合 → exit 2
- 否定句「不取代 X」→ 觸發檢查（fail-closed 鎖進測試）
- inventory smoke：假 workspace（timeline 抽取／無 timeline 首跑訊息／行數／缺檔標示）
- 模式互斥同給/皆不給 → 2；--check 無路徑 → 2；錯誤 JSON schema

## 4. E2E（主 session 跑，worker 範圍外）

- `leak_check.py --eval-set <真實 judgment-eval-set-2026-07.md>`：期望 0 洩題；邊緣命中則校準閾值並記錄。
- `linkage_check.py --check <遺產五檔> --expect-claims <playbook 路徑>`：期望全通過；playbook 斷言**目標集合**（非只數量）：解析出的 target edges 涵蓋 `02-model-dispatch.md` 與 `03-judgment-rubrics.md`（02:72,86、03:75 已有回指，round 2 實查）。
- `linkage_check.py --inventory`：期望 8 錨定檔 + 6 governance 檔、上次蒸餾 2026-07-12。

## 5. 非目標

- 不自動修（報告 only）
- 不做語意方向/否定判斷（fail-closed，誤抓人工豁免；不設白名單）
- 不解析 `[[wiki]]` 參照、不掃 wiki 內部連結健康（/wiki lint 職責）
- 不處理繁中以外的 CJK 變體語料（假名/諺文不入單位，§0 明載）
