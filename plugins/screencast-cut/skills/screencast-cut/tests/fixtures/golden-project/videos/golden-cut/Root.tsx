import React from "react";
import { AbsoluteFill, Series } from "remotion";
import { IntroCard } from "./scenes/IntroCard";
import { TerminalRun } from "./scenes/TerminalRun";
import { IdleCutCard } from "./scenes/IdleCutCard";
import { OutroCard } from "./scenes/OutroCard";
import { Captions, Transcript } from "./scenes/Captions";
import timing from "./source/timing.json";
import transcript from "./source/transcript.json";

const SLUG = "golden-cut";
const frameTimesS = timing.frame_times_s as number[];

// Beat layout (output frames). Derived from the cast gaps in timing.json:
//   speedramp 2.1s→5.8s, cut 6.2s→15.0s.
export const BEATS = {
  intro: 45,
  runA: 63, // realtime: cast 0.0 → 2.1
  ramp: 28, // speedramp gap 2.1 → 5.8 at 4x → ~3.7s/4*30
  runC: 12, // realtime: cast 5.8 → 6.2
  cut: 30, // "…" card for the long cut gap
  runE: 12, // realtime: cast 15.0 → 15.4
  outro: 60,
};

// Narration begins when the content starts (after the intro card).
export const TRANSCRIPT_START_FRAME = BEATS.intro;

export const GoldenCut: React.FC = () => {
  return (
    <AbsoluteFill>
      <Series>
        <Series.Sequence durationInFrames={BEATS.intro}>
          <IntroCard title="golden cut" />
        </Series.Sequence>
        <Series.Sequence durationInFrames={BEATS.runA}>
          <TerminalRun slug={SLUG} frameTimesS={frameTimesS} beatStartS={0.0} factor={1} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={BEATS.ramp}>
          <TerminalRun slug={SLUG} frameTimesS={frameTimesS} beatStartS={2.1} factor={4} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={BEATS.runC}>
          <TerminalRun slug={SLUG} frameTimesS={frameTimesS} beatStartS={5.8} factor={1} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={BEATS.cut}>
          <IdleCutCard />
        </Series.Sequence>
        <Series.Sequence durationInFrames={BEATS.runE}>
          <TerminalRun slug={SLUG} frameTimesS={frameTimesS} beatStartS={15.0} factor={1} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={BEATS.outro}>
          <OutroCard />
        </Series.Sequence>
      </Series>
      <Captions
        transcript={transcript as Transcript}
        style="band"
        transcriptStartFrame={TRANSCRIPT_START_FRAME}
      />
    </AbsoluteFill>
  );
};
