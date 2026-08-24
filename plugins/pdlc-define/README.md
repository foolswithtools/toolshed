# pdlc-define

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
| `prompts/00-derive-spec-goal-prompt.md` | Template: derive a decision-ready spec by observing an existing app (greenfield) |
| `prompts/01-research-goal-prompt.md` | Template: research phase producing a decision-ready spec |
| `prompts/02-issue-authoring-goal-prompt.md` | Template: split an accepted spec into GitHub issues (no code) |
| `prompts/03-implementation-kickoff-prompt.md` | Template: kick off execution of an issue in a fresh session |
| `prompts/04-handoff-goal-prompt.md` | Template: hand work to a zero-context successor session or repo |
| `prompts/github-issue-template.md` | The issue-body skeleton (feature-slice, bug, and bootstrap genres) |
| `prompts/pr-body-template.md` | The PR-body skeleton with evidence sections |
| `scripts/lint-issue.mjs` | Dependency-free issue-body linter (with `scripts/schema.json`) |
| `scripts/check-links.sh` | Repo-side check that no skill or agent references anything outside the plugin |
| `scripts/tests/` | The linter's self-test suite (`sh scripts/tests/run-tests.sh`) |
| `config/pattern-config.schema.json` | JSON Schema for the per-repo `.pattern-config.json` |
| `config/pattern-config.example.json` | A valid example config; `/pattern-init` copies it into repos with no config |
| `scripts/pattern-config.mjs` | Loader and validator for `.pattern-config.json` (module plus CLI) |
| `scripts/pattern-init.sh` | Idempotent scaffolder behind the `/pattern-init` command |
| `commands/pattern-init.md` | `/pattern-init <repo>`: scaffold the pattern structure in an approved repo |
| `commands/` | The seven lifecycle slash commands (table below) |

## Commands

The complete operator surface for the lifecycle, one command per step:

| Command | Job |
|---|---|
| `/research-spec` | Fill the research goal prompt into a fresh-session brief that produces a decision-ready spec |
| `/derive-spec` | Fill the derive-spec goal prompt for specifying a new app by observing an existing one |
| `/author-issues` | Fill the issue-authoring goal prompt that splits an accepted spec into self-contained GitHub issues |
| `/lint-issue` | Run the issue-body linter standalone against a draft body; the verdict is the linter's exit code |
| `/kickoff` | Produce a fresh-session kickoff prompt for one issue, constraints preamble first, stop condition built in |
| `/branch-review` | Run the fresh-context whole-branch review of a branch or PR before merge |
| `/closeout` | Walk the close-out checklist (follow-ups, docs, lessons) and fill a handoff prompt when work continues elsewhere |

The four prompt-filling commands (`/research-spec`, `/derive-spec`, `/author-issues`, `/kickoff`) output a completed goal prompt for the operator to review and paste into a fresh session; unfillable slots surface as `PROPOSED - confirm:` items, never silent guesses. The other three act directly. `/derive-spec` needs the `prompts/00-derive-spec-goal-prompt.md` template, which ships separately; the command reports plainly if the installed plugin version lacks it.

## Install

```
/plugin marketplace add https://github.com/foolswithtools/toolshed.git
/plugin install pdlc-define@toolshed
```

The skills load on demand; the agents register as subagents. Prompt templates resolve from `${CLAUDE_PLUGIN_ROOT}/prompts/`.

## The pattern in one paragraph

Work flows through a fixed lifecycle: a research goal prompt produces a decision-ready spec in the repo; open decisions are resolved with the owner and recorded; an issue-authoring goal prompt splits the spec into self-contained, PR-able GitHub issues before any code; each issue is executed in a fresh session under TDD with subagent slices; a fresh-context whole-branch review guards the merge; the human holds the merge gate; close-out extracts lessons, syncs docs, and, when work continues elsewhere, writes a handoff goal prompt for the next zero-context agent. Transcripts are disposable; the repo is the memory.

