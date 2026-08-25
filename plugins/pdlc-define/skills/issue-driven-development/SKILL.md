---
name: issue-driven-development
description: Use when starting any unit of project work - a feature, bug fix, or infrastructure change - or when tempted to start coding from a verbal request, a chat message, or an undocumented idea.
---

# Issue-Driven Development

## Overview

**No unit of work without a written, self-contained spec - and the spec's home is a GitHub issue.** A fresh agent with zero context must be able to deliver the work from the issue body alone. Session transcripts are disposable; the repo (issues, specs, docs) is the memory.

## Per-repo configuration

Before resolving any repo convention (spec directory, known-issues home, roadmap path, coverage partitions, gate commands, issue labels), check the repo root for `.pattern-config.json`. When present it is authoritative; when absent use the template defaults (`docs/specs/`, `docs/known-issues/`, `docs/ROADMAP.md`). Either way, state which source you used, e.g. "using .pattern-config.json" or "no .pattern-config.json; template defaults". Schema and example: `${CLAUDE_PLUGIN_ROOT}/config/`. Scaffold a repo with the `/pattern-init` command; the linter reads the same file.

## The lifecycle

1. **Research** (if the design is open): goal prompt → decision-ready spec in the repo's spec directory (dated, e.g. `docs/specs/<date>-<topic>.md`; use whatever spec home the repo already has, never hard-code one) with comparison matrix, `file:line` integration points, phased plan, and explicit open questions. Template: `${CLAUDE_PLUGIN_ROOT}/prompts/01-research-goal-prompt.md`.
2. **Decide**: batch open questions to the owner with recommended defaults; record answers INTO the spec as dated decisions. Unanswered → `blocked: decision`. Never silently pick for the owner.
3. **Author issues - before any code**: split into PR-able slices per `${CLAUDE_PLUGIN_ROOT}/prompts/02-issue-authoring-goal-prompt.md` and the skeleton in `${CLAUDE_PLUGIN_ROOT}/prompts/github-issue-template.md`. Unit of work = 0.5-3 days, independently green, `main` stays shippable. Every body: why-this-slice, verified `file:line` anchors, "Test plan (write these first)", observable acceptance criteria, out-of-scope, `Blocked by #N`. Program-sized work also gets a tracker issue holding the phase DAG. Two fully worked, synthetic examples (both lint clean): `${CLAUDE_PLUGIN_ROOT}/skills/issue-driven-development/examples/`.
4. **Kick off in a fresh session**: `complete github issue <N> in a TDD manner, do not merge the produced PR until CI is green`. If a one-liner feels insufficient, the issue is under-specified - fix the issue.
5. **Execute**: brainstorm → plan → parallel TDD subagent slices, each with a fixed wire contract and allowed-files list; slice reports paste observed RED output. Subagents don't commit.
6. **Review**: per-task reviews, then a REQUIRED whole-branch review by a fresh-context agent. **REQUIRED SUB-SKILL:** whole-branch-review.
7. **Merge gate**: PR per `${CLAUDE_PLUGIN_ROOT}/prompts/pr-body-template.md`; CI green; the human says "merge". Squash-merge; branch `type/kebab-slug`; subject `type(scope): prose (#issue)`.
8. **Close out** - none of these are optional:
   - File follow-up issues for everything deferred or discovered.
   - Docs hygiene per CLAUDE.md (features doc, api-reference, roadmap marker; bugs → resolved-issues entry + named regression test).
   - Extract lessons and update cross-session state. **REQUIRED SUB-SKILL:** context-layering.
   - Work continuing elsewhere → write a handoff goal prompt (`${CLAUDE_PLUGIN_ROOT}/prompts/04-handoff-goal-prompt.md`).

## Invariants (apply at every step)

- **Date everything; re-verify everything.** Every `file:line` claim carries a verification date; stale references are reported, never silently reused.
- **Evidence before assertions.** Paste real command output - test counts, RED output, plan results. Record the numeric baseline before starting.
- **Verify at the real surface**, not only against fakes; done = an observable check at the real boundary.
- **Negative space is explicit**: what already exists (don't rebuild), what NOT to do, decisions not to re-open.
- **Failure honesty**: process lapses get their own issues ("…decided to file it as a follow-up - and then did not. Filing it now, late.").

## Rationalization table

| Excuse | Reality |
|---|---|
| "It's a small fix, no issue needed" | Small fixes get small issues (the source project's minimum body: 541 chars). The issue is where the regression test and root cause live. |
| "The context is in our conversation" | The conversation will be purged. Assume the implementer has NOT read it. |
| "I'll write the issue after shipping" | Then the issue can't contain the write-first test plan, and the slice boundary was never checked against 'main stays shippable'. |
| "Casual question, casual answer" | Correct - ops Q&A does NOT need this machinery. Reserve it for units of work. |

## Red flags - STOP

- Writing implementation code while the issue authoring phase is incomplete.
- A kickoff prompt that restates context the issue should carry.
- Merging on your own judgment, or before CI is green.
- Ending a session without the close-out checklist.
