from __future__ import annotations

import json
import os
import time


def test_inventory_timeline_lines_missing_and_mtime(linkage_fixture, run_cli):
    f = linkage_fixture
    anchor = f["write"](
        "company/_shared/references/post-fable-playbook-2026-07.md",
        "- 2026-07-11 | 舊\n- 2026-07-12 | 新",
    )
    os.utime(anchor, (time.time(), time.time()))
    f["memory"].write_text("一\n二\n三\n", encoding="utf-8")
    result = run_cli(
        "linkage_check.py", "--inventory", "--workspace", f["workspace"],
        "--memory-md", f["memory"], "--json",
    )
    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["last_timeline_date"] == "2026-07-12"
    assert payload["memory"]["lines"] == 3
    assert any(item["exists"] and item["mtime"] for item in payload["files"])
    assert any(not item["exists"] and item["mtime"] is None for item in payload["files"])


def test_inventory_first_run_message(linkage_fixture, run_cli):
    f = linkage_fixture
    result = run_cli(
        "linkage_check.py", "--inventory", "--workspace", f["workspace"],
        "--memory-md", f["memory"], "--json",
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["last_timeline_date"] == "無紀錄（首跑）"
