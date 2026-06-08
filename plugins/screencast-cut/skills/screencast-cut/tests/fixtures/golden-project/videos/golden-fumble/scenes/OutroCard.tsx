import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { palette, fonts, sizes } from "../../../src/brand/active";

export const OutroCard: React.FC<{ text?: string }> = ({
  text = "thanks for watching",
}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 15], [0, 1], {
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
          fontFamily: fonts.display,
          fontSize: sizes.title,
          fontWeight: 700,
          color: palette.accent,
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};
