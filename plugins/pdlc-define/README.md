# pdlc-define

Goal-prompt driven development: every unit of work gets a written, self-contained spec that a fresh agent with zero context can execute. The discipline works on any project, but it is built for factory projects (the pattern plus the factory pipeline). Extracted from a five-month production project (2026): hundreds of merged PRs, none abandoned, every one driven by a written spec.

Two harnesses, one shared core: the skills, prompt templates, and linter under this directory are the only copy. The Claude Code plugin (`.claude-plugin/plugin.json`, `agents/`, `commands/`) and the pi package (`package.json`'s `pi` key) both point at the same `skills/` and `prompts/` directories; neither harness gets a duplicated copy.

## What it ships

| Path | What it is |
|---|---|
| `skills/issue-driven-development/` | The full lifecycle as an executable process: research, decide, author issues, kick off, execute, review, merge, close out |
| `skills/issue-driven-development/examples/` | Two fully worked, synthetic example issues (invented codebase, fictional product) showing the Genre 1 anatomy end to end; both lint clean |
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
| `scripts/kickoff-preflight.mjs` | `/kickoff`'s mandatory preflight: runs the linter, then re-verifies every `Existing:` anchor's named symbol against current `main` |
| `scripts/check-links.sh` | Repo-side check that no skill or agent references anything outside the plugin |
| `scripts/check-public-hygiene.sh` | Deny-list sweep proving no file under the plugin tree contains a banned string; the deny list is supplied at run time from outside this repo, never committed |
| `scripts/check-no-pi-duplication.sh` | Proves the pi manifest points at the shared `skills/` and `prompts/` directories and that no file elsewhere in the tree duplicates their content |
| `package.json` | The pi package manifest: `pi.skills` and `pi.prompts` reference `./skills` and `./prompts` directly, no copy |
| `scripts/tests/` | The linter's self-test suite (`sh scripts/tests/run-tests.sh`), the preflight's (`sh scripts/tests/run-kickoff-preflight-tests.sh`), and the pi package smoke test (`sh scripts/tests/run-pi-smoke-tests.sh`) |
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
| `/kickoff` | Run the mandatory preflight (linter plus anchor-freshness check), then produce a fresh-session kickoff prompt for one issue, constraints preamble first, stop condition built in. A failed preflight refuses to start: no prompt, no worker |
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

The `bootstrap` genre covers issue zero of an empty repo, where there is no code to anchor into: all-`New:` integration points are legal (no `file:line` anchor required, at least one `New:` path mandatory), and the first acceptance criterion must be a `Shippable main:` bullet defining what shippable means for that repo before anything exists. See Genre 3 in `prompts/github-issue-template.md`. A bootstrap (or any genre's) spec anchor still has to resolve to a real file under `--repo`/`--plan-root`; write the spec before linting the issue, not after.

A body may also declare its own genre with a `Genre: <name>` line before the first section heading; this wins over `--genre` when both are given, so a draft body is self-describing without the caller having to know which genre it is.

Exit 0 when clean; exit 1 with a readable finding list otherwise. It requires only `node`, no dependencies. The schema is data (`scripts/schema.json`); point `--config` at a copy to adapt section names, title grammar, or banned phrases to your repo. The linter's own suite lives at `scripts/tests/run-tests.sh`; it must pass before any linter or schema change ships.

When the repo root carries a `.pattern-config.json` (or `--pattern-config` points at one), the linter also enforces it: spec anchors must live under the configured `spec_dir`, and when partitions are declared the test plan section must name one of them. An invalid config file is a usage error (exit 2), not an issue finding.

## Kickoff preflight

Staleness accrues between issue authoring and execution: `file:line` anchors rot as `main` moves, and an under-specified issue burns a full worker session before anyone notices. `/kickoff` runs a preflight before it produces a kickoff prompt at all, host-side (anchors are unreachable from inside agent containers, so the check has to run where the checkout lives).

The preflight is `scripts/kickoff-preflight.mjs`, invoked over the fetched issue body:

```
node ${CLAUDE_PLUGIN_ROOT}/scripts/kickoff-preflight.mjs body.md --genre feature --repo /path/to/repo
```

It runs in two layers:

1. It invokes `scripts/lint-issue.mjs` unmodified as a subprocess (the mechanical linter, not reimplemented) and folds its findings in verbatim: missing sections, bad title grammar, an `Existing:` anchor whose file is gone, a line number past end of file.
2. It adds a check the linter does not do. When an `Existing:` anchor names its symbol in a second backtick span, the plugin's own convention (see `prompts/github-issue-template.md`, "Existing prior art to fold in: `` `<path:line>` `<functionName>` ``"), the preflight greps the anchor's target file for that symbol within 20 lines either side of the anchor line. A line count still in range does not mean the code at that line is still what the issue describes; a line-length check alone cannot see a symbol that moved elsewhere in the same file. A miss here is reported as `ANCHOR_SYMBOL_DRIFT`.

Exit 0 prints `PREFLIGHT PASS` plus, for every anchor it could re-verify, a freshness line (the symbol confirmed present, and the anchor file's last-touched date from `git log` when the checkout is a git repo). Exit nonzero prints `PREFLIGHT REFUSED` and the combined finding list; `/kickoff` refuses to start on a failed preflight, posts the finding list as a GitHub issue comment when the issue is on GitHub (prints it for local issue files), and never produces a kickoff prompt. A refused kickoff starts no worker; the fix is to fix the issue body, not the prompt.

The preflight's own self-test suite lives at `scripts/tests/run-kickoff-preflight-tests.sh` (fixtures under `scripts/tests/kickoff-preflight/`), proving three outcomes: a clean body passes with anchor freshness reported, a body with a rotted anchor is refused by the symbol-freshness check, and a body missing a required section is refused by the wrapped linter.

## Public-hygiene sweep

toolshed is a public repo. `scripts/check-public-hygiene.sh` proves that no
file under this plugin's tree contains a banned string (a private project
name, a client or company reference, a private repo slug, anything
owner-identifying beyond the public author block). The deny list itself is
never committed here: the script takes it as an external file, so the
banned names are not part of this repo's history either.

```
PDLC_DEFINE_HYGIENE_DENYLIST=/path/to/denylist.env \
  bash scripts/check-public-hygiene.sh
```

Exit 0 on zero hits; exit 1 with a `FINDING:` list otherwise; exit 2 on a
usage error (no deny list supplied, or the file is missing).

## pi package

pi is the pattern's second harness: the factory's default backend, and the client team's daily driver, so the same skills, prompt templates, and linter install with one pi command. `package.json` carries the pi manifest (the `pi` key), pointing at the shared `skills/` and `prompts/` directories this plugin already ships; nothing is copied for pi.

```json
{
  "pi": {
    "skills": ["./skills"],
    "prompts": ["./prompts"]
  }
}
```

Install (verified against pi 0.84.2):

```
pi install /path/to/toolshed/plugins/pdlc-define
```

This is the narrowest form pi 0.84.2 supports for a plugin nested inside a larger repo. pi's `git:` source has no subpath syntax: `git:github.com/foolswithtools/toolshed/plugins/pdlc-define` parses as a (nonexistent) repository path, not a package root inside a repository. So `pi install git:github.com/foolswithtools/toolshed` installs the whole toolshed checkout and finds zero skills or prompts there (this plugin's resources are nested, and toolshed's repo root carries no pi manifest of its own by design: it hosts several unrelated plugins). Clone first, then install the subdirectory as a local path, as above.

Add `-l` to install project-locally instead of to user settings; see pi's [`docs/packages.md`](https://pi.dev) for scope and update semantics.

The linter is not a pi resource type (skills/prompts/extensions/themes); pi does not need to know about it. Run it from the installed package path directly:

```
node /path/to/toolshed/plugins/pdlc-define/scripts/lint-issue.mjs body.md --genre feature --repo /path/to/repo
```

`scripts/tests/run-pi-smoke-tests.sh` is the smoke test: it installs the package into an isolated, throwaway pi settings scope (never `~/.pi/agent`), confirms pi's own resolver discovers all skills and prompt templates, runs the linter against a fixture body, and runs `check-no-pi-duplication.sh`. It makes no model call and needs no provider key; it skips (exit 0) if `pi` is not on `PATH`.

## The pdlc family

`pdlc-define` is the first plugin in a planned `pdlc-*` family, one plugin
per phase of the product development lifecycle. Coverage today, and the
names reserved for the phases not yet built:

| # | Phase | Status |
|---|---|---|
| 1 | Discover | Reserved: `pdlc-discover` |
| 2 | Define | Covered by `pdlc-define`: goal prompts through a decision-ready spec |
| 3 | Design | Reserved: `pdlc-design` |
| 4 | Plan | Covered by `pdlc-define`: spec to self-contained issues, plus the linter |
| 5 | Build | Reserved: `pdlc-build` |
| 6 | Verify | Covered by `pdlc-define`: TDD discipline in the issue body, whole-branch review |
| 7 | Release | Reserved: `pdlc-release` |
| 8 | Operate | Reserved: `pdlc-operate` |
| 9 | Feedback | Reserved: `pdlc-feedback` |

Reserved names mark a spot for a future plugin; none of them ship code
today, and none of the above is a timeline commitment.

## Provenance and honesty notes

- Extracted from a five-month production project (2026) by analyzing session transcripts, git history, issue and PR history, and the project's goal-prompt corpus. The claims in the skills reflect observed practice in that project, not aspiration.
- The originating project did not use GitHub issues from day one; early work carried its specs in docs or PR bodies. The invariant was always "every unit of work has a written, self-contained spec"; these templates encode the mature form.
- The skills are distilled from observed practice. Cold-start tested 2026-08-26: a fresh session with only this plugin installed (no other project context) ran `/pattern-init` on an empty repo, authored a bootstrap-genre issue from the shipped templates alone, passed the shipped linter and the `/kickoff` preflight on the first try with zero human edits to the issue body, and executed the issue in a TDD loop (RED observed, GREEN observed, mutation-verified) to a green, committed test suite with no mid-run coaching (toolshed#19). Accepted limitations that run surfaced, not yet folded into the plugin:
  - `/pattern-init` seeds `.pattern-config.json` with npm-shaped `gate_commands` before any deliverable or stack is chosen; a repo whose first deliverable isn't Node.js has to notice and edit the config itself.
  - `/author-issues` is built to hand a goal-prompt to a *separate* fresh session ("it writes no implementation code"); a single session that both authors and executes an issue has to bypass the command and apply `prompts/github-issue-template.md` directly instead.
  - There is no documented home for an issue body in a repo with no GitHub remote; `docs/known-issues/` is scoped to bug write-ups with regression tests, not general issue bodies.
  - `/kickoff` Register A's one-liner and stop condition assume a GitHub issue number and a CI-gated PR, with no documented fallback stop condition for local, remote-less work.
