#!/bin/sh
# Self-test for kickoff-preflight.mjs. Exercises the three fixture outcomes
# the plugin's kickoff-preflight issue requires: a clean body passes, a body
# with a rotted anchor is refused by the preflight's own symbol-freshness
# check, and a body missing a required section is refused by the linter it
# wraps. Exits nonzero on any assertion failure.
set -u
here="$(cd "$(dirname "$0")" && pwd)"
preflight="$here/../kickoff-preflight.mjs"
fixtures="$here/kickoff-preflight"
repo="$fixtures/fakerepo"
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

# Fixture 1: clean body passes. Prints anchor freshness for the pass case.
out=$(node "$preflight" "$fixtures/clean.md" --genre feature --repo "$repo" 2>&1)
assert_eq 0 $? "clean fixture: PASS"
assert_contains "PREFLIGHT PASS" "$out"
assert_contains "anchor freshness" "$out"

# Fixture 2: an anchor whose line is still in range but whose named symbol has
# moved more than 20 lines away is refused (the drift the linter's own
# line-length check cannot see).
out=$(node "$preflight" "$fixtures/rotted-anchor.md" --genre feature --repo "$repo" 2>&1)
assert_eq 1 $? "rotted-anchor fixture: REFUSED"
assert_contains "PREFLIGHT REFUSED" "$out"
assert_contains "ANCHOR_SYMBOL_DRIFT" "$out"
assert_contains "src/example.ts:70" "$out"

# Fixture 3: a body missing a required section is refused via the wrapped
# linter, not reimplemented logic.
out=$(node "$preflight" "$fixtures/missing-section.md" --genre feature --repo "$repo" 2>&1)
assert_eq 1 $? "missing-section fixture: REFUSED"
assert_contains "PREFLIGHT REFUSED" "$out"
assert_contains "SECTION_MISSING" "$out"

# A malformed body-file argument (missing file) is a usage error, not a
# silent pass.
out=$(node "$preflight" "$fixtures/does-not-exist.md" --genre feature --repo "$repo" 2>&1)
code=$?
if [ "$code" -eq 0 ]; then
  echo "ASSERT FAIL: missing body file must not exit 0 (got 0)"
  fails=$((fails + 1))
else
  echo "ok: missing body file exits nonzero ($code)"
fi

echo ""
if [ "$fails" -eq 0 ]; then
  echo "SELF-TEST PASS"
  exit 0
else
  echo "SELF-TEST FAIL: $fails assertion(s)"
  exit 1
fi
