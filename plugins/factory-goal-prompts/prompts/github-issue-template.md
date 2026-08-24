# GitHub Issue Body Template

Two genres share one backbone. The bar for both: **a cold implementer who has read nothing but this body (and what it links) can deliver the slice.** Zero one-liner issues - if the body is under ~500 characters, it isn't an issue yet.

Titles use conventional-commit style: `feat(scope): …` / `fix(scope): …` / `infra(scope): …` - concrete deliverable or symptom, lowercase prose.

---

## Genre 1 - Feature slice (part of a program)

```markdown
Part of <program> - spec: `<spec-dir>/<date>-<name>.md` (§refs; use the repo's actual spec directory). Tracker: #<NNN>.
<If security-sensitive (the flag may live here or on the tracker entry; either counts):> **⚠ whole-branch review required before merge.**

## Why this slice
<Why this exists now and what later phases consume from it. One paragraph.>

## Scope
- <Deliverable 1, concretely - new files by path, behavior by contract>
- <Exported API given VERBATIM: `scanL1(text) → {findings[], redacted}` - pure, no I/O>

## Integration points
- New: `<src/path/new-file.ts>` (+ scripts, data files)
- Existing prior art to fold in: `<src/path/file.ts:NN>` `<functionName>` - <and what NOT
  to touch yet: "do NOT rewire callers - that's the #<NNN> issue">

## Test plan (write these first)
- `tests/<path>.test.ts` - <positive/negative cases, the drift/regression guards>
- Partition/suite: <which coverage partition owns this, thresholds that apply>
- <Repo-specific gotcha, e.g. "run `npm run typecheck` before pushing - tests/ is
  typechecked in CI only">

## Acceptance criteria
- <Falsifiable, observable statements: "CI fails if the committed catalog drifts from
  the snapshot", never "works correctly">

## Out of scope
- <Named deferred work, WITH the issue number it is deferred to>

## Blocked by
- #<NNN> <one clause on why>; cross-repo: <org/repo#NN>

## Docs (definition of done)
- <exact docs files: current-features entry, roadmap status marker, api-reference>
```

## Genre 2 - Bug

```markdown
## Problem
<Observed symptom with an ABSOLUTE date and real identifiers:
"Observed 2026-07-03: i-05141904fb1b7e775 was `terminated` in AWS but still listed…">
<Provenance - HOW found: "surfaced by the whole-branch review of <branch>",
"found during <activity>">

## Root cause / Detail
<The MECHANISM, not just the symptom. Trace the paths with exact anchors:>
- Path A: `<route>` → `<src/file.ts>` `<fn>` - **enforced**
- Path B: `<route>` → `<src/other.ts>` - **no check anywhere on this path**
<Verbatim code/log excerpts where load-bearing. Note misleading comments/docs to fix.>

## Impact
<Who/what breaks and which boundary it defeats. Downgrade honestly where true:
"not a credential leak, but it defeats the policy boundary X exists to provide."
"cosmetic but confusing.">

## Fix options
1. **<Simplest>:** <one gate covering all paths, by file>
2. **<Deeper / defense-in-depth>:** <…>
Recommend (1) now, (2) as follow-up. <Also name collateral fixes: "fix the misleading comment.">

## Test plan (write these first)
<A test that FAILS on the buggy behavior; regression test named and linked to the
resolved-issues doc entry.>

## Out of scope / Related
<…>
```

---

**Lifecycle conventions**
- Amend in place with **dated addenda** ("added 2026-07-18 - read before snapshotting"); strike through resolved open questions with bold resolutions ("~~scope guard~~ **Resolved: filed as #179**").
- Comments are a **disposition log**, not discussion: "Option 3 shipped in #114 (merged 4017c1d)"; "Decision: accepted for now - <risk> stands"; a closing rationale.
- Deferred work is split OUT into its own issue ("Deferred follow-up split out of #104 … Status: DEFERRED"), never left as a silent checkbox.
