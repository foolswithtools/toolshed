# toolsmith Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `toolsmith` plugin: it lists existing toolshed tools at session start, captures a repeatable process from the current session into a staged reusable skill on demand (`/crystallize`), and prints a mechanical reminder at session end so a substantial session is not lost.

**Architecture:** One plugin in this marketplace with three parts. Part A is a `SessionStart` hook backed by a shell enumerator (`list-toolshed.sh`). Part B is a manual, non-auto-invoked skill (`/crystallize`) that reasons over the in-session context and writes approved drafts to a personal staging area. Part C is a `SessionEnd` hook backed by a deterministic scanner (`friction-scan.sh`). Promotion into this committed repo is a separate manual skill (`/promote`).

**Tech Stack:** Bash (3.2-compatible, no `mapfile`), Python 3 (for JSON/transcript parsing, already used in this repo), Claude Code plugin format (plugin.json, hooks.json, SKILL.md).

**Spec:** `docs/superpowers/specs/2026-08-28-toolsmith-design.md`

## Global Constraints

- **No em-dashes** in any committed file. Use commas, colons, periods, or parentheses. (Repo CLAUDE.md.)
- **No AI-tell vocabulary or rhetorical tics** in committed prose. (Repo CLAUDE.md.)
- **Cross-claim guardrail (`check-no-anthropic-remotion-claim`):** no committed file may place the two forbidden bare terms within 3 lines of each other. Run `bash scripts/check-no-anthropic-remotion-claim.sh` before finishing. Safe tokens (`anthropic-brand`, `remotion-video`, etc.) are exempt. The rule is stated in the toolshed CLAUDE.md.
- **Skill naming rules (Anthropic public guidance):** skill `name` is lowercase-hyphen, gerund-preferred, no `anthropic`/`claude` in the name, no vague `helper`/`utils`. `description` is third person, states what it does and when to use it, key use case first.
- **Bash target is macOS bash 3.2:** no `mapfile`/`readarray`, no associative arrays. Use POSIX loops.
- **One job per plugin.** Mirror the shape of `plugins/youtube-transcript/`.
- **Validate every JSON file** you touch with `python3 -m json.tool`.
- **Every new plugin needs a `marketplace.json` entry** and a `version` in its `plugin.json`.

---

### Task 1: Plugin scaffold, manifest, and marketplace entry

**Files:**
- Create: `plugins/toolsmith/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json` (add one entry to the `plugins` array)

**Interfaces:**
- Produces: the plugin directory root `plugins/toolsmith/`, plugin name `toolsmith`, version `0.1.0`.

- [ ] **Step 1: Create the plugin manifest**

Create `plugins/toolsmith/.claude-plugin/plugin.json`:

```json
{
  "name": "toolsmith",
  "version": "0.1.0",
  "description": "Capture a repeatable process from the current Claude Code session into a reusable, staged skill with your approval (/crystallize), list existing toolshed tools at session start, and print a mechanical reminder at session end so a substantial session is not lost.",
  "author": {
    "name": "foolswithtools",
    "email": "claudet@ohnobono.com"
  },
  "homepage": "https://github.com/foolswithtools/toolshed",
  "license": "MIT"
}
```

- [ ] **Step 2: Validate the manifest**

Run: `python3 -m json.tool plugins/toolsmith/.claude-plugin/plugin.json`
Expected: pretty-printed JSON, exit 0.

- [ ] **Step 3: Add the marketplace entry**

In `.claude-plugin/marketplace.json`, add this object to the end of the `plugins` array (mind the trailing comma on the previous entry):

```json
{
  "name": "toolsmith",
  "source": "./plugins/toolsmith",
  "description": "Turn a repeatable process from a session into a reusable, staged skill with your approval (/crystallize), surface existing toolshed tools at session start, and get a mechanical reminder at session end. Manual trigger, per-proposal approval, staging-first before any commit, default-on secret redaction."
}
```

- [ ] **Step 4: Validate the marketplace file**

Run: `python3 -m json.tool .claude-plugin/marketplace.json`
Expected: pretty-printed JSON, exit 0.

- [ ] **Step 5: Commit**

