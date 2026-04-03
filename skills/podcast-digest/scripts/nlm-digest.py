#!/usr/bin/env python3
"""NLM-based podcast digest: download → NotebookLM summary → clean markdown.

Usage:
    python3 nlm-digest.py --audio /tmp/podscribe-work/episode.mp3 \
        --show "The Changelog" --title "From GitLab to Kilo Code" \
        --date 2026-01-07 --duration "1:17:18" \
        --output company/podscribe/transcripts/slug-summary.md \
        --state /Users/fredchu/Documents/For_Claude/company/podscribe/nlm-state.json

Handles:
- Notebook management (create or reuse per show)
- Source upload + wait
- NLM ask with fixed prompt
- Strip NLM citation refs [1, 2] and trailing follow-up questions
- Write clean markdown with frontmatter
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

NLM_BIN = os.environ.get("NLM_BIN", "notebooklm")

NLM_PROMPT = """用繁體中文，針對最新加入的音檔來源，嚴格按照以下格式產出。每個編號項目必須獨立一段，不可合併。不要加引用編號。不要推薦其他功能。輸出到第 5 個 Q&A 的答案後立即停止，不要加任何後續問題、引導語或結語。

## 分章節摘要

1. **章節標題**：3-5 句摘要。

2. **章節標題**：3-5 句摘要。

3. **章節標題**：3-5 句摘要。

## 5 個最重要的觀點

1. **觀點標題**：說明。

2. **觀點標題**：說明。

3. **觀點標題**：說明。

4. **觀點標題**：說明。

5. **觀點標題**：說明。

## 5 個 Q&A

1. **問：**問題內容？
**答：**答案內容。

2. **問：**問題內容？
**答：**答案內容。

3. **問：**問題內容？
**答：**答案內容。

4. **問：**問題內容？
**答：**答案內容。

5. **問：**問題內容？
**答：**答案內容。"""


def run_cmd(cmd, timeout=900):
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        print(f"FAILED: {' '.join(cmd)}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result


def load_state(path):
    p = Path(path)
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return {"notebooks": {}}


def save_state(state, path):
    with open(path, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_or_create_notebook(show, state, state_path):
    notebook_id = state["notebooks"].get(show)
    if notebook_id:
        return notebook_id

    result = run_cmd([NLM_BIN, "create", f"PodScribe: {show}", "--json"])
    data = json.loads(result.stdout)
    notebook_id = data["notebook"]["id"]
    state["notebooks"][show] = notebook_id
    save_state(state, state_path)
    return notebook_id


def add_source_and_wait(audio_path, notebook_id):
    result = run_cmd([NLM_BIN, "source", "add", str(audio_path), "--json", "--notebook", notebook_id])
    data = json.loads(result.stdout)
    source_id = data["source"]["id"]

    run_cmd([NLM_BIN, "source", "wait", source_id, "-n", notebook_id, "--timeout", "600"], timeout=660)
    return source_id


def ask_nlm(notebook_id):
    result = run_cmd([NLM_BIN, "ask", NLM_PROMPT, "--json", "--notebook", notebook_id])
    data = json.loads(result.stdout)
    return data.get("answer", result.stdout.strip())


def clean_answer(answer):
    # Strip NLM citation references [1, 2] [9-11] etc
    answer = re.sub(r'\s*\[[\d,\s\-]+\]', '', answer)
    # Strip trailing NLM follow-up questions
    answer = re.sub(
        r'\n+[^\n]*(?:想進一步|想再深入|想更深入|還有什麼|有什麼想|會想了解|需要我)[^\n]*(?:嗎？|呢？)\s*$',
        '', answer
    )
    return answer.strip()


def write_output(answer, args):
    frontmatter = f"""---
title: "{args.title}"
podcast: "{args.show}"
guest: "{args.guest or ''}"
date: "{args.date or ''}"
duration: "{args.duration or ''}"
mode: summary
source: notebooklm
---

"""
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(frontmatter + answer)
    return str(output)


def main():
    parser = argparse.ArgumentParser(description="NLM podcast digest")
    parser.add_argument("--audio", required=True, help="Path to mp3 audio file")
    parser.add_argument("--show", required=True, help="Podcast show name")
    parser.add_argument("--title", required=True, help="Episode title")
    parser.add_argument("--guest", default="", help="Guest name")
    parser.add_argument("--date", default="", help="Publish date")
    parser.add_argument("--duration", default="", help="Episode duration")
    parser.add_argument("--output", required=True, help="Output markdown path")
    parser.add_argument("--state", default="/Users/fredchu/Documents/For_Claude/company/podscribe/nlm-state.json",
                        help="NLM state file path")
    args = parser.parse_args()

    state = load_state(args.state)

    print(f"Getting notebook for: {args.show}")
    notebook_id = get_or_create_notebook(args.show, state, args.state)
    print(f"Notebook ID: {notebook_id}")

    print(f"Adding source: {args.audio}")
    source_id = add_source_and_wait(args.audio, notebook_id)
    print(f"Source ready: {source_id}")

    print("Asking NLM for summary...")
    raw_answer = ask_nlm(notebook_id)
    answer = clean_answer(raw_answer)

    output_path = write_output(answer, args)
    print(f"Written: {output_path} ({len(answer)} chars)")


if __name__ == "__main__":
    main()
