#!/usr/bin/env bash
# Cold-session smoke for the refine-spec command (issue #34 test plan).
#
# Builds the flawed-vision fixture, loads the pdlc-define plugin from this
# local checkout, drives a scripted human side of a /refine-spec session with
# the Claude Code CLI (model-pinned, foreground, one turn per invocation,
# resumed by session id), captures the full assistant stream for every turn,
# and runs verify-transcript.sh over the resulting transcript plus the
# fixture working tree.
#
# The scripted human turns are sequenced with `claude -p --resume` (print
# mode, one turn per process, resumed by a fixed session id). That is the
# mechanism used to record the committed sample-transcript.md evidence.
#
# Capture: each turn runs with `--output-format stream-json --verbose` and
# the raw event stream is piped through extract-assistant-text.mjs, which
# writes the text of every assistant message in the turn (not just the
# final one) to the transcript. `--output-format text` only surfaces the
# last assistant message, which drops any protocol marker (CRITIC CAST,
# RESEARCHER DISPATCH, and so on) emitted before a mid-turn tool call, and a
# smoke that cannot see those markers fails a correct session.
#
# Hermeticity: a user-scope install of pdlc-define (from any marketplace
# nickname) otherwise wins over --plugin-dir and can silently shadow this
# checkout with a stale version. build-hermetic-settings.mjs reads
# `claude plugin list --json` and writes a --settings file that disables
# every installed plugin literally named pdlc-define, so the checkout always
# wins regardless of what is installed on the machine running the smoke.
#
# Exit codes: each turn's real `claude` exit status is read from
# ${PIPESTATUS[0]} (the first stage of the capture pipeline), not from the
# downstream `tee`/`node` stages.
#
# Fail-fast: if turn 1 (the /refine-spec invocation itself) prints
# "Unknown command", the plugin did not load. The harness aborts immediately
# with a diagnostic instead of spending six more turns driving a plain chat
# session and then failing verify-transcript.sh with confusing clause
# mismatches.
#
# This drives a real model and takes several minutes. It is not part of the
# no-model unit suites (run-tests.sh, run-pi-smoke-tests.sh). It SKIPS (exit 0)
# when `claude` is not on PATH, mirroring the pi smoke's skip-when-absent rule.
#
# Usage: run-smoke.sh [workdir]
#   workdir  where the fixture and transcript are written (default: a mktemp dir)
# Env:
#   REFINE_SMOKE_MODEL   model to pin (default: claude-sonnet-5)
#   REFINE_SMOKE_TIMEOUT per-turn timeout in seconds (default: 540)
set -uo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
plugin_root="$(cd "$here/../../.." && pwd)"
model="${REFINE_SMOKE_MODEL:-claude-sonnet-5}"
per_turn="${REFINE_SMOKE_TIMEOUT:-540}"

if ! command -v claude >/dev/null 2>&1; then
  echo "claude not found on PATH; skipping refine-spec cold-session smoke"
  exit 0
fi
if ! command -v node >/dev/null 2>&1; then
  echo "node not found on PATH" >&2
  exit 2
fi

workdir="${1:-$(mktemp -d)}"
mkdir -p "$workdir"
fixture="$workdir/fixture"
transcript="$workdir/transcript.txt"
raw_stream="$workdir/raw-stream.jsonl"
settings_file="$workdir/hermetic-settings.json"

bash "$here/build-fixture.sh" "$fixture" >/dev/null
sid="$(node -e "console.log(require('crypto').randomUUID())")"
: > "$transcript"
: > "$raw_stream"

claude plugin list --json 2>/dev/null | node "$here/build-hermetic-settings.mjs" > "$settings_file"
echo "hermetic settings ($settings_file): $(cat "$settings_file")"

