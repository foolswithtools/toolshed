---
name: context-layering
description: Use when finishing a unit of work, recording a decision or lesson, resolving a bug, or deciding where any piece of project context should live - issue, repo doc, or agent memory. Also use when picking up a project thread from a previous session.
---

# Context Layering & the Lesson Loop

## Overview

Context has three homes with strict division of labor. The router question: **who needs this, from where, and does the repo's history already record it?** Anything a fresh session elsewhere will need must be **promoted** upward into the repo or a goal prompt - memory is the least durable layer.

## The three layers

| Layer | Holds | Examples |
|---|---|---|
| **GitHub issues/PRs** | Units of work, accepted risks, owner decisions, dependency DAGs, disposition comments | "Decision: accepted for now - client-side containment stands"; "Option 3 shipped in #114 (merged 4017c1d)" |
| **Repo docs** | Durable multi-consumer truth: dated specs/plans, roadmap with status markers, resolved-bugs log, numbered lessons, doc→code index | `docs/specs/2026-07-17-sdp-controls-evaluation.md`; lessons-learned.md #46 |
| **Agent memory** | Cross-session execution state (issue→PR→SHA→date), live/destroyed infra + cost, machine-specific facts, process lessons, a singular NEXT-STEP pointer | "DESTROYED - ZERO instances running, $0; recreate: terraform apply in ubuntu-obs" |

Shared rule: context serving multiple issues goes in the repo, **not pasted into every body**.

## Memory conventions

- **Append, don't rewrite**: dated sections per shipped unit; superseded sections marked, kept for rationale. Wrong claims get a bold **CORRECTION** section - never silent deletion.
- **Fields per unit**: issue #(s) → PR # → merge SHA → date → test counts → CI status → what the whole-branch review caught → accepted gaps → follow-ups filed. Infra adds cost + destruction proof + exact recreate command.
- **Status vocabulary** (bold caps): SHIPPED, MERGED, BLOCKED on \<exact dependency\>, DEFERRED, ACCEPTED, DESTROYED, INERT (merged but unwired), FIXED, CORRECTION.
- **Index hooks are resumable**: the one-line index entry alone should let a session resume the thread (PRs, SHAs, "next:").
- **Handoff across memory boundaries**: if the next step runs where this memory won't load, promote state into a goal-prompt file and record the pointer: "Handoff prompt: `<path>`. Start that session in `<dir>` (this memory will NOT load there)."
- Decisions (`*_decisions`), execution state (`*_state`), and research (`*_research`) are separate files; research converts to state when executed.

## The lesson loop (bugs)

```
bug fixed → resolved.md entry (date / symptom / root cause / fix / affected files)
         → NAMED regression test pinning the fix (linked from the entry)
         → if it generalizes: numbered lesson - MECHANISM, not moral:
           what failed, WHY green signals missed it, the actionable generalization
         → future commits and issues cite the lesson by number
```

Example of the register: *"A sanitize gate only guards what it scans for - and per-chunk scanning misses payloads that span chunks."* Lessons about **how to work** (process, tooling, CI quirks) go to memory as `feedback_*` files with mandatory **Why:** and **How to apply:** sections.

## Common mistakes

- Recording a decision only in conversation - it must land in the spec/issue the next reader will open.
- Pasting the same design context into five issue bodies instead of one repo doc + links.
- Deleting a wrong memory claim instead of CORRECTING it (the correction teaches; the deletion hides).
- A lesson phrased as a moral ("be careful with gates") instead of a mechanism ("per-chunk scanning is not chunking-invariant").
- Letting memory hold the only copy of something a different machine/repo session will need.
