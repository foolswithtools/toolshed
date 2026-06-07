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


def caption_word_to_frame(word_start_s, fps):
    """Map a caption word's start time (seconds) to an output frame index."""
    return _round_half_up(word_start_s * fps)
