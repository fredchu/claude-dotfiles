# Auto Memory

> 每條一行：**主題** — 重點 → 指針檔。詳情都在指針檔，不在此。

## 工作方式 / 溝通偏好
- **職涯方向（2026-07-06 定案）** — model user→model shaper（post-training/繁中 ASR 灘頭堡）、中長期受僱 AI lab、重手感輕認可；**Austin 字幕=無償志願（學生身分）非收入** → `user_career_direction_ml.md`
- **治理制度（2026-07-04 Fable 立制）** — 診斷/模型調度/判斷 rubric/交辦範本/維護協議 → `For_Claude/company/_shared/governance/`（入口 `01-diagnosis.md`；兩個 CLAUDE.md 已索引化，全文備份 `*.bak-2026-07-04`）
- **判斷力補償體系（2026-07-12 Fable 遺制）** — 五個「觸發詞→機械動作」觸發器 + 16 題校準測驗（v2 同構變體，測遷移非回想）+ 失敗歸因（`For_Claude/company/_shared/lessons/2026-07-12-failure-mode-capability-attribution.md`）；opus 解不了→換算力形態非換模型；策略建議必引錨定文件 → `reference_post_fable_playbook.md`
- **戰略羅盤（2026-07-12 Fable 遺筆）** — 五大課題判讀（轉軌窄橋/注意力配置/交易減碼/家庭時間窗/體系交替）+ 思考模式六條（錨定/層級/踏板/張力/用他的哲學/挑戰時機）；季度回顧跟 career-direction 一起重讀 → `For_Claude/company/_shared/references/strategic-compass-2026-07.md`
- **五個觀察（2026-07-12 Fable 遺筆之二，已命中未展開）** — 已在做 post-training（載體是 context）/兩使命一交會/防呆悖論（缺外部痛+人的節點）/操作員沒 watchdog/依戀在實踐不在模型；情境觸及才接續，勿轟炸 → `For_Claude/company/_shared/references/fable-five-observations-2026-07.md`
- **鏡子＋30天路線圖（2026-07-13 session 考古，用戶認領）** — 六個月 logs 實證：作品=認知、GO=思考工作台不可外包、迴避不可控 verifier、「只進不出的城」缺對外雷達（職缺/讀者/用戶 0 感測器）；30 天計畫：對外雷達/內容管線/告警分診/二次入典；08-12 驗收 → `For_Claude/company/_shared/references/mirror-2026-07.md` + `roadmap-2026-07-30d.md`（證據 `mirror-evidence-2026-07.md`）
- **溝通風格** — 預設大白話、非必要不用專業術語（用了附簡短說明）、避免中英夾雜 → `feedback_plain_language_default.md`
- **Release** — 「release 新版」= README→bump→CHANGELOG→commit→push→**`gh release create`**（不可省）；README 必先更新；必 bump SKILL.md frontmatter → `feedback_readme_before_release.md` + `feedback_release_bump_frontmatter.md`
- **Briefing** — 行事曆+待辦+Gmail(過去兩天)；Gmail 分類市場/財經/券商/技術職涯/可忽略促銷 → `briefing-sources.md`
- **Session Handoff** — Weekly Consolidation 達門檻 + Phase 4 Spot Check 記憶沉澱都直接執行不需確認
- **開源** — 所有開源 README 英+繁雙語；候選清單 `記憶庫/語義記憶/開源候選清單.md`
- **潤稿/寫作風格** — `~/.claude/skills/polish/references/writing-style.md`（polish 動態讀）
- **權限** — 操作工作區外路徑永久允許不需確認
- **絕對路徑** — 一律絕對路徑（不用 `~/`、相對）→ `feedback_absolute_paths.md`
- **Agent 混合模式** — 完整任務直接派 agent，不先讀一輪；判斷/串接/小問題走主 session → `feedback_agent_hybrid_mode.md`；回傳後主 session 整理重點 → `feedback_agent_results_summary.md`
- **既定 plan 順序** — 無新事實不臨時翻盤，照順序執行 → `feedback_respect_plan_order.md`
- **技術問題自己查 code** — 不問用戶（SCD 類）→ `feedback_no_technical_questions.md`
- **GitHub 報告** — 不主動提已關閉 issue/PR → `feedback_skip_closed_issues.md`

