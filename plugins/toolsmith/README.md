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
