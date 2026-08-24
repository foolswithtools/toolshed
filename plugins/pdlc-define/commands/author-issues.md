---
description: Fill the issue-authoring goal-prompt template into a brief that splits an accepted spec into self-contained GitHub issues
argument-hint: <path to the accepted spec> [program name]
---

Produce a filled issue-authoring goal prompt for: $ARGUMENTS

You are filling a template, not authoring the issues. The output of this command is the completed goal prompt itself, ready for the operator to review and paste as the opening prompt of a fresh session. The session that runs it produces the issues via `gh`; it writes no implementation code.

Steps:

1. Read the template at `${CLAUDE_PLUGIN_ROOT}/prompts/02-issue-authoring-goal-prompt.md`.
2. Read the accepted spec named in the arguments (if no path was given, look in the repo's spec directory and ask the operator rather than guessing). Fill every `<slot>` from the spec, `CLAUDE.md`, and repo context: program name, spec path and section refs, post-spec amendments, labels.
3. Keep the template's issue-splitting rules intact and keep the pointer to the issue skeleton at `${CLAUDE_PLUGIN_ROOT}/prompts/github-issue-template.md`; every issue the downstream session files must follow that anatomy (why-this-slice, verified `file:line` anchors, "Test plan (write these first)", observable acceptance criteria, out-of-scope, blocked-by).
4. Add one line to the filled prompt's Verify section: lint every issue body before filing with `node ${CLAUDE_PLUGIN_ROOT}/scripts/lint-issue.mjs <body-file> --genre <genre> --repo <checkout>` and file only bodies that exit 0.
5. Slots you cannot fill from the spec or repo get a concrete proposal marked `PROPOSED - confirm:`, never a bare `<slot>` left in place.

The filled prompt must keep every required section of the template: the mission line, Source of truth, Task 0 (amendments and owner decisions), Issue-splitting rules, Deliverables (issues plus tracker DAG), and Verify before finishing.

Output the completed goal prompt in a single fenced block, followed by a short list of the `PROPOSED - confirm:` items awaiting the operator.