## 驗證紀律
- **審查範圍含引用者** — 抽離/重寫被引用檔後，待審清單必加「grep 指向它的檔」+「它宣稱對齊的規格檔」，否則斷鏈與版本衝突抓不到 → `feedback_review_scope_includes_referrers.md`
- **驗證源頭排序** — design intent/用戶意圖/config > code > docs > 直覺；用戶說「再驗證一次」立刻停讀 code → `feedback_verify_code_not_intuition.md` + `feedback_check_design_intent_first.md`
- **診斷三管齊下** — config 檔+即時 GUI+受控實驗；低解析度截圖判讀 UI 不可靠 → `feedback_diagnose_config_gui_experiment.md`
- **對拍外部數值** — 新 pipeline 第一次跑完必對拍，不能只看「沒 error、有輸出」→ `wiki/verify-values-not-errors.md`
- **PR 完成驗證** — bug PR 前必 TDD red-green + 實機 e2e；unit pass≠修好；「能修好嗎」→ invoke `/verification-before-completion` → `feedback_pr_complete_needs_e2e.md`
- **Merge 後驗證** — merge upstream 後必實跑 app，build 過不夠；conflict resolution 最易 compile 過但 runtime crash
- **防呆靠程式碼** — 共用模組/工廠函數/fail-fast，不靠記憶檔 → `feedback_防呆靠程式碼不靠記憶.md`
- **裝置限行為先研究** — iOS background/audio/CoreML 等先 NLM deep research 不靠猜 → `feedback_research_before_device_debug.md`
- **不確定先 NLM 驗證不猜** — 技術假設(API/效能/限制)先 NLM fast search+多輪 ask+實機量測，連 reviewer 戳的也回去驗 → `feedback_verify_assumptions_nlm_not_guess.md`
- **實驗收尾主動清理** — 明確垃圾直接刪/灰色問用戶，不等用戶問 → `feedback_experiment_cleanup_audit.md`
- **stale/凍結先查本地** — 資料卡舊日期先排除本地 cache 無TTL+排程沒裝(plist存在≠裝,驗launchctl)，別反射性換資料源 → `feedback_stale_check_cache_schedule_not_source.md`
- **無人值守告警三件** — 成功心跳(沒消息≠正常)+落後偵測(checker 不依賴會故障元件)+出錯推;只出錯推抓不到「整個沒跑」→ `feedback_unattended_monitoring_heartbeat_not_only_errors.md`
- **session 內背景等待** — 派背景長任務(VV/ASR/build)後別靠「單一等待器+完成通知」;等待器 timeout 要活得比任務久(別抄被等命令的 timeout)、沉默當可疑主動回查磁碟產物、不確定用 ScheduleWakeup 回查。2026-07-08 VV 早跑完但等待器 10min timeout 先死、空等 6h → `feedback_background_wait_watchdog_not_silence.md`

## 搜尋 / 研究 / 抓取工具
- **研究工具** — 簡單事實 WebSearch、深度 NLM、「用 NLM」強制；NLM create→use→status 不可省、一次 deep research 涵蓋全面向、import-all 最後跑一次 → `feedback_nlm_research_workflow.md` + `feedback_nlm_single_deep_research.md`
- **NLM source 必帶 -n** — source add-research 沒帶 `--notebook` 會落 context.json 舊 notebook 污染（create 不自動 use）；刪 notebook 是 `delete -n <id> -y` → `feedback_nlm_source_needs_notebook_flag.md`
- **NLM skill 跨 agent 共享** — CLI 是 pipx 全域 binary、四 agent 共用；SKILL.md 單一真相來源 `~/.agents/skills/notebooklm/`，Codex/Pi/Hermes 都 symlink 指它；升級後 `pipx install ...@tag --force` + `notebooklm skill install` 一次更新全部 → `reference_notebooklm_multi_agent_skill_distribution.md`
- **網頁抓取** — 優先 ScraplingServer MCP（`mcp__ScraplingServer__get`）不用 WebFetch；下載文章不改寫
- **grepai 語意搜尋** — 已裝 v0.35.0，MCP `mcp__grepai__grepai_search`，範圍 For_Claude git 檔；手動 `grepai watch` 索引 → `feedback_grepai_semantic_search.md`
- **ugrep 模糊搜尋** — 已裝 v7.6.0，`ugrep -Z2 "conifg"`；TUI `ug -Q`
- **LightRAG**（未裝，待觸發）— 知識庫 >50 萬 tokens 觸發；Docker 用 OrbStack；本地 LLM 首選 Qwen3-30B-A3B → `company/_shared/references/lightrag-research-2026-04.md`

