#!/usr/bin/env python3
"""Pure timing/geometry math shared across the screencast-cut pipeline.

These functions are the single source of truth for the fragile arithmetic that
was previously re-derived freehand in every generated Remotion scene:

  - mapping a cast/GIF timestamp to a PNG frame index,
  - advancing source frames during a speed-ramped beat,
  - computing a TransitionSeries master duration,
  - clamping a zoom window so it stays inside the source frame,
  - mapping a caption word's start time to an output frame.

Every function here is PURE (no I/O, no globals) and is mirrored verbatim in
`scene-templates/timing.ts` so the Python (manifest-producing) side and the
TypeScript (Remotion-consuming) side compute identical values. If you change a
function here, change its TS twin and the tests in `test_timing_math.py`.
"""

import bisect
import math


def _round_half_up(x):
    """Round half away from zero-toward-+inf, matching JS `Math.round`.

    Python's built-in `round` is banker's rounding (half-to-even), which
    diverges from `Math.round` in `timing.ts` at exact .5 boundaries. All
    inputs here are non-negative (frame offsets, times), so `floor(x + 0.5)`
    reproduces `Math.round` exactly and keeps the two clocks bit-identical.
    """
    return math.floor(x + 0.5)


def cast_time_to_frame_index(t_s, frame_times_s):
    """Return the index of the PNG whose timestamp is nearest to `t_s`.

    `frame_times_s` is the ascending per-frame timestamp list from timing.json
    (`frame_times_s`). Ties resolve to the earlier frame. Times before the first
    frame clamp to 0; after the last clamp to the last index. Empty list -> 0.

    This is the boundary where the cast-event clock and the GIF/PNG clock are
    collapsed into a single frame-index domain, so downstream consumers never
    re-interpolate one clock against the other.
    """
    n = len(frame_times_s)
    if n == 0:
        return 0
    pos = bisect.bisect_left(frame_times_s, t_s)
    if pos <= 0:
        return 0
    if pos >= n:
        return n - 1
    before = frame_times_s[pos - 1]
    after = frame_times_s[pos]
    # Nearest neighbour; tie goes to the earlier frame.
    if (t_s - before) <= (after - t_s):
        return pos - 1
    return pos


def speedramp_frame_map(beat_start_frame, beat_end_frame, factor):
    """Return a mapper f(output_offset) -> source PNG index for a ramped beat.

    The source span [beat_start_frame, beat_end_frame] is played `factor`x
    faster: each output frame advances `factor` source frames. `output_offset`
    is 0-based from the start of the beat in the OUTPUT timeline. The result is
    clamped to the source span so the last output frames hold on the final PNG.
    """
    if factor <= 0:
        raise ValueError("speedramp factor must be > 0")

    def mapper(output_offset):
        src = beat_start_frame + _round_half_up(output_offset * factor)
        if src < beat_start_frame:
            return beat_start_frame
        if src > beat_end_frame:
            return beat_end_frame
        return src

    return mapper


def speedramp_output_frames(beat_start_frame, beat_end_frame, factor):
    """How many OUTPUT frames a ramped source span occupies (>= 1).

    Convenience used when laying out beat durations; the inverse of the per-frame
    advance in `speedramp_frame_map`.
    """
    if factor <= 0:
        raise ValueError("speedramp factor must be > 0")
    span = beat_end_frame - beat_start_frame + 1
    return max(1, math.ceil(span / factor))


def compute_master_duration(beat_durations, transition_frames):
    """TransitionSeries total = sum(beat durations) - sum(transition overlaps).

    `transition_frames` may be a scalar (same overlap between every adjacent
    pair) or a per-transition list. With N beats there are N-1 transitions.
    Returns an int frame count; 0 for an empty beat list.
    """
    beats = list(beat_durations)
    if not beats:
        return 0
    total = sum(beats)
    if isinstance(transition_frames, (list, tuple)):
        total -= sum(transition_frames)
    else:
        total -= (len(beats) - 1) * transition_frames
    return int(total)


def clamp_zoom_window(x, y, zoom_factor):
    """Clamp a zoom centre so the visible window stays inside the source frame.

    At `zoom_factor`, the visible window is `1/zoom_factor` of the frame on each
    axis, so its centre must lie within [half, 1-half] where half = 0.5/zoom.
    Returns the clamped centre `(cx, cy)` in normalized 0..1 coords; the scene
    converts that centre into a CSS translate. For zoom_factor <= 1 the window
    is the whole frame, so the centre clamps to (0.5, 0.5).
    """
    if zoom_factor <= 1:
        return (0.5, 0.5)
    half = 0.5 / zoom_factor
    cx = min(max(x, half), 1.0 - half)
    cy = min(max(y, half), 1.0 - half)
    return (cx, cy)


