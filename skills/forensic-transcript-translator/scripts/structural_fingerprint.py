"""
Structural Fingerprint Extractor

Extracts a deterministic structural fingerprint from a transcript file:
- Total paragraph count
- Speaker sequence (ordered list)
- All numeric values (dollars, percentages, counts)
- Total word count

Usage:
    python3 structural_fingerprint.py <file_path> [--json]
"""
import sys
import re
import json
import os


def extract_speakers(text):
    """Extract speaker names in order of appearance."""
    patterns = [
        r'^(?:\*\*)?([A-Z][a-zA-Z\s\.\-\']+?)(?:\s*[\|\-—]\s*.+?)?\s*(?:\*\*)?[:：]',
        r'^([A-Z][a-zA-Z\s\.\-\']+?)(?:\s*\(.+?\))?\s*[:：]',
    ]
    speakers = []
    seen = set()
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        for pattern in patterns:
            m = re.match(pattern, line)
            if m:
                name = m.group(1).strip().strip('*').strip()
                if len(name) > 2 and len(name) < 60 and name not in seen:
                    speakers.append(name)
                    seen.add(name)
                break
    return speakers


def extract_numbers(text):
    """Extract all numeric values with context."""
    numbers = []
    # Dollar amounts: $1.2B, $479.1 million, $12,345
    for m in re.finditer(r'\$[\d,]+\.?\d*\s*(?:billion|million|thousand|B|M|K|T)?', text, re.IGNORECASE):
        numbers.append(m.group(0).strip())
    # Percentages: 25%, 3.5%
    for m in re.finditer(r'[\d]+\.?\d*\s*%', text):
        numbers.append(m.group(0).strip())
    # Standalone large numbers with units
    for m in re.finditer(r'(?<!\$)\b[\d,]+\.?\d*\s+(?:billion|million|thousand|locations|customers|restaurants|units)\b', text, re.IGNORECASE):
        numbers.append(m.group(0).strip())
    return numbers


def count_paragraphs(text):
    """Count non-empty paragraphs."""
    paragraphs = re.split(r'\n\s*\n', text)
    return len([p for p in paragraphs if p.strip()])


def word_count(text):
    """Count words (English) or characters (Chinese)."""
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    return {"english_words": english_words, "chinese_chars": chinese_chars, "total": english_words + chinese_chars}


def main():
    if len(sys.argv) < 2:
        print("Usage: structural_fingerprint.py <file_path> [--json]")
        sys.exit(1)

    file_path = sys.argv[1]
    output_json = "--json" in sys.argv

    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    fingerprint = {
        "file": os.path.basename(file_path),
        "paragraph_count": count_paragraphs(text),
        "word_count": word_count(text),
        "speakers": extract_speakers(text),
        "speaker_count": len(extract_speakers(text)),
        "numbers": extract_numbers(text),
        "number_count": len(extract_numbers(text)),
    }

    if output_json:
        print(json.dumps(fingerprint, ensure_ascii=False, indent=2))
    else:
        print(f"=== Structural Fingerprint: {fingerprint['file']} ===")
        print(f"Paragraphs: {fingerprint['paragraph_count']}")
        wc = fingerprint['word_count']
        print(f"Words: {wc['english_words']} EN / {wc['chinese_chars']} ZH / {wc['total']} total")
        print(f"Speakers ({fingerprint['speaker_count']}):")
        for i, s in enumerate(fingerprint['speakers'], 1):
            print(f"  {i}. {s}")
        print(f"Numbers ({fingerprint['number_count']}):")
        for n in fingerprint['numbers']:
            print(f"  - {n}")


if __name__ == "__main__":
    main()