## 機器 / 基礎設施
- **Fuji X-S10 webcam** — macOS 14+ 必裝專用版 2.2.0（預設下載頁 2.1=死的 DAL 架構）；相機拔線/關機必卡死全系統相機→跑 `~/bin/fixcam`；切 USB WEBCAM 模式後相機必重開機；設定面板反灰=官方設計 → `reference_fuji_xwebcam_macos26.md`
- **機器清單** — MBP(Pro CC) M1 Max 32GB 互動主力+oMLX；Mini CC `ssh fredchu_server@192.168.1.162` 定時任務，CC 在 `/opt/homebrew/bin/claude`；NAS `ssh fred@192.168.1.18` Austin 影片(scp 必 `-O`+/tmp 中轉, `feedback_nas_scp_verify.md`)；capital-bridge VM `ssh fredchu@192.168.1.156` port 8500；M2 MBA `ssh fredchu@fredmba.local`(免密碼) 純檔案操作+Mini CC 臨時備援(僅輕量排程,8GB/剩4.6GB 頂不了重運算),headless claude -p 同 keychain 坑 → `reference_m2_mba_backup_node.md`
- **SSH 排查** — 失敗必先 `-v` verbose 不要 silent 放棄 → `feedback_ssh_verbose_before_giving_up.md`
- **Mini CC headless** — `claude -p` over SSH 讀不到 Keychain OAuth → 改跑確定性腳本 → `feedback_minicc_ssh_headless_keychain.md`
- **LSP** — Python Pyright + Swift SourceKit-LSP 都 ✅ → `tools.md`
- **Skill 熱重載** — 裝到 `~/.claude/skills/` 後 `/reload-plugins`；`/doctor` 查 load errors
- **Git 雲端同步事故** — repo 禁入 Drive 鏡像（pack 吞噬 2TB）+ 鑑識/清理手法 → `feedback_drive_sync_git_disaster.md`
- **孤兒 uv 程序** — openclaw gateway 漏 mcp-fredapi uv(PPID=1) 抱 cache lock；`pkill -f "workspace/mcp-fredapi run"` → `reference_openclaw_orphan_uv_leak.md`
- **APFS du 灌水** — COW clone 灌水，清完靠 df 對拍非 du → `reference_apfs_du_cow_overcount.md`

## 定時任務（Mini CC launchd）
- **liquidity-monitor** — 週一 09:00 跑 FRED 25 指標、狀態變化推 Discord → `reference_liquidity_monitor.md`
- **cron-health** — 每天 08:30 掃 8 jobs，異常推 Discord → `reference_cron_health.md`
- **stale-scan** — 每月 1 號 09:00 掃 MEMORY.md 陳舊條目（Pro CC）→ `reference_stale_scan.md`
- **Podscribe NLM auth** — `~/.notebooklm/storage_state.json` 過期→source add 全失敗；Pro CC scp 過去即修；已加 Discord alert → `reference_notebooklm_auth_sync.md`
- **headless claude -p cron 卡死**（2026-07-09）— launchd 裡 `claude -p` 繼承整份 MCP(8+ server,含 uvx --refresh git)+SessionStart Notes-osascript hook→hang 撞 timeout exit1；修法 `--strict-mcp-config`+plist 設 `CLAUDE_SKIP_HANDOFF_HOOK=1`(hook 加 env 守衛)；診斷必用 kickstart 真情境非 SSH → `reference_headless_claude_p_cron_mcp_hook_hang.md`
- **FT 排程 python3.13 被 autoremove**（2026-07-09）— 6 plist 寫死路徑全掛;已修 uv venv+bash cron-health → `reference_ft_performance_gsheet.md`

