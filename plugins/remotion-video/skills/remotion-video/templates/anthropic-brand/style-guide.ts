// Brand profile: anthropic-brand
//
// Source of truth: anthropics/skills repo, skills/brand-guidelines/SKILL.md
// (https://github.com/anthropics/skills/blob/main/skills/brand-guidelines/SKILL.md)
//
// Reflects the public Anthropic visual identity (palette + typography). Values
// here are taken verbatim from that public skill — do not invent extras and do
// not infer values not stated there.

import { Easing } from "remotion";

// Main + accent colors, verbatim from skills/brand-guidelines/SKILL.md.
export const palette = {
  // Light canvas — primary background.
  bg: "#faf9f5",
  // Slightly tinted surface for elevation/cards.
  bgElevated: "#e8e6dc",
  surface: "#e8e6dc",
  border: "rgba(20, 20, 19, 0.12)",

  // Dark — primary text on the light canvas.
  text: "#141413",
  textMuted: "#b0aea5",
  textDim: "rgba(20, 20, 19, 0.45)",

  // Accents (cycle order). One accent per scene, restraint over saturation.
  accentOrange: "#d97757",
  accentBlue: "#6a9bcc",
  accentGreen: "#788c5d",

  // `accent` aliases the primary accent so generic code paths still work.
  accent: "#d97757",
  accentSoft: "rgba(217, 119, 87, 0.18)",
  accentGlow: "rgba(217, 119, 87, 0.35)",
} as const;

// Cycle through these in order: scene 1 = orange, scene 2 = blue, scene 3 = green,
// scene 4 = orange, ... Use accentForBeat(i) to pull the right one.
export const accentCycle = [
  palette.accentOrange,
  palette.accentBlue,
  palette.accentGreen,
] as const;

export function accentForBeat(beatIndex: number): string {
  return accentCycle[beatIndex % accentCycle.length];
}

// Typography per SKILL.md: Poppins for headings (Arial fallback), Lora for body
// (Georgia fallback). Mono is not specified in the source; we use a neutral
// system mono only where we genuinely need monospace (code/numbers).
export const fonts = {
  display: '"Poppins", "Arial", sans-serif',
  body: '"Lora", "Georgia", serif',
  mono: 'ui-monospace, "SF Mono", Menlo, monospace',
} as const;

export const sizes = {
  hero: 144,
  title: 88,
  subtitle: 52,
  body: 32,
  caption: 24,
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
} as const;

export const springs = {
  appear: { damping: 18, mass: 0.6, stiffness: 110 } as const,
  pop: { damping: 12, mass: 0.5, stiffness: 180 } as const,
};

export const durations = {
  intro: 90,
  beat: 75,
  outro: 90,
  transition: 18,
} as const;

export const layout = {
  safePadding: 120,
  cardPadding: 56,
  gap: 32,
} as const;

export const shadows = {
  card: "0 24px 60px rgba(20, 20, 19, 0.12), 0 2px 8px rgba(20, 20, 19, 0.06)",
  glow: `0 0 60px ${palette.accentGlow}`,
} as const;

export const gradients = {
  bgRadial: `radial-gradient(120% 80% at 50% 0%, ${palette.bgElevated} 0%, ${palette.bg} 60%)`,
} as const;
