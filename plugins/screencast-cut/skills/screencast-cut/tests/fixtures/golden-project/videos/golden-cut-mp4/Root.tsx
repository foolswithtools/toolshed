import React from "react";
import { AbsoluteFill, Series } from "remotion";
import { IntroCard } from "./scenes/IntroCard";
import { OutroCard } from "./scenes/OutroCard";
import { ZoomedSection } from "./scenes/ZoomedSection";
import zoom from "./source/zoom_anchors.json";

const SLUG = "golden-cut-mp4";
const anchor = zoom.anchors[0];

export const BEATS_MP4 = { intro: 45, zoom: 90, outro: 60 };

export const GoldenCutMp4: React.FC = () => {
  return (
    <AbsoluteFill>
      <Series>
        <Series.Sequence durationInFrames={BEATS_MP4.intro}>
          <IntroCard title="zoom demo" />
        </Series.Sequence>
        <Series.Sequence durationInFrames={BEATS_MP4.zoom}>
          <ZoomedSection
            slug={SLUG}
            anchor={anchor}
            zoomFactor={1.6}
            anchorFrame={45}
            rampInFrames={9}
            holdFrames={45}
            rampOutFrames={12}
            videoStartFromFrame={0}
          />
        </Series.Sequence>
        <Series.Sequence durationInFrames={BEATS_MP4.outro}>
          <OutroCard text="done" />
        </Series.Sequence>
      </Series>
    </AbsoluteFill>
  );
};
