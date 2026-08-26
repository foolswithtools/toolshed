#!/usr/bin/env bash
# Link check for the pdlc-build plugin.
#
# Proves that no reference in any skill, command, or prompt file points
# outside the plugin root:
#   1. Every ${CLAUDE_PLUGIN_ROOT}/... path mentioned in skills/, commands/,
#      prompts/, and README.md resolves to a file that ships in the plugin.
#   2. No skill, command, or prompt file carries a parent-directory escape (../).
#   3. Every markdown link target that looks like a local path exists under
#      the plugin root.
#
# Exit 0 when clean; exit 1 with a finding list otherwise.

set -u
plugin_root="$(cd "$(dirname "$0")/.." && pwd)"
fail=0
note() { echo "FINDING: $*"; fail=1; }

dirs=""
for d in skills commands prompts; do
  [ -d "$plugin_root/$d" ] && dirs="$dirs $plugin_root/$d"
done
files=$(find $dirs -name '*.md' 2>/dev/null; echo "$plugin_root/README.md")

# 1. ${CLAUDE_PLUGIN_ROOT}/... references must resolve inside the plugin.
while IFS=: read -r file ref; do
  [ -z "$ref" ] && continue
  rel="${ref#\$\{CLAUDE_PLUGIN_ROOT\}/}"
  if [ ! -e "$plugin_root/$rel" ]; then
    note "$file references \${CLAUDE_PLUGIN_ROOT}/$rel which does not ship in the plugin"
  fi
done < <(echo "$files" | xargs grep -o '\${CLAUDE_PLUGIN_ROOT}/[A-Za-z0-9_./-]*' /dev/null 2>/dev/null | sed 's/:\(.*\)/:\1/')

# 2. Parent-directory escapes anywhere in shipped markdown.
while IFS= read -r hit; do
  note "parent-directory escape: $hit"
done < <(echo "$files" | xargs grep -n '\.\./' /dev/null 2>/dev/null)

# 3. Markdown link targets that look like local paths must exist.
while IFS=: read -r file target; do
  [ -z "$target" ] && continue
  case "$target" in
    http://*|https://*|\#*) continue ;;
  esac
  base="$(dirname "$file")"
  if [ ! -e "$base/$target" ] && [ ! -e "$plugin_root/$target" ]; then
    note "$file links to $target which does not exist in the plugin"
  fi
done < <(echo "$files" | xargs grep -o '](\([^)#][^)]*\))' /dev/null 2>/dev/null \
  | sed 's/:](\(.*\))$/:\1/')

if [ "$fail" -eq 0 ]; then
  echo "OK: all skill/command/prompt references resolve inside $plugin_root"
fi
exit "$fail"
