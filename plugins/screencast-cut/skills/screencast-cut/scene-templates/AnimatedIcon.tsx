import React from "react";
import {
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { SpringConfig } from "remotion";
import { makeCircle } from "@remotion/shapes";
import {
  animationPhase,
  burstParticles,
  resolveMotion,
  DEFAULT_MOTION,
  type MotionSettings,
} from "./timing";
import {
  drawOnDash,
  morphPath,
  popInScale,
  spinAngle,
  type RecipeName,
} from "./recipes";
// Theme-tunable defaults come from the ACTIVE brand profile. Swapping the active
// profile (src/brand/active) changes these without touching any scene.
import { motion as brandMotion, easings } from "../../../src/brand/active";

// An icon is just "an SVG": a viewBox plus its `<path>` d-strings. The curated
// floor (icons/index.ts) and the Iconify puller both emit this shape, so the
// recipe engine consumes them identically regardless of source. `strokeWidth`
// is the source set's native stroke (2 for Lucide) and can be overridden.
export interface IconDef {
  viewBox: string;
  paths: string[];
  strokeWidth?: number;
}

export interface AnimatedIconProps {
  icon: IconDef;
  /** Recipe to run; defaults to the active profile's `motion.defaultRecipe`. */
  recipe?: RecipeName;
  /** Brand color; recolors stroke (icons use stroke="currentColor"). */
  color?: string;
  strokeWidth?: number;
  /** Rendered pixel size of the square icon. */
  size?: number;
  startFrame?: number;
  /** Overrides the profile's `motion.durationInFrames`. */
  durationInFrames?: number;
  /** Overrides the profile's `motion.easing` (a key of the profile `easings`). */
  easing?: string;
  /** Overrides the profile's `motion.particleIntensity`. */
  particleIntensity?: number;
  springConfig?: Partial<SpringConfig>;
  /** drawOn stagger overlap (0 sequential … 1 simultaneous). */
  staggerOverlap?: number;
  /** burst recipe: base particle count (scaled by particleIntensity). */
  burstCount?: number;
  burstRadius?: number;
  /** spin recipe: rotations per durationInFrames. */
  spinTurns?: number;
  /** morph recipe: the destination icon (single compatible path). */
  morphTo?: IconDef;
  /**
   * Optional THEME override carrying a `motion` block and the profile `easings`
   * map. When provided it replaces the active-profile defaults for this render
   * (precedence unchanged: config `DEFAULT_MOTION` < theme < per-use prop). With
   * no `theme` the component reads `src/brand/active` exactly as before, so this
   * is backward-compatible. Used by the per-theme example packs to render the
   * same pack under multiple themes in one composition.
   */
  theme?: {
    motion: Partial<MotionSettings>;
    easings: Record<string, (x: number) => number>;
  };
}

const DEFAULT_SPRING: Partial<SpringConfig> = {
  damping: 12,
  mass: 0.5,
  stiffness: 180,
};

const identity = (x: number): number => x;

/**
 * Render a single animated icon with one of the motion recipes.
 *
 * Theme defaults are resolved with precedence **config < profile < per-use**:
 * the `DEFAULT_MOTION` floor (mirrors config.json), then the active profile's
 * `motion` block, then any per-use prop. `popIn`/`spin`/`burst` transform the
 * whole `<svg>`, so they work on ANY icon. `drawOn` needs path `d`-strings (it
 * strokes them on via `evolvePath`, staggered with `staggeredProgress`, eased by
 * the profile easing); for a pathless icon it falls back to `popIn`. `morph`
 * needs two structurally-compatible single-path icons; without a valid `morphTo`
 * it also falls back to `popIn`. Recolor is a single `color` prop.
 */
export const AnimatedIcon: React.FC<AnimatedIconProps> = ({
  icon,
  recipe,
  color = "currentColor",
  strokeWidth,
  size = 96,
  startFrame = 0,
  durationInFrames,
  easing,
  particleIntensity,
  springConfig = DEFAULT_SPRING,
  staggerOverlap = 0.6,
  burstCount = 8,
  burstRadius,
  spinTurns = 1,
  morphTo,
  theme,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Theme tokens come from the active profile unless an explicit `theme` prop
  // overrides them (per-theme example packs). Either way precedence below is
  // config < theme/profile < per-use.
  const themeMotion = theme?.motion ?? brandMotion;
  const themeEasings = theme?.easings ?? easings;

  // config < profile < per-use. Only the keys named per-use override.
  const m = resolveMotion(DEFAULT_MOTION, themeMotion, {
    durationInFrames,
    easing,
    particleIntensity,
  });
  const duration = m.durationInFrames;
  const recipeName: RecipeName = recipe ?? (m.defaultRecipe as RecipeName);
  const easingsMap = themeEasings as unknown as Record<
    string,
    (x: number) => number
  >;
  const easeFn = easingsMap[m.easing] ?? identity;
  const intensity = m.particleIntensity;

  const progress = animationPhase(frame, startFrame, duration);
  const sw = strokeWidth ?? icon.strokeWidth ?? 2;

  const pathProps = {
    stroke: color,
    strokeWidth: sw,
    fill: "none",
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };

  const hasPaths = icon.paths.length > 0;
  const canMorph =
    !!morphTo && icon.paths.length === 1 && morphTo.paths.length === 1;

  // Resolve fallbacks explicitly so a non-path icon never silently fails to
  // animate (drawOn → popIn) and a misconfigured morph degrades gracefully.
  let effective: RecipeName = recipeName;
  if (recipeName === "drawOn" && !hasPaths) effective = "popIn";
  if (recipeName === "morph" && !canMorph) effective = "popIn";

  if (effective === "drawOn") {
    const eased = easeFn(progress);
    return (
      <svg
        viewBox={icon.viewBox}
        width={size}
        height={size}
        style={{ overflow: "visible" }}
      >
        {icon.paths.map((d, i) => {
          const dash = drawOnDash(
            eased,
            d,
            i,
            icon.paths.length,
            staggerOverlap,
          );
          return (
            <path
              key={i}
              d={d}
              {...pathProps}
              strokeDasharray={dash.strokeDasharray}
              strokeDashoffset={dash.strokeDashoffset}
            />
          );
        })}
      </svg>
    );
  }

  if (effective === "spin") {
    const angle = spinAngle(frame, startFrame, duration, spinTurns);
    return (
      <svg
        viewBox={icon.viewBox}
        width={size}
        height={size}
        style={{
          transform: `rotate(${angle}deg)`,
          transformOrigin: "center",
          overflow: "visible",
        }}
      >
        {icon.paths.map((d, i) => (
          <path key={i} d={d} {...pathProps} />
        ))}
      </svg>
    );
  }

  if (effective === "morph" && morphTo) {
    const d = morphPath(easeFn(progress), icon.paths[0], morphTo.paths[0]);
    return (
      <svg
        viewBox={icon.viewBox}
        width={size}
        height={size}
        style={{ overflow: "visible" }}
      >
        <path d={d} {...pathProps} />
      </svg>
    );
  }

  // Shared spring used by popIn (and the icon body of burst).
  const s = spring({
    frame: frame - startFrame,
    fps,
    config: springConfig,
    durationInFrames: duration,
  });
  const scale = popInScale(s);
  const fadeIn = Math.max(1, Math.round(duration * 0.2));
  const opacity = interpolate(
    frame,
    [startFrame, startFrame + fadeIn],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  const iconSvg = (
    <svg
      viewBox={icon.viewBox}
      width={size}
      height={size}
      style={{
        transform: `scale(${scale})`,
        opacity,
        overflow: "visible",
      }}
    >
      {icon.paths.map((d, i) => (
        <path key={i} d={d} {...pathProps} />
      ))}
    </svg>
  );

  if (effective === "burst") {
    const maxR = burstRadius ?? size * 0.7;
    const count = Math.max(1, Math.round(burstCount * intensity));
    const particles = burstParticles(count, progress, maxR);
    const dot = makeCircle({ radius: Math.max(2, size * 0.05) });
    return (
      <div
        style={{
          position: "relative",
          width: size,
          height: size,
          display: "inline-block",
        }}
      >
        <div style={{ position: "absolute", inset: 0 }}>{iconSvg}</div>
        <svg
          width={size}
          height={size}
          viewBox={`${-size / 2} ${-size / 2} ${size} ${size}`}
          style={{ position: "absolute", inset: 0, overflow: "visible" }}
        >
          {particles.map((p, i) => (
            <path
              key={i}
              d={dot.path}
              fill={color}
              opacity={p.opacity}
              transform={`translate(${p.x} ${p.y}) scale(${p.scale})`}
            />
          ))}
        </svg>
      </div>
    );
  }

  // popIn (and drawOn/morph fallbacks land here).
  return iconSvg;
};
