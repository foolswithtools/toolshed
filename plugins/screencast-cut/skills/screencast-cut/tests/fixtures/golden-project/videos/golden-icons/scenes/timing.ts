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
 * How many OUTPUT frames a video span [startS, endS] occupies at `factor`x.
 *
 * Screen-recording idle-trim (Slice C) plays a source span via OffthreadVideo
 * with `playbackRate = factor`; the beat's Sequence length must be the source
 * duration divided by the factor, in output frames. factor=1 is a realtime run
 * beat; factor>1 is a speed-ramp. Always >= 1. Twin of `video_beat_output_frames`
 * in `scripts/timing_math.py`.
 */
export function videoBeatOutputFrames(
  startS: number,
  endS: number,
  fps: number,
  factor = 1,
): number {
  if (factor <= 0) throw new Error("speedramp factor must be > 0");
  if (endS < startS) throw new Error("endS must be >= startS");
  return Math.max(1, Math.floor(((endS - startS) * fps) / factor + 0.5));
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

/**
 * Focal point to keep centred at the current `scale`, eased from the frame
 * centre (0.5, 0.5) at scale 1 to the clamped click `[cx, cy]` at peak zoom.
 *
 * Centring the click at EVERY scale (`tx = W*(0.5 - scale*cx)`) shifts the
 * un-zoomed frame off-centre and exposes a background gutter at scale 1. Moving
 * the focal point with zoom progress keeps the video full-frame at scale 1 and
 * pans toward the click as it zooms in. Returns `[ecx, ecy]`; the scene maps
 * them to a translate: tx = W*(0.5 - scale*ecx), ty = H*(0.5 - scale*ecy).
 * At scale 1 this gives ecx=ecy=0.5 -> tx=ty=0 (identity, no gutter).
 */
export function zoomFocalPoint(
  scale: number,
  cx: number,
  cy: number,
  zoomFactor: number,
): [number, number] {
  if (zoomFactor <= 1) return [0.5, 0.5];
  let progress = (scale - 1) / (zoomFactor - 1);
  if (progress < 0) progress = 0;
  else if (progress > 1) progress = 1;
  return [0.5 + (cx - 0.5) * progress, 0.5 + (cy - 0.5) * progress];
}

/** Map a caption word's start time (seconds) to an output frame index. */
export function captionWordToFrame(wordStartS: number, fps: number): number {
  return Math.round(wordStartS * fps);
}

// --- Motion-primitive math (animated icons) ---------------------------------
//
// The pure geometry/timing the icon recipes need. `spring()`, `evolvePath()`,
// `interpolatePath()` are Remotion built-ins used directly in the recipes and
// are NOT reimplemented here — these are only the bits *we* own and must keep
// identical to `timing_math.py`.

function clamp01(x: number): number {
  if (x < 0) return 0;
  if (x > 1) return 1;
  return x;
}

/**
 * Clamped 0..1 progress of an animation that runs over a frame window.
 *
 * Returns 0 before `startFrame`, 1 at/after `startFrame + durationFrames`, and
 * the linear fraction in between. A non-positive `durationFrames` means an
 * instantaneous animation: 0 before the start frame, 1 at/after it.
 */
export function animationPhase(
  frame: number,
  startFrame: number,
  durationFrames: number,
): number {
  if (durationFrames <= 0) return frame < startFrame ? 0 : 1;
  const p = (frame - startFrame) / durationFrames;
  if (p < 0) return 0;
  if (p > 1) return 1;
  return p;
}

/**
 * Per-element progress for a multi-element draw-on stagger.
 *
 * Spreads a global `progress` (0..1) across `count` elements so element `index`
 * animates within its own sub-window, then clamps to 0..1. `overlap` in [0,1]
 * controls how much consecutive windows overlap:
 *   - overlap = 1 → every window is the whole timeline (all animate together),
 *   - overlap = 0 → windows are sequential and non-overlapping (1/count each).
 * With `count <= 1` the element just tracks `progress`.
 */
export function staggeredProgress(
  progress: number,
  index: number,
  count: number,
  overlap: number,
): number {
  if (count <= 1) return clamp01(progress);
  const o = overlap < 0 ? 0 : overlap > 1 ? 1 : overlap;
  const lastStart = ((count - 1) / count) * (1 - o);
  const width = 1 - lastStart;
  const startI = (index / count) * (1 - o);
  return clamp01((progress - startI) / width);
}

export interface BurstParticle {
  x: number;
  y: number;
  scale: number;
  opacity: number;
}

/**
 * Deterministic radial burst: `count` particles flung from the origin.
 *
 * Particle `i` sits at angle `i / count * 2π` (evenly spaced, no randomness), at
 * radius `progress * maxRadius`. It shrinks and fades as it travels. Returns
 * `{x, y, scale, opacity}` offsets relative to the origin; the component adds
 * the anchor position.
 */
export function burstParticles(
  count: number,
  progress: number,
  maxRadius: number,
): BurstParticle[] {
  const n = Math.trunc(count);
  if (n <= 0) return [];
  const p = clamp01(progress);
  const radius = p * maxRadius;
  const fade = 1 - p;
  const out: BurstParticle[] = [];
  for (let i = 0; i < n; i++) {
    const angle = (i / n) * 2 * Math.PI;
    out.push({
      x: Math.cos(angle) * radius,
      y: Math.sin(angle) * radius,
      scale: fade,
      opacity: fade,
    });
  }
  return out;
}

/**
 * Expanding ring for a click-ripple: `radius` grows (`progress * maxRadius`,
 * monotonically increasing) and `opacity` fades (`1 - progress`, monotonically
 * decreasing) so the ring expands outward and dissolves.
 */
export function rippleGeometry(
  progress: number,
  maxRadius: number,
): { radius: number; opacity: number } {
  const p = clamp01(progress);
  return { radius: p * maxRadius, opacity: 1 - p };
}

// --- Theme-tunable motion defaults ------------------------------------------
//
// The lowest-precedence motion defaults. Mirrors the `"motion"` block in
// `config.json` and `DEFAULT_MOTION` in `timing_math.py` VERBATIM — the global
// floor a profile only deviates from. `defaultRecipe` is typed as `string` here
// (not `RecipeName`) so this twin stays free of any Remotion/recipe import.
export interface MotionSettings {
  defaultRecipe: string;
  durationInFrames: number;
  easing: string;
  particleIntensity: number;
}

export const DEFAULT_MOTION: MotionSettings = {
  defaultRecipe: "drawOn",
  durationInFrames: 30,
  easing: "pop",
  particleIntensity: 1,
};

/**
 * Merge motion settings with precedence config < profile < per-use.
 *
 * Later layers override earlier ones key-by-key; an `undefined`/`null` value is
 * treated as "not set" and falls through, so a per-use override only names the
 * keys it changes. Returns a new merged object.
 */
export function resolveMotion(
  configDefaults?: Partial<MotionSettings> | null,
  profileMotion?: Partial<MotionSettings> | null,
  perUse?: Partial<MotionSettings> | null,
): MotionSettings {
  const out: Record<string, unknown> = {};
  for (const layer of [configDefaults, profileMotion, perUse]) {
    if (!layer) continue;
    for (const [k, v] of Object.entries(layer)) {
      if (v !== undefined && v !== null) out[k] = v;
    }
  }
  return out as unknown as MotionSettings;
}
