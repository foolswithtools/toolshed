---
name: operating-factory-runs
description: Use when driving work through a running factory as an operator - submitting a GitHub issue as a factory run, reading a run's verdict, triaging an escalation, or checking credits before and after a metered run. The recurring actions a person takes against a factory that has landed work for real, as opposed to authoring the issue in the first place (that is pdlc-define).
---

# Operating factory runs

## Overview

Once a factory lands work for real, an operator has four recurring actions that
were raw shell rituals before this plugin packaged them: hand a GitHub issue to
factory as a run, watch the run and read its verdict honestly, triage an
escalation into a fixed issue rather than a shrug, and check spend before and
after. This skill is the discipline behind those four actions; each action's exact
steps and its pinned, verbatim factory invocations live in a shared procedure both
harnesses run.

## The line: define versus build

pdlc-define owns the issue discipline (writing a self-contained issue is valuable
with or without a factory). pdlc-build owns the actions a person takes against a
*running* factory. If you are writing the issue, that is pdlc-define. If you are
handing an already-written issue to factory and reading what came back, that is
here.

## The four actions

| Action | Procedure | What it does |
|---|---|---|
| submit-run | `prompts/submit-run.md` | Fetch a GitHub issue, write it as a factory work item under a real work-item id (`gh-<owner/repo>#<n>`), start the run, report the run id |
| run-status | `prompts/run-status.md` | Read the run's verdict and present the two scores and the confidence legs without collapsing them |
| escalation-triage | `prompts/escalation-triage.md` | Walk an escalated run's reasons and produce a corrected issue body (that lints clean) or a documented retry decision |
| budget-check | `prompts/budget-check.md` | Read credits pre-run and post-run and append a row to the caller's ledger |

In Claude Code these are the `/submit-run`, `/run-status`, `/escalation-triage`,
and `/budget-check` commands. In pi they are the same procedure files, invoked as
prompts. Both harnesses read the one shared copy under this plugin; nothing is
duplicated per harness.

## The non-negotiables

- **Consume the factory interface, do not modify it.** These actions run `factory
  init`, `factory run`, and `factory status` and read what they write. A run that
  needs a factory change is a finding, not a reason to edit factory.
- **A live run spends real money.** `backend = pi` calls a paid model through
  OpenRouter. Read credits before and after every metered run, record both, honor
  the cap, and stop spending if a settled cost would cross it.
- **Read the verdict honestly.** The two scores (`framework-portability` and
  `app-buildability`) are separate by design, and `land` is a two-leg AND of the
  confidence leg and the governance leg. Never merge the scores into one number or
  hide which leg failed. Carry the `thresholds: uncalibrated defaults` banner when
  factory prints it.
- **Escalation means fix the issue, not the prompt.** An under-specified issue that
  escalates gets rewritten to a body a fresh run could land; a re-prompt against the
  same broken issue is not triage.
- **Never end a turn with a live run in flight.** A run killed by an ending session
  wastes its spend. Run in the foreground or poll in-session until it settles.
- **The human holds the merge gate.** Report the branch factory created on a real
  land; do not merge on the operator's behalf.

## Prerequisites for a live run

- A factory checkout with the `factory` binary built and its
  `scripts/scoped-creds.sh` credential wrapper (see the factory checkout's
  `docs/QUICKSTART.md` and `docs/CREDENTIALS.md`).
- Docker, for the agent container and the held-out executor. Build the pi agent
  image with the factory checkout's `scripts/build-agent-pi-image.sh`; the held-out
  executor pulls a node-bearing image on first use.
- An OpenRouter key provisioned in the factory checkout's encrypted secret store,
  injected least-privilege by `scripts/scoped-creds.sh pi`.

## Constraints preamble

Every action prepends the operator constraints preamble
(`prompts/operator-constraints.md`). A consuming repo with its own written
worker-protocol document supersedes it; when the repo has none, the default is
carried and marked `PROPOSED - confirm:` for the operator to ratify.
