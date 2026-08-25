#!/usr/bin/env bash
# Public-hygiene sweep for the pdlc-define plugin.
#
# toolshed is a public repo. This script proves that no file under the
# plugin tree contains any of a set of banned strings (private project
# names, client or company references, private repo slugs, anything
# owner-identifying beyond the public author block).
#
# By design the banned strings are NOT committed to this repo. They are
# supplied at run time as a deny-list file, one string per line (blank
# lines and lines starting with # are ignored, matching is a plain
# case-insensitive substring search). This script itself names nothing
# private; it is safe to ship.
#
# Usage:
#   PDLC_DEFINE_HYGIENE_DENYLIST=/path/to/denylist.env \
#     bash check-public-hygiene.sh [plugin_root]
# or:
#   bash check-public-hygiene.sh [plugin_root] --denylist /path/to/denylist.env
#
# plugin_root defaults to the directory this script's parent lives in
# (i.e. the pdlc-define plugin root when run from scripts/).
#
# Exit 0 when the deny-list file itself is clean and zero hits are found
# across the swept tree. Exit 1 with a finding list otherwise. Exit 2 on
# a usage error (no deny-list supplied, or the deny-list file is missing).

set -u

denylist="${PDLC_DEFINE_HYGIENE_DENYLIST:-}"
plugin_root=""

while [ $# -gt 0 ]; do
  case "$1" in
    --denylist)
      denylist="$2"
      shift 2
      ;;
    *)
      plugin_root="$1"
      shift
      ;;
  esac
done

if [ -z "$plugin_root" ]; then
  plugin_root="$(cd "$(dirname "$0")/.." && pwd)"
fi

if [ -z "$denylist" ]; then
  echo "usage: PDLC_DEFINE_HYGIENE_DENYLIST=<path> $0 [plugin_root]" >&2
  echo "   or: $0 [plugin_root] --denylist <path>" >&2
  echo "no deny-list file supplied; refusing to run a no-op sweep" >&2
  exit 2
fi

if [ ! -f "$denylist" ]; then
  echo "deny-list file not found: $denylist" >&2
  exit 2
fi

fail=0
hits=0

# Read the deny-list, skipping blanks and comments.
terms=()
while IFS= read -r line; do
  trimmed="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [ -z "$trimmed" ] && continue
  case "$trimmed" in
    \#*) continue ;;
  esac
  terms+=("$trimmed")
done < "$denylist"

if [ "${#terms[@]}" -eq 0 ]; then
  echo "deny-list file has no active terms: $denylist" >&2
  exit 2
fi

echo "sweeping $plugin_root against ${#terms[@]} deny-list term(s) from $denylist"

for term in "${terms[@]}"; do
  matches=$(grep -rniF "$term" "$plugin_root" 2>/dev/null)
  if [ -n "$matches" ]; then
    fail=1
    while IFS= read -r m; do
      hits=$((hits + 1))
      echo "FINDING: banned term matched: $m"
    done <<< "$matches"
  fi
done

# The deny-list file itself must not leak into the swept tree verbatim as
# a file (belt-and-suspenders: it must live outside plugin_root).
case "$denylist" in
  "$plugin_root"/*)
    fail=1
    echo "FINDING: deny-list file lives inside the swept plugin tree: $denylist"
    ;;
esac

if [ "$fail" -eq 0 ]; then
  echo "OK: zero hits for ${#terms[@]} deny-list term(s) across $plugin_root"
else
  echo "$hits finding(s)."
fi

exit "$fail"
