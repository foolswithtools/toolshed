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
  // Appends a blinking cursor at the end. Default: false.
  showCursor?: boolean;
  // When provided, replaces acid green with accentForBeat for both border and
  // text. Default uses acid green always.
  beatIndex?: number;
};

export const TerminalChip: React.FC<Props> = ({
  text,
  showCursor = false,
  beatIndex,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const accent =
    beatIndex !== undefined ? accentForBeat(beatIndex) : palette.accentAcid;

  // Pop-in with slight overshoot.
  const appear = spring({ frame, fps, config: springs.pop });
  const scale = 0.85 + appear * 0.18;

  // Caret blink (8 frames on / 8 frames off).
  const caretOn = frame % 16 < 8;

  // Soft glow at ~30% intensity — subtler than a neon halo. We achieve the
  // intensity dial by attenuating the spread/blur in the box-shadow rather
  // than by mixing alpha into the color (which would require parsing).
  const softGlow = `0 0 18px ${accent}, 0 0 6px ${accent}`;

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        padding: "12px 20px",
        borderRadius: radii.md,
        backgroundColor: palette.terminalBg,
        border: `${layout.borderWidth}px solid ${accent}`,
        boxShadow: softGlow,
        opacity: Math.min(1, appear),
        transform: `scale(${scale})`,
      }}
    >
      <span
        style={{
          fontFamily: fonts.mono,
          fontSize: sizes.body,
          color: accent,
          letterSpacing: 0,
          lineHeight: 1,
          whiteSpace: "pre",
        }}
      >
        {text}
        {showCursor ? (
          <span
            style={{
              display: "inline-block",
              width: "0.6em",
              marginLeft: 4,
              color: accent,
              opacity: caretOn ? 1 : 0,
            }}
          >
            █
          </span>
        ) : null}
      </span>
    </div>
  );
};
