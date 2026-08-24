#!/usr/bin/env bash
# Link check for the pdlc-define plugin.
#
# Proves that no reference in any skill or agent file points outside the
# plugin root:
#   1. Every ${CLAUDE_PLUGIN_ROOT}/... path mentioned in skills/, agents/,
#      prompts/, and README.md resolves to a file that ships in the plugin.
#   2. No skill or agent file carries a bare relative reference to the old
#      pattern-directory layout (prompts/... or agents/... outside a
#      ${CLAUDE_PLUGIN_ROOT} prefix) or a parent-directory escape (../).
#   3. Every markdown link target that looks like a local path exists under
#      the plugin root.
#
# Exit 0 when clean; exit 1 with a finding list otherwise.

set -u
plugin_root="$(cd "$(dirname "$0")/.." && pwd)"
fail=0
note() { echo "FINDING: $*"; fail=1; }

files=$(find "$plugin_root/skills" "$plugin_root/agents" "$plugin_root/prompts" -name '*.md'; echo "$plugin_root/README.md")

# 1. ${CLAUDE_PLUGIN_ROOT}/... references must resolve inside the plugin.
while IFS=: read -r file ref; do
  [ -z "$ref" ] && continue
  rel="${ref#\$\{CLAUDE_PLUGIN_ROOT\}/}"
  # A reference to a directory (trailing slash) or a file must exist.
  if [ ! -e "$plugin_root/$rel" ]; then
    note "$file references \${CLAUDE_PLUGIN_ROOT}/$rel which does not ship in the plugin"
  fi
done < <(echo "$files" | xargs grep -o '\${CLAUDE_PLUGIN_ROOT}/[A-Za-z0-9_./-]*' /dev/null 2>/dev/null | sed 's/:\(.*\)/:\1/')

# 2a. Bare relative references to the old layout in skills/ and agents/.
while IFS= read -r hit; do
  note "bare relative reference (should be \${CLAUDE_PLUGIN_ROOT}-prefixed): $hit"
done < <(find "$plugin_root/skills" "$plugin_root/agents" -name '*.md' \
  | xargs grep -n '`\(prompts\|agents\)/[A-Za-z0-9_.-]*`' /dev/null 2>/dev/null)

# 2b. Parent-directory escapes anywhere in shipped markdown.
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
  echo "OK: all skill/agent/prompt references resolve inside $plugin_root"
fi
exit "$fail"
