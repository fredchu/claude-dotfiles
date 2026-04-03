---
name: podcast-digest
description: "播客消化 pipeline：URL/音檔 → 帶講者分離的逐字稿 + AI 摘要 + 高光 + Q&A。觸發詞：「跑播客」「podcast digest」「消化這集」「幫我聽」「transcribe podcast」。也適用於用戶貼了一個播客 URL 或音檔路徑並暗示需要摘要/逐字稿的場景。不適用於：已有文字只想潤稿（用 polish）、影片字幕（用 srt）、純翻譯（用 translator）。"
---

# Podcast Digest Pipeline

將播客 URL 或音檔轉為摘要或完整逐字稿。兩種模式：

- **輕量模式**：NLM 摘要（~5 分鐘），快速掃一眼新集內容
- **完整模式**：ASR + 講者分離 + 校正 + 翻譯（~25 分鐘），深度消化

```
摘要一下 https://pca.st/episode/xxx        ← 輕量
深讀 https://www.youtube.com/watch?v=xxx     ← 完整
跑播客 /path/to/audio.mp3                   ← 完整
```

支援來源：YouTube、Pocket Casts、Apple Podcasts、純 mp3/wav URL、本地檔案、RSS feed。

---

## 模式選擇

| 用戶說的話 | 模式 |
|-----------|------|
| 「摘要一下 {URL}」「先看摘要」「podcast 摘要 {URL}」「輕量 {URL}」 | 輕量 |
| 「深讀 {URL}」「跑播客 {URL}」「消化這集」「transcribe」「/podcast-digest {URL}」 | 完整 |
| 「深讀 最新的{節目}」 | 完整（SSH Mini CC 找音檔） |
| 用戶貼 URL 但沒有明確指示 | **詢問**：「要摘要就好，還是深讀出完整逐字稿？」 |

---

# 輕量模式（NLM Pipeline）

## Stage L1: 解析 URL + metadata

與完整模式相同的 metadata 提取流程（見 Stage 1）。存入 `/tmp/podscribe-work/metadata.json`。

## Stage L2: 下載音檔

```bash
mkdir -p /tmp/podscribe-work
# 直接下載 mp3，不需轉 WAV（NLM 直接吃 mp3）
curl -L -o /tmp/podscribe-work/episode.mp3 "{AUDIO_URL}"
# YouTube 用 yt-dlp：
# yt-dlp -x --audio-format mp3 -o /tmp/podscribe-work/episode.mp3 "{URL}"
```

## Stage L3-L4: NLM 摘要 + 存檔

### 🔧 nlm-digest.py

```bash
python3 ~/.claude/skills/podcast-digest/scripts/nlm-digest.py \
  --audio /tmp/podscribe-work/episode.mp3 \
  --show "{SHOW_NAME}" \
  --title "{EPISODE_TITLE}" \
  --guest "{GUEST}" \
  --date "{DATE}" \
  --duration "{DURATION}" \
  --output "company/podscribe/transcripts/{slug}-summary.md"
```

腳本一次完成：
1. 讀/寫 `nlm-state.json`（notebook 映射，每個節目一個 notebook）
2. `notebooklm create` or reuse → `source add` → `source wait` → `ask`（固定 prompt）
3. Strip NLM citation 引用編號 `[1, 2]` + 尾部跟進問句
4. 寫出帶 frontmatter 的 summary markdown

### Readwise 推送

```bash
python3 ~/.claude/skills/podcast-digest/scripts/push_readwise.py \
  "company/podscribe/transcripts/{slug}-summary.md" \
  --slug "{slug}" \
  --title "🎙️ {SHOW_NAME} — {EPISODE_TITLE}" \
  --summary "{從 NLM 摘要第一章提取 2-3 句，≤200字}" \
  --metadata /tmp/podscribe-work/metadata.json \
  --tags podscribe podcast summary
```

### 更新 index.md

`company/podscribe/index.md` 加一行，標 `summary` tag：

```markdown
- **{Show} — {Title}**
  {lang} | summary | {tags} | {duration} | [summary](transcripts/{slug}-summary.md)
```

### 不寫 Apple Notes

輕量摘要太短，不值得佔 Apple Notes 空間。

## Stage L5: 清理

```bash
rm -rf /tmp/podscribe-work
```

## 後續升級

輕量摘要完成後，用戶可隨時說「深讀這集」→ 用同一 URL 跑完整模式，產出會覆蓋 index.md 中的 summary 條目。

---

# 完整模式（Full Pipeline）

## 設計原則

每個 Stage 分為兩種步驟：
- **🔧 腳本步驟**：確定性邏輯，用 `scripts/` 下的腳本執行。**禁止現場重寫這些邏輯。**
- **🧠 LLM 步驟**：需要語言理解的工作（校正、摘要、翻譯），用 sonnet subagent 平行處理。

工作目錄：`/tmp/podscribe-work/`，pipeline 完成後清理。

---

## Stage 1: 下載 + metadata 提取

### 🔧 下載音檔

```bash
mkdir -p /tmp/podscribe-work
AUDIO_PATH=$(~/.claude/skills/podcast-digest/scripts/download.sh "{INPUT_URL_OR_PATH}")
```

