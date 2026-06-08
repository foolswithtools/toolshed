import React from "react";
import { AbsoluteFill, Loop } from "remotion";
import { AnimatedIcon } from "../golden-icons/scenes/AnimatedIcon";
import type { MotionSettings } from "../golden-icons/scenes/timing";
import { icons } from "../golden-icons/scenes/icons";
import * as defaultTheme from "../../src/brand/profiles/default/style-guide";
import * as fwtTheme from "../../src/brand/profiles/foolswithtools-brand/style-guide";

// Per-theme example animation packs (Phase 3). The SAME pack code renders under
// each shipped demo theme; only the brand tokens (palette + `motion` + `easings`)
// change, so swapping the theme visibly changes the pack's motion and color.
//
// Built on the Phase-1 SVG engine (AnimatedIcon + recipes) — bundleable,
// frame-deterministic, theme-aware. NOT Lottie.

export interface Theme {
  id: string;
  label: string;
  palette: { bg: string; text: string; textMuted: string; accent: string };
  /** The profile `easings` map (bezier fns keyed by name). */
  easings: Record<string, (x: number) => number>;
  /** The profile `motion` block. */
  motion: Partial<MotionSettings>;
}

// The two shipped demo themes, each carrying its own motion personality.
export const THEMES: Theme[] = [
  {
    id: "default",
    label: "default",
    palette: {
      bg: defaultTheme.palette.bg,
      text: defaultTheme.palette.text,
      textMuted: defaultTheme.palette.textMuted,
      accent: defaultTheme.palette.accent,
    },
    easings: defaultTheme.easings as Record<string, (x: number) => number>,
    motion: defaultTheme.motion,
  },
  {
    id: "foolswithtools-brand",
    label: "foolswithtools-brand",
    palette: {
      bg: fwtTheme.palette.bg,
      text: fwtTheme.palette.text,
      textMuted: fwtTheme.palette.textMuted,
      accent: fwtTheme.palette.accent,
    },
    easings: fwtTheme.easings as Record<string, (x: number) => number>,
    motion: fwtTheme.motion,
  },
];

export function themeById(id: string): Theme {
  const t = THEMES.find((x) => x.id === id);
  if (!t) throw new Error(`unknown theme: ${id}`);
  return t;
}

// One animation beat each cell runs over; cells loop so the filmstrip lands
// mid-animation. 40 = ~30 animate + ~10 hold, matching golden-icons.
const BEAT = 30;
const LOOP = 40;

// Neutral probe palette: identical for BOTH themes so that the ONLY thing that
// can differ between two probe renders is the motion itself (recipe/easing/
// intensity/duration), never the color or background. The differ-assertion test
// relies on this.
const NEUTRAL_BG = "#202531";
const NEUTRAL_ICON = "#ffffff";

// The four cells. Each isolates one axis of the theme `motion` block:
//  - headline: NO recipe → theme `defaultRecipe` (drawOn vs popIn)
//  - stroke:   drawOn     → theme `easing` changes the stroke progress curve
//  - burst:    burst      → theme `particleIntensity` changes particle count
//  - pop:      popIn      → theme `durationInFrames` changes the settle timing
const CELLS: { key: string; iconName: string; recipe?: "drawOn" | "burst" | "popIn" }[] = [
  { key: "headline", iconName: "check" },
  { key: "stroke", iconName: "sparkles", recipe: "drawOn" },
  { key: "burst", iconName: "bell", recipe: "burst" },
  { key: "pop", iconName: "download", recipe: "popIn" },
];

const Cell: React.FC<{
  theme: Theme;
  iconName: string;
  recipe?: "drawOn" | "burst" | "popIn";
  color: string;
  labelColor: string;
  loop: boolean;
  size: number;
}> = ({ theme, iconName, recipe, color, labelColor, loop, size }) => {
  const icon = (
    <AnimatedIcon
      icon={icons[iconName]}
      recipe={recipe}
      theme={{ motion: theme.motion, easings: theme.easings }}
      color={color}
      size={size}
      startFrame={0}
      durationInFrames={BEAT}
    />
  );
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 12,
        color,
      }}
    >
      {loop ? (
        <Loop durationInFrames={LOOP} layout="none">
          {icon}
        </Loop>
      ) : (
        icon
      )}
      <div style={{ color: labelColor, fontSize: 20 }}>{iconName}</div>
    </div>
  );
};

export interface ThemePackProps {
  theme: Theme;
  /**
   * Neutral mode (the probes): identical gray bg + white icons for every theme,
   * NO loop, so the only inter-theme difference is the motion. Showcase mode
   * (default): the theme's own palette + looped cells.
   */
  neutral?: boolean;
  showTitle?: boolean;
}

export const ThemePack: React.FC<ThemePackProps> = ({
  theme,
  neutral = false,
  showTitle = true,
}) => {
  const bg = neutral ? NEUTRAL_BG : theme.palette.bg;
  const iconColor = neutral ? NEUTRAL_ICON : theme.palette.accent;
  const labelColor = neutral ? "rgba(255,255,255,0.55)" : theme.palette.textMuted;
  const size = neutral ? 200 : 130;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: bg,
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      {showTitle && (
        <div
          style={{
            position: "absolute",
            top: neutral ? 70 : 56,
            width: "100%",
            textAlign: "center",
            color: neutral ? NEUTRAL_ICON : theme.palette.text,
            fontSize: 40,
            fontWeight: 800,
          }}
        >
          {theme.label}
        </div>
      )}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: neutral ? 80 : 56,
          rowGap: neutral ? 90 : 64,
        }}
      >
        {CELLS.map((c) => (
          <Cell
            key={c.key}
            theme={theme}
            iconName={c.iconName}
            recipe={c.recipe}
            color={iconColor}
            labelColor={labelColor}
            loop={!neutral}
            size={size}
          />
        ))}
      </div>
    </AbsoluteFill>
  );
};

// Thin wrapper for the <Composition> boundary: all props optional (resolves the
// theme by id internally) so it satisfies Remotion's loose component typing.
// `showTitle={false}` is deliberate: the probe must render NOTHING that varies
// between themes except the motion — the per-theme label text would itself
// force a byte difference and defeat the "difference is purely motion" gate.
export const ThemeProbe: React.FC<{ themeId?: string }> = ({
  themeId = "default",
}) => <ThemePack theme={themeById(themeId)} neutral showTitle={false} />;

// Per-theme PROBE registry — one composition id per theme, each rendering the
// identical neutral pack. test_themes_e2e.py renders a shared mid-animation
// frame of each and asserts the stills are NOT byte-identical: a deterministic
// backstop proving the theme's motion block actually drives the pack.
export const THEME_PROBES: { id: string; themeId: string }[] = THEMES.map((t) => ({
  id: `theme-pack-${t.id}`,
  themeId: t.id,
}));
