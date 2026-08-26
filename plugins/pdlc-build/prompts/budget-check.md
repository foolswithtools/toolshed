# budget-check: read credits before and after, append a ledger row

Read the OpenRouter credits balance for pre-run and post-run checks and append a
row to a ledger the caller supplies. Plugin users bring their own ledger, so the
ledger path is always an input, never a path this plugin owns. This is the shared
procedure both harnesses run.

Prepend the constraints preamble (`operator-constraints`) before you act.

## Inputs

- The phase: `pre` or `post` (which side of a run this read is).
- The ledger file path to append to (the caller's ledger).
- A label for the row (for example the run id `gh-<owner/repo>#<n>/AT-1`).
- The factory checkout, when reading credits through its scoped-credential wrapper.

## What it wraps

`scripts/check-credits.sh` in this plugin reads the credits API and appends a
ledger row. It reads OpenRouter's `GET /api/v1/credits` and reports
`data.total_usage` to nine decimals (the authoritative metered figure; the
generations API is by-request-id only and pi surfaces no ids, so the credits
delta is the ledger of record). The credits read itself is not a model call and
costs nothing.

## Pinned invocations (verbatim)

The credits key reaches the read through the factory checkout's scoped-credential
wrapper, so this read gets only `OPENROUTER_API_KEY`:

1. Print the current total usage (no ledger write):

   ```
   scripts/scoped-creds.sh pi -- bash <pdlc-build>/scripts/check-credits.sh read
   ```

2. Read and append a ledger row in one step (the `pre` or `post` snapshot around a
   run):

   ```
   scripts/scoped-creds.sh pi -- bash <pdlc-build>/scripts/check-credits.sh append \
     --ledger <ledger-path> --phase <pre|post> --label "<run id>"
   ```

`<pdlc-build>` is wherever this plugin is installed. The API endpoint and the
`total_usage` field are pinned against OpenRouter's credits API as used by
factory's own cost-reconciliation flow; re-verify the endpoint if OpenRouter
revises it.

## Steps

1. Before a metered run, run the `append --phase pre` invocation against the
   caller's ledger with the run's label. Record the printed `total_usage`.
2. Launch the run (see `submit-run`).
3. After the run process exits, run the `append --phase post` invocation with the
   same label. OpenRouter meters with slight lag, so for an exact settled figure
   read once immediately and once again after roughly 45 seconds and record both;
   the later read is the settled cost.
4. Report the settled delta (`post` minus `pre`) as the run's metered cost and
   reconcile it against the run report's `model_cost` from
   `<work-dir>/.factory/last-run.txt`. A large divergence from expected cost is
   itself a finding: stop and report rather than retrying blindly.

## Ledger row format

`check-credits.sh append` writes one tab-separated row per call:

```
<iso8601-utc>	<phase>	<label>	<total_usage>
```

Never touch a private planning ledger from a smoke or a demo: append to the
caller's ledger path only. The row carries no secret; the credits key is never
echoed, logged, or written.

## Report

Report the pre and post `total_usage` figures (nine decimals), the settled delta,
the ledger path and the appended rows, and the reconciliation against
`model_cost`.
