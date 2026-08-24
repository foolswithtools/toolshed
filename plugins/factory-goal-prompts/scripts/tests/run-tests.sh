#!/bin/sh
# Self-test for lint-issue.mjs. Exercises pass and fail fixtures and asserts
# exit codes and expected finding codes. Exits nonzero on any assertion failure.
set -u
here="$(cd "$(dirname "$0")" && pwd)"
lint="$here/../lint-issue.mjs"
repo="$here/fakerepo"
fails=0

assert_eq() {
  if [ "$1" != "$2" ]; then
    echo "ASSERT FAIL: $3 (expected $1, got $2)"
    fails=$((fails + 1))
  else
    echo "ok: $3"
  fi
}

assert_contains() {
  if printf '%s' "$2" | grep -q "$1"; then
    echo "ok: finding $1 fired"
  else
    echo "ASSERT FAIL: expected finding $1 in output"
    fails=$((fails + 1))
  fi
}

# 1. Passing feature body exits 0.
node "$lint" "$here/pass-feature.md" --genre feature --repo "$repo" >/dev/null 2>&1
assert_eq 0 $? "pass-feature exits 0"

# 2. Passing bootstrap body exits 0 (New: paths must not exist in the fake repo).
node "$lint" "$here/pass-bootstrap.md" --genre bootstrap --repo "$repo" >/dev/null 2>&1
assert_eq 0 $? "pass-bootstrap exits 0"

# 3. Failing feature body exits 1 with the expected finding codes.
out=$(node "$lint" "$here/fail-feature.md" --genre feature --repo "$repo" 2>&1)
assert_eq 1 $? "fail-feature exits 1"
for code in TITLE_GRAMMAR SECTION_MISSING SPEC_ANCHOR_MISSING RELATIVE_DATE \
  TEST_PLAN_NO_PATH VAGUE_ACCEPTANCE BLOCKED_BY_EMPTY EXISTING_PATH_MISSING; do
  assert_contains "$code" "$out"
done

# 4. Banned character rule. The em dash is built from its code point so no
#    banned character literal is committed anywhere in this tree.
tmp="$here/.tmp-banned.md"
node -e "const fs=require('fs');const src=fs.readFileSync('$here/pass-feature.md','utf8');fs.writeFileSync('$tmp',src.replace('the seam','the seam '+String.fromCharCode(0x2014)+' truly'))"
out=$(node "$lint" "$tmp" --genre feature --repo "$repo" 2>&1)
assert_eq 1 $? "banned-char fixture exits 1"
assert_contains BANNED_CHAR "$out"
rm -f "$tmp"

# 5. New: path that already exists must fail under bootstrap.
tmp2="$here/.tmp-newexists.md"
node -e "const fs=require('fs');const src=fs.readFileSync('$here/pass-bootstrap.md','utf8');fs.writeFileSync('$tmp2',src.replace('New: \`App/AppMain.swift\`','New: \`src/example.ts\`'))"
out=$(node "$lint" "$tmp2" --genre bootstrap --repo "$repo" 2>&1)
assert_eq 1 $? "new-path-exists fixture exits 1"
assert_contains NEW_PATH_EXISTS "$out"
rm -f "$tmp2"

# 6. Decision genre, declared in the body (no --genre flag), spec resolved via
#    --plan-root only (no --repo).
node "$lint" "$here/pass-decision.md" --plan-root "$repo" >/dev/null 2>&1
assert_eq 0 $? "pass-decision exits 0 (Genre: line, plan-root spec)"

# 7. Verify: line satisfies the test plan; Planned: marker satisfies anchor
#    presence; [NNN] slug ref satisfies Blocked by.
node "$lint" "$here/pass-verify.md" --genre feature --repo "$repo" >/dev/null 2>&1
assert_eq 0 $? "pass-verify exits 0 (Verify:, Planned:, slug ref)"

