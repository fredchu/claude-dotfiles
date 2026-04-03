#!/usr/bin/env python3
"""Convert podcast JSON chunks to/from numbered plain text for LLM processing.

Separates JSON structure handling from LLM tasks (correction/translation),
so Gemma only processes plain text and never needs to output valid JSON.

Usage:
    # Extract: JSON → numbered text
    python3 chunk_text.py extract --input chunk_0.json --output chunk_0.txt

    # Merge correction: put corrected text back into JSON
    python3 chunk_text.py merge --input chunk_0.json --text chunk_0_corrected.txt --output chunk_0_corrected.json

    # Merge translation: add text_zh field from translated text
    python3 chunk_text.py merge-translation --input chunk_0.json --text chunk_0_translated.txt --output chunk_0_translated.json
"""

import argparse
import json
import re
import sys
from pathlib import Path


def extract(input_path, output_path):
    """Extract text fields from JSON segments as numbered lines."""
    data = json.load(open(input_path))
    if isinstance(data, dict):
        data = data.get("segments", [])

    lines = []
    for i, seg in enumerate(data):
        lines.append(f"{i+1}. {seg['text']}")

    Path(output_path).write_text("\n\n".join(lines))
    print(f"Extracted {len(lines)} segments", file=sys.stderr)


def _parse_numbered(text):
    """Parse numbered output back into a list of strings."""
    parts = re.split(r"\n\n(?=\d+\.)", text.strip())
    result = []
    for part in parts:
        cleaned = re.sub(r"^\d+\.\s*", "", part).strip()
        result.append(cleaned)
    return result


def merge(input_path, text_path, output_path, strict=False):
    """Replace text fields in JSON with corrected text."""
    data = json.load(open(input_path))
    segments = data if isinstance(data, list) else data.get("segments", [])

    corrected = _parse_numbered(Path(text_path).read_text())

    if len(corrected) != len(segments):
        msg = f"segment count mismatch: {len(segments)} segments vs {len(corrected)} lines"
        if strict:
            print(f"ERROR: {msg}", file=sys.stderr)
            sys.exit(1)
        print(f"WARNING: {msg}", file=sys.stderr)

    for i, seg in enumerate(segments):
        if i < len(corrected):
            seg["text"] = corrected[i]

    with open(output_path, "w") as f:
        json.dump(segments if isinstance(data, list) else data, f, ensure_ascii=False, indent=2)

    print(f"Merged {min(len(corrected), len(segments))} segments", file=sys.stderr)


def merge_translation(input_path, text_path, output_path, strict=False):
    """Add text_zh field to JSON from translated text."""
    data = json.load(open(input_path))
    segments = data if isinstance(data, list) else data.get("segments", [])

    translated = _parse_numbered(Path(text_path).read_text())

    if len(translated) != len(segments):
        msg = f"segment count mismatch: {len(segments)} segments vs {len(translated)} lines"
        if strict:
            print(f"ERROR: {msg}", file=sys.stderr)
            sys.exit(1)
        print(f"WARNING: {msg}", file=sys.stderr)

    for i, seg in enumerate(segments):
        if i < len(translated):
            seg["text_zh"] = translated[i]

    with open(output_path, "w") as f:
        json.dump(segments if isinstance(data, list) else data, f, ensure_ascii=False, indent=2)

    print(f"Translated {min(len(translated), len(segments))} segments", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="JSON ↔ numbered text converter")
    sub = parser.add_subparsers(dest="command", required=True)

    p_extract = sub.add_parser("extract", help="JSON → numbered text")
    p_extract.add_argument("--input", required=True)
    p_extract.add_argument("--output", required=True)

    p_merge = sub.add_parser("merge", help="Put corrected text back into JSON")
    p_merge.add_argument("--input", required=True, help="Original JSON")
    p_merge.add_argument("--text", required=True, help="Corrected text file")
    p_merge.add_argument("--output", required=True)
    p_merge.add_argument("--strict", action="store_true", help="Exit with error if segment count mismatches")

    p_trans = sub.add_parser("merge-translation", help="Add text_zh from translated text")
    p_trans.add_argument("--input", required=True, help="Original JSON")
    p_trans.add_argument("--text", required=True, help="Translated text file")
    p_trans.add_argument("--output", required=True)
    p_trans.add_argument("--strict", action="store_true", help="Exit with error if segment count mismatches")

    args = parser.parse_args()

    if args.command == "extract":
        extract(args.input, args.output)
    elif args.command == "merge":
        merge(args.input, args.text, args.output, strict=args.strict)
    elif args.command == "merge-translation":
        merge_translation(args.input, args.text, args.output, strict=args.strict)


if __name__ == "__main__":
    main()
