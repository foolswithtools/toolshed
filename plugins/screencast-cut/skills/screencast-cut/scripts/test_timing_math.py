#!/usr/bin/env python3
"""Unit tests for the pure timing/geometry math core.

These run with plain pytest, no heavy tools. They are the contract the TS
twin in `scene-templates/timing.ts` must also satisfy — if you change a
function here, change the TS mirror and re-check both.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from timing_math import (
    cast_time_to_frame_index,
    speedramp_frame_map,
    speedramp_output_frames,
    compute_master_duration,
    clamp_zoom_window,
    caption_word_to_frame,
)


# --- cast_time_to_frame_index -------------------------------------------------

def test_frame_index_empty_list():
    assert cast_time_to_frame_index(1.0, []) == 0


def test_frame_index_clamps_before_first():
    ft = [0.0, 0.5, 1.0]
    assert cast_time_to_frame_index(-5.0, ft) == 0


def test_frame_index_clamps_after_last():
    ft = [0.0, 0.5, 1.0]
    assert cast_time_to_frame_index(99.0, ft) == 2


def test_frame_index_exact_hit():
    ft = [0.0, 0.5, 1.0, 1.5]
    assert cast_time_to_frame_index(1.0, ft) == 2


def test_frame_index_nearest_neighbour():
    ft = [0.0, 1.0, 2.0]
    # 1.4 is closer to 1.0 (index 1) than 2.0 (index 2)
    assert cast_time_to_frame_index(1.4, ft) == 1
    # 1.6 is closer to 2.0 (index 2)
    assert cast_time_to_frame_index(1.6, ft) == 2


def test_frame_index_tie_goes_to_earlier():
    ft = [0.0, 1.0, 2.0]
    # exactly halfway -> earlier frame
    assert cast_time_to_frame_index(1.5, ft) == 1


# --- speedramp_frame_map ------------------------------------------------------

def test_speedramp_direction_advances_forward():
    # A 4x ramp over source frames 100..200. Each output frame advances 4 src.
    m = speedramp_frame_map(100, 200, 4)
    assert m(0) == 100      # start
    assert m(1) == 104      # +4
    assert m(10) == 140     # +40
    # output frames march forward in source order (no reversal)
    assert m(5) > m(4) > m(3)


def test_speedramp_clamps_to_source_span():
    m = speedramp_frame_map(100, 200, 4)
    # 30 output frames * 4 = 120 src offset -> would be 220, clamp to 200
    assert m(30) == 200
    assert m(1000) == 200


def test_speedramp_factor_one_is_realtime():
    m = speedramp_frame_map(0, 50, 1)
    assert m(0) == 0
    assert m(25) == 25
    assert m(50) == 50


def test_speedramp_rejects_nonpositive_factor():
    import pytest
    with pytest.raises(ValueError):
        speedramp_frame_map(0, 10, 0)
    with pytest.raises(ValueError):
        speedramp_frame_map(0, 10, -2)


def test_speedramp_output_frames_basic():
    # span = 200-100+1 = 101 source frames; at 4x -> ceil(101/4) = 26 output
    assert speedramp_output_frames(100, 200, 4) == 26


def test_speedramp_output_frames_min_one():
    # zero-length span still occupies at least one output frame
    assert speedramp_output_frames(50, 50, 4) == 1


def test_speedramp_output_frames_realtime():
    assert speedramp_output_frames(0, 99, 1) == 100


# --- compute_master_duration --------------------------------------------------

def test_master_duration_empty():
    assert compute_master_duration([], 18) == 0


def test_master_duration_single_beat_no_transition():
    # one beat -> zero transitions -> full duration
    assert compute_master_duration([90], 18) == 90


def test_master_duration_scalar_transition():
    # 3 beats, 2 transitions of 18 frames each: 90+75+60 - 2*18 = 189
    assert compute_master_duration([90, 75, 60], 18) == 189


def test_master_duration_per_transition_list():
    # explicit per-transition overlaps
    assert compute_master_duration([90, 75, 60], [18, 12]) == 90 + 75 + 60 - 30


def test_master_duration_many_transitions():
    beats = [30] * 10            # 300 frames
    # 9 transitions of 6 frames -> 300 - 54 = 246
    assert compute_master_duration(beats, 6) == 246


# --- clamp_zoom_window --------------------------------------------------------

def test_zoom_clamp_no_zoom_centers():
    assert clamp_zoom_window(0.2, 0.9, 1.0) == (0.5, 0.5)
    assert clamp_zoom_window(0.2, 0.9, 0.5) == (0.5, 0.5)


def test_zoom_clamp_corner_top_left():
    # at 2x, half-window = 0.25; a click at (0,0) clamps to (0.25, 0.25)
    cx, cy = clamp_zoom_window(0.0, 0.0, 2.0)
    assert cx == 0.25 and cy == 0.25


def test_zoom_clamp_corner_bottom_right():
    cx, cy = clamp_zoom_window(1.0, 1.0, 2.0)
    assert cx == 0.75 and cy == 0.75


def test_zoom_clamp_center_unchanged():
    cx, cy = clamp_zoom_window(0.5, 0.5, 1.6)
    assert cx == 0.5 and cy == 0.5


def test_zoom_clamp_partial_axis():
    # 1.6x -> half = 0.3125; x=0.1 clamps up to 0.3125, y=0.5 stays
    cx, cy = clamp_zoom_window(0.1, 0.5, 1.6)
    assert abs(cx - 0.3125) < 1e-9
    assert cy == 0.5


# --- caption_word_to_frame ----------------------------------------------------

def test_caption_word_to_frame_basic():
    assert caption_word_to_frame(1.0, 30) == 30
    assert caption_word_to_frame(0.0, 30) == 0


def test_caption_word_to_frame_rounds():
    # 1.234s * 30 = 37.02 -> 37
    assert caption_word_to_frame(1.234, 30) == 37
    # 0.05s * 30 = 1.5 -> 2 (half-up matches JS Math.round)
    assert caption_word_to_frame(0.05, 30) == 2


def test_caption_word_to_frame_half_up_matches_js():
    # Lock the half-up contract: where Python's banker's rounding would give 2,
    # we must give 3 to match JS Math.round(2.5) in timing.ts. 2.5/30 * 30 = 2.5.
    assert caption_word_to_frame(2.5 / 30, 30) == 3
    # 4.5 -> 5 (banker's would give 4)
    assert caption_word_to_frame(4.5 / 30, 30) == 5


def test_speedramp_half_up_matches_js():
    # output_offset * factor = 2.5 -> +3 (half-up), not +2 (banker's).
    m = speedramp_frame_map(0, 100, 2.5)
    assert m(1) == 3        # round_half_up(2.5) = 3
    m2 = speedramp_frame_map(0, 100, 4.5)
    assert m2(1) == 5       # round_half_up(4.5) = 5


# --- multi-minute drift case --------------------------------------------------

def test_frame_index_over_long_timeline():
    # Simulate a 5-minute cast at 30fps: 9000 frames, perfectly clean clock.
    fps = 30
    ft = [round(i / fps, 4) for i in range(9000)]
    # A beat boundary at 247.3s should map to the nearest frame index.
    idx = cast_time_to_frame_index(247.3, ft)
    assert idx == round(247.3 * fps)            # 7419
    # And the ramp map starting there advances forward without drift.
    m = speedramp_frame_map(idx, idx + 400, 4)
    assert m(0) == idx
    assert m(100) == idx + 400                  # exactly hits the end
    assert m(200) == idx + 400                  # clamps, no overrun
