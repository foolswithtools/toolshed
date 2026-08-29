#!/usr/bin/env bash
# List toolshed skills (name + short description) from plugin SKILL.md files.
# Usage: list-toolshed.sh [root]   (root defaults to current dir)
# bash 3.2 compatible: no mapfile, no associative arrays.
set -u
root="${1:-.}"

# Find every plugin skill manifest under the root.
find "$root" -type f -path '*/plugins/*/skills/*/SKILL.md' 2>/dev/null | sort | while IFS= read -r f; do
  name=""
  desc=""
  # Read only the YAML frontmatter (between the first two --- lines).
  in_fm=0
  while IFS= read -r line; do
    if [ "$line" = "---" ]; then
      if [ "$in_fm" -eq 0 ]; then in_fm=1; continue; else break; fi
    fi
    case "$line" in
      name:*) name="$(printf '%s' "$line" | sed 's/^name:[[:space:]]*//')" ;;
      description:*) desc="$(printf '%s' "$line" | sed 's/^description:[[:space:]]*//')" ;;
    esac
  done < "$f"
  [ -z "$name" ] && continue
  # Truncate the description to keep injected context small.
  short="$(printf '%s' "$desc" | cut -c1-120)"
  printf -- '- %s: %s\n' "$name" "$short"
done
