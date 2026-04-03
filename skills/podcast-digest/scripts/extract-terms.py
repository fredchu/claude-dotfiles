#!/usr/bin/env python3
"""Extract terminology from a podcast episode via NotebookLM.

Uploads audio to NLM, asks for proper nouns/technical terms,
cleans output into a term list for injection into correction/translation prompts.

Usage:
    python3 extract-terms.py --audio episode.mp3 --show "Show Name" \
        --output /tmp/podscribe-work/nlm-terms.txt
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

NLM_BIN = os.environ.get("NLM_BIN", "notebooklm")
STATE_PATH = "/Users/fredchu/Documents/For_Claude/company/podscribe/nlm-state.json"

TERM_PROMPT_ZH = """列出這集播客中出現的所有專有名詞、人名、技術術語、概念名稱。
格式：每行一個，用 | 分隔術語和簡短說明。
例如：習得性無助 | 心理學概念，指反覆失敗後學會放棄
只列出術語，不要加前言或結語。"""

TERM_PROMPT_EN = """List all proper nouns, person names, technical terms, and key concepts in this podcast episode.
Format: one per line, separated by | with a brief description.
Example: hypertrophy | increase in muscle size through training
Only list terms, no preamble or conclusion."""


def run_cmd(cmd, timeout=900):
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        print(f"FAILED: {' '.join(cmd)}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return None
    return result


def load_state():
    p = Path(STATE_PATH)
    if p.exists():
        return json.load(open(p))
    return {"notebooks": {}}


def save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_or_create_notebook(show, state):
    notebook_id = state["notebooks"].get(show)
    if notebook_id:
        return notebook_id

    result = run_cmd([NLM_BIN, "create", f"PodScribe: {show}", "--json"])
    if not result:
        return None
    data = json.loads(result.stdout)
    notebook_id = data["notebook"]["id"]
    state["notebooks"][show] = notebook_id
    save_state(state)
    return notebook_id


def clean_terms(raw):
    """Strip NLM citation refs and extract clean term lines."""
    # Remove citation markers [1], [1, 2], [1-3]
    cleaned = re.sub(r'\s*\[[\d,\s\-]+\]', '', raw)
    lines = []
    for line in cleaned.strip().split('\n'):
        line = line.strip()
        # Skip empty lines, headers, preamble
        if not line or line.startswith('#') or line.startswith('Answer'):
            continue
        # Strip leading ** bold markers
        line = re.sub(r'^\*\*(.+?)\*\*', r'\1', line)
        # Keep lines with | separator (term | description)
        if '|' in line:
            lines.append(line)
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description="Extract podcast terminology via NLM")
    parser.add_argument("--audio", required=True, help="Path to mp3 audio file")
    parser.add_argument("--show", required=True, help="Podcast show name")
    parser.add_argument("--lang", default="zh", choices=["zh", "en"], help="Language")
    parser.add_argument("--output", required=True, help="Output terms file path")
    parser.add_argument("--timeout", type=int, default=300, help="Source wait timeout")
    args = parser.parse_args()

    state = load_state()
    notebook_id = get_or_create_notebook(args.show, state)
    if not notebook_id:
        print("ERROR: Failed to create/get notebook", file=sys.stderr)
        sys.exit(1)

    print(f"Notebook: {notebook_id}", file=sys.stderr)

    # Upload audio source
    result = run_cmd([NLM_BIN, "source", "add", str(args.audio),
                      "--json", "--notebook", notebook_id])
    if not result:
        print("ERROR: Failed to add source", file=sys.stderr)
        sys.exit(1)

    data = json.loads(result.stdout)
    source_id = data["source"]["id"]
    print(f"Source: {source_id}", file=sys.stderr)

    # Wait for source processing
    result = run_cmd([NLM_BIN, "source", "wait", source_id,
                      "-n", notebook_id, "--timeout", str(args.timeout)],
                     timeout=args.timeout + 60)
    if not result:
        print("WARNING: Source wait failed, writing empty terms", file=sys.stderr)
        Path(args.output).write_text("")
        sys.exit(0)

    # Ask for terms
    prompt = TERM_PROMPT_ZH if args.lang == "zh" else TERM_PROMPT_EN
    result = run_cmd([NLM_BIN, "ask", prompt, "--json", "--notebook", notebook_id])
    if not result:
        print("WARNING: NLM ask failed, writing empty terms", file=sys.stderr)
        Path(args.output).write_text("")
        sys.exit(0)

    data = json.loads(result.stdout)
    answer = data.get("answer", result.stdout.strip())

    # Clean and write
    terms = clean_terms(answer)
    Path(args.output).write_text(terms)
    term_count = len([l for l in terms.split('\n') if l.strip()])
    print(f"Extracted {term_count} terms → {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
