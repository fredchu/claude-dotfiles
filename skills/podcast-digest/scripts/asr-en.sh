#!/bin/bash
set -euo pipefail

# English ASR via FluidAudio Parakeet TDT v3
# Usage: asr-en.sh <audio.wav>
# Output: JSON to stdout (same format as asr-zh.swift)

AUDIO_PATH="${1:-}"
if [[ -z "$AUDIO_PATH" ]]; then
  echo "Usage: asr-en.sh <audio.wav>" >&2
  exit 1
fi

if [[ ! -f "$AUDIO_PATH" ]]; then
  echo "ERROR: File not found: $AUDIO_PATH" >&2
  exit 1
fi

FLUIDAUDIO_DIR="$HOME/ghkb/interested/FluidAudio"
WORK_DIR="/tmp/podscribe-work"
mkdir -p "$WORK_DIR"
RAW_JSON="$WORK_DIR/asr-en-raw.json"

echo "Running Parakeet TDT v3 ASR..." >&2
cd "$FLUIDAUDIO_DIR" && swift run -c release fluidaudiocli transcribe "$AUDIO_PATH" --output-json "$RAW_JSON" >&2

# Convert FluidAudio wordTimings JSON to segments format matching asr-zh.swift output
python3 -c "
import json, sys

with open('$RAW_JSON') as f:
    data = json.load(f)

words = data.get('wordTimings', [])
if not words:
    print(json.dumps({'segments': [], 'processing_time_seconds': data.get('processingTimeSeconds', 0), 'rtf': data.get('rtfx', 0), 'duration_seconds': data.get('durationSeconds', 0)}))
    sys.exit(0)

# Group words into sentence-like segments by pauses (>0.8s gap)
segments = []
current = {'start': words[0]['startTime'], 'end': words[0]['endTime'], 'text': words[0]['word']}

for w in words[1:]:
    gap = w['startTime'] - current['end']
    if gap > 0.8 or (current['end'] - current['start']) > 30:
        segments.append({
            'start': round(current['start'], 2),
            'end': round(current['end'], 2),
            'text': current['text'].strip()
        })
        current = {'start': w['startTime'], 'end': w['endTime'], 'text': w['word']}
    else:
        current['end'] = w['endTime']
        current['text'] += ' ' + w['word']

# Last segment
segments.append({
    'start': round(current['start'], 2),
    'end': round(current['end'], 2),
    'text': current['text'].strip()
})

output = {
    'segments': segments,
    'processing_time_seconds': data.get('processingTimeSeconds', 0),
    'rtf': data.get('rtfx', 0),
    'duration_seconds': data.get('durationSeconds', 0)
}

print(json.dumps(output, ensure_ascii=False, indent=2))
"
