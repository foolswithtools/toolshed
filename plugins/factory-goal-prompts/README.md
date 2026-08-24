# factory-goal-prompts

Goal-prompt driven development for Claude Code: every unit of work gets a written, self-contained spec that a fresh agent with zero context can execute. The discipline works on any project, but it is built for factory projects (the pattern plus the factory pipeline). Extracted from a five-month production project (2026): hundreds of merged PRs, none abandoned, every one driven by a written spec.

## What it ships

| Path | What it is |
|---|---|
| `skills/issue-driven-development/` | The full lifecycle as an executable process: research, decide, author issues, kick off, execute, review, merge, close out |
| `skills/writing-goal-prompts/` | Authoring goal prompts a cold agent can execute without asking what you meant |
| `skills/whole-branch-review/` | The fresh-context merge safety net that catches cross-task wiring defects green suites miss |
| `skills/context-layering/` | Where context lives (issues vs repo docs vs agent memory) and the lesson loop |
| `agents/issue-author.md` | Turns an accepted spec into self-contained, PR-able GitHub issues plus a tracker DAG |
| `agents/slice-implementer.md` | Executes exactly one TDD slice under a fixed wire contract and allowed-files list |
| `agents/branch-reviewer.md` | Whole-branch, cross-task-wiring review before merge |
| `prompts/01-research-goal-prompt.md` | Template: research phase producing a decision-ready spec |
| `prompts/02-issue-authoring-goal-prompt.md` | Template: split an accepted spec into GitHub issues (no code) |
| `prompts/03-implementation-kickoff-prompt.md` | Template: kick off execution of an issue in a fresh session |
| `prompts/04-handoff-goal-prompt.md` | Template: hand work to a zero-context successor session or repo |
| `prompts/github-issue-template.md` | The issue-body skeleton (feature-slice, bug, and bootstrap genres) |
| `prompts/pr-body-template.md` | The PR-body skeleton with evidence sections |
| `scripts/lint-issue.mjs` | Dependency-free issue-body linter (with `scripts/schema.json`) |
| `scripts/check-links.sh` | Repo-side check that no skill or agent references anything outside the plugin |
| `scripts/tests/` | The linter's self-test suite (`sh scripts/tests/run-tests.sh`) |

## Install

```
/plugin marketplace add https://github.com/foolswithtools/toolshed.git
/plugin install factory-goal-prompts@toolshed
```

The skills load on demand; the agents register as subagents. Prompt templates resolve from `${CLAUDE_PLUGIN_ROOT}/prompts/`.

## The pattern in one paragraph

Work flows through a fixed lifecycle: a research goal prompt produces a decision-ready spec in the repo; open decisions are resolved with the owner and recorded; an issue-authoring goal prompt splits the spec into self-contained, PR-able GitHub issues before any code; each issue is executed in a fresh session under TDD with subagent slices; a fresh-context whole-branch review guards the merge; the human holds the merge gate; close-out extracts lessons, syncs docs, and, when work continues elsewhere, writes a handoff goal prompt for the next zero-context agent. Transcripts are disposable; the repo is the memory.

## The linter

`scripts/lint-issue.mjs` mechanically checks an issue body before it is filed: required sections in order, conventional-commit title grammar, minimum body size, spec anchor present, `file:line` anchors resolve against a checkout, test plan names real test paths or a `Verify:` line, absolute dates only, banned vague acceptance phrases, blocked-by discipline. Four genres: `feature`, `bug`, `bootstrap`, `decision`.

```
node ${CLAUDE_PLUGIN_ROOT}/scripts/lint-issue.mjs body.md --genre feature --repo /path/to/repo
```

The `bootstrap` genre covers issue zero of an empty repo, where there is no code to anchor into: all-`New:` integration points are legal (no `file:line` anchor required, at least one `New:` path mandatory), and the first acceptance criterion must be a `Shippable main:` bullet defining what shippable means for that repo before anything exists. See Genre 3 in `prompts/github-issue-template.md`.

Exit 0 when clean; exit 1 with a readable finding list otherwise. It requires only `node`, no dependencies. The schema is data (`scripts/schema.json`); point `--config` at a copy to adapt section names, title grammar, or banned phrases to your repo. The linter's own suite lives at `scripts/tests/run-tests.sh`; it must pass before any linter or schema change ships.

## Provenance and honesty notes

- Extracted from a five-month production project (2026) by analyzing session transcripts, git history, issue and PR history, and the project's goal-prompt corpus. The claims in the skills reflect observed practice in that project, not aspiration.
- The originating project did not use GitHub issues from day one; early work carried its specs in docs or PR bodies. The invariant was always "every unit of work has a written, self-contained spec"; these templates encode the mature form.
- The skills are distilled from observed practice but have not been pressure-tested on fresh agents per the superpowers:writing-skills TDD cycle. Test before treating them as bulletproof.