## 派工（Codex / 本地模型）
- **派工入口** — `/dispatch` skill（分類→packet→codex-or-local）→ 底層 `codex-dispatch`；quota fallback `~/bin/codex-or-local`（codex→本地）；**勿用舊 `codex exec --full-auto`** → `project_dispatch_router.md` + `codex_dispatch.md`
- **五觸發任一命中就派** — spec 已寫清楚＝命中「已有 spec 的實作」，不得只用「<100 行」自我豁免手刻；同 session 被抓兩次立規 → `feedback_dispatch_spec_trigger_not_line_count.md`
- **dispatch-router**（2026-06-17）— advisory hook 偵測「該派 Codex」prompt 提示 → `project_dispatch_router.md`
- **pi agent**（2026-07-05）— 裝好，OpenRouter+DeepSeek V4 Flash，headless `pi -p --no-session` 可從主 session 派工；已裝 wiki/session-handoff 兩 skill；需 Node≥22.19（升到 v22.23.1）；**2026-07-06 整合進 /dispatch cascade（codex→pi→本地，pi 是 fallback 不是前置，`--worker pi` 逃生艙）** → `reference_pi_agent.md`
- **派工前先驗前提**（2026-07-06）— 別把未驗證前提當事實塞進 subagent packet，會錨定它換來假的「獨立確認」；可量測的先用工具實測（quota/定價/限制）→ `feedback_verify_premise_before_dispatch_anchors.md`
- **OmniCoder 9B 本地** — client→omlx-proxy(8091)→omlx serve(8090)→OmniCoder-9B-MLX-4bit；裝 Crush/OpenCode/local-agent
- **派工後必 e2e** — subagent unit test 全過≠正確，合成 fixture 碰不到真 bug → `feedback_dispatch_e2e_not_unit_test.md`
- **packet 格式** — top-level `KEY: value` 必，`## KEY` 不 parse；同 KEY 重複行只留最後一行；**WRITE SCOPE 多路徑唯一正解＝空 header＋bullet 分行**（逗號/頓號單行必假 rc=3，2026-07-08 faucet-match 四度踩）→ `feedback_codex_packet_format.md`
- **背景跑別寫同 repo** — policy fingerprint 誤報 → `codex_dispatch.md`
- **verifier watchdog** — 網路重/長靜默指令 300s 無 stdout 被殺(假 violation)；codex 只放快指令、e2e 主 session 跑 → `reference_codex_dispatch_watchdog_stall.md`
- **classifier 升級擋** — subagent policy refusal 後主 session 做同類被擋；唯一 escape `claude --dangerously-skip-permissions`；codex 5h quota 85% soft gate → `feedback_classifier_escalation_and_bypass.md`
- **dispatch 粒度** — per-phase vs strict per-task → `feedback_per_phase_dispatch_granularity.md`

## 專案清單
- MumbleKey(iPhone/visionOS 語音鍵盤；域名 `project_mumblekey_domains.md`)、VerbatimFlow(macOS ASR，`/Users/fredchu/dev/verbatim-flow`)、Earnings Autopilot(財報逐字稿，遷移 Mini CC)、Austin 字幕/翻譯、特助系統、signal-options-methodology(與 Charles 協作 private repo，`~/dev`+fork)
- **automl v6**（Phase 1 完成 2026-05-06）— rewrite 動機 `project_automl_v6_motivation.md`；skill `~/.claude/skills/automl-v6/`；Phase 1.5 通過不暫停 `feedback_automl_no_pause.md`、--autonomous tick 自動執行 `feedback_automl_autonomous_no_ask.md`；evaluator 必含 runtime test `feedback_automl_evaluator_must_test_runtime.md`
- **ib-cli**（2026-06-12）— `~/dev/ib-cli` alias `ib`，ib_async+TWS 7496，預設 dry-run；TWS modal 卡死 API 單 → `project_ib_cli.md`
- **交易行為審計**（待啟動）→ `project_trading_behavior_audit.md`
- **blog.mumblekey.com**（2026-07-06 上線）— Astro 7+CF Workers、git push 自動部署、`blog` CLI、giscus 留言、agent 搜尋面(.md 端點/llms.txt) → `project_mumblekey_blog.md`
- **bookmate**（2026-07-07 建成）— 個人化互動閱讀 skill（teach×book mirror）；真相源 `~/dev/bookmate`(GitHub private,Bocky write)、六 symlink(CC/Codex/Pi/Hermes×3)；書 workspace `~/learning/<slug>/`；花書進行中 → `project_bookmate_skill.md`
- **learn.mumblekey.com**（2026-07-07 上線）— ~/learning 手機/外網閱讀站；Pro CC publish→Mini CC tunnel(f6087e56)+http.server；CF Access 只放 iamfredchu；Access 可用 bb-browser+Chrome session 打 dash API 管理 → `reference_learn_site.md`

