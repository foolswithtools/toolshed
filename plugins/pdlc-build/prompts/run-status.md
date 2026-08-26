# run-status: read a run's verdict honestly

Read a factory run's evidence and present its verdict without collapsing the two
scores or the confidence legs. This is the shared procedure both harnesses run.

Prepend the constraints preamble (`operator-constraints`) before you act.

## Inputs

- The work directory a run was executed in.
- Optionally, the specific work-item id and attempt id to read (defaults to the
  last run recorded in the dir).

## Pinned factory invocations (verbatim)

Pinned at authoring time against factory `main` (`factory 0.1.0`, commit
`ff10bd0`). `status` reads written artifacts only; there is no daemon and it
re-runs nothing.

1. Report the last run and every run the dir recorded:

   ```
   factory status <work-dir>
   ```

2. The artifacts `status` reads, if you need the raw values:
   - Run report: `<work-dir>/.factory/last-run.txt` (`factory-run v1`).
   - Verdict file:
     `<work-dir>/.factory/verdicts/<work_item_id>/<attempt_id>.verdict`
     (`factory-verdict v1`).

## What the verdict carries, and how to read it

The verdict file is a frozen `key = value` record:

```
factory-verdict v1
work_item_id      = <string>
attempt_id        = <string>
validation_rate   = <f64>      # app gates that ran and passed
heldout_rate      = <f64>      # held-out scenarios that passed
gap               = <f64>      # validation minus held-out
mutation_score    = <f64>      # NaN when not computed
confidence_land   = <bool>     # the confidence leg
governance_cleared= <bool>     # the governance leg
land              = <bool>     # confidence_land AND governance_cleared
reason            = <one line> # the human-readable leg detail
```

Present these three things, kept apart:

1. **The two scores, never merged.** factory prints both on every `run` and
   `status`:
   - `framework-portability: PASS|FAIL` - did the loop run to a written verdict at
     all (host-tooling independent).
   - `app-buildability: PASS|PARTIAL|FAIL` - did the app's own gates actually
     execute and pass (`validation_rate` 1.0 is PASS, between 0 and 1 is PARTIAL, 0
     is FAIL). Report both lines verbatim. One passing and the other not is a
     legitimate, common state; do not average them.

2. **The two confidence legs, separately.** The `land` field is a two-leg AND:
   the confidence leg (`confidence_land`, driven by blocking gates plus
   `heldout_rate` against its threshold and `gap` against its gap-threshold) and
   the governance leg (`governance_cleared`). Report each leg's own value and the
   `reason` line that explains why each did or did not clear. Do not report `land`
   without reporting which leg failed when it is false.

3. **The thresholds banner.** When factory prints `thresholds: uncalibrated
   defaults`, carry it forward: the held-out pass bar is a placeholder, so a
   passing held-out leg under it is not yet a calibrated guarantee.

## Report

Reproduce factory's outcome line, both score lines verbatim, the verdict's
`land`, `confidence_land`, `governance_cleared`, `validation_rate`,
`heldout_rate`, `gap`, and the full `reason`. Name the verdict file path so the
reader can audit it. If the run escalated, say so plainly and point at
`escalation-triage` for the next step.
