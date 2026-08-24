# Goal Prompt - Cross-Session / Cross-Repo Handoff

Use this when work continues in a different session, repo, or machine where your memory and conversation will NOT be available. The test of a good handoff: an agent with **zero prior context** executes it without asking what you meant. Save under `.claude/prompts/<topic>-goal.md` and record the pointer in memory.

---

# Handoff - <one-line mission>

> Paste everything below the line. It is written for an agent with **no prior context**.
> Start the session in `<absolute repo path>` - that is where the work is, and its `CLAUDE.md` carries the operational hazards you need.
> Every fact below was verified on <YYYY-MM-DD>. The repo(s) move - re-read before depending on anything, and if a reference has moved say so rather than quietly using a stale one.

## The task

<What exists now, what is missing, and the precise deliverable. State the stakes plainly if they are high: "This is the arming step… treat it accordingly.">

## Read these first (in this order)

- `<repo>/CLAUDE.md` - operational hazards. Non-negotiable.
- <issues by number, with one clause each on what they decide: "#288 - the accepted risk; #289 - the blocker">
- <spec/plan docs by path>

## What already exists (do not rebuild)

| Artifact | What it provides |
|---|---|
| `<path>` | <capability, with counts: "31 tests", "vendored at <repo> <SHA>"> |

## The trap that killed the previous attempt

<The concrete failure mechanism, spelled out - not the moral. Why the green suite missed it. Then the falsifiable countermeasure:> **Write a test that fails against the broken version first.**

## Must stay true / Standing decisions (do not re-open)

- <invariant 1 - stated as behavior: "An empty allowlist means no execution, never all targets.">
- <owner decision + where it was recorded>

## Do NOT do

- <operator-only actions: "Do not deploy anything. Do not merge without asking.">
- <scope fence: adjacent work that is explicitly someone else's>

## Gates - run each separately, never chained

```
<test command>        # baseline before you start: <N passed, M skipped>
<lint command>
<typecheck command>
```

## How to work

TDD, and **mutation-verify every new test**: change the thing under test, confirm the test fails, restore. **Verify at the real surface, not only against fakes** - every significant defect in this work so far was invisible to a green suite.

## When it works

<Done as an OBSERVABLE check at the real boundary, not a tool's return value - e.g. "Have a job write `hostname` to a marker file, then look inside the container and on the host. A completed call proves nothing about containment.">
