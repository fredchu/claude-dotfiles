#!/usr/bin/env python3
"""Align ASR transcript with speaker diarization using word-level assignment.

Word-level strategy (English):
    1. Clean diarization: filter noise clusters
    2. Assign speaker to each word based on temporal overlap (linear scan for correctness)
    3. Group words into sentences using punctuation (.?!) with abbreviation awareness
    4. For sentences with mixed speakers, majority vote decides
    5. Merge consecutive sentences from the same speaker
    6. Auto-detect speaker roles (host/guest) and output speaker_map

Segment-level strategy (Chinese, fallback):
    Same as v1 — segment-level overlap matching + merge consecutive same-speaker.
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict


def overlap(a_start, a_end, b_start, b_end):
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def clean_diarization(diarize_segments, min_share=0.01):
    """Filter noise clusters (< min_share of total time) and return cleaned segments."""
    speaker_time = defaultdict(float)
    for s in diarize_segments:
        speaker_time[s["speakerId"]] += s["endTimeSeconds"] - s["startTimeSeconds"]
    total_time = sum(speaker_time.values())

    if total_time <= 0.0:
        print("WARNING: total diarization time is 0, returning all segments unfiltered", file=sys.stderr)
        return diarize_segments

    noise_speakers = set()
    for sid, t in speaker_time.items():
        if t / total_time < min_share:
            noise_speakers.add(sid)

    if noise_speakers:
        print(f"Noise speakers filtered ({min_share*100:.0f}% threshold): {noise_speakers}", file=sys.stderr)

    cleaned = [s for s in diarize_segments if s["speakerId"] not in noise_speakers]

    if not cleaned:
        print("WARNING: all speakers filtered as noise, returning original segments", file=sys.stderr)
        return diarize_segments

    for sid, t in sorted(speaker_time.items(), key=lambda x: -x[1]):
        marker = " [NOISE]" if sid in noise_speakers else ""
        print(f"  {sid}: {t/60:.1f} min ({t/total_time*100:.1f}%){marker}", file=sys.stderr)

    return cleaned


def find_nearest_speaker(time_point, diarize_segments):
    """Find the speaker of the nearest diarization segment to a time point."""
    if not diarize_segments:
        return "UNKNOWN"
    best_dist = float("inf")
    best_speaker = diarize_segments[0]["speakerId"]
    for d in diarize_segments:
        if time_point < d["startTimeSeconds"]:
            dist = d["startTimeSeconds"] - time_point
        elif time_point > d["endTimeSeconds"]:
            dist = time_point - d["endTimeSeconds"]
        else:
            dist = 0.0
        if dist < best_dist:
            best_dist = dist
            best_speaker = d["speakerId"]
    return best_speaker


def assign_speaker_to_word(word_start, word_end, diarize_segments):
    """Assign speaker via overlap (linear scan); fallback to nearest segment.

    Returns (speaker_id, is_gap) tuple. is_gap=True means no direct overlap was found.
    Linear scan is correct for all segment lengths; ~5s for 20K words × 1K segments.
    """
    best_speaker = None
    best_ov = 0.0
    for d in diarize_segments:
        ov = overlap(word_start, word_end, d["startTimeSeconds"], d["endTimeSeconds"])
        if ov > best_ov:
            best_ov = ov
            best_speaker = d["speakerId"]

    if best_speaker is None:
        best_speaker = find_nearest_speaker((word_start + word_end) / 2, diarize_segments)
        return best_speaker, True
    return best_speaker, False


# Common abbreviations and patterns that end with '.' but don't end a sentence
_ABBREVS = frozenset({
    "dr.", "mr.", "mrs.", "ms.", "jr.", "sr.", "st.", "vs.", "etc.", "inc.", "ltd.",
    "corp.", "dept.", "prof.", "gen.", "gov.", "sgt.", "cpl.", "pvt.", "rev.",
    "approx.", "est.", "avg.", "min.", "max.", "no.", "vol.", "ch.", "fig.",
    "u.s.", "u.k.", "e.u.", "a.i.", "i.e.", "e.g.", "a.m.", "p.m.",
})


def _is_sentence_end(word_text, next_word_text):
    """Check if a word ending in .?! is a real sentence boundary."""
    if not word_text:
        return False
    last_char = word_text[-1]
    if last_char in "?!":
        return True
    if last_char != ".":
        return False

    # Ellipsis "..." — treat as sentence end (check before other rules)
    if word_text.endswith("..."):
        return True

    lower = word_text.lower()

    # Known abbreviations
    if lower in _ABBREVS:
        return False

    # Single letter + dot (initials like "J." or "R.")
    if len(word_text) == 2 and word_text[0].isalpha():
        return False

    # Decimal numbers: "3.5", "$2.5M", "1.0" — but NOT "sentence.$3.5" edge case
    # Only suppress sentence-end if the ENTIRE word (minus currency prefix) is numeric
    stripped = word_text.lstrip("$€£¥")
    if stripped.rstrip(".") != stripped:
        # Word has trailing dot(s) beyond the decimal — e.g. "$3.5."
        # Strip the final sentence-ending dot, check if remainder is numeric
        core = stripped[:-1]  # remove the last dot
        if core and core.replace(".", "", 1).replace(",", "").isdigit():
            # "$3.5." — the last dot IS a sentence-end, the rest is a number
            return True
    else:
        # No trailing dot beyond content — e.g. "3.5" mid-word
        core = stripped
        if core and core.replace(".", "", 1).replace(",", "").isdigit():
            return False

    # Lookahead: if next word starts with lowercase, probably not a sentence end
    if next_word_text:
        first_char = next_word_text.lstrip("\"'([").strip()
        if first_char and first_char[0].islower():
            return False

    return True


def split_into_sentences(words_with_speakers):
    sentences = []
    current = []
    for i, w in enumerate(words_with_speakers):
        current.append(w)
        word_text = w["word"].rstrip()
        next_word = words_with_speakers[i + 1]["word"].strip() if i + 1 < len(words_with_speakers) else None
        if _is_sentence_end(word_text, next_word):
            sentences.append(current)
            current = []
    if current:
        sentences.append(current)
    return sentences


def majority_speaker(sentence_words):
    if not sentence_words:
        return "UNKNOWN"
    speakers = [w["speaker"] for w in sentence_words]
    counter = Counter(speakers)
    winner, _ = counter.most_common(1)[0]
    return winner


def auto_detect_speakers(merged_segments):
    """Auto-detect host vs guest for 2-person podcasts.

    Signals:
    1. First speaker (first 2 min) = host
    2. More total talk time = guest (in interviews)
    3. Shorter avg segment = host (questions are shorter)
    4. More questions = host

    Returns: {"host": speaker_id, "guest": speaker_id, "host_name": str|None, "guest_name": str|None}
    """
    if not merged_segments:
        return {}

    # Get distinct speakers — use sorted list for deterministic order
    # Filter out "UNKNOWN" which is a fallback, not a real speaker
    speakers = sorted(set(s["speaker"] for s in merged_segments) - {"UNKNOWN"})
    if len(speakers) != 2:
        print(f"Auto-detect: {len(speakers)} real speakers found, skipping (expected 2)", file=sys.stderr)
        return {}

    # Signal 1: Who talks first?
    first_speaker = merged_segments[0]["speaker"]
    if first_speaker == "UNKNOWN":
        # Find first non-UNKNOWN speaker
        for s in merged_segments:
            if s["speaker"] != "UNKNOWN":
                first_speaker = s["speaker"]
                break

    # Signal 2: Total talk time per speaker
    talk_time = defaultdict(float)
    for s in merged_segments:
        if s["speaker"] != "UNKNOWN":
            talk_time[s["speaker"]] += s["end"] - s["start"]

    # Signal 3: Average segment duration (seconds)
    seg_durations = defaultdict(list)
    for s in merged_segments:
        if s["speaker"] != "UNKNOWN":
            seg_durations[s["speaker"]].append(s["end"] - s["start"])
    avg_duration = {sid: sum(v)/len(v) for sid, v in seg_durations.items()}

    # Signal 4: Question ratio (segments ending with ?)
    question_ratio = {}
    for sid in speakers:
        segs = [s for s in merged_segments if s["speaker"] == sid]
        q_count = sum(1 for s in segs if s["text"].rstrip().endswith("?"))
        question_ratio[sid] = q_count / len(segs) if segs else 0

    # Scoring: host gets +1 for each signal
    scores = {sid: 0 for sid in speakers}
    if first_speaker in scores:
        scores[first_speaker] += 1  # Signal 1: first speaker = host

    less_talk = min(speakers, key=lambda s: talk_time[s])
    scores[less_talk] += 1  # Signal 2: less talk time = host

    shorter_segs = min(speakers, key=lambda s: avg_duration.get(s, 0))
    scores[shorter_segs] += 1  # Signal 3: shorter segments = host

    more_questions = max(speakers, key=lambda s: question_ratio[s])
    scores[more_questions] += 1  # Signal 4: more questions = host

    # Deterministic tie-breaking: prefer first_speaker as host on tie
    host = max(speakers, key=lambda s: (scores[s], 1 if s == first_speaker else 0))
    guest = [s for s in speakers if s != host][0]

    is_tie = scores[speakers[0]] == scores[speakers[1]]

    print(f"\nAuto speaker detection{' (TIE — first speaker wins)' if is_tie else ''}:", file=sys.stderr)
    for sid in speakers:
        print(f"  {sid}: talk={talk_time[sid]/60:.1f}min, avg_dur={avg_duration.get(sid, 0):.1f}s, "
              f"q_ratio={question_ratio[sid]:.2f}, first={'Y' if sid==first_speaker else 'N'}, "
              f"score={scores[sid]} → {'HOST' if sid==host else 'GUEST'}", file=sys.stderr)

    # Try to extract guest name from intro — scan first 5 segments
    guest_name = None
    for seg in merged_segments[:5]:
        m = re.search(r'conversation with\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', seg["text"])
        if m:
            guest_name = m.group(1)
            print(f"  Guest name extracted from intro: {guest_name}", file=sys.stderr)
            break

    return {"host": host, "guest": guest, "host_name": None, "guest_name": guest_name}


def align_word_level(word_timings, diarize_segments):
    if not word_timings:
        print("WARNING: no word timings, returning empty", file=sys.stderr)
        return []

    gap_count = 0
    words_with_speakers = []
    for wt in word_timings:
        speaker, is_gap = assign_speaker_to_word(wt["startTime"], wt["endTime"], diarize_segments)
        if is_gap:
            gap_count += 1
        words_with_speakers.append({
            "word": wt["word"], "start": wt["startTime"],
            "end": wt["endTime"], "speaker": speaker,
        })

    total = len(words_with_speakers)
    print(f"Words: {total}, gap-assigned: {gap_count} ({gap_count/total*100:.1f}%)", file=sys.stderr)

    sentences = split_into_sentences(words_with_speakers)
    print(f"Sentences detected: {len(sentences)}", file=sys.stderr)

    sentence_segments = []
    for sent_words in sentences:
        speaker = majority_speaker(sent_words)
        text = " ".join(w["word"] for w in sent_words)
        text = re.sub(r" {2,}", " ", text).strip()
        sentence_segments.append({
            "start": round(sent_words[0]["start"], 2),
            "end": round(sent_words[-1]["end"], 2),
            "speaker": speaker, "text": text,
        })

    merged = []
    for seg in sentence_segments:
        if merged and merged[-1]["speaker"] == seg["speaker"]:
            merged[-1]["end"] = seg["end"]
            merged[-1]["text"] += " " + seg["text"]
        else:
            merged.append(dict(seg))

    print(f"Sentence segments: {len(sentence_segments)}, after merge: {len(merged)}", file=sys.stderr)
    return merged


def align_segment_level(asr_segments, diarize_segments):
    aligned = []
    for asr_seg in asr_segments:
        speaker, _ = assign_speaker_to_word(asr_seg["start"], asr_seg["end"], diarize_segments)
        aligned.append({"start": round(asr_seg["start"], 2), "end": round(asr_seg["end"], 2),
                        "speaker": speaker, "text": asr_seg["text"]})

    # Chinese text: no space separator when merging
    merged = []
    for seg in aligned:
        if merged and merged[-1]["speaker"] == seg["speaker"]:
            merged[-1]["end"] = seg["end"]
            merged[-1]["text"] += seg["text"]
        else:
            merged.append(dict(seg))
    print(f"Aligned: {len(aligned)}, merged: {len(merged)}", file=sys.stderr)
    return merged


def apply_speaker_names(segments, speaker_map, host_name=None, guest_name=None):
    """Replace speaker IDs with names in segments (mutates in-place, non-idempotent)."""
    name_map = {}
    if speaker_map.get("host"):
        name_map[speaker_map["host"]] = host_name or speaker_map.get("host_name") or "Host"
    if speaker_map.get("guest"):
        name_map[speaker_map["guest"]] = guest_name or speaker_map.get("guest_name") or "Guest"

    for seg in segments:
        if seg["speaker"] in name_map:
            seg["speaker"] = name_map[seg["speaker"]]


def main():
    parser = argparse.ArgumentParser(description="Align ASR + diarization (v2)")
    parser.add_argument("--asr-words", help="ASR JSON with wordTimings (English)")
    parser.add_argument("--asr", help="ASR JSON with segments (Chinese)")
    parser.add_argument("--diarize", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--host", help="Host name (e.g. 'Lex Fridman')")
    parser.add_argument("--guest", help="Guest name (e.g. 'Jensen Huang')")
    parser.add_argument("--no-auto-detect", action="store_true", help="Skip auto speaker detection")
    args = parser.parse_args()

    if not args.asr_words and not args.asr:
        print("ERROR: Provide either --asr-words or --asr", file=sys.stderr)
        sys.exit(1)

    with open(args.diarize) as f:
        diarize_data = json.load(f)
    raw_segments = diarize_data.get("segments")
    if raw_segments is None:
        print("ERROR: diarization JSON missing 'segments' key", file=sys.stderr)
        sys.exit(1)
    print(f"Diarize segments: {len(raw_segments)}", file=sys.stderr)

    diarize_segments = clean_diarization(raw_segments)
    print(f"After cleanup: {len(diarize_segments)} segments", file=sys.stderr)

    if args.asr_words:
        with open(args.asr_words) as f:
            asr_data = json.load(f)
        word_timings = asr_data.get("wordTimings", [])
        print(f"Word timings: {len(word_timings)}", file=sys.stderr)
        merged = align_word_level(word_timings, diarize_segments)
    else:
        with open(args.asr) as f:
            asr_data = json.load(f)
        asr_segments = asr_data.get("segments")
        if asr_segments is None:
            print("ERROR: ASR JSON missing 'segments' key", file=sys.stderr)
            sys.exit(1)
        print(f"ASR segments: {len(asr_segments)}", file=sys.stderr)
        merged = align_segment_level(asr_segments, diarize_segments)

    speaker_map = {}
    if not args.no_auto_detect:
        speaker_map = auto_detect_speakers(merged)

    if speaker_map or args.host or args.guest:
        apply_speaker_names(merged, speaker_map, host_name=args.host, guest_name=args.guest)

    output_data = {
        "segments": merged,
        "speaker_map": speaker_map,
    }
    with open(args.output, "w") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"\nWritten to {args.output}: {len(merged)} segments", file=sys.stderr)


if __name__ == "__main__":
    main()
