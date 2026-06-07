// Frame-deterministic motion recipes for animated icons.
//
// Animation is CODE, not data: each recipe is a small, pure helper built on
// Remotion's deterministic primitives (`evolvePath`, `interpolatePath`,
// `spring`, `interpolate`) plus the motion math twins in `timing.ts`
// (`animationPhase`, `staggeredProgress`, `burstParticles`). `AnimatedIcon.tsx`
// composes these into a rendered SVG; `ClickRipple.tsx` is the standalone
// beachhead. Nothing here reaches for randomness or wall-clock time, so two
// renders of the same frame are bit-identical.

import { evolvePath, interpolatePath } from "@remotion/paths";
import { staggeredProgress } from "./timing";

export type RecipeName = "drawOn" | "popIn" | "spin" | "burst" | "morph";

export const RECIPE_NAMES: readonly RecipeName[] = [
  "drawOn",
  "popIn",
  "spin",
  "burst",
  "morph",
] as const;

/**
 * `drawOn` — stroke reveal for one `<path>` of a multi-path icon.
 *
 * Wraps Remotion's `evolvePath` with our `staggeredProgress` twin so paths in a
 * multi-stroke icon draw on in a staggered cascade rather than all at once.
 * Returns the `strokeDasharray`/`strokeDashoffset` the caller spreads onto the
 * `<path>`. Only works on path data — `AnimatedIcon` falls back to `popIn` for
 * icons with no paths.
 */
export function drawOnDash(
  progress: number,
  d: string,
  index: number,
  count: number,
  overlap: number,
): { strokeDasharray: string; strokeDashoffset: number } {
  const local = staggeredProgress(progress, index, count, overlap);
  return evolvePath(local, d);
}

/**
 * `popIn` — spring scale. Maps a 0..1 spring value to a scale that overshoots
 * slightly and settles at 1 (the spring config supplies the overshoot).
 */
export function popInScale(springValue: number): number {
  return 0.6 + 0.4 * springValue;
}

/**
 * `spin` — continuous rotation in degrees, for loaders. Does NOT clamp, so the
 * icon keeps turning for the whole composition; `turns` rotations per
 * `durationInFrames`.
 */
export function spinAngle(
  frame: number,
  startFrame: number,
  durationInFrames: number,
  turns: number,
): number {
  if (durationInFrames <= 0) return 0;
  return ((frame - startFrame) / durationInFrames) * 360 * turns;
}

/**
 * `morph` — interpolate between two structurally-compatible single-path icons.
 * Thin wrapper over `interpolatePath`; `progress` 0 = `from`, 1 = `to`.
 */
export function morphPath(progress: number, from: string, to: string): string {
  return interpolatePath(progress, from, to);
}
