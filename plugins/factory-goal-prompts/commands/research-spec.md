---
description: Fill the research goal-prompt template into a ready-to-run brief that produces a decision-ready spec (no implementation)
argument-hint: <the capability or architecture question to investigate>
---

Produce a filled research goal prompt for: $ARGUMENTS

You are filling a template, not doing the research. The output of this command is the completed goal prompt itself, ready for the operator to review and paste as the opening prompt of a fresh session (or save under `.claude/prompts/`).

Steps:

1. Read the template at `${CLAUDE_PLUGIN_ROOT}/prompts/01-research-goal-prompt.md`.
2. Fill every `<slot>` from the arguments above plus repo context: read `CLAUDE.md`, the repo's spec directory (`docs/specs/` or wherever dated specs already live), and any open issues or docs that bound the problem. Delete sections the template marks as inapplicable when they truly do not apply.
3. Slots you cannot fill from the repo (candidate options to evaluate, decision criteria, hard constraints beyond CLAUDE.md) get your best concrete proposal marked `PROPOSED - confirm:` so the operator can correct them before use, never a bare `<slot>` left in place.
4. Every `file:line` anchor you write into the prompt must be verified against the current checkout right now; cite what you verified.

The filled prompt must keep every required section of the template: the mission line ending in "Do NOT implement anything", Source of truth, What to evaluate, Deliverables (comparison matrix, recommended architecture, phased plan, open questions with recommended defaults, rejection rationale), Constraints, and Done when.

Output the completed goal prompt in a single fenced block, followed by a short list of the `PROPOSED - confirm:` items awaiting the operator.
