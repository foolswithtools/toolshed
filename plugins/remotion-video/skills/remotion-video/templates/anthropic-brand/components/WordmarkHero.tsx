import { AbsoluteFill, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { palette, fonts, sizes, layout, springs } from "../style-guide";

type Props = {
  word: string;
  subtitle?: string;
};

export const WordmarkHero: React.FC<Props> = ({ word, subtitle }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const appear = spring({ frame, fps, config: springs.appear });
  const subAppear = spring({
    frame: frame - 8,
    fps,
    config: springs.appear,
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: palette.bg,
        padding: layout.safePadding,
        justifyContent: "center",
        alignItems: "flex-start",
      }}
    >
      <div
        style={{
          fontFamily: fonts.display,
          fontWeight: 600,
          fontSize: sizes.hero,
          color: palette.text,
          letterSpacing: -2,
          lineHeight: 1.0,
          opacity: appear,
          transform: `translateY(${(1 - appear) * 24}px)`,
        }}
      >
        {word}
      </div>
      {subtitle ? (
        <div
          style={{
            marginTop: layout.gap,
            fontFamily: fonts.body,
            fontSize: sizes.subtitle,
            color: palette.textMuted,
            opacity: subAppear,
            transform: `translateY(${(1 - subAppear) * 16}px)`,
          }}
        >
          {subtitle}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
