// Pure timing/geometry math — the TypeScript twin of `scripts/timing_math.py`.
//
// These functions are the single source of truth for the fragile arithmetic
// that used to be re-derived freehand in every generated Remotion scene:
//
//   - mapping a cast/GIF timestamp to a PNG frame index,
//   - advancing source frames during a speed-ramped beat,
//   - computing a TransitionSeries master duration,
//   - clamping a zoom window so it stays inside the source frame,
//   - mapping a caption word's start time to an output frame.
//
// Every function here is PURE and mirrors `timing_math.py` VERBATIM so the
// Python (manifest-producing) side and the TypeScript (Remotion-consuming)
// side compute identical values. If you change a function here, change its
// Python twin and the tests in `scripts/test_timing_math.py`.
//
// This file is copied into `videos/<slug>/scenes/timing.ts` at Phase 4. It has
// no Remotion imports, so the scenes import their math from here and never
// re-derive it inline.

/**
 * Index of the PNG whose timestamp is nearest to `tSeconds`.
 *
 * `frameTimesS` is the ascending per-frame timestamp list from timing.json
 * (`frame_times_s`). Ties resolve to the EARLIER frame. Times before the first
 * frame clamp to 0; after the last clamp to the last index. Empty list -> 0.
 */
export function castTimeToFrameIndex(
  tSeconds: number,
  frameTimesS: readonly number[],
): number {
  const n = frameTimesS.length;
  if (n === 0) return 0;
  // bisect_left: first index whose value is >= tSeconds.
  let lo = 0;
  let hi = n;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (frameTimesS[mid] < tSeconds) lo = mid + 1;
    else hi = mid;
  }
  const pos = lo;
  if (pos <= 0) return 0;
  if (pos >= n) return n - 1;
  const before = frameTimesS[pos - 1];
  const after = frameTimesS[pos];
  // Nearest neighbour; tie goes to the earlier frame.
  if (tSeconds - before <= after - tSeconds) return pos - 1;
  return pos;
}

/**
 * Returns a mapper f(outputOffset) -> source PNG index for a ramped beat.
 *
 * The source span [beatStartFrame, beatEndFrame] is played `factor`x faster:
 * each output frame advances `factor` source frames. `outputOffset` is 0-based
 * from the start of the beat in the OUTPUT timeline. The result is clamped to
 * the source span so the last output frames hold on the final PNG.
 */
export function speedrampFrameMap(
  beatStartFrame: number,
  beatEndFrame: number,
  factor: number,
): (outputOffset: number) => number {
  if (factor <= 0) throw new Error("speedramp factor must be > 0");
  return (outputOffset: number): number => {
    const src = beatStartFrame + Math.round(outputOffset * factor);
    if (src < beatStartFrame) return beatStartFrame;
    if (src > beatEndFrame) return beatEndFrame;
    return src;
  };
}

/**
 * How many OUTPUT frames a ramped source span occupies (>= 1).
 * Inverse of the per-frame advance in `speedrampFrameMap`.
 */
export function speedrampOutputFrames(
  beatStartFrame: number,
  beatEndFrame: number,
  factor: number,
): number {
  if (factor <= 0) throw new Error("speedramp factor must be > 0");
  const span = beatEndFrame - beatStartFrame + 1;
  return Math.max(1, Math.ceil(span / factor));
}

/**
 * TransitionSeries total = sum(beat durations) - sum(transition overlaps).
 *
 * `transitionFrames` may be a scalar (same overlap between every adjacent pair)
 * or a per-transition array. With N beats there are N-1 transitions. Returns an
 * integer frame count; 0 for an empty beat list.
 */
export function computeMasterDuration(
  beatDurations: readonly number[],
  transitionFrames: number | readonly number[],
): number {
  const beats = beatDurations;
  if (beats.length === 0) return 0;
  let total = beats.reduce((a, b) => a + b, 0);
  if (Array.isArray(transitionFrames)) {
    total -= (transitionFrames as readonly number[]).reduce((a, b) => a + b, 0);
  } else {
    total -= (beats.length - 1) * (transitionFrames as number);
  }
  return Math.trunc(total);
}

/**
 * Clamp a zoom centre so the visible window stays inside the source frame.
 *
 * At `zoomFactor`, the visible window is `1/zoomFactor` of the frame on each
 * axis, so its centre must lie within [half, 1-half] where half = 0.5/zoom.
 * Returns the clamped centre `[cx, cy]` in normalized 0..1 coords. For
 * zoomFactor <= 1 the window is the whole frame, so the centre is (0.5, 0.5).
 */
export function clampZoomWindow(
  x: number,
  y: number,
  zoomFactor: number,
): [number, number] {
  if (zoomFactor <= 1) return [0.5, 0.5];
  const half = 0.5 / zoomFactor;
  const cx = Math.min(Math.max(x, half), 1.0 - half);
  const cy = Math.min(Math.max(y, half), 1.0 - half);
  return [cx, cy];
}

/** Map a caption word's start time (seconds) to an output frame index. */
export function captionWordToFrame(wordStartS: number, fps: number): number {
  return Math.round(wordStartS * fps);
}
