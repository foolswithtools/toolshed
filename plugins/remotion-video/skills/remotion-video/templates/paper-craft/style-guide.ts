// Brand profile: paper-craft
//
// A genre/aesthetic profile (not a company identity): layered "cut construction
// paper" dioramas — soft drop shadows, flat matte fills, a warm key light, deep
// navy hills receding into dusk. Think stop-motion papercraft storybook.
//
// The signature deliverable is the `LayeredParallaxScene` component: hand it an
// ordered list of paper layers (far -> near) and it produces a living diorama
// (camera push-in, depth-scaled parallax, per-layer idle sway). Layers can be
// inline SVG (see PaperPrimitives) OR generated PNGs via <SafeImg> — the rig
// treats both identically. See BRAND.md for the art pipeline.
//
// The top-level exports below mirror the `default` profile's shape so ordinary
// scenes that `import { palette, fonts, ... } from "../../brand/active"` keep
// working when this profile is active. Diorama-specific tokens live under the
// `paper` namespace at the bottom.

import { Easing } from "remotion";

export const palette = {
  // Canvas — dusk navy, the color between the hill bands.
  bg: "#20304f",
  bgElevated: "#273a5e",
  surface: "#2f4670",
  border: "rgba(0, 0, 0, 0.25)",

  // Text — warm paper cream reads as a cut-paper title on the navy.
  text: "#efe7d6",
  textMuted: "rgba(239, 231, 214, 0.72)",
  textDim: "rgba(239, 231, 214, 0.45)",

  // Accent — the warm lantern glow spilling out of the silos.
  accent: "#f2c777",
  accentSoft: "rgba(242, 199, 119, 0.22)",
  accentGlow: "rgba(242, 199, 119, 0.5)",

  warn: "#d98a3d",
  ok: "#8aa06a", // sage paper
  bad: "#b45b4e", // terracotta roof red
} as const;

export const fonts = {
  // Chunky display for the cut-paper title. Archivo Black / Fredoka look great
  // if loaded via @remotion/google-fonts; heavy system fallback otherwise.
  display: '"Archivo Black", "Arial Black", system-ui, sans-serif',
  body: '"Inter", "SF Pro Text", system-ui, sans-serif',
  mono: '"JetBrains Mono", "SF Mono", ui-monospace, monospace',
} as const;

export const sizes = {
  hero: 150,
  title: 96,
  subtitle: 52,
  body: 34,
  caption: 26,
  micro: 18,
} as const;

export const radii = {
  sm: 8,
  md: 16,
  lg: 24,
  pill: 999,
} as const;

export const easings = {
  swiftOut: Easing.bezier(0.22, 1, 0.36, 1),
  softInOut: Easing.bezier(0.65, 0, 0.35, 1),
  pop: Easing.bezier(0.34, 1.56, 0.64, 1),
  // Standard Material/Apple curve for camera moves (push-in, pan). Always
  // present so scenes can rely on `easings.camera` without a fallback branch.
  camera: Easing.bezier(0.4, 0, 0.2, 1),
} as const;

export const springs = {
  appear: { damping: 18, mass: 0.6, stiffness: 110 } as const,
  // Cut-paper cards being "placed" want a little overshoot.
  pop: { damping: 12, mass: 0.5, stiffness: 180 } as const,
};

export const durations = {
  intro: 90,
  beat: 75,
  outro: 90,
  transition: 18,
} as const;

export const motion = {
  defaultRecipe: "popIn",
  durationInFrames: 30,
  easing: "pop",
  particleIntensity: 1,
} as const;

export const layout = {
  safePadding: 96,
  cardPadding: 56,
  gap: 32,
} as const;

// Cut-paper shadows are soft and layered — never a hard 1px edge.
export const shadows = {
  card: "0 24px 60px rgba(0, 0, 0, 0.4), 0 4px 10px rgba(0, 0, 0, 0.3)",
  glow: `0 0 80px ${palette.accentGlow}`,
  // Per-layer paper lift. Apply as a CSS `filter` on an SVG group / PNG layer.
  paperFilter: "drop-shadow(0 8px 10px rgba(0,0,0,0.35))",
} as const;

export const gradients = {
  bgRadial: `radial-gradient(120% 90% at 50% 100%, ${palette.bgElevated} 0%, ${palette.bg} 55%)`,
  duskSky: `linear-gradient(180deg, ${palette.bg} 0%, #1a2740 100%)`,
} as const;

// --- Diorama-specific tokens ---------------------------------------------
// Named colors for the papercraft world. `PaperPrimitives` and any generated
// art should stay inside this range so hand-drawn and generated layers blend.
export const paper = {
  // Hill bands, far -> near. Nearer bands are lighter (atmospheric depth).
  hillFar: "#2c3f66",
  hillMid: "#33507f",
  hillNear: "#3a5a8c",

  // Kraft / construction-paper tan for structures.
  kraft: "#c9a56b",
  kraftDark: "#a9853f",
  kraftLite: "#dcc08a",

  roof: "#b45b4e", // terracotta
  glow: "#f2c777", // lantern light
  wheat: "#cbab6a",
  wheatDark: "#a9863f",

  // Title treatment: cream fill + stacked soft shadow (cut-paper lift).
  titleFill: "#efe7d6",
  titleShadow:
    "0 2px 0 #cbb48f, 0 10px 22px rgba(0,0,0,0.45), 0 3px 6px rgba(0,0,0,0.35)",
} as const;