```bash
git add plugins/toolsmith/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "Add toolsmith plugin manifest and marketplace entry"
```

---

### Task 2: Config file with thresholds

**Files:**
- Create: `plugins/toolsmith/config.json`

**Interfaces:**
- Produces: `config.json` with keys `session_start_max_chars` (int), `friction_word_threshold` (int). Consumed by Task 3 (`friction-scan.sh`) and Task 4 (`list-toolshed.sh` size budget).

- [ ] **Step 1: Create the config**

Create `plugins/toolsmith/config.json`:

```json
{
  "session_start_max_chars": 1500,
  "friction_word_threshold": 1000
}
```

- [ ] **Step 2: Validate**

Run: `python3 -m json.tool plugins/toolsmith/config.json`
Expected: pretty-printed JSON, exit 0.

- [ ] **Step 3: Commit**

```bash
git add plugins/toolsmith/config.json
git commit -m "Add toolsmith config with session-start and friction thresholds"
```

---

### Task 3: list-toolshed.sh (Part A enumerator)

**Files:**
- Create: `plugins/toolsmith/scripts/list-toolshed.sh`
- Test: `plugins/toolsmith/tests/test-list-toolshed.sh`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: executable `list-toolshed.sh`. Behavior: scans `plugins/*/skills/*/SKILL.md` (relative to a root passed as `$1`, default `.`), extracts each skill's `name:` and `description:` from YAML frontmatter, prints one line per skill as `- <name>: <description-first-120-chars>`. Exit 0 even when nothing is found (prints nothing). Later tasks (hooks.json) call it as `bash scripts/list-toolshed.sh <root>`.

- [ ] **Step 1: Write the failing test**

Create `plugins/toolsmith/tests/test-list-toolshed.sh`:

```bash
#!/usr/bin/env bash
# Dependency-free test for list-toolshed.sh. Exits nonzero on failure.
set -u
here="$(cd "$(dirname "$0")" && pwd)"
script="$here/../scripts/list-toolshed.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# Fixture: a fake marketplace root with one plugin skill.
mkdir -p "$tmp/plugins/demo/skills/make-widgets"
cat > "$tmp/plugins/demo/skills/make-widgets/SKILL.md" <<'EOF'
---
name: make-widgets
description: Use when building widgets from parts. Assembles and verifies them.
---
body text here
EOF

out="$(bash "$script" "$tmp")"

echo "$out" | grep -q "make-widgets" || { echo "FAIL: name missing"; exit 1; }
echo "$out" | grep -q "Assembles and verifies" || { echo "FAIL: description missing"; exit 1; }

# Empty root prints nothing and still exits 0.
empty="$(mktemp -d)"
bash "$script" "$empty" >/dev/null || { echo "FAIL: nonzero on empty"; exit 1; }
rm -rf "$empty"

echo "PASS"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `bash plugins/toolsmith/tests/test-list-toolshed.sh`
Expected: FAIL (script does not exist yet; a "No such file" error and nonzero exit).

- [ ] **Step 3: Write the script**

Create `plugins/toolsmith/scripts/list-toolshed.sh`:

```bash
#!/usr/bin/env bash
# List toolshed skills (name + short description) from plugin SKILL.md files.
# Usage: list-toolshed.sh [root]   (root defaults to current dir)
# bash 3.2 compatible: no mapfile, no associative arrays.
set -u
root="${1:-.}"

# Find every plugin skill manifest under the root.
find "$root" -type f -path '*/plugins/*/skills/*/SKILL.md' 2>/dev/null | sort | while IFS= read -r f; do
  name=""
  desc=""
  # Read only the YAML frontmatter (between the first two --- lines).
  in_fm=0
  while IFS= read -r line; do
    if [ "$line" = "---" ]; then
      if [ "$in_fm" -eq 0 ]; then in_fm=1; continue; else break; fi
    fi
    case "$line" in
      name:*) name="$(printf '%s' "$line" | sed 's/^name:[[:space:]]*//')" ;;
      description:*) desc="$(printf '%s' "$line" | sed 's/^description:[[:space:]]*//')" ;;
    esac
  done < "$f"
  [ -z "$name" ] && continue
  # Truncate the description to keep injected context small.
  short="$(printf '%s' "$desc" | cut -c1-120)"
  printf -- '- %s: %s\n' "$name" "$short"