# 8. Decision genre with a missing required section fails.
tmp3="$here/.tmp-decision-broken.md"
node -e "const fs=require('fs');const src=fs.readFileSync('$here/pass-decision.md','utf8');fs.writeFileSync('$tmp3',src.replace('## Recommendation','## Suggestion'))"
out=$(node "$lint" "$tmp3" --plan-root "$repo" 2>&1)
assert_eq 1 $? "broken decision fixture exits 1"
assert_contains SECTION_MISSING "$out"
rm -f "$tmp3"

# 9. Bootstrap genre requires a "Shippable main:" acceptance criterion; a body
#    without one fails with SHIPPABLE_MAIN_MISSING.
tmp4="$here/.tmp-no-shippable.md"
node -e "const fs=require('fs');const src=fs.readFileSync('$here/pass-bootstrap.md','utf8');fs.writeFileSync('$tmp4',src.replace('Shippable main:','First criterion:'))"
out=$(node "$lint" "$tmp4" --genre bootstrap --repo "$repo" 2>&1)
assert_eq 1 $? "no-shippable-main fixture exits 1"
assert_contains SHIPPABLE_MAIN_MISSING "$out"
rm -f "$tmp4"

# 10. The shippable-main criterion must be the FIRST acceptance bullet; a body
#     where another bullet precedes it fails with SHIPPABLE_MAIN_NOT_FIRST.
tmp5="$here/.tmp-shippable-second.md"
node -e "const fs=require('fs');const src=fs.readFileSync('$here/pass-bootstrap.md','utf8');fs.writeFileSync('$tmp5',src.replace('- Shippable main:','- The repo has a green badge.\n- Shippable main:'))"
out=$(node "$lint" "$tmp5" --genre bootstrap --repo "$repo" 2>&1)
assert_eq 1 $? "shippable-main-not-first fixture exits 1"
assert_contains SHIPPABLE_MAIN_NOT_FIRST "$out"
rm -f "$tmp5"

# 11. Pattern config: the same passing feature body passes against a repo whose
#     .pattern-config.json declares its spec_dir and partition (fakerepo-config).
crepo="$here/fakerepo-config"
node "$lint" "$here/pass-feature.md" --genre feature --repo "$crepo" >/dev/null 2>&1
assert_eq 0 $? "pass-feature exits 0 against the config repo"

# 12. Pattern config: a spec anchor outside the configured spec_dir fails with
#     SPEC_OUTSIDE_SPEC_DIR (the target file exists, isolating the new check).
tmp6="$here/.tmp-spec-outside.md"
node -e "const fs=require('fs');const src=fs.readFileSync('$here/pass-feature.md','utf8');fs.writeFileSync('$tmp6',src.replace('docs/specs/2026-08-24-sample.md','notes/other.md'))"
out=$(node "$lint" "$tmp6" --genre feature --repo "$crepo" 2>&1)
assert_eq 1 $? "spec-outside-spec-dir fixture exits 1"
assert_contains SPEC_OUTSIDE_SPEC_DIR "$out"
rm -f "$tmp6"

# 13. Pattern config: a test plan naming none of the declared partitions fails
#     with PARTITION_UNDECLARED.
tmp7="$here/.tmp-partition.md"
node -e "const fs=require('fs');const src=fs.readFileSync('$here/pass-feature.md','utf8');fs.writeFileSync('$tmp7',src.replace('Partition: core-coverage','Partition: nightly'))"
out=$(node "$lint" "$tmp7" --genre feature --repo "$crepo" 2>&1)
assert_eq 1 $? "undeclared-partition fixture exits 1"
assert_contains PARTITION_UNDECLARED "$out"
rm -f "$tmp7"

# 14. An invalid pattern config is a usage error (exit 2), not an issue finding.
tmp8="$here/.tmp-bad-config.json"
printf '{"version":2,"spec_dir":"/abs"}' > "$tmp8"
node "$lint" "$here/pass-feature.md" --genre feature --repo "$repo" --pattern-config "$tmp8" >/dev/null 2>&1
assert_eq 2 $? "invalid pattern config exits 2"
rm -f "$tmp8"

echo ""
if [ "$fails" -eq 0 ]; then
  echo "SELF-TEST PASS"
  exit 0
else
  echo "SELF-TEST FAIL: $fails assertion(s)"
  exit 1
fi
