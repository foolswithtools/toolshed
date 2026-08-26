#!/usr/bin/env bash
# Duplicate-surface check for the pdlc-build plugin (issue #21 acceptance
# criteria: no file duplication between the pi surface and the Claude Code
# surface; hygiene check per #18). The two harnesses share one core: skills/
# and prompts/ live once under this plugin, and the pi manifest (package.json's
# "pi" key) must point straight at them rather than at a copy.
#
# Proves three things:
#   1. The pi manifest's skills/prompts entries are exactly the shared
#      ./skills and ./prompts directories, not some pi-only path.
#   2. No file under the plugin tree is byte-identical to a file already
#      shipped under skills/ or prompts/ (a checksum match outside those two
#      directories means something got copied instead of referenced).
#   3. Extension for pdlc-build's dual-harness shape: every Claude Code command
#      under commands/ is a thin wrapper that references its shared procedure
#      under ${CLAUDE_PLUGIN_ROOT}/prompts/, so the action logic lives once in
#      the shared core and is not reimplemented per harness.
#
# Usage: check-no-pi-duplication.sh [plugin_root]
# plugin_root defaults to this script's parent directory's parent (the
# pdlc-build plugin root when run from scripts/).
#
# Exit 0 when clean; exit 1 with a finding list otherwise; exit 2 on a usage
# error (manifest missing or unreadable).

set -u

plugin_root="${1:-}"
if [ -z "$plugin_root" ]; then
  plugin_root="$(cd "$(dirname "$0")/.." && pwd)"
fi

manifest="$plugin_root/package.json"
if [ ! -f "$manifest" ]; then
  echo "pi manifest not found: $manifest" >&2
  exit 2
fi

fail=0

# 1. Manifest must reference the shared directories verbatim.
manifest_check=$(node -e '
  const fs = require("node:fs");
  const m = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
  const skills = (m.pi && m.pi.skills) || [];
  const prompts = (m.pi && m.pi.prompts) || [];
  const extra = [
    ...skills.filter((p) => p !== "./skills"),
    ...prompts.filter((p) => p !== "./prompts"),
  ];
  if (skills.length !== 1 || prompts.length !== 1 || extra.length > 0) {
    process.stdout.write("FINDING: pi manifest skills/prompts must be exactly [\"./skills\"] and [\"./prompts\"], got skills=" + JSON.stringify(skills) + " prompts=" + JSON.stringify(prompts));
    process.exit(1);
  }
' "$manifest" 2>&1)
manifest_status=$?
if [ "$manifest_status" -ne 0 ]; then
  fail=1
  echo "$manifest_check"
fi

# 2. Checksum sweep: nothing outside skills/ or prompts/ may duplicate a file
#    already shipped inside them.
shared_sums="$(mktemp)"
trap 'rm -f "$shared_sums"' EXIT

find "$plugin_root/skills" "$plugin_root/prompts" -type f 2>/dev/null \
  | xargs -r shasum -a 256 \
  | awk '{print $1}' | sort -u > "$shared_sums"

while IFS= read -r -d '' file; do
  case "$file" in
    "$plugin_root/skills/"*|"$plugin_root/prompts/"*) continue ;;
  esac
  sum=$(shasum -a 256 "$file" | awk '{print $1}')
  if grep -qx "$sum" "$shared_sums"; then
    fail=1
    echo "FINDING: $file duplicates content already shipped under skills/ or prompts/"
  fi
done < <(find "$plugin_root" -type f -not -path "*/.git/*" -print0)

# 3. Every command under commands/ must reference a shared procedure under
#    prompts/, proving it wraps the shared core rather than reimplementing it.
if [ -d "$plugin_root/commands" ]; then
  while IFS= read -r cmd; do
    if ! grep -q '${CLAUDE_PLUGIN_ROOT}/prompts/' "$cmd"; then
      fail=1
      echo "FINDING: $cmd does not reference a shared procedure under \${CLAUDE_PLUGIN_ROOT}/prompts/ (a command must wrap the shared core, not reimplement it)"
    fi
  done < <(find "$plugin_root/commands" -name '*.md')
fi

if [ "$fail" -eq 0 ]; then
  echo "OK: pi manifest references the shared skills/ and prompts/ directories, no duplicate files, and every command wraps a shared procedure under $plugin_root"
fi

exit "$fail"
