#!/usr/bin/env swift
// asr-zh.swift — Chinese ASR via Speech.framework DictationTranscriber
// Usage: xcrun --sdk macosx swift asr-zh.swift [--locale zh-TW] <audio.wav>
// Output: JSON to stdout, logs to stderr
// Requires: macOS 26.0+

import AVFoundation
import Foundation
import Speech

// ── Helpers ────────────────────────────────────────────────────────────────

func die(_ message: String) -> Never {
    fputs("ERROR: \(message)\n", stderr)
    exit(1)
}

func log(_ message: String) {
    fputs("\(message)\n", stderr)
}

// ── Argument parsing ───────────────────────────────────────────────────────

var localeIdentifier = "zh-TW"
var audioPath: String? = nil

var args = CommandLine.arguments.dropFirst()
var idx = args.startIndex
while idx < args.endIndex {
    let arg = args[idx]
    if arg == "--locale" {
        idx = args.index(after: idx)
        guard idx < args.endIndex else { die("--locale requires a value") }
        localeIdentifier = args[idx]
    } else if arg.hasPrefix("--locale=") {
        localeIdentifier = String(arg.dropFirst("--locale=".count))
    } else if !arg.hasPrefix("-") {
        if audioPath == nil {
            audioPath = arg
        }
    }
    idx = args.index(after: idx)
}

guard let resolvedAudioPath = audioPath else {
    die("Usage: asr-zh.swift [--locale zh-TW] <audio.wav>")
}

// ── JSON output structures ─────────────────────────────────────────────────

struct Segment: Encodable {
    let start: Double
    let end: Double
    let text: String
}

struct ASROutput: Encodable {
    let segments: [Segment]
    let processing_time_seconds: Double
    let rtf: Double
    let duration_seconds: Double
}

// ── Main transcription function ────────────────────────────────────────────

@available(macOS 26.0, *)
func transcribe(audioPath: String, localeIdentifier: String) async throws -> ASROutput {
    let audioURL = URL(fileURLWithPath: audioPath)

    guard FileManager.default.fileExists(atPath: audioPath) else {
        die("Audio file not found: \(audioPath)")
    }

    let audioFile: AVAudioFile
    do {
        audioFile = try AVAudioFile(forReading: audioURL)
    } catch {
        die("Cannot open audio file: \(error.localizedDescription)")
    }

    let duration = Double(audioFile.length) / audioFile.fileFormat.sampleRate
    log("Audio: \(audioPath)")
    log("Duration: \(String(format: "%.1f", duration))s  Locale: \(localeIdentifier)")

    let locale = Locale(identifier: localeIdentifier)

    let module = DictationTranscriber(
        locale: locale,
        preset: .timeIndexedLongDictation
    )

    // Reserve locale and download model if needed
    for reserved in await AssetInventory.reservedLocales {
        await AssetInventory.release(reservedLocale: reserved)
    }
    try await AssetInventory.reserve(locale: locale)

    let modules: [any SpeechModule] = [module]
    if let request = try await AssetInventory.assetInstallationRequest(supporting: modules) {
        log("Downloading language model...")
        try await request.downloadAndInstall()
        log("Model ready.")
    }

    let startTime = Date()

    let analyzer = try await SpeechAnalyzer(
        inputAudioFile: audioFile,
        modules: modules,
        finishAfterFile: true
    )
    _ = analyzer

    var segments: [Segment] = []

    for try await result in module.results {
        let text = String(result.text.characters)
        guard !text.isEmpty else { continue }
        let range = result.range
        segments.append(Segment(
            start: range.start.seconds,
            end: range.end.seconds,
            text: text
        ))
    }

    let elapsed = Date().timeIntervalSince(startTime)
    let rtf = duration / elapsed

    log("Done. \(segments.count) segments, \(String(format: "%.1f", elapsed))s processing, RTF \(String(format: "%.1f", rtf))x")

    return ASROutput(
        segments: segments,
        processing_time_seconds: elapsed,
        rtf: rtf,
        duration_seconds: duration
    )
}

// ── Entry point ────────────────────────────────────────────────────────────

if #available(macOS 26.0, *) {
    do {
        let output = try await transcribe(
            audioPath: resolvedAudioPath,
            localeIdentifier: localeIdentifier
        )
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let json = try encoder.encode(output)
        print(String(data: json, encoding: .utf8)!)
    } catch {
        die("Transcription failed: \(error)")
    }
} else {
    die("Requires macOS 26.0+")
}
