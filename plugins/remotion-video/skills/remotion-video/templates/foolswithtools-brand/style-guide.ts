// Brand profile: foolswithtools-brand
//
// Source of truth: the live foolswithtools site and its source repo.
//   - https://foolswith.tools/
//   - https://github.com/foolswithtools/website
//
// Tokens here are taken verbatim from the site's `src/app.css` and
// `tailwind.config.js`. This is the **master brand** profile for the
// foolswithtools project — i.e. the published visual identity, not a
// genre-skinned promo treatment.
//
// Vibe: pop-art / punk-zine / maker-blog. Cream paper canvas, charcoal text,
// acid green as the workhorse signature, hot orange + banana yellow as cycle
// accents. Anti-guru, "no hype no gurus" voice.

import { Easing } from "remotion";

// Palette — pulled straight from the site tokens. Don't add new entries.
export const palette = {
  // Canvas
  bg: "#FAFAF8", // paper / off-white — primary canvas
  bgElevated: "#F9FAFB", // zen-paper — slightly lifted surface
  surface: "#F4F4F0", // subtle separator surface
  border: "rgba(26, 26, 26, 0.18)", // 2px charcoal borders are the default

  // Text
  text: "#1A1A1A", // charcoal — primary text
  textMuted: "#3F3F3F", // softer charcoal
  textDim: "rgba(26, 26, 26, 0.45)",

  // Signature accent — the brand color
  accentAcid: "#CCFF00", // acid green — used aggressively
  accentAcidSoft: "rgba(204, 255, 0, 0.20)",
  accentAcidGlow: "rgba(204, 255, 0, 0.55)",

  // Pop accents (cycle order)
  accentOrange: "#F5471D", // hot orange — Tailwind `primary`
  accentBanana: "#FFE55C", // banana yellow
  accentForest: "#2D7A3E", // link / hover green

  // Cool accents (less used, available for variety)
  accentCyan: "#00B5E2",
  accentMagenta: "#E91E63",
  accentLilac: "#E8D5FF",
  accentMint: "#B4FFE8",
  accentMocha: "#6B5B4F",

  // Terminal motif
  terminalBg: "#1A1A1A", // black
  terminalText: "#CCFF00", // acid green CRT text

  // `accent` aliases the primary signature so generic code paths still work.
  accent: "#CCFF00",
  accentSoft: "rgba(204, 255, 0, 0.20)",
  accentGlow: "rgba(204, 255, 0, 0.55)",
} as const;

// Cycle: scene 0 → acid green (workhorse), scene 1 → orange, scene 2 → banana,
// repeating. Use accentForBeat(i) to pull the right one.
export const accentCycle = [
  palette.accentAcid,
  palette.accentOrange,
  palette.accentBanana,
] as const;

export function accentForBeat(beatIndex: number): string {
  return accentCycle[beatIndex % accentCycle.length];
}

// Typography — all from Google Fonts (free).
// Display defaults are: ALL-CAPS, tight tracking (-0.02em), tight leading (0.95).
// Apply those in components by default; expose props to override for CLI strings.
export const fonts = {
  display: '"Archivo Black", "Helvetica Neue", system-ui, sans-serif',
  displayAlt: '"Archivo", system-ui, sans-serif', // for non-bold display variants
  body: '"Inter", system-ui, sans-serif',
  secondary: '"Space Grotesk", "Inter", system-ui, sans-serif', // secondary body, button labels, excerpts
  mono: '"JetBrains Mono", "SF Mono", ui-monospace, monospace',
} as const;

// Sizes — even bigger than anthropic-brand's 144 hero — the wordmark dominates.
export const sizes = {
  hero: 192,
  title: 104,
  subtitle: 56,
  body: 36,
  caption: 24,
  micro: 18,
} as const;

export const radii = {
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  pill: 999,
} as const;

// Easings — energetic but not frantic; the scribble is hand-drawn-feeling.
export const easings = {
  swiftOut: Easing.bezier(0.22, 1, 0.36, 1),
  softInOut: Easing.bezier(0.65, 0, 0.35, 1),
  pop: Easing.bezier(0.34, 1.56, 0.64, 1),
  expoOut: Easing.bezier(0.16, 1, 0.3, 1),
  // For hand-drawn marker reveal — not too smooth.
  scribble: Easing.bezier(0.4, 0.1, 0.6, 0.9),
} as const;

// Springs — punchy with a tiny overshoot. Less aggressive than promo.
export const springs = {
  appear: { damping: 14, mass: 0.5, stiffness: 140 } as const,
  pop: { damping: 10, mass: 0.45, stiffness: 200 } as const,
  // For slow hero breathes.
  settle: { damping: 22, mass: 0.6, stiffness: 90 } as const,
};

// Durations (frames @ 30fps). Mid-tempo: faster than anthropic, slower than promo.
export const durations = {
  intro: 75, // 2.5s
  beat: 80, // ~2.7s
  outro: 80,
  transition: 10, // fast hard cuts mostly, with rare 10-frame fades
} as const;

// Layout — chunky 2px borders are the site convention.
export const layout = {
  safePadding: 100,
  cardPadding: 56,
  gap: 32,
  borderWidth: 2,
} as const;

// Shadows — gentle card lift; gummy/glow are functions you call with a color.
export const shadows = {
  card: "0 16px 48px rgba(26, 26, 26, 0.10), 0 4px 12px rgba(26, 26, 26, 0.06)",
} as const;

// Fat-glow shadow used for gummy buttons.
export function gummyShadow(color: string): string {
  return `0 8px 32px ${color}`;
}

// Halo glow (soft, non-neon).
export function glowFor(color: string): string {
  return `0 0 60px ${color}, 0 0 16px ${color}`;
}

// Gradients
export const gradients = {
  acidToBanana: `linear-gradient(135deg, ${palette.accentAcid} 0%, ${palette.accentBanana} 100%)`,
  acidHalo: `radial-gradient(circle at 50% 50%, rgba(204,255,0,0.18) 0%, transparent 60%)`,
  paperRadial: `radial-gradient(120% 80% at 50% -10%, #FFFFFF 0%, ${palette.bg} 70%)`,
} as const;
