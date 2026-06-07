import React from "react";
import { AbsoluteFill, Loop } from "remotion";
import { palette, fonts, sizes } from "../../src/brand/active";
import { AnimatedIcon, type IconDef } from "./scenes/AnimatedIcon";
import { ClickRipple } from "./scenes/ClickRipple";
import { computeMasterDuration } from "./scenes/timing";
import type { RecipeName } from "./scenes/recipes";
import { icons } from "./scenes/icons";
import zoom from "./source/zoom_anchors.json";

// Showcase composition exercising EVERY recipe + the ClickRipple, all recolored
// to the brand accent, using curated local icons only (no network in render).
// Each recipe loops so it is mid-animation across the verify filmstrip.

const FPS = 30;
// One beat, no transitions → computeMasterDuration keeps the Root.tsx duration
// in lockstep with the tested helper (same pattern as golden-cut).
export const GOLDEN_ICONS_DURATION = computeMasterDuration([120], 0);
const LOOP = 40; // 30 frames animate, 10 hold, then re-trigger

// morph needs two structurally-compatible single-path icons; plus → minus keeps
// the shared horizontal stroke and dissolves the vertical one.
const PLUS: IconDef = { viewBox: "0 0 24 24", paths: ["M5 12 L19 12 M12 5 L12 19"] };
const MINUS: IconDef = { viewBox: "0 0 24 24", paths: ["M5 12 L19 12 M12 12 L12 12"] };

const RECIPES: { recipe: RecipeName; icon: IconDef; morphTo?: IconDef; label: string }[] = [
  { recipe: "drawOn", icon: icons["check"], label: "drawOn" },
  { recipe: "popIn", icon: icons["bell"], label: "popIn" },
  { recipe: "spin", icon: icons["loader-circle"], label: "spin" },
  { recipe: "burst", icon: icons["sparkles"], label: "burst" },
  { recipe: "morph", icon: PLUS, morphTo: MINUS, label: "morph" },
];

const FLOOR_NAMES = [
  "terminal",
  "arrow-right",
  "mouse-pointer-click",
  "download",
  "folder",
  "play",
  "alert-triangle",
];

const Cell: React.FC<{ label: string; children: React.ReactNode }> = ({
  label,
  children,
}) => (
  <div
    style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: 14,
      color: palette.accent,
    }}
  >
    {children}
    <div style={{ color: palette.textMuted, fontSize: 24, fontFamily: fonts.body }}>
      {label}
    </div>
  </div>
);

export const GoldenIcons: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: palette.bg, fontFamily: fonts.body }}>
      {/* title */}
      <div
        style={{
          position: "absolute",
          top: 70,
          width: "100%",
          textAlign: "center",
          color: palette.text,
          fontFamily: fonts.display,
          fontSize: sizes.subtitle,
          fontWeight: 800,
        }}
      >
        motion primitives
      </div>

      {/* the five recipes, each looping so they stay mid-animation */}
      <div
        style={{
          position: "absolute",
          top: 230,
          width: "100%",
          display: "flex",
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "center",
          gap: 110,
        }}
      >
        {RECIPES.map((r) => (
          <Cell key={r.label} label={r.label}>
            <Loop durationInFrames={LOOP} layout="none">
              <AnimatedIcon
                icon={r.icon}
                recipe={r.recipe}
                morphTo={r.morphTo}
                color={palette.accent}
                size={150}
                startFrame={0}
                durationInFrames={30}
              />
            </Loop>
          </Cell>
        ))}
      </div>

      {/* the curated floor, drawn on, recolored */}
      <div
        style={{
          position: "absolute",
          top: 560,
          width: "100%",
          display: "flex",
          flexDirection: "row",
          flexWrap: "wrap",
          alignItems: "center",
          justifyContent: "center",
          gap: 64,
        }}
      >
        {FLOOR_NAMES.map((name) => (
          <Cell key={name} label={name}>
            <Loop durationInFrames={LOOP} layout="none">
              <AnimatedIcon
                icon={icons[name]}
                recipe="drawOn"
                color={palette.accent}
                size={92}
                startFrame={0}
                durationInFrames={30}
              />
            </Loop>
          </Cell>
        ))}
      </div>

      {/* a continuously-looping center ripple … */}
      <Loop durationInFrames={LOOP}>
        <ClickRipple
          x={0.5}
          y={0.7}
          color={palette.accentGlow}
          startFrame={0}
          durationInFrames={30}
          maxRadius={150}
        />
      </Loop>

      {/* … plus one anchored ripple per zoom anchor, offset so it is mid-expand
          at the anchor's sampled filmstrip frame (proves centering on x/y). */}
      {zoom.anchors.map((a, i) => (
        <ClickRipple
          key={i}
          x={a.x}
          y={a.y}
          color={palette.accent}
          startFrame={Math.round(a.t_s * FPS) - 12}
          durationInFrames={30}
          maxRadius={130}
          rings={1}
        />
      ))}
    </AbsoluteFill>
  );
};
