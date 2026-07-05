// LayeredParallaxScene — the signature component of the `paper-craft` profile.
//
// Takes an ordered list of paper layers (far background first, closest
// foreground last) and produces a living diorama: a slow camera push-in,
// depth-scaled parallax (nearer layers grow faster than distant ones), and
// per-layer idle motion (sway / bob) so the paper never sits dead still.
//
// Each layer's `render` can be inline SVG (see PaperPrimitives) OR a
// <SafeImg src={staticFile("layers/cat.png")} /> pointing at a generated
// paper-craft PNG — the rig treats both identically. Generate the art upstream,
// hand the layers here, get motion for free. See BRAND.md for the pipeline.

import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from "remotion";
import { fonts, easings, springs, palette, paper } from "../style-guide";

export type IdleMotion = {
  swayPx?: number; // horizontal drift amplitude, px
  bobPx?: number; // vertical drift amplitude, px
  swayDeg?: number; // gentle rotation amplitude, degrees
  periodInFrames?: number; // one full oscillation
  phase?: number; // 0..1 offset so layers don't move in lockstep
};

export type ParallaxLayer = {
  id: string;
  // 0 = infinitely far (barely moves), 1 = right at the lens (moves most).
  depth: number;
  render: React.ReactNode;
  idle?: IdleMotion;
};

const idleTransform = (frame: number, idle?: IdleMotion): string => {
  if (!idle) return "";
  const period = idle.periodInFrames ?? 120;
  const t = (frame / period + (idle.phase ?? 0)) * Math.PI * 2;
  const sway = (idle.swayPx ?? 0) * Math.sin(t);
  const bob = (idle.bobPx ?? 0) * Math.sin(t * 0.9 + 0.6);
  const rot = (idle.swayDeg ?? 0) * Math.sin(t);
  return `translate(${sway}px, ${bob}px) rotate(${rot}deg)`;
};

export const LayeredParallaxScene: React.FC<{
  layers: ParallaxLayer[];
  title?: string;
  bg?: string;
  // How aggressive the push-in is. 0.12 => zooms to 112% by the end.
  zoomAmount?: number;
  panPx?: number; // horizontal camera drift across the whole scene, px
}> = ({ layers, title, bg = palette.bg, zoomAmount = 0.12, panPx = 40 }) => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();

  // Camera: ease a slow push-in and a touch of lateral drift across the scene.
  const zoom = interpolate(frame, [0, durationInFrames], [1, 1 + zoomAmount], {
    easing: easings.camera,
    extrapolateRight: "clamp",
  });
  const pan = interpolate(frame, [0, durationInFrames], [0, panPx], {
    easing: easings.camera,
    extrapolateRight: "clamp",
  });

  // Title springs in and lifts slightly, like a cut-paper card being placed.
  const titleIn = spring({ frame: frame - 8, fps, config: springs.pop });

  return (
    <AbsoluteFill style={{ backgroundColor: bg, overflow: "hidden" }}>
      {layers.map((layer) => {
        // Nearer layers take more of the zoom and more of the pan → depth.
        const layerZoom = 1 + (zoom - 1) * (0.35 + 0.65 * layer.depth);
        const layerPan = -pan * layer.depth;
        return (
          <AbsoluteFill
            key={layer.id}
            style={{
              transform: `translateX(${layerPan}px) scale(${layerZoom})`,
              transformOrigin: "50% 62%", // push toward the horizon/glow
              willChange: "transform",
            }}
          >
            <AbsoluteFill style={{ transform: idleTransform(frame, layer.idle) }}>
              {layer.render}
            </AbsoluteFill>
          </AbsoluteFill>
        );
      })}

      {title ? (
        <AbsoluteFill
          style={{
            justifyContent: "flex-start",
            alignItems: "center",
            paddingTop: 70,
          }}
        >
          <div
            style={{
              fontFamily: fonts.display,
              fontWeight: 900,
              fontSize: 150,
              letterSpacing: 4,
              color: paper.titleFill,
              textShadow: paper.titleShadow,
              opacity: titleIn,
              transform: `translateY(${interpolate(titleIn, [0, 1], [40, 0])}px)`,
            }}
          >
            {title}
          </div>
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};