done
```

- [ ] **Step 4: Make it executable and run the test to verify it passes**

Run: `chmod +x plugins/toolsmith/scripts/list-toolshed.sh && bash plugins/toolsmith/tests/test-list-toolshed.sh`
Expected: `PASS`, exit 0.

- [ ] **Step 5: Sanity-check against the real repo**

Run: `bash plugins/toolsmith/scripts/list-toolshed.sh .`
Expected: one line per existing plugin skill (youtube-transcript, remotion-video, screencast-cut, music-grab, and toolsmith's own skills once they exist). Descriptions truncated to 120 chars.

- [ ] **Step 6: Commit**

```bash
git add plugins/toolsmith/scripts/list-toolshed.sh plugins/toolsmith/tests/test-list-toolshed.sh
git commit -m "Add list-toolshed.sh enumerator with test"
```

---

### Task 4: friction-scan.sh (Part C signal check)

**Files:**
- Create: `plugins/toolsmith/scripts/friction-scan.sh`
- Test: `plugins/toolsmith/tests/test-friction-scan.sh`

**Interfaces:**
- Consumes: `config.json` from Task 2 (`friction_word_threshold`).
- Produces: executable `friction-scan.sh`. Behavior: reads a SessionEnd-style JSON object from stdin containing a `transcript_path` string; counts words across the human/assistant text in that transcript; if the count is at or above `friction_word_threshold`, prints the one-line reminder to stdout and exits 0; otherwise prints nothing and exits 0. If the transcript is missing or unreadable, prints nothing and exits 0 (never blocks or errors the session). Uses Python 3 for robust JSON parsing.

Design note: word count is the v1 trigger because it is robust to transcript format drift. The retry / re-read / re-approval signals named in the spec are documented extension points; they require heuristic JSONL parsing and are deliberately deferred to keep this deterministic and quiet.

- [ ] **Step 1: Write the failing test**

Create `plugins/toolsmith/tests/test-friction-scan.sh`:

```bash
#!/usr/bin/env bash
set -u
here="$(cd "$(dirname "$0")" && pwd)"
script="$here/../scripts/friction-scan.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# A transcript with ~12 words of text: below the 1000-word threshold.
short_t="$tmp/short.jsonl"
printf '%s\n' '{"type":"user","message":{"content":"one two three four five"}}' \
              '{"type":"assistant","message":{"content":"six seven eight nine ten eleven twelve"}}' > "$short_t"
out_short="$(printf '{"transcript_path":"%s"}' "$short_t" | bash "$script")"
[ -z "$out_short" ] || { echo "FAIL: fired below threshold"; exit 1; }

# A transcript with >1000 words: should fire.
long_t="$tmp/long.jsonl"
words="$(python3 -c 'print("word " * 1200)')"
python3 - "$long_t" "$words" <<'PY'
import json, sys
path, words = sys.argv[1], sys.argv[2]
with open(path, "w") as fh:
    fh.write(json.dumps({"type":"assistant","message":{"content":words}}) + "\n")
PY
out_long="$(printf '{"transcript_path":"%s"}' "$long_t" | bash "$script")"
echo "$out_long" | grep -q "crystallize" || { echo "FAIL: did not fire above threshold"; exit 1; }

# Missing transcript: silent, exit 0.
out_missing="$(printf '{"transcript_path":"%s/nope.jsonl"}' "$tmp" | bash "$script")"
[ -z "$out_missing" ] || { echo "FAIL: output on missing transcript"; exit 1; }

echo "PASS"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `bash plugins/toolsmith/tests/test-friction-scan.sh`
Expected: FAIL (script missing).

- [ ] **Step 3: Write the script**

Create `plugins/toolsmith/scripts/friction-scan.sh`:

