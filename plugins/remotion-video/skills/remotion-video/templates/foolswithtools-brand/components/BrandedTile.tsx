import type { ReactNode } from "react";
import { palette, fonts, sizes } from "../style-guide";
import { BentoTile } from "./BentoTile";
import { HalftoneOverlay } from "./HalftoneOverlay";

type HalftonePosition = "corner-tl" | "corner-tr" | "corner-bl" | "corner-br";

type Props = {
  // Display heading rendered prominently inside the tile (Archivo Black, uppercase).
  title?: string;
  // Halftone dot color. Falls back to HalftoneOverlay's default (acid green).
  accent?: string;
  // Which corner the halftone clips into.
  halftonePosition: HalftonePosition;
  // Optional body content rendered below the title.
  children?: ReactNode;
  // Forwarded to BentoTile for beat-cycle border accents.
  beatIndex?: number;
};

export const BrandedTile: React.FC<Props> = ({
  title,
  accent,
  halftonePosition,
  children,
  beatIndex,
}) => {
  return (
    <div
      style={{
        position: "relative",
        overflow: "hidden",
        borderRadius: 24,
      }}
    >
      <BentoTile size="md" beatIndex={beatIndex}>
        {title ? (
          <div
            style={{
              fontFamily: fonts.display,
              fontWeight: 900,
              fontSize: sizes.caption,
              color: palette.text,
              textTransform: "uppercase",
              letterSpacing: "-0.02em",
              lineHeight: 1.0,
              minHeight: 56,
            }}
          >
            {title}
          </div>
        ) : null}
        {children}
      </BentoTile>
      <HalftoneOverlay
        color={accent}
        density="normal"
        opacity={0.5}
        position={halftonePosition}
        size={140}
      />
    </div>
  );
};
