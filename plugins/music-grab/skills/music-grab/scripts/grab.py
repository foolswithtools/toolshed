#!/usr/bin/env python3
"""Grab audio from a URL and append a CREDITS.md stanza.

Wraps yt-dlp twice: first a metadata probe, then an audio extraction.
Searches the source page description for license-phrase evidence,
captures the surrounding context, writes the credits file, and prints
the final audio path on the last line of stdout.

The skill expects the script to be the source of truth for slug
generation, license-phrase matching, and credits-file format —
keeping these in one place makes the credits log reproducible across
runs.

Usage:
    grab.py <URL> \\
        --output-dir <dir> \\
        --audio-format mp3 \\
        --audio-quality 0 \\
        --credits-file CREDITS.md \\
        [--phrase "creative commons" --phrase "royalty free" ...]
"""

import argparse
import datetime as dt
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path


SLUG_BAD_CHARS = re.compile(r"[^a-z0-9]+")
SAFE_FIELD_SEP = "|||"
PROBE_FIELDS = [
    "uploader",
    "title",
    "id",
    "duration",
    "license",
    "description",
]


def slugify(value: str, max_len: int = 80) -> str:
    if not value:
        return "unknown"
    s = value.strip().lower()
    s = SLUG_BAD_CHARS.sub("-", s)
    s = s.strip("-")
    if not s:
        return "unknown"
    return s[:max_len].rstrip("-")


def probe(url: str) -> dict:
    fmt = SAFE_FIELD_SEP.join(f"%({f})s" for f in PROBE_FIELDS)
    cmd = ["yt-dlp", "--print", fmt, "--skip-download", "--no-playlist", url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        sys.exit(result.returncode)
    parts = result.stdout.strip().split(SAFE_FIELD_SEP)
    while len(parts) < len(PROBE_FIELDS):
        parts.append("")
    return dict(zip(PROBE_FIELDS, parts))


def find_license_evidence(description: str, license_field: str, phrases: list[str]) -> dict:
    haystack_parts = [description or "", license_field or ""]
    haystack = "\n".join(haystack_parts)
    haystack_lower = haystack.lower()

    matched_phrase = None
    matched_pos = -1
    for phrase in phrases:
        idx = haystack_lower.find(phrase.lower())
        if idx >= 0 and (matched_pos < 0 or idx < matched_pos):
            matched_phrase = phrase
            matched_pos = idx

    if matched_phrase is None:
        excerpt = haystack[:200].strip()
        return {
            "matched": False,
            "phrase": None,
            "excerpt": excerpt or "(source page returned no description text)",
        }

    start = max(0, matched_pos - 80)
    end = min(len(haystack), matched_pos + len(matched_phrase) + 120)
    excerpt = haystack[start:end].replace("\n", " ").strip()
    return {"matched": True, "phrase": matched_phrase, "excerpt": excerpt}


def find_attribution(description: str) -> str:
    if not description:
        return ""
    desc_lower = description.lower()
    triggers = [
        "attribution required",
        "credit @",
        "credit the artist",
        "credit:",
        "please credit",
        "include link",
        "please link",
        "must credit",
    ]
    for t in triggers:
        idx = desc_lower.find(t)
        if idx >= 0:
            start = max(0, idx - 20)
            end = min(len(description), idx + len(t) + 100)
            return description[start:end].replace("\n", " ").strip()
    return ""


def pick_unique_path(directory: Path, base: str, ext: str) -> Path:
    candidate = directory / f"{base}.{ext}"
    if not candidate.exists():
        return candidate
    for i in range(2, 11):
        candidate = directory / f"{base}-{i}.{ext}"
        if not candidate.exists():
            return candidate
    sys.stderr.write(
        f"Refusing to grab — already 10 collisions for slug '{base}' in {directory}.\n"
        "Check CREDITS.md; the track is probably already there.\n"
    )
    sys.exit(2)


def download(url: str, output_template: str, audio_format: str, audio_quality: str) -> None:
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", audio_format,
        "--audio-quality", str(audio_quality),
        "--no-playlist",
        "--output", output_template,
        url,
    ]
    sys.stderr.write(f"$ {shlex.join(cmd)}\n")
    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        sys.exit(result.returncode)


def append_credits(
    credits_path: Path,
    slug_base: str,
    audio_path: Path,
    url: str,
    meta: dict,
    license_info: dict,
    attribution_text: str,
) -> None:
    today = dt.date.today().isoformat()
    duration = meta.get("duration", "") or "unknown"

    if license_info["matched"]:
        license_evidence = license_info["phrase"]
        attribution_label = "yes" if attribution_text else "unclear"
    else:
        license_evidence = "none found — user-verified"
        attribution_label = "unknown — user-verified"

    if not credits_path.exists():
        credits_path.write_text("# Music credits\n\n", encoding="utf-8")

    stanza = (
        f"## {slug_base}\n\n"
        f"- File: `{audio_path.name}`\n"
        f"- Source: {url}\n"
        f"- Uploader / artist: {meta.get('uploader') or 'unknown'}\n"
        f"- Title: {meta.get('title') or 'unknown'}\n"
        f"- Duration: {duration}s\n"
        f"- Grabbed: {today}\n"
        f"- License evidence: {license_evidence}\n"
        f"- Attribution required: {attribution_label}"
        + (f" — {attribution_text}" if attribution_text else "")
        + "\n"
        f"- License context (excerpt): \"{license_info['excerpt']}\"\n\n"
    )
    with credits_path.open("a", encoding="utf-8") as f:
        f.write(stanza)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("url")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--audio-format", default="mp3")
    p.add_argument("--audio-quality", default="0")
    p.add_argument("--credits-file", default="CREDITS.md")
    p.add_argument(
        "--phrase",
        action="append",
        default=[],
        help="License phrase to search for (case-insensitive). Repeatable.",
    )
    args = p.parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    meta = probe(args.url)

    slug_base = f"{slugify(meta.get('uploader', ''))}-{slugify(meta.get('title', ''))}"
    slug_base = slug_base.strip("-") or "unknown-track"

    audio_path = pick_unique_path(output_dir, slug_base, args.audio_format)
    output_template = str(audio_path.with_suffix("")) + ".%(ext)s"

    download(args.url, output_template, args.audio_format, args.audio_quality)

    if not audio_path.exists():
        for alt in output_dir.glob(f"{audio_path.stem}.*"):
            if alt.suffix.lower() in {".mp3", ".m4a", ".wav", ".opus", ".aac", ".flac"}:
                audio_path = alt
                break

    if not audio_path.exists():
        sys.stderr.write(
            "yt-dlp finished but the expected audio file is not on disk.\n"
            f"Checked: {audio_path}\n"
        )
        return 3

    license_info = find_license_evidence(
        meta.get("description", ""),
        meta.get("license", ""),
        args.phrase or [],
    )
    attribution_text = find_attribution(meta.get("description", ""))

    credits_path = output_dir / args.credits_file
    append_credits(
        credits_path,
        slug_base,
        audio_path,
        args.url,
        meta,
        license_info,
        attribution_text,
    )

    summary = {
        "audio_path": str(audio_path),
        "credits_path": str(credits_path),
        "license_matched": license_info["matched"],
        "license_phrase": license_info["phrase"],
        "attribution_text": attribution_text,
        "uploader": meta.get("uploader") or "",
        "title": meta.get("title") or "",
    }
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
