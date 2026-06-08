#!/usr/bin/env python3
"""Unit tests for the pure timing/geometry math core.

These run with plain pytest, no heavy tools. They are the contract the TS
twin in `scene-templates/timing.ts` must also satisfy — if you change a
function here, change the TS mirror and re-check both.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import math

from timing_math import (
    cast_time_to_frame_index,
    speedramp_frame_map,
    speedramp_output_frames,
    video_beat_output_frames,
    compute_master_duration,
    clamp_zoom_window,
    zoom_focal_point,
    caption_word_to_frame,
    animation_phase,
    staggered_progress,
    burst_particles,
    ripple_geometry,
    resolve_motion,
    DEFAULT_MOTION,
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


# --- video_beat_output_frames (Slice C twin) ---------------------------------

def test_video_beat_output_frames_realtime():
    # 2s @ 30fps realtime = 60 output frames.
    assert video_beat_output_frames(0, 2, 30, 1) == 60


def test_video_beat_output_frames_speedramp_rounds_half_up():
    # 3s @ 30fps / 4 = 90/4 = 22.5 → round-half-up → 23 (matches JS Math.round).
    assert video_beat_output_frames(13, 16, 30, 4) == 23


def test_video_beat_output_frames_min_one():
    assert video_beat_output_frames(5, 5, 30, 1) == 1


def test_video_beat_output_frames_rejects_bad_args():
    import pytest
    with pytest.raises(ValueError):
        video_beat_output_frames(0, 1, 30, 0)
    with pytest.raises(ValueError):
        video_beat_output_frames(2, 1, 30, 1)


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


# --- zoom_focal_point ---------------------------------------------------------

def test_zoom_focal_point_identity_at_scale_one():
    # At scale 1 the focal point is the frame centre regardless of the click,
    # so the translate tx = W*(0.5 - 1*ecx) is exactly 0 -> no gutter.
    assert zoom_focal_point(1.0, 0.3125, 0.4, 1.6) == (0.5, 0.5)


def test_zoom_focal_point_full_pan_at_peak():
    # At peak zoom the focal point is the clamped click.
    ecx, ecy = zoom_focal_point(1.6, 0.3125, 0.4, 1.6)
    assert abs(ecx - 0.3125) < 1e-9 and abs(ecy - 0.4) < 1e-9


def test_zoom_focal_point_regression_no_gutter():
    # The exact golden-cut-mp4 case that shipped a 360px gutter: click x=0.3
    # clamps to cx=0.3125; the buggy formula gave tx = 1920*(0.5-0.3125)=360 at
    # scale 1. With the eased focal point, tx must be 0.
    cx, cy = clamp_zoom_window(0.3, 0.4, 1.6)
    ecx, _ = zoom_focal_point(1.0, cx, cy, 1.6)
    width = 1920
    tx = width * (0.5 - 1.0 * ecx)
    assert tx == 0.0


def test_zoom_focal_point_monotonic_between():
    # Focal point moves monotonically from centre toward the click as scale rises.
    cx = 0.3125
    xs = [zoom_focal_point(s, cx, 0.5, 1.6)[0] for s in (1.0, 1.2, 1.4, 1.6)]
    assert xs[0] == 0.5
    assert all(b <= a for a, b in zip(xs, xs[1:]))  # decreasing toward cx<0.5
    assert abs(xs[-1] - cx) < 1e-9


def test_zoom_focal_point_no_zoom():
    assert zoom_focal_point(1.0, 0.2, 0.9, 1.0) == (0.5, 0.5)


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


# --- animation_phase ----------------------------------------------------------

def test_animation_phase_before_start_is_zero():
    assert animation_phase(5, 10, 20) == 0.0


def test_animation_phase_at_start_is_zero():
    assert animation_phase(10, 10, 20) == 0.0


def test_animation_phase_at_end_is_one():
    # frame == start + duration -> fully done
    assert animation_phase(30, 10, 20) == 1.0


def test_animation_phase_after_end_clamps_to_one():
    assert animation_phase(999, 10, 20) == 1.0


def test_animation_phase_midpoint():
    assert abs(animation_phase(20, 10, 20) - 0.5) < 1e-12


def test_animation_phase_zero_duration_is_step():
    # instantaneous: 0 before the start frame, 1 at/after it
    assert animation_phase(9, 10, 0) == 0.0
    assert animation_phase(10, 10, 0) == 1.0
    assert animation_phase(11, 10, 0) == 1.0


def test_animation_phase_monotonic_nondecreasing():
    vals = [animation_phase(f, 0, 30) for f in range(40)]
    assert all(b >= a for a, b in zip(vals, vals[1:]))


# --- staggered_progress -------------------------------------------------------

def test_staggered_single_element_tracks_progress():
    assert staggered_progress(0.37, 0, 1, 0.5) == 0.37


def test_staggered_full_overlap_all_equal_progress():
    # overlap=1 -> every element sees the global progress
    for i in range(4):
        assert abs(staggered_progress(0.6, i, 4, 1.0) - 0.6) < 1e-12


def test_staggered_zero_overlap_sequential_windows():
    # overlap=0, count=4 -> each window is 1/4 wide and non-overlapping.
    # At global progress 0.1 only element 0 is mid-animation; later ones are 0.
    assert abs(staggered_progress(0.1, 0, 4, 0.0) - 0.4) < 1e-12  # 0.1/0.25
    assert staggered_progress(0.1, 1, 4, 0.0) == 0.0
    assert staggered_progress(0.1, 3, 4, 0.0) == 0.0


def test_staggered_last_element_finishes_at_one():
    # The last element completes exactly when global progress hits 1.
    assert staggered_progress(1.0, 3, 4, 0.0) == 1.0
    assert staggered_progress(1.0, 3, 4, 0.5) == 1.0


def test_staggered_clamped_0_1():
    assert staggered_progress(-0.5, 0, 3, 0.5) == 0.0
    assert staggered_progress(2.0, 2, 3, 0.5) == 1.0


def test_staggered_overlap_clamped():
    # out-of-range overlap is clamped, never divides by zero or NaNs
    assert staggered_progress(0.5, 1, 3, 5.0) == 0.5     # treated as overlap=1
    v = staggered_progress(0.5, 1, 3, -1.0)              # treated as overlap=0
    assert 0.0 <= v <= 1.0


def test_staggered_first_element_leads():
    # At a mid global progress, earlier elements are further along than later.
    p = 0.5
    vals = [staggered_progress(p, i, 5, 0.3) for i in range(5)]
    assert all(a >= b for a, b in zip(vals, vals[1:]))


# --- burst_particles ----------------------------------------------------------

def test_burst_count_and_angles():
    parts = burst_particles(6, 1.0, 100.0)
    assert len(parts) == 6
    # particle i is at angle i/6 * 2pi, radius = progress*max = 100
    for i, p in enumerate(parts):
        angle = (i / 6) * 2 * math.pi
        assert abs(p["x"] - math.cos(angle) * 100.0) < 1e-9
        assert abs(p["y"] - math.sin(angle) * 100.0) < 1e-9


def test_burst_zero_count_empty():
    assert burst_particles(0, 0.5, 100.0) == []


def test_burst_at_progress_zero_collapsed_at_origin():
    parts = burst_particles(8, 0.0, 100.0)
    assert all(abs(p["x"]) < 1e-12 and abs(p["y"]) < 1e-12 for p in parts)
    # fully visible at the start
    assert all(abs(p["opacity"] - 1.0) < 1e-12 for p in parts)


def test_burst_fade_and_shrink_with_progress():
    parts = burst_particles(4, 0.75, 100.0)
    assert all(abs(p["opacity"] - 0.25) < 1e-12 for p in parts)
    assert all(abs(p["scale"] - 0.25) < 1e-12 for p in parts)


def test_burst_first_particle_on_positive_x_axis():
    parts = burst_particles(4, 1.0, 50.0)
    assert abs(parts[0]["x"] - 50.0) < 1e-9
    assert abs(parts[0]["y"]) < 1e-9


def test_burst_radius_monotonic_in_progress():
    def r(p):
        part = burst_particles(4, p, 100.0)[0]
        return math.hypot(part["x"], part["y"])
    rs = [r(p) for p in (0.0, 0.25, 0.5, 0.75, 1.0)]
    assert all(b >= a for a, b in zip(rs, rs[1:]))


# --- ripple_geometry ----------------------------------------------------------

def test_ripple_radius_grows_opacity_fades():
    a = ripple_geometry(0.0, 200.0)
    b = ripple_geometry(0.5, 200.0)
    c = ripple_geometry(1.0, 200.0)
    assert a["radius"] == 0.0 and abs(a["opacity"] - 1.0) < 1e-12
    assert abs(b["radius"] - 100.0) < 1e-12 and abs(b["opacity"] - 0.5) < 1e-12
    assert abs(c["radius"] - 200.0) < 1e-12 and c["opacity"] == 0.0


def test_ripple_opacity_monotonic_decreasing():
    ops = [ripple_geometry(p, 200.0)["opacity"] for p in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)]
    assert all(b <= a for a, b in zip(ops, ops[1:]))


def test_ripple_radius_monotonic_increasing():
    rs = [ripple_geometry(p, 200.0)["radius"] for p in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)]
    assert all(b >= a for a, b in zip(rs, rs[1:]))


def test_ripple_clamps_progress():
    assert ripple_geometry(-1.0, 200.0)["radius"] == 0.0
    assert ripple_geometry(5.0, 200.0)["radius"] == 200.0


# --- resolve_motion (theme-tunable motion precedence) -------------------------

def test_motion_config_only():
    out = resolve_motion(DEFAULT_MOTION, None, None)
    assert out["defaultRecipe"] == "drawOn"
    assert out["durationInFrames"] == 30


def test_motion_profile_overrides_config():
    profile = {"defaultRecipe": "popIn", "durationInFrames": 45}
    out = resolve_motion(DEFAULT_MOTION, profile, None)
    assert out["defaultRecipe"] == "popIn"      # profile wins
    assert out["durationInFrames"] == 45
    assert out["easing"] == "pop"               # untouched key falls through to config


def test_motion_per_use_overrides_profile_and_config():
    profile = {"defaultRecipe": "popIn", "durationInFrames": 45}
    per_use = {"durationInFrames": 12}
    out = resolve_motion(DEFAULT_MOTION, profile, per_use)
    assert out["durationInFrames"] == 12        # per-use wins
    assert out["defaultRecipe"] == "popIn"      # still the profile value
    assert out["easing"] == "pop"               # still the config value


def test_motion_none_values_fall_through():
    # a layer that names a key but sets it None must NOT clobber a lower layer
    profile = {"defaultRecipe": "spin"}
    per_use = {"defaultRecipe": None, "particleIntensity": 0.5}
    out = resolve_motion(DEFAULT_MOTION, profile, per_use)
    assert out["defaultRecipe"] == "spin"       # per-use None did not override
    assert out["particleIntensity"] == 0.5


def test_motion_full_precedence_chain():
    out = resolve_motion(
        {"defaultRecipe": "drawOn", "durationInFrames": 30, "easing": "pop", "particleIntensity": 1.0},
        {"easing": "camera", "particleIntensity": 0.8},
        {"particleIntensity": 0.2},
    )
    assert out == {
        "defaultRecipe": "drawOn",      # from config
        "durationInFrames": 30,         # from config
        "easing": "camera",             # from profile
        "particleIntensity": 0.2,       # from per-use
    }


def test_default_motion_has_expected_keys():
    # Locks the config<->twin contract: these keys mirror config.json "motion".
    assert set(DEFAULT_MOTION) == {
        "defaultRecipe",
        "durationInFrames",
        "easing",
        "particleIntensity",
    }


def test_default_motion_mirrors_config_json():
    # config.json "motion" is the documented global default; DEFAULT_MOTION is its
    # twin. They must agree value-for-value (the same mirroring contract the
    # timing twins keep).
    import json
    from pathlib import Path

    config = json.loads(
        (Path(__file__).resolve().parent.parent / "config.json").read_text()
    )
    assert config["motion"] == DEFAULT_MOTION
