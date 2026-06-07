import React from "react";
import { AbsoluteFill } from "remotion";
import { palette, fonts, sizes } from "../../src/brand/active";
import { LottieIcon } from "./scenes/LottieIcon";
import { computeMasterDuration } from "../golden-icons/scenes/timing";

// The Lottie BRING-YOUR-OWN showcase. It renders an Lottie animation we AUTHORED
// ourselves (public/lottie/owned-pulse.json — flat-fill, expression-free, in the
// brand palette) through the Phase-2 `@remotion/lottie` path. Nothing here is a
// pulled third-party file; the only Lottie in this repo is owned/CC0 with a
// provenance note (public/lottie/PROVENANCE).
//
// We load it via `src` (staticFile → fetch behind delayRender) to exercise the
// exact BYO code path; because the file has no expressions it renders
// deterministically every pass, so `verify_render` can gate it.

const FPS = 30;
// 60 frames = two loops of the 30-frame pulse. One beat, no transitions → the
// tested helper keeps Root.tsx duration honest (same pattern as golden-icons).
export const GOLDEN_LOTTIE_DURATION = computeMasterDuration([60], 0);

export const GoldenLottie: React.FC = () => {
  return (
    <AbsoluteFill
      style={{
        backgroundColor: palette.bg,
        fontFamily: fonts.body,
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: 90,
          width: "100%",
          textAlign: "center",
          color: palette.text,
          fontFamily: fonts.display,
          fontSize: sizes.subtitle,
          fontWeight: 800,
        }}
      >
        lottie (bring-your-own)
      </div>

      <LottieIcon
        src="lottie/owned-pulse.json"
        loop
        style={{ width: 360, height: 360 }}
      />

      <div
        style={{
          position: "absolute",
          bottom: 110,
          width: "100%",
          textAlign: "center",
          color: palette.textMuted,
          fontSize: 24,
        }}
      >
        owned-pulse · expression-free · rendered via @remotion/lottie
      </div>
    </AbsoluteFill>
  );
};
