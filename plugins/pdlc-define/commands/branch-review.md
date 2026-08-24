---
description: Run the fresh-context whole-branch review of a branch or PR, hunting the cross-task wiring defects per-task reviews miss
argument-hint: [branch name, PR number, or blank for the current branch]
---

Run a whole-branch review of: $ARGUMENTS (blank means the current branch against `main`).

This command performs the review; it is the invocable form of the whole-branch-review skill. Read `${CLAUDE_PLUGIN_ROOT}/skills/whole-branch-review/SKILL.md` first and follow it exactly. The non-negotiables:

1. Fresh context is the point. The review is done by a subagent that did not write the code, briefed from `${CLAUDE_PLUGIN_ROOT}/agents/branch-reviewer.md`. If this very session authored any of the branch, you MUST dispatch the subagent rather than review inline; hand it only the branch name, the driving issue numbers, and the repo path, not your session context.
2. Resolve the target first: a PR number means check out or fetch its head branch; a branch name means that branch. Scope is the ENTIRE branch diff, `git diff main...HEAD` (plus `git log main..HEAD` for intent), never per-commit.
3. The reviewer works the skill's hunt list in priority order: reachability wiring, deploy wiring, cross-slice contract drift, second doors, real-surface behavior, issue fidelity. Load-bearing claims carry pasted grep or command evidence (construction-site searches especially).
4. The verdict is explicit and unhedged: **READY TO MERGE** with what was checked and how, or **BLOCKERS** as a numbered list, each with `file:line`, the failure scenario, and the check that will prove the fix. Blockers are fixed on the branch and the review re-run from scratch; non-blocking findings become follow-up issues, not merge conditions.
5. Relay the verdict to the operator unedited, and record it in the PR body's Process section if a PR exists.

Never declare READY TO MERGE on the author's own read of the diff; that is the contamination this pass exists to remove.
