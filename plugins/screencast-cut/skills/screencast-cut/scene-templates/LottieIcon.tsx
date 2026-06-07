import React, { useEffect, useState } from "react";
import {
  cancelRender,
  continueRender,
  delayRender,
  staticFile,
} from "remotion";
import { Lottie, type LottieAnimationData } from "@remotion/lottie";

// BRING-YOUR-OWN Lottie hatch (Phase 2). Lottie is a SECOND-CLASS citizen beside
// the SVG recipe engine: it cannot be cleanly theme-recolored and is only
// CONDITIONALLY frame-deterministic (After-Effects *expressions* read wall-clock
// state and flicker in headless renders). So it sits next to the SVG system, not
// inside it, and the rules around it are strict:
//
//   - We NEVER bundle or redistribute a third-party Lottie JSON. The only Lottie
//     committed to this repo is one we AUTHORED ourselves (or a CC0 file), with
//     a provenance note. A user's own file is read from THEIR path at render
//     time — see `src` below.
//   - Before using a BYO file, vet it with `scripts/lottie_ingest.py` (rejects
//     expression-driven files, best-effort recolors flat fills). The component
//     assumes a vetted, expression-free file.
//
// Determinism: `<Lottie>` maps `useCurrentFrame()` to a Lottie frame, so an
// expression-free file renders bit-identically every pass.
export interface LottieIconProps {
  /**
   * Pre-loaded animation data. Preferred for an in-repo authored/CC0 fixture:
   * no fetch, no delayRender, fully deterministic.
   */
  animationData?: LottieAnimationData;
  /**
   * OR a path to fetch at render time — the BYO escape hatch. A bare path is
   * resolved through `staticFile()` (served from the project's `public/`); an
   * `http(s)://` URL is fetched as-is. Loaded behind `delayRender`.
   */
  src?: string;
  loop?: boolean;
  playbackRate?: number;
  style?: React.CSSProperties;
}

export const LottieIcon: React.FC<LottieIconProps> = ({
  animationData,
  src,
  loop = true,
  playbackRate = 1,
  style,
}) => {
  const [data, setData] = useState<LottieAnimationData | null>(
    animationData ?? null,
  );
  // Only delay the render when we actually have to fetch.
  const [handle] = useState(() =>
    animationData || src == null ? null : delayRender("Loading BYO Lottie file"),
  );

  useEffect(() => {
    if (animationData || src == null || handle == null) return;
    const url = /^https?:\/\//.test(src) ? src : staticFile(src);
    fetch(url)
      .then((res) => {
        if (!res.ok) {
          throw new Error(
            `LottieIcon: failed to load "${src}" (HTTP ${res.status}). ` +
              `Check the file was copied into public/ and the path matches.`,
          );
        }
        return res.json();
      })
      .then((json: LottieAnimationData) => {
        setData(json);
        continueRender(handle);
      })
      .catch((err) => cancelRender(err));
  }, [animationData, src, handle]);

  if (!data) return null;
  return (
    <Lottie
      animationData={data}
      loop={loop}
      playbackRate={playbackRate}
      style={style}
    />
  );
};
