---
description: Fill the derive-spec goal-prompt template into a brief for specifying a new app by observing an existing one
argument-hint: <observed app and where to observe it> for <target platform or repo>
---

Produce a filled derive-spec goal prompt for: $ARGUMENTS

This is the greenfield counterpart of `/research-spec`: instead of deriving a spec from this repo, the resulting prompt derives one by observing a different, running application. You are filling a template, not writing the spec. The output of this command is the completed goal prompt itself, ready for the operator to review and paste into a fresh session.

Steps:

1. Read the template at `${CLAUDE_PLUGIN_ROOT}/prompts/00-derive-spec-goal-prompt.md`. If that file does not exist, stop and report that this plugin version does not yet ship the derive-spec template; do not substitute another template.
2. Fill every `<slot>` from the arguments above plus whatever the operator has provided about the observed application (paths to its checkout, a running instance, capture notes). Where the observed codebase is available locally, record its upstream SHA in the prompt as the template requires.
3. Preserve the template's anchor policy verbatim: Existing anchors point into the OBSERVED codebase (read-only reference), New paths point into the target repo.
4. Slots you cannot fill (fidelity decision, target-platform affordances, capture access) get a concrete proposal marked `PROPOSED - confirm:` so the operator can correct them before use, never a bare `<slot>` left in place.

The filled prompt must keep every required section of the template, including the screen and flow inventory, the inferred state and data model, the API contract transcription with verbatim shapes and source anchors, edge cases, the explicit fidelity decision, the feature-parity matrix, open questions with recommended defaults, and the contract-test verification hook.

Output the completed goal prompt in a single fenced block, followed by a short list of the `PROPOSED - confirm:` items awaiting the operator.
