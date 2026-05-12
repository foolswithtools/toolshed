#!/usr/bin/env python3
"""List ElevenLabs voices and cache the name -> voice_id mapping.

Usage:
    list_voices.py [--refresh] [--json]

Reads the ElevenLabs API key the same way script_to_audio.py does
(env vars, then ~/.config/screencast-cut/secrets.env). Caches the
result at ~/.cache/screencast-cut/voices.json so future runs of
script_to_audio.py can resolve a voice name -> voice_id without
re-hitting the API.

Pass --refresh to force a fresh fetch even if the cache exists.
Pass --json to emit the raw cache contents (machine-readable).
Without --json, prints a human-readable table.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


ELEVENLABS_VOICES_URL = "https://api.elevenlabs.io/v2/voices"
CACHE_PATH = Path.home() / ".cache" / "screencast-cut" / "voices.json"


def resolve_api_key():
    for env in ("ELEVENLABS_API_TOKEN", "ELEVENLABS_API_KEY"):
        v = os.environ.get(env)
        if v:
            return v
    secrets = Path.home() / ".config" / "screencast-cut" / "secrets.env"
    if secrets.is_file():
        for raw in secrets.read_text(encoding="utf-8").splitlines():
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
    raise SystemExit(
        "ElevenLabs API key not found.\n"
        "Set ELEVENLABS_API_TOKEN in your environment, "
        "or write KEY=value into ~/.config/screencast-cut/secrets.env."
    )


def fetch_voices(api_key):
    req = urllib.request.Request(
        ELEVENLABS_VOICES_URL,
        headers={"xi-api-key": api_key, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            pass
        raise SystemExit(
            f"ElevenLabs voices fetch failed: HTTP {e.code} {e.reason}. {detail}"
        )
    except urllib.error.URLError as e:
        raise SystemExit(f"ElevenLabs voices network error: {e.reason}")

    voices = []
    for v in data.get("voices", []):
        voices.append({
            "voice_id": v.get("voice_id"),
            "name": v.get("name"),
            "category": v.get("category"),
            "labels": v.get("labels") or {},
        })
    return voices


def write_cache(voices):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"voices": voices}
    CACHE_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_cache():
    if not CACHE_PATH.is_file():
        return None
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def print_table(voices):
    if not voices:
        print("(no voices)")
        return
    width = max(len(v.get("name") or "") for v in voices)
    width = max(width, len("name"))
    print(f"{'name'.ljust(width)}  voice_id                       category")
    print(f"{'-' * width}  -----------------------------  --------")
    for v in voices:
        name = (v.get("name") or "").ljust(width)
        vid = (v.get("voice_id") or "")[:32]
        cat = v.get("category") or ""
        print(f"{name}  {vid.ljust(32)} {cat}")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refresh", action="store_true",
                    help="Force re-fetch even if the local cache exists.")
    ap.add_argument("--json", action="store_true",
                    help="Emit machine-readable JSON instead of a table.")
    args = ap.parse_args(argv)

    cache = None if args.refresh else load_cache()
    if cache is None:
        api_key = resolve_api_key()
        voices = fetch_voices(api_key)
        write_cache(voices)
    else:
        voices = cache.get("voices", [])

    if args.json:
        json.dump({"voices": voices}, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print_table(voices)
        print(f"\ncached at: {CACHE_PATH}")


if __name__ == "__main__":
    main(sys.argv[1:])
