// Captions — word-timed captions from transcript.json.
//
// REFERENCE SCENE. Copied into `videos/<slug>/scenes/` at Phase 4 and adapted.
// Word -> output-frame mapping is imported from `./timing` (captionWordToFrame),
// the tested twin of `scripts/timing_math.py`. DO NOT inline the * fps math.
//
// Two styles (resolved from the playbook in Phase 2, not raw config):
//   "band"     — a clean two-line caption bar; the whole active segment shows,
//                tutorial default (16:9).
//   "karaoke"  — per-word reveal: the active word is highlighted in the brand
//                accent against dimmer siblings, shortform default (9:16).
//
// This component is mounted for the FULL composition duration (it is its own
// layer over the terminal/video), so it reads absolute output frames and
// decides what to show. `transcriptStartFrame` lets you offset the transcript
// if narration starts after an intro card.

import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { captionWordToFrame } from "./timing";
import { palette, fonts, sizes } from "../../../src/brand/active";

export type Word = { start_s: number | null; end_s: number | null; text: string };
export type Segment = {
  start_s: number | null;
  end_s: number | null;
  text: string;
  words: Word[];
};
export type Transcript = { segments: Segment[] };

export type CaptionsProps = {
  transcript: Transcript;
  style?: "band" | "karaoke";
  /** Output frame at which the narration (transcript t=0) begins. */
  transcriptStartFrame?: number;
};

type TimedWord = Word & { startFrame: number; endFrame: number; segIndex: number };

export const Captions: React.FC<CaptionsProps> = ({
  transcript,
  style = "band",
  transcriptStartFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Flatten to timed words once, mapping each word's start to an output frame
  // through the shared helper.
  const words: TimedWord[] = [];
  transcript.segments.forEach((seg, segIndex) => {
    seg.words.forEach((w) => {
      if (w.start_s == null) return;
      const startFrame =
        transcriptStartFrame + captionWordToFrame(w.start_s, fps);
      const endFrame =
        w.end_s != null
          ? transcriptStartFrame + captionWordToFrame(w.end_s, fps)
          : startFrame + Math.round(fps * 0.4);
      words.push({ ...w, startFrame, endFrame, segIndex });
    });
  });

  // Active word = last word whose startFrame <= current frame, within its window.
  let activeIdx = -1;
  for (let i = 0; i < words.length; i++) {
    if (words[i].startFrame <= frame) activeIdx = i;
    else break;
  }
  if (activeIdx < 0) return null;
  const active = words[activeIdx];
  // Hide once we are well past the last word of the segment (no narration).
  const segWords = words.filter((w) => w.segIndex === active.segIndex);
  const segEnd = segWords[segWords.length - 1].endFrame + Math.round(fps * 0.6);
  if (frame > segEnd) return null;

  const barStyle: React.CSSProperties = {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: "8%",
    display: "flex",
    justifyContent: "center",
    padding: "0 6%",
  };

  if (style === "karaoke") {
    return (
      <AbsoluteFill>
        <div style={barStyle}>
          <div
            style={{
              fontFamily: fonts.display,
              fontSize: sizes.title,
              fontWeight: 800,
              lineHeight: 1.1,
              textAlign: "center",
              textShadow: "0 4px 24px rgba(0,0,0,0.7)",
            }}
          >
            {segWords.map((w, i) => {
              const isActive = w.startFrame <= frame && frame <= w.endFrame;
              const isPast = frame > w.endFrame;
              return (
                <span
                  key={i}
                  style={{
                    color: isActive
                      ? palette.accent
                      : isPast
                        ? palette.text
                        : palette.textDim,
                    marginRight: "0.3em",
                  }}
                >
                  {w.text}
                </span>
              );
            })}
          </div>
        </div>
      </AbsoluteFill>
    );
  }

  // "band": the whole active segment in a clean caption bar.
  const segText = transcript.segments[active.segIndex].text.trim();
  return (
    <AbsoluteFill>
      <div style={barStyle}>
        <div
          style={{
            maxWidth: "80%",
            background: "rgba(0,0,0,0.62)",
            borderRadius: 16,
            padding: "18px 32px",
            fontFamily: fonts.body,
            fontSize: sizes.subtitle,
            fontWeight: 600,
            lineHeight: 1.25,
            color: palette.text,
            textAlign: "center",
          }}
        >
          {segText}
        </div>
      </div>
    </AbsoluteFill>
  );
};
