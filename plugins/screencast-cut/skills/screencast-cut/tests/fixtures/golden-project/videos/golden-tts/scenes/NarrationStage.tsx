// NarrationStage — the content beat for a Script:-driven cut.
//
// There's no terminal/video here: the "content" IS the generated narration,
// played over a plain brand-bg stage with the word-timed Captions layer (mounted
// in Root) on top. The audio rides through SafeStaticAudio (warn-only: a missing
// voiceover should still ship a render).

import React from "react";
import { AbsoluteFill } from "remotion";
import { SafeStaticAudio } from "./SafeVideo";
import { palette, fonts, sizes } from "../../../src/brand/active";

export const NarrationStage: React.FC<{ slug: string }> = ({ slug }) => {
  return (
    <AbsoluteFill
      style={{
        backgroundColor: palette.bg,
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <SafeStaticAudio path={`${slug}/narration.wav`} />
      <div
        style={{
          fontFamily: fonts.body,
          fontSize: sizes.body,
          fontWeight: 600,
          color: palette.textMuted,
          letterSpacing: 1,
        }}
      >
        narration · generated from script
      </div>
    </AbsoluteFill>
  );
};
