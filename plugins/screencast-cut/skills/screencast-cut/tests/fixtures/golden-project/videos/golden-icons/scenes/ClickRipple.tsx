import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { makeCircle } from "@remotion/shapes";
import { animationPhase, rippleGeometry } from "./timing";

// The beachhead primitive: an animated ripple centered on a click anchor. It
// needs no icon set — just `@remotion/shapes` `makeCircle` driven by the
// `rippleGeometry` twin — so it is the cheapest motion primitive that proves the
// whole pattern end-to-end on the MP4 zoom path. `x`/`y` are the normalized
// anchor coordinates straight out of `zoom_anchors.json`.
export interface ClickRippleProps {
  /** Normalized click position within the frame, 0..1 (from zoom_anchors.json). */
  x: number;
  y: number;
  /** Brand accent; the ring stroke color. */
  color?: string;
  startFrame?: number;
  durationInFrames?: number;
  maxRadius?: number;
  strokeWidth?: number;
  /** Concentric rings, each staggered later than the last. */
  rings?: number;
}

export const ClickRipple: React.FC<ClickRippleProps> = ({
  x,
  y,
  color = "currentColor",
  startFrame = 0,
  durationInFrames = 30,
  maxRadius = 120,
  strokeWidth = 4,
  rings = 2,
}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      {Array.from({ length: rings }).map((_, i) => {
        const delay = Math.round((i / rings) * durationInFrames * 0.5);
        const progress = animationPhase(frame, startFrame + delay, durationInFrames);
        const { radius, opacity } = rippleGeometry(progress, maxRadius);
        // makeCircle is centered on the origin; a symmetric viewBox keeps it so.
        const circle = makeCircle({ radius: Math.max(0.001, radius) });
        return (
          <svg
            key={i}
            width={radius * 2}
            height={radius * 2}
            viewBox={`${-radius} ${-radius} ${radius * 2} ${radius * 2}`}
            style={{
              position: "absolute",
              left: `${x * 100}%`,
              top: `${y * 100}%`,
              transform: "translate(-50%, -50%)",
              overflow: "visible",
              opacity,
            }}
          >
            <path
              d={circle.path}
              fill="none"
              stroke={color}
              strokeWidth={strokeWidth}
            />
          </svg>
        );
      })}
    </AbsoluteFill>
  );
};
