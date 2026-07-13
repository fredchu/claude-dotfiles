#!/usr/bin/env python3
"""檢查 legacy-distill 產物的可發現性與雙向連結。"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path


DEFAULT_MEMORY = "~/.claude/projects/-Users-fredchu-Documents-For-Claude/memory/MEMORY.md"
DEFAULT_CLAUDE = ("~/.claude/CLAUDE.md", "/Users/fredchu/Documents/For_Claude/CLAUDE.md")
DEFAULT_WORKSPACE = "/Users/fredchu/Documents/For_Claude"
ANCHORS = (
    "company/_shared/references/career-direction-ml-bci-2026-07.md",
    "company/_shared/references/user-goals-and-philosophy.md",
    "company/_shared/references/strategic-compass-2026-07.md",
    "company/_shared/references/post-fable-playbook-2026-07.md",
    "company/_shared/references/judgment-eval-set-2026-07.md",
    "company/_shared/references/fable-five-observations-2026-07.md",
    "本體畫像/00-核心身份.md",
    "本體畫像/05-偏好與地雷.md",
)
CLAIM_RE = re.compile(r"更新|接續|放寬|升格|取代|已被")
STEM_RE = re.compile(
    r"(?<![A-Za-z0-9_-])(0\d-[a-z][a-z-]+)(?:\.md)?(?=\s*§|\s|[，。！？；、,:：)）\]]|$)"
)
SHORT_RE = re.compile(r"(?<!\d)(0\d)(?=\s*§)")
FILENAME_RE = re.compile(r"[A-Za-z0-9._-]+\.md")
DATE_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) \|", re.MULTILINE)


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


def sentences(text: str) -> list[str]:
    return [part.strip() for line in text.splitlines() for part in re.split(r"[。！？；]", line) if part.strip()]


def references(sentence: str) -> list[tuple[str, str]]:
    found: list[tuple[int, str, str]] = []
    for match in STEM_RE.finditer(sentence):
        found.append((match.start(), match.group(0).removesuffix(".md"), "stem"))
    for match in SHORT_RE.finditer(sentence):
        found.append((match.start(), match.group(), "short"))
    for match in FILENAME_RE.finditer(sentence):
        found.append((match.start(), match.group(), "filename"))
    return [(raw, kind) for _, raw, kind in sorted(found)]


def target_candidates(raw: str, kind: str, workspace: Path, memory: Path) -> tuple[list[Path], str | None]:
    governance = workspace / "company/_shared/governance"
    if kind == "stem":
        candidates = sorted(path for path in governance.glob(f"{raw}.md") if path.is_file())
        return [path.resolve() for path in candidates], None
    if kind == "short":
        candidates = sorted(path for path in governance.glob(f"{raw}-*.md") if path.is_file())
        if len(candidates) > 1:
            return [], f"縮寫歧義：{raw} 命中 {', '.join(path.name for path in candidates)}"
        return [path.resolve() for path in candidates], None
    directories = (
        governance,
        workspace / "company/_shared/references",
        memory.parent,
        workspace / "wiki",
    )
    return [candidate.resolve() for directory in directories if (candidate := directory / raw).is_file()], None


def contains_backlink(path: Path, product: Path) -> bool:
    text = read_text(path)
    return product.name in text or product.stem in text


def check_product(
    product: Path, discovery_text: str, workspace: Path, memory: Path, expect_claims: bool
) -> dict[str, object]:
    text = read_text(product)
    discoverable = product.name in discovery_text or product.stem in discovery_text
    violations: list[str] = []
    if not discoverable:
        violations.append(f"不可發現：MEMORY.md/CLAUDE.md 未提及 {product.name} 或 {product.stem}")

    claims: list[dict[str, object]] = []
    edge_keys: set[tuple[int, Path]] = set()
    for sentence_index, sentence in enumerate(sentences(text)):
        refs = references(sentence)
        if not CLAIM_RE.search(sentence) or not refs:
            continue
        claim_targets: list[dict[str, object]] = []
        seen_paths: set[Path] = set()
        for raw, kind in refs:
            candidates, problem = target_candidates(raw, kind, workspace, memory)
            if problem:
                violations.append(f"{product.name}：{problem}；句子：{sentence}")
                continue
            if not candidates:
                violations.append(f"{product.name}：目標不存在：{raw}；句子：{sentence}")
                continue
            target_results = []
            for candidate in candidates:
                if candidate in seen_paths:
                    continue
                seen_paths.add(candidate)
                backlink_ok = contains_backlink(candidate, product)
                edge_keys.add((sentence_index, candidate))
                target = {"raw": raw, "resolved": str(candidate), "backlink_ok": backlink_ok}
                claim_targets.append(target)
                target_results.append(target)
            if target_results and not any(target["backlink_ok"] for target in target_results):
                names = ", ".join(target["resolved"] for target in target_results)
                violations.append(f"{product.name}：缺少回指，請補至 {names}；句子：{sentence}")
        claims.append({"sentence": sentence, "targets": claim_targets})

    if expect_claims and not edge_keys:
        violations.append(f"{product.name}：預期至少一條宣稱目標，但 target_edges 為 0")
    return {
        "path": str(product),
        "discoverable": discoverable,
        "claim_sentences_found": len(claims),
        "target_edges": len(edge_keys),
        "claims": claims,
        "violations": violations,
    }


def inventory(workspace: Path, memory: Path) -> dict[str, object]:
    paths = [workspace / relative for relative in ANCHORS]
    paths.extend(sorted((workspace / "company/_shared/governance").glob("*.md")))
    files = []
    for path in paths:
        exists = path.is_file()
        files.append(
            {
                "path": str(path.resolve()),
                "exists": exists,
                "mtime": datetime.datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()
                if exists
                else None,
            }
        )

    timeline_paths = sorted((workspace / "wiki").glob("model-succession-*.md"))
    timeline_paths += sorted((workspace / "company/_shared/references").glob("*playbook*.md"))
    dates = [match for path in timeline_paths for match in DATE_RE.findall(read_text(path))]
    memory_text = read_text(memory)
    return {
        "files": files,
        "last_timeline_date": max(dates) if dates else "無紀錄（首跑）",
        "memory": {"path": str(memory), "lines": len(memory_text.splitlines()), "limit": 200},
    }


def build_parser() -> argparse.ArgumentParser:
    parser = Parser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--inventory", action="store_true")
    modes.add_argument("--check", nargs="+")
    parser.add_argument("--expect-claims", action="append", default=[])
    parser.add_argument("--memory-md", default=DEFAULT_MEMORY)
    parser.add_argument("--claude-md", action="append")
    parser.add_argument("--workspace", default=DEFAULT_WORKSPACE)
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
        workspace = resolved(args.workspace)
        memory = resolved(args.memory_md)
        if args.inventory:
            result = inventory(workspace, memory)
            if json_mode:
                print(json.dumps(result, ensure_ascii=False))
            else:
                for item in result["files"]:
                    status = item["mtime"] if item["exists"] else "缺檔"
                    print(f'{item["path"]}: {status}')
                print(f'上次蒸餾：{result["last_timeline_date"]}')
                print(f'MEMORY.md：{result["memory"]["lines"]}/{result["memory"]["limit"]} 行')
            return 0

        products = [resolved(path) for path in args.check]
        expected = {resolved(path) for path in args.expect_claims}
        if not expected.issubset(set(products)):
            raise CheckError("usage", "--expect-claims 必須是 --check 的子集")
        claude_paths = [resolved(path) for path in (args.claude_md or DEFAULT_CLAUDE)]
        discovery_text = read_text(memory) + "\n" + "\n".join(read_text(path) for path in claude_paths)
        product_results = [
            check_product(product, discovery_text, workspace, memory, product in expected)
            for product in products
        ]
        result = {"products": product_results, "pass": not any(p["violations"] for p in product_results)}
    except CheckError as error:
        return emit_error(error, json_mode)

    if json_mode:
        print(json.dumps(result, ensure_ascii=False))
    else:
        for product in result["products"]:
            verdict = "通過" if not product["violations"] else "未通過"
            print(
                f'{product["path"]}: {verdict}; discoverable={product["discoverable"]}; '
                f'claim_sentences_found={product["claim_sentences_found"]}; '
                f'target_edges={product["target_edges"]}'
            )
            for violation in product["violations"]:
                print(f"  - {violation}")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
