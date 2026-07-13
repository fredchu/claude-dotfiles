from __future__ import annotations

import json


def check(run_cli, fixture, product, *extra):
    result = run_cli(
        "linkage_check.py",
        "--check", product,
        "--workspace", fixture["workspace"],
        "--memory-md", fixture["memory"],
        "--claude-md", fixture["claude"],
        "--json", *extra,
    )
    return result, json.loads(result.stdout)


def test_discoverable_and_backlink_pass(linkage_fixture, run_cli):
    f = linkage_fixture
    product = f["write"]("products/output.md", "本文件更新 02-model-dispatch.md。")
    f["claude"].write_text("請讀 output.md", encoding="utf-8")
    (f["governance"] / "02-model-dispatch.md").write_text("回指 output.md", encoding="utf-8")
    result, payload = check(run_cli, f, product)
    assert result.returncode == 0
    item = payload["products"][0]
    assert item["discoverable"] is True
    assert item["claim_sentences_found"] == 1
    assert item["target_edges"] == 1  # stem 與檔名 pattern 命中同一路徑仍只算一次
    assert item["claims"][0]["targets"][0]["backlink_ok"] is True
    assert payload["pass"] is True


def test_undiscoverable_and_missing_backlink_fail(linkage_fixture, run_cli):
    f = linkage_fixture
    product = f["write"]("products/hidden.md", "接續 02-model-dispatch §5。")
    (f["governance"] / "02-model-dispatch.md").write_text("沒有回指", encoding="utf-8")
    result, payload = check(run_cli, f, product)
    assert result.returncode == 1
    violations = payload["products"][0]["violations"]
    assert any("不可發現" in item for item in violations)
    assert any("請補至" in item and "02-model-dispatch.md" in item for item in violations)


def test_short_reference_and_ambiguity(linkage_fixture, run_cli):
    f = linkage_fixture
    product = f["write"]("products/playbook.md", "02 §6 已有此法，現升格。")
    f["memory"].write_text("playbook.md", encoding="utf-8")
    (f["governance"] / "02-model-dispatch.md").write_text("playbook", encoding="utf-8")
    result, payload = check(run_cli, f, product)
    assert result.returncode == 0
    assert payload["products"][0]["target_edges"] == 1

    (f["governance"] / "02-other.md").write_text("playbook", encoding="utf-8")
    result, payload = check(run_cli, f, product)
    assert result.returncode == 1
    assert any("縮寫歧義" in item for item in payload["products"][0]["violations"])


def test_verb_and_target_in_different_sentences_are_not_claim(linkage_fixture, run_cli):
    f = linkage_fixture
    product = f["write"]("products/output.md", "必須先讀 02-model-dispatch.md。接著更新文件。")
    f["memory"].write_text("output.md", encoding="utf-8")
    result, payload = check(run_cli, f, product)
    assert result.returncode == 0
    assert payload["products"][0]["claim_sentences_found"] == 0
    assert payload["products"][0]["target_edges"] == 0


def test_missing_target_and_negation_trigger(linkage_fixture, run_cli):
    f = linkage_fixture
    product = f["write"]("products/output.md", "本規則不取代 missing.md。")
    f["memory"].write_text("output", encoding="utf-8")
    result, payload = check(run_cli, f, product)
    assert result.returncode == 1
    assert payload["products"][0]["claim_sentences_found"] == 1
    assert any("目標不存在：missing.md" in item for item in payload["products"][0]["violations"])


def test_duplicate_basename_any_backlink_passes(linkage_fixture, run_cli):
    f = linkage_fixture
    product = f["write"]("products/output.md", "本文件更新 shared.md。")
    f["memory"].write_text("output.md", encoding="utf-8")
    (f["governance"] / "shared.md").write_text("無", encoding="utf-8")
    (f["references"] / "shared.md").write_text("output.md", encoding="utf-8")
    result, payload = check(run_cli, f, product)
    assert result.returncode == 0
    item = payload["products"][0]
    assert item["target_edges"] == 2
    assert sorted(target["backlink_ok"] for target in item["claims"][0]["targets"]) == [False, True]


def test_zero_claim_expectation_and_subset_validation(linkage_fixture, run_cli):
    f = linkage_fixture
    product = f["write"]("products/output.md", "純資訊。")
    f["memory"].write_text("output", encoding="utf-8")
    result, payload = check(run_cli, f, product)
    assert result.returncode == 0
    assert payload["products"][0]["target_edges"] == 0

    result, payload = check(run_cli, f, product, "--expect-claims", product)
    assert result.returncode == 1
    assert any("target_edges 為 0" in item for item in payload["products"][0]["violations"])

    other = f["write"]("products/other.md", "x")
    result, payload = check(run_cli, f, product, "--expect-claims", other)
    assert result.returncode == 2
    assert payload["error"]["kind"] == "usage"


def test_modes_and_io_errors_json(linkage_fixture, run_cli):
    f = linkage_fixture
    base = ["--workspace", f["workspace"], "--memory-md", f["memory"], "--claude-md", f["claude"], "--json"]
    for args in (base, ["--inventory", "--check", "x", *base], ["--check", *base]):
        result = run_cli("linkage_check.py", *args)
        assert result.returncode == 2
        assert json.loads(result.stdout)["error"]["kind"] == "usage"

    missing = f["workspace"] / "missing.md"
    result, payload = check(run_cli, f, missing)
    assert result.returncode == 2
    assert payload["error"]["kind"] == "io"
    assert payload["error"]["path"] == str(missing.resolve())


def test_success_json_exact_per_product_schema(linkage_fixture, run_cli):
    f = linkage_fixture
    product = f["write"]("products/output.md", "純資訊")
    f["memory"].write_text("output", encoding="utf-8")
    result, payload = check(run_cli, f, product)
    assert result.returncode == 0
    assert set(payload) == {"products", "pass"}
    assert set(payload["products"][0]) == {
        "path", "discoverable", "claim_sentences_found", "target_edges", "claims", "violations"
    }
