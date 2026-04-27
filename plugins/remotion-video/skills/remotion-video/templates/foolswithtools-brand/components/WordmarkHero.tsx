import { AbsoluteFill, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { palette, fonts, sizes, layout, springs } from "../style-guide";

type Props = {
  // Override the default wordmark, e.g. for video titles.
  word?: string;
  // When true, splits the wordmark into one word per line (mirrors the hero on
  // foolswith.tools). Default: false (one line).
  breakLines?: boolean;
  // Optional subtitle, e.g. "just empowered". Renders in `secondary` font,
  // lower-case (preserve), text dim color.
  tagline?: string;
  // Skip the uppercase transform for non-wordmark uses. Default: false.
  preserveCase?: boolean;
  // Horizontal alignment of the wordmark + tagline block.
  // - "left" (default): canonical foolswith.tools hero treatment, flush-left.
  // - "center": product-reveal Apple-pace treatment, centered both axes.
  align?: "left" | "center";
};

export const WordmarkHero: React.FC<Props> = ({
  word = "FOOLS WITH TOOLS",
  breakLines = false,
  tagline,
  preserveCase = false,
  align = "left",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Lines: either one full string or split into words.
  const lines = breakLines ? word.split(/\s+/) : [word];
  const isCentered = align === "center";

  return (
    <AbsoluteFill
      style={{
        backgroundColor: palette.bg,
        padding: layout.safePadding,
        flexDirection: "column",
        justifyContent: "center",
        alignItems: isCentered ? "center" : "flex-start",
        textAlign: isCentered ? "center" : "left",
      }}
    >
      {lines.map((line, i) => {
        const lineAppear = spring({
          frame: frame - i * 4,
          fps,
          config: springs.pop,
        });
        return (
          <div
            key={`${i}-${line}`}
            style={{
              fontFamily: fonts.display,
              fontWeight: 900,
              fontSize: sizes.hero,
              color: palette.text,
              textTransform: preserveCase ? "none" : "uppercase",
              letterSpacing: "-0.02em",
              lineHeight: 0.95,
              opacity: lineAppear,
              transform: `translateY(${(1 - lineAppear) * 24}px)`,
            }}
          >
            {line}
          </div>
        );
      })}
      {tagline ? (
        (() => {
          const taglineAppear = spring({
            frame: frame - (lines.length - 1) * 4 - 8,
            fps,
            config: springs.appear,
          });
          return (
            <div
              style={{
                marginTop: layout.gap,
                fontFamily: fonts.secondary,
                fontWeight: 500,
                fontSize: sizes.subtitle,
                color: palette.textDim,
                letterSpacing: "-0.01em",
                opacity: taglineAppear,
                transform: `translateY(${(1 - taglineAppear) * 16}px)`,
              }}
            >
              {tagline}
            </div>
          );
        })()
      ) : null}
    </AbsoluteFill>
  );
};
