"""Tests for cast_to_frames.py — pure parsing/gap logic always; full pipeline
(agg+ffmpeg) tool-gated."""

import json
from pathlib import Path

import pytest

import cast_to_frames as c2f
from schema_validate import validate

FIXTURES = Path(__file__).resolve().parent / "fixtures"


# --- parse_cast --------------------------------------------------------------

def test_parse_v1():
    header, events = c2f.parse_cast(FIXTURES / "sample-v1.cast")
    assert header["version"] == 1
    assert events == [
        (0.5, "o", "hello "),
        (1.0, "o", "world\r\n"),
        (2.0, "o", "done\r\n"),
    ]


def test_parse_v2_and_v3_same_recording_equal():
    _, ev2 = c2f.parse_cast(FIXTURES / "sample-v2.cast")
    _, ev3 = c2f.parse_cast(FIXTURES / "sample-v3.cast")
    assert len(ev2) == len(ev3)
    for (t2, code2, data2), (t3, code3, data3) in zip(ev2, ev3):
        assert code2 == code3
        assert data2 == data3
        # v3 cumulative intervals must reconstruct v2 absolute times.
        assert t2 == pytest.approx(t3, abs=1e-6)


def test_parse_rejects_unsupported_version(tmp_path):
    bad = tmp_path / "v4.cast"
    bad.write_text('{"version": 4, "width": 80, "height": 24}\n[0.1, "o", "x"]\n')
    with pytest.raises(SystemExit):
        c2f.parse_cast(bad)


def test_parse_empty_file_rejected(tmp_path):
    empty = tmp_path / "empty.cast"
    empty.write_text("\n  \n")
    with pytest.raises(SystemExit):
        c2f.parse_cast(empty)


# --- find_idle_gaps ----------------------------------------------------------

def test_idle_gaps_boundary():
    _, events = c2f.parse_cast(FIXTURES / "idle.cast")
    gaps = c2f.find_idle_gaps(events, speedramp_threshold=2.0, cut_threshold=8.0)
    assert len(gaps) == 2
    assert gaps[0]["kind"] == "speedramp"
    assert gaps[0]["duration_s"] == pytest.approx(2.5, abs=1e-6)
    assert gaps[1]["kind"] == "cut"
    assert gaps[1]["duration_s"] == pytest.approx(9.0, abs=1e-6)


def test_idle_gaps_exact_threshold_is_inclusive():
    # gap exactly == speedramp_threshold should count (>=).
    events = [(0.0, "o", "a"), (2.0, "o", "b")]
    gaps = c2f.find_idle_gaps(events, 2.0, 8.0)
    assert len(gaps) == 1 and gaps[0]["kind"] == "speedramp"


def test_empty_output_has_no_gaps():
    _, events = c2f.parse_cast(FIXTURES / "empty-output.cast")
    assert c2f.find_idle_gaps(events, 2.0, 8.0) == []
    assert sum(1 for (_, code, _) in events if code == "o") == 0


def test_sample_v2_gaps_one_speedramp_one_cut():
    _, events = c2f.parse_cast(FIXTURES / "sample-v2.cast")
    gaps = c2f.find_idle_gaps(events, 2.0, 8.0)
    kinds = sorted(g["kind"] for g in gaps)
    assert kinds == ["cut", "speedramp"]


# --- find_fumble_regions -----------------------------------------------------

def _typed(t, ch):
    return (t, "i", ch)


def test_fumble_basic_backspace_run():
    # Type "ehco", backspace x4, retype "echo".
    events = [
        (0.5, "o", "$ "),
        _typed(1.0, "e"), _typed(1.2, "h"), _typed(1.4, "c"), _typed(1.6, "o"),
        _typed(2.0, "\x7f"), _typed(2.1, "\x7f"), _typed(2.2, "\x7f"), _typed(2.3, "\x7f"),
        _typed(2.8, "e"), _typed(3.0, "c"), _typed(3.2, "h"), _typed(3.4, "o"),
        _typed(4.0, "\r"),
    ]
    regions = c2f.find_fumble_regions(events, min_backspaces=3)
    assert len(regions) == 1
    r = regions[0]
    assert r["kind"] == "fumble"
    assert r["start_s"] == pytest.approx(1.0)   # start of the mistyped line
    assert r["end_s"] == pytest.approx(2.8)     # first recovery keystroke
    assert r["duration_s"] == pytest.approx(1.8)
    assert r["backspaces"] == 4
    assert r["triggers"] == ["backspace"]


def test_fumble_below_threshold_ignored():
    events = [
        _typed(1.0, "a"), _typed(1.2, "b"),
        _typed(2.0, "\x7f"), _typed(2.1, "\x7f"),  # only 2 backspaces
        _typed(2.8, "c"),
    ]
    assert c2f.find_fumble_regions(events, min_backspaces=3) == []


def test_fumble_backspaces_split_across_events_or_packed():
    # 3 backspaces packed into one event still trips the threshold.
    events = [_typed(1.0, "x"), _typed(1.5, "\x7f\x7f\x7f"), _typed(2.0, "y")]
    regions = c2f.find_fumble_regions(events, min_backspaces=3)
    assert len(regions) == 1
    assert regions[0]["backspaces"] == 3


