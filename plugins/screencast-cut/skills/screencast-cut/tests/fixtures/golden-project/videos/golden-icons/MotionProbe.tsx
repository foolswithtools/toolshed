import React from "react";
import { AbsoluteFill } from "remotion";
import { palette } from "../../src/brand/active";
import { AnimatedIcon, type IconDef } from "./scenes/AnimatedIcon";
import { ClickRipple } from "./scenes/ClickRipple";
import type { RecipeName } from "./scenes/recipes";
import { icons } from "./scenes/icons";

// Per-recipe PROBE compositions for the deterministic motion assertion
// (tests/test_icons_motion.py). Each probe renders exactly ONE primitive,
// full-frame, with NO <Loop>, on a 30-frame beat starting at frame 0. That makes
// the sampled frames meaningful by construction:
//   frame 0  → animation start (progress 0)
//   frame 15 → GUARANTEED mid-animation (progress 0.5, never a hold/plateau)
//   frame 30 → settled end (progress 1)
// The test renders those three frames and asserts they are not all identical AND
// that the mid frame differs from the start — a recipe that has fallen flat (or
// was swapped for a static placeholder) produces identical stills and FAILS.
//
// Per-recipe ISOLATION is the point: in `golden-icons` all five recipes animate
// in lockstep, so one broken recipe would hide behind the others still moving.
// One probe per recipe means a single static recipe is caught on its own comp —
// which is exactly what the P1.1 mutation sanity-check exercises.

export const PROBE_DURATION = 31; // frames 0..30 inclusive
export const PROBE_BEAT = 30; // the animation beat each probe runs over

// morph needs two structurally-compatible single-path icons (same as the
// golden-icons showcase): plus → minus keeps the shared horizontal stroke and
// collapses the vertical one.
const PLUS: IconDef = { viewBox: "0 0 24 24", paths: ["M5 12 L19 12 M12 5 L12 19"] };
const MINUS: IconDef = { viewBox: "0 0 24 24", paths: ["M5 12 L19 12 M12 12 L12 12"] };

export interface MotionProbeProps {
  kind?: "icon" | "ripple";
  recipe?: RecipeName;
  iconName?: string;
  morph?: boolean;
}

export const MotionProbe: React.FC<MotionProbeProps> = ({
  kind = "icon",
  recipe = "drawOn",
  iconName = "check",
  morph = false,
}) => {
  return (
    <AbsoluteFill
      style={{
        backgroundColor: palette.bg,
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {kind === "ripple" ? (
        <ClickRipple
          x={0.5}
          y={0.5}
          color={palette.accent}
          startFrame={0}
          durationInFrames={PROBE_BEAT}
          maxRadius={240}
          rings={1}
        />
      ) : (
        <AnimatedIcon
          icon={morph ? PLUS : icons[iconName]}
          morphTo={morph ? MINUS : undefined}
          recipe={recipe}
          color={palette.accent}
          size={420}
          startFrame={0}
          durationInFrames={PROBE_BEAT}
        />
      )}
    </AbsoluteFill>
  );
};

// The probe registry — one composition id per recipe + the ripple. Root.tsx maps
// this to <Composition> entries; the motion test parametrizes over the ids.
export const MOTION_PROBES: { id: string; props: MotionProbeProps }[] = [
  { id: "motion-probe-drawOn", props: { kind: "icon", recipe: "drawOn", iconName: "check" } },
  { id: "motion-probe-popIn", props: { kind: "icon", recipe: "popIn", iconName: "bell" } },
  { id: "motion-probe-spin", props: { kind: "icon", recipe: "spin", iconName: "loader-circle" } },
  { id: "motion-probe-burst", props: { kind: "icon", recipe: "burst", iconName: "sparkles" } },
  { id: "motion-probe-morph", props: { kind: "icon", recipe: "morph", morph: true } },
  { id: "motion-probe-ripple", props: { kind: "ripple" } },
];