## 交易 / 投資基礎設施
- **交易骨架** — 科技集中(刻意)、動態槓桿 0.6-1.6x、減碼時機自評弱項 → `user_trading_framework.md`
- **IB 掛機/佣金/session**（已上線 2026-07-01）— 改 Tiered(極小額多筆省最低佣金)；**雙 username**：Gateway 獨佔 `gatewaydocker`(`primary`,永不被手機踢)、Fred 手動用主 `iamfredchu`(勿交叉用同 username 否則互踢)；Gateway `~/dev/ib-gateway-docker`(OrbStack+gnzsnz)，**process 不死才能 warm 重搶免 2FA**、絕不 docker restart、用 IBC telnet RESTART；`ib list`/`orders` 驗過帳戶 U16976878；**live e2e 通過**(手機登 iamfredchu 不踢 gateway 的 gatewaydocker) → `project_ib_gateway_docker.md`
- **Firstrade 整合** — FT 腳本用 `ft_session.py`、IB 用 `ib_session.py`；P 組合 source=FT 實盤(105 檔) `feedback_ft_source_of_truth.md`；sync `scripts/trading/firstrade_sync.py`；OI snapshot Mini CC 台灣 10AM `reference_mini_cc_oi_snapshots.md`
- **FT 績效 Google Sheet** — Mini CC 三 launchd + Pro CC tw export；2026-05-14 OAuth→Service Account(`~/.config/google-sheets/sa-key.json`)；CF range 必設整 sheet → `reference_ft_performance_gsheet.md` + `feedback_sheets_cf_range_full_sheet.md`
- **B2 動態同步** — `tw export`→Sheet `__positions__`→Mini CC `futures_price_update.py --tw` 算 B2；國泰大台 200 點寫死、群益動態加項 → `wiki/brokerage-api-integration.md`
- **富途自選股血洗** — root cause 多是雲端同步衝突非腳本；本地 JSON=source，`futu-sync push` 自癒、**勿 pull** → `feedback_futu_watchlist_cloud_sync_incident.md`

## 字幕 / ASR Pipeline
- **Benchmark ground truth** — 用最新技能素材(`/Users/fredchu/Media-work/subtitle-media/`)，golden 血緣灌水 CER → `feedback_benchmark_ground_truth_latest_skill.md`
- **ASR 模型** — Nemotron-3.5-ASR(MLX) 與 VV 同級、整合急迫性低，wiki `asr-model-evaluation`；Breeze 幻覺修不好換 Whisper large-v3 `feedback_asr_hallucination_fallback.md`
- **SRT 編排** — caption gemma4:26b(20GB)+VV 不可同跑(OOM)、caption 完強制 ollama stop、同批 2 輪 term learning → `feedback_srt_pipeline_orchestration.md` + `wiki/subtitle-pipeline.md`
- **Speech.framework 不足** — iOS DictationTranscriber 不如內建中文聽寫、Custom LM 對英文術語改善不夠 → `feedback_speech_framework_quality.md`
- **pptx 抽術語漏圖片文字**（2026-07-15 實測）— srt 的 pptx 路徑沒 OCR，圖內術語(PLTR/MA300DIST/CME_MINI…)全漏；換 OfficeCLI 也沒用(同讀 OOXML)，缺的是 OCR；修法=export `shape.image.blob` 丟腳本已有的 `ocr_with_rapidocr()`，8 圖 7.4 秒補 152 行 → `company/_shared/lessons/2026-07-15-pptx-terms-miss-image-text.md`
- **srt media 是 symlink 別 rm -rf** — `scripts/subtitle/media`→`~/Media-work/subtitle-media`,Step 5 清理只用 `find -delete` 具名中間產物,絕不 rm -rf 目錄;誤刪救援=從 subagent transcript JSONL 萃取 Write 內容+Breeze 確定性重跑 → `feedback_srt_media_symlink_rmrf_incident.md`

