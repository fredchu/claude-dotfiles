---
name: bookcast
version: 1.0.0
description: >
  把 EPUB 電子書變成有聲書並發佈成私人 podcast feed（extract → 合成 → 組裝 m4a →
  publish → 部署）。當用戶說「把這本書做成有聲書」「產有聲書」「唸成 podcast」
  「bookcast」「這本書我想用聽的」「合成進度到哪」「重新部署 feed」，或給一個 EPUB
  路徑並表明要用聽的時使用。也適用於查詢某本書的合成進度、續跑中斷的合成、
  重出 m4a、更新 feed。
  不適用於：翻譯電子書（用 book-translator）、影片字幕（用 srt）、
  把音檔轉文字（用 speech-to-prose／podcast-digest）、互動式讀書課（用 bookmate）。
---

# bookcast — EPUB → 私人有聲書 podcast

真相源：`~/dev/bookcast`（GitHub `fredchu/bookcast`，private，Apache-2.0）。
書的工作目錄在 `~/dev/bookcast/books/<slug>/`，發佈用的成品在 `library/`。

## 五步流程

```bash
cd ~/dev/bookcast

# 1. 抽章節（雙語翻譯 EPUB 也吃）
python3 -m bookcast.cli extract <book.epub> --book-dir books/<slug>

# 2. 人工修剪 books/<slug>/manifest.json：拿掉目錄頁、版權頁、註釋頁
#    （用戶通常要看過才動工；chars 欄位是後面 duration 驗證的依據）

# 3. 合成（唯一該用的跑法，見下方硬規則）
bin/bookcast_run.sh books/<slug>

# 4. 組裝 m4a：章節軌＋封面＋VTT 逐字稿，內建驗證
python3 -m bookcast.cli assemble --book-dir books/<slug>

# 5. 發佈：進 library/、重生 RSS、推到主機
python3 -m bookcast.cli publish --book-dir books/<slug> --library library
python3 -m bookcast.cli feed --library library --base-url "$BOOKCAST_FEED_BASE/$(cat .feed_token)"
bin/deploy.sh
```

## 硬規則（踩到就是重跑一整晚或資料損毀）

- **`books/<slug>/wav/` 與 `state.json` 是合成進度，絕不刪**。一本書的 wav 快取是 GB 級
  （superagency 2.2GB / 2582 chunks）。要清理先問用戶。
- **`--max-chars` 換值會作廢同書已合成的進度**（chunk id 是文本雜湊）。續跑必須沿用原值；
  要改就換一本新書從頭測。目前預設 80，品質已驗到 ~150。
- **同一本書不可中途換引擎**。torch 引擎輸出 48kHz、MLX 引擎不同，assemble 會以
  `audio format mismatch` 擋下整批。
- **合成一律走 `bin/bookcast_run.sh`**，它自我脫鉤成新 session（免疫 Claude Code 每半小時
  的背景任務清除波次）＋防睡眠＋完成推 Discord。不要在前景直接跑 `cli synth`。
- **章節工具**：PATH 上有 `mp4chaps` 就用它，否則用 gpac 的 `MP4Box`，都沒有會 fail loud。
  macOS 兩者皆有；Linux/Windows 實際上只有 MP4Box（mp4v2 已從 Ubuntu 24.04 移除）。
- **部署設定在 `bin/deploy.env`**（gitignored，不進版控）。缺設定會 fail loud。
  實際值與完整架構：`For_Claude/company/bookcast/references/2026-08-11-bookcast-personal-deploy.md`。

## 常見任務

| 用戶說 | 做什麼 |
|---|---|
| 「合成到哪了」 | 讀 `books/<slug>/state.json` 的 `chunk_order` 長度與 `errors`，或 `tail books/<slug>/synth.log` |
| 「繼續跑」 | 直接再跑 `bin/bookcast_run.sh books/<slug>`，chunk 級續跑不掉進度 |
| 「重出 m4a」 | 只跑 assemble；它會寫暫存檔、全驗證過才原子替換，失敗不會毀掉舊成品 |
| 「feed 掛了」 | `curl -A <自訂UA> "$BASE/$TOKEN/feed.xml"` 應 200、`-r 0-100` 應 206、根路徑應 404。urllib 預設 UA 會被 Cloudflare 403，測試要帶 UA |
| 「換聲音」 | `--ref-audio/--ref-text` 指到 `voices/` 下另一組錨點；換錨點等於換音色，同一本書不要中途換 |
| 「讀音怪怪的」 | `books/<slug>/lexicon.json` 做 TTS 前的字面替換，改完只有未合成的 chunk 會生效 |

## 平台與引擎

- 預設 `--engine auto`：Apple Silicon → `mlx`（已驗證，M1 Max RTF 1.3–1.8），其餘 → `torch`。
- **torch 引擎從未在真機 GPU 跑過**（作者沒有那類硬體）。要判斷一台新機器值不值得跑整本：
  `python tests/test_spike_manual.py --engine torch`，它會印 RTF 與「7h book ≈ Xh Ym」。
- 沒有顯卡＝不切實際（比即時慢一個數量級）。

## 改這個 repo 的時候

- 派工前把 `~/dev/bookcast/AGENTS.md` 內容帶進 packet。
- repo 有三平台 CI（ubuntu/macos/windows）；**push 後要確認 CI 綠**，本機綠不等於 CI 綠
  （2026-08-11 首跑就抓到兩個本機看不見的缺陷：Ubuntu 24.04 沒有 mp4v2-utils、
  Linux 的 ffmpeg 會在失敗前截斷輸出檔）。
- 平台差異只能落在兩條縫：引擎 registry（`bookcast/engines/`）與外部工具 PATH 偵測
  （`_detect_chapter_tool`）。主幹不准出現平台分支。
- 外部協作者：Bocky（`bockybocky`）、CK（`cking2001`），write 權限，2026-08-11 邀請。
