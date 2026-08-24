---
description: Run the plugin's issue-body linter against a draft issue body and report its findings and exit code
argument-hint: <body-file> [--genre feature|bug|bootstrap|decision] [--title "..."] [--repo <root>] [--plan-root <root>] [--config <schema.json>]
allowed-tools: Bash(node:*)
---

Lint an issue body: $ARGUMENTS

Run the plugin's linter exactly as given, passing the arguments through unchanged:

```
node "${CLAUDE_PLUGIN_ROOT}/scripts/lint-issue.mjs" $ARGUMENTS
```

Rules:

1. If no body file was given, ask the operator for one; do not invent a path.
2. Run the script once via the Bash tool and capture both its output and its exit code (append `; echo "exit code: $?"` to observe it).
3. Report faithfully: paste the linter's output verbatim, then state the exit code. Exit 0 means the body is clean; exit 1 means findings. The command's verdict IS the linter's exit code; never soften a finding into a suggestion or declare a body clean when the exit code was nonzero.
4. Do not edit the body file unless the operator asks. If they do ask, fix only what a finding names, re-run the linter, and report the new exit code the same way.

The same script runs automatically inside the `/author-issues` flow; this command exists to run it standalone against any draft body.