def test_fumble_ctrl_w_triggers_regardless_of_count():
    # A single Ctrl-W (kill-word) is a fumble trigger even though backspaces < 3.
    events = [_typed(1.0, "f"), _typed(1.2, "o"), _typed(1.4, "o"),
              _typed(2.0, "\x17"), _typed(2.6, "b"), _typed(2.8, "a"), _typed(3.0, "r")]
    regions = c2f.find_fumble_regions(events, min_backspaces=3)
    assert len(regions) == 1
    assert regions[0]["triggers"] == ["kill-word"]
    assert regions[0]["backspaces"] == 0
    assert regions[0]["start_s"] == pytest.approx(1.0)
    assert regions[0]["end_s"] == pytest.approx(2.6)


def test_fumble_ctrl_u_triggers():
    events = [_typed(1.0, "g"), _typed(1.2, "i"), _typed(1.4, "t"),
              _typed(2.0, "\x15"), _typed(2.5, "l"), _typed(2.7, "s")]
    regions = c2f.find_fumble_regions(events, min_backspaces=3)
    assert len(regions) == 1
    assert regions[0]["triggers"] == ["kill-line"]


def test_fumble_mixed_triggers_sorted_unique():
    events = [_typed(1.0, "a"), _typed(1.2, "b"),
              _typed(2.0, "\x7f\x7f\x7f"), _typed(2.1, "\x17"),
              _typed(2.8, "c")]
    regions = c2f.find_fumble_regions(events, min_backspaces=3)
    assert len(regions) == 1
    assert regions[0]["triggers"] == ["backspace", "kill-word"]
    assert regions[0]["backspaces"] == 3


def test_fumble_no_input_events_returns_empty():
    # A cast recorded without stdin has no `i` events.
    _, events = c2f.parse_cast(FIXTURES / "sample-v2.cast")
    assert c2f.find_fumble_regions(events) == []


def test_fumble_anchors_start_after_previous_enter():
    # A clean prior command must not bleed into the fumble's start.
    events = [
        _typed(0.5, "l"), _typed(0.6, "s"), _typed(0.7, "\r"),  # prior command
        _typed(1.0, "e"), _typed(1.2, "h"), _typed(1.4, "c"), _typed(1.6, "o"),
        _typed(2.0, "\x7f"), _typed(2.1, "\x7f"), _typed(2.2, "\x7f"),
        _typed(2.8, "e"),
    ]
    regions = c2f.find_fumble_regions(events, min_backspaces=3)
    assert len(regions) == 1
    assert regions[0]["start_s"] == pytest.approx(1.0)  # not 0.5


def test_fumble_two_rounds_merge():
    # Type, delete, retype, delete again, recover — one merged region.
    events = [
        _typed(1.0, "a"), _typed(1.2, "b"), _typed(1.4, "c"),
        _typed(2.0, "\x7f"), _typed(2.1, "\x7f"), _typed(2.2, "\x7f"),
        _typed(2.6, "x"), _typed(2.8, "y"),
        _typed(3.2, "\x7f"), _typed(3.3, "\x7f"), _typed(3.4, "\x7f"),
        _typed(3.9, "z"),
    ]
    regions = c2f.find_fumble_regions(events, min_backspaces=3)
    assert len(regions) == 1
    assert regions[0]["start_s"] == pytest.approx(1.0)
    assert regions[0]["end_s"] == pytest.approx(3.9)
    assert regions[0]["backspaces"] == 6


# --- full pipeline (tool-gated) ----------------------------------------------

def test_full_pipeline_clock_drift_invariants(agg_available, tmp_path):
    out = tmp_path / "out"
    c2f.main([
        str(FIXTURES / "sample-v2.cast"),
        str(out),
        "--fps", "30",
        "--idle-speedramp", "2",
        "--idle-cut", "8",
    ])
    manifest = json.loads((out / "timing.json").read_text())

    # Contract: validates against its own schema.
    validate(manifest, "timing", what="timing.json")

    pngs = sorted((out / "frames").glob("*.png"))
    # Invariant 1: PNG count == frame_count == png_count.
    assert len(pngs) == manifest["frame_count"] == manifest["png_count"]
    # Invariant 2: frame_times_s strictly non-decreasing.
    ft = manifest["frame_times_s"]
    assert ft == sorted(ft)
    # Invariant 3: last frame time ~ cast duration (our agg idle fix → ~0 drift).
    assert ft[-1] == pytest.approx(manifest["duration_s"], abs=max(0.5, 0.02 * manifest["duration_s"]))
    assert manifest["clock_drift_s"] <= max(0.5, 0.02 * manifest["duration_s"])
    # Gap frame indices are within the PNG range.
    for g in manifest["idle_gaps"]:
        assert 0 <= g["start_frame"] < len(pngs)
        assert 0 <= g["end_frame"] < len(pngs)


def test_full_pipeline_emits_fumble_regions(agg_available, tmp_path):
    out = tmp_path / "out"
    c2f.main([
        str(FIXTURES / "fumble.cast"), str(out),
        "--fps", "30", "--fumble-min-backspaces", "3",
    ])
    manifest = json.loads((out / "timing.json").read_text())
    validate(manifest, "timing", what="timing.json")

    assert "fumble_regions" in manifest
    assert len(manifest["fumble_regions"]) == 1
    f = manifest["fumble_regions"][0]
    assert f["kind"] == "fumble"
    assert f["backspaces"] >= 3
    assert f["triggers"] == ["backspace"]
    # Frame indices land inside the PNG range and span forward.
    pngs = sorted((out / "frames").glob("*.png"))
    assert 0 <= f["start_frame"] < f["end_frame"] < len(pngs)
