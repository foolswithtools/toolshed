Title: feat(widgets): add widget listing endpoint with stage filters
Part of the sample program - spec: `docs/specs/2026-08-24-sample.md` (section 2).

## Why this slice
The widget listing endpoint is the seam every later slice consumes: the detail view
(#13) and the search wiring (#14) both read from it. Shipping it first, behind the
existing router registration pattern, means later slices land without touching the
route table again.

## Scope
- New endpoint `GET /api/widgets` returning `{ widgets: WidgetSummary[] }`, paginated.
- Exported API given verbatim: `listWidgets(tenantId, filter) -> Promise<WidgetSummary[]>`, pure data access, no side effects.
- Stage filter values validated against the stage table, unknown values rejected with 400.

## Integration points
- New: `src/widgets/list.ts` (handler plus data access)
- Existing prior art to fold in: `src/example.ts:10` `exampleHandler`, mirror its
  envelope and error mapping. Do NOT rewire the detail view yet, that is #13.

## Test plan (write these first)
- `tests/widgets/list.test.ts`: returns seeded widgets for the tenant; rejects an
  unknown stage value with 400; never returns another tenant's rows.
- Partition: core-coverage. Run the typecheck before pushing.

## Acceptance criteria
- A request with a valid stage filter returns only widgets in that stage, verified
  against seeded fixtures.
- A request with an unknown stage value fails with 400 and a named error code.
- CI fails if the response envelope drifts from the recorded snapshot.

## Out of scope
- Detail view wiring (#13); search integration (#14).

## Blocked by
- #12 seed fixtures for widgets.

## Docs (definition of done)
- `docs/features/current-features.md` entry; roadmap status marker updated.
