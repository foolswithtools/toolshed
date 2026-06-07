// TerminalRun — plays the exploded terminal PNG sequence for one beat.
//
// REFERENCE SCENE. Copied into `videos/<slug>/scenes/` at Phase 4 and adapted.
// The fragile timing math is imported from `./timing` (the tested twin of
// `scripts/timing_math.py`) — DO NOT re-derive frame mapping inline here.
//
// Why time-based mapping (not "output frame n -> PNG n"): agg/ffmpeg only emit
// a GIF frame when the terminal actually changes, so the PNG sequence is NOT
// evenly spaced in time. timing.json's `frame_times_s[i]` is the real cast-clock
// timestamp of PNG i. We map output time -> nearest PNG via castTimeToFrameIndex
// so a long idle render holds the right frame instead of racing the PNGs.
//
// Realtime run beat:   factor = 1.
// Speed-ramped beat:   factor = speedramp_factor (e.g. 4) — each output frame
//                      advances `factor` cast-seconds of source, so the beat
//                      plays `factor`x faster. The scene's Sequence length in
//                      Root.tsx must equal speedrampOutputFrames(...) for the
//                      span, so the last output frame lands on the last PNG.

import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { castTimeToFrameIndex } from "./timing";
import { SafeStaticImg } from "./SafeImg";
import { palette } from "../../../src/brand/active";

export type TerminalRunProps = {
  /** Video slug — used to build the public/<slug>/frames path. */
  slug: string;
  /** `frame_times_s` from timing.json (ascending PNG timestamps, seconds). */
  frameTimesS: number[];
  /** Cast-clock time (seconds) where this beat begins. */
  beatStartS: number;
  /** 1 = realtime; >1 = speed-ramp factor. */
  factor?: number;
  /** Zero-padding width of the PNG filenames (ffmpeg %05d -> 5). */
  padWidth?: number;
};

const pad = (n: number, width: number) => String(n).padStart(width, "0");

export const TerminalRun: React.FC<TerminalRunProps> = ({
  slug,
  frameTimesS,
  beatStartS,
  factor = 1,
  padWidth = 5,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Output time -> cast time (scaled by the ramp factor) -> nearest PNG index.
  const castTime = beatStartS + (frame * factor) / fps;
  const idx = castTimeToFrameIndex(castTime, frameTimesS);
  // PNGs are 1-indexed on disk (ffmpeg %05d starts at 00001).
  const path = `${slug}/frames/${pad(idx + 1, padWidth)}.png`;

  return (
    <AbsoluteFill style={{ backgroundColor: palette.bg }}>
      <SafeStaticImg
        path={path}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "contain",
        }}
      />
    </AbsoluteFill>
  );
};
