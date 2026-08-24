---
description: Fill the implementation kickoff template into a fresh-session prompt for one issue, with the constraints preamble and the stop condition built in
argument-hint: <issue-number> <owner/repo or path to checkout>
allowed-tools: Bash(node:*), Bash(gh issue view:*), Bash(gh issue comment:*)
---

Produce a kickoff prompt for the issue and repo named here: $ARGUMENTS

You are filling a template, not implementing the issue. The output of this command is the completed kickoff prompt itself, ready to open a fresh worker session.

## Step 0: mandatory preflight (run before anything else)

Before touching the template, run the kickoff preflight over the fetched issue body. This is not optional and it is not advisory: a failed preflight means this command produces no kickoff prompt at all.

1. Fetch the issue body into a file: `gh issue view <N> --repo <owner/repo> --json body -q .body > <tmp-file>` (or, for a local issue file, use it directly).
2. Run `node "${CLAUDE_PLUGIN_ROOT}/scripts/kickoff-preflight.mjs" <tmp-file> --genre <genre> --repo <path to the checkout named in $ARGUMENTS>` (add `--plan-root`, `--config`, or `--pattern-config` only if the repo's conventions require them).
3. On exit 0 (`PREFLIGHT PASS`): the printed anchor-freshness lines confirm every `Existing:` anchor still points at the symbol it names. Carry that PASS line and the anchor-freshness lines forward as the first thing prepended to the produced kickoff prompt's context, so the worker session knows the anchors were verified and does not have to re-derive that from scratch.
4. On exit nonzero (`PREFLIGHT REFUSED`): refuse to start. Do not proceed to step 1 below and do not emit a kickoff prompt.
   - If the issue lives on GitHub, post the preflight's finding list as an issue comment: `gh issue comment <N> --repo <owner/repo> --body "<the PREFLIGHT REFUSED output>"`.
   - If it is a local issue file, print the finding list to the operator instead.
   - Report which fixture-shaped problem it was (rotted anchor, missing section, or another linter finding) and stop. A refused kickoff starts no worker.

Only continue to the steps below once the preflight has printed `PREFLIGHT PASS`.

Steps:

1. Read the template at `${CLAUDE_PLUGIN_ROOT}/prompts/03-implementation-kickoff-prompt.md` and read the issue body (`gh issue view <N> --repo <owner/repo>`, or from the checkout's tracker).
2. Pick the register the template defines. A self-contained issue body (why-this-slice, verified anchors, write-first test plan, acceptance criteria, out-of-scope) gets Register A, the one-liner. An issue that leans on external context gets Register B, the kickoff file; if you find yourself pasting context the issue should carry, say so: the fix is to fix the issue, not to fatten the prompt.
3. Prepend the constraints preamble, and after it the preflight's PASS result and anchor-freshness lines from Step 0. Every kickoff prompt begins with the project's non-negotiable constraints, injected verbatim from wherever the project keeps them (a worker-protocol doc, CLAUDE.md, or the operator). If the project has no written preamble, emit a `PROPOSED - confirm:` preamble built from `CLAUDE.md` and repo conventions instead of skipping it. Constraint inheritance is the point: a fresh session knows only what this prompt tells it, including that its anchors were already verified.
4. Append the stop condition. Include the following block in the produced prompt verbatim, unmodified:

```
Stop condition: when your PR is open and CI is green, post your completion
report and STOP. Do not merge your own PR. Do not pick up new work.
```

5. End the produced prompt with the report requirements: PR number, branch, one-paragraph summary, discovered follow-ups, and approximate session token usage.

Anchor note: Step 0 already re-verified the issue's `file:line` anchors against current `main`, host-side, before this prompt was produced (anchors are unreachable from inside agent containers, so that check has to happen here, not in the worker). Say so in the produced prompt rather than asking the worker to redo it.

Output the completed kickoff prompt in a single fenced block, followed by any `PROPOSED - confirm:` items awaiting the operator.
