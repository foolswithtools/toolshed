import React from "react";
import { AbsoluteFill, Series } from "remotion";
import { IntroCard } from "./scenes/IntroCard";
import { NarrationStage } from "./scenes/NarrationStage";
import { OutroCard } from "./scenes/OutroCard";
import { Captions, Transcript } from "./scenes/Captions";
import { computeMasterDuration } from "./scenes/timing";
import transcript from "./source/transcript.json";

// Slice A golden path: a cut whose narration came from a `Script:` input.
// script_to_audio.py turned source/script.md into the committed OWNED fixture
// public/golden-tts/narration.wav (see source/narration.manifest.json for the
// provenance). The render never calls ElevenLabs.
const SLUG = "golden-tts";

export const BEATS = {
  intro: 45,
  body: 150, // ~5s narration stage
  outro: 60,
};

// Computed with the SAME tested helper the scenes use — no hand-added counts.
export const GOLDEN_TTS_DURATION = computeMasterDuration(
  [BEATS.intro, BEATS.body, BEATS.outro],
  0,
);

// Narration (transcript t=0) begins when the content stage starts.
export const TRANSCRIPT_START_FRAME = BEATS.intro;

export const GoldenTts: React.FC = () => {
  return (
    <AbsoluteFill>
      <Series>
        <Series.Sequence durationInFrames={BEATS.intro}>
          <IntroCard title="from a script" />
        </Series.Sequence>
        <Series.Sequence durationInFrames={BEATS.body}>
          <NarrationStage slug={SLUG} />
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
