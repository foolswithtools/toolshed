Title: feat(trails): waypoint radius search

Part of the Trailmark trail-data program - spec: `docs/specs/2026-08-01-trailmark-data.md` (section 4).

## Why this slice

Field testers need to find named waypoints near their current position
without scrolling the full trail list. This slice adds radius search once
the elevation profile slice (companion example issue) has established the
handler pattern, so both new endpoints ship independently and stay green on
their own.

## Scope

- New endpoint `GET /api/waypoints/search?lat&lng&radiusMeters` returning `{ waypoints: WaypointSummary[] }`, sorted nearest first.
- Exported API given verbatim: `searchWaypoints(center, radiusMeters) -> Promise<WaypointSummary[]>`, pure data access, no side effects.
- Radius is capped at 20000 meters server-side; a larger request is clamped, not rejected.

## Integration points

- New: `src/trails/waypoints.ts` (handler plus data access)
- Existing prior art to fold in: `src/trails/list.ts:15` `listTrailsHandler`, mirror its envelope and error mapping. Do NOT merge this endpoint into the trail listing handler, it stays a separate route.

## Test plan (write these first)

- `tests/trails/waypoints.test.ts`: returns waypoints within radius sorted nearest first; clamps an oversized radius to the cap; returns an empty list, not an error, when nothing is in range.
- Partition: core-coverage. Run the typecheck before pushing.

## Acceptance criteria

- A request within a seeded cluster returns only waypoints inside the radius, nearest first, verified against fixture data.
- A request with a radius above the cap is served as if capped at 20000 meters, verified by comparing both responses.
- CI fails if the response envelope drifts from the recorded snapshot.

## Out of scope

- Elevation profile endpoint (companion example issue, issue-1-elevation-profile.md); route-preview screen wiring.

## Blocked by

- none.

## Docs (definition of done)

- `docs/features/current-features.md` entry; roadmap status marker updated.
