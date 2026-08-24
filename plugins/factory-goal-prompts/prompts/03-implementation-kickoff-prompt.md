# Kickoff Prompt - Implementation Phase

Use this to start execution **in a fresh session**. Two registers - pick by how much context the issue already carries.

---

## Register A - one-liner (the issue is self-contained)

When the issue was authored under the splitting rules, this is the entire kickoff (ideally via a goal/stop-hook mechanism so the session cannot end before the brief is met):

```
complete github issue <N> in a TDD manner, do not merge the produced PR until CI is green
```

That works *because* the issue body carries the why, the file:line anchors, the write-these-first test plan, the acceptance criteria, and the out-of-scope fence. If typing this feels insufficient, the issue is under-specified - fix the issue, not the prompt.

## Register B - kickoff file (multi-phase feature or extra context)

Save as `docs/context/<YYYY-MM-DD>-<feature>-KICKOFF-PROMPT.md` next to a verified `-context.md`, or paste directly:

---

Read `docs/context/<YYYY-MM-DD>-<feature>-context.md` in this repo - it is on `main` (commit <SHA>) and is the verified analysis + plan-of-record for <roadmap item>. **Verify any claim in it against the current code before relying on it - line numbers may have shifted.**

**Goal:** <one sentence: the capability, the user it serves, and the roadmap item it completes> (~<estimate>).

**Run the flow:** brainstorming → writing-plans → subagent-driven development → finishing-a-development-branch. START by brainstorming with me to resolve the open design decisions in the context doc BEFORE writing the spec - one question at a time.

**Key anchors to verify first:**
- `<src/path/file.ts:NN>` - <what lives there and why it matters>
- `<src/path/other.ts:NN>` - <same>

**Constraints (CLAUDE.md + repo conventions):**
- <the 3-6 constraints that actually bind this work, restated - never make the agent hunt for them>
- Heed the <#N> process lesson: <one sentence>.
- Branch off `main` as `<type>/<kebab-slug>`; open a PR; CI must be green INCLUDING <the suite that historically gets skipped>.
- Subagent slices get a fixed wire contract and an allowed-files list; every slice report pastes observed RED output before implementation.
- Per-task reviews, then a whole-branch review by a fresh-context agent before the PR is declared ready.
- Do not merge without my explicit word.

**Docs hygiene (definition of done):** <exact docs files to update - api-reference, current-features, roadmap item → COMPLETED>.
