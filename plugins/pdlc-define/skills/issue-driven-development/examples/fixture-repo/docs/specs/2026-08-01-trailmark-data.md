# Trailmark data endpoints

Spec for a small set of read endpoints in Trailmark, a fictional hiking-trail
app used only as a worked example for this skill. Not a real product.

## 1. Overview

Trailmark serves trail listings, elevation data, and named waypoints to a
mobile client. This spec covers three endpoints against the same trail
dataset.

## 2. Trail listing

`GET /api/trails` returns the trail catalog. Already shipped; see
`src/trails/list.ts`.

## 3. Elevation profile

`GET /api/trails/:id/elevation` returns a sampled elevation profile for one
trail, at a caller-configurable sample interval.

## 4. Waypoint search

`GET /api/waypoints/search` returns named waypoints within a radius of a
given point, nearest first.