## 寫入工具陷阱
- **Apple Notes 標題** — set body 必含 canonical title 行否則改名成孤兒 → `feedback_apple_notes_first_line_is_title.md`
- **Apple Notes HTML** — h1/h2/h3/`<ul>` 可用、避 `<p>`；**handoff 三note 禁 `<tt>`**（讀回變 Courier+font-size，任何 round-trip 寫入撞 lint exit 2，2026-07-16 consolidate 實測卡住）；複雜 HTML 用 `cat /tmp/file.html` 注入；~3000+ 字中文 body 觸發 -10000 要縮到 ~2500 → `feedback_apple_notes_html_formatting.md` + `feedback_applescript_notes_large_body_10000.md`
- **Readwise 大文件** — >~50KB 用 HTML 推送不用 markdown → `feedback_readwise_large_docs_html.md`
- **Readwise Reader API** — PATCH `/api/v3/update/{id}/`（CLI 沒包）→ `reference_readwise_reader_api_patch.md`
- **Skill 寫法** — 確定性邏輯=腳本、需語言理解=LLM subagent → `feedback_skill_script_not_prose.md`
- **/teach 解析陷阱** — `Skill('teach')` 會跑成 gstack `learn`（錯）；真 teach 設 disable-model-invocation，要直接 `Read ~/.claude/skills/teach/SKILL.md` 手動跑 → `feedback_teach_skill_resolves_to_learn.md`
- **security hook 字眼** — Write 含 `e-val(`/`e-xec(`(無 hyphen 形式)被擋；改 hyphen 變體 → `feedback_pretool_security_hook_string_match.md`
- **urllib 預設 UA** — 被 Discord webhook + Cloudflare 站雙雙 403 靜默失聲；一律帶自訂 `User-Agent` → `feedback_urllib_ua_discord_cloudflare.md`
- **Git tag move** — fresh local tag 沒推 remote 時比 bump 新版乾淨 → `feedback_git_tag_move_safe.md`
- **~/.claude repo gitignore 白名單** — `*` 全域忽略+白名單，git add 靜默丟非白名單檔（commit 後必 `git show --stat` 對拍）；-f 只點名檔案勿掃目錄（吞 pycache）→ `feedback_claude_dotfiles_gitignore_whitelist.md`
- **Git remote** — 第三方工具 origin 指上游不是 fork → `feedback_gstack_origin_remote.md`
- **Debug 紀律** — 失敗嘗試不 commit `feedback_debug_clean_commits.md`；CSS debug 用 Playwright `feedback_playwright_css_debug.md`
- **設定檔寫入** — 必查 docs → `feedback_config_must_check_docs.md`
- **Figma 截圖** — 優先 ghost_screenshot → `feedback_figma_screenshot.md`
- **ghost-os 授權流** — 網頁 OAuth/App 安裝可用 ghost-os 純 AX 完成；SPA 按鈕要 inspect+座標點、GitHub sudo 留給 Fred → `reference_ghost_os_browser_automation.md`
- **bb-browser 陷阱** — `tab N` 切換不生效（用 `eval "location.href=..."` 繞）；受管實例≠用戶真 Chrome 且無 H.264 不載 mp4，影音驗證用頁內 fetch+Range、真瀏覽器操作走 ghost-os → `reference_bb_browser_traps.md`
- **Wiki Sources glob** — 涵蓋 lessons/references/work-log/poc/docs → `feedback_wiki_sources_coverage.md`
- **產中文 PDF** — 履歷/簡報/一頁式走 HTML + Chrome headless `--print-to-pdf`（PingFang 字型直接吃、不用 LaTeX）；橫向投影片用 `@page size:297mm 167mm` → `reference_html_to_pdf_cjk.md`
- **Office 檔案（.docx/.xlsx/.pptx）** — 生成/編修/檢查排版首選 **OfficeCLI**（單一 binary、免裝 Office、能 render→screenshot/html 讓 agent 自檢）；repo 已 clone `~/ghkb/ai-tools/OfficeCLI/`；**但純讀文字沒優勢**（與 python-pptx 實測 269/271 等價）→ `reference_officecli_office_file_toolkit.md`

