#!/usr/bin/env python3
"""List the ElevenLabs voices this API key can use, cross-referenced with which
brand themes already reference each voice.

Ergonomics helper for picking per-theme voices/alternates (Slice A). It does not
spend TTS credits — it only calls GET /v1/voices (and refreshes the name→id
cache as a side benefit).

Usage:
    list_voices.py [--project DIR] [--json] [options]

    --project DIR   scan DIR/src/brand/profiles/*/style-guide.ts for `tts`
                    blocks and show which themes use each voice (as default or
                    alternate). Omit to just list account voices.
    --cache PATH    voice name→id cache to refresh (default as script_to_audio)
    --envrc PATH    extra dotenv file to search for the token (repeatable)
    --secrets PATH  plugin-scoped secrets file
    --json          emit JSON instead of a table

Token handling is identical to script_to_audio.py (never echoed).
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from script_to_audio import (
    DEFAULT_CACHE,
    DEFAULT_SECRETS,
    alias_map,
    fetch_voices,
    load_cache,
    resolve_api_key,
    save_cache,
)

# Match `voice: "Name"` and the strings inside an `alternates: [...]` array.
_VOICE_RE = re.compile(r'\bvoice\s*:\s*["\']([^"\']+)["\']')
_ALTERNATES_RE = re.compile(r"\balternates\s*:\s*\[([^\]]*)\]", re.DOTALL)
_STR_RE = re.compile(r'["\']([^"\']+)["\']')


def scan_theme_voices(project):
    """Return {voice_name_lower: [(theme, role), ...]} from a project's profiles.

    role is "default" (the theme's `voice`) or "alternate". Best-effort regex —
    style-guide.ts is TypeScript, not JSON, so we don't fully parse it.
    """
    out = {}
    profiles = Path(project) / "src" / "brand" / "profiles"
    if not profiles.is_dir():
        return out
    for sg in sorted(profiles.glob("*/style-guide.ts")):
        theme = sg.parent.name
        text = sg.read_text(encoding="utf-8")
        m = _VOICE_RE.search(text)
        if m:
            out.setdefault(m.group(1).lower(), []).append((theme, "default"))
        alt = _ALTERNATES_RE.search(text)
        if alt:
            for name in _STR_RE.findall(alt.group(1)):
                out.setdefault(name.lower(), []).append((theme, "alternate"))
    return out


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", type=Path, default=None)
    ap.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    ap.add_argument("--envrc", type=Path, action="append", default=None)
    ap.add_argument("--secrets", type=Path, default=DEFAULT_SECRETS)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    api_key = resolve_api_key(envrc_paths=args.envrc, secrets_path=args.secrets)
    voices = fetch_voices(api_key)

    # Refresh the cache as a side benefit (full + short-name aliases).
    cache = load_cache(args.cache)
    for k, v in alias_map(voices).items():
        cache[k] = v
    save_cache(args.cache, cache)

    theme_map = scan_theme_voices(args.project) if args.project else {}

    rows = []
    for v in sorted(voices, key=lambda x: x["name"].lower()):
        themes = theme_map.get(v["name"].lower(), [])
        rows.append({
            "name": v["name"],
            "voice_id": v["voice_id"],
            "themes": [{"theme": t, "role": r} for t, r in themes],
        })

    if args.json:
        print(json.dumps(rows, indent=2))
        return

    if not rows:
        print("(no voices on this account)")
        return
    name_w = max(len(r["name"]) for r in rows)
    for r in rows:
        used = ", ".join(f"{t['theme']}({t['role']})" for t in r["themes"]) or "-"
        print(f"{r['name']:<{name_w}}  {r['voice_id']:<24}  {used}")


if __name__ == "__main__":
    main(sys.argv[1:])
