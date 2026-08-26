#!/bin/sh
# pi package smoke test for pdlc-define (issue #20 test plan).
#
# Installs plugins/pdlc-define into an isolated, throwaway pi settings scope
# (never the real ~/.pi/agent) with one `pi install` command, then proves,
# through pi's own package manager and CLI, that the install surfaces the
# shared skills and prompt templates and that the linter runs from the
# installed package path. No provider key is used and nothing here makes a
# model call.
#
# Requires pi and node on PATH. Skips (exit 0) if pi is not installed, since
# this suite is a smoke test of a specific pi install, not a build-blocking
# unit test.
set -u
here="$(cd "$(dirname "$0")" && pwd)"
plugin_root="$(cd "$here/../.." && pwd)"
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

# --- 0. manifest shape: the pi manifest must exist and reference the shared
#        skills/ and prompts/ directories verbatim, never a copy. ---
manifest="$plugin_root/package.json"
if [ ! -f "$manifest" ]; then
  echo "ASSERT FAIL: pi manifest missing: $manifest"
  fails=$((fails + 1))
else
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
fi

# --- resolve pi's own installed package root from the pi binary on PATH, so
#     this script never hardcodes a machine-specific path. ---
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
  *pdlc-define*)
    echo "ok: pi list shows pdlc-define"
    ;;
  *)
    echo "ASSERT FAIL: pi list does not mention pdlc-define"
    fails=$((fails + 1))
    ;;
esac

# --- 3. discovery: pi's own package manager resolves the shared skills and
#        prompt templates (no model call; this is the same resolver pi runs
#        at startup). ---
resolve_output=$(cd "$project_dir" && PI_PKG_ROOT="$pi_pkg_root" node "$here/pi-resolve-smoke.mjs" 2>&1)
resolve_status=$?
echo "$resolve_output"
assert_eq 0 "$resolve_status" "pi's resolver runs clean with no model call"

skills_count=$(echo "$resolve_output" | sed -n 's/^SKILLS=//p')
prompts_count=$(echo "$resolve_output" | sed -n 's/^PROMPTS=//p')
skills_expected=$(find "$plugin_root/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
prompts_expected=$(find "$plugin_root/prompts" -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')
assert_eq "$skills_expected" "${skills_count:-0}" "pi discovers all pdlc-define skills through the installed package"
assert_eq "$prompts_expected" "${prompts_count:-0}" "pi discovers all pdlc-define prompt templates through the installed package"

# --- 4. linter: runs against a fixture body via the installed package path.
#        Local installs point at the checkout directly (no copy), so the
#        "installed package path" here is plugin_root itself. ---
linter="$plugin_root/scripts/lint-issue.mjs"
fixture="$here/pass-feature.md"
fakerepo="$here/fakerepo"
lint_output=$(node "$linter" "$fixture" --genre feature --repo "$fakerepo" 2>&1)
lint_status=$?
echo "$lint_output"
assert_eq 0 "$lint_status" "linter exits 0 against a fixture body via the installed package path"

# --- 5. hygiene: no file duplication between the pi surface and the Claude
#        Code surface. ---
dup_check="$plugin_root/scripts/check-no-pi-duplication.sh"
if [ ! -x "$dup_check" ] && [ ! -f "$dup_check" ]; then
  echo "ASSERT FAIL: duplicate-file check script missing: $dup_check"
  fails=$((fails + 1))
else
  dup_output=$(bash "$dup_check" "$plugin_root" 2>&1)
  dup_status=$?
  echo "$dup_output"
  assert_eq 0 "$dup_status" "no file duplication between the pi surface and the Claude Code surface"
fi

if [ "$fails" -gt 0 ]; then
  echo "$fails failure(s)."
  exit 1
fi
echo "OK: pi package smoke clean (install, list, ${skills_count:-0} skills, ${prompts_count:-0} prompts, linter, no duplication)"
