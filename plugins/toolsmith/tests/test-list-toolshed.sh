#!/usr/bin/env bash
# Dependency-free test for list-toolshed.sh. Exits nonzero on failure.
set -u
here="$(cd "$(dirname "$0")" && pwd)"
script="$here/../scripts/list-toolshed.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# Fixture: a fake marketplace root with one plugin skill.
mkdir -p "$tmp/plugins/demo/skills/make-widgets"
cat > "$tmp/plugins/demo/skills/make-widgets/SKILL.md" <<'EOF'
---
name: make-widgets
description: Use when building widgets from parts. Assembles and verifies them.
---
body text here
EOF

out="$(bash "$script" "$tmp")"

echo "$out" | grep -q "make-widgets" || { echo "FAIL: name missing"; exit 1; }
echo "$out" | grep -q "Assembles and verifies" || { echo "FAIL: description missing"; exit 1; }

# Empty root prints nothing and still exits 0.
empty="$(mktemp -d)"
bash "$script" "$empty" >/dev/null || { echo "FAIL: nonzero on empty"; exit 1; }
rm -rf "$empty"

echo "PASS"
