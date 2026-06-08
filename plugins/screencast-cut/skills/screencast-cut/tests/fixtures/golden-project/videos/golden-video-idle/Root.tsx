import React from "react";
import { AbsoluteFill, Series } from "remotion";
import { IntroCard } from "./scenes/IntroCard";
import { VideoRun } from "./scenes/VideoRun";
import { BlurredFrozenFrameCard } from "./scenes/BlurredFrozenFrameCard";
import { OutroCard } from "./scenes/OutroCard";
import { computeMasterDuration, videoBeatOutputFrames } from "./scenes/timing";
import timing from "./source/timing.json";

// Slice C golden path: a screen recording whose idle stretches are trimmed.
// video_to_frames.py detected two static stretches (source/timing.json
// idle_gaps): a CUT (2.0→10.75s) and a SPEEDRAMP (13.0→15.75s). The cut is
// replaced by a BlurredFrozenFrameCard; the speedramp plays the span at 4× via
// OffthreadVideo playbackRate. Active stretches play at 1×.
const SLUG = "golden-video-idle";
const FPS = 30;
const SPEEDRAMP_FACTOR = 4;

// Source-frame spans (composition fps). Active runs sit between the detected
// idle gaps; the idle gaps themselves are trimmed.
const RUN_A = { startS: 0, endS: 2 }; // active intro
const CUT_FREEZE_FRAME = 5 * FPS; // a static frame inside the 2–10.75s cut
const RUN_B = { startS: 11, endS: 13 }; // active middle
const RAMP = { startS: 13, endS: 16 }; // dwell → speed-ramp 4×
const RUN_C = { startS: 16, endS: 18 }; // active tail

export const BEATS = {
  intro: 45,
  runA: videoBeatOutputFrames(RUN_A.startS, RUN_A.endS, FPS, 1), // 60
  cut: 30, // BlurredFrozenFrameCard standing in for the long static cut
  runB: videoBeatOutputFrames(RUN_B.startS, RUN_B.endS, FPS, 1), // 60
  ramp: videoBeatOutputFrames(RAMP.startS, RAMP.endS, FPS, SPEEDRAMP_FACTOR), // 23
  runC: videoBeatOutputFrames(RUN_C.startS, RUN_C.endS, FPS, 1), // 60
  outro: 60,
};

export const GOLDEN_VIDEO_IDLE_DURATION = computeMasterDuration(
  [BEATS.intro, BEATS.runA, BEATS.cut, BEATS.runB, BEATS.ramp, BEATS.runC, BEATS.outro],
  0,
);

// Reference timing.json so an unused-import lint never strips the provenance and
// the manifest travels with the bundle.
export const SOURCE_TYPE = timing.source_type;

export const GoldenVideoIdle: React.FC = () => {
  return (
    <AbsoluteFill>
      <Series>
        <Series.Sequence durationInFrames={BEATS.intro}>
          <IntroCard title="idle trim" />
        </Series.Sequence>
        <Series.Sequence durationInFrames={BEATS.runA}>
          <VideoRun slug={SLUG} startFromFrame={RUN_A.startS * FPS} endAtFrame={RUN_A.endS * FPS} factor={1} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={BEATS.cut}>
          <BlurredFrozenFrameCard slug={SLUG} freezeSourceFrame={CUT_FREEZE_FRAME} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={BEATS.runB}>
          <VideoRun slug={SLUG} startFromFrame={RUN_B.startS * FPS} endAtFrame={RUN_B.endS * FPS} factor={1} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={BEATS.ramp}>
          <VideoRun slug={SLUG} startFromFrame={RAMP.startS * FPS} endAtFrame={RAMP.endS * FPS} factor={SPEEDRAMP_FACTOR} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={BEATS.runC}>
          <VideoRun slug={SLUG} startFromFrame={RUN_C.startS * FPS} endAtFrame={RUN_C.endS * FPS} factor={1} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={BEATS.outro}>
          <OutroCard text="trimmed" />
        </Series.Sequence>
      </Series>
    </AbsoluteFill>
  );
};
