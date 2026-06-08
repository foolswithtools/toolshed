import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { palette, fonts, sizes, springs } from "../../../src/brand/active";

export const IntroCard: React.FC<{ title?: string }> = ({
  title = "golden cut",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: springs.appear });
  // Scale settles 0.85 → 1 and opacity 0.6 → 1: the card is legible from frame
  // 0 (no fade-from-black), so the very first composition frame is a clean
  // intro rather than an ambiguous blank for the verify filmstrip.
  const scale = 0.85 + 0.15 * s;
  const opacity = interpolate(frame, [0, 10], [0.6, 1], {
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill
      style={{
        backgroundColor: palette.bg,
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          opacity,
          transform: `scale(${scale})`,
          fontFamily: fonts.display,
          fontSize: sizes.hero,
          fontWeight: 800,
          color: palette.text,
        }}
      >
        {title}
      </div>
    </AbsoluteFill>
  );
};
