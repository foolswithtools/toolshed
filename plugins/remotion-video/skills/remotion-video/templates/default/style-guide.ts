// Persistent brand style guide for this Remotion project.
// All scenes import from here instead of hardcoding colors/fonts/easings.
// When the user approves a new visual element, promote it into this file
// and note the rationale in BRAND.md so the next video starts ahead.

import { Easing } from "remotion";

export const palette = {
  bg: "#0b0d12",
  bgElevated: "#141822",
  surface: "#1c2230",
  border: "rgba(255, 255, 255, 0.08)",

  text: "#f5f7fa",
  textMuted: "rgba(245, 247, 250, 0.65)",
  textDim: "rgba(245, 247, 250, 0.4)",

  accent: "#22d3ee",
  accentSoft: "rgba(34, 211, 238, 0.18)",
  accentGlow: "rgba(34, 211, 238, 0.45)",

  warn: "#f59e0b",
  ok: "#10b981",
  bad: "#ef4444",
} as const;

export const fonts = {
  display: '"Inter", "SF Pro Display", system-ui, sans-serif',
  body: '"Inter", "SF Pro Text", system-ui, sans-serif',
  mono: '"JetBrains Mono", "SF Mono", ui-monospace, monospace',
} as const;

export const sizes = {
  hero: 128,
  title: 84,
  subtitle: 48,
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
  // For the most common "appear and settle" motion.
  appear: { damping: 18, mass: 0.6, stiffness: 110 } as const,
  // For more energetic pops (CTAs, beat hits).
  pop: { damping: 12, mass: 0.5, stiffness: 180 } as const,
};

export const durations = {
  intro: 90,
  beat: 75,
  outro: 90,
  transition: 18,
} as const;

export const layout = {
  safePadding: 96,
  cardPadding: 56,
  gap: 32,
} as const;

export const shadows = {
  card: "0 30px 80px rgba(0, 0, 0, 0.45), 0 4px 12px rgba(0, 0, 0, 0.25)",
  glow: `0 0 60px ${palette.accentGlow}`,
} as const;

export const gradients = {
  bgRadial: `radial-gradient(120% 80% at 50% 0%, ${palette.bgElevated} 0%, ${palette.bg} 60%)`,
  accentSweep: `linear-gradient(135deg, ${palette.accent} 0%, #6366f1 100%)`,
} as const;
