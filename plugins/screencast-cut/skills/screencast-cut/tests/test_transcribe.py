"""Tests for transcribe.py — the pure reshape() of whisper.cpp JSON into our
schema (word merging, trailing-punctuation join, ms→s). No whisper needed."""

import json
from pathlib import Path

import pytest

import transcribe as tr
from schema_validate import validate

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_reshape_words_and_ms_conversion():
    raw = json.loads((FIXTURES / "whisper-raw.json").read_text())
    out = tr.reshape(raw)
    validate(out, "transcript", what="transcript.json")

    assert out["language"] == "en"
    assert out["model"] == "base.en"
    assert len(out["segments"]) == 2

    seg0 = out["segments"][0]
    # Special tokens dropped; " Hello" / " world" become words; "." merges onto
    # "world" → "world." with end extended.
    assert [w["text"] for w in seg0["words"]] == ["Hello", "world."]
    assert seg0["words"][0]["start_s"] == pytest.approx(0.0)
    assert seg0["words"][0]["end_s"] == pytest.approx(0.4)
    assert seg0["words"][1]["text"] == "world."
    assert seg0["words"][1]["end_s"] == pytest.approx(1.2)  # ms 1200 → 1.2s

    seg1 = out["segments"][1]
    assert [w["text"] for w in seg1["words"]] == ["Tests", "passed."]
    assert seg1["words"][0]["start_s"] == pytest.approx(1.2)

    # Duration = last segment end (2500ms → 2.5s).
    assert out["duration_s"] == pytest.approx(2.5)


def test_reshape_empty_transcription():
    out = tr.reshape({"transcription": [], "result": {"language": "en"}})
    assert out["segments"] == []
    assert out["duration_s"] == 0.0
