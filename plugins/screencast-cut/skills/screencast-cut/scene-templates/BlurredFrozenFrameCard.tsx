// BlurredFrozenFrameCard — the idle-CUT placeholder for screen recordings
// (Slice C). Where a terminal cut shows the "…" IdleCutCard, a video cut holds a
// BLURRED FROZEN FRAME of the recording with a "skipped ahead" hint — the "…"
// card reads as wrong over a screen-capture aesthetic.
//
// REFERENCE SCENE. Copied into `videos/<slug>/scenes/` at Phase 4 and adapted.
// Deterministic: <Freeze frame={freezeSourceFrame}> pins the OffthreadVideo
// (startFrom=0) to one source frame, so every render of this card shows the same
// static frame from inside the cut stretch.

import React from "react";
import { AbsoluteFill, Freeze } from "remotion";
import { SafeStaticVideo } from "./SafeVideo";
import { palette, fonts, sizes } from "../../../src/brand/active";

export type BlurredFrozenFrameCardProps = {
  /** Video slug — builds the public/<slug>/<videoFile> path. */
  slug: string;
  /** Source frame (composition fps) to freeze on — pick one inside the cut. */
  freezeSourceFrame: number;
  /** Blur radius in px. */
  blurPx?: number;
  /** Overlay hint text. */
  hint?: string;
  /** Source MP4 filename under public/<slug>/ (default source.mp4). */
  videoFile?: string;
};

export const BlurredFrozenFrameCard: React.FC<BlurredFrozenFrameCardProps> = ({
  slug,
  freezeSourceFrame,
  blurPx = 16,
  hint = "skipped ahead",
  videoFile = "source.mp4",
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: palette.bg, overflow: "hidden" }}>
      {/* scale(1.1) hides the blur's soft transparent edges. */}
      <AbsoluteFill style={{ filter: `blur(${blurPx}px)`, transform: "scale(1.1)" }}>
        <Freeze frame={freezeSourceFrame}>
          <SafeStaticVideo
            path={`${slug}/${videoFile}`}
            startFrom={0}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </Freeze>
      </AbsoluteFill>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 16,
            padding: "16px 32px",
            borderRadius: 999,
            background: "rgba(0,0,0,0.55)",
            color: palette.text,
            fontFamily: fonts.body,
            fontSize: sizes.subtitle,
            fontWeight: 600,
          }}
        >
          <span style={{ color: palette.accent }}>⏩</span>
          {hint}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
