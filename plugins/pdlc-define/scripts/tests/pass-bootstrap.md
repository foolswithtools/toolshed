Title: infra(bootstrap): scaffold the app repo to a green stub build
Part of the sample program - spec: `docs/specs/2026-08-24-sample.md` (section 1).

## Why this slice
Nothing exists yet. Every later slice needs a repo that builds, launches to a stub
screen, and runs a green suite, so shippable-main has a defined meaning from the
first merge. This slice creates that floor and nothing else, so the follow-on issues
can each stay independently green.

## Scope
- Project scaffold that compiles and launches to a placeholder screen.
- Test harness wired with one passing smoke test so the suite is runnable in CI.
- Repo hygiene files: contributor doc, docs skeleton, config for the pipeline.

## Integration points
- New: `App/AppMain.swift` (entry point, placeholder screen)
- New: `Tests/SmokeTests.swift` (one passing launch test)
- New: `Config/pipeline.yml` (CI pipeline config for the build and test jobs)

## Test plan (write these first)
- `Tests/SmokeTests.swift`: the app target builds and the placeholder view is
  constructed without throwing. This is the suite's first green test.

## Acceptance criteria
- Shippable main: a clean checkout builds, the app launches to the placeholder
  screen, and the suite passes with its one test, captured in CI output.
- Launching the app shows the placeholder screen, verified by the smoke test.

## Out of scope
- Any real screen, data model, or networking; those are the numbered slices after
  this one.

## Blocked by
- none

## Docs (definition of done)
- Readme quick-start section: how to build and run the suite.
