# Per-theme example animation packs

A small, curated **example pack** of animated-icon usages, tuned to each shipped
demo theme's *motion personality* via its `motion` block. The pack is identical
code for every theme — only the active brand tokens (palette + `motion` +
`easings`) change — so swapping the theme visibly changes the pack's motion and
color. These are reference/demo compositions the skill can draw on when
assembling a cut, plus this gallery.

Built entirely with the **Phase-1 SVG engine** (`AnimatedIcon` + recipes), not
Lottie: bundleable, frame-deterministic, theme-aware.

## Shipped demo themes

The project ships two brand profiles (in
`plugins/remotion-video/skills/remotion-video/templates/`). Each carries a
theme-level `motion` block (Phase-1 P1-M5):

| Theme | `defaultRecipe` | `durationInFrames` | `easing` | `particleIntensity` | accent / canvas |
|-------|-----------------|--------------------|----------|---------------------|-----------------|
| `default` | `drawOn` | 30 | `pop` (overshoot bezier) | 1.0 | cyan `#22d3ee` on near-black `#0b0d12` |
| `foolswithtools-brand` | `popIn` | 26 | `scribble` (hand-drawn marker) | 1.4 | acid `#CCFF00` on cream `#FAFAF8` |

The two blocks differ on **every** axis — that is what makes "theme-tunable"
non-vacuous: the same pack reads completely differently under each.

## The example pack (same for every theme)

A row of four cells, chosen so each axis of the `motion` block shows up
visibly:

1. **`headline` cell** — `<AnimatedIcon icon="check">` with **no `recipe` prop**,
   so the theme's `motion.defaultRecipe` drives it. `default` strokes a check on
   (`drawOn`); `foolswithtools-brand` pops it in (`popIn`). Proves
   `defaultRecipe` is theme-driven.
2. **`stroke` cell** — `<AnimatedIcon icon="sparkles" recipe="drawOn">`, same
   recipe under both themes but eased by the theme's `motion.easing`. At a shared
   mid-animation frame the stroke progress differs (`pop` overshoot vs `scribble`
   marker curve). Proves `easing` is theme-driven.
3. **`burst` cell** — `<AnimatedIcon icon="bell" recipe="burst">`. Particle count
   scales with `motion.particleIntensity` (8 vs ~11 dots). Proves
   `particleIntensity` is theme-driven.
4. **`pop` cell** — `<AnimatedIcon icon="download" recipe="popIn">`. The spring
   settles over the theme's `motion.durationInFrames` (30 vs 26), so the scale at
   a shared frame differs. Proves `durationInFrames` is theme-driven.

All four recolor to the theme accent and sit on the theme canvas, so the pack
also reads as an on-brand flourish strip, not just a motion test.

## How the engine is parameterized

`AnimatedIcon` normally reads its motion defaults from `src/brand/active` (the
active profile). For a multi-theme showcase that can't swap the module-level
active import, it also accepts an optional **`theme`** prop —
`{ motion, easings }` — that overrides the active-profile defaults for that one
render. Precedence is unchanged: **config `DEFAULT_MOTION` < theme/profile <
per-use prop**. With no `theme` prop the behavior is exactly as before (reads
`active`), so this is backward-compatible.

The `golden-themes` composition renders the pack twice side-by-side — once with
each theme's tokens — proving the difference in a single deterministic render.
The per-theme **probe** compositions (`theme-pack-default`,
`theme-pack-foolswithtools-brand`) render the identical pack on a *neutral*
background with an *identical* icon color, so the only thing that can differ
between them is the motion itself; the e2e test renders a shared mid-animation
frame of each and asserts the stills are not byte-identical (a deterministic
backstop for "switching the theme changes the motion", complementing the vision
pass on the full-palette showcase).
