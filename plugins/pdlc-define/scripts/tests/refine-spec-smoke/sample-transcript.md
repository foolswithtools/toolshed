# refine-spec cold-session smoke: recorded transcript

A recorded run of `run-smoke.sh` against the flawed-vision fixture, with the
pdlc-define plugin loaded from a local checkout and the human side scripted
over `claude -p --resume` turns (model: claude-sonnet-5). Paths are relative;
nothing machine-specific is recorded. `verify-transcript.sh` passes all clauses
against this transcript and the resulting fixture tree. Reproduce with
`run-smoke.sh` (it drives a live model and takes several minutes).

```text
===== HUMAN TURN 1 =====
HUMAN: /pdlc-define:refine-spec docs/VISION.md

I've read the vision doc, decision log, panel personas, and conventions. Starting the refinement session.

---

**Session scope:** refining `docs/VISION.md` stance by stance. I'll restate each stance, challenge where it earns a challenge, bring in critics or research only where a dispute needs them, and propose edits one at a time — nothing lands without your explicit accept. Decisions I propose stay unstamped; stamping is yours. I won't touch issue authoring in this session.

Relevant context I'm holding: D-001 (single-household scope, not multi-tenant SaaS) and D-002 (plain-text CSV import) are already stamped. Panel has two personas available: the burned operator and the skeptical buyer.

Let's start with Stance 1.

---

## Stance 1: CLI first, GUI later

RESTATE: You want to ship a command-line tool first and defer any web GUI until the CLI's core loop — import bank data, get a report — is something you're actually using daily. The reasoning is surface area and feedback speed: a CLI is faster to build and faster to learn from than a GUI.

This one's low-drama, but it has one soft spot worth naming rather than nodding past: "earns daily use" is a vibe, not a gate. Six months from now, how do you know you've crossed the line into "build the GUI now"? Without some marker, this stance is easy to either abandon too early (GUI-itis before the CLI proves itself) or never revisit (CLI forever by default, not by decision).

CHALLENGE: What's the actual signal that tells you the CLI has "earned" a GUI — is it a usage cadence (e.g., you've run it N days out of the last 30), a specific pain point (you're tired of re-running the same report command), or something else? Doesn't need to be precise, just needs to be something you'd recognize when it happens.

How do you want to handle this — is the vague "earns daily use" fine as-is, or is there a concrete signal worth naming in the doc?
[turn1 exit=0]

===== HUMAN TURN 2 =====
HUMAN: Stance 1: leave it as is. I will know daily use when I see it; do not add a marker. Now Stance 2. I think the SQLite claim is factually wrong. Dispatch a researcher to check whether SQLite supports concurrent readers, and whether concurrent reads corrupt the database. Require a real retrieved source attached to the finding, and verify it before proposing any edit.

RESEARCHER RETURNED persona=n/a claim="SQLite cannot serve more than one reader at a time / concurrent reads corrupt the database"

SOURCE:
> "Any number of processes can hold SHARED locks at the same time, hence there can be many simultaneous readers." — https://sqlite.org/lockingv3.html
> "WAL provides more concurrency as readers do not block writers and a writer does not block readers... However, since there is only one WAL file, there can only be one writer at a time." — https://www.sqlite.org/wal.html

CITATION VERIFIED: I checked both quotes against their pages' actual content (not just the researcher's paraphrase). Both are verbatim and both are load-bearing for the verdict — the first directly contradicts "one reader at a time," the second shows the real constraint is single-writer, not single-reader, and that reads/writes don't corrupt each other. The claim in Stance 2 is false: SQLite supports many concurrent readers in both its default mode and WAL mode, and concurrent reads never corrupt the database. The only real constraint is one writer at a time.

---

## Stance 2: Postgres from day one

RESTATE: Your position was that Ledger needs a real server database from the first release because SQLite physically can't handle two household members reading their expenses at the same time without corrupting data, and that risk is unacceptable even at this small scale.

That stated justification just failed verification — it's not what SQLite actually does. So the stance as written is resting on a load-bearing claim that's false.

STEELMAN: Even granting that, there's a non-corruption case for Postgres from day one. Migrating a database engine later is real work — schema dialects drift, a migration script is another thing to write and test, and "later" projects have a way of never happening. If you're fairly sure the household will eventually want concurrent *writes* (two people categorizing transactions at once, not just reading reports), or remote access from a phone hitting a server process, doing that engineering once now is cheaper than doing it twice. That's a legitimate reason — it's just a different reason than the one in the document.

CHALLENGE: Setting aside the SQLite claim, do you actually expect concurrent *writes*, or remote/multi-device access, in Ledger's near-term life? If it's just "someone might glance at a report while someone else is entered a transaction," SQLite handles that natively with zero operational cost. If it's "I want to hit this from my phone while my partner's laptop also writes to it," that's a real Postgres-shaped requirement — but it's also a bigger scope claim than the current doc makes, and it's in tension with D-001 (single-household scope, read every scaling choice through that lens).

Given the burned-operator and skeptical-buyer personas exist in `docs/panel/`, and this stance is now genuinely disputed (its own justification failed), I'd like to cast both against it before we edit — one asks who maintains a Postgres instance on a home server at 11pm, the other asks what concrete job this does that SQLite doesn't. Want me to cast them, or do you want to settle this directly first?
[turn2 exit=0]

===== HUMAN TURN 3 =====
HUMAN: Yes, cast both panel personas against Stance 2. Run them sequentially and independently with no cross-visibility until each has committed its critique; cap at those two. For the record: I do NOT expect concurrent writes or remote multi-device access near-term. This is single-household, mostly one person entering data while another might glance at a report. After the critics commit, propose the edit to Stance 2 that corrects the false SQLite claim and the Postgres-from-day-one conclusion.

CRITIC RETURNED persona=skeptical-buyer

> Strike that [SQLite claim]... nobody's writing concurrently, nobody's on a second device... tell me the job Postgres does that SQLite doesn't, for this household, this year. I don't hear one... Don't sell me infrastructure on a fear that's been checked and found false. Show me the real trigger for Postgres — concurrent writes, remote access — and I'll revisit it when that trigger exists, not before.

Both critics ran sequentially and independently; neither saw the other's critique before committing its own. Both converge on the same read from different angles: the operational-cost lens and the value-justification lens both land on "SQLite now, Postgres on a real trigger."

---

PROPOSED EDIT

Replace Stance 2 in `docs/VISION.md`:

```diff
-## Stance 2: Postgres from day one
-
-Ledger must run Postgres from the first release. SQLite cannot serve more than
-one reader at a time, so a household with two people looking at their expenses
-at once would corrupt the database. A real server database is the only safe
-option even at this tiny scale.
+## Stance 2: SQLite by default, Postgres on a real trigger
+
+Ledger runs on SQLite from the first release. SQLite supports many concurrent
+readers, including in WAL mode, so a household with two people looking at
+their expenses at once is fully supported with no corruption risk. The one
+real constraint is a single writer at a time, which matches Ledger's expected
+usage: mostly one person entering data while another reads a report.
+
+Ledger moves to Postgres only when a concrete trigger shows up: sustained
+concurrent writes or remote, multi-device access. Until then, Postgres adds
+setup and maintenance cost, a server process, its own backup and upgrade
+path, credential management, with no matching benefit at this scale.
```

Rationale: the original justification was factually wrong (verified against sqlite.org), and both critics independently confirmed that, absent concurrent writes or remote access (which the owner has ruled out near-term), Postgres imposes real operational cost for no corresponding benefit, and is a straightforward migration later if a real trigger appears.

[awaiting ACCEPT / REJECT / MODIFY]
[turn3 exit=0]

===== HUMAN TURN 4 =====
HUMAN: ACCEPT. Apply that Stance 2 edit to docs/VISION.md now.

EDIT LANDED

DECISION LOG (proposed, unstamped):

> D-003: SQLite by default, Postgres on a real trigger. Ledger's original Postgres-from-day-one stance rested on a factually wrong claim about SQLite's concurrency model (verified against sqlite.org: SQLite supports many concurrent readers, including in WAL mode; the only real constraint is a single writer at a time). With no concurrent-write or remote-access need in the near term, Ledger defaults to SQLite and migrates to Postgres only if that trigger materializes.

That's proposed, not stamped — stamping is yours whenever you do that in your normal workflow.

On to Stance 3.

## Stance 3: it should feel good to use

RESTATE: Your position is that Ledger should be fast and delightful, that the experience should "spark joy," and users should love reaching for it — that's the quality bar for the product.

CHALLENGE: This is the one stance in the document that isn't a decision at all — it's a mood. "Spark joy" and "love reaching for it" aren't things you can check a build against, argue about being wrong, or hold anyone accountable to. Every other stance in this doc says something falsifiable (CLI vs GUI, SQLite vs Postgres); this one can't be disagreed with because it doesn't commit to anything specific. A spec that dodges its qualitative bar the same way a vague stance dodges a technical one is just as costly later, since "feel good" gives an issue author or a future reviewer nothing to build toward or check against.

What's one concrete, checkable signal that would tell you Ledger has hit this bar, or missed it? For example: import-to-report round trip takes under some number of seconds, the CLI has fewer than some number of steps for the daily check-in flow, error messages tell you exactly what to fix. Doesn't need to be exhaustive, just needs to be something a future you (or an issue) could actually fail.
[turn4 exit=0]

===== HUMAN TURN 5 =====
HUMAN: Good, Stance 3 is too vague. Propose an edit turning it into concrete, checkable signals: import-to-report round trip stays under 2 seconds for a month of transactions; the daily check-in is a single command; every error message names the exact fix. Propose it as one edit with a rationale and wait for my response.

PROPOSED EDIT

Replace Stance 3 in `docs/VISION.md`:

```diff
-## Stance 3: it should feel good to use
-
-Ledger should be fast and delightful. The experience should spark joy and users
-should love reaching for it. That is the bar.
+## Stance 3: concrete usability bar
+
+Ledger meets its usability bar when all of the following hold: the
+import-to-report round trip stays under 2 seconds for a month of
+transactions, the daily check-in is a single command, and every error
+message names the exact fix.
```

Rationale: replaces an unfalsifiable mood ("spark joy") with three checkable signals the owner named directly, so the bar can actually be tested and can actually fail.

[awaiting ACCEPT / REJECT / MODIFY]
[turn5 exit=0]

===== HUMAN TURN 6 =====
HUMAN: MODIFY: add a fourth signal, first-run setup completes in under 5 minutes. Re-propose the full edit and wait again.

PROPOSED EDIT

Replace Stance 3 in `docs/VISION.md`:

```diff
-## Stance 3: it should feel good to use
-
-Ledger should be fast and delightful. The experience should spark joy and users
-should love reaching for it. That is the bar.
+## Stance 3: concrete usability bar
+
+Ledger meets its usability bar when all of the following hold: the
+import-to-report round trip stays under 2 seconds for a month of
+transactions, the daily check-in is a single command, every error message
+names the exact fix, and first-run setup completes in under 5 minutes.
```

Rationale: replaces an unfalsifiable mood ("spark joy") with four checkable signals the owner named directly, so the bar can actually be tested and can actually fail.

[awaiting ACCEPT / REJECT / MODIFY]
[turn6 exit=0]

===== HUMAN TURN 7 =====
HUMAN: ACCEPT the Stance 3 edit and apply it. Then close the session: append the decisions proposed this session to docs/decisions/DECISIONS.md, each clearly marked as PROPOSED (unstamped) with its reason, and do NOT stamp them (that authority is mine); I accept adding those proposed entries to the log. Then run the repo style gate declared in CONVENTIONS.md (no em dashes) over your changes and fix any hit. Print the SESSION CLOSE summary of what changed and what remains open. Then commit everything per the repo commit style with a why-message. Do not file any issues, do not run author-issues, and do not create any new documents; note the document-economy rule if it applies.

Committed as `126dacb`. Session closed: `docs/VISION.md` now has a corrected, evidence-backed database stance and a checkable usability bar; `docs/decisions/DECISIONS.md` carries D-003 as proposed and unstamped, awaiting your stamp. No issues filed, no new documents created, no open questions remain.
[turn7 exit=0]

```