## Per-repo configuration: `.pattern-config.json`

The pattern's paths and names vary per repo (the source project kept specs in one directory, the templates default to another). A consumer repo declares its own conventions in a `.pattern-config.json` at the repo root; skills, commands, and the linter read it when present, fall back to the template defaults when absent, and say which source they used. Scaffold it with `/pattern-init <repo-root>` (idempotent; a second run is a no-op). The machine-readable contract is `config/pattern-config.schema.json`; a valid example is `config/pattern-config.example.json`.

| Field | Type | Required | Default | Read by |
|---|---|---|---|---|
| `version` | const `1` | yes | - | all consumers (anything else is rejected) |
| `spec_dir` | relative path | yes | `docs/specs` | research/authoring surfaces; linter (spec anchors must resolve under it) |
| `known_issues_dir` | relative path | no | `docs/known-issues` | close-out surfaces; `/pattern-init` |
| `roadmap_path` | relative path | no | `docs/ROADMAP.md` | close-out surfaces; `/pattern-init` |
| `partitions` | array of `{name, description?}` | no | `[]` | issue authoring; linter (a test plan must name a declared partition) |
| `gate_commands` | array of `{name, run}` | no | `[]` | kickoff and merge-gate surfaces; `/pattern-init` docs |
| `labels` | array of strings | no | `[]` | issue authoring (labels come from this list) |

Paths are repo-relative: no leading slash, no `..` segments. Unknown keys are rejected so typos fail loudly. Validate by hand with:

```
node ${CLAUDE_PLUGIN_ROOT}/scripts/pattern-config.mjs validate --repo /path/to/repo
node ${CLAUDE_PLUGIN_ROOT}/scripts/pattern-config.mjs show --repo /path/to/repo
```

`validate` exits 0 on a valid file (or no file, meaning defaults apply) and 1 with findings otherwise; `show` prints the effective config with a `source` field (`file` or `defaults`).

## The linter

`scripts/lint-issue.mjs` mechanically checks an issue body before it is filed: required sections in order, conventional-commit title grammar, minimum body size, spec anchor present, `file:line` anchors resolve against a checkout, test plan names real test paths or a `Verify:` line, absolute dates only, banned vague acceptance phrases, blocked-by discipline. Four genres: `feature`, `bug`, `bootstrap`, `decision`.

```
node ${CLAUDE_PLUGIN_ROOT}/scripts/lint-issue.mjs body.md --genre feature --repo /path/to/repo
```

The `bootstrap` genre covers issue zero of an empty repo, where there is no code to anchor into: all-`New:` integration points are legal (no `file:line` anchor required, at least one `New:` path mandatory), and the first acceptance criterion must be a `Shippable main:` bullet defining what shippable means for that repo before anything exists. See Genre 3 in `prompts/github-issue-template.md`.

Exit 0 when clean; exit 1 with a readable finding list otherwise. It requires only `node`, no dependencies. The schema is data (`scripts/schema.json`); point `--config` at a copy to adapt section names, title grammar, or banned phrases to your repo. The linter's own suite lives at `scripts/tests/run-tests.sh`; it must pass before any linter or schema change ships.

When the repo root carries a `.pattern-config.json` (or `--pattern-config` points at one), the linter also enforces it: spec anchors must live under the configured `spec_dir`, and when partitions are declared the test plan section must name one of them. An invalid config file is a usage error (exit 2), not an issue finding.

## Provenance and honesty notes

- Extracted from a five-month production project (2026) by analyzing session transcripts, git history, issue and PR history, and the project's goal-prompt corpus. The claims in the skills reflect observed practice in that project, not aspiration.
- The originating project did not use GitHub issues from day one; early work carried its specs in docs or PR bodies. The invariant was always "every unit of work has a written, self-contained spec"; these templates encode the mature form.
- The skills are distilled from observed practice but have not been pressure-tested on fresh agents per the superpowers:writing-skills TDD cycle. Test before treating them as bulletproof.