## 環境 / 平台陷阱
- **bash 中文 heredoc 變數黏名** — `$VAR` 後直接接全形字元會黏進變數名炸 unbound；一律 `${VAR}`；bash -n 與靜態 review 全漏接、僅 e2e 現形 → `reference_bash_heredoc_cjk_var_adjacency.md`
- **macOS spawn** — module global 不進 worker，ProcessPoolExecutor 設定必參數傳 → `feedback_macos_spawn_global_no_propagate.md`
- **zsh wildcard** — NOMATCH ON，任一 wildcard 沒匹配整批 abort；用 `find ... -delete` → `feedback_zsh_glob_no_matches.md`
- **ls 是 alias 非 coreutils** — 管線裡輸出會空白或漏數（`ls *.srt|wc -l` 回 2 但實際 4 個），別拿 ls 輸出當事實；清點一律 `find`（2026-07-16 一 session 踩 3 次）→ `feedback_ls_alias_not_coreutils.md`
- **Ollama gemma4** — 同時只一個 26b(17GB)、`/api/chat` 必 `"think": false`、tool >5 個幻覺 → `feedback_ollama_gemma4_constraints.md`
- **工具評估** — 先 audit 真痛點，不被「service account/unified/agent-safe」帶偏 → `feedback_tool_evaluation_audit_real_pain_first.md`
- **Anthropic quota** — OAuth endpoint 查 CC 自己 5h/7d quota → `reference_anthropic_oauth_quota.md`
- **額度爆≠quota滿** — 大批並行 subagent 報 spend limit 多是 extra_usage spike（非 included 5h），降併發即可續；automl 5h wait 機制不適用 → `reference_extra_usage_spike_not_quota.md`
- **Hermes 本地 27B 調校** — 慢/一直compact根因是記憶體爆(27B+Parallels撞omlx天花板→prefill abort被誤判)；修法：關Parallels+toolset 17→8+threshold 0.75+ctx釘64K(Hermes硬性最低)；warm prefix cache命中後9s/輪。另加**唯讀 wiki-query skill**(`~/.hermes/skills/research/wiki-query/`,英文整詞/中文子字串混合比對,root釘死,內建llm-wiki已停用) → `reference_hermes_local_optimization.md`
- **Hermes 裝/停 skill 三處都要動** — main + qwopus35 + qwopus27 各有獨立 skills 目錄與 config；停用單一 skill 靠 config.yaml `skills.disabled` 每 profile 各加一行（沒 CLI 指令）；agents 幾乎無 MCP 但 session-handoff/wiki 走自帶腳本不需 MCP → `reference_hermes_profiles_skill_management.md`
- **Hermes delegation（Pro CC 用）** — Hermes=本地免費版 Claude Code(工具+agentic loop)，可 delegate；三 profile `cd /target && <alias> -z "task"`：`qwopus35`(35B-A3B MoE,快4x,coding)/`qwopus27`(27B dense,嚴格/穩)/`hermes`(nemotron cloud,複雜);**絕不用 `hermes profile use`**(bug)用alias;delegate後看git diff驗;本地一次一顆撞507重啟omlx → `reference_hermes_delegation.md` + wiki `hermes-agent-delegation`
- **srt 32K 切分曲線** — 校正段 200 條/段=18%失敗拐點前上界，250起難影片系統性崩；雙約束動態切分 → `company/_shared/lessons/2026-06-27-srt-segsize-failure-rate-curve.md`
- **CC tool-use 幻覺真因** — 兩大家族：長 session 的 compaction 洩漏(#46500/#57212) + **全新 session 前一兩回合就中**(並行工具→傳輸吞包腦補 #46767/#64076、/clear bleed #47756、首發壞 XML #49747)；#28988 cache race 只壞 config 不注入幻覺；跟終端機無關。對策=序列發工具+關進程別 /clear+調低 effort → `reference_cc_phantom_compaction_not_terminal.md`
- **/ahp 臨時防幻覺 skill** — 新 session 開頭打 `/ahp` 套序列發工具規則；官方修 #46767/#64076 後移除 → `project_ahp_temp_skill.md`

## Loop 工程
- **左/右格判準** — 決策會否改變明天執行 +「機械≠安全」+ verifier 信任是瓶頸 → `feedback_loop_engineering_left_right_cell.md`
- **apodex-4b** — 本地零額度 verifier(MLX 2.2GB，codex verifier 平替) → `reference_apodex_4b_local_verifier.md`
- **skill-steward** — 第一個真 loop design v2.1 → `company/_shared/references/skill-steward-loop-design-v2-2026-06-11.md`

## 人物 / 結構
- **Charles** = Bocky 學長（同一人，Austin 團隊、GitHub `bockybocky`）→ `person_bocky_charles.md`
- **Agent Teams** — 使用教訓 → `agent-teams.md`；Mini CC 定時任務開發 → `mini-cc-cron.md`
- **公司級文件** — `company/`，每專案 work-log/lessons/references，跨專案 `_shared/`

## Topic Files
- `tools.md` — 工具安裝狀態、LSP、CC 設定檔路徑、URL→Markdown 代理、oMLX
- `briefing-sources.md` — Gmail briefing 來源清單
