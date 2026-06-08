import React from "react";
import { AbsoluteFill } from "remotion";
import { LottieIcon } from "../golden-lottie/scenes/LottieIcon";
import { computeMasterDuration } from "../golden-icons/scenes/timing";
import * as defaultTheme from "../../src/brand/profiles/default/style-guide";
import * as fwtTheme from "../../src/brand/profiles/foolswithtools-brand/style-guide";

// ORIGINATED per-theme Lottie showcase (Phase 4). For each shipped demo theme we
// AUTHORED one signature Lottie motif, in that theme's palette/personality
// (scripts/gen_theme_lottie.py → public/lottie/*.json, OWNED + expression-free).
// Here we render both at once, side-by-side, each on its own theme background,
// through the Phase-2 `LottieIcon` (`@remotion/lottie`) path. Because the files
// have NO After-Effects expressions they render deterministically headlessly, so
// `verify_render` can gate them. Nothing here is a pulled third-party file — the
// only Lottie committed to this repo is owned/CC0 with a provenance note.

const FPS = 30;
// 60 frames = one full loop of each 30/60-frame motif. One beat, no transitions
// → the tested helper keeps Root.tsx duration honest (same pattern as
// golden-lottie / golden-themes).
export const GOLDEN_THEME_LOTTIE_DURATION = computeMasterDuration([60], 0);

interface Panel {
  id: string;
  label: string;
  src: string;
  bg: string;
  text: string;
  textMuted: string;
}

const PANELS: Panel[] = [
  {
    id: "default",
    label: "default · orbit",
    src: "lottie/default-orbit.json",
    bg: defaultTheme.palette.bg,
    text: defaultTheme.palette.text,
    textMuted: defaultTheme.palette.textMuted,
  },
  {
    id: "foolswithtools-brand",
    label: "foolswithtools-brand · spark",
    src: "lottie/foolswithtools-spark.json",
    bg: fwtTheme.palette.bg,
    text: fwtTheme.palette.text,
    textMuted: fwtTheme.palette.textMuted,
  },
];

const PanelView: React.FC<{ panel: Panel }> = ({ panel }) => (
  <AbsoluteFill
    style={{
      backgroundColor: panel.bg,
      alignItems: "center",
      justifyContent: "center",
      fontFamily: defaultTheme.fonts.body,
    }}
  >
    <div
      style={{
        position: "absolute",
        top: 90,
        width: "100%",
        textAlign: "center",
        color: panel.text,
        fontFamily: defaultTheme.fonts.display,
        fontSize: defaultTheme.sizes.subtitle,
        fontWeight: 800,
      }}
    >
      {panel.label}
    </div>

    <LottieIcon src={panel.src} loop style={{ width: 360, height: 360 }} />

    <div
      style={{
        position: "absolute",
        bottom: 110,
        width: "100%",
        textAlign: "center",
        color: panel.textMuted,
        fontSize: 24,
      }}
    >
      owned · expression-free · rendered via @remotion/lottie
    </div>
  </AbsoluteFill>
);

export const GoldenThemeLottie: React.FC = () => {
  return (
    <AbsoluteFill style={{ flexDirection: "row", backgroundColor: "#000" }}>
      {PANELS.map((p) => (
        <div
          key={p.id}
          style={{ position: "relative", width: "50%", height: "100%" }}
        >
          <PanelView panel={p} />
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
          backgroundColor: "rgba(128,128,128,0.4)",
        }}
      />
    </AbsoluteFill>
  );
};
