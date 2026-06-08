#!/usr/bin/env python3
"""Pure idle-detection math for screen recordings (Slice C).

Separated from `video_to_frames.py` (the ffmpeg I/O wrapper) so the detection
logic is unit-testable offline with no ffmpeg and no real video. Two pure
pieces:

  - `downsample_mask` — zero out the top-right menubar-clock box on an already
    downsampled grayscale frame, so a ticking clock doesn't read as activity.
  - `mean_abs_diff` — mean absolute per-pixel difference between two frames.
  - `detect_idle_gaps` — turn a sequence of adjacent-frame diffs into idle_gaps
    in the SAME shape `cast_to_frames.find_idle_gaps` emits (start_s/end_s/
    duration_s/kind), so the downstream cut/speed-ramp logic is shared.

Frames here are 2-D `numpy` uint8 arrays (grayscale). `video_to_frames.py` makes
them by asking ffmpeg for `fps=N,scale=W:H,format=gray` rawvideo.
"""

import numpy as np


def downsample_mask(frame, *, mask_top_frac=0.08, mask_right_frac=0.12):
    """Return a copy of `frame` with the top-right menubar-clock box zeroed.

    A macOS/desktop menubar clock advances every minute in the top-right corner;
    masking that box keeps a clock tick from defeating the static-frame test.
    `mask_top_frac` / `mask_right_frac` are fractions of height / width. Either
    <= 0 disables masking on that axis (no box masked if either is <= 0).
    """
    out = frame.copy()
    if mask_top_frac <= 0 or mask_right_frac <= 0:
        return out
    h, w = out.shape[:2]
    top = max(1, int(round(h * mask_top_frac)))
    right = max(1, int(round(w * mask_right_frac)))
    out[0:top, w - right:w] = 0
    return out


def mean_abs_diff(a, b):
    """Mean absolute per-pixel difference of two same-shape grayscale frames.

    Result is on the 0..255 grayscale scale. Computed in int16 to avoid uint8
    wraparound.
    """
    a16 = a.astype(np.int16)
    b16 = b.astype(np.int16)
    return float(np.mean(np.abs(a16 - b16)))


def frame_diffs(frames):
    """Adjacent-frame mean-abs diffs for a list/array of grayscale frames.

    Returns a list of length max(0, len(frames) - 1).
    """
    return [mean_abs_diff(frames[i], frames[i + 1]) for i in range(len(frames) - 1)]


def detect_idle_gaps(
    diffs,
    sample_fps,
    *,
    pixel_diff_threshold=2.0,
    speedramp_threshold=2.0,
    cut_threshold=8.0,
):
    """Turn adjacent-frame diffs into idle_gaps (same shape as the cast path).

    `diffs[i]` is the mean-abs diff between sampled frame i and i+1, i.e. it
    describes the interval [i / sample_fps, (i+1) / sample_fps]. An interval is
    "static" when `diffs[i] < pixel_diff_threshold`. A maximal run of static
    intervals [k0 .. k1] covers wall time [k0 / fps, (k1 + 1) / fps]; if that
    duration is >= cut_threshold it's a `cut`, elif >= speedramp_threshold a
    `speedramp`, else dropped.

    Returns list of {start_s, end_s, duration_s, kind} (kind in speedramp|cut),
    matching `cast_to_frames.find_idle_gaps` so the Remotion side is shared.
    """
    if sample_fps <= 0:
        raise ValueError("sample_fps must be > 0")
    gaps = []
    n = len(diffs)
    i = 0
    while i < n:
        if diffs[i] >= pixel_diff_threshold:
            i += 1
            continue
        j = i
        while j < n and diffs[j] < pixel_diff_threshold:
            j += 1
        # Static run covers intervals [i .. j-1] → time [i/fps, j/fps].
        start_s = i / sample_fps
        end_s = j / sample_fps
        dur = end_s - start_s
        if dur >= speedramp_threshold:
            kind = "cut" if dur >= cut_threshold else "speedramp"
            gaps.append({
                "start_s": round(start_s, 4),
                "end_s": round(end_s, 4),
                "duration_s": round(dur, 4),
                "kind": kind,
            })
        i = j
    return gaps
