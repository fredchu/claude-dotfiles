from __future__ import annotations

import json

from scripts.leak_check import is_cjk, normalize


def run_json(run_cli, eval_path, context_path, *extra):
    result = run_cli(
        "leak_check.py", "--eval-set", eval_path, "--context", context_path, "--json", *extra
    )
    return result, json.loads(result.stdout)


def test_pure_cjk_verbatim_hit_reports_source(tmp_path, eval_file, run_cli):
    eval_path = eval_file(["甲乙丙丁戊己庚辛"])
    context = tmp_path / "context.md"
    context.write_text("前文甲乙丙丁戊己庚辛後文", encoding="utf-8")
    result, payload = run_json(run_cli, eval_path, context)
    assert result.returncode == 1
    assert payload["questions"][0]["leaked"] is True
    assert payload["questions"][0]["verbatim_hits"][0]["context_file"] == str(context.resolve())


def test_mixed_ascii_cjk_verbatim_and_short_input(tmp_path, eval_file, run_cli):
    eval_path = eval_file(["10min timeout 先死", "甲乙"])
    context = tmp_path / "context.md"
    context.write_text("別讓 10MIN timeout 先死", encoding="utf-8")
    result, payload = run_json(run_cli, eval_path, context, "--min-verbatim", 4)
    assert result.returncode == 1
    assert [item["leaked"] for item in payload["questions"]] == [True, False]


def test_overlap_positive_exact_threshold_and_raw_filtered(tmp_path, eval_file, run_cli):
    eval_path = eval_file(["alpha beta", "共同開場 gamma", "共同開場 delta"])
    context = tmp_path / "context.md"
    context.write_text("alpha", encoding="utf-8")
    result, payload = run_json(
        run_cli, eval_path, context, "--min-verbatim", 8, "--overlap-threshold", 0.5
    )
    first = payload["questions"][0]
    assert result.returncode == 0
    assert first["overlap_raw"] == 0.5
    assert first["overlap_filtered"] == 0.5
    assert first["leaked"] is False

    result, payload = run_json(
        run_cli, eval_path, context, "--min-verbatim", 8, "--overlap-threshold", 0.49
    )
    assert result.returncode == 1
    assert payload["questions"][0]["leaked"] is True


def test_template_filter_and_no_distinctive_warning(tmp_path, eval_file, run_cli):
    eval_path = eval_file(["共同開場 alpha", "共同開場 beta", "共同開場 gamma"])
    context = tmp_path / "context.md"
    context.write_text("共同開場", encoding="utf-8")
    result, payload = run_json(run_cli, eval_path, context, "--min-verbatim", 8)
    assert result.returncode == 0
    assert payload["questions"][0]["overlap_raw"] > payload["questions"][0]["overlap_filtered"]

    eval_path = eval_file(["alpha", "alpha", "alpha"])
    context.write_text("unrelated", encoding="utf-8")
    result, payload = run_json(run_cli, eval_path, context)
    assert result.returncode == 0
    assert all(item["warning"] == "no_distinctive_tokens" for item in payload["questions"])


def test_multiple_contexts_second_hit_and_context_replaces_defaults(tmp_path, eval_file, run_cli):
    eval_path = eval_file(["甲乙丙丁戊己庚辛"])
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    first.write_text("無關", encoding="utf-8")
    second.write_text("甲乙丙丁戊己庚辛", encoding="utf-8")
    result = run_cli(
        "leak_check.py", "--eval-set", eval_path, "--context", first, "--context", second, "--json"
    )
    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert payload["questions"][0]["verbatim_hits"][0]["context_file"] == str(second.resolve())


def test_parser_prefixes_colons_crlf_multiline_and_bold_body(tmp_path, run_cli):
    eval_path = tmp_path / "eval.md"
    eval_path.write_bytes(
        "### 題目\r\n> **情境**: 第一行\r\n**一般粗體**不截斷\r\n第二行\r\n- **誘答**：錯誤\r\n**正解**: 正確".encode()
    )
    context = tmp_path / "context.md"
    context.write_text("第一行一般粗體不截斷第二行", encoding="utf-8")
    result, payload = run_json(run_cli, eval_path, context, "--min-verbatim", 3)
    assert result.returncode == 1
    assert payload["questions"][0]["title"] == "題目"


def test_parse_io_and_usage_errors_are_json(tmp_path, eval_file, run_cli):
    context = tmp_path / "context.md"
    context.write_text("x", encoding="utf-8")
    for body in (
        "### 缺情境\n**誘答**：x",
        "### 缺誘答\n**情境**：x",
        "## 沒有題目",
    ):
        path = tmp_path / f"bad-{len(body)}.md"
        path.write_text(body, encoding="utf-8")
        result = run_cli("leak_check.py", "--eval-set", path, "--context", context, "--json")
        assert result.returncode == 2
        assert json.loads(result.stdout)["error"]["kind"] == "parse"

    good = eval_file(["正常情境"])
    missing = tmp_path / "missing.md"
    result = run_cli("leak_check.py", "--eval-set", good, "--context", missing, "--json")
    payload = json.loads(result.stdout)
    assert result.returncode == 2
    assert payload["error"] == {"kind": "io", "message": payload["error"]["message"], "path": str(missing.resolve())}

    for option, value in (("--min-verbatim", 2), ("--overlap-threshold", 1.5)):
        result = run_cli(
            "leak_check.py", "--eval-set", good, "--context", context, option, value, "--json"
        )
        assert result.returncode == 2
        assert json.loads(result.stdout)["error"]["kind"] == "usage"


def test_cjk_ranges_exclude_yijing_hexagrams():
    assert is_cjk("㐀") and is_cjk("鿿") and is_cjk("豈") and is_cjk("﫿")
    assert not is_cjk("䷀")
    assert normalize("甲䷀乙かな한") == ["甲", "乙"]


def test_json_schema(tmp_path, eval_file, run_cli):
    eval_path = eval_file(["alpha beta"])
    context = tmp_path / "context.md"
    context.write_text("none", encoding="utf-8")
    result, payload = run_json(run_cli, eval_path, context)
    assert result.returncode == 0
    assert set(payload) == {"questions", "leaked_count"}
    assert set(payload["questions"][0]) == {
        "id", "title", "verbatim_hits", "overlap_raw", "overlap_filtered", "warning", "leaked"
    }
