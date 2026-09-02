# toolsmith: a session-to-skill capture plugin

**Status:** design, awaiting review
**Date:** 2026-08-28
**Repo home:** `plugins/toolsmith/` (new plugin in this marketplace)

## Goal

Close a loop around Claude Code sessions so that a useful, repeatable process
you work out in a session does not evaporate when the session ends. Two halves:

1. **Retrieval:** at the start of a session, surface what the toolshed already
   holds, so you check for an existing tool before rebuilding one.
2. **Capture:** on demand (and with a nudge so you do not forget), review the
   session, and if it contains a repeatable method worth keeping, turn it into a
   reusable artifact (a skill, an agent, a slash command, or a rule) with your
   approval.

The user runs Claude Code heavily and repeatedly re-derives the same processes.
The cost being paid today is re-derivation and lost method. The tool exists to
turn a hard-won method into something the next session can pick up.

## Background: what the prior art tells us

This space is crowded. At least five shipping Claude Code projects already do
some form of session-to-skill capture (retro-skill, self-learning-skills,
self-improving-agent, Hivemind, and others), plus a commercial product and a
2025-26 academic subfield on procedural memory for agents. The idea is not novel
as a category. What is still contested is the design, and that is where the
value is.

The findings that shaped this design, with the evidence behind them:

- **Silent background capture drowns in noise.** The one hard data point in the
  survey: retro-skill's predecessor used continuous background capture and
  produced 1,011 pending candidates, 0 approved, a 35 MB database, and roughly
  35x duplicates of the same issue. Field consensus, including from the tool
  authors, is "start manual, then automate."
- **The approval gate is the feature people demand the moment auto-capture
  exists.** The most-viral write-first tool (self-learning-skills) has an
  unanswered top issue asking for exactly the per-proposal gate that the more
  engineered tool (retro-skill) already ships.
- **Capture the method, not the answer.** The cleanest stated heuristic:
  "how to find the right tables and build the query" is a good skill; "join
  orders to customers for EMEA" is a bad one, because it transfers an answer
  with no reusable procedure.
- **Redaction is the under-defended failure mode.** One tool with real adoption
  shipped a token-exfiltration incident. Skill files get committed, so a secret
  written into one leaks. Record the location of a secret, never its value.
- **No tool in the category has verified daily-use stickiness, and "never
  reused" plus "near-duplicate spam" are the two failure modes with filed
  evidence.** Treat reuse as something to measure, not assume.

Human process-improvement practice points the same way. The through-line across
the Army After-Action Review, Toyota's standard work, PDCA, and personal
knowledge management is that the enemy is write-only capture. Every practice that
endured paired cheap capture with a deliberate, gated, owned path from a captured
observation to a reused standard, and pruned what stopped being used. The Army
distinction is exact: an observation is not yet a lesson learned, promotion is a
separate validated step.

## Design principles

These are the load-bearing rules the implementation follows.

1. **Manual trigger, no silent capture.** The heavy work runs only when the user
   asks (`/crystallize`) or approves. No per-turn model-driven detection.
2. **Two tiers with a gate between them.** Capture drafts to a personal staging
   area. Promotion into the committed, public toolshed repo is a separate
   deliberate act. An observation is not yet a standard.
3. **Per-proposal approval, no silent writes.** Every materialized file needs an
   explicit approve / edit / reject.
4. **Capture the method, not the answer.** Every drafted skill passes a
   portability test: read it without the original context; would it still help in
   a repo you have never seen?
5. **Redaction is default-on.** Record where a secret lives (env var, MCP tool,
   selector), never its value.
6. **Killer items, not transcripts.** A captured process distills to the few
   steps a capable agent would otherwise skip, not a replay of everything done.
7. **Cap the output.** At most a small number of proposals per run, so the user
   never faces a wall.
8. **Context is a public good.** The session-start injection stays short; every
   token of injected context has a measured accuracy cost.

## Architecture

One plugin, `toolsmith`, with three parts. It does one job (turn session work
into reusable toolshed artifacts and help you find existing ones), consistent
with the marketplace convention of one job per plugin.

### Part A: the toolshed check (retrieval)

A `SessionStart` hook runs a script that enumerates installed toolshed skills,
plugins, and agents (name plus description only) and injects a short note into
the session: here is what the toolshed holds; if the current task looks
repeatable, check whether one of these already helps before building from
scratch.

- Deterministic shell work, no model call.
- Output is kept short by design (names and one-line descriptions, not bodies).
- Also exposed as a manual `/toolshed` command for when the injection is not
  wanted or the user wants to re-list mid-session.

Assumption to verify during implementation: that a `SessionStart` hook in this
Claude Code version can inject context the main agent sees (via the hook's JSON
output / additionalContext mechanism). If that mechanism is unavailable or
changes, Part A degrades to the manual `/toolshed` command with no loss to Parts
B and C.

### Part B: /crystallize (gated capture)

A manual command (a skill with `disable-model-invocation: true` so it never
auto-fires; capture has side effects). When invoked, Claude works from its own
in-context memory of the current session, not by parsing the on-disk JSONL
transcript (which lags and is version-fragile). The flow:

1. **Frame as a delta (AAR).** What was the session trying to do, what actually
   happened, and what is the reusable method inside it.
2. **Apply the quality gate.** A candidate earns artifact status only if it has:
   - a verified success (a check that actually passed; "seemed to work" does not
     count),
   - a named failure pattern it prevents, and
   - ideally a ruled-out dead-end.
   Candidates that fail the gate are reported as "not worth capturing" with a
   one-line reason, not silently dropped.
