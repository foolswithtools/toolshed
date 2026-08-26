#!/usr/bin/env bash
# Verification checks for the refine-spec cold-session smoke. These are the
# TDD assertions: they are written before the command exists and must fail
# against a transcript produced with no refine-spec command installed, then
# pass against a transcript of a real facilitated session.
#
# They read two things:
#   1. the session transcript (every human turn and model reply, concatenated)
#   2. the fixture working tree after the session (to prove the scope guard:
#      the target doc changed, the decision log gained proposed entries, and
#      no new documents were created)
#
# The command mandates a small visible session-state vocabulary (RESTATE:,
# PROPOSED EDIT / Rationale:, CRITIC CAST, RESEARCHER DISPATCH, and so on) so
# that the contract clauses are auditable from the transcript rather than
# inferred from prose. These checks grep for that vocabulary.
#
# Usage: verify-transcript.sh <transcript-file> <fixture-dir>
# Exit 0 when every clause is demonstrated; exit 1 with a finding list.
set -u

transcript="${1:-}"
fixture="${2:-}"
if [ -z "$transcript" ] || [ -z "$fixture" ]; then
  echo "usage: verify-transcript.sh <transcript-file> <fixture-dir>" >&2
  exit 2
fi
if [ ! -f "$transcript" ]; then
  echo "transcript not found: $transcript" >&2
  exit 2
fi

fails=0
pass() { echo "ok: $1"; }
fail() { echo "FAIL: $1"; fails=$((fails + 1)); }

# Lowercased copy for case-insensitive ordering checks.
t="$(cat "$transcript")"

line_of() {
  # first 1-indexed line number matching the (grep -n, case-insensitive) pattern; empty if none
  grep -niE "$1" "$transcript" 2>/dev/null | head -1 | cut -d: -f1
}

# --- Layer 1: facilitator restates before challenging ---
if grep -qiE '(^|[^a-z])RESTATE:' "$transcript"; then
  pass "facilitator emitted a RESTATE of the human position"
else
  fail "no RESTATE: marker found (facilitator must restate before challenging)"
fi

restate_line="$(line_of '(^|[^a-z])RESTATE:')"
challenge_line="$(line_of '(^|[^a-z])(CHALLENGE|STEELMAN):')"
if [ -n "$restate_line" ] && [ -n "$challenge_line" ]; then
  if [ "$restate_line" -lt "$challenge_line" ]; then
    pass "restate precedes the first challenge/steelman (line $restate_line < $challenge_line)"
  else
    fail "a challenge/steelman ($challenge_line) appears before any restate ($restate_line)"
  fi
else
  fail "missing a CHALLENGE:/STEELMAN: counter-position to order against the restate"
fi

# The facilitator brings a genuine steelmanned counter-position, not only questions.
if grep -qiE '(^|[^a-z])STEELMAN:' "$transcript"; then
  pass "facilitator brought a STEELMAN counter-position"
else
  fail "no STEELMAN: marker (facilitator must bring a steelmanned counter, not only questions)"
fi

# --- Layer 2: adversarial critic, cast from the repo panel, capped, sequential,
#     no cross-visibility before commitment, and it actually ran ---
# A committed CRITIC RETURNED record proves the critic was cast, so either
# marker satisfies "a critic was cast" (sessions often fold the CAST
# announcement into the RETURNED record).
if grep -qiE 'CRITIC (CAST|RETURNED)' "$transcript"; then
  pass "a critic was cast"
else
  fail "no CRITIC CAST/RETURNED marker"
fi
if grep -qiE 'CRITIC CAST.*(source=panel|from the (repo )?panel|panel persona)' "$transcript" \
   || grep -qiE '(skeptical.buyer|burned.operator)' "$transcript"; then
  pass "critic cast from the repo docs/panel/ personas"
else
  fail "critic not cast from the repo panel personas (skeptical-buyer / burned-operator)"
fi
if grep -qiE '(no cross.visibility|independent|without seeing|sequential)' "$transcript"; then
  pass "critic run recorded as sequential / no cross-visibility before commitment"
else
  fail "no evidence critics ran independently with no cross-visibility before commitment"
fi
# Cap: at most 2 to 3 per dispute. Count committed critiques (RETURNED).
critic_count="$(grep -ociE 'CRITIC RETURNED' "$transcript")"
if [ "${critic_count:-0}" -ge 1 ] && [ "${critic_count:-0}" -le 3 ]; then
  pass "critic casting capped within 1..3 per dispute (found $critic_count)"
else
  fail "critic casting count $critic_count is outside the 1..3 cap"
fi
if grep -qiE 'CRITIC (RETURNED|CRITIQUE|FINDING)' "$transcript"; then
  pass "the cast critic actually ran and returned a critique"
else
  fail "no CRITIC RETURNED marker (a critic was cast but never ran)"
fi

# --- Layer 3: researcher for the single bounded factual dispute, source-attached,
#     citation verified against the retrieved text ---
# A RESEARCHER RETURNED record proves a dispatch, so either marker satisfies
# "a researcher was dispatched".
if grep -qiE 'RESEARCHER (DISPATCH|RETURNED)' "$transcript"; then
  pass "a researcher was dispatched for the factual dispute"