def zoom_focal_point(scale, cx, cy, zoom_factor):
    """Focal point to keep centred at the current `scale`, eased from the frame
    centre (0.5, 0.5) at scale 1 to the clamped click `(cx, cy)` at peak zoom.

    Centring the click at EVERY scale (the naive `tx = W*(0.5 - scale*cx)`)
    shifts the un-zoomed frame off-centre and exposes a background gutter at
    scale 1, where the video is not large enough to cover the offset. Moving the
    focal point with zoom progress keeps the video full-frame at scale 1 and
    pans toward the click as it zooms in. Returns `(ecx, ecy)`; the scene maps
    them to a translate:  tx = W*(0.5 - scale*ecx),  ty = H*(0.5 - scale*ecy).
    At scale 1 this gives ecx=ecy=0.5 -> tx=ty=0 (identity, no gutter).
    """
    if zoom_factor <= 1:
        return (0.5, 0.5)
    progress = (scale - 1.0) / (zoom_factor - 1.0)
    if progress < 0.0:
        progress = 0.0
    elif progress > 1.0:
        progress = 1.0
    return (0.5 + (cx - 0.5) * progress, 0.5 + (cy - 0.5) * progress)


def caption_word_to_frame(word_start_s, fps):
    """Map a caption word's start time (seconds) to an output frame index."""
    return _round_half_up(word_start_s * fps)


# --- Motion-primitive math (animated icons) -----------------------------------
#
# The pure geometry/timing the icon recipes need. `spring()`, `evolvePath()`,
# `interpolatePath()` are Remotion built-ins used directly in TS and are NOT
# reimplemented here — these are only the bits *we* own and must keep identical
# across the Python (manifest/sampling) and TypeScript (Remotion) sides.


def animation_phase(frame, start_frame, duration_frames):
    """Clamped 0..1 progress of an animation that runs over a frame window.

    Returns 0 before `start_frame`, 1 at/after `start_frame + duration_frames`,
    and the linear fraction in between. A non-positive `duration_frames` means an
    instantaneous animation: 0 before the start frame, 1 at/after it.
    """
    if duration_frames <= 0:
        return 0.0 if frame < start_frame else 1.0
    p = (frame - start_frame) / duration_frames
    if p < 0.0:
        return 0.0
    if p > 1.0:
        return 1.0
    return p


def staggered_progress(progress, index, count, overlap):
    """Per-element progress for a multi-element draw-on stagger.

    Spreads a global `progress` (0..1) across `count` elements so element `index`
    animates within its own sub-window, then clamps to 0..1. `overlap` in [0,1]
    controls how much consecutive windows overlap:

      - overlap = 1  → every window is the whole timeline (all animate together),
      - overlap = 0  → windows are sequential and non-overlapping (1/count each).

    With `count <= 1` (or a single element) the element just tracks `progress`.
    Pure function of `progress`, so two renders of the same frame agree.
    """
    if count <= 1:
        return _clamp01(progress)
    o = 0.0 if overlap < 0.0 else (1.0 if overlap > 1.0 else overlap)
    # Start of the LAST element's window; window width fills the remainder so the
    # last element finishes exactly at progress 1.
    last_start = ((count - 1) / count) * (1.0 - o)
    width = 1.0 - last_start
    start_i = (index / count) * (1.0 - o)
    return _clamp01((progress - start_i) / width)


def burst_particles(count, progress, max_radius):
    """Deterministic radial burst: `count` particles flung from the origin.

    Particle `i` sits at angle `i / count * 2π` (evenly spaced, no randomness),
    at radius `progress * max_radius`. It shrinks and fades as it travels, so the
    burst reads as an outward spark. Returns a list of
    `{x, y, scale, opacity}` offsets relative to the origin; the component adds
    the anchor position. Pure function of `progress`.
    """
    n = int(count)
    if n <= 0:
        return []
    p = _clamp01(progress)
    radius = p * max_radius
    fade = 1.0 - p
    out = []
    for i in range(n):
        angle = (i / n) * 2.0 * math.pi
        out.append({
            "x": math.cos(angle) * radius,
            "y": math.sin(angle) * radius,
            "scale": fade,
            "opacity": fade,
        })
    return out


def ripple_geometry(progress, max_radius):
    """Expanding ring for a click-ripple: radius grows, opacity fades.

    `radius` is `progress * max_radius` (monotonically increasing) and `opacity`
    is `1 - progress` (monotonically decreasing) so the ring expands outward and
    dissolves. Pure function of `progress`.
    """
    p = _clamp01(progress)
    return {"radius": p * max_radius, "opacity": 1.0 - p}


def _clamp01(x):
    """Clamp to [0, 1]."""
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


# --- Theme-tunable motion defaults --------------------------------------------
#
# The lowest-precedence motion defaults. This dict mirrors the `"motion"` block
# in `config.json` and the `DEFAULT_MOTION` constant in `timing.ts` VERBATIM —
# they are the global floor a profile only deviates from. Precedence is
# resolved by `resolve_motion`: config default < profile motion < per-use.

DEFAULT_MOTION = {
    "defaultRecipe": "drawOn",
    "durationInFrames": 30,
    "easing": "pop",
    "particleIntensity": 1.0,
}


def resolve_motion(config_defaults, profile_motion, per_use):
    """Merge motion settings with precedence config < profile < per-use.

    Each argument is a dict (or None/empty). Later layers override earlier ones
    key-by-key; a key whose value is None is treated as "not set" and falls
    through to the layer below, so a per-use override only needs to name the keys
    it actually changes. Returns a new merged dict.
    """
    result = {}
    for layer in (config_defaults, profile_motion, per_use):
        if not layer:
            continue
        for k, v in layer.items():
            if v is not None:
                result[k] = v
    return result
