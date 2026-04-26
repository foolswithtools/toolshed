#!/usr/bin/env bash
# Fails if any committed file (other than CLAUDE.md, which describes the rule)
# places "anthropic" and "remotion" (or "remotion-dev") within 3 lines of each
# other — i.e. anywhere a reader could plausibly link the two concepts.
#
# Run before every push:
#     bash scripts/check-no-anthropic-remotion-claim.sh

set -euo pipefail

cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"

WINDOW=3
violations=0

# All tracked files except CLAUDE.md and this script itself — both intentionally
# describe the rule and would otherwise trip it.
# Skip binary files (cheap mime heuristic below).
self_path="scripts/check-no-anthropic-remotion-claim.sh"
mapfile -t files < <(git ls-files | grep -v -x -e 'CLAUDE.md' -e "$self_path" || true)

for f in "${files[@]}"; do
  [ -f "$f" ] || continue
  # Skip non-text files (cheap heuristic).
  if file -b --mime "$f" | grep -qv 'charset=binary'; then
    :
  else
    continue
  fi

  # awk scans the file once; for each line it strips "safe tokens" (project /
  # repo / profile names that legitimately contain the words but are not claims
  # about the company), then looks for the remaining bare references. The rule
  # is about "Anthropic-the-company uses Remotion-the-tool" — not about our
  # profile named anthropic-brand or our plugin named remotion-video.
  output=$(awk -v window="$WINDOW" '
    function clean(s) {
      # Strip known safe tokens before checking proximity.
      gsub(/anthropic-brand/, "", s)
      gsub(/anthropics\/skills/, "", s)
      gsub(/anthropics\//, "", s)
      gsub(/remotion-video/, "", s)
      return s
    }
    BEGIN { last_a = -10000; last_r = -10000 }
    {
      line = clean(tolower($0))
      has_a = index(line, "anthropic") > 0
      # plain "remotion" covers "remotion-dev" too (it is a substring).
      has_r = index(line, "remotion") > 0
      if (has_a) last_a = NR
      if (has_r) last_r = NR
      if (has_a && (NR - last_r) <= window && last_r > 0) {
        printf "%d: anthropic near remotion (last remotion: line %d): %s\n", NR, last_r, $0
      } else if (has_r && (NR - last_a) <= window && last_a > 0) {
        printf "%d: remotion near anthropic (last anthropic: line %d): %s\n", NR, last_a, $0
      }
    }
  ' "$f" || true)

  if [ -n "$output" ]; then
    echo "VIOLATION in $f:"
    echo "$output" | sed 's/^/  /'
    echo
    violations=$((violations + 1))
  fi
done

if [ "$violations" -gt 0 ]; then
  echo "Found $violations file(s) with potential anthropic/remotion proximity claims." >&2
  echo "If the co-occurrence is genuinely about something other than 'Anthropic uses Remotion', rewrite to keep the words far apart and unambiguous." >&2
  exit 1
fi

echo "OK: no anthropic/remotion proximity claims found in committed files."
