# Operator constraints preamble

Every pdlc-build action carries this preamble. It is the standing contract for
anyone (human or agent) driving a factory run through these commands. Prepend it
verbatim before you act.

A consuming repo that keeps its own written worker-protocol document supersedes
this default: when the repo names one, carry that document's preamble instead and
say which one you used. When the repo has none, carry the preamble below and mark
it `PROPOSED - confirm:` so the operator can ratify or replace it.

## The contract

1. **Consume the factory interface, never modify it.** These commands run
   `factory init`, `factory run`, and `factory status` against a factory checkout
   and read the artifacts those write. They change nothing inside factory. If a run
   needs a factory change, stop and report it as a finding rather than editing
   factory to make a run pass.

2. **A live run spends real money.** `factory run` with `backend = pi` calls a paid
   model through OpenRouter. Read credits before and after every metered run
   (`/budget-check`), record both figures, and honor the run's spend cap. If a
   settled cost or the running total would cross the cap, stop spending, keep the
   evidence, and report.

3. **Least-privilege credentials.** Launch live runs through the factory checkout's
   own scoped-credential wrapper so the run gets exactly the one credential its
   backend needs and nothing else. Never export the whole secret store to a run,
   never echo, log, or commit a key.

4. **Read the verdict honestly.** The two scores are separate by design; never
   collapse them into one number or one word. An escalation is a real outcome to
   act on, not a failure to hide: walk its reasons and fix the issue, not the
   prompt.

5. **Never end a turn with a live run in flight.** A run launched from a session
   that ends mid-run is killed and its spend wasted. Run in the foreground, or stay
   in-session and poll with a status line until the run settles.

6. **Do not merge on the operator's behalf.** These commands report a run's
   outcome and, on a real land, the branch factory created. The human holds the
   merge gate.

7. **Public-surface hygiene.** Nothing you write into a durable place (a committed
   file, a PR body, an issue comment) may name a private project, company, client,
   or local filesystem path. Scrub captured logs of local paths before you commit
   them as evidence. No em dashes, no filler.
