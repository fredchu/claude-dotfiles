"""
Forensic Audit Diff Tool

Compares structural fingerprints of source (EN) and target (ZH) files.
Reports mismatches in paragraph count, speaker sequence, and numeric values.

Usage:
    python3 audit_diff.py <source_file> <target_file> [--json]
"""
import sys
import json
import os

# Import from sibling module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from structural_fingerprint import extract_speakers, extract_numbers, count_paragraphs, word_count


def normalize_number(n):
    """Normalize a number string for comparison."""
    n = n.strip().replace(',', '').replace(' ', '')
    return n


def audit(source_path, target_path):
    with open(source_path, 'r', encoding='utf-8') as f:
        source_text = f.read()
    with open(target_path, 'r', encoding='utf-8') as f:
        target_text = f.read()

    results = {"passed": True, "issues": [], "summary": {}}

    # 1. Paragraph count
    src_para = count_paragraphs(source_text)
    tgt_para = count_paragraphs(target_text)
    diff = abs(src_para - tgt_para)
    tolerance = max(3, int(src_para * 0.1))  # 10% or 3, whichever is larger
    results["summary"]["paragraphs"] = {"source": src_para, "target": tgt_para, "diff": diff}
    if diff > tolerance:
        results["passed"] = False
        results["issues"].append(f"PARAGRAPH_MISMATCH: source={src_para}, target={tgt_para}, diff={diff} (tolerance={tolerance})")

    # 2. Speaker sequence
    src_speakers = extract_speakers(source_text)
    tgt_speakers = extract_speakers(target_text)
    results["summary"]["speakers"] = {"source": src_speakers, "target": tgt_speakers}
    # Check if all source speakers appear in target (name might be translated)
    if len(src_speakers) != len(tgt_speakers):
        results["issues"].append(f"SPEAKER_COUNT_MISMATCH: source={len(src_speakers)}, target={len(tgt_speakers)}")
        # Not auto-fail: speaker names get translated

    # 3. Number audit (critical - must be exact)
    src_numbers = extract_numbers(source_text)
    tgt_numbers = extract_numbers(target_text)
    src_normalized = set(normalize_number(n) for n in src_numbers)
    tgt_normalized = set(normalize_number(n) for n in tgt_numbers)
    missing_in_target = src_normalized - tgt_normalized
    results["summary"]["numbers"] = {
        "source_count": len(src_numbers),
        "target_count": len(tgt_numbers),
        "missing_in_target": list(missing_in_target)[:20],
    }
    if missing_in_target:
        results["passed"] = False
        results["issues"].append(f"NUMBERS_MISSING: {len(missing_in_target)} numbers from source not found in target")

    # 4. Word count ratio sanity check
    src_wc = word_count(source_text)
    tgt_wc = word_count(target_text)
    results["summary"]["word_count"] = {"source": src_wc, "target": tgt_wc}

    return results


def main():
    if len(sys.argv) < 3:
        print("Usage: audit_diff.py <source_file> <target_file> [--json]")
        sys.exit(1)

    source_path = sys.argv[1]
    target_path = sys.argv[2]
    output_json = "--json" in sys.argv

    for p in [source_path, target_path]:
        if not os.path.exists(p):
            print(f"Error: File not found: {p}")
            sys.exit(1)

    results = audit(source_path, target_path)

    if output_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        status = "PASSED" if results["passed"] else "FAILED"
        print(f"=== Forensic Audit Result: {status} ===")
        s = results["summary"]
        print(f"\nParagraphs: source={s['paragraphs']['source']}, target={s['paragraphs']['target']}")
        print(f"Speakers: source={len(s['speakers']['source'])}, target={len(s['speakers']['target'])}")
        print(f"Numbers: source={s['numbers']['source_count']}, target={s['numbers']['target_count']}")
        if s['numbers']['missing_in_target']:
            print(f"  Missing in target: {', '.join(s['numbers']['missing_in_target'][:10])}")
        if results["issues"]:
            print(f"\nIssues ({len(results['issues'])}):")
            for issue in results["issues"]:
                print(f"  - {issue}")
        else:
            print("\nNo issues found.")


if __name__ == "__main__":
    main()
