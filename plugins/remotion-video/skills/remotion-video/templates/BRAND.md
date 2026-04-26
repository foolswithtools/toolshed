# Brand notes

This file is the human-readable companion to `style-guide.ts`. Read it first when starting any new video so you stay consistent with what's already been established. Update it whenever the user approves a new visual element worth promoting.

## Vibe

Modern, dark-mode, cinematic. Confidence over flash. The accent color does the heavy lifting — most surfaces are restrained dark-grey neutrals so the accent pops.

## Foundations

- **Background:** dark grey (`palette.bg`), softened with `gradients.bgRadial` for depth on hero shots.
- **Text:** off-white display + muted secondary. Body copy never sits on pure black.
- **Accent:** electric teal (`palette.accent`). Use it for emphasis only — one or two uses per scene.
- **Typography:** Inter for everything. Display weights for titles, regular for body, mono only when showing code/numbers.

## Motion

- **Default appearance:** spring with `springs.appear`. Items slide in 16–24px and settle.
- **Beat hits:** `springs.pop` for energy moments (logos landing, stats revealing).
- **Transitions between scenes:** `TransitionSeries` with `fade()` at 18 frames, unless the beat justifies a wipe or slide.
- **Hold time:** never less than 60 frames on a primary visual; viewers need time to absorb.

## Composition primitives (when added)

When you build a reusable element (e.g. a glass card, lower-third, karaoke caption, stat counter), put the component in `src/brand/components/<Name>.tsx` and document its purpose here so future videos pick it up.

- _(none yet — first promotion goes here)_

## Promotion log

Every time an element is promoted from a one-off into the brand, add a one-liner: date, video slug, what was promoted, why.

- _(empty)_
