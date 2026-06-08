import React from "react";
import { AbsoluteFill } from "remotion";
import { computeMasterDuration } from "../golden-icons/scenes/timing";
import { THEMES, ThemePack } from "./ThemePack";

// Per-theme example-pack SHOWCASE (Phase 3). The SAME pack rendered once per
// shipped demo theme, side-by-side, each in its own brand palette + motion
// personality. Swapping the active theme would change a single pack; rendering
// both at once makes the difference legible in one deterministic still (vision
// pass) — and the per-theme probe comps add the deterministic byte-differ gate.
//
// Built on the Phase-1 SVG engine (AnimatedIcon + recipes), NOT Lottie.

const FPS = 30;
// One beat, no transitions → the tested helper keeps Root.tsx duration honest
// (same pattern as golden-icons / golden-lottie). Cells loop inside the beat.
export const GOLDEN_THEMES_DURATION = computeMasterDuration([120], 0);

export const GoldenThemes: React.FC = () => {
  return (
    <AbsoluteFill style={{ flexDirection: "row", backgroundColor: "#000" }}>
      {THEMES.map((t) => (
        <div
          key={t.id}
          style={{ position: "relative", width: "50%", height: "100%" }}
        >
          <ThemePack theme={t} />
        </div>
      ))}
      {/* hairline divider between the two theme panels */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: 0,
          bottom: 0,
          width: 2,
          backgroundColor: "rgba(255,255,255,0.18)",
        }}
      />
    </AbsoluteFill>
  );
};
