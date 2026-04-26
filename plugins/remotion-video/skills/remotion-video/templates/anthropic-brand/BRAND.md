# Brand notes — `anthropic-brand` profile

This profile reflects the public visual identity documented in the [`anthropics/skills` repo, `brand-guidelines/SKILL.md`](https://github.com/anthropics/skills/blob/main/skills/brand-guidelines/SKILL.md). That file is the single source of truth. Don't add palette entries, typefaces, or rules that aren't in it.

This profile is for **us** — toolshed users — to produce videos that resemble that public visual identity. It does not describe how Anthropic produces its own videos.

## Palette (verbatim from source)

**Main:**

- Dark `#141413` — primary text, dark elements.
- Light `#faf9f5` — primary canvas, text on dark.
- Mid Gray `#b0aea5` — secondary elements (muted text, dividers, supporting shapes).
- Light Gray `#e8e6dc` — subtle elevated surfaces.

**Accents:**

- Orange `#d97757` — primary accent.
- Blue `#6a9bcc` — secondary accent.
- Green `#788c5d` — tertiary accent.

## Typography (verbatim from source)

- **Headings:** Poppins (Arial fallback). Use for display and title weight (≥24pt per the source skill).
- **Body:** Lora (Georgia fallback).

The source notes fonts should be pre-installed for best results; otherwise the fallbacks engage automatically.

## Usage rules from the source

- **Smart font application.** Poppins on headings, Lora on body. Don't mix this up.
- **Non-text shapes use accent colors.** Body text stays in dark/light neutrals.
- **Cycle through accents** in order: orange → blue → green. The `accentForBeat(i)` helper in `style-guide.ts` does the math.

## Practical conventions for this profile (toolshed-side, derived from the rules above — not new claims about the source)

- **One accent per scene.** The source emphasizes restraint and cycling; in practice that means a given scene picks one accent and sticks with it.
- **Light canvas first.** `palette.bg` (`#faf9f5`) is the default surface. Use `palette.bgElevated` (`#e8e6dc`) when you need a hint of separation; never invent intermediate tones.
- **Type does the work.** Generous whitespace, large display sizes from `sizes.hero`/`sizes.title`, body in Lora at `sizes.body`. Avoid decorative chrome.
- **Cycle order across a multi-beat video** is `accentForBeat(beatIndex)` — beat 0 → orange, beat 1 → blue, beat 2 → green, beat 3 → orange again.

## Components shipped with this profile

- `WordmarkHero.tsx` — large display word(s) on the light canvas. For intros and titlecards.
- `TypeLedTitle.tsx` — title + subtitle pair with generous whitespace; type-led, no boxes.
- `AccentCallout.tsx` — small emphasis element that takes the active beat's accent (via `accentForBeat`).

## When you promote a new component

After Phase 6 of the `remotion-video` workflow, if a new component is worth keeping, move it into `src/brand/profiles/anthropic-brand/components/<Name>.tsx` and add a one-liner to the **Promotion log** below.

Only promote things that respect the source rules (palette, typography, accent restraint). If a one-off used a color not in the source, don't promote it — leave it as a one-off and pick a source-compliant alternative next time.

## Promotion log

- _(empty — first promotion goes here)_
