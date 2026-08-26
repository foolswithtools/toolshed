---
description: Read a factory run's verdict and present both scores and both confidence legs honestly, without collapsing them
argument-hint: <work-dir> [<work-item-id> <attempt-id>]
allowed-tools: Bash, Read
---

Report the run status for: $ARGUMENTS

Execute the shared procedure at `${CLAUDE_PLUGIN_ROOT}/prompts/run-status.md`
against these arguments. That procedure is the single source of truth for the
steps and the pinned, verbatim factory invocations; the pi harness runs the same
file. Do not reimplement its steps here.

Before you act, carry the constraints preamble at
`${CLAUDE_PLUGIN_ROOT}/prompts/operator-constraints.md` verbatim (or the consuming
repo's own worker-protocol preamble, when it has one).

Read the run with `factory status <work-dir>` and the verdict file it names. Report
the two scores (`framework-portability` and `app-buildability`) verbatim and
separately, the two legs (`confidence_land` and `governance_cleared`) separately,
the numeric rates, and the full `reason`. Never average the two scores or hide
which leg failed. If the run escalated, point at `/escalation-triage`.