```bash
#!/usr/bin/env bash
# SessionEnd friction check. Reads hook JSON on stdin, prints a reminder if the
# session is substantial. Never errors the session: any problem -> silent exit 0.
# Usage: echo '{"transcript_path":"..."}' | friction-scan.sh
set -u
here="$(cd "$(dirname "$0")" && pwd)"
config="$here/../config.json"

python3 - "$config" <<'PY'
import json, sys, os

config_path = sys.argv[1]
try:
    with open(config_path) as fh:
        threshold = int(json.load(fh).get("friction_word_threshold", 1000))
except Exception:
    threshold = 1000

try:
    hook = json.load(sys.stdin)
    tpath = hook.get("transcript_path", "")
except Exception:
    sys.exit(0)

if not tpath or not os.path.isfile(tpath):
    sys.exit(0)

def text_of(content):
    # content may be a string or a list of block dicts.
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict) and isinstance(b.get("text"), str):
                parts.append(b["text"])
        return " ".join(parts)
    return ""

words = 0
try:
    with open(tpath) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            msg = obj.get("message") or {}
            words += len(text_of(msg.get("content", "")).split())
except Exception:
    sys.exit(0)

if words >= threshold:
    print("[toolsmith] This session looked substantial (%d words). "
          "Worth a /crystallize before you go?" % words)
PY
```

- [ ] **Step 4: Make it executable and run the test to verify it passes**

Run: `chmod +x plugins/toolsmith/scripts/friction-scan.sh && bash plugins/toolsmith/tests/test-friction-scan.sh`
Expected: `PASS`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add plugins/toolsmith/scripts/friction-scan.sh plugins/toolsmith/tests/test-friction-scan.sh
git commit -m "Add friction-scan.sh session-end reminder with test"
```

---

### Task 5: Wire the hooks

**Files:**
- Create: `plugins/toolsmith/hooks/hooks.json`

**Interfaces:**
- Consumes: `list-toolshed.sh` (Task 3), `friction-scan.sh` (Task 4).
- Produces: `hooks.json` registering a `SessionStart` hook that injects the toolshed listing and a `SessionEnd` hook that runs the friction reminder. `${CLAUDE_PLUGIN_ROOT}` is the plugin root at runtime.

Verification note: the exact SessionStart context-injection contract should be confirmed against the running Claude Code version (the spec flags this). The wrapper below emits the documented `hookSpecificOutput.additionalContext` shape. If that key is not honored, Part A still works through the `/toolshed` manual skill (Task 6), and this file needs only the `additionalContext` wrapper adjusted, not the enumerator.

- [ ] **Step 1: Create hooks.json**

Create `plugins/toolsmith/hooks/hooks.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "printf '{\"hookSpecificOutput\":{\"hookEventName\":\"SessionStart\",\"additionalContext\":%s}}' \"$(bash \"${CLAUDE_PLUGIN_ROOT}/scripts/list-toolshed.sh\" . | python3 -c 'import json,sys; t=sys.stdin.read().strip(); print(json.dumps((\"Toolshed tools available. If this task looks repeatable, check whether one already helps before building from scratch:\\n\"+t) if t else \"\"))')\""
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "bash \"${CLAUDE_PLUGIN_ROOT}/scripts/friction-scan.sh\""
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: Validate the JSON**

Run: `python3 -m json.tool plugins/toolsmith/hooks/hooks.json`
Expected: pretty-printed JSON, exit 0.

- [ ] **Step 3: Smoke-test the SessionStart command in isolation**

Run: `bash plugins/toolsmith/scripts/list-toolshed.sh . | python3 -c 'import json,sys; t=sys.stdin.read().strip(); print(json.dumps(("Toolshed tools available...\n"+t) if t else ""))'`
Expected: a single valid JSON string containing the listing. Confirms the injection payload builds.

- [ ] **Step 4: Commit**

```bash
git add plugins/toolsmith/hooks/hooks.json
git commit -m "Wire toolsmith SessionStart and SessionEnd hooks"
```

---

### Task 6: /toolshed manual listing skill

**Files:**
- Create: `plugins/toolsmith/skills/toolshed/SKILL.md`

**Interfaces:**
- Consumes: `list-toolshed.sh` (Task 3).
- Produces: a manual command `/toolshed`.

- [ ] **Step 1: Write the skill**

