from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def run_cli():
    def run(script: str, *args: object) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script), *(str(arg) for arg in args)],
            text=True,
            capture_output=True,
            check=False,
        )

    return run


@pytest.fixture
def eval_file(tmp_path):
    def make(contexts: list[str], *, line_ending: str = "\n") -> Path:
        chunks = []
        for index, context in enumerate(contexts, 1):
            chunks.append(
                f"### Q{index}\n**情境**：{context}\n**誘答**: 錯誤答案\n**正解**：正確答案"
            )
        path = tmp_path / "eval.md"
        path.write_bytes(line_ending.join("\n\n".join(chunks).splitlines()).encode())
        return path

    return make


@pytest.fixture
def linkage_fixture(tmp_path):
    workspace = tmp_path / "workspace"
    governance = workspace / "company/_shared/governance"
    references = workspace / "company/_shared/references"
    wiki = workspace / "wiki"
    memory_dir = tmp_path / "memory"
    for directory in (governance, references, wiki, memory_dir):
        directory.mkdir(parents=True, exist_ok=True)
    memory = memory_dir / "MEMORY.md"
    memory.write_text("", encoding="utf-8")
    claude = tmp_path / "CLAUDE.md"
    claude.write_text("", encoding="utf-8")

    def write(relative: str, text: str) -> Path:
        path = workspace / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    return {
        "workspace": workspace,
        "governance": governance,
        "references": references,
        "wiki": wiki,
        "memory": memory,
        "claude": claude,
        "write": write,
    }
