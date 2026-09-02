#!/usr/bin/env bash
# SessionEnd friction check. Reads hook JSON on stdin, prints a reminder if the
# session is substantial. Never errors the session: any problem -> silent exit 0.
# Usage: echo '{"transcript_path":"..."}' | friction-scan.sh
set -u
here="$(cd "$(dirname "$0")" && pwd)"
config="$here/../config.json"

# Read stdin into a variable (bash heredocs consume piped input)
hook_json="$(cat)"

python3 - "$config" "$hook_json" <<'PY'
import json, sys, os

config_path = sys.argv[1]
hook_json = sys.argv[2]

try:
    with open(config_path) as fh:
        threshold = int(json.load(fh).get("friction_word_threshold", 1000))
except Exception:
    threshold = 1000

try:
    hook = json.loads(hook_json)
    tpath = hook.get("transcript_path", "")
except Exception:
    sys.exit(0)

if not tpath or not os.path.isfile(tpath):
    sys.exit(0)

def text_of(content):
    # content may be a string or a list of block dicts.
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict) and isinstance(b.get("text"), str):
                parts.append(b["text"])
        return " ".join(parts)
    return ""

words = 0
try:
    with open(tpath) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            msg = obj.get("message") or {}
            words += len(text_of(msg.get("content", "")).split())
except Exception:
    sys.exit(0)

if words >= threshold:
    print("[toolsmith] This session looked substantial (%d words). "
          "Worth a /crystallize before you go?" % words)
PY
