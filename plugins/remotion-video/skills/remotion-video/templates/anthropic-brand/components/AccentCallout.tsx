import { useCurrentFrame, spring, useVideoConfig } from "remotion";
import {
  palette,
  fonts,
  sizes,
  radii,
  layout,
  springs,
  accentForBeat,
} from "../style-guide";

type Props = {
  text: string;
  // Beat index in the video. Drives accent cycle (0 → orange, 1 → blue, 2 → green, ...).
  beatIndex: number;
};

export const AccentCallout: React.FC<Props> = ({ text, beatIndex }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const accent = accentForBeat(beatIndex);

  const appear = spring({ frame, fps, config: springs.pop });

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 16,
        padding: `${layout.cardPadding / 4}px ${layout.cardPadding / 2}px`,
        borderRadius: radii.pill,
        backgroundColor: palette.bg,
        border: `2px solid ${accent}`,
        opacity: appear,
        transform: `scale(${0.92 + appear * 0.08})`,
      }}
    >
      <span
        style={{
          width: 14,
          height: 14,
          borderRadius: radii.pill,
          backgroundColor: accent,
          display: "inline-block",
        }}
      />
      <span
        style={{
          fontFamily: fonts.display,
          fontWeight: 500,
          fontSize: sizes.body,
          color: palette.text,
          letterSpacing: -0.2,
        }}
      >
        {text}
      </span>
    </div>
  );
};
