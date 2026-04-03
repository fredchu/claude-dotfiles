#!/usr/bin/env bash
# Test harness for asr-zh.swift
# RED phase: defines what the output must satisfy BEFORE implementation exists
#
# Usage:
#   ./test-asr-zh.sh <audio.wav>
#   Exits 0 if all assertions pass, non-zero otherwise.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ASR_SCRIPT="$SCRIPT_DIR/asr-zh.swift"
AUDIO_FILE="${1:-}"

PASS=0
FAIL=0

assert_eq() {
    local label="$1" expected="$2" actual="$3"
    if [ "$expected" = "$actual" ]; then
        echo "  PASS: $label"
        ((PASS++))
    else
        echo "  FAIL: $label — expected '$expected', got '$actual'"
        ((FAIL++))
    fi
}

assert_nonempty() {
    local label="$1" value="$2"
    if [ -n "$value" ]; then
        echo "  PASS: $label"
        ((PASS++))
    else
        echo "  FAIL: $label — value is empty"
        ((FAIL++))
    fi
}

assert_gt() {
    local label="$1" threshold="$2" value="$3"
    if awk "BEGIN{exit !($value > $threshold)}"; then
        echo "  PASS: $label ($value > $threshold)"
        ((PASS++))
    else
        echo "  FAIL: $label — expected > $threshold, got $value"
        ((FAIL++))
    fi
}

if [ -z "$AUDIO_FILE" ]; then
    echo "Usage: $0 <audio.wav>"
    exit 1
fi

if [ ! -f "$AUDIO_FILE" ]; then
    echo "Audio file not found: $AUDIO_FILE"
    exit 1
fi

echo "=== asr-zh.swift test harness ==="
echo "Audio: $AUDIO_FILE"
echo ""

# ── Test 1: script exits 0 on valid input ──────────────────────────────────
echo "[T1] exit code on valid input"
set +e
OUTPUT=$(xcrun --sdk macosx swift "$ASR_SCRIPT" "$AUDIO_FILE" 2>/tmp/asr-zh-stderr.txt)
EXIT_CODE=$?
set -e
assert_eq "exit code is 0" "0" "$EXIT_CODE"

# ── Test 2: stdout is valid JSON ────────────────────────────────────────────
echo "[T2] stdout is valid JSON"
if echo "$OUTPUT" | python3 -m json.tool > /dev/null 2>&1; then
    echo "  PASS: valid JSON"
    ((PASS++))
else
    echo "  FAIL: not valid JSON"
    echo "  stdout was: $OUTPUT"
    ((FAIL++))
fi

# ── Test 3: top-level keys exist ────────────────────────────────────────────
echo "[T3] required top-level keys"
KEYS=$(echo "$OUTPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(' '.join(sorted(d.keys())))" 2>/dev/null || echo "")
assert_eq "keys: duration_seconds processing_time_seconds rtf segments" \
    "duration_seconds processing_time_seconds rtf segments" "$KEYS"

# ── Test 4: segments is an array ────────────────────────────────────────────
echo "[T4] segments is a non-empty array"
SEG_COUNT=$(echo "$OUTPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['segments']))" 2>/dev/null || echo "0")
assert_gt "segment count > 0" "0" "$SEG_COUNT"

# ── Test 5: each segment has start / end / text ──────────────────────────────
echo "[T5] each segment has start, end, text"
BAD_SEGS=$(echo "$OUTPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
bad = 0
for i, s in enumerate(d['segments']):
    if 'start' not in s or 'end' not in s or 'text' not in s:
        bad += 1
print(bad)
" 2>/dev/null || echo "1")
assert_eq "no malformed segments" "0" "$BAD_SEGS"

# ── Test 6: numeric fields are positive floats ───────────────────────────────
echo "[T6] numeric fields > 0"
PROC=$(echo "$OUTPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['processing_time_seconds'])" 2>/dev/null || echo "0")
RTF=$(echo  "$OUTPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['rtf'])" 2>/dev/null || echo "0")
DUR=$(echo  "$OUTPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['duration_seconds'])" 2>/dev/null || echo "0")
assert_gt "processing_time_seconds > 0" "0" "$PROC"
assert_gt "rtf > 0" "0" "$RTF"
assert_gt "duration_seconds > 0" "0" "$DUR"

# ── Test 7: stderr is empty (no stray logs to stdout leaking) ────────────────
echo "[T7] stdout contains only JSON (no log lines mixed in)"
LINE_COUNT=$(echo "$OUTPUT" | wc -l | tr -d ' ')
# Valid JSON can be multi-line; just ensure first non-whitespace char is '{'
FIRST_CHAR=$(echo "$OUTPUT" | python3 -c "import sys; s=sys.stdin.read().strip(); print(s[0] if s else '')" 2>/dev/null || echo "")
assert_eq "first char is '{'" "{" "$FIRST_CHAR"

# ── Test 8: --locale flag accepted ───────────────────────────────────────────
echo "[T8] --locale flag accepted"
set +e
OUT2=$(xcrun --sdk macosx swift "$ASR_SCRIPT" --locale zh-TW "$AUDIO_FILE" 2>/tmp/asr-zh-stderr2.txt)
EC2=$?
set -e
assert_eq "--locale flag: exit code 0" "0" "$EC2"

# ── Test 9: missing file → non-zero exit + stderr message ───────────────────
echo "[T9] missing audio file exits non-zero"
set +e
xcrun --sdk macosx swift "$ASR_SCRIPT" /nonexistent/file.wav > /dev/null 2>/tmp/asr-zh-err-missing.txt
EC3=$?
set -e
assert_gt "exit code > 0 for missing file" "0" "$EC3"
ERRMSG=$(cat /tmp/asr-zh-err-missing.txt)
assert_nonempty "stderr message for missing file" "$ERRMSG"

# ── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -eq 0 ]; then
    echo "ALL TESTS PASSED"
    exit 0
else
    echo "TESTS FAILED"
    exit 1
fi
