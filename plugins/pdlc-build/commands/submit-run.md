---
description: Hand a GitHub issue to a running factory as a work item, start the run under a real work-item id, and report the run id
argument-hint: <owner/repo>#<number> <factory-checkout> <work-dir> [--mock]
allowed-tools: Bash, Read, Write, Edit
---

Submit a run for: $ARGUMENTS

Execute the shared procedure at `${CLAUDE_PLUGIN_ROOT}/prompts/submit-run.md`
against these arguments. That procedure is the single source of truth for the
steps and the pinned, verbatim factory invocations; the pi harness runs the same
file. Do not reimplement its steps here.

Before you act, carry the constraints preamble at
`${CLAUDE_PLUGIN_ROOT}/prompts/operator-constraints.md` verbatim (or the consuming
repo's own worker-protocol preamble, when it has one, and say which you used).

Notes for this harness:

- Fetch the issue body with `gh issue view <number> --repo <owner/repo> --json
  title,body`. If the issue is not on GitHub, read the local issue file the
  operator names instead.
- A live run (`backend = pi`, `model = z-ai/glm-5.3`, `effort = high`) spends real
  credits: run `/budget-check pre` first, launch through the factory checkout's
  `scripts/scoped-creds.sh pi -- ...` wrapper, and stay in-session until the run
  process exits. Pass `--mock` to run `backend = mock` for a zero-spend structural
  check.
- Read the run id back from `<work-dir>/.factory/last-run.txt` (`work_item_id`
  plus `attempt_id`) and report it, the outcome, and the verdict file path. Hand
  the verdict to `/run-status` rather than judging land yourself.
