#!/usr/bin/env python3
"""Turn a narration *script* (text) into a loudnormed narration WAV via TTS.

This is Slice A of the screencast-cut expansion: the user can hand the skill a
`Script:` (a .txt/.md file) instead of pre-recorded `Audio:`. We synthesize the
narration with ElevenLabs, normalize it with `ffmpeg loudnorm`, and write a
16 kHz mono `narration.wav` that drops straight into the existing audio path
(transcribe.py → Captions.tsx → render). A small JSON manifest records the
provenance (provider/voice/model/character count) for the Phase 3 Decisions
table.

Usage:
    script_to_audio.py <script.(txt|md)> <out_dir> [options]

Writes:
    <out_dir>/narration.wav            16 kHz mono, loudnormed
    <out_dir>/narration.manifest.json  provenance (validated; NO token in it)

Options (all fall back to config.json `tts_*` defaults when omitted):
    --voice NAME            human-readable voice name (resolved → id via API)
    --voice-id ID           canonical ElevenLabs voice id (wins over --voice)
    --model NAME            ElevenLabs model id
    --provider NAME         only "elevenlabs" is implemented (seam for future)
    --loudnorm JSON         '{"I":-18,"TP":-2,"LRA":11}'
    --voice-settings JSON   ElevenLabs voice_settings object
    --on-brand / --off-brand  records whether the chosen voice is on the theme
                              roster (the skill decides; default on-brand)
    --cache PATH            voice name→id cache (default ~/.cache/screencast-cut/voices.json)
    --envrc PATH            extra dotenv-style file to search for the token
                            (repeatable; searched before the built-in fallbacks)
    --secrets PATH          plugin-scoped secrets file
                            (default ~/.config/screencast-cut/secrets.env)
    --config PATH           config.json to read tts_* defaults from

API key resolution order (see resolve_api_key):
    1. $ELEVENLABS_API_TOKEN
    2. any --envrc file(s), in order
    3. ~/.envrc
    4. ~/.config/screencast-cut/secrets.env  (or --secrets)
    5. fail with an actionable message (the token value is NEVER printed)

Hard rule: the token is never echoed. We use urllib (no shell), never log the
key, and never put it in an error message or the manifest.

Requires: `ffmpeg` on PATH (loudnorm + transcode). Network access to ElevenLabs
for the actual synthesis; the unit tests mock that, and the golden render uses a
committed OWNED fixture WAV so it never calls the API.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schema_validate import validate, SchemaError

ENV_VAR = "ELEVENLABS_API_TOKEN"
API_BASE = "https://api.elevenlabs.io"
DEFAULT_CACHE = Path.home() / ".cache" / "screencast-cut" / "voices.json"
DEFAULT_SECRETS = Path.home() / ".config" / "screencast-cut" / "secrets.env"
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


# --------------------------------------------------------------------------- #
# Config defaults
# --------------------------------------------------------------------------- #
def load_config(path=None):
    """Read tts_* defaults from config.json. Missing file → empty dict."""
    p = Path(path) if path else CONFIG_PATH
    if not p.is_file():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Script reading
# --------------------------------------------------------------------------- #
def read_script(path):
    """Read a script file → a single whitespace-collapsed narration string.

    Lines are stripped and concatenated with single spaces; blank lines become
    paragraph breaks (kept as a single space so TTS reads it as one flow). The
    raw text drives `characters_used`; sentence boundaries are left to Whisper.
    """
    text = Path(path).read_text(encoding="utf-8")
    parts = [ln.strip() for ln in text.splitlines()]
    joined = " ".join(p for p in parts if p)
    return joined.strip()


# --------------------------------------------------------------------------- #
# API key resolution — NEVER echo the token
# --------------------------------------------------------------------------- #
def _parse_dotenv_value(path, key):
    """Pull a single KEY's value out of a dotenv/.envrc-style file.

    Handles `export KEY=value`, `KEY=value`, optional surrounding single/double
    quotes, inline `#` comments only when unquoted, and skips blanks/comments.
    Returns the value string, or None if absent/unreadable.
    """
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        if "=" not in line:
            continue
        name, _, val = line.partition("=")
        if name.strip() != key:
            continue
        val = val.strip()
        if val and val[0] in "\"'":
            quote = val[0]
            end = val.find(quote, 1)
            if end != -1:
                return val[1:end]
            return val[1:]
        # Unquoted: drop an inline comment.
        hash_idx = val.find(" #")
        if hash_idx != -1:
            val = val[:hash_idx]
        return val.strip()
    return None


def resolve_api_key(*, env=None, envrc_paths=None, secrets_path=None):
    """Resolve the ElevenLabs token. Returns the token string.

    Raises SystemExit with an actionable message (listing the SEARCHED paths,
    never any value) when nothing resolves.
    """
    env = os.environ if env is None else env
    val = env.get(ENV_VAR)
    if val and val.strip():
        return val.strip()

    searched = []
    candidates = list(envrc_paths or [])
    candidates.append(Path.home() / ".envrc")
    candidates.append(secrets_path or DEFAULT_SECRETS)
    for cand in candidates:
        if cand is None:
            continue
        searched.append(str(cand))
        found = _parse_dotenv_value(cand, ENV_VAR)
        if found and found.strip():
            return found.strip()

    raise SystemExit(
        f"{ENV_VAR} not set and not found in any fallback file.\n"
        f"Set it one of these ways:\n"
        f"  - export {ENV_VAR}=... in your shell/.envrc\n"
        f"  - put {ENV_VAR}=... in {secrets_path or DEFAULT_SECRETS}\n"
        f"Searched files: " + (", ".join(searched) if searched else "(none)")
    )


# --------------------------------------------------------------------------- #
# Voice name → id resolution (cached)
# --------------------------------------------------------------------------- #
def _http_json(url, *, api_key, method="GET", payload=None):
    """Minimal JSON HTTP helper over urllib. The key rides in a header and is
    never logged. Raises SystemExit with a network-shaped message on failure
    (the token is never included)."""
    headers = {"xi-api-key": api_key, "accept": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["content-type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "replace")[:500]
        except Exception:
            pass
        raise SystemExit(f"ElevenLabs API error {e.code} for {url}: {body}")
    except urllib.error.URLError as e:
        raise SystemExit(f"could not reach ElevenLabs ({url}): {e.reason}")


def fetch_voices(api_key):
    """GET /v1/voices → [{"name":..., "voice_id":...}, ...]."""
    data = _http_json(f"{API_BASE}/v1/voices", api_key=api_key)
    out = []
    for v in data.get("voices", []):
        if v.get("name") and v.get("voice_id"):
            out.append({"name": v["name"], "voice_id": v["voice_id"]})
    return out


def voice_aliases(name):
    """Lowercased lookup keys for an ElevenLabs voice name.

    The API returns descriptive names like "Rachel - Social Media Narrator",
    but themes/prompts use the bare label ("Rachel"). We index both the full
    name and the short part before " - " so either resolves.
    """
    full = name.strip().lower()
    keys = [full]
    if " - " in name:
        short = name.split(" - ", 1)[0].strip().lower()
        if short and short != full:
            keys.append(short)
    return keys


def alias_map(voices):
    """Build {lookup_key: voice_id} from a /v1/voices list, including short-name
    aliases. First voice wins on a short-name collision (full names never
    collide in practice)."""
    mapping = {}
    for v in voices:
        vid = v["voice_id"]
        for key in voice_aliases(v["name"]):
            mapping.setdefault(key, vid)
    return mapping


def load_cache(cache_path):
    try:
        return json.loads(Path(cache_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_cache(cache_path, mapping):
    p = Path(cache_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(mapping, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def resolve_voice_id(
    voice_name,
    voice_id,
    *,
    api_key,
    cache_path=DEFAULT_CACHE,
    fetch=fetch_voices,
):
    """Resolve to a canonical voice id.

    Precedence: explicit voice_id wins. Else resolve voice_name via the cache
    (no network on a hit), falling back to the API and refreshing the cache.
    A name that the account can't see raises SystemExit listing what IS visible.
    """
    if voice_id:
        return voice_id
    if not voice_name:
        return None

    keys = voice_aliases(voice_name)
    cache = load_cache(cache_path)
    for key in keys:
        if key in cache:
            return cache[key]

    voices = fetch(api_key)
    fresh = alias_map(voices)
    # Keep existing cache entries authoritative; add any new aliases.
    for k, v in fresh.items():
        cache.setdefault(k, v)
    save_cache(cache_path, cache)
    for key in keys:
        if key in cache:
            return cache[key]

    available = ", ".join(sorted(v["name"] for v in voices)) or "(none)"
    raise SystemExit(
        f'voice "{voice_name}" not found on this ElevenLabs account.\n'
        f"Available voices: {available}\n"
        f"Pass --voice-id directly, or pick a name from the list above."
    )


# --------------------------------------------------------------------------- #
# Synthesis + loudnorm
# --------------------------------------------------------------------------- #
def synthesize(text, voice_id, *, model, voice_settings, api_key):
    """POST /v1/text-to-speech/<voice_id> → MP3 bytes. Network call; mocked in
    tests. The key rides in a header (never shelled, never logged)."""
    url = f"{API_BASE}/v1/text-to-speech/{voice_id}"
    payload = {"text": text, "model_id": model}
    if voice_settings:
        payload["voice_settings"] = voice_settings
    headers = {
        "xi-api-key": api_key,
        "accept": "audio/mpeg",
        "content-type": "application/json",
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "replace")[:500]
        except Exception:
            pass
        raise SystemExit(f"ElevenLabs TTS error {e.code}: {body}")
    except urllib.error.URLError as e:
        raise SystemExit(f"could not reach ElevenLabs TTS endpoint: {e.reason}")


def mp3_to_loudnorm_wav(mp3_bytes, out_path, loudnorm):
    """Transcode MP3 bytes → a 16 kHz mono loudnormed WAV (Whisper-ready).

    16 kHz mono matches transcribe.ensure_wav's target, so the same WAV feeds
    Whisper without a second resample.
    """
    if shutil.which("ffmpeg") is None:
        raise SystemExit(
            "ffmpeg not on PATH — needed to loudnorm/transcode the narration. "
            "Install with `brew install ffmpeg`."
        )
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    af = "loudnorm=I={I}:TP={TP}:LRA={LRA}".format(**loudnorm)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tf:
        tf.write(mp3_bytes)
        tmp_mp3 = tf.name
    try:
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", tmp_mp3,
            "-af", af,
            "-ar", "16000", "-ac", "1",
            str(out_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise SystemExit(f"ffmpeg loudnorm failed:\n{result.stderr}")
    finally:
        Path(tmp_mp3).unlink(missing_ok=True)
    return out_path


# --------------------------------------------------------------------------- #
# Manifest
# --------------------------------------------------------------------------- #
def build_manifest(
    *, provider, voice, voice_id, model, characters_used, output_path,
    loudnorm=None, voice_settings=None, on_brand=True,
):
    manifest = {
        "provider": provider,
        "voice": voice,
        "voice_id": voice_id,
        "model": model,
        "characters_used": characters_used,
        "output_path": str(output_path),
        "on_brand": on_brand,
    }
    if loudnorm is not None:
        manifest["loudnorm"] = loudnorm
    if voice_settings:
        manifest["voice_settings"] = voice_settings
    validate(manifest, "narration", what="narration.manifest.json")
    return manifest


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _parse_json_opt(value, what):
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        raise SystemExit(f"--{what} is not valid JSON: {e}")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--voice", default=None)
    ap.add_argument("--voice-id", default=None)
    ap.add_argument("--model", default=None)
    ap.add_argument("--provider", default=None)
    ap.add_argument("--loudnorm", default=None)
    ap.add_argument("--voice-settings", default=None)
    ap.add_argument("--on-brand", dest="on_brand", action="store_true", default=True)
    ap.add_argument("--off-brand", dest="on_brand", action="store_false")
    ap.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    ap.add_argument("--envrc", type=Path, action="append", default=None)
    ap.add_argument("--secrets", type=Path, default=DEFAULT_SECRETS)
    ap.add_argument("--config", type=Path, default=None)
    args = ap.parse_args(argv)

    if not args.script.is_file():
        raise SystemExit(f"not a file: {args.script}")

    cfg = load_config(args.config)
    provider = args.provider or cfg.get("tts_provider", "elevenlabs")
    if provider != "elevenlabs":
        raise SystemExit(
            f"tts_provider {provider!r} is not implemented — only 'elevenlabs' "
            "is supported in this version. (The config/CLI seam exists so a "
            "future slice can add others.)"
        )

    model = args.model or cfg.get("tts_default_model", "eleven_multilingual_v2")
    loudnorm = _parse_json_opt(args.loudnorm, "loudnorm") or cfg.get(
        "tts_loudnorm", {"I": -18, "TP": -2, "LRA": 11}
    )
    voice_settings = _parse_json_opt(args.voice_settings, "voice-settings")
    if voice_settings is None:
        voice_settings = cfg.get("tts_voice_settings") or None

    text = read_script(args.script)
    if not text:
        raise SystemExit(f"script is empty after stripping: {args.script}")

    api_key = resolve_api_key(envrc_paths=args.envrc, secrets_path=args.secrets)

    voice_id = resolve_voice_id(
        args.voice, args.voice_id, api_key=api_key, cache_path=args.cache
    )
    voice_name = args.voice
    if voice_id is None:
        voice_id = cfg.get("tts_default_voice_id")
        voice_name = voice_name or cfg.get("tts_default_voice")
    if not voice_id:
        raise SystemExit(
            "no voice resolved — pass --voice-id or --voice, or set "
            "tts_default_voice_id in config.json."
        )

    mp3_bytes = synthesize(
        text, voice_id, model=model, voice_settings=voice_settings, api_key=api_key
    )

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    wav_path = out_dir / "narration.wav"
    mp3_to_loudnorm_wav(mp3_bytes, wav_path, loudnorm)

    manifest = build_manifest(
        provider=provider,
        voice=voice_name,
        voice_id=voice_id,
        model=model,
        characters_used=len(text),
        output_path=wav_path,
        loudnorm=loudnorm,
        voice_settings=voice_settings,
        on_brand=args.on_brand,
    )
    manifest_path = out_dir / "narration.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(str(wav_path))


if __name__ == "__main__":
    main(sys.argv[1:])
