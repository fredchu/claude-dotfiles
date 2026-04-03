#!/bin/bash
set -euo pipefail

WORK_DIR="/tmp/podscribe-work"
mkdir -p "$WORK_DIR"

INPUT="${1:-}"

if [[ -z "$INPUT" ]]; then
  echo "Usage: download.sh <URL or file path>" >&2
  exit 1
fi

WAV_OUT="$WORK_DIR/audio.wav"

convert_to_wav() {
  local src="$1"
  echo "Converting to 16kHz mono WAV..." >&2
  ffmpeg -i "$src" -ar 16000 -ac 1 -y "$WAV_OUT" >&2
}

# Case 1: YouTube URL
if [[ "$INPUT" == *"youtube.com"* || "$INPUT" == *"youtu.be"* ]]; then
  echo "Detected YouTube URL, downloading..." >&2
  yt-dlp -x --audio-format wav -o "$WORK_DIR/audio.%(ext)s" "$INPUT" >&2
  RAW="$WORK_DIR/audio.wav"
  if [[ ! -f "$RAW" ]]; then
    # yt-dlp may produce a different extension before conversion
    RAW=$(ls "$WORK_DIR"/audio.* 2>/dev/null | head -1)
  fi
  convert_to_wav "$RAW"

# Case 2: Pocket Casts URL
elif [[ "$INPUT" == *"pca.st"* ]]; then
  echo "Detected Pocket Casts URL, fetching page..." >&2
  HTML=$(curl -sL "$INPUT")
  MP3_URL=$(echo "$HTML" | grep -oP 'href="\K[^"]+(?=" download=)' | head -1)
  if [[ -z "$MP3_URL" ]]; then
    echo "Failed to extract mp3 URL from Pocket Casts page" >&2
    exit 1
  fi
  echo "Found audio URL: $MP3_URL" >&2
  RAW="$WORK_DIR/raw_audio.mp3"
  curl -sL -o "$RAW" "$MP3_URL" >&2
  convert_to_wav "$RAW"

# Case 3: Direct audio URL (mp3/wav/m4a)
elif [[ "$INPUT" == http* ]]; then
  echo "Detected direct audio URL, downloading..." >&2
  EXT="${INPUT##*.}"
  EXT="${EXT%%\?*}"  # strip query string if any
  RAW="$WORK_DIR/raw_audio.$EXT"
  curl -sL -o "$RAW" "$INPUT" >&2
  convert_to_wav "$RAW"

# Case 4: Local file
else
  if [[ ! -f "$INPUT" ]]; then
    echo "File not found: $INPUT" >&2
    exit 1
  fi
  echo "Using local file: $INPUT" >&2
  convert_to_wav "$INPUT"
fi

echo "$WAV_OUT"
