#!/bin/bash
# dispatch-router advisory hook (UserPromptSubmit).
# 只在 classifier 判 dispatch_recommended 時注入一行提示；其餘安靜。
# Fail-safe：任何錯誤/逾時一律靜默 exit 0，絕不阻擋使用者 prompt 送出。
set +e

ROUTER="/Users/fredchu/dev/claude-dispatch-router/scripts/dispatch_router.py"
[ -f "$ROUTER" ] || exit 0

input="$(cat)"
[ -n "$input" ] || exit 0

# 3s 上限；timeout binary 不一定在 PATH（本機在 /opt/homebrew/bin）
TIMEOUT_BIN="$(command -v timeout || command -v gtimeout)"
if [ -n "$TIMEOUT_BIN" ]; then
  out="$(printf '%s' "$input" | "$TIMEOUT_BIN" 3 python3 "$ROUTER" 2>/dev/null)"
  rc=$?
else
  out="$(printf '%s' "$input" | python3 "$ROUTER" 2>/dev/null)"
  rc=$?
fi
# spec §3.2 fail-safe：router 非 0 exit（含 timeout 124）一律靜默，不解析 stdout
[ "$rc" -eq 0 ] || exit 0
[ -n "$out" ] || exit 0

decision="$(printf '%s' "$out" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("decision",""))' 2>/dev/null)"
if [ "$decision" = "dispatch_recommended" ]; then
  reason="$(printf '%s' "$out" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("reason",""))' 2>/dev/null)"
  echo "⚠️ dispatch-router: 這個請求命中「預設派 Codex」觸發條件（${reason}）。動工前先自問是否走 /dispatch 或 codex-dispatch。"
fi
exit 0