Create `plugins/toolsmith/skills/toolshed/SKILL.md`:

```markdown
---
name: toolshed
description: Use when the user asks what tools, skills, or plugins are available, says "check the toolshed", or wants to know whether an existing tool already covers the task before building something new. Lists installed toolshed skills with their descriptions.
version: 0.1.0
disable-model-invocation: false
---

# Toolshed listing

List the tools already available so the user can reuse instead of rebuild.

## Steps

1. Run the enumerator from the plugin root:

   `bash "${CLAUDE_PLUGIN_ROOT}/scripts/list-toolshed.sh" .`

2. Present the result as a short list, grouped if long. For each tool give its
   name and its one-line description.

3. If the user described a task, say plainly whether any listed tool looks like
   a fit, and name it. If nothing fits, say so in one line and continue; do not
   invent a match.
```

- [ ] **Step 2: Verify structure**

Run: `bash plugins/toolsmith/scripts/list-toolshed.sh .`
Expected: the listing the skill will present. Confirm the SKILL.md frontmatter has `name` and a third-person `description`.

- [ ] **Step 3: Commit**

```bash
git add plugins/toolsmith/skills/toolshed/SKILL.md
git commit -m "Add /toolshed manual listing skill"
```

---

### Task 7: /crystallize capture skill (the core deliverable)

**Files:**
- Create: `plugins/toolsmith/skills/crystallize/SKILL.md`

**Interfaces:**
- Consumes: nothing at runtime beyond the current session context and the user's shell.
- Produces: a manual command `/crystallize` that writes approved drafts to a staging area under `~/.claude/skills/`. Never writes into this repo.

- [ ] **Step 1: Write the skill**

Create `plugins/toolsmith/skills/crystallize/SKILL.md` with exactly this content:

````markdown
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
````

- [ ] **Step 2: Verify frontmatter and guardrail**

Run: `python3 -c "import re,sys; t=open('plugins/toolsmith/skills/crystallize/SKILL.md').read(); print('disable-model-invocation: true' in t and 'name: crystallize' in t)"`
Expected: `True`.
Run: `grep -in "remotion" plugins/toolsmith/skills/crystallize/SKILL.md || echo "clean"`
Expected: `clean`.

- [ ] **Step 3: Dry-run review (no automation)**

Read the skill body end to end against the spec's Part B list (delta, gate,
redaction, routing, portability, drafting rules, per-proposal approval, staging
write). Confirm each of the eight is present. This is a manual read, not a test
command.

- [ ] **Step 4: Commit**

```bash
git add plugins/toolsmith/skills/crystallize/SKILL.md
git commit -m "Add /crystallize capture skill"
```

---

### Task 8: /promote skill (staging to committed repo)

**Files:**
- Create: `plugins/toolsmith/skills/promote/SKILL.md`

**Interfaces:**
- Consumes: a staged skill directory under `~/.claude/skills/<name>/`.
- Produces: a manual command `/promote` that guides moving one staged skill into this repo, updates `marketplace.json`, bumps a version, and runs the guardrails. v1 guides and runs checks; it does not fully automate the marketplace edit.

- [ ] **Step 1: Write the skill**

Create `plugins/toolsmith/skills/promote/SKILL.md`:

```markdown
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
   - Re-read every new or edited Markdown file against the cross-claim rule in
     the toolshed CLAUDE.md (keep the two forbidden terms far apart if both must appear).

6. Show the diff and let the user commit. Do not commit for them unless they ask.
```

- [ ] **Step 2: Verify frontmatter**

Run: `python3 -c "print('name: promote' in open('plugins/toolsmith/skills/promote/SKILL.md').read())"`
Expected: `True`.

- [ ] **Step 3: Commit**

```bash
git add plugins/toolsmith/skills/promote/SKILL.md
git commit -m "Add /promote staging-to-repo skill"
```

---

### Task 9: README and final verification

**Files:**
- Create: `plugins/toolsmith/README.md`

**Interfaces:**
- Consumes: everything above.
- Produces: user-facing README; a clean guardrail and JSON-validation pass over the whole plugin.

- [ ] **Step 1: Write the README**