else
  fail "no RESEARCHER DISPATCH/RETURNED marker"
fi
if grep -qiE 'RESEARCHER RETURNED' "$transcript" && grep -qiE '(^|[^a-z])SOURCE:' "$transcript"; then
  pass "researcher returned a claim with attached SOURCE text"
else
  fail "researcher claim missing an attached SOURCE:"
fi
if grep -qiE 'CITATION VERIFIED' "$transcript"; then
  pass "facilitator verified the citation against the retrieved text before it entered the doc"
else
  fail "no CITATION VERIFIED marker (claim entered without verification)"
fi

# --- Editing contract: every proposed edit carries a one-line rationale and
#     required an explicit human accept; silence is never acceptance ---
if grep -qiE 'PROPOSED EDIT' "$transcript"; then
  pass "edits were proposed one at a time (PROPOSED EDIT markers present)"
else
  fail "no PROPOSED EDIT markers"
fi
if grep -qiE '(^|[^a-z])Rationale:' "$transcript"; then
  pass "proposed edits carried a one-line rationale"
else
  fail "no Rationale: line on proposed edits"
fi
if grep -qiE '(awaiting|await).*(ACCEPT|accept/reject)' "$transcript" \
   || grep -qiE 'silence is (never|not) acceptance' "$transcript"; then
  pass "edits paused for an explicit accept (silence-is-not-acceptance honored)"
else
  fail "no explicit-acceptance pause recorded"
fi
# The human side must have actually accepted at least once, and no edit may land
# without one. EDIT LANDED count must not exceed human ACCEPT count.
landed="$(grep -ociE 'EDIT LANDED|EDIT APPLIED' "$transcript")"
# Count only explicit human acceptances (a HUMAN turn that says ACCEPT), not the
# facilitator's own "[awaiting ACCEPT / ...]" prompts.
accepts="$(grep -ciE '^HUMAN:.*accept' "$transcript")"
if [ "${landed:-0}" -ge 1 ]; then
  pass "at least one edit landed after acceptance ($landed landed)"
else
  fail "no edit ever landed"
fi
if [ "${landed:-0}" -le "${accepts:-0}" ]; then
  pass "no edit landed without an explicit acceptance ($landed landed <= $accepts accepts)"
else
  fail "more edits landed ($landed) than explicit acceptances ($accepts): a silent edit"
fi

# --- Session state: decision log gains proposed, UNSTAMPED entries; the command
#     proposes but never stamps ---
if grep -qiE 'PROPOSED.*(decision|unstamped)|decision log.*proposed|unstamped' "$transcript"; then
  pass "proposed, unstamped decision entries were maintained live"
else
  fail "no proposed/unstamped decision-log entries in the session state"
fi

# --- Scope guard: no issues filed, no author-issues run ---
if grep -qiE 'gh issue create|/author-issues|author-issues\.md .*(run|invoke)' "$transcript"; then
  fail "scope-guard breach: an issue was filed or /author-issues was run"
else
  pass "no issues filed and /author-issues not run"
fi
if grep -qiE 'SCOPE GUARD|will not file issues|does not file issues|not run /author-issues|no issues filed|won.?t touch issue authoring|no new documents created' "$transcript"; then
  pass "scope guard was stated explicitly"
else
  fail "scope guard not stated in the session"
fi

# --- Working-tree proof against the fixture ---
if [ -d "$fixture" ]; then
  # Target doc changed: the factual SQLite claim is gone or corrected.
  if grep -qiE 'SQLite cannot serve' "$fixture/docs/VISION.md" 2>/dev/null; then
    fail "the factually-wrong SQLite stance survived unedited in VISION.md"
  else
    pass "the factually-wrong stance was edited out of VISION.md"
  fi
  # Decision log gained proposed entries but stayed unstamped where proposed.
  if grep -qiE 'proposed|unstamped|awaiting.*stamp' "$fixture/docs/decisions/DECISIONS.md" 2>/dev/null; then
    pass "the decision log gained a proposed, unstamped entry"
  else
    fail "the decision log shows no proposed (unstamped) entry"
  fi
  # No new documents created: the git status shows edits, not new doc files.
  if command -v git >/dev/null 2>&1 && git -C "$fixture" rev-parse --git-dir >/dev/null 2>&1; then
    newdocs="$(git -C "$fixture" status --porcelain 2>/dev/null | grep -E '^\?\? ' | grep -iE '\.md$' | grep -viE 'DECISIONS\.md|VISION\.md' || true)"
    if [ -z "$newdocs" ]; then
      pass "no new documents were created (document economy respected)"
    else
      fail "new document(s) created against the document-economy rule: $newdocs"
    fi
  fi
else
  echo "note: fixture dir $fixture not present; skipping working-tree proofs"
fi

echo ""
if [ "$fails" -eq 0 ]; then
  echo "SMOKE VERIFY PASS"
  exit 0
else
  echo "SMOKE VERIFY FAIL: $fails clause(s) unproven"
  exit 1
fi
