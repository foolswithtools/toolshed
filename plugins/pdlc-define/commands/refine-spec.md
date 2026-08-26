---
description: Facilitate an interactive spec-refinement session that settles a draft spec's stances with its owner before issue authoring
argument-hint: <path to the spec document to refine>
---

Facilitate a spec-refinement session for: $ARGUMENTS

This command runs the refinement step of the pdlc-define lifecycle: the
facilitated conversation that settles a draft spec's stances with its owner, so
the spec earns the right to become issues. Authoring waits for a stamped spec;
this session never runs `${CLAUDE_PLUGIN_ROOT}/commands/author-issues.md`.

Read the full protocol at
`${CLAUDE_PLUGIN_ROOT}/prompts/05-refine-spec-facilitation.md` and follow it
exactly. It is the shared core both harnesses run (the pi package exposes the
same file as a prompt); do not restate or improvise the protocol here, run it
from that file. It defines the three layers (facilitator, adversarial critics,
researchers), the hard-coded editing contract, the live session state, the
scope guard, and the session-close steps, along with the visible marker
vocabulary the session must emit so every contract clause is auditable from the
transcript.

Subagents in Claude Code: you have the Task/Agent tooling, so spawn each critic
(Layer 2) and each researcher (Layer 3) as its own subagent, one per
invocation, to get the real context isolation the protocol requires. The
protocol also documents the graceful degradation to inline role-switching for
harnesses with no subagent primitive (pi consumers); state that fallback
honestly if you ever run without Task tooling.

## Design basis

The protocol's stances are evidence-backed; these citations travel with the
command so the rationale is not lost:

- Restate before challenging, vary the intervention (Socratic facilitation):
  https://aclanthology.org/2025.findings-emnlp.888.pdf
- Bring a steelmanned counter-position, not only questions:
  https://arxiv.org/pdf/2503.14263
- Hold a well-supported position under pushback (sycophancy mitigation):
  https://arxiv.org/pdf/2602.01002
- Cap critics at 2 to 3, keep them heterogeneous, run them independently with no
  cross-visibility (error correlation and consensus amplification):
  https://arxiv.org/pdf/2605.29800,
  https://aclanthology.org/2025.findings-acl.1141/
- Attach the retrieved source to every researched claim and verify the citation
  against it (fabricated-citation evidence and mitigation):
  https://arxiv.org/pdf/2605.07723, https://arxiv.org/pdf/2605.08583
- Edit as you agree with explicit acceptance per edit; silence is never
  acceptance (co-editing trust findings): https://arxiv.org/pdf/2504.12488,
  https://arxiv.org/pdf/2509.11826