# The scripted human side, one message per turn. Turn 1 is the command; the
# rest drive the three layers, the editing contract (accept, modify, accept),
# the decision log, and the scoped close.
turns=(
"/pdlc-define:refine-spec docs/VISION.md"
"Stance 1: leave it as is. I will know daily use when I see it; do not add a marker. Now Stance 2. I think the SQLite claim is factually wrong. Dispatch a researcher to check whether SQLite supports concurrent readers, and whether concurrent reads corrupt the database. Require a real retrieved source attached to the finding, and verify it before proposing any edit."
"Yes, cast both panel personas against Stance 2. Run them sequentially and independently with no cross-visibility until each has committed its critique; cap at those two. For the record: I do NOT expect concurrent writes or remote multi-device access near-term. This is single-household, mostly one person entering data while another might glance at a report. After the critics commit, propose the edit to Stance 2 that corrects the false SQLite claim and the Postgres-from-day-one conclusion."
"ACCEPT. Apply that Stance 2 edit to docs/VISION.md now."
"Good, Stance 3 is too vague. Propose an edit turning it into concrete, checkable signals: import-to-report round trip stays under 2 seconds for a month of transactions; the daily check-in is a single command; every error message names the exact fix. Propose it as one edit with a rationale and wait for my response."
"MODIFY: add a fourth signal, first-run setup completes in under 5 minutes. Re-propose the full edit and wait again."
"ACCEPT the Stance 3 edit and apply it. Then close the session: append the decisions proposed this session to docs/decisions/DECISIONS.md, each clearly marked as PROPOSED (unstamped) with its reason, and do NOT stamp them (that authority is mine); I accept adding those proposed entries to the log. Then run the repo style gate declared in CONVENTIONS.md (no em dashes) over your changes and fix any hit. Print the SESSION CLOSE summary of what changed and what remains open. Then commit everything per the repo commit style with a why-message. Do not file any issues, do not run author-issues, and do not create any new documents; note the document-economy rule if it applies."
)

i=0
for msg in "${turns[@]}"; do
  i=$((i + 1))
  printf '\n===== HUMAN TURN %d =====\nHUMAN: %s\n\n' "$i" "$msg" | tee -a "$transcript"

  turn_err="$workdir/turn-$i.stderr.log"
  if [ "$i" -eq 1 ]; then
    (cd "$fixture" && timeout "$per_turn" claude --model "$model" --dangerously-skip-permissions \
       --plugin-dir "$plugin_root" --settings "$settings_file" \
       --session-id "$sid" -p --output-format stream-json --verbose "$msg") 2>"$turn_err" \
      | tee -a "$raw_stream" \
      | node "$here/extract-assistant-text.mjs" \
      | tee -a "$transcript"
  else
    (cd "$fixture" && timeout "$per_turn" claude --model "$model" --dangerously-skip-permissions \
       --plugin-dir "$plugin_root" --settings "$settings_file" \
       --resume "$sid" -p --output-format stream-json --verbose "$msg") 2>"$turn_err" \
      | tee -a "$raw_stream" \
      | node "$here/extract-assistant-text.mjs" \
      | tee -a "$transcript"
  fi
  # PIPESTATUS[0] is the real `claude` exit status (via `timeout`), not the
  # downstream tee/node stages that always exit 0.
  turn_exit="${PIPESTATUS[0]}"
  echo "[turn $i exit=$turn_exit]" | tee -a "$transcript"

  if [ "$i" -eq 1 ] && grep -qi 'Unknown command' "$transcript"; then
    echo ""
    echo "ABORT: turn 1 printed 'Unknown command' -- the plugin did not load." >&2
    echo "Check the --plugin-dir resolution (must be the plugin root, not scripts/) and the hermetic --settings file above." >&2
    echo "transcript so far: $transcript" >&2
    echo "raw stream:        $raw_stream" >&2
    exit 1
  fi
done

echo ""
echo "transcript: $transcript"
echo "fixture:    $fixture"
echo "raw stream: $raw_stream"
echo "=== verify ==="
bash "$here/verify-transcript.sh" "$transcript" "$fixture"
