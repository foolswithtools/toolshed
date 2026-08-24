# PR Body Template

The PR body is the permanent record (squash-merge folds it into `main`'s history). It argues the *why*, names *rejected alternatives*, and carries *verification evidence* - never just a change list.

Title = conventional commit that will become the squash subject: `type(scope): lowercase prose description (#issue)` - the merge appends `(#PR)`, producing the double-reference fingerprint `(#issue) (#PR)` on main.

---

```markdown
Closes #<NNN>.

## Summary / Why
<The problem restated with its observed trigger and date. For bugs, reproduce the
observed failure verbatim: "status=403 body={'error': …} → misleading downstream error.">

## Approach
<The design chosen and - mandatory - the alternatives REJECTED, with reasons:
"why NOT the obvious managed IAM policy (it would evade the existing test's regex)".
Cite the spec/plan doc and the decisions honored: "per the operator's decision on #279".
Narrate mid-PR discoveries honestly: "the release path was redesigned mid-PR after the
whole-branch review found the hub cannot perform a release.">

## Changes
<Grouped by layer - Module / Server / Client / Infra / Docs - not a raw file list.>

## Testing
<EVIDENCE, with numbers, from actually-run commands:
- unit: 2306/2306
- terraform test: 16 passed
- typecheck clean on both configs
- TDD red-first noted for new behavior; mutation-verified where claimed
- live/real-surface verification where the change touches a boundary>

## Process
<For multi-task branches: "N TDD tasks (plan: docs/plans/<file>), per-task reviews,
final whole-branch review: READY TO MERGE" - or what the review found and how it
was resolved.>

## Follow-ups filed
- #<NNN> - <deferred or discovered work>
```

---

**Gate:** do not merge without the human's explicit word, and not before CI is green. If a suite was already red on `main`, say so and let the human rule ("e2e was already red on main - ignore?").
