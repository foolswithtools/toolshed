---
name: whole-branch-review
description: Use when a multi-task branch is about to be declared ready to merge, when per-task reviews have all passed, or when a change touches security-sensitive surfaces, deploy wiring, or code produced by multiple subagents.
---

# Whole-Branch Review

## Overview

**Per-task reviews structurally miss cross-task wiring.** After all slices pass their own reviews and tests are green, a **fresh-context agent** reviews the ENTIRE branch diff as one unit before merge. In the source project this pass caught every merge-blocker that per-task reviews and green suites missed: a feature "unwired in every topology", a deploy-wiring no-op, a chat feature dead-on-arrival against real servers, a verdict-corruption bug, a SwiftUI observation bug an opus per-task review approved.

## Why green tests aren't enough

Each slice is tested against its own contract, usually with fakes at the seams. Nothing checks that the seams were actually connected: a module built and tested but never constructed at the composition root passes everything and does nothing. *"Every significant defect in this work was invisible to a green suite."*

## How to run it

1. **Fresh context is the point.** The reviewer must NOT be the session that wrote the code - dispatch a subagent (or new session) that reads only the branch diff, the issue(s), and the repo. See the `branch-reviewer` agent shipped with this plugin (`${CLAUDE_PLUGIN_ROOT}/agents/branch-reviewer.md`).
2. Scope = the whole branch diff against `main` (`git diff main...HEAD`), not per-commit.
3. Hunt list, in priority order:
   - **Wiring**: is every new module reachable from a real entry point in EVERY topology/build target? Grep for construction sites, not just definitions.
   - **Deploy wiring**: do units/manifests/env plumbing actually pass the new knobs the code reads?
   - **Cross-task contract drift**: did slice B implement the interface slice A actually exports, or the one in the plan?
   - **Second doors**: for any gate/policy added, enumerate every other path to the protected resource.
   - **Dead-on-arrival paths**: what happens against the real server/DB, not the fake?
4. Verdict is explicit: **READY TO MERGE** or a numbered blocker list. Blockers get fixed on the branch and the review re-run.
5. The PR body's Process section records the outcome - including honest narration when the review forced a redesign.

## When it is mandatory

- Any branch built from multiple subagent tasks.
- Security-sensitive surfaces (auth, IAM, policy gates) - flag these at issue-authoring time: "⚠ whole-branch review required before merge". The flag may live in the issue body or on the tracker entry; either placement counts.
- Any change to deploy/provisioning wiring.

## Rationalization table

| Excuse | Reality |
|---|---|
| "Every task was already reviewed" | Per-task reviews cannot see cross-task wiring - that's structural, not a diligence failure. |
| "All tests are green" | Green suites missed every one of the historical merge-blockers. Tests validate slices; the review validates the assembly. |
| "The branch is small" | Small branches with two tasks still have one seam. Review the seam. |
| "I'll review it myself" | The author's context is the contamination. Fresh eyes or it doesn't count. |

## Real-world impact

Review escapes become issues naming which review layer missed them and why - and repeated findings become issue-template rules. The loop is what keeps this pass load-bearing.
