#!/usr/bin/env python3
"""Generate narration audio from a text script via ElevenLabs.

Pipeline:
    script.txt --[ElevenLabs TTS]--> mp3 --[ffmpeg loudnorm]--> narration.wav

The output WAV is mono 16kHz so `transcribe.py` (whisper.cpp) can consume
it directly without an extra transcode step.

Usage:
    script_to_audio.py <script.txt> <output.wav>
        --voice-id <id>
        [--voice-name LABEL]
        [--model eleven_multilingual_v2]
        [--stability 0.45] [--similarity-boost 0.75] [--style 0.0]
        [--loudnorm-i -18] [--loudnorm-tp -2] [--loudnorm-lra 11]

Output WAV is written to <output.wav>. A sidecar manifest at
<output.wav>.json captures: voice, voice_id, model, characters_used,
loudnorm target, output_path. Phase 3 of SKILL.md surfaces this in the
Decisions table.

API key resolution (first one wins):
  1. ELEVENLABS_API_TOKEN env var.
  2. ELEVENLABS_API_KEY env var (common alternate name).
  3. ~/.config/screencast-cut/secrets.env (plugin-scoped fallback —
     KEY=value lines, parsed without sourcing).

If none resolve, the script exits with an actionable message and does
not echo any token-shaped string.

Requires: `ffmpeg` on PATH (loudnorm + mp3-to-wav). Python stdlib only;
the ElevenLabs HTTP call uses `urllib`, no third-party deps.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


def resolve_api_key():
    """Return the ElevenLabs API key, or raise SystemExit with a hint.

    Never echo the resolved value. Error messages must not reveal which
    source produced the key.
    """
    for env in ("ELEVENLABS_API_TOKEN", "ELEVENLABS_API_KEY"):
        v = os.environ.get(env)
        if v:
            return v

    secrets_file = Path.home() / ".config" / "screencast-cut" / "secrets.env"
    if secrets_file.is_file():
        try:
            for raw in secrets_file.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("export "):
                    line = line[len("export "):]
                if "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k in ("ELEVENLABS_API_TOKEN", "ELEVENLABS_API_KEY") and v:
                    return v
        except OSError:
            pass

    raise SystemExit(
        "ElevenLabs API key not found.\n"
        "Set ELEVENLABS_API_TOKEN in your environment, "
        "or write KEY=value into ~/.config/screencast-cut/secrets.env."
    )


def read_script(script_path):
    text = script_path.read_text(encoding="utf-8")
    paragraphs = [p.strip() for p in text.split("\n\n")]
    return "\n\n".join(p for p in paragraphs if p)


def synthesize(api_key, voice_id, model, text, voice_settings, mp3_out):
    """POST to ElevenLabs, stream MP3 bytes to disk."""
    url = ELEVENLABS_TTS_URL.format(voice_id=voice_id)
    payload = {
        "text": text,
        "model_id": model,
        "voice_settings": voice_settings,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            with mp3_out.open("wb") as f:
                while True:
                    chunk = resp.read(64 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
    except urllib.error.HTTPError as e:
        # ElevenLabs returns a JSON error body; surface it without the token.
        detail = ""
        try:
            detail = e.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            pass
        raise SystemExit(
            f"ElevenLabs TTS request failed: HTTP {e.code} {e.reason}. "
            f"Response: {detail}"
        )
    except urllib.error.URLError as e:
        raise SystemExit(f"ElevenLabs TTS network error: {e.reason}")


def loudnorm_to_wav(mp3_in, wav_out, target_i, target_tp, target_lra):
    """Single-pass loudnorm + mono 16kHz WAV (matches whisper.cpp input).

    Two-pass loudnorm is technically more accurate but the audible
    difference on a 30-second narration is negligible and a second
    ffmpeg invocation doubles wall time.
    """
    if shutil.which("ffmpeg") is None:
        raise SystemExit(
            "ffmpeg not on PATH. Install with `brew install ffmpeg`."
        )
    cmd = [
        "ffmpeg",
        "-hide_banner", "-loglevel", "error",
        "-y",
        "-i", str(mp3_in),
        "-af", f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}",
        "-ar", "16000", "-ac", "1",
        str(wav_out),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(
            f"ffmpeg loudnorm failed: {result.stderr.strip() or 'unknown error'}"
        )


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("script", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--voice-id", required=True,
                    help="ElevenLabs voice ID (canonical). Resolve names via list_voices.py.")
    ap.add_argument("--voice-name", default=None,
                    help="Human-readable voice label, recorded in the manifest.")
    ap.add_argument("--model", default="eleven_multilingual_v2")
    ap.add_argument("--stability", type=float, default=0.45)
    ap.add_argument("--similarity-boost", type=float, default=0.75)
    ap.add_argument("--style", type=float, default=0.0)
    ap.add_argument("--loudnorm-i", type=float, default=-18.0)
    ap.add_argument("--loudnorm-tp", type=float, default=-2.0)
    ap.add_argument("--loudnorm-lra", type=float, default=11.0)
    args = ap.parse_args(argv)

    if not args.script.is_file():
        raise SystemExit(f"not a file: {args.script}")
    if args.output.suffix.lower() != ".wav":
        raise SystemExit(
            f"output must end in .wav (got {args.output.suffix}). "
            "whisper.cpp consumes WAV directly."
        )

    api_key = resolve_api_key()
    text = read_script(args.script)
    if not text:
        raise SystemExit(f"script is empty after stripping whitespace: {args.script}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    voice_settings = {
        "stability": args.stability,
        "similarity_boost": args.similarity_boost,
        "style": args.style,
    }

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        mp3_path = Path(tmp.name)
    try:
        synthesize(api_key, args.voice_id, args.model, text, voice_settings, mp3_path)
        loudnorm_to_wav(
            mp3_path, args.output,
            args.loudnorm_i, args.loudnorm_tp, args.loudnorm_lra,
        )
    finally:
        mp3_path.unlink(missing_ok=True)

    manifest = {
        "voice": args.voice_name,
        "voice_id": args.voice_id,
        "model": args.model,
        "characters_used": len(text),
        "loudnorm": {
            "I": args.loudnorm_i,
            "TP": args.loudnorm_tp,
            "LRA": args.loudnorm_lra,
        },
        "voice_settings": voice_settings,
        "output_path": str(args.output.resolve()),
    }
    manifest_path = args.output.with_suffix(args.output.suffix + ".json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"audio:    {args.output}")
    print(f"manifest: {manifest_path}")
    print(f"voice:    {args.voice_name or args.voice_id} ({args.model})")
    print(f"chars:    {len(text)}")


if __name__ == "__main__":
    main(sys.argv[1:])
