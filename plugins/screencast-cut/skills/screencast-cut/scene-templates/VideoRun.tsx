// VideoRun — plays one span of a screen-recording MP4 for a beat, optionally
// speed-ramped (Slice C, screen-recording idle-trim).
//
// REFERENCE SCENE. Copied into `videos/<slug>/scenes/` at Phase 4 and adapted.
// Beat layout durations come from `videoBeatOutputFrames(startS, endS, fps,
// factor)` in `./timing` (the tested twin of `scripts/timing_math.py`) — DO NOT
// re-derive the output-frame count inline.
//
// Realtime run beat:  factor = 1.
// Speed-ramped beat:  factor = speedramp_factor — OffthreadVideo plays the
//                     source span at `playbackRate = factor`, and the beat's
//                     Sequence length in Root.tsx must equal
//                     videoBeatOutputFrames(startS, endS, fps, factor) so the
//                     ramp lands exactly on the span's end.
// Hard-cut idle gaps don't use VideoRun — they get a BlurredFrozenFrameCard.

import React from "react";
import { AbsoluteFill } from "remotion";
import { SafeStaticVideo } from "./SafeVideo";
import { palette } from "../../../src/brand/active";

export type VideoRunProps = {
  /** Video slug — builds the public/<slug>/<videoFile> path. */
  slug: string;
  /** Source frame (at composition fps) where this beat begins. */
  startFromFrame: number;
  /** Source frame (exclusive) where this beat ends. Omit to play to the end. */
  endAtFrame?: number;
  /** 1 = realtime; >1 = speed-ramp factor (OffthreadVideo playbackRate). */
  factor?: number;
  /** Source MP4 filename under public/<slug>/ (default source.mp4). */
  videoFile?: string;
};

export const VideoRun: React.FC<VideoRunProps> = ({
  slug,
  startFromFrame,
  endAtFrame,
  factor = 1,
  videoFile = "source.mp4",
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: palette.bg }}>
      <SafeStaticVideo
        path={`${slug}/${videoFile}`}
        startFrom={startFromFrame}
        endAt={endAtFrame}
        playbackRate={factor}
        style={{ width: "100%", height: "100%", objectFit: "contain" }}
      />
    </AbsoluteFill>
  );
};
