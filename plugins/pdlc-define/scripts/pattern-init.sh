#!/usr/bin/env bash
# Scaffold the pdlc-define pattern structure in a target repo.
# Idempotent: a second run on an initialized repo is a no-op.
#
# Usage: pattern-init.sh <target-repo-root>
#
# What it does, in order:
#   1. Writes .pattern-config.json from the template example if absent
#      (an existing config is kept and used as-is).
#   2. Validates the config with pattern-config.mjs; aborts on an invalid file.
#   3. Creates spec_dir and known_issues_dir (with .gitkeep) if missing.
#   4. Creates a roadmap stub at roadmap_path if missing.
#   5. Appends a documentation-hygiene section to CLAUDE.md if its marker
#      comment is absent (creates CLAUDE.md if needed).
#
# Requires bash and node. Only ever run this inside a repo the owner has
# approved for the pattern; the /pattern-init command enforces that guard.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLE="$HERE/../config/pattern-config.example.json"
CONFIG_NAME=".pattern-config.json"

if [ $# -ne 1 ] || [ ! -d "${1:-}" ]; then
  echo "usage: pattern-init.sh <target-repo-root> (must be an existing directory)" >&2
  exit 2
fi
TARGET="$(cd "$1" && pwd)"
CONFIG="$TARGET/$CONFIG_NAME"
changes=0

if [ -f "$CONFIG" ]; then
  echo "exists   $CONFIG_NAME (using the repo's own config)"
else
  cp "$EXAMPLE" "$CONFIG"
  echo "created  $CONFIG_NAME (template defaults; edit to fit the repo)"
  changes=$((changes + 1))
fi

node "$HERE/pattern-config.mjs" validate --repo "$TARGET"

json_field() {
  node -p 'JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"))[process.argv[2]] ?? ""' \
    "$CONFIG" "$1"
}
SPEC_DIR="$(json_field spec_dir)"
KNOWN_ISSUES_DIR="$(json_field known_issues_dir)"
ROADMAP_PATH="$(json_field roadmap_path)"
[ -n "$KNOWN_ISSUES_DIR" ] || KNOWN_ISSUES_DIR="docs/known-issues"
[ -n "$ROADMAP_PATH" ] || ROADMAP_PATH="docs/ROADMAP.md"

ensure_dir() {
  local rel="$1"
  if [ -d "$TARGET/$rel" ]; then
    echo "exists   $rel/"
  else
    mkdir -p "$TARGET/$rel"
    touch "$TARGET/$rel/.gitkeep"
    echo "created  $rel/ (with .gitkeep)"
    changes=$((changes + 1))
  fi
}
ensure_dir "$SPEC_DIR"
ensure_dir "$KNOWN_ISSUES_DIR"

if [ -f "$TARGET/$ROADMAP_PATH" ]; then
  echo "exists   $ROADMAP_PATH"
else
  mkdir -p "$(dirname "$TARGET/$ROADMAP_PATH")"
  printf '# Roadmap\n\nStatus markers: planned / in-progress / done. Update at close-out, in the same PR as the change.\n' \
    > "$TARGET/$ROADMAP_PATH"
  echo "created  $ROADMAP_PATH (stub)"
  changes=$((changes + 1))
fi

MARKER="<!-- pdlc-define: documentation hygiene -->"
CLAUDE_MD="$TARGET/CLAUDE.md"
if [ -f "$CLAUDE_MD" ] && grep -qF "$MARKER" "$CLAUDE_MD"; then
  echo "exists   CLAUDE.md documentation-hygiene section"
else
  [ -f "$CLAUDE_MD" ] && printf '\n' >> "$CLAUDE_MD"
  cat >> "$CLAUDE_MD" <<EOF
$MARKER
## Documentation hygiene (pdlc-define)

- Specs are dated files under \`$SPEC_DIR/\` (YYYY-MM-DD-topic.md); every unit of work anchors to one.
- Known-issue and resolved-bug write-ups live under \`$KNOWN_ISSUES_DIR/\`; every fixed bug gets an entry plus a named regression test.
- The roadmap at \`$ROADMAP_PATH\` carries status markers; update it at close-out, in the same PR as the change.
- Repo-specific paths, coverage partitions, gate commands, and issue labels are declared in \`$CONFIG_NAME\`; pattern skills and the issue linter read that file and fall back to template defaults when it is absent.
EOF
  echo "updated  CLAUDE.md (documentation-hygiene section appended)"
  changes=$((changes + 1))
fi

if [ "$changes" -eq 0 ]; then
  echo "pattern-init: no-op (already initialized)"
else
  echo "pattern-init: $changes change(s) applied to $TARGET"
fi
