# Goal Prompt - Issue Authoring Phase

Use this after a spec is accepted and its open questions are resolved. The deliverable is **the GitHub issues themselves** (via `gh`), the cross-linking structure, and repo-side context updates - **no implementation code**. This prompt is the methodology's core: it makes every downstream kickoff a one-liner.

---

Split the accepted <program name> architecture into GitHub issues that maximize delivery success under this repo's TDD discipline. Produce the issues themselves (via `gh`), the cross-linking/milestone structure, and the repo-side context updates - do NOT implement any feature code.

## Source of truth (read first, in this order)

1. `CLAUDE.md` - constraints.
2. The accepted spec: a dated file in the repo's spec directory (e.g. `docs/specs/<YYYY-MM-DD>-<topic>.md`; the spec directory varies per repo). All `file:line` integration points are in <§refs> - carry them into issues verbatim, but **re-verify against current `main` before citing**; the repo moves fast.
3. <any amendments decided AFTER the spec was written - name them explicitly: "the report does NOT yet reflect it; your first task is to fold it in">

## Task 0 - before any issues

1. Fold post-spec amendments into the spec (dated amendment note, amend in place).
2. Resolve the spec's remaining open questions with the owner via batched questions - recommend defaults. Record the answers in the spec as decisions. Any left unanswered → the affected issue gets a `blocked: decision` label; never silently pick for the owner.

## Issue-splitting rules

- **Unit of work = one PR-able slice: 0.5–3 days, independently green.** Every issue must leave `main` shippable. If a phase can't be split without a dead-code intermediate state, prefer a slice that ships the seam + a fake implementation first.
- **TDD is the structure of the issue, not a checkbox.** Each issue body must contain a "Test plan (write these first)" section naming the exact test files and the coverage partition/suite that owns them.
- **Every issue carries its own context.** Assume the implementer has NOT read this conversation: why-this-slice, verified `file:line` anchors, verbatim interfaces for anything new, acceptance criteria as observable behavior, explicit out-of-scope. Use the skeleton in `${CLAUDE_PLUGIN_ROOT}/prompts/github-issue-template.md`.
- **Context that serves multiple issues belongs in the repo** (docs/, CLAUDE.md), not pasted into every body - add those repo files as part of this task and link them.
- **Dependency structure is explicit:** `Blocked by #N` edges (cross-repo refs where needed), plus one tracker meta-issue holding the phase DAG - checkboxes, `←` dependency arrows, parallelism notes, the critical path.
- **Security-sensitive slices get a review note:** "⚠ whole-branch review required before merge" (in the issue body or on the tracker entry; either placement counts) - this repo's record shows per-task reviews miss cross-task wiring; the whole-branch review is the safety net.
- Titles use conventional-commit style: `feat(<scope>): …`, `fix(<scope>): …`, `infra(<scope>): …`.

## Deliverables

- The issues, labeled <label(s)>, cross-linked, with the tracker issue pinned.
- Repo-side context updates (shared docs, roadmap entries marked PLANNED).

## Verify before finishing

`gh issue list --label <label>` shows every issue; each body renders with working links; **no issue lacks a test plan or acceptance criteria**; the tracker's DAG covers every issue exactly once.
