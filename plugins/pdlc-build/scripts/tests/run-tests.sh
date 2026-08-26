#!/bin/sh
# Verification checks for the pdlc-build plugin (issue #21 test plan, written
# first). Two layers: the plugin's structural contract (manifests, the four
# actions present in the shared core, every command wrapping a shared procedure,
# each procedure carrying its pinned factory invocations), and check-credits.sh's
# own behavior against fixtures (no network, no model call). The recorded live
# smokes against a real factory are the other half of the test plan and live in
# the PR body and the evidence bundle.
#
# Exits nonzero on any assertion failure.
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

assert_contains() {
  if printf '%s' "$2" | grep -qF "$1"; then
    echo "ok: $3"
  else
    echo "ASSERT FAIL: $3 (missing [$1])"
    fails=$((fails + 1))
  fi
}

assert_file() {
  if [ -f "$1" ]; then
    echo "ok: $2"
  else
    echo "ASSERT FAIL: $2 (missing $1)"
    fails=$((fails + 1))
  fi
}

echo "== 1. manifests =="
plugin_json="$plugin_root/.claude-plugin/plugin.json"
pkg_json="$plugin_root/package.json"
assert_file "$plugin_json" "plugin.json present"
assert_file "$pkg_json" "package.json present"

name_check=$(node -e '
  const fs=require("node:fs");
  const p=JSON.parse(fs.readFileSync(process.argv[1],"utf8"));
  process.stdout.write(p.name==="pdlc-build" && p.version ? "ok":"bad");
' "$plugin_json" 2>&1)
assert_eq "ok" "$name_check" "plugin.json names pdlc-build with a version"

manifest_check=$(node -e '
  const fs=require("node:fs");
  const m=JSON.parse(fs.readFileSync(process.argv[1],"utf8"));
  const skills=(m.pi&&m.pi.skills)||[];
  const prompts=(m.pi&&m.pi.prompts)||[];
  const keywords=m.keywords||[];
  const ok=skills.length===1&&skills[0]==="./skills"
    &&prompts.length===1&&prompts[0]==="./prompts"
    &&keywords.includes("pi-package");
  process.stdout.write(ok?"ok":"bad");
' "$pkg_json" 2>&1)
assert_eq "ok" "$manifest_check" "pi manifest references ./skills and ./prompts and carries the pi-package keyword"

echo "== 2. shared core: skill + four action procedures =="
assert_file "$plugin_root/skills/operating-factory-runs/SKILL.md" "the operating-factory-runs skill ships"
assert_file "$plugin_root/prompts/operator-constraints.md" "the operator-constraints preamble ships"
for action in submit-run run-status escalation-triage budget-check; do
  assert_file "$plugin_root/prompts/$action.md" "shared procedure prompts/$action.md ships"
  assert_file "$plugin_root/commands/$action.md" "Claude Code command commands/$action.md ships"
  cmd_body="$(cat "$plugin_root/commands/$action.md" 2>/dev/null)"
  assert_contains "\${CLAUDE_PLUGIN_ROOT}/prompts/$action.md" "$cmd_body" "command $action wraps its shared procedure (no reimplementation)"
  assert_contains "operator-constraints" "$cmd_body" "command $action carries the constraints preamble"
done

echo "== 3. pinned factory invocations recorded verbatim in the procedures =="
sr="$(cat "$plugin_root/prompts/submit-run.md")"
assert_contains "factory init <work-dir>" "$sr" "submit-run pins factory init"
assert_contains "backend = pi" "$sr" "submit-run pins the pi backend"
assert_contains "model = z-ai/glm-5.3" "$sr" "submit-run pins the glm-5.3 builder"
assert_contains "scripts/scoped-creds.sh pi --" "$sr" "submit-run pins the scoped-creds run wrapper"
assert_contains "id: gh-<owner/repo>#<number>" "$sr" "submit-run pins the run-identity id convention"
rs="$(cat "$plugin_root/prompts/run-status.md")"
assert_contains "factory status <work-dir>" "$rs" "run-status pins factory status"
assert_contains "framework-portability" "$rs" "run-status keeps the two scores separate (framework-portability)"
assert_contains "app-buildability" "$rs" "run-status keeps the two scores separate (app-buildability)"
et="$(cat "$plugin_root/prompts/escalation-triage.md")"
assert_contains "factory status <work-dir>" "$et" "escalation-triage pins factory status"
assert_contains "lint-issue.mjs" "$et" "escalation-triage lints the corrected issue body"
bc="$(cat "$plugin_root/prompts/budget-check.md")"
assert_contains "check-credits.sh" "$bc" "budget-check wraps the credits script"
assert_contains "total_usage" "$bc" "budget-check reads the authoritative total_usage figure"

echo "== 4. hygiene: links + no-duplication =="
links_out=$(bash "$plugin_root/scripts/check-links.sh" 2>&1); links_status=$?
echo "$links_out"
assert_eq 0 "$links_status" "check-links.sh is clean"
dup_out=$(bash "$plugin_root/scripts/check-no-pi-duplication.sh" "$plugin_root" 2>&1); dup_status=$?
echo "$dup_out"
assert_eq 0 "$dup_status" "check-no-pi-duplication.sh is clean"

echo "== 5. check-credits.sh behavior (fixtures, no network) =="
cc="$plugin_root/scripts/check-credits.sh"
assert_file "$cc" "check-credits.sh ships"

# read from a fixture prints total_usage to nine decimals.
read_out=$(bash "$cc" read --from-file "$fixtures/credits-pre.json" 2>&1); read_status=$?
assert_eq 0 "$read_status" "read from fixture exits 0"
assert_eq "9.218964862" "$read_out" "read prints total_usage to nine decimals"

# append writes a tab-separated row to the caller's ledger and prints the usage.
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
ledger="$scratch/ledger.tsv"
pre_out=$(bash "$cc" append --ledger "$ledger" --phase pre --label "gh-foo/bar#1/AT-1" --from-file "$fixtures/credits-pre.json" 2>&1)
assert_eq "9.218964862" "$pre_out" "append --phase pre prints the usage"
post_out=$(bash "$cc" append --ledger "$ledger" --phase post --label "gh-foo/bar#1/AT-1" --from-file "$fixtures/credits-post.json" 2>&1)
assert_eq "9.258413902" "$post_out" "append --phase post prints the usage"
rows=$(wc -l < "$ledger" | tr -d ' ')
assert_eq "2" "$rows" "ledger has two rows after two appends"
cols=$(head -1 "$ledger" | awk -F'\t' '{print NF}')
assert_eq "4" "$cols" "ledger row is four tab-separated columns"
assert_contains "pre" "$(sed -n '1p' "$ledger")" "row 1 carries the pre phase"
assert_contains "9.218964862" "$(sed -n '1p' "$ledger")" "row 1 carries the pre usage"
assert_contains "post" "$(sed -n '2p' "$ledger")" "row 2 carries the post phase"
assert_contains "gh-foo/bar#1/AT-1" "$(sed -n '2p' "$ledger")" "row 2 carries the run label"

# the settled delta reconciles to the known land-proof precedent (0.039449040).
delta=$(node -e 'process.stdout.write((9.258413902-9.218964862).toFixed(9))')
assert_eq "0.039449040" "$delta" "settled delta matches the land-proof precedent to nine decimals"

echo "== 6. check-credits.sh error handling =="
bash "$cc" append --phase pre --label x --from-file "$fixtures/credits-pre.json" >/dev/null 2>&1
assert_eq 2 $? "append without --ledger is a usage error (exit 2)"
bash "$cc" read --from-file "$fixtures/does-not-exist.json" >/dev/null 2>&1
assert_eq 1 $? "read from a missing fixture fails (exit 1)"
bash "$cc" read --from-file "$fixtures/credits-bad.json" >/dev/null 2>&1
assert_eq 1 $? "read of non-JSON fails (exit 1)"
bash "$cc" read --from-file "$fixtures/credits-missing-usage.json" >/dev/null 2>&1
assert_eq 1 $? "read of JSON without data.total_usage fails (exit 1)"
bash "$cc" bogus >/dev/null 2>&1
assert_eq 2 $? "an unknown command is a usage error (exit 2)"

echo ""
if [ "$fails" -eq 0 ]; then
  echo "SELF-TEST PASS"
  exit 0
else
  echo "SELF-TEST FAIL: $fails assertion(s)"
  exit 1
fi
