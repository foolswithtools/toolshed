---
description: Read the OpenRouter credits balance for a pre-run or post-run check and append a row to a ledger you supply
argument-hint: <pre|post> --ledger <path> --label <run-id> [<factory-checkout>]
allowed-tools: Bash, Read
---

Check the budget for: $ARGUMENTS

Execute the shared procedure at `${CLAUDE_PLUGIN_ROOT}/prompts/budget-check.md`
against these arguments. That procedure is the single source of truth for the steps
and the pinned, verbatim invocations; the pi harness runs the same file. Do not
reimplement its steps here.

Before you act, carry the constraints preamble at
`${CLAUDE_PLUGIN_ROOT}/prompts/operator-constraints.md` verbatim (or the consuming
repo's own worker-protocol preamble, when it has one).

Wrap `${CLAUDE_PLUGIN_ROOT}/scripts/check-credits.sh`. Read credits through the
factory checkout's scoped-credential wrapper so the read gets only
`OPENROUTER_API_KEY`:

```
scripts/scoped-creds.sh pi -- bash ${CLAUDE_PLUGIN_ROOT}/scripts/check-credits.sh \
  append --ledger <ledger-path> --phase <pre|post> --label "<run id>"
```

The ledger path is always the caller's: never append to a private planning ledger
from a smoke or a demo. Report the `total_usage` figure (nine decimals), the
appended row, and, on a post read, the settled delta and its reconciliation
against `<work-dir>/.factory/last-run.txt` `model_cost`. A large divergence from
expected cost is a finding: stop and report.
