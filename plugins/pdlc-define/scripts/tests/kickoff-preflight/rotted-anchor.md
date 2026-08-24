Title: feat(sample-fixture): add widget summary endpoint
Part of the sample program - spec: `docs/specs/2026-08-24-sample.md` (section 2).

## Why this slice
The widget summary endpoint is the seam every later slice consumes: the detail
view and the search wiring both read from it. Shipping it first, behind the
existing router registration pattern, means later slices land without touching
the route table again. This fixture body exists only to exercise the kickoff
preflight's anchor-freshness check against a fresh, unmoved anchor.

## Scope
- New endpoint `GET /api/widgets/summary` returning `{ widgets: WidgetSummary[] }`.
- Exported API given verbatim: `listWidgetSummaries(tenantId) -> Promise<WidgetSummary[]>`.
- Stage filter values validated against the stage table, unknown values rejected.

## Integration points
- New: `src/newthing.ts` (handler plus data access)
- Existing prior art to fold in: `src/example.ts:70` `exampleHandler`, mirror its
  envelope and error mapping. Do NOT rewire the detail view yet.

## Test plan (write these first)
- `tests/widgets/summary.test.ts`: returns seeded widgets for the tenant; rejects
  an unknown stage value with 400; never returns another tenant's rows.
- Partition: core-coverage. Run the typecheck before pushing.

## Acceptance criteria
- A request with a valid stage filter returns only widgets in that stage.
- A request with an unknown stage value fails with 400 and a named error code.
- CI fails if the response envelope drifts from the recorded snapshot.

## Out of scope
- Detail view wiring; search integration.

## Blocked by
- None.

## Docs (definition of done)
- `docs/features/current-features.md` entry; roadmap status marker updated.
