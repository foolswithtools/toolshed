#!/usr/bin/env python3
"""Transcribe an audio file with whisper.cpp, emit word-level timestamps as JSON.

Why whisper.cpp: it's actively maintained, has no Python runtime tax, and
is what Remotion's own `@remotion/install-whisper-cpp` ships with — so the
same model files work on both sides if the user already has Remotion's
helper installed.

Usage:
    transcribe.py <audio> <output.json> [--model NAME] [--language en]
                                        [--whisper-bin PATH]
                                        [--models-dir DIR]

Output JSON shape:
    {
      "language": "en",
      "model": "base.en",
      "duration_s": 67.34,
      "segments": [
        {"start_s": 0.0, "end_s": 3.2, "text": "Hello there.",
         "words": [{"start_s": 0.0, "end_s": 0.4, "text": "Hello"}, ...]},
        ...
      ]
    }

Requires: `whisper-cli` (whisper.cpp) on PATH, plus a ggml model file.
On macOS: `brew install whisper-cpp`. Models can be fetched with
`whisper-cli --model-download base.en` (or copy from a Remotion install).
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def find_whisper_bin(explicit):
    if explicit:
        if Path(explicit).is_file() and os.access(explicit, os.X_OK):
            return explicit
        raise SystemExit(f"whisper binary not found or not executable: {explicit}")
    for name in ("whisper-cli", "whisper-cpp", "main"):
        found = shutil.which(name)
        if found:
            return found
    raise SystemExit(
        "whisper.cpp not on PATH. Install with `brew install whisper-cpp` "
        "or pass --whisper-bin pointing to the compiled binary."
    )


def find_model(name, models_dir):
    """Resolve a model name to a ggml file path.

    Lookup order:
      1. <models_dir>/ggml-<name>.bin (if --models-dir given)
      2. ~/.cache/whisper.cpp/ggml-<name>.bin
      3. /opt/homebrew/share/whisper-cpp/ggml-<name>.bin (Apple silicon brew)
      4. /usr/local/share/whisper-cpp/ggml-<name>.bin (Intel brew)
    """
    candidates = []
    if models_dir:
        candidates.append(Path(models_dir) / f"ggml-{name}.bin")
    candidates += [
        Path.home() / ".cache" / "whisper.cpp" / f"ggml-{name}.bin",
        Path("/opt/homebrew/share/whisper-cpp") / f"ggml-{name}.bin",
        Path("/usr/local/share/whisper-cpp") / f"ggml-{name}.bin",
    ]
    for c in candidates:
        if c.is_file():
            return c
    raise SystemExit(
        f"ggml-{name}.bin not found. Searched:\n  "
        + "\n  ".join(str(c) for c in candidates)
        + "\nDownload with `whisper-cli --model-download "
        + name
        + "` or pass --models-dir."
    )


def run_whisper(bin_path, audio, model_path, language, work_dir):
    """Invoke whisper.cpp to produce a JSON sidecar with word-level timing.

    whisper.cpp's `--output-json-full` writes a `<audio>.json` next to a
    chosen `--output-file` stem. We capture that and reshape it into our
    schema below.
    """
    stem = work_dir / "transcript"
    cmd = [
        bin_path,
        "--model", str(model_path),
        "--file", str(audio),
        "--language", language,
        "--output-file", str(stem),
        "--output-json-full",
        "--print-progress",
    ]
    subprocess.run(cmd, check=True)
    json_path = Path(str(stem) + ".json")
    if not json_path.is_file():
        raise SystemExit(f"whisper did not produce {json_path}")
    return json_path


def reshape(raw):
    """Convert whisper.cpp JSON to our compact schema.

    whisper.cpp emits `transcription` (segments) with `tokens` carrying
    per-token `t0`/`t1` in centiseconds. We aggregate tokens into words
    by dropping leading-space markers and merging trailing punctuation.
    """
    segments_out = []
    for seg in raw.get("transcription", []):
        seg_text = (seg.get("text") or "").strip()
        seg_start = seg.get("offsets", {}).get("from")
        seg_end = seg.get("offsets", {}).get("to")
        words = []
        cur = None
        for tok in seg.get("tokens", []):
            text = tok.get("text", "")
            # whisper.cpp marks special tokens (timestamps, BOS, etc.) — skip.
            if text.startswith("[_") or text.startswith("<|"):
                continue
            t0 = tok.get("offsets", {}).get("from")
            t1 = tok.get("offsets", {}).get("to")
            starts_word = text.startswith(" ") or cur is None
            stripped = text.lstrip()
            if not stripped:
                continue
            if starts_word:
                if cur is not None:
                    words.append(cur)
                cur = {
                    "start_s": (t0 / 1000.0) if t0 is not None else None,
                    "end_s": (t1 / 1000.0) if t1 is not None else None,
                    "text": stripped,
                }
            else:
                cur["text"] += stripped
                if t1 is not None:
                    cur["end_s"] = t1 / 1000.0
        if cur is not None:
            words.append(cur)
        segments_out.append({
            "start_s": (seg_start / 1000.0) if seg_start is not None else None,
            "end_s": (seg_end / 1000.0) if seg_end is not None else None,
            "text": seg_text,
            "words": words,
        })
    duration = 0.0
    if segments_out and segments_out[-1]["end_s"] is not None:
        duration = round(segments_out[-1]["end_s"], 3)
    return {
        "language": raw.get("result", {}).get("language") or "en",
        "model": raw.get("model", {}).get("type"),
        "duration_s": duration,
        "segments": segments_out,
    }


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("audio", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--model", default="base.en")
    ap.add_argument("--language", default="en")
    ap.add_argument("--whisper-bin", default=None)
    ap.add_argument("--models-dir", default=None)
    args = ap.parse_args(argv)

    if not args.audio.is_file():
        raise SystemExit(f"not a file: {args.audio}")

    bin_path = find_whisper_bin(args.whisper_bin)
    model_path = find_model(args.model, args.models_dir)

    work_dir = args.output.parent
    work_dir.mkdir(parents=True, exist_ok=True)
    raw_json_path = run_whisper(bin_path, args.audio, model_path, args.language, work_dir)
    raw = json.loads(raw_json_path.read_text(encoding="utf-8"))
    shaped = reshape(raw)
    shaped["model"] = shaped["model"] or args.model

    args.output.write_text(json.dumps(shaped, indent=2) + "\n", encoding="utf-8")
    print(str(args.output))


if __name__ == "__main__":
    main(sys.argv[1:])
