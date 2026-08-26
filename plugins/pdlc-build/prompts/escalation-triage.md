# escalation-triage: turn an escalation into a fixed issue or a documented retry

When a run escalates, walk the recorded reasons and produce one of two honest
outcomes: a corrected issue body (fix the issue, not the prompt) that a fresh
run could land, or a documented decision to retry as-is with the reason it is
worth another attempt. A shrug is not an outcome. This is the shared procedure
both harnesses run.

Prepend the constraints preamble (`operator-constraints`) before you act.

## Inputs

- The work directory of the escalated run.
- The original issue or work item the run was submitted with (its body is what you
  will correct).

## Pinned factory invocations (verbatim)

Pinned at authoring time against factory `main` (`factory 0.1.0`, commit
`ff10bd0`).

1. Read the escalated run's verdict and reasons:

   ```
   factory status <work-dir>
   ```

   The machine-readable reasons live in the verdict file at
   `<work-dir>/.factory/verdicts/<work_item_id>/<attempt_id>.verdict`; the `reason`
   line names which leg failed and why (for example `blocking gate(s) failed:
   <gates>` for a confidence-leg failure, or `governance: <policy>` for a
   governance-leg refusal).

## What escalation looks like

A run escalates (outcome `Escalated`, `land = false`) when a leg does not clear.
The three shapes, and what each tells you:

- **Confidence-leg failure** (`confidence_land = false`): the app's blocking gates
  failed against the attempt worktree, or the held-out rate fell below its
  threshold, or the gap exceeded its gap-threshold. Read `validation_rate`,
  `heldout_rate`, and `gap`. A `validation_rate` of 0 with an under-specified issue
  usually means the agent could not build a coherent candidate: the fix is a
  clearer issue, not a re-prompt.
- **Governance-leg refusal** (`governance_cleared = false`): the policy gate
  declined the run's scope. This is a scope or authority question, not a code
  question; route it, do not paper over it.
- **Routing refusal** (no verdict written, `framework-portability: FAIL`): factory
  refused the work item's declared type before running. Fix the type declaration.

## Steps

1. Read the verdict with the pinned invocation above and enumerate every reason,
   quoted, from the `reason` line and the two legs' fields.
2. For each reason, decide: does it point at the issue (under-specified, wrong
   scope, missing acceptance detail) or at a transient condition (a flaky external
   dependency, a resource limit hit)?
3. **If the issue is at fault, rewrite it.** Produce a corrected issue body that
   names the acceptance the run could not meet, following the pdlc-define issue
   anatomy (why-this-slice, verified anchors, write-first test plan, observable
   acceptance criteria, out-of-scope). The corrected body must pass the
   pdlc-define linter before you hand it back:

   ```
   node <pdlc-define>/scripts/lint-issue.mjs <corrected-body-file> --genre <genre> --repo <checkout>
   ```

   (`<pdlc-define>` is wherever the pdlc-define plugin is installed; pdlc-build
   consumes that linter, it does not ship its own.) Report the linter's exit code;
   exit 0 is the bar. Do not soften a finding into a suggestion.
4. **If a retry as-is is the right call, document it.** State the transient reason,
   what will be different next time, and the spend a retry costs (a retry is a
   fresh metered run: read credits before and after per the constraints preamble).
   A retry with no changed condition and no written reason is not a decision.

## Report

Report the enumerated reasons, the verdict path, and the outcome you chose: either
the corrected issue body (in a fenced block) with the linter exit code, or the
documented retry decision with its transient reason and expected spend. Fix the
issue, not the prompt.
