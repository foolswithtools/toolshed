Title: feat(trails): add elevation profile endpoint

Part of the Trailmark trail-data program - spec: `docs/specs/2026-08-01-trailmark-data.md` (section 3).

## Why this slice

The route-preview screen needs an elevation profile before it can render a
trail card, and the waypoint search slice (companion example issue) depends
on the same data layer. Shipping the elevation endpoint first, behind the
existing handler pattern, keeps the preview screen buildable without waiting
on search.

## Scope

- New endpoint `GET /api/trails/:id/elevation` returning `{ points: ElevationPoint[] }`, sampled at a fixed distance interval.
- Exported API given verbatim: `getElevationProfile(trailId, sampleIntervalMeters) -> Promise<ElevationPoint[]>`, pure data access, no side effects.
- Interval defaults to 50 meters when the caller omits it; a non-positive interval is rejected with 400.

## Integration points

- New: `src/trails/elevation.ts` (handler plus data access)
- Existing prior art to fold in: `src/trails/list.ts:15` `listTrailsHandler`, mirror its envelope and error mapping. Do NOT rewire the trail listing endpoint yet, that stays out of scope here.

## Test plan (write these first)

- `tests/trails/elevation.test.ts`: returns points sampled at the default interval; honors a caller-supplied interval; rejects a non-positive interval with 400.
- Partition: core-coverage. Run the typecheck before pushing.

## Acceptance criteria

- A request with no interval returns points sampled every 50 meters, verified against a seeded trail fixture.
- A request with a non-positive interval fails with 400 and a named error code.
- CI fails if the response envelope drifts from the recorded snapshot.

## Out of scope

- Waypoint radius search (companion example issue, issue-2-waypoint-search.md); route-preview screen wiring.

## Blocked by

- none.

## Docs (definition of done)

- `docs/features/current-features.md` entry; roadmap status marker updated.
