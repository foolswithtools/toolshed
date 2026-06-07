// ZoomedSection — plays the screen-capture MP4 with an auto-zoom on one click
// anchor.
//
// REFERENCE SCENE. Copied into `videos/<slug>/scenes/` at Phase 4 and adapted.
// The zoom-window clamp is imported from `./timing` (clampZoomWindow), the
// tested twin of `scripts/timing_math.py`. DO NOT re-derive the clamp inline.
//
// One ZoomedSection wraps ONE zoom segment (300ms ramp-in, 1.5s hold, 400ms
// ramp-out by default). For multiple clicks, mount one per segment in Root.tsx;
// adjacent clicks the skill merged into a pan become a single segment with two
// anchors (extend this to interpolate the centre between them).
//
// Geometry: with transform-origin at the top-left, the transform
//   translate(Tx, Ty) scale(s)
// maps element point (px, py) -> screen (Tx + s*px, Ty + s*py). To land the
// clamped click centre (cx*W, cy*H) at the viewport centre (W/2, H/2):
//   Tx = W * (0.5 - s*cx),  Ty = H * (0.5 - s*cy).
// At s=1, cx=cy=0.5 this is a no-op, so the un-zoomed video is untouched.

import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { clampZoomWindow } from "./timing";
import { SafeStaticVideo } from "./SafeVideo";
import { palette, easings } from "../../../src/brand/active";

export type ZoomAnchor = { t_s: number; x: number; y: number; label?: string | null };

export type ZoomedSectionProps = {
  /** Video slug — builds the public/<slug>/source.mp4 path. */
  slug: string;
  /** Click anchor (normalized 0..1, top-left origin). */
  anchor: ZoomAnchor;
  /** Peak zoom (config `zoom_factor`, default 1.6). */
  zoomFactor?: number;
  /** Output frame of the click (anchor.t_s mapped to the output timeline). */
  anchorFrame: number;
  rampInFrames?: number;
  holdFrames?: number;
  rampOutFrames?: number;
  /** OffthreadVideo startFrom (frames into the source MP4). */
  videoStartFromFrame?: number;
  /** Source MP4 filename under public/<slug>/ (default source.mp4). */
  videoFile?: string;
};

export const ZoomedSection: React.FC<ZoomedSectionProps> = ({
  slug,
  anchor,
  zoomFactor = 1.6,
  anchorFrame,
  rampInFrames = 9, // ~300ms @ 30fps
  holdFrames = 45, // ~1.5s @ 30fps
  rampOutFrames = 12, // ~400ms @ 30fps
  videoStartFromFrame = 0,
  videoFile = "source.mp4",
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  // Clamp the zoom centre so the visible window stays inside the frame.
  const [cx, cy] = clampZoomWindow(anchor.x, anchor.y, zoomFactor);

  // scale: 1 -> zoomFactor (ramp in) -> hold -> 1 (ramp out), eased.
  const inStart = anchorFrame - rampInFrames;
  const holdEnd = anchorFrame + holdFrames;
  const outEnd = holdEnd + rampOutFrames;
  const scale = interpolate(
    frame,
    [inStart, anchorFrame, holdEnd, outEnd],
    [1, zoomFactor, zoomFactor, 1],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: easings.camera,
    },
  );

  const tx = width * (0.5 - scale * cx);
  const ty = height * (0.5 - scale * cy);

  return (
    <AbsoluteFill style={{ backgroundColor: palette.bg, overflow: "hidden" }}>
      <AbsoluteFill
        style={{
          transform: `translate(${tx}px, ${ty}px) scale(${scale})`,
          transformOrigin: "0 0",
        }}
      >
        <SafeStaticVideo
          path={`${slug}/${videoFile}`}
          startFrom={videoStartFromFrame}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
