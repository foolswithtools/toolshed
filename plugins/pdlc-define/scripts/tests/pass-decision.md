Title: decision(sample): pick the widget supplier from the trial data
Genre: decision

Part of the sample program, spec: `docs/specs/2026-08-24-sample.md` (section 2).

## Decision needed
From the recorded trial data, assign the widget supplier role for the next phase.
Two candidates completed the trial; one must be selected before ordering opens.

## Context
The trial ran 2026-08-20 to 2026-08-23. Candidate A delivered every widget on
time at a higher unit price; candidate B missed one delivery window but costs
less per unit. The full comparison table is attached to the trial record. Budget
policy caps the order at the approved ceiling regardless of the choice.

## Recommendation
Candidate A, because delivery reliability dominates unit price at this order
size; where the owner weighs cost heavier, candidate B with a buffer stock is
the fallback.

## What unblocks
- The purchase order draft and the phase kickoff both wait on this decision.

## Blocked by
- none.
