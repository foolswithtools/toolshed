// SafeVideo / SafeAudio — asset wrappers with the cancelRender convention.
//
//   SafeVideo  — VISUAL asset. A missing/broken MP4 calls cancelRender(), so a
//                bad path fails the render deterministically instead of showing
//                a black frame the verify pass might miss.
//   SafeAudio  — AUDIO asset. A missing voiceover only WARNS (console.warn) and
//                renders silently. A render should still ship without narration;
//                losing audio is a soft failure, not a hard one.
//
// Use SafeVideo for the screen-capture MP4 in the ZoomedSection / ScreenPlayback
// path. Use SafeAudio for the voiceover track.

import React from "react";
import { OffthreadVideo, Audio, cancelRender, staticFile } from "remotion";

export const SafeVideo: React.FC<
  React.ComponentProps<typeof OffthreadVideo> & { src: string }
> = ({ src, ...rest }) => {
  return (
    <OffthreadVideo
      src={src}
      onError={(e) => {
        cancelRender(
          new Error(
            `SafeVideo: failed to load visual asset "${src}". ` +
              `Check that the MP4 was copied into public/ and the staticFile() ` +
              `path matches. Underlying error: ${String(e)}`,
          ),
        );
      }}
      {...rest}
    />
  );
};

export const SafeAudio: React.FC<
  React.ComponentProps<typeof Audio> & { src: string }
> = ({ src, ...rest }) => {
  return (
    <Audio
      src={src}
      onError={(e) => {
        // Warn-only: a missing voiceover should not kill the render.
        // eslint-disable-next-line no-console
        console.warn(
          `SafeAudio: failed to load audio asset "${src}" — rendering silent. ` +
            `Underlying error: ${String(e)}`,
        );
      }}
      {...rest}
    />
  );
};

export const SafeStaticVideo: React.FC<
  Omit<React.ComponentProps<typeof OffthreadVideo>, "src"> & { path: string }
> = ({ path, ...rest }) => <SafeVideo src={staticFile(path)} {...rest} />;

export const SafeStaticAudio: React.FC<
  Omit<React.ComponentProps<typeof Audio>, "src"> & { path: string }
> = ({ path, ...rest }) => <SafeAudio src={staticFile(path)} {...rest} />;
