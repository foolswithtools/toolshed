---
description: Walk an escalated run's recorded reasons and produce either a corrected issue body that lints clean or a documented retry decision
argument-hint: <work-dir> <original-issue-or-body-file>
allowed-tools: Bash, Read, Write
---

Triage the escalation for: $ARGUMENTS

Execute the shared procedure at `${CLAUDE_PLUGIN_ROOT}/prompts/escalation-triage.md`
against these arguments. That procedure is the single source of truth for the steps
and the pinned, verbatim factory invocations; the pi harness runs the same file. Do
not reimplement its steps here.

Before you act, carry the constraints preamble at
`${CLAUDE_PLUGIN_ROOT}/prompts/operator-constraints.md` verbatim (or the consuming
repo's own worker-protocol preamble, when it has one).

Read the escalated verdict with `factory status <work-dir>`, enumerate every reason
from the verdict file, and decide per reason whether the issue is at fault or a
retry is warranted. When the issue is at fault, rewrite it to the pdlc-define issue
anatomy and lint the corrected body with the installed pdlc-define linter (`node
<pdlc-define>/scripts/lint-issue.mjs <body> --genre <genre> --repo <checkout>`);
exit 0 is the bar. Fix the issue, not the prompt. When a retry as-is is the right
call, document the transient reason and the spend it costs. Report the reasons, the
corrected body with its linter exit code, or the documented retry decision.
