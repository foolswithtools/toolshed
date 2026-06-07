// SafeImg — an <Img> that turns a missing/broken VISUAL asset into a
// deterministic render failure instead of a silent black frame.
//
// Why this exists: screencast cuts reference dozens of `staticFile()` PNGs
// (the terminal frame sequence). If one is missing, plain <Img> renders an
// empty frame — which a verify pass might wave through as "looks fine-ish".
// Calling cancelRender() in onError converts that into a hard `renderStill`
// failure that the verify loop's deterministic gates catch every time.
//
// Use this for every frame/PNG/image asset in a generated scene. For audio,
// use SafeAudio (warn-only — a missing voiceover should not kill the render).

import React from "react";
import { Img, cancelRender, staticFile } from "remotion";

export const SafeImg: React.FC<
  React.ComponentProps<typeof Img> & { src: string }
> = ({ src, ...rest }) => {
  return (
    <Img
      src={src}
      onError={(e) => {
        cancelRender(
          new Error(
            `SafeImg: failed to load visual asset "${src}". ` +
              `Check that the file was copied into public/ and the staticFile() ` +
              `path matches. Underlying error: ${String(e)}`,
          ),
        );
      }}
      {...rest}
    />
  );
};

// Convenience: build a SafeImg from a public-relative path via staticFile.
export const SafeStaticImg: React.FC<
  Omit<React.ComponentProps<typeof Img>, "src"> & { path: string }
> = ({ path, ...rest }) => <SafeImg src={staticFile(path)} {...rest} />;