腳本處理：YouTube → yt-dlp、純 URL → curl、本地檔案 → 直接使用、最後 ffmpeg 轉 16kHz mono WAV。

**Pocket Casts 例外**：download.sh 無法處理 Pocket Casts（需 MCP 工具解析 JS 頁面）。手動流程：
1. `ScraplingServer get` 抓頁面 HTML（`extraction_type: html`）
2. 從 `<a href="...audio.mp3" download>` 提取 mp3 URL
3. `curl -L -o /tmp/podscribe-work/episode.mp3 "$MP3_URL"`
4. `ffmpeg -i episode.mp3 -ar 16000 -ac 1 -f wav episode.wav -y`

### 🔧 metadata 提取

提取後存入 `/tmp/podscribe-work/metadata.json`：

```json
{"cover_url": "...", "podcast_name": "...", "episode_title": "...", "duration": "...", "publish_date": "..."}
```

封面圖提取方式：
- Pocket Casts → `ScraplingServer get` 抓 `meta[property='og:image']`（**必須 `main_content_only=false`**）
- YouTube → `yt-dlp --dump-json` 的 `thumbnail`
- Apple Podcasts → feed XML 的 `<itunes:image href="...">`

**封面圖驗證（不可省略）**：
```bash
curl -sI "$COVER_URL" | head -1 | grep -q "200" || COVER_URL=""
```

---

## Stage 2: 語言偵測

優先級：用戶指定 > subscriptions.yaml > 自動偵測（看頁面語言或前 30 秒音頻）。

---

## Stage 3: ASR + 講者分離（平行）

兩條用 Bash `&` + `wait` 平行跑。

### 🔧 ASR（按語言路由）

中文：
```bash
xcrun --sdk macosx swift ~/.claude/skills/podcast-digest/scripts/asr-zh.swift "$AUDIO_PATH" > /tmp/podscribe-work/asr.json
```

英文（必須加 `--output-json` 取得 word-level timestamps）：
```bash
cd ~/ghkb/interested/FluidAudio && swift run -c release fluidaudiocli transcribe "$AUDIO_PATH" --output-json /tmp/podscribe-work/asr-raw.json
```

### 🔧 講者分離（中英通用）

```bash
cd ~/ghkb/interested/FluidAudio && swift run -c release fluidaudiocli process "$AUDIO_PATH" --mode offline --output /tmp/podscribe-work/diarize.json
```

---

## Stage 4: 對齊合併

### 🔧 align.py

```bash
# 英文（word-level alignment）
python3 ~/.claude/skills/podcast-digest/scripts/align.py \
  --asr-words /tmp/podscribe-work/asr-raw.json \
  --diarize /tmp/podscribe-work/diarize.json \
  --host "{HOST_NAME}" --guest "{GUEST_NAME}" \
  --output /tmp/podscribe-work/aligned.json

# 中文（segment-level alignment）
python3 ~/.claude/skills/podcast-digest/scripts/align.py \
  --asr /tmp/podscribe-work/asr.json \
  --diarize /tmp/podscribe-work/diarize.json \
  --host "{HOST_NAME}" --guest "{GUEST_NAME}" \
  --output /tmp/podscribe-work/aligned.json
```

自動執行：noise cluster 過濾、speaker-word 對齊、智慧斷句、同講者合併、auto speaker detection（4 訊號投票）、guest name 提取。

---

## Stage 5: Sonnet 校正

### 🧠 分 chunks 平行校正

讀取 aligned.json，按 ~5000 chars 分 chunks，每 chunk 一個 sonnet subagent。

**校正 prompt 模板**（每個 subagent 都帶這段）：

```
你是中文播客逐字稿校正專家。校正以下 ASR 輸出。

節目：{podcast_name}，主持人：{host}，來賓：{guest}。主題：{topic}。

校正規則：
1. 標點符號 — 補齊句號、逗號、問號
2. 錯字/專有名詞 — 修正 ASR 誤辨（已知術語：{terms_list}）
3. 斷句 — 確保句子正確分隔
4. 分段 — 段落內按主題插入 \n\n
5. 段落標題 — 新主題段落加 **標題** — 格式

讀取 {chunk_path}，校正每個 segment 的 text，保留 start/end/speaker 不變。
寫回 {output_path}（同格式 JSON array）。
```

校正完合併為 `/tmp/podscribe-work/corrected-all.json`。

---

## Stage 6a: LLM 結構化

### 🧠 平行產出 4 項（每項一個 sonnet subagent）

每個 subagent 讀取 corrected-all.json，產出寫入對應 .md 檔：

| 產出 | 檔案 | 要求 |
|------|------|------|
| 分章節摘要 | `/tmp/podscribe-work/summary.md` | 6-10 章，每章 3-5 句，`[MM:SS]` 時間戳 |
| 高光片段 | `/tmp/podscribe-work/highlights.md` | 8-10 個，帶引用原文 + 為什麼值得注意 |
| 關鍵字 | `/tmp/podscribe-work/keywords.md` | 三類：人名、公司/產品、概念/術語 |
| Q&A | `/tmp/podscribe-work/qa.md` | 6-8 題，帶時間戳參考 |

