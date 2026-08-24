# Goal Prompt - Derive a Spec by Observing an Existing App

Use this when the spec's source of truth is not your own repo but a **different, existing application** - one you can run and whose code you can read, while the deliverable lives in a **new target repo**, often on a different platform. This is the greenfield counterpart to the research prompt (`${CLAUDE_PLUGIN_ROOT}/prompts/01-research-goal-prompt.md`): instead of mining your own codebase, you practice behavioral archaeology on someone else's. The deliverable is a **decision-ready behavioral spec checked into the target repo** - not an implementation, and not a single write to the observed codebase. Fill the `<slots>`, delete inapplicable sections, and paste as the session's opening prompt.

---

Derive a decision-ready spec for <the target app: platform and one-line mission> by observing <the observed app: name, how to run it, where its code lives>. Do NOT implement anything. The observed codebase is **strictly read-only reference material**: never edit, commit, push, or open issues or PRs there.

## Source of truth (in this order)

1. `CLAUDE.md` in the target repo - constraints. Non-negotiable.
2. The observed app, **running** - when observed behavior and observed code disagree, behavior wins and the disagreement is recorded.
3. The observed codebase, pinned: record the upstream commit as `Observed at <org/repo> <SHA>` at the top of the spec. Every anchor into the observed code cites against that SHA, so the spec stays checkable after upstream moves.

## Capture discipline

Walk the observed app screen by screen and flow by flow, and capture as you go - screenshots or numbered observation notes, each labeled with the screen, the action taken, and what happened. Force the states that do not appear on the happy path: kill the network, empty the data, submit garbage. A behavior you did not capture is a behavior you may not claim.

## Deliverables

Write the spec to the target repo's spec directory as a dated file (e.g. `docs/specs/<YYYY-MM-DD>-<topic>.md`; use whatever spec home the target repo has) containing:

1. **Screen and flow inventory** - every screen with its entry points, user actions, and exits; every flow as an ordered screen sequence. Each row cites its capture.
2. **State and data model, inferred from behavior** - the entities, fields, and lifecycle the observed behavior implies. Mark every element `observed` (seen on screen or in traffic) or `inferred` (deduced), and say from what.
3. **API contract transcription** - request and response shapes given VERBATIM from the observed code or captured traffic, each with a `file:line` anchor into the observed codebase at the pinned SHA. No paraphrased shapes: a field you renamed is a field you invented.
4. **Edge cases** - offline, empty, and error states, each observed by forcing it, with the observed behavior and what the target app should do.
5. **Platform affordances** - where <the target platform>'s native idioms should replace the observed app's, named concretely; the goal is a native citizen of the target platform, not a foreign UI in translation.
6. **Fidelity decision** - job-to-be-done versus clone, recorded as an explicit spec decision with rationale. Every later scope call traces back to this line.
7. **Feature-parity matrix** - every observed feature marked `clone` / `adapt` / `not-cloned`, with an honest rationale for every `not-cloned` row - future readers must see why NOT, not just what made it.
8. **Open questions** - numbered, in their own section, each with a recommended default. These get resolved with the owner and recorded back as decisions; never silently pick for the owner.
9. **Contract tests emitted from the transcribed shapes** - runnable test files in the target repo asserting the transcribed request/response shapes, as the spec's own verification hook: when the target implementation exists, these tests fail if it drifts from the observed contract.

## Anchor policy (greenfield)

Issues derived from this spec split their anchors by side, and the issue linter's New-versus-Existing rules apply per side:

- **Existing** anchors point into the OBSERVED codebase (read-only reference), cited against the pinned SHA.
- **New** paths point into the target repo.

Never mix the two in one line; a reader must always know which repo an anchor lives in.

## Constraints

- <hard constraints from the target repo's CLAUDE.md, restated>
- Evidence before assertions: every behavioral claim traces to a labeled capture or a `file:line` in the observed code, quoted where load-bearing.
- The observed codebase stays untouched; if the task appears to require writing there, stop and report instead.

## Done when

The spec exists at the path above with the upstream SHA recorded, every section above present, every anchor verified against the pinned SHA, the contract tests committed alongside it, and the open-questions section ready to be walked through with the owner in one batch.

---

## Worked micro-example (one screen)

One screen of a hypothetical web app, "Brewlog" (a coffee-brewing journal), being respecced for mobile - so a cold author sees the register:

> Observed at example/brewlog `4f2c91a`.
>
> **Inventory - Log Entry screen.** Entry: tap a bean on the Beans list (capture 07). Actions: pick method from a fixed list, enter grams and seconds, save. Exit: back to Beans list with a toast (capture 09).
>
> **Model (inferred).** Entity `Brew`: `beanId` (observed - the URL carries it), `method` (observed - fixed list of 5), `doseGrams`, `brewSeconds` (observed - numeric inputs), `rating` (inferred - stars render on the list screen but no input exists here; open question 3).
>
> **Contract.** `POST /api/brews` accepts `{ "beanId": string, "method": string, "doseGrams": number, "brewSeconds": number }` and returns `201` with `{ "id": string, "createdAt": string }` - `src/routes/brews.ts:41` at the pinned SHA.
>
> **Parity.** `method picker: clone` (core to the job). `toast on save: adapt` (target platform uses its native confirmation idiom). `keyboard shortcuts: not-cloned` (no hardware keyboard on the target platform; revisit if tablets enter scope).
>
> **Contract test (emitted).** `tests/contracts/brews.test.ts` - asserts a valid `POST /api/brews` body round-trips to a `201` whose response carries exactly `id` and `createdAt`.
