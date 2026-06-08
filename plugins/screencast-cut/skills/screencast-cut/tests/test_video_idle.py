"""Tests for video_idle.py — the pure screen-recording idle detector (Slice C).

No ffmpeg, no real video: synthetic numpy grayscale frames and diff sequences.
"""

import numpy as np
import pytest

import video_idle as vi


# --- mean_abs_diff -----------------------------------------------------------

def test_mean_abs_diff_identical_is_zero():
    a = np.full((4, 4), 100, dtype=np.uint8)
    assert vi.mean_abs_diff(a, a) == 0.0


def test_mean_abs_diff_no_uint8_wraparound():
    a = np.zeros((2, 2), dtype=np.uint8)
    b = np.full((2, 2), 255, dtype=np.uint8)
    # 0 vs 255 must be 255, not a wrapped-around small number.
    assert vi.mean_abs_diff(a, b) == 255.0


def test_mean_abs_diff_partial():
    a = np.zeros((2, 2), dtype=np.uint8)
    b = np.array([[0, 0], [40, 40]], dtype=np.uint8)
    assert vi.mean_abs_diff(a, b) == pytest.approx(20.0)


# --- downsample_mask ---------------------------------------------------------

def test_downsample_mask_zeros_top_right_box():
    f = np.full((100, 100), 200, dtype=np.uint8)
    masked = vi.downsample_mask(f, mask_top_frac=0.1, mask_right_frac=0.2)
    # Top-right box zeroed.
    assert masked[0:10, 80:100].sum() == 0
    # Bottom-left untouched.
    assert masked[50, 10] == 200
    # The original is not mutated.
    assert f[0, 99] == 200


def test_downsample_mask_disabled_when_frac_zero():
    f = np.full((10, 10), 7, dtype=np.uint8)
    out = vi.downsample_mask(f, mask_top_frac=0, mask_right_frac=0.2)
    assert np.array_equal(out, f)


def test_downsample_mask_defeats_corner_clock():
    # A frame that only changes in the top-right corner (a ticking clock) reads
    # as STATIC once masked.
    a = np.full((50, 50), 120, dtype=np.uint8)
    b = a.copy()
    b[0:5, 45:50] = 0  # clock changed
    diff_unmasked = vi.mean_abs_diff(a, b)
    diff_masked = vi.mean_abs_diff(
        vi.downsample_mask(a, mask_top_frac=0.12, mask_right_frac=0.12),
        vi.downsample_mask(b, mask_top_frac=0.12, mask_right_frac=0.12),
    )
    assert diff_unmasked > 0
    assert diff_masked == 0.0


# --- detect_idle_gaps --------------------------------------------------------

def test_detect_idle_gaps_cut_and_speedramp():
    # sample_fps=4 → each diff covers 0.25s.
    # Active (high diff) 0–1s, static 1–11s (10s → cut), active 11–12s,
    # static 12–15s (3s → speedramp), active 15–16s.
    fps = 4
    diffs = []
    diffs += [50] * 4          # 0.00–1.00 active
    diffs += [0] * 40          # 1.00–11.00 static (10s)
    diffs += [50] * 4          # 11.00–12.00 active
    diffs += [0] * 12          # 12.00–15.00 static (3s)
    diffs += [50] * 4          # 15.00–16.00 active
    gaps = vi.detect_idle_gaps(diffs, fps, pixel_diff_threshold=2.0,
                               speedramp_threshold=2.0, cut_threshold=8.0)
    assert len(gaps) == 2
    cut, ramp = gaps
    assert cut["kind"] == "cut"
    assert cut["start_s"] == pytest.approx(1.0)
    assert cut["end_s"] == pytest.approx(11.0)
    assert cut["duration_s"] == pytest.approx(10.0)
    assert ramp["kind"] == "speedramp"
    assert ramp["duration_s"] == pytest.approx(3.0)
    # Same shape as the cast idle_gaps (shared downstream logic).
    assert set(cut) == {"start_s", "end_s", "duration_s", "kind"}


def test_detect_idle_gaps_below_speedramp_threshold_ignored():
    # 1s static < speedramp_threshold 2s → no gap.
    diffs = [50, 0, 0, 0, 50]  # 1s static at 4fps
    assert vi.detect_idle_gaps(diffs, 4, speedramp_threshold=2.0, cut_threshold=8.0) == []


def test_detect_idle_gaps_all_static():
    diffs = [0] * 40  # 10s static @ 4fps
    gaps = vi.detect_idle_gaps(diffs, 4, cut_threshold=8.0)
    assert len(gaps) == 1 and gaps[0]["kind"] == "cut"
    assert gaps[0]["start_s"] == 0.0


def test_detect_idle_gaps_rejects_bad_fps():
    with pytest.raises(ValueError):
        vi.detect_idle_gaps([0, 0], 0)


def test_frame_diffs_length_and_values():
    frames = [np.zeros((2, 2), np.uint8),
              np.full((2, 2), 10, np.uint8),
              np.full((2, 2), 10, np.uint8)]
    d = vi.frame_diffs(frames)
    assert len(d) == 2
    assert d[0] == pytest.approx(10.0)
    assert d[1] == pytest.approx(0.0)
