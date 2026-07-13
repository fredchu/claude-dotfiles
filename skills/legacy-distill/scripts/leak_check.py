#!/usr/bin/env python3
"""檢查校準測驗的情境是否洩漏到既有 context。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


DEFAULT_CONTEXTS = (
    "~/.claude/projects/-Users-fredchu-Documents-For-Claude/memory/MEMORY.md",
    "~/.claude/CLAUDE.md",
    "/Users/fredchu/Documents/For_Claude/CLAUDE.md",
)
FIELD_RE = re.compile(
    r"^\s*(?:[>*-]\s*)*\*\*(情境|誘答|正解|原型|出處)\*\*\s*[:：]"
)
QUESTION_RE = re.compile(r"^###\s")
SECTION_RE = re.compile(r"^##\s")
ASCII_RE = re.compile(r"[A-Za-z0-9]+")
SEP = "\x00"


class CheckError(Exception):
    def __init__(self, kind: str, message: str, path: Path | None = None):
        super().__init__(message)
        self.kind = kind
        self.path = path


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CheckError("usage", message)


def resolved(value: str) -> Path:
    return Path(value).expanduser().resolve()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise CheckError("io", str(exc), path) from exc


def parse_questions(text: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    starts = [index for index, line in enumerate(lines) if QUESTION_RE.match(line)]
    if not starts:
        raise CheckError("parse", "找不到任何題目")

    questions: list[dict[str, str]] = []
    for number, start in enumerate(starts, 1):
        end = len(lines)
        for index in range(start + 1, len(lines)):
            if QUESTION_RE.match(lines[index]) or SECTION_RE.match(lines[index]):
                end = index
                break
        title = lines[start][4:].strip()
        fields: dict[str, list[str]] = {}
        active: str | None = None
        for line in lines[start + 1 : end]:
            match = FIELD_RE.match(line)
            if match:
                active = match.group(1)
                fields.setdefault(active, []).append(line[match.end() :].strip())
            elif active is not None:
                fields[active].append(line)
        missing = [name for name in ("情境", "誘答") if name not in fields]
        if missing:
            raise CheckError("parse", f"題目「{title}」缺少欄位：{'、'.join(missing)}")
        questions.append(
            {
                "id": str(number),
                "title": title,
                "context": "\n".join(fields["情境"]).strip(),
            }
        )
    return questions


def is_cjk(char: str) -> bool:
    code = ord(char)
    return 0x3400 <= code <= 0x4DBF or 0x4E00 <= code <= 0x9FFF or 0xF900 <= code <= 0xFAFF


def normalize(text: str) -> list[str]:
    units: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if is_cjk(char):
            units.append(char)
            index += 1
            continue
        match = ASCII_RE.match(text, index)
        if match:
            units.append(match.group().lower())
            index = match.end()
            continue
        index += 1
    return units


def feature_tokens(units: list[str]) -> set[str]:
    tokens = {unit for unit in units if unit.isascii() and len(unit) >= 3}
    for index in range(len(units) - 2):
        triple = units[index : index + 3]
        if all(len(unit) == 1 and is_cjk(unit) for unit in triple):
            tokens.add("".join(triple))
    return tokens


def analyze(
    questions: list[dict[str, str]], contexts: list[tuple[Path, str]], min_verbatim: int, threshold: float
) -> dict[str, object]:
    question_units = [normalize(question["context"]) for question in questions]
    question_tokens = [feature_tokens(units) for units in question_units]
    counts = Counter(token for tokens in question_tokens for token in tokens)
    templates = {token for token, count in counts.items() if count >= 3}
    normalized_contexts = [(path, normalize(text)) for path, text in contexts]
    context_tokens: set[str] = set()
    for _, units in normalized_contexts:
        context_tokens.update(feature_tokens(units))

    results = []
    for question, units, raw_tokens in zip(questions, question_units, question_tokens):
        hits: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        if len(units) >= min_verbatim:
            for offset in range(len(units) - min_verbatim + 1):
                window = units[offset : offset + min_verbatim]
                needle = SEP.join(window)
                for path, context_units in normalized_contexts:
                    if needle in SEP.join(context_units):
                        hit = ("".join(window), str(path))
                        if hit not in seen:
                            hits.append({"text": hit[0], "context_file": hit[1]})
                            seen.add(hit)
        distinctive = raw_tokens - templates
        overlap_raw = len(raw_tokens & context_tokens) / len(raw_tokens) if raw_tokens else 0.0
        overlap_filtered = (
            len(distinctive & context_tokens) / len(distinctive) if distinctive else 0.0
        )
        warning = "no_distinctive_tokens" if not distinctive else None
        results.append(
            {
                "id": question["id"],
                "title": question["title"],
                "verbatim_hits": hits,
                "overlap_raw": overlap_raw,
                "overlap_filtered": overlap_filtered,
                "warning": warning,
                "leaked": bool(hits) or overlap_filtered > threshold,
            }
        )
    return {"questions": results, "leaked_count": sum(item["leaked"] for item in results)}


def build_parser() -> argparse.ArgumentParser:
    parser = Parser(description=__doc__)
    parser.add_argument("--eval-set", required=True)
    parser.add_argument("--context", action="append")
    parser.add_argument("--min-verbatim", type=int, default=8)
    parser.add_argument("--overlap-threshold", type=float, default=0.5)
    parser.add_argument("--json", action="store_true")
    return parser


def emit_error(error: CheckError, json_mode: bool) -> int:
    payload = {
        "error": {
            "kind": error.kind,
            "message": str(error),
            "path": str(error.path) if error.path is not None else None,
        }
    }
    if json_mode:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"錯誤：{error}", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    args_list = sys.argv[1:] if argv is None else argv
    json_mode = "--json" in args_list
    try:
        args = build_parser().parse_args(args_list)
        json_mode = args.json
        if args.min_verbatim < 3:
            raise CheckError("usage", "--min-verbatim 必須大於等於 3")
        if not 0 <= args.overlap_threshold <= 1:
            raise CheckError("usage", "--overlap-threshold 必須介於 0 與 1")
        eval_path = resolved(args.eval_set)
        context_paths = [resolved(path) for path in (args.context or DEFAULT_CONTEXTS)]
        questions = parse_questions(read_text(eval_path))
        contexts = [(path, read_text(path)) for path in context_paths]
        result = analyze(questions, contexts, args.min_verbatim, args.overlap_threshold)
    except CheckError as error:
        return emit_error(error, json_mode)

    if json_mode:
        print(json.dumps(result, ensure_ascii=False))
    else:
        for question in result["questions"]:
            warning = question["warning"] or "-"
            verdict = "洩題" if question["leaked"] else "通過"
            print(
                f'{question["id"]} {question["title"]}: {verdict}; '
                f'逐字={len(question["verbatim_hits"])}; '
                f'filtered={question["overlap_filtered"]:.3f}; '
                f'raw={question["overlap_raw"]:.3f}; warning={warning}'
            )
            for hit in question["verbatim_hits"]:
                print(f'  - 逐字「{hit["text"]}」@ {hit["context_file"]}')
        print(f'{result["leaked_count"]}/{len(result["questions"])} 題洩題')
    return 1 if result["leaked_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
