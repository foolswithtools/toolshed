import { useCurrentFrame, interpolate } from "remotion";
import { palette, easings } from "../style-guide";

type Position = "corner-tl" | "corner-tr" | "corner-bl" | "corner-br" | "fill";
type Density = "sparse" | "normal" | "dense";

type Props = {
  // Dot color. Default: palette.accentAcid.
  color?: string;
  // Dot spacing. Default: 'normal'.
  density?: Density;
  // Overall layer opacity. Default: 0.18.
  opacity?: number;
  // Where to mount it. Default: 'corner-br'.
  position?: Position;
  // Pixel dimensions if not 'fill'. Default: 600.
  size?: number;
};

const DENSITY_PX: Record<Density, number> = {
  sparse: 24,
  normal: 16,
  dense: 10,
};

export const HalftoneOverlay: React.FC<Props> = ({
  color = palette.accentAcid,
  density = "normal",
  opacity = 0.18,
  position = "corner-br",
  size = 600,
}) => {
  const frame = useCurrentFrame();

  // Subtle drift over the scene (~8px) in a corner-appropriate direction.
  // We assume scenes are ~80–120 frames; ease across 120.
  const drift = interpolate(frame, [0, 120], [0, 8], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easings.softInOut,
  });

  // Compute mount + drift direction per position.
  let mount: React.CSSProperties = {};
  let dx = 0;
  let dy = 0;
  switch (position) {
    case "corner-tl":
      mount = { top: 0, left: 0 };
      dx = -drift;
      dy = -drift;
      break;
    case "corner-tr":
      mount = { top: 0, right: 0 };
      dx = drift;
      dy = -drift;
      break;
    case "corner-bl":
      mount = { bottom: 0, left: 0 };
      dx = -drift;
      dy = drift;
      break;
    case "corner-br":
      mount = { bottom: 0, right: 0 };
      dx = drift;
      dy = drift;
      break;
    case "fill":
      mount = { top: 0, left: 0, right: 0, bottom: 0 };
      dx = drift;
      dy = drift;
      break;
  }

  const dotSpacing = DENSITY_PX[density];

  const layerSize: React.CSSProperties =
    position === "fill"
      ? { top: 0, left: 0, right: 0, bottom: 0 }
      : { width: size, height: size };

  return (
    <div
      style={{
        position: "absolute",
        ...mount,
        ...layerSize,
        opacity,
        backgroundImage: `radial-gradient(circle at center, ${color} 1.5px, transparent 2px)`,
        backgroundSize: `${dotSpacing}px ${dotSpacing}px`,
        transform: `translate(${dx}px, ${dy}px)`,
        pointerEvents: "none",
      }}
    />
  );
};
