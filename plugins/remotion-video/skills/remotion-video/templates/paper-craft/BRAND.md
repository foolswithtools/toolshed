# Brand notes — `paper-craft` profile

An **aesthetic** profile, not a company identity: layered "cut construction
paper" dioramas. Flat matte fills, soft stacked drop shadows, a warm lantern
key light, deep navy hills receding into dusk. Stop-motion papercraft storybook.

This profile is genre skinning — safe to bundle and reuse. It doesn't track any
real brand's published identity.

## The vibe

Warm and handmade, not slick. Everything looks like it was scissor-cut from
construction paper and stacked with a few millimeters of air between layers —
hence the soft, layered shadows (`shadows.paperFilter`) rather than hard edges.
Deep navy canvas at dusk; a single warm glow (silo lantern light) as the only
hot accent. Chunky cream cut-paper title.

## Foundations

- **Canvas** — dusk navy `palette.bg` (`#20304f`); the color between hill bands.
- **Title** — cream `paper.titleFill` (`#efe7d6`) with the stacked
  `paper.titleShadow` cut-paper lift. Heavy display font (`fonts.display`).
- **Hills recede** — `paper.hillFar → hillMid → hillNear` get lighter as they
  approach the lens (atmospheric depth). Match this in generated art.
- **Structures** — kraft tan (`paper.kraft` / `kraftLite` / `kraftDark`),
  terracotta roofs (`paper.roof`).
- **One warm accent** — `palette.accent` / `paper.glow` (`#f2c777`), used only
  as spilled light. Don't scatter warm elsewhere or the dusk mood breaks.
- **Every layer lifts** — apply `shadows.paperFilter` (a soft
  `drop-shadow`) to each paper group / PNG layer.

## The signature: `LayeredParallaxScene`

The whole profile exists to drive this component (`components/`). Hand it an
ordered `ParallaxLayer[]` — far background first, closest foreground last — and
it gives you a living diorama:

- **Camera push-in** eased on `easings.camera` (`zoomAmount`, default 12%).
- **Depth-scaled parallax** — each layer's `depth` (0 = far, 1 = at the lens)
  scales how much of the zoom + pan it takes. Nearer layers grow faster.
- **Per-layer idle** — optional `idle: { swayPx, bobPx, swayDeg, periodInFrames,
  phase }` keeps wheat swaying, silos breathing, a cat bobbing so nothing sits
  dead still. Offset `phase` per layer so they don't move in lockstep.
- **Cut-paper title** springs in with overshoot (`springs.pop`).

```tsx
const layers: ParallaxLayer[] = [
  { id: "sky", depth: 0.05, render: <SkyFar /> },
  { id: "village", depth: 0.25, render: <Village /> },
  { id: "silos", depth: 0.45, render: <Silos />, idle: { bobPx: 4, periodInFrames: 90 } },
  { id: "wheat", depth: 0.9, render: <Wheat />, idle: { swayDeg: 1.2, swayPx: 6, periodInFrames: 70 } },
  { id: "cat", depth: 1, render: <Cat />, idle: { bobPx: 6, swayDeg: 0.8, phase: 0.5 } },
];
<LayeredParallaxScene layers={layers} title="PARTNERSHIP" />
```

## The art pipeline (how you get the *rich* look)

`PaperPrimitives` ships flat SVG stand-ins (hills, houses, glowing silos, wheat,
a crude cat) so you can build and preview motion with **zero external assets**.
They are deliberately crude — good enough to block out depth and timing.

To reach the textured, photoreal-ish papercraft look, replace primitives with
**generated PNG layers**:

1. **Generate** each layer with an image model on a transparent background —
   e.g. "cut construction-paper cat holding a mouse, side view, soft drop
   shadow, transparent background." Keep the palette inside the `paper` tokens
   above so layers blend. Alternatively generate one full scene and cut it into
   layers (Photoshop, or `rembg` for background removal).
2. **Drop** the PNGs in `<project>/public/layers/`.
3. **Wire** each as a layer via the project's `SafeImg` wrapper — a missing PNG
   then fails the render deterministically instead of rendering a silent black
   layer:
   ```tsx
   import { staticFile } from "remotion";
   import { SafeImg } from "../../SafeImg"; // adjust depth to your scene
   { id: "cat", depth: 1, render: <SafeImg src={staticFile("layers/cat.png")} />,
     idle: { bobPx: 6, phase: 0.5 } }
   ```
4. Keep `depth` and `idle` exactly as with the SVG version — the rig doesn't
   care what's inside `render`.

Order layers back-to-front in the array; the first entry paints first (furthest
back). Give each generated layer generous transparent margins so parallax scaling
never reveals a hard edge.

## Fonts

`fonts.display` prefers **Archivo Black** / Arial Black. For a guaranteed heavy
title in renders, load one via `@remotion/google-fonts/ArchivoBlack` and set it
on the title; the system fallback (`Arial Black`) is fine for previews.

## Promotion log

- **2026-07-04** — profile created from the `paper-craft-parallax` prototype.
  Promoted `LayeredParallaxScene` (camera push-in + depth parallax + idle) and
  `PaperPrimitives` (SVG stand-in layers). Established the `paper` token
  namespace and the generated-PNG-layer pipeline above.
