import { useCurrentFrame, spring, interpolate, useVideoConfig } from "remotion";
import {
  palette,
  fonts,
  sizes,
  radii,
  springs,
  accentCycle,
  accentForBeat,
  gradients,
} from "../style-guide";

type Props = {
  text: string;
  // primary = filled gradient + glow. ghost = transparent with charcoal border.
  variant?: "primary" | "ghost";
  // When provided, recolors the gradient to use accentForBeat → next-cycle-color.
  beatIndex?: number;
  size?: "md" | "lg";
};

export const GummyButton: React.FC<Props> = ({
  text,
  variant = "primary",
  beatIndex,
  size = "lg",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const appear = spring({ frame, fps, config: springs.pop });
  const scale = 0.92 + appear * 0.08;

  // Glow grows from 0 to full over ~10 frames.
  const glowProgress = interpolate(frame, [0, 10], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Resolve gradient + glow color.
  const isBeatCycled = beatIndex !== undefined;
  const startColor = isBeatCycled
    ? accentForBeat(beatIndex)
    : palette.accentAcid;
  const endColor = isBeatCycled
    ? accentCycle[(beatIndex + 1) % accentCycle.length]
    : palette.accentBanana;
  const beatGradient = `linear-gradient(135deg, ${startColor} 0%, ${endColor} 100%)`;
  const useGradient = isBeatCycled ? beatGradient : gradients.acidToBanana;

  const padding = size === "lg" ? "20px 40px" : "14px 28px";
  const fontSize = size === "lg" ? sizes.body : sizes.caption;

  const isPrimary = variant === "primary";
  const background = isPrimary ? useGradient : "transparent";
  const border = isPrimary ? "none" : `2px solid ${palette.text}`;
  const glowColor = startColor;
  const boxShadow = isPrimary
    ? `0 ${8 * glowProgress}px ${32 * glowProgress}px ${glowColor}`
    : "none";

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        padding,
        borderRadius: radii.pill,
        background,
        border,
        boxShadow,
        opacity: appear,
        transform: `scale(${scale})`,
      }}
    >
      <span
        style={{
          fontFamily: fonts.secondary,
          fontWeight: 700,
          fontSize,
          color: palette.text,
          textTransform: "uppercase",
          letterSpacing: "-0.02em",
          lineHeight: 1,
        }}
      >
        {text}
      </span>
    </div>
  );
};
