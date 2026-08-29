#!/usr/bin/env bash
set -u
here="$(cd "$(dirname "$0")" && pwd)"
script="$here/../scripts/friction-scan.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# A transcript with ~12 words of text: below the 1000-word threshold.
short_t="$tmp/short.jsonl"
printf '%s\n' '{"type":"user","message":{"content":"one two three four five"}}' \
              '{"type":"assistant","message":{"content":"six seven eight nine ten eleven twelve"}}' > "$short_t"
out_short="$(printf '{"transcript_path":"%s"}' "$short_t" | bash "$script")"; rc=$?
[ "$rc" -eq 0 ] || { echo "FAIL: nonzero exit ($rc) below threshold"; exit 1; }
[ -z "$out_short" ] || { echo "FAIL: fired below threshold"; exit 1; }

# A transcript with >1000 words: should fire.
long_t="$tmp/long.jsonl"
words="$(python3 -c 'print("word " * 1200)')"
python3 - "$long_t" "$words" <<'PY'
import json, sys
path, words = sys.argv[1], sys.argv[2]
with open(path, "w") as fh:
    fh.write(json.dumps({"type":"assistant","message":{"content":words}}) + "\n")
PY
out_long="$(printf '{"transcript_path":"%s"}' "$long_t" | bash "$script")"; rc=$?
[ "$rc" -eq 0 ] || { echo "FAIL: nonzero exit ($rc) above threshold"; exit 1; }
echo "$out_long" | grep -q "crystallize" || { echo "FAIL: did not fire above threshold"; exit 1; }

# Missing transcript: silent, exit 0.
out_missing="$(printf '{"transcript_path":"%s/nope.jsonl"}' "$tmp" | bash "$script")"; rc=$?
[ "$rc" -eq 0 ] || { echo "FAIL: nonzero exit ($rc) on missing transcript"; exit 1; }
[ -z "$out_missing" ] || { echo "FAIL: output on missing transcript"; exit 1; }

# Malformed JSON on stdin: silent, exit 0.
out_malformed="$(printf '{"broken' | bash "$script")"; rc=$?
[ "$rc" -eq 0 ] || { echo "FAIL: nonzero exit ($rc) on malformed JSON"; exit 1; }
[ -z "$out_malformed" ] || { echo "FAIL: output on malformed JSON"; exit 1; }

echo "PASS"
