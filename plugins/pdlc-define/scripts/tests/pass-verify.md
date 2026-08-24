Title: docs(sample): document the widget import flow end to end

Part of the sample program, spec: `docs/specs/2026-08-24-sample.md` (section 3).

## Why this slice
The widget import flow has no written walkthrough, so every new operator relearns
it from scratch by reading code. A single documented pass, verified against a real
import on 2026-08-24, removes that repeated cost and gives the review process a
stable reference to diff against when the flow changes.

## Scope
- One walkthrough document covering trigger, transform, and landing steps.
- Planned: `ops-handbook/widget-import.md` (lives in the handbook repo, created
  when this lands there; informational anchor for the implementer).

## Integration points
- Planned: `ops-handbook/widget-import.md` (target home for the document).

## Test plan (write these first)
- Verify: a fresh operator follows the document against the sample dataset and
  completes an import with zero questions; the run is recorded in the PR.

## Acceptance criteria
- The document names every step with its owning module and the observable output
  of each step on the sample dataset.

## Out of scope
- Changing the import flow itself.

## Blocked by
- [010].

## Docs (definition of done)
- The walkthrough document itself is the deliverable.
