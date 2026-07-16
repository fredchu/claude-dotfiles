---
name: bb-browser-traps
description: bb-browser CLI 兩個實測陷阱——tab 切換不生效（用 eval 導航繞過）、受管實例無 H.264 且與用戶真 Chrome 是兩個實例
metadata: 
  node_type: memory
  type: reference
  originSessionId: b41a1d49-ee6a-477c-8461-1c6afd9de29a
---

bb-browser CLI（2026-07-16 實測，MM demo site 驗證場景）：

1. **`bb-browser tab <n>` 切換不生效**：指令會印出目標 URL 但 `tab list` 的當前分頁（`*`）不變，後續 `eval` 仍打在舊分頁。繞法：不切分頁，直接讓當前分頁自己導航——`bb-browser eval "location.href='<url>'"`，sleep 1-2 秒後再 eval 操作。
2. **受管實例 ≠ 用戶的 Chrome**：bb-browser 起的是自己的 Chrome 實例（`tab list` 只見 about:blank 即是此況），看不到用戶開著的視窗與分頁。且該實例**不載 mp4**（疑無 H.264 的 headless 核心）——`<video>` 永遠 readyState 0、網路層連請求都不發。影音驗證改用頁內 `fetch` 帶 Range header（網路層等價），或要操作用戶真 Chrome 時走 ghost-os（AX 座標點擊，見 [[reference_ghost_os_browser_automation]]）。

適用：需要「用戶登入態/真實視窗」的操作先想 ghost-os；bb-browser 適合乾淨的 headless 驗證與 fetch。
