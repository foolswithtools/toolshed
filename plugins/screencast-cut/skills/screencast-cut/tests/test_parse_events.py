"""Tests for parse_events.py — manual + polyrecorder normalization, debounce,
clamping, formatVersion handling, and input validation. All pure (no tools)."""

import json
from pathlib import Path

import pytest

import parse_events as pe
from schema_validate import validate

FIXTURES = Path(__file__).resolve().parent / "fixtures"


# --- manual path -------------------------------------------------------------

def test_normalize_manual_debounce_and_clamp():
    out = pe.normalize_manual(FIXTURES / "manual-events.json", debounce_ms=250)
    validate(out, "zoom_anchors", what="zoom_anchors.json")
    # The 2.1s click is within 250ms of the 2.0s click → dropped.
    assert [a["label"] for a in out["anchors"]] == ["open", "run"]
    assert out["anchors"][0]["x"] == pytest.approx(0.3)
    assert out["duration_s"] == 20.0
    assert out["display"]["scale"] == 2


def test_normalize_manual_oob_coords_rejected(tmp_path):
    # The manual schema enforces 0..1, so an out-of-range coordinate is a
    # precise error (better than silently moving the user's click).
    f = tmp_path / "ev.json"
    f.write_text(json.dumps({
        "clicks": [{"t_s": 1.0, "x": 1.5, "y": -0.2, "label": "oob"}]
    }))
    with pytest.raises(SystemExit) as ei:
        pe.normalize_manual(f, debounce_ms=0)
    assert "x" in str(ei.value) or "y" in str(ei.value)


def test_normalize_polyrecorder_clamps_pixels(tmp_path):
    # Pixel coords beyond the display bounds normalize >1 and get clamped.
    rec = tmp_path / "recording"
    rec.mkdir()
    (rec / "metadata.json").write_text(json.dumps({
        "formatVersion": 2, "processTimeStartMs": 0,
        "display": {"widthPx": 1000, "heightPx": 1000}
    }))
    (rec / "mouseclicks-0.json").write_text(json.dumps([
        {"type": "mouseDown", "processTimeMs": 100, "x": 1200, "y": -50}
    ]))
    loaded = pe.load_polyrecorder(rec)
    out = pe.normalize_polyrecorder(loaded, debounce_ms=0)
    assert out["anchors"][0]["x"] == 1.0
    assert out["anchors"][0]["y"] == 0.0


def test_manual_missing_t_s_precise_error(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text(json.dumps({"clicks": [{"x": 0.4, "y": 0.6}]}))
    with pytest.raises(SystemExit) as ei:
        pe.normalize_manual(f, debounce_ms=0)
    assert "t_s" in str(ei.value)


# --- polyrecorder path -------------------------------------------------------

def test_normalize_polyrecorder_debounce_and_norm():
    rec = FIXTURES / "screenize-pkg" / "recording"
    loaded = pe.load_polyrecorder(rec)
    out = pe.normalize_polyrecorder(loaded, debounce_ms=250)
    validate(out, "zoom_anchors", what="zoom_anchors.json")
    assert out["source"] == "polyrecorder-v2"
    # 3 mouseDown events; the 3150ms one is within 250ms of 3000ms → dropped.
    assert [a["label"] for a in out["anchors"]] == ["Run", "Save"]
    # t0 = processTimeStartMs (1000). Run at 3000 → 2.0s; Save at 9000 → 8.0s.
    assert out["anchors"][0]["t_s"] == pytest.approx(2.0)
    assert out["anchors"][1]["t_s"] == pytest.approx(8.0)
    # 960/1920 = 0.5, 540/1080 = 0.5; 1536/1920 = 0.8, 216/1080 = 0.2.
    assert out["anchors"][0]["x"] == pytest.approx(0.5)
    assert out["anchors"][1]["x"] == pytest.approx(0.8)
    assert out["anchors"][1]["y"] == pytest.approx(0.2)
    assert out["duration_s"] == pytest.approx(20.0)


def test_polyrecorder_formatversion_mismatch(tmp_path):
    rec = tmp_path / "recording"
    rec.mkdir()
    (rec / "metadata.json").write_text(json.dumps({
        "formatVersion": 3, "display": {"widthPx": 1920, "heightPx": 1080}
    }))
    with pytest.raises(SystemExit) as ei:
        pe.load_polyrecorder(rec)
    assert "formatVersion" in str(ei.value)


def test_polyrecorder_missing_display_rejected(tmp_path):
    rec = tmp_path / "recording"
    rec.mkdir()
    (rec / "metadata.json").write_text(json.dumps({"formatVersion": 2}))
    with pytest.raises(SystemExit):
        pe.load_polyrecorder(rec)


# --- input detection ---------------------------------------------------------

def test_detect_input_polyrecorder_root():
    kind, target = pe.detect_input(FIXTURES / "screenize-pkg")
    assert kind == "polyrecorder"
    assert target.name == "recording"


def test_detect_input_manual_file():
    kind, target = pe.detect_input(FIXTURES / "manual-events.json")
    assert kind == "manual"
