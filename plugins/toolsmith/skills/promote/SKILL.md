---
name: promote
description: Use when the user wants to move a staged skill (drafted by /crystallize under ~/.claude/skills) into the committed toolshed repo so it can be shared, says "promote this skill", or "publish the staged skill". Guides the copy, the marketplace entry, the version bump, and the guardrail checks. Deliberate second step, never automatic.
version: 0.1.0
disable-model-invocation: true
---

# Promote a staged skill into the toolshed repo

Move a skill from personal staging into this committed, public repo. This is the
gate between a captured observation and a shared standard, so it is deliberate.

## Steps

1. Ask which staged skill to promote. List candidates:
   `ls -1 ~/.claude/skills`

2. Re-read the staged `SKILL.md` in full with the user. Confirm:
   - no secret values (only references to where secrets live),
   - the `name` and `description` follow the naming rules,
   - the method is portable (would help in a repo you have never seen).
   Fix anything before promoting.

3. Decide the home in this repo. Either a new one-job plugin under
   `plugins/<name>/skills/<name>/`, or a skill added to an existing plugin if it
   clearly belongs there. Follow the shape of `plugins/youtube-transcript/`.

4. Copy the file into place. If it is a new plugin, add its
   `.claude-plugin/plugin.json` (version `0.1.0`) and a `marketplace.json` entry.
   If it extends an existing plugin, bump that plugin's `version`.

5. Run the guardrails before finishing:
   - `bash scripts/check-no-anthropic-remotion-claim.sh`
   - `python3 -m json.tool` on every JSON file touched.
   - Re-read every new or edited Markdown file against the cross-claim rule
     stated in the toolshed CLAUDE.md, keeping the two forbidden terms far
     apart if both must appear.

6. Show the diff and let the user commit. Do not commit for them unless they ask.
