#!/bin/sh
# pi package smoke test for pdlc-build (issue #21 dual-harness acceptance).
#
# Installs plugins/pdlc-build into an isolated, throwaway pi settings scope
# (never the real ~/.pi/agent) with one `pi install` command, then proves,
# through pi's own package manager and CLI, that the install surfaces the shared
# skills and action procedures and that the credits script runs from the
# installed package path. No provider key is used and nothing here makes a model
# call: the same four actions are invocable from pi via the shared core, with one
# install command and no per-harness file duplication.
#
# Requires pi and node on PATH. Skips (exit 0) if pi is not installed, since this
# suite is a smoke test of a specific pi install, not a build-blocking unit test.
set -u
here="$(cd "$(dirname "$0")" && pwd)"
plugin_root="$(cd "$here/../.." && pwd)"
fixtures="$here/fixtures"
fails=0

assert_eq() {
  if [ "$1" != "$2" ]; then
    echo "ASSERT FAIL: $3 (expected [$1], got [$2])"
    fails=$((fails + 1))
  else
    echo "ok: $3"
  fi
}

if ! command -v pi >/dev/null 2>&1; then
  echo "pi not found on PATH; skipping pi package smoke test"
  exit 0
fi
if ! command -v node >/dev/null 2>&1; then
  echo "node not found on PATH" >&2
  exit 2
fi

echo "pi version: $(pi --version 2>&1)"

# --- 0. manifest shape ---
manifest="$plugin_root/package.json"
manifest_check=$(node -e '
  const fs = require("node:fs");
  const m = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
  const skills = (m.pi && m.pi.skills) || [];
  const prompts = (m.pi && m.pi.prompts) || [];
  const keywords = m.keywords || [];
  const ok = skills.includes("./skills") && prompts.includes("./prompts") && keywords.includes("pi-package");
  process.stdout.write(ok ? "ok" : "bad");
' "$manifest" 2>&1)
assert_eq "ok" "$manifest_check" "manifest declares ./skills, ./prompts, and the pi-package keyword"

# --- resolve pi's own installed package root from the pi binary on PATH. ---
pi_bin="$(command -v pi)"
if command -v readlink >/dev/null 2>&1 && readlink -f "$pi_bin" >/dev/null 2>&1; then
  pi_real="$(readlink -f "$pi_bin")"
else
  pi_real="$(realpath "$pi_bin")"
fi
pi_pkg_root="$(cd "$(dirname "$pi_real")/.." && pwd)"

# --- isolated scratch scope: never touch the real ~/.pi/agent settings. ---
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
agent_dir="$scratch/agentdir"
project_dir="$scratch/project"
mkdir -p "$agent_dir" "$project_dir"
export PI_CODING_AGENT_DIR="$agent_dir"
export PI_OFFLINE=1

# --- 1. install: one pi command, from the local checkout. ---
install_output=$(cd "$project_dir" && pi install "$plugin_root" -l -a 2>&1)
install_status=$?
echo "$install_output"
assert_eq 0 "$install_status" "pi install exits 0"

# --- 2. list: the package is registered. ---
list_output=$(cd "$project_dir" && pi list -a 2>&1)
echo "$list_output"
case "$list_output" in
  *pdlc-build*)
    echo "ok: pi list shows pdlc-build"
    ;;
  *)
    echo "ASSERT FAIL: pi list does not mention pdlc-build"
    fails=$((fails + 1))
    ;;
esac

# --- 3. discovery: pi's own package manager resolves the shared skills and
#        action procedures. ---
resolve_output=$(cd "$project_dir" && PI_PKG_ROOT="$pi_pkg_root" node "$here/pi-resolve-smoke.mjs" 2>&1)
resolve_status=$?
echo "$resolve_output"
assert_eq 0 "$resolve_status" "pi's resolver runs clean with no model call"

skills_count=$(echo "$resolve_output" | sed -n 's/^SKILLS=//p')
prompts_count=$(echo "$resolve_output" | sed -n 's/^PROMPTS=//p')
skills_expected=$(find "$plugin_root/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
prompts_expected=$(find "$plugin_root/prompts" -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')
assert_eq "$skills_expected" "${skills_count:-0}" "pi discovers all pdlc-build skills through the installed package"
assert_eq "$prompts_expected" "${prompts_count:-0}" "pi discovers all pdlc-build action procedures through the installed package"

# --- 4. credits script: runs against a fixture via the installed package path.
#        Local installs point at the checkout directly (no copy), so the
#        "installed package path" here is plugin_root itself. ---
cc="$plugin_root/scripts/check-credits.sh"
cc_out=$(bash "$cc" read --from-file "$fixtures/credits-pre.json" 2>&1)
cc_status=$?
echo "$cc_out"
assert_eq 0 "$cc_status" "check-credits.sh exits 0 against a fixture via the installed package path"
assert_eq "9.218964862" "$cc_out" "check-credits.sh reads total_usage through the installed package path"

# --- 5. hygiene: no file duplication between the pi surface and the Claude Code
#        surface. ---
dup_check="$plugin_root/scripts/check-no-pi-duplication.sh"
dup_output=$(bash "$dup_check" "$plugin_root" 2>&1)
dup_status=$?
echo "$dup_output"
assert_eq 0 "$dup_status" "no file duplication between the pi surface and the Claude Code surface"

if [ "$fails" -gt 0 ]; then
  echo "$fails failure(s)."
  exit 1
fi
echo "OK: pi package smoke clean (install, list, ${skills_count:-0} skills, ${prompts_count:-0} prompts, credits script, no duplication)"
