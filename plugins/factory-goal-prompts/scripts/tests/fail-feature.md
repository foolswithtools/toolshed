Title: feature(Widgets): Add widget listing
This body exercises the failure paths of the linter. It deliberately violates several
rules at once so the self-test can assert each finding code fires. It has no spec
anchor line in this preamble, which is itself one of the violations under test here.

## Why this slice
We noticed yesterday that listing was missing, so this adds it. This paragraph also
pads the body over the minimum length so the short-body rule does not mask the other
findings being exercised by this fixture, which needs to stay above five hundred
characters in total across all of its sections to keep the assertions independent.

## Scope
- Add a listing endpoint that works correctly for all users.

## Test plan (write these first)
- We will add tests later once the shape settles.

## Acceptance criteria
- The endpoint works correctly and handles errors as expected.

## Out of scope
- Everything else.

## Blocked by
- Nothing in particular, whenever it fits.

## Docs (definition of done)
- Existing docs to update: `src/missing-file.ts:12` reference check should fail.
