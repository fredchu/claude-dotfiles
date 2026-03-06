---
name: forensic-transcript-translator
description: 法證級美股電話會議逐字稿翻譯工具，含獨立交叉審計。五階段流程：結構指紋提取 → 動態術語鎖定 → 嚴格逐字翻譯 → 獨立 subagent 法證審計 → 組裝輸出。確保 100% 零遺漏、零曲解。使用時機：(1) 使用者提供英文 earnings call 逐字稿檔案並要求翻譯成繁體中文, (2) 使用者要求「法證翻譯」或「forensic translate」, (3) 使用者要求翻譯長篇（超過 2000 字）財報電話會議逐字稿且強調不可遺漏。與 taiwan-earnings-translator 的差異：本技能增加「結構指紋比對」與「獨立 subagent 交叉審計」，適用於對完整性有嚴格要求的場景。
---

# 法證級逐字稿翻譯器 (Forensic Transcript Translator)

五階段流程，將英文 earnings call 逐字稿翻譯為台灣繁體中文，並以獨立審計確保零遺漏。

```
Phase 0: 結構指紋 → Phase 1: 術語鎖定 → Phase 2: 分段翻譯 → Phase 3: 法證審計 → Phase 4: 組裝輸出
```

## 模型路由策略

主對話（Opus 4.6）擔任指揮官，負責流程控制、術語決策、品質判斷。重型工作分派給 subagent：

| Phase | 執行者 | 模型 | 原因 |
|-------|--------|------|------|
| 0 結構指紋 | Task subagent (Bash) | **haiku** | 純腳本執行 |
| 1 術語建立 | 主對話自行處理 | **opus**（當前） | 需要判斷力 |
| 2 分段翻譯 | Task subagent (general-purpose) | **sonnet** | 翻譯重活，Sonnet 品質足夠且快 |
| 3a 腳本審計 | Task subagent (Bash) | **haiku** | 純腳本執行 |
| 3b 語意審計 | Task subagent (Explore) | **haiku** | 比對閱讀，不需生成能力 |
| 3c 問題修復 | 主對話自行處理 | **opus**（當前） | 需要精準重翻判斷 |
| 4 組裝輸出 | 主對話自行處理 | **opus**（當前） | 需要統整所有結果 |

Phase 2 的 Task 呼叫範例：
```
Task(
  subagent_type="general-purpose",
  model="sonnet",
  prompt="你是法證級翻譯員。以下是術語表和翻譯規則...[完整規則]...請翻譯以下段落：[段落內容]"
)
```

Phase 3b 的 Task 呼叫範例：
```
Task(
  subagent_type="Explore",
  model="haiku",
  prompt="你是獨立審計員。請比對以下兩份檔案...[EN_PATH]...[TW_PATH]..."
)
```

## Phase 0: 結構指紋提取

1. 使用 Read 工具讀取使用者提供的英文逐字稿檔案。
2. 將原文存為工作目錄下的暫存檔：`[TICKER]_[QUARTER]_Transcript_EN.tmp`。
3. 執行結構指紋腳本：
   ```bash
   python3 [SKILL_PATH]/scripts/structural_fingerprint.py [EN_TMP_PATH] --json
   ```
4. 記錄指紋結果（段落數、發言者序列、所有數字、字數），後續 Phase 3 比對用。
5. 向使用者回報指紋摘要（段落數、發言者人數、數字總量），然後**自動進入 Phase 1**。

## Phase 1: 動態術語表建立

1. 載入基底術語表：讀取 `references/glossary-base.md`。
2. 掃描原文，找出基底表中**未涵蓋**的公司專屬術語（產品名、業務指標、人名職稱）。
3. 建立本次翻譯的**完整術語表**，格式：

```markdown
## 本次專屬術語
| English | 中文 | 備註 |
|---------|------|------|
| Toast Capital | Toast Capital | 不翻譯 |
| Aman Narang | Aman Narang | CEO |
```

4. 術語表自動生效，**不暫停等待使用者確認**。
5. **自動進入 Phase 2**。

## Phase 2: 分段翻譯

### 翻譯原則（不可違反）

