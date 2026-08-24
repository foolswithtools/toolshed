# Goal Prompt - Research / Evaluation Phase

Use this when a feature or architecture question needs investigation before anyone writes code. The deliverable is a **decision-ready spec checked into the repo** - not an implementation. Fill the `<slots>`, delete inapplicable sections, and paste as the session's opening prompt (or save under `.claude/prompts/` and point a fresh session at it).

---

Evaluate and recommend an architecture for <the capability, stated concretely - including the distinct data/control paths it must cover>, and produce a **decision-ready evaluation report** with a recommended architecture and a phased implementation plan. Do NOT implement anything.

## Source of truth (read first, in this order)

1. `CLAUDE.md` - project constraints. Non-negotiable.
2. <existing docs/specs/issues that bound the problem, by path and issue number>
3. <decisions already made that this evaluation must honor - with where they are recorded>

Every `file:line` reference you cite must be re-verified against current `main` before citing - the repo moves fast. If a reference has moved, say so rather than quietly using a stale one.

## What to evaluate

- <option/approach 1>
- <option/approach 2>
- <any approach you find that the list above misses - say why you added it>

## Deliverables

Write the report to the repo's spec directory as a dated file (e.g. `docs/specs/<YYYY-MM-DD>-<topic>.md`; use whatever spec home the repo already has) containing:

1. **A comparison matrix** of all evaluated options against the criteria that actually matter here: <e.g. security posture, operational cost, integration effort, failure modes>.
2. **A recommended architecture**, with integration points in the existing codebase - name the actual modules and `file:line` anchors (e.g. <2-3 real candidate modules>), not abstract layers.
3. **A phased implementation plan** where every phase leaves `main` shippable.
4. **Explicit open questions / decisions that need user input** - numbered, in their own section, each with a recommended default. These will be resolved with the owner and recorded back into this report as decisions; never silently pick for the owner.
5. **Honest rejection rationale** for options that don't fit - future readers must see why NOT, not just what won.

## Constraints

- <hard constraints from CLAUDE.md or prior decisions, restated>
- Evidence before assertions: any claim about current behavior must come from reading the code or running a command, with the observation quoted.

## Done when

The report exists at the path above, renders cleanly, every integration point cites a verified `file:line`, and the open-questions section is ready to be walked through with the owner in one batch.
