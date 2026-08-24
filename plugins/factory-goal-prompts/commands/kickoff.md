---
description: Fill the implementation kickoff template into a fresh-session prompt for one issue, with the constraints preamble and the stop condition built in
argument-hint: <issue-number> <owner/repo or path to checkout>
---

Produce a kickoff prompt for the issue and repo named here: $ARGUMENTS

You are filling a template, not implementing the issue. The output of this command is the completed kickoff prompt itself, ready to open a fresh worker session.

Steps:

1. Read the template at `${CLAUDE_PLUGIN_ROOT}/prompts/03-implementation-kickoff-prompt.md` and read the issue body (`gh issue view <N> --repo <owner/repo>`, or from the checkout's tracker).
2. Pick the register the template defines. A self-contained issue body (why-this-slice, verified anchors, write-first test plan, acceptance criteria, out-of-scope) gets Register A, the one-liner. An issue that leans on external context gets Register B, the kickoff file; if you find yourself pasting context the issue should carry, say so: the fix is to fix the issue, not to fatten the prompt.
3. Prepend the constraints preamble. Every kickoff prompt begins with the project's non-negotiable constraints, injected verbatim from wherever the project keeps them (a worker-protocol doc, CLAUDE.md, or the operator). If the project has no written preamble, emit a `PROPOSED - confirm:` preamble built from `CLAUDE.md` and repo conventions instead of skipping it. Constraint inheritance is the point: a fresh session knows only what this prompt tells it.
4. Append the stop condition. Include the following block in the produced prompt verbatim, unmodified:

```
Stop condition: when your PR is open and CI is green, post your completion
report and STOP. Do not merge your own PR. Do not pick up new work.
```

5. End the produced prompt with the report requirements: PR number, branch, one-paragraph summary, discovered follow-ups, and approximate session token usage.

Anchor note: re-verifying the issue's `file:line` anchors against current `main` is the worker's first task; say so in the produced prompt.

Output the completed kickoff prompt in a single fenced block, followed by any `PROPOSED - confirm:` items awaiting the operator.
