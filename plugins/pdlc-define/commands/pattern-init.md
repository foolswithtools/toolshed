---
description: Scaffold the goal-prompt pattern structure (.pattern-config.json, spec and known-issues dirs, roadmap stub, CLAUDE.md hygiene section) in an approved target repo
argument-hint: <target-repo-root>
---

# /pattern-init

Initialize a repo for the pdlc-define pattern.

## Guard: approved repos only

This command writes files into the target repo. Run it only inside a repo the
user has explicitly named for initialization in this conversation. If the
target is missing, ambiguous, or not clearly the repo the user asked to
initialize, stop and ask; never guess a directory and never run it on a repo
you merely happen to have open.

## Steps

1. Resolve the target repo root from the arguments: `$ARGUMENTS`. It must be an
   existing directory; confirm it is the repo the user asked to initialize.
2. If the target already has a `.pattern-config.json`, tell the user their
   config will be kept and used as-is; otherwise say the template defaults from
   `${CLAUDE_PLUGIN_ROOT}/config/pattern-config.example.json` will be written
   for them to edit.
3. Run:

   ```
   bash ${CLAUDE_PLUGIN_ROOT}/scripts/pattern-init.sh <target-repo-root>
   ```

   The script is idempotent: it writes `.pattern-config.json` if absent,
   validates it, creates the declared `spec_dir` and `known_issues_dir`,
   creates a roadmap stub at `roadmap_path`, and appends a
   documentation-hygiene section to CLAUDE.md exactly once. A second run on an
   initialized repo reports `pattern-init: no-op`.
4. Report the script output verbatim: each created/exists line, and whether the
   run used the repo's own config or the template defaults.
5. If the script exits non-zero on an invalid existing config, show the
   validation findings and offer to fix `.pattern-config.json` (schema:
   `${CLAUDE_PLUGIN_ROOT}/config/pattern-config.schema.json`), then re-run.
6. Remind the user the created files are unstaged; they choose what to commit.
