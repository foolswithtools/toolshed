import type { ReactNode } from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { palette, easings } from "../style-guide";

type Props = {
  children: ReactNode;
  // Default: palette.accentAcid.
  color?: string;
  // Stroke width in px. Default: 6.
  thickness?: number;
  // When in the parent Sequence to start drawing. Default: 4.
  delayFrames?: number;
  // How long the draw-on takes. Default: 12.
  drawDurationFrames?: number;
  // Pixel width of the underline. The caller passes this since we don't measure
  // children at render time.
  width: number;
};

export const ScribbleUnderline: React.FC<Props> = ({
  children,
  color = palette.accentAcid,
  thickness = 6,
  delayFrames = 4,
  drawDurationFrames = 12,
  width,
}) => {
  const frame = useCurrentFrame();

  // Build a slightly-wavy quadratic-bezier path so the line feels hand-drawn.
  // Two segments with small Y-jitter (~3px).
  const height = 14; // svg height — leaves room for stroke + jitter
  const baseline = height / 2;
  const jitter = 3;
  const startX = thickness / 2;
  const endX = width - thickness / 2;
  const midX = (startX + endX) / 2;
  // Control points pull slightly off the baseline for the marker feel.
  const cpY1 = baseline - jitter;
  const cpY2 = baseline + jitter;
  // Two segments: Q (up-bow) then a second Q via explicit control to dip down.
  const path = `M ${startX} ${baseline} Q ${(startX + midX) / 2} ${cpY1}, ${midX} ${baseline} Q ${(midX + endX) / 2} ${cpY2}, ${endX} ${baseline + 1}`;

  // Approximate path length — we use the chord length plus a fudge factor for
  // the bezier wiggle so dashoffset reveal looks correct without measuring.
  const pathLength = (endX - startX) * 1.06;

  const drawProgress = interpolate(
    frame,
    [delayFrames, delayFrames + drawDurationFrames],
    [0, 1],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: easings.scribble,
    },
  );
  const dashoffset = pathLength * (1 - drawProgress);

  return (
    <span
      style={{
        position: "relative",
        display: "inline-block",
      }}
    >
      {children}
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        style={{
          position: "absolute",
          left: 0,
          // Sit just below the text baseline.
          bottom: -height,
          pointerEvents: "none",
          overflow: "visible",
        }}
      >
        <path
          d={path}
          stroke={color}
          strokeWidth={thickness}
          strokeLinecap="round"
          fill="none"
          strokeDasharray={pathLength}
          strokeDashoffset={dashoffset}
        />
      </svg>
    </span>
  );
};
