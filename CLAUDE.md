# toolshed conventions

Guardrails and conventions for anyone (human or Claude) editing this repo. Keep this file short — link out to plugin SKILL.md files for specifics.

## Hard rule: do not claim Anthropic uses Remotion

No file committed to this repo may state, imply, or hint that Anthropic uses Remotion, that Anthropic builds its launch videos with Remotion, or that any Anthropic-produced video was created with Remotion. That link is unverified and we will not put it into a public repo.

This rule is enforced by `scripts/check-no-anthropic-remotion-claim.sh`, which fails if a committed file places the words "anthropic" and "remotion" (or "remotion-dev") within ~3 lines of each other. Before checking, the script strips a small set of *safe tokens* — names that legitimately contain those words but aren't claims about the company:

- `anthropic-brand` (a profile name)
- `anthropics/skills`, `anthropics/` (the public repo)
- `remotion-video` (this plugin's name)

That means you can write "the `anthropic-brand` profile in `remotion-video`" freely. What you cannot write is bare "Anthropic" near bare "Remotion".

`CLAUDE.md` and the script itself are exempted from the scan because they exist to describe the rule. Run it before every push:

```
bash scripts/check-no-anthropic-remotion-claim.sh
```

If you need to talk about Remotion *and* Anthropic in the same file (e.g. citing the Anthropic brand-guidelines skill from a Remotion-related doc), keep the words far apart and unambiguous about *what* uses Remotion (us, not them).

## Profile naming for the `remotion-video` plugin

The brand-profile that tracks Anthropic's *public* visual identity is named **`anthropic-brand`**. Never `anthropic-style`, `anthropic-launch-video-style`, or any variant that could be read as "this is how Anthropic makes its videos." `anthropic-brand` is correct because the profile reflects Anthropic's published *brand* (colors, type, motifs), not their video pipeline.

The profile must cite, as its source of truth, only:

- The public `anthropics/skills` repo, specifically `skills/brand-guidelines/SKILL.md`.
- Anthropic's published visual identity (colors, typography, motifs as documented in that skill).

Do not cite or paraphrase any non-public material. Do not describe Anthropic's internal tooling.

## General toolshed conventions

- **One job per plugin.** Mirror the shape of `plugins/youtube-transcript/` (a single skill, a small `config.json`, scripts under `scripts/`).
- **Keep SKILL.md actionable.** Phases, prerequisites, configuration, error handling. No marketing.
- **Don't bundle vendored dependencies.** Tell the user what to install (`brew install ...`).
- **Marketplace registration.** Every new plugin needs an entry in `.claude-plugin/marketplace.json`. Bump the plugin's `version` when you want auto-update users to pick up changes.
- **Pre-push ritual.** Run the guardrail script. Re-read every new/edited Markdown file with the lens "does this imply Anthropic uses Remotion?" `python3 -m json.tool` every JSON file you touched.
