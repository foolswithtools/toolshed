import React from "react";
import { AbsoluteFill, Series } from "remotion";
import { IntroCard } from "./scenes/IntroCard";
import { TerminalRun } from "./scenes/TerminalRun";
import { IdleCutCard } from "./scenes/IdleCutCard";
import { OutroCard } from "./scenes/OutroCard";
import { computeMasterDuration } from "./scenes/timing";
import timing from "./source/timing.json";

// Slice B golden path: a cast with a backspace fumble that gets CUT. The fumble
// region (source/timing.json `fumble_regions[0]`: cast 1.0s→3.6s) is approved
// and dropped exactly like an idle_cut — runA plays up to the mistype, an
// IdleCutCard stands in for the scrapped typing, then runB resumes on the
// corrected command.
const SLUG = "golden-fumble";
const frameTimesS = timing.frame_times_s as number[];

export const BEATS = {
  intro: 45,
  runA: 30, // realtime: cast 0.0 → 1.0 (prompt, before the fumble)
  fumbleCut: 30, // "…" card replacing the fumble stretch (cast 1.0 → 3.6)
  runB: 81, // realtime: cast 3.6 → 6.3 (corrected `echo hello` + output)
  outro: 60,
};

export const GOLDEN_FUMBLE_DURATION = computeMasterDuration(
  [BEATS.intro, BEATS.runA, BEATS.fumbleCut, BEATS.runB, BEATS.outro],
  0,
);

export const GoldenFumble: React.FC = () => {
  return (
    <AbsoluteFill>
      <Series>
        <Series.Sequence durationInFrames={BEATS.intro}>
          <IntroCard title="fumble cut" />
        </Series.Sequence>
        <Series.Sequence durationInFrames={BEATS.runA}>
          <TerminalRun slug={SLUG} frameTimesS={frameTimesS} beatStartS={0.0} factor={1} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={BEATS.fumbleCut}>
          <IdleCutCard />
        </Series.Sequence>
        <Series.Sequence durationInFrames={BEATS.runB}>
          <TerminalRun slug={SLUG} frameTimesS={frameTimesS} beatStartS={3.6} factor={1} />
        </Series.Sequence>
        <Series.Sequence durationInFrames={BEATS.outro}>
          <OutroCard />
        </Series.Sequence>
      </Series>
    </AbsoluteFill>
  );
};
