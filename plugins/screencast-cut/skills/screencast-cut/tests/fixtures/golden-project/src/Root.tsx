import React from "react";
import { Composition } from "remotion";
import { GoldenCut } from "../videos/golden-cut/Root";
import { GoldenCutMp4 } from "../videos/golden-cut-mp4/Root";
import { GoldenIcons, GOLDEN_ICONS_DURATION } from "../videos/golden-icons/Root";
import {
  MotionProbe,
  MOTION_PROBES,
  PROBE_DURATION,
} from "../videos/golden-icons/MotionProbe";
import { computeMasterDuration } from "../videos/golden-cut/scenes/timing";

const FPS = 30;
const WIDTH = 1920;
const HEIGHT = 1080;

// Durations are computed with the SAME tested helper the scenes use — no
// hand-added frame counts. golden-cut beats: intro 45, runA 63, ramp 28,
// runC 12, cut 30, runE 12, outro 60 → 250 (no transitions).
export const GOLDEN_CUT_DURATION = computeMasterDuration(
  [45, 63, 28, 12, 30, 12, 60],
  0,
);
// golden-cut-mp4 beats: intro 45, zoom 90, outro 60 → 195.
export const GOLDEN_CUT_MP4_DURATION = computeMasterDuration([45, 90, 60], 0);

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="golden-cut"
        component={GoldenCut}
        durationInFrames={GOLDEN_CUT_DURATION}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
      />
      <Composition
        id="golden-cut-mp4"
        component={GoldenCutMp4}
        durationInFrames={GOLDEN_CUT_MP4_DURATION}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
      />
      <Composition
        id="golden-icons"
        component={GoldenIcons}
        durationInFrames={GOLDEN_ICONS_DURATION}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
      />
      {/* Per-recipe motion-probe compositions (one primitive each, no Loop) for
          the deterministic motion assertion in tests/test_icons_motion.py. */}
      {MOTION_PROBES.map((p) => (
        <Composition
          key={p.id}
          id={p.id}
          component={MotionProbe}
          defaultProps={p.props}
          durationInFrames={PROBE_DURATION}
          fps={FPS}
          width={WIDTH}
          height={HEIGHT}
        />
      ))}
    </>
  );
};