Create `plugins/toolsmith/README.md`:

```markdown
# toolsmith

Turn a repeatable process from a Claude Code session into a reusable skill, and
find the tools you already have.

## What it does

- **At session start:** lists the toolshed's tools so you check for an existing
  one before rebuilding. Also available on demand as `/toolshed`.
- **On demand:** `/crystallize` reviews the session, and if it holds a durable,
  repeatable method, drafts a staged skill for your approval. It gates on
  verified success, redacts secrets, and never writes without a yes.
- **At session end:** a mechanical reminder prints if the session was
  substantial, so a good process does not slip away. No model call, no capture.

## Two tiers

`/crystallize` writes drafts to personal staging (`~/.claude/skills/`). Moving a
draft into this shared repo is a separate, deliberate step: `/promote`. That
keeps immature or secret-bearing drafts out of a public repo.

## Limits

- The session-end reminder cannot pause `/exit`; it prints on the way out.
- The v1 friction trigger is session length. Retry-based signals are a planned
  extension.
- Redaction is best-effort. Staging-first is the real safety margin.
```

- [ ] **Step 2: Run the full test suite**

Run: `bash plugins/toolsmith/tests/test-list-toolshed.sh && bash plugins/toolsmith/tests/test-friction-scan.sh`
Expected: `PASS` from both.

- [ ] **Step 3: Validate every JSON file**

Run: `for f in plugins/toolsmith/.claude-plugin/plugin.json plugins/toolsmith/config.json plugins/toolsmith/hooks/hooks.json .claude-plugin/marketplace.json; do python3 -m json.tool "$f" >/dev/null && echo "ok $f"; done`
Expected: `ok` for all four.

- [ ] **Step 4: Run the repo guardrail**

Run: `bash scripts/check-no-anthropic-remotion-claim.sh; echo "exit $?"`
Expected: exit 0. Note: if the script errors with `mapfile: command not found` (macOS bash 3.2), record that as a pre-existing repo-script bug and instead grep the plugin directly: `grep -rin "remotion" plugins/toolsmith | grep -vi "remotion-video" || echo clean` should print `clean`.

- [ ] **Step 5: Re-read the Markdown lens**

Re-read every new Markdown file (`README.md` and the three `SKILL.md` files) against the cross-claim rule in the toolshed CLAUDE.md. Confirm the two forbidden bare terms never sit within 3 lines of each other.

- [ ] **Step 6: Commit**

```bash
git add plugins/toolsmith/README.md
git commit -m "Add toolsmith README and finalize plugin"
```

---

## Self-Review

**Spec coverage:**
- Part A retrieval (SessionStart injection + `/toolshed`): Tasks 3, 5, 6.
- Part B `/crystallize` with delta framing, quality gate, redaction, routing, portability test, drafting rules, per-proposal approval, staging write: Task 7 (all eight elements present in the skill body).
- Part C mechanical exit reminder: Tasks 4, 5.
- Staging-first default: Task 7 Step 7.
- Promotion as a separate deliberate step: Task 8.
- Redaction default-on: Task 7 Step 3.
- Config/thresholds: Task 2.
- Plugin manifest + marketplace entry + versioning: Task 1.
- Guardrails and JSON validation: Task 9.
- Out-of-scope items (automatic capture, cross-session mining, reuse instrumentation, Pi port) are correctly absent.

**Placeholder scan:** No TBD/TODO. Every script and JSON file is given in full; every SKILL.md body is given in full.

**Type/interface consistency:** `list-toolshed.sh` takes a root arg and prints `- name: desc` lines, consumed the same way by Task 5 and Task 6. `friction-scan.sh` reads stdin JSON with `transcript_path` and reads `friction_word_threshold` from the `config.json` created in Task 2. `${CLAUDE_PLUGIN_ROOT}` is used consistently in hooks and skills. Staging paths (`~/.claude/skills/<name>/`) match between Task 7 (write) and Task 8 (read).

**Known assumption:** the SessionStart `additionalContext` injection contract (Task 5) is to be confirmed against the running Claude Code version; the documented fallback is the `/toolshed` manual skill, which is already built in Task 6.
