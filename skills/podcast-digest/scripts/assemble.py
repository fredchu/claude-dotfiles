#!/usr/bin/env python3
"""Assemble final podcast digest markdown from corrected transcript + structured outputs.

Usage:
    python3 assemble.py \
      --corrected corrected-all.json \
      --summary summary.md --highlights highlights.md \
      --keywords keywords.md --qa qa.md \
      --title "Episode Title" --host "Host" --guest "Guest" \
      --date 2026-03-30 --duration "1h 2m" \
      --output transcript.md

For bilingual (English podcast with Chinese translation):
    python3 assemble.py ... --bilingual

As module:
    from assemble import assemble_digest
"""

import argparse
import json
import os


def assemble_digest(
    corrected_path: str,
    summary_path: str,
    highlights_path: str,
    keywords_path: str,
    qa_path: str,
    title: str,
    host: str,
    guest: str,
    date: str,
    duration: str,
    bilingual: bool = False,
) -> str:
    """Assemble all parts into final markdown. Returns markdown string."""

    with open(corrected_path) as f:
        data = json.load(f)

    parts = {}
    for name, path in [
        ("summary", summary_path),
        ("highlights", highlights_path),
        ("keywords", keywords_path),
        ("qa", qa_path),
    ]:
        with open(path) as f:
            parts[name] = f.read()

    # Build transcript section
    transcript_lines = []
    for seg in data["segments"]:
        mins = int(seg["start"] // 60)
        secs = int(seg["start"] % 60)
        transcript_lines.append(f"### [{mins:02d}:{secs:02d}] {seg['speaker']}\n")

        if bilingual and "text_zh" in seg:
            transcript_lines.append(seg["text"] + "\n")
            transcript_lines.append(seg["text_zh"] + "\n")
        else:
            transcript_lines.append(seg["text"] + "\n")

        transcript_lines.append("---\n")

    transcript = "\n".join(transcript_lines)

    full = f"""# {title}

> 主持人：{host}｜來賓：{guest}
> 日期：{date}｜時長：{duration}

---

{parts['summary']}

---

{parts['highlights']}

---

{parts['keywords']}

---

{parts['qa']}

---

# 逐字稿

{transcript}
"""
    return full


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Assemble podcast digest")
    parser.add_argument("--corrected", required=True, help="corrected-all.json path")
    parser.add_argument("--summary", required=True)
    parser.add_argument("--highlights", required=True)
    parser.add_argument("--keywords", required=True)
    parser.add_argument("--qa", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--guest", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--duration", required=True)
    parser.add_argument("--bilingual", action="store_true")
    parser.add_argument("--output", required=True, help="Output markdown path")
    args = parser.parse_args()

    md = assemble_digest(
        corrected_path=args.corrected,
        summary_path=args.summary,
        highlights_path=args.highlights,
        keywords_path=args.keywords,
        qa_path=args.qa,
        title=args.title,
        host=args.host,
        guest=args.guest,
        date=args.date,
        duration=args.duration,
        bilingual=args.bilingual,
    )

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w") as f:
        f.write(md)
    print(f"Written: {args.output} ({len(md)} chars)")
