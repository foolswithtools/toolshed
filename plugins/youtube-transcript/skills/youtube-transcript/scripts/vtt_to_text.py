#!/usr/bin/env python3
"""Convert a WebVTT subtitle file to clean plain text.

Strips: WEBVTT header, NOTE/STYLE/REGION blocks, cue id lines,
timestamp lines, inline tags (<...>), HTML entities like &nbsp;.
Collapses consecutive duplicates and rolling-prefix duplicates
(YouTube auto-subs: each cue contains the previous cue's text
plus a few new words).

Usage: vtt_to_text.py <path/to/file.vtt>
Writes <same-stem>.txt next to the input, UTF-8.
"""

import re
import sys
from pathlib import Path

TIMESTAMP_RE = re.compile(
    r"^\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}"
)
INLINE_TAG_RE = re.compile(r"<[^>]+>")
ENTITY_MAP = {
    "&nbsp;": " ", "&amp;": "&", "&lt;": "<",
    "&gt;": ">", "&quot;": '"', "&#39;": "'",
}


def strip_entities(s):
    for k, v in ENTITY_MAP.items():
        s = s.replace(k, v)
    return s


def is_cue_id(line):
    s = line.strip()
    if not s:
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9_\-]+", s)) and len(s) <= 40


def parse_cues(vtt_text):
    lines = vtt_text.splitlines()
    i, n = 0, len(lines)

    if i < n and lines[i].lstrip("﻿").startswith("WEBVTT"):
        i += 1
        while i < n and lines[i].strip() != "":
            i += 1

    while i < n:
        while i < n and lines[i].strip() == "":
            i += 1
        if i >= n:
            break

        head = lines[i].strip()
        if head.startswith(("NOTE", "STYLE", "REGION")):
            i += 1
            while i < n and lines[i].strip() != "":
                i += 1
            continue

        if "-->" not in lines[i]:
            if is_cue_id(lines[i]):
                i += 1
            else:
                i += 1
                continue

        if i < n and TIMESTAMP_RE.match(lines[i].strip()):
            i += 1
        else:
            while i < n and lines[i].strip() != "":
                i += 1
            continue

        while i < n and lines[i].strip() != "":
            cleaned = strip_entities(INLINE_TAG_RE.sub("", lines[i])).strip()
            if cleaned:
                yield cleaned
            i += 1


def dedupe(lines):
    out, prev = [], ""
    for line in lines:
        if not line or line == prev:
            continue
        if prev and line.startswith(prev):
            suffix = line[len(prev):].strip()
            if suffix:
                out.append(suffix)
            prev = line
            continue
        out.append(line)
        prev = line
    return out


def main(argv):
    if len(argv) != 2:
        print("usage: vtt_to_text.py <file.vtt>", file=sys.stderr)
        return 2
    in_path = Path(argv[1])
    if not in_path.is_file():
        print(f"not a file: {in_path}", file=sys.stderr)
        return 1
    text = in_path.read_text(encoding="utf-8", errors="replace")
    cleaned = dedupe(list(parse_cues(text)))
    out_path = in_path.with_suffix(".txt")
    out_path.write_text("\n".join(cleaned) + "\n", encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
