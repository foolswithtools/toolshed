import React from "react";
import { AbsoluteFill } from "remotion";
import { palette, fonts, sizes } from "../../../src/brand/active";

// The "…" placeholder shown in place of a long idle (cut) gap.
export const IdleCutCard: React.FC = () => (
  <AbsoluteFill
    style={{
      backgroundColor: palette.bgElevated,
      alignItems: "center",
      justifyContent: "center",
    }}
  >
    <div
      style={{
        fontFamily: fonts.mono,
        fontSize: sizes.hero,
        color: palette.textMuted,
        letterSpacing: "0.25em",
      }}
    >
      …
    </div>
  </AbsoluteFill>
);