3. **Redact.** A default-on pass replaces any secret value with a reference to
   its location. Runs before anything is shown or written.
4. **Route each candidate to one home.** In priority order: update an existing
   skill, a new skill, an agent, a slash command, a CLAUDE.md rule, or nothing.
   Prefer patching an existing tool over spawning a near-duplicate.
5. **Draft.** For a new skill, distill to killer items, run the portability test,
   and write the SKILL.md following Anthropic's public authoring rules (gerund
   name, third-person "Use when..." description with the key use case first,
   body under ~500 lines, no hardcoded paths or secrets, verbatim key error
   strings since people search by error message). Delegate to
   `superpowers:writing-skills` when that skill is present, since it encodes
   these rules; fall back to applying them directly otherwise.
6. **Approve per proposal.** Present each candidate with approve / edit / reject.
   Cap at a small number per run (target: at most 5).
7. **Write to staging.** Approved artifacts land in the personal staging area
   (default: `~/.claude/skills/<name>/` for skills, with the equivalent
   user-level locations for agents and commands). Nothing is written into this
   committed repo by `/crystallize`.

### Part C: the exit reminder (mechanical safety net)

A `SessionEnd` hook that checks cheap, deterministic signals and, if a threshold
is crossed, prints a one-line reminder: this session looked substantial, worth a
`/crystallize`? It makes no model call and captures nothing. Signals, borrowed
from retro-skill's friction catalog:

- session length over a word/turn threshold (default around 1,000 words),
- repeated tool-retry clusters (>= 3 similar retries),
- file re-reads without an intervening edit (>= 2),
- permission re-approvals (>= 3).

Honest limitation: a `SessionEnd` hook cannot pause `/exit` and hold an
interactive prompt. The reminder prints on the way out. That is enough to keep a
substantial session from leaving without asking, which is the stated need.

## Promotion: staging to committed toolshed

Separate from `/crystallize`, a `/promote` command (or a documented manual step)
moves a staged skill into `plugins/<...>/` in this repo, adds or updates the
`marketplace.json` entry, bumps the plugin version, and re-runs the repo
guardrails. This is the deliberate, gated second tier. It is deliberately not
automatic, matching the observation-vs-standard distinction and keeping immature
or secret-bearing drafts out of a public repo.

Promotion is lighter in v1: the command may simply guide the user through the
steps and run the checks rather than fully automating the marketplace edit. The
gate (a human decision to promote) is the part that must exist; the automation
around it can grow later.

## File layout

```
plugins/toolsmith/
  .claude-plugin/plugin.json
  hooks/hooks.json                      # SessionStart (Part A), SessionEnd (Part C)
  skills/crystallize/SKILL.md           # Part B, disable-model-invocation: true
  skills/toolshed/SKILL.md              # manual /toolshed listing
  skills/promote/SKILL.md               # staging -> committed repo (optional v1)
  scripts/list-toolshed.sh              # enumerate installed skills/plugins/agents
  scripts/friction-scan.sh              # cheap SessionEnd signal check
  config.json                           # thresholds (word count, retry counts)
  README.md
```

Plus a new entry in `.claude-plugin/marketplace.json`.

## Error handling and limitations

- **Transcript access:** the design avoids parsing the JSONL transcript. If a
  future feature needs it, expect lag and version-fragility, and prefer the
  hook-provided `last_assistant_message` fields.
- **Hook context injection:** if `SessionStart` injection is unavailable, Part A
  falls back to the manual `/toolshed` command.
- **Redaction is best-effort.** It reduces the leak risk but is not a guarantee.
  The staging-first default is the real safety margin: nothing reaches the public
  repo without a human promotion step.
- **Abstraction level stays a judgment call.** No source has a mechanical rule.
  The portability test and Anthropic's degrees-of-freedom framing (exact steps
  for fragile tasks, reasoning plus a default with an escape hatch for open ones)
  are the guides, applied by the model and checked by the user at approval.

## Testing

- **Part A:** `list-toolshed.sh` against a fixture toolshed directory produces the
  expected name/description list; output stays under a size budget.
- **Part C:** `friction-scan.sh` against synthetic session inputs fires the
  reminder exactly when a threshold is crossed and stays silent otherwise
  (boundary cases at each threshold).
- **Part B:** the quality gate is exercised with worked session examples: a
  genuine reusable method (should propose), a one-off answer (should decline with
  a reason), and a session containing a secret (redaction must fire before any
  output). Portability test and per-proposal approval are checked on the
  proposals.
- **Guardrails:** `scripts/check-no-anthropic-remotion-claim.sh` passes; every
  touched JSON validates.

## Out of scope for v1

- Automatic (non-manual) capture of any kind.
- Cross-session recurrence mining.
- Reuse instrumentation (tracking whether a captured skill is later invoked).
  Flagged by the research as a real gap and a strong candidate for v2, but it
  adds scope and is not needed to prove capture quality first.
- A Pi (pi.dev) port. Pi has session-start bootstrapping already (via the
  pi-superpowers package) but no session-end event, so the capture half would
  need a different trigger there. Out of scope now, noted as possible later.

## Open questions

None blocking. The two assumptions to confirm early in implementation are the
`SessionStart` injection mechanism and the exact `SessionEnd` hook payload
available in the target Claude Code version; both have documented fallbacks
above.
