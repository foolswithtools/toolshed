---
name: crystallize
description: Use when the user wants to turn a repeatable process from the current session into a reusable skill, says "crystallize this", "turn this into a skill", "save this process", or "make this repeatable". Reviews the session, gates on whether a durable method is worth keeping, redacts secrets, and drafts a staged skill for the user's approval. Never auto-runs and never commits to a repo on its own.
version: 0.1.0
disable-model-invocation: true
---

# Crystallize a session into a reusable skill

Turn a hard-won, repeatable method from this session into a staged skill the
next session can pick up. Manual only. Nothing is written without explicit
approval, and nothing is written into a git repo: drafts go to a personal
staging area the user promotes later.

## Operating rules

- Work from your own memory of this session. Do not parse the on-disk transcript.
- Capture the method, not the answer. If what you would write is a specific
  result rather than a reusable procedure, it fails the gate.
- No silent writes. Every file is shown and approved first.
- Cap output at 5 proposals per run. Fewer is better.

## Step 1: Frame the session as a delta

State, in a few lines:
- what the session was trying to do,
- what actually happened (including what went wrong and how it was resolved),
- the reusable method inside it, if any.

## Step 2: Apply the quality gate

A candidate is worth capturing only if all of these hold. Say which it meets.

1. Verified success: a check actually passed. "Seemed to work" does not count.
2. Named failure it prevents: the specific mistake or dead-end the method avoids.
3. A ruled-out dead-end (strongly preferred): an approach you tried that did not
   work, worth recording so it is not retried.

If a candidate fails the gate, name it and say in one line why it is not worth
capturing. Do not draft it.

## Step 3: Redact before anything is shown or written

Scan every candidate for secrets: tokens, keys, passwords, connection strings,
private URLs. Replace each secret value with a reference to where it lives (the
env var name, the MCP tool, the file, the selector). Never write a secret value.
These files get shared, so a value written here leaks.

## Step 4: Route each candidate to one home

Pick the single best home, in this priority order:
1. Update an existing skill (prefer this over a near-duplicate new one).
2. A new skill.
3. An agent (`~/.claude/agents/<name>.md`).
4. A slash command (a skill invoked manually).
5. A CLAUDE.md rule (for a one-line durable preference, not a procedure).
6. Nothing.

## Step 5: Draft (for a new or updated skill)

Before drafting, run the portability test: read the method as if you had never
seen this session or this repo. Does it still make sense and still help in a repo
you have never seen? If not, raise its altitude (method over specifics) or drop it.

Then write the draft following these rules:
- `name`: lowercase-hyphen, gerund preferred (for example `provisioning-tenants`).
  Must not contain `anthropic` or `claude`, and must not be vague (`helper`,
  `utils`).
- `description`: third person, states what it does and when to use it, key use
  case first. Include verbatim any distinctive error string, since people search
  by error message.
- Body: the few killer steps a capable agent would otherwise skip, not a
  transcript of everything done. Keep it under about 500 lines. No hardcoded
  paths, no secret values.
- For a fragile task, give exact steps. For an open task, give the reasoning and
  a sensible default with an escape hatch.
- If the `superpowers:writing-skills` skill is available, use it to author the
  file so its conventions are applied; otherwise apply the rules above directly.

## Step 6: Approve per proposal

Show each proposed file in full. For each, ask: approve, edit, or reject.
Apply edits and re-show before writing. Write only what is approved.

## Step 7: Write to staging

Write approved skills under `~/.claude/skills/<name>/SKILL.md` (create the
directory). Agents go to `~/.claude/agents/<name>.md`. After writing, tell the
user where each file landed and that promoting it into the committed toolshed
repo is a separate step (`/promote`). Do not edit any file inside a git repo
here.