- **原子級鏡像**：嚴禁摘要、刪減、優化語法。
- **口語贅詞保留**："um" → 嗯, "you know" → 你知道的, "uh" → 呃, "well" → 這個, "I mean" → 我的意思是, "sort of" → 算是, "kind of" → 有點, "right?" → 對吧？
- **未完成句子**：如實保留，用 ⋯⋯ 表示中斷。
- **自我糾正**：如實保留（例："revenue was — sorry, operating income was"）。
- **數字格式**：$479.1 million → **4.791億美元**, 25% → **25%**, 130,000 locations → **13萬個餐廳據點**。所有數字加粗。
- **雙語標記**：核心術語採「中文 (English)」格式，依術語表執行。
- **台灣在地化**：使用台灣金管會與財經媒體慣用語。禁用簡體或港式詞彙。

### 排版規範

- **角色標籤**：`**姓名 | 職稱 (Emoji)**`，標籤後強制空一行。
  - 管理層：🎙️
  - 分析師：❓
  - 主持人/Operator：📞
- **章節分隔**：Prepared Remarks 與 Q&A 之間使用 `---`。
- **分析師提問**：使用 Markdown 引用 `>` 區隔。
- **呼吸感**：長段落每 300-500 字依邏輯分段（若原文已有分段則遵循原文）。

### 執行方式

若原文超過 2,000 字，採分段輸出：

1. 按「發言者完整段落」為單位切分，每段約 1,000-1,500 英文字。
2. 每段翻譯前宣告進度：`[進度：X/Y 段 | 術語表已載入]`。
3. 使用 append.py 追加寫入中文暫存檔 `[TICKER]_[QUARTER]_Transcript_TW.tmp`：
   ```bash
   cat [BUFFER_PATH] | python3 [SKILL_PATH]/scripts/append.py [TW_TMP_PATH]
   ```
4. 全部段落翻譯完成後，清除進度標記：
   ```bash
   sed -i '' '/\[進度：.*\]/d' [TW_TMP_PATH]
   ```
5. **自動進入 Phase 3**。

## Phase 3: 獨立法證審計

這是本技能的核心差異化功能。**必須使用 Task 工具開啟獨立 subagent 執行審計**，確保審計者與翻譯者不共享偏見。

### 3a: 自動化腳本審計

執行比對腳本：
```bash
python3 [SKILL_PATH]/scripts/audit_diff.py [EN_TMP_PATH] [TW_TMP_PATH] --json
```

檢查項目：
- 段落數差異是否在容許範圍內（10% 或 3 段）
- 所有數字是否存在於譯文中
- 發言者數量是否一致

### 3b: Subagent 語意審計

使用 Task 工具啟動獨立 Explore subagent，prompt 如下：

```
你是一位獨立的翻譯品質審計員。請比對以下兩份檔案：
- 英文原文：[EN_TMP_PATH]
- 中文譯文：[TW_TMP_PATH]

執行以下檢查：
1. 隨機抽取 5 個段落，逐句比對是否有遺漏、縮寫或意譯
2. 檢查所有發言者的出場順序是否與原文一致
3. 檢查是否有任何句子被合併或拆分
4. 列出所有發現的問題，格式：[段落編號] [問題類型] [具體描述]
```

### 3c: 問題修復

- 若審計發現問題 → 定位該段落 → 重新翻譯 → 覆寫該段 → **再次執行 3a 驗證**
- 若審計通過 → **自動進入 Phase 4**

## Phase 4: 組裝輸出

1. 將暫存檔更名為正式檔案：
   - 中文：`[TICKER]_[QUARTER]_Transcript_TW.md`
   - 英文（保留）：`[TICKER]_[QUARTER]_Transcript_EN.md`
2. 在中文檔案末尾追加：

```markdown
---

## 附錄 A：術語對照表

[插入 Phase 1 建立的完整術語表]

## 附錄 B：審計報告

- 段落數：原文 XX 段 / 譯文 XX 段 ✅
- 發言者：XX 位，序列一致 ✅
- 數字核對：XX 個數字，全數吻合 ✅
- 語意抽查：X 段隨機抽查，無遺漏 ✅
- 審計結果：**PASSED**
```

3. 向使用者回報完成，提供檔案路徑。

## 檔案命名規則

```
[TICKER]_FY[YEAR]Q[QUARTER]_EarningsCall_TW.md
[TICKER]_FY[YEAR]Q[QUARTER]_EarningsCall_EN.md
```

例：`TOST_FY2026Q4_EarningsCall_TW.md`

若使用者未提供 ticker 或季度資訊，從逐字稿內文推斷。

## 參考資源

- 基底術語對照表：`references/glossary-base.md`
- 結構指紋腳本：`scripts/structural_fingerprint.py`
- 審計比對腳本：`scripts/audit_diff.py`
- 追加寫入腳本：`scripts/append.py`
