# Brand notes — `default` profile

This file is the human-readable companion to this profile's `style-guide.ts`. Read it first when starting any new video so you stay consistent with what's already been established. Update it whenever the user approves a new visual element worth promoting.

## How brand profiles work in this project

Brand profiles live under `src/brand/profiles/<name>/`. Each profile is a self-contained set of `style-guide.ts`, `BRAND.md`, and an optional `components/` directory.

The **active profile** is selected by `src/brand/active.ts`, which simply re-exports the active profile's style guide. Scenes import from `src/brand/active` so they don't care which profile is current.

```
src/brand/
├── active.ts                  # re-exports from the active profile
└── profiles/
    ├── default/               # this profile (always seeded)
    │   ├── style-guide.ts
    │   ├── BRAND.md
    │   └── components/        # promoted reusable components (if any)
    └── <other-profile>/       # additional profiles, copied in on request
```

**Switching profiles:** edit the `export * from "./profiles/<name>/style-guide"` line in `active.ts`. Or re-run the `remotion-video` skill with phrasing like "use the `<name>` profile" and it will switch for you.

**Adding a new profile from scratch:**

```bash
cp -R src/brand/profiles/default src/brand/profiles/<new-name>
# edit src/brand/profiles/<new-name>/style-guide.ts and BRAND.md
# then point src/brand/active.ts at the new profile
```

To ship the new profile to other toolshed users, also drop a copy under the plugin's `templates/<new-name>/` directory.

## Vibe (this profile)

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

When you build a reusable element (e.g. a glass card, lower-third, karaoke caption, stat counter), put the component in `src/brand/profiles/default/components/<Name>.tsx` and document its purpose here so future videos pick it up.

- _(none yet — first promotion goes here)_

## Promotion log

Every time an element is promoted from a one-off into the brand, add a one-liner: date, video slug, what was promoted, why.

- _(empty)_
