import { AbsoluteFill, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { palette, fonts, sizes, layout, springs } from "../style-guide";

type Props = {
  title: string;
  subtitle?: string;
};

export const TypeLedTitle: React.FC<Props> = ({ title, subtitle }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleIn = spring({ frame, fps, config: springs.appear });
  const subIn = spring({ frame: frame - 10, fps, config: springs.appear });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: palette.bg,
        padding: layout.safePadding,
        flexDirection: "column",
        justifyContent: "center",
        gap: layout.gap,
      }}
    >
      <div
        style={{
          fontFamily: fonts.display,
          fontWeight: 600,
          fontSize: sizes.title,
          color: palette.text,
          letterSpacing: -1,
          lineHeight: 1.05,
          opacity: titleIn,
          transform: `translateY(${(1 - titleIn) * 18}px)`,
          maxWidth: "75%",
        }}
      >
        {title}
      </div>
      {subtitle ? (
        <div
          style={{
            fontFamily: fonts.body,
            fontSize: sizes.subtitle,
            color: palette.textMuted,
            lineHeight: 1.3,
            opacity: subIn,
            transform: `translateY(${(1 - subIn) * 12}px)`,
            maxWidth: "70%",
          }}
        >
          {subtitle}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
