import { Img, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { palette, springs } from "../style-guide";

type Props = {
  // Image path; pass `staticFile("...")` from caller.
  src: string;
  // Degrees. Default: -4 (slight left tilt). Pass 0 for no rotation.
  rotation?: number;
  // Diameter px. Default: 120.
  size?: number;
  // Sticker border. Default: palette.bg (cream — looks like cut-out paper).
  borderColor?: string;
  borderWidth?: number;
};

export const StickerAvatar: React.FC<Props> = ({
  src,
  rotation = -4,
  size = 120,
  borderColor = palette.bg,
  borderWidth = 4,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Pop-in with overshoot.
  const appear = spring({ frame, fps, config: springs.pop });
  const popScale = 0.85 + appear * 0.18;

  // Gentle rotational sway: ±0.5deg over 90 frames once settled.
  // Use a sine on currentFrame so it feels alive.
  const swayDeg = Math.sin((frame / 90) * Math.PI * 2) * 0.5;
  const totalRotation = rotation + swayDeg;

  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        overflow: "hidden",
        border: `${borderWidth}px solid ${borderColor}`,
        boxShadow:
          "0 4px 12px rgba(0,0,0,0.18), inset 0 1px 2px rgba(255,255,255,0.4)",
        opacity: Math.min(1, appear),
        transform: `rotate(${totalRotation}deg) scale(${popScale})`,
        // Make sure the rotation pivots around center.
        transformOrigin: "center center",
      }}
    >
      <Img
        src={src}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          display: "block",
        }}
      />
    </div>
  );
};
