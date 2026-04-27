import type { ReactNode } from "react";
import { useCurrentFrame, spring, useVideoConfig } from "remotion";
import {
  palette,
  fonts,
  sizes,
  radii,
  layout,
  shadows,
  springs,
  accentForBeat,
} from "../style-guide";

type Props = {
  // Optional eyebrow title at top.
  title?: string;
  children: ReactNode;
  // Border accent override; defaults to palette.text (charcoal).
  accent?: string;
  // Controls radius and padding.
  size?: "md" | "lg";
  // When provided and accent is undefined, uses accentForBeat for the border.
  beatIndex?: number;
};

export const BentoTile: React.FC<Props> = ({
  title,
  children,
  accent,
  size = "lg",
  beatIndex,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const borderColor =
    accent ??
    (beatIndex !== undefined ? accentForBeat(beatIndex) : palette.text);

  const appear = spring({ frame, fps, config: springs.appear });
  const scale = 0.96 + appear * 0.04;

  const borderRadius = size === "lg" ? radii.xl : radii.lg;

  return (
    <div
      style={{
        backgroundColor: palette.bgElevated,
        border: `${layout.borderWidth}px solid ${borderColor}`,
        borderRadius,
        padding: layout.cardPadding,
        boxShadow: shadows.card,
        opacity: appear,
        transform: `scale(${scale})`,
        display: "flex",
        flexDirection: "column",
        gap: layout.gap / 2,
      }}
    >
      {title ? (
        <div
          style={{
            fontFamily: fonts.display,
            fontWeight: 900,
            fontSize: sizes.caption,
            color: palette.textMuted,
            textTransform: "uppercase",
            letterSpacing: "-0.02em",
            lineHeight: 0.95,
          }}
        >
          {title}
        </div>
      ) : null}
      <div
        style={{
          fontFamily: fonts.body,
          fontSize: sizes.body,
          color: palette.text,
          lineHeight: 1.4,
        }}
      >
        {children}
      </div>
    </div>
  );
};