**語言規則**：中文播客 → 繁體中文產出。英文播客 → 全部繁體中文產出，關鍵字保留英文原文加中文說明，高光引用附英文原句。

## Stage 6b: 中文翻譯（英文播客必跑）

### 🧠 分 chunks 平行翻譯

英文播客限定。分 chunks 平行發 sonnet subagent，每 segment 加 `text_zh` 欄位。

翻譯規則：繁體中文（台灣用語）、英文專有名詞保留原文、技術術語首次出現加中文說明。

---

## Stage 7: 組裝 + 存檔

### 🔧 組裝（assemble.py）

```bash
python3 ~/.claude/skills/podcast-digest/scripts/assemble.py \
  --corrected /tmp/podscribe-work/corrected-all.json \
  --summary /tmp/podscribe-work/summary.md \
  --highlights /tmp/podscribe-work/highlights.md \
  --keywords /tmp/podscribe-work/keywords.md \
  --qa /tmp/podscribe-work/qa.md \
  --title "{TITLE}" --host "{HOST}" --guest "{GUEST}" \
  --date "{DATE}" --duration "{DURATION}" \
  --output "company/podscribe/transcripts/{slug}.md"
  # 英文播客加 --bilingual
```

### 存檔目的地

**1. 本地**（assemble.py 已處理）：`company/podscribe/transcripts/{slug}.md`

**2. Apple Notes**（精簡版：摘要 + 高光 + 關鍵字）：
- `mcp__apple-notes__create-note`（format: html）→ `mcp__apple-notes__move-note` 到「Claude 工作區」
- HTML 格式用 `<h2>`/`<h3>`/`<b>`/`<ul><li>` 語義化標籤，不用 `<br>`

**3. 🔧 Readwise Reader**（push_readwise.py）：

```bash
python3 ~/.claude/skills/podcast-digest/scripts/push_readwise.py \
  "company/podscribe/transcripts/{slug}.md" \
  --slug "{slug}" \
  --title "{TITLE}" \
  --summary "{2-3 句中文摘要，≤200字}" \
  --metadata /tmp/podscribe-work/metadata.json \
  --tags podscribe podcast
```

腳本自動處理：md → 語義化 HTML（via md2html.py）→ Readwise API POST（含 image_url + summary）。

**Readwise 注意事項**：
- `image_url` 和 `summary` 必須在首次 POST 就帶齊（事後 upsert 不會更新這兩個欄位）
- 摘要規則：2-3 句繁體中文，涵蓋來賓身份 + 核心主題 + 最有記憶點的論點，≤200 字

**4. 更新 index.md**：`company/podscribe/index.md`

### 🔧 清理

```bash
rm -rf /tmp/podscribe-work
```

---

## 共用規則

### 檔名規則

slug 化：日期前綴 `YYYY-MM-DD_`、英文全小寫、空格/破折號 → `-`、移除特殊字元、中文保留、連續 `-` 合併。

### 腳本清單

| 腳本 | 用途 | 模式 | 可現場重寫？ |
|------|------|------|------------|
| `scripts/nlm-digest.py` | NLM 摘要（notebook 管理 + ask + 清理） | 輕量 | 否 |
| `scripts/download.sh` | 下載 + ffmpeg 轉檔 | 完整 | 否 |
| `scripts/asr-zh.swift` | 中文 ASR（Speech.framework） | 完整 | 否 |
| `scripts/align.py` | 對齊合併 + auto speaker detection | 完整 | 否 |
| `scripts/md2html.py` | Markdown → 語義化 HTML | 兩者 | 否 |
| `scripts/assemble.py` | 組裝最終 markdown | 完整 | 否 |
| `scripts/push_readwise.py` | 推送 Readwise Reader | 兩者 | 否 |

**「可現場重寫？否」= 禁止在 session 中現場寫替代函數。有 bug 就修腳本本身。**

### 技術棧

| 元件 | 技術 |
|------|------|
| 中文 ASR | Speech.framework DictationTranscriber |
| 英文 ASR | FluidAudio Parakeet TDT v3 |
| 講者分離 | FluidAudio Offline VBx |
| 對齊合併 | align.py |
| 校正/翻譯/結構化 | Claude Code sonnet subagents（平行） |
| NLM 摘要（輕量模式） | NotebookLM CLI + Google NotebookLM |
| HTML 轉換 | md2html.py（語義化 HTML，禁止 `<br>` 灌空行） |
| 組裝 | assemble.py |
| 存檔 | 本地 Markdown + Apple Notes MCP + push_readwise.py |

### 牛牛清單連動

消化完投資類播客後，如果提到值得關注的標的，主動建議：
「播客提到 XXX，要不要放進牛牛的 YYY 清單觀察？」

### Plan 文件

- 完整規劃：`/Users/fredchu/Documents/For_Claude/company/podscribe/references/podcast-digest-system-plan-2026-03-26.md`
- 技術驗證：`/Users/fredchu/Documents/For_Claude/company/podscribe/references/asr-diarization-feasibility-test-2026-03-26.md`
