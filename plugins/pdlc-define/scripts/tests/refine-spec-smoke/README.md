# refine-spec cold-session smoke

The acceptance evidence for the `/refine-spec` command (issue #34). Toolshed has
no CI, so this smoke is a reproducible harness plus a recorded transcript, not a
gate that runs on every push. It drives a real model and is deliberately kept
out of the no-model unit suites.

## What it proves

A cold session with only pdlc-define installed, pointed at a deliberately flawed
vision document, runs `/refine-spec` and demonstrates every clause of the
command's contract from the transcript and the resulting working tree:

- **Layer 1 (facilitator):** restates the owner's position before challenging
  it, and brings a steelmanned counter-position, not only questions.
- **Layer 2 (critics):** casts critics from the repo's `docs/panel/` personas,
  capped at the dispute, run sequentially with no cross-visibility before each
  commits its critique.
- **Layer 3 (researcher):** dispatched for the single bounded factual dispute
  (the SQLite concurrency claim), returns a source-attached finding, and the
  facilitator verifies the citation against the retrieved text before it lands.
- **Editing contract:** every edit is proposed one at a time with a one-line
  rationale and lands only on an explicit accept (the run also exercises a
  modify then accept); silence is never acceptance; zero silent edits.
- **Session state and scope guard:** the decision log gains a proposed,
  **unstamped** entry (D-001 and D-002 stay stamped); no issues are filed, no
  new documents are created, `/author-issues` is not run.

## Files

- `build-fixture.sh <dir>` builds the fixture: a `docs/VISION.md` with three
  stances (one defensible, one factually wrong, one vague), a two-entry decision
  log, a `docs/panel/` of two persona memos, and a `CONVENTIONS.md` declaring a
  document-economy rule and a no-em-dash style gate. Everything is synthetic.
- `verify-transcript.sh <transcript> <fixture>` is the check set. It was written
  before the command existed and failed against a no-command transcript (17+
  clauses unproven), then passes against a real session transcript. It greps the
  transcript for the command's visible session-state vocabulary (`RESTATE:`,
  `STEELMAN:`, `CRITIC ...`, `RESEARCHER ...`, `PROPOSED EDIT` / `Rationale:`,
  `EDIT LANDED`, proposed-unstamped decision entries) and inspects the fixture
  tree for the scope-guard proofs. It tolerates a session folding a `CAST` or
  `DISPATCH` announcement into its `RETURNED` record: a committed critique or
  finding proves the critic was cast or the researcher dispatched.
- `run-smoke.sh [workdir]` builds the fixture, loads the plugin from this
  checkout with `--plugin-dir`, disables any user-scope install of the same
  plugin for the session (see Hermeticity below), drives the scripted human
  turns over `claude -p --resume` with `--output-format stream-json
  --verbose`, extracts the transcript from the full assistant event stream,
  and runs the checks. It aborts immediately if turn 1 prints `Unknown
  command` (plugin failed to load) instead of driving six more turns of a
  plain chat session. It skips (exit 0) when `claude` is not on `PATH`.
- `extract-assistant-text.mjs` reads a turn's stream-json event log from
  stdin and writes the text of every assistant message to stdout, in order.
  This is what lets the transcript capture protocol markers emitted ahead of
  a mid-turn tool call, not only each turn's final message.
- `build-hermetic-settings.mjs` reads `claude plugin list --json` from stdin
  and writes a `--settings` file that disables every installed plugin
  literally named `pdlc-define`, regardless of which marketplace nickname it
  was installed under, so the checkout loaded by `--plugin-dir` always wins.
- `sample-transcript.md` is a recorded passing run, path-scrubbed, kept as
  durable evidence for reviewers who do not want to spend a live model run.

## Hermeticity

A user-scope install of pdlc-define otherwise wins over `--plugin-dir` and
can silently shadow this checkout with a stale version, so the command in
turn 1 either fails outright or resolves to the wrong plugin version.
`run-smoke.sh` builds a per-run `--settings` file (via
`build-hermetic-settings.mjs`) that disables any such install for the
session, so the checkout is what actually runs regardless of what else is
installed on the machine.

## Harness portability

The command tells the session to use its subagent primitive for critics and
researchers (Claude Code Task/Agent tooling in this smoke), and documents the
graceful degradation to inline role-switching for harnesses with no subagent
primitive (pi consumers). The recorded run uses Claude Code, so the critics and
researcher run as real subagents.
