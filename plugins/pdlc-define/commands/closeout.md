---
description: Walk the close-out checklist for merged work (follow-ups, docs, lessons) and fill a handoff prompt when work continues elsewhere
argument-hint: [issue or PR number just completed]
---

Close out: $ARGUMENTS (blank means the unit of work just merged in this session; identify it from the branch and recent PRs and confirm with the operator).

This command executes the close-out step of the lifecycle in `${CLAUDE_PLUGIN_ROOT}/skills/issue-driven-development/SKILL.md`. Read that skill's "Close out" list first; none of its items are optional. Work through them in order and report evidence for each:

1. **Follow-up issues.** Everything deferred or discovered during the work gets filed as its own issue (using the anatomy in `${CLAUDE_PLUGIN_ROOT}/prompts/github-issue-template.md`). List what you filed with issue numbers, or state explicitly that a sweep of the PR body, review verdicts, and TODO comments found nothing to file.
2. **Docs hygiene.** Sync every doc the repo's CLAUDE.md and the driving issue's "Docs (definition of done)" section name: features doc, api-reference, roadmap marker; bugs additionally get a resolved-issues entry naming the regression test. List each file touched or state why none applied.
3. **Lessons and cross-session state.** Extract what the next session must know that the repo does not yet say, per `${CLAUDE_PLUGIN_ROOT}/skills/context-layering/SKILL.md`: repo-wide lessons into CLAUDE.md or docs, process lessons into their own issues (failure honesty applies: lapses get filed, not buried).
4. **Handoff, when work continues elsewhere.** If the work continues in another session, repo, or machine, fill `${CLAUDE_PLUGIN_ROOT}/prompts/04-handoff-goal-prompt.md` from this session's verified facts and output the completed handoff prompt in a fenced block; slots you cannot verify get `PROPOSED - confirm:`, never a silent guess. If nothing continues elsewhere, say so and skip this step.

Finish with a checklist summary: each of the four items above, done or not-applicable, with the evidence (issue numbers, file paths, the handoff block). A close-out that skipped an item without saying why is not done.
