---
name: writing-goal-prompts
description: Use when handing work to a fresh session, another repo, another machine, or a future agent with no access to the current conversation - or when asked to "write a handoff", "write a kickoff prompt", or "capture this so we can continue later".
---

# Writing Goal Prompts

## Overview

A goal prompt is a written brief that a **zero-context agent** can execute without asking what you meant. Three sub-genres share one skeleton: **build** (implement something), **evaluate** (research → decision-ready report), **decompose** (spec → GitHub issues). Filled templates: `01` through `04` under `${CLAUDE_PLUGIN_ROOT}/prompts/`, shipped with this plugin.

## The skeleton (all genres)

1. **Mission line** - one imperative sentence stating what to produce AND what not to do ("produce the issues themselves… do NOT implement any feature code").
2. **Handoff preamble** (cross-session): where to start the session and why; freshness disclaimer: "Every fact below was verified on \<date\>. The repo moves - re-read before depending on anything; if a reference has moved, say so rather than quietly using a stale one."
3. **Read these first, in order** - CLAUDE.md, the spec, the deciding issues (one clause each on what they decide), amendments decided after the spec ("the report does NOT yet reflect it; your first task is to fold it in").
4. **What already exists (do not rebuild)** - a table of artifact → what it provides, with counts and pinned SHAs.
5. **The trap** - the failure mechanism that killed the previous attempt, why green signals missed it, and the test that must be written to catch it.
6. **Must stay true / Standing decisions (do not re-open)** - invariants stated as behavior, so the agent doesn't re-litigate.
7. **Do NOT do** - the scope fence, especially operator-only actions ("Do not deploy. Do not merge without asking.").
8. **Gates** - exact verify commands, run separately, with the numeric baseline recorded ("1852 passed, 12 skipped").
9. **How to work** - TDD; mutation-verify new tests; verify at the real surface, not only against fakes.
10. **When it works** - done as an OBSERVABLE check at the real boundary, with the epistemology stated ("the decisive check is not 'the tool returns output' - it is WHERE the command ran").

## Quick reference

| Rule | Form |
|---|---|
| References | Concrete and pinned: `file.ts:NNN`, SHAs, issue #s - plus the re-verify instruction |
| Dates | Absolute only ("2026-08-07"), never "yesterday" |
| Failure history | Transferred with mechanism, not moral - often the longest section |
| Decomposition prompts | Apply the skeleton recursively: every issue produced must itself be zero-context-executable |
| Shared context | Push into repo files and link; never paste into every body |
| Storage | `.claude/prompts/<topic>-goal.md` or `docs/context/<date>-<x>-KICKOFF-PROMPT.md`; record the pointer in memory |

## Common mistakes

- **Success-only handoffs.** Omitting why the last attempt failed guarantees the successor repeats it.
- **Aspirational references.** Citing `file:line` without re-verifying, or without telling the reader to.
- **Missing negative space.** No "do not rebuild" inventory → duplicated work; no "Do NOT do" fence → scope creep into operator-only actions.
- **Done = tool returned output.** Define done as an observation at the real boundary.
