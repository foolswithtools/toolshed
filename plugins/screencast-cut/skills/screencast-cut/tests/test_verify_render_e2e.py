"""End-to-end gate: bundle + render the committed golden Remotion project for
real and assert the verifier passes.

Needs node + npm (the `golden_installed` fixture runs `npm ci` once; it skips if
node/npm are absent or the install fails). node_modules is NOT committed.
"""

import json
from pathlib import Path

import pytest

import verify_render as vr

EXPECTED_DURATION = 250
WIDTH, HEIGHT = 1920, 1080
FPS = 30
# Offsets matching the golden-cut layout (intro card is 45 frames).
TRANSCRIPT_START = 45
TERMINAL_START = 45
MAX_STILLS = 10


def _load(path):
    return json.loads(Path(path).read_text())


def test_golden_cut_renders_and_verifies(golden_installed):
    project = golden_installed
    rc = vr.main([
        str(project), "golden-cut",
        "--expect-duration-frames", str(EXPECTED_DURATION),
        "--expect-width", str(WIDTH),
        "--expect-height", str(HEIGHT),
        "--scale", "0.5",
        "--max-stills", str(MAX_STILLS),
        "--transcript-start-frame", str(TRANSCRIPT_START),
        "--terminal-start-frame", str(TERMINAL_START),
    ])
    assert rc == 0, "verify_render did not exit 0 on the golden project"

    summary = _load(project / "videos" / "golden-cut" / ".checks" / "verify-summary.json")
    assert summary["status"] == "pass"
    assert summary["gates"]["bundle"]["pass"]
    assert summary["gates"]["composition_exists"]["pass"]
    assert summary["gates"]["dimensions"]["pass"]
    assert summary["gates"]["duration"]["pass"]
    assert summary["gates"]["duration"]["actual"] == EXPECTED_DURATION
    assert summary["gates"]["stills_render"]["pass"]
    assert summary["gates"]["stills_render"]["count"] > 0

    # Every still rendered ok.
    assert all(s["rendered"] for s in summary["filmstrip"]), \
        "a filmstrip still failed to render"

    # The filmstrip index set must equal the deterministic set computed from the
    # committed manifests — proving the verifier is reproducible, not ad hoc.
    timing = _load(project / "videos" / "golden-cut" / "source" / "timing.json")
    transcript = _load(project / "videos" / "golden-cut" / "source" / "transcript.json")
    expected = vr.compute_filmstrip_frames(
        EXPECTED_DURATION,
        FPS,
        timing=timing,
        transcript=transcript,
        zoom=None,
        transcript_start_frame=TRANSCRIPT_START,
        terminal_start_frame=TERMINAL_START,
        max_stills=MAX_STILLS,
    )
    expected_frames = sorted(e["frame"] for e in expected)
    actual_frames = sorted(s["frame"] for s in summary["filmstrip"])
    assert actual_frames == expected_frames


def test_golden_cut_mp4_zoomed_section_renders(golden_installed):
    """The MP4/ZoomedSection variant also bundles and renders (SafeVideo +
    clampZoomWindow path)."""
    project = golden_installed
    rc = vr.main([
        str(project), "golden-cut-mp4",
        "--expect-duration-frames", "195",
        "--expect-width", str(WIDTH),
        "--expect-height", str(HEIGHT),
        "--scale", "0.4",
        "--max-stills", "6",
        "--video-start-frame", "45",
    ])
    assert rc == 0
    summary = _load(project / "videos" / "golden-cut-mp4" / ".checks" / "verify-summary.json")
    assert summary["status"] == "pass"
    assert all(s["rendered"] for s in summary["filmstrip"])


# golden-icons: the animated-icon showcase. Curated local icons only (no
# network), every recipe + the ClickRipple, recolored to the brand accent.
GOLDEN_ICONS_DURATION = 120
GOLDEN_ICONS_MAX_STILLS = 8

# golden-lottie: the bring-your-own Lottie showcase. An owned, expression-free
# fixture rendered through @remotion/lottie (staticFile → fetch behind
# delayRender), proving the BYO path renders deterministically headlessly.
GOLDEN_LOTTIE_DURATION = 60
GOLDEN_LOTTIE_MAX_STILLS = 6


def test_golden_icons_renders_and_verifies(golden_installed):
    """Every motion recipe + the ClickRipple bundle and render for real, and the
    filmstrip frame set is reproducible from the committed zoom_anchors.json."""
    project = golden_installed
    rc = vr.main([
        str(project), "golden-icons",
        "--expect-duration-frames", str(GOLDEN_ICONS_DURATION),
        "--expect-width", str(WIDTH),
        "--expect-height", str(HEIGHT),
        "--scale", "0.5",
        "--max-stills", str(GOLDEN_ICONS_MAX_STILLS),
        "--video-start-frame", "0",
    ])
    assert rc == 0, "verify_render did not exit 0 on golden-icons"

    summary = _load(project / "videos" / "golden-icons" / ".checks" / "verify-summary.json")
    assert summary["status"] == "pass"
    assert summary["gates"]["bundle"]["pass"]
    assert summary["gates"]["composition_exists"]["pass"]
    assert summary["gates"]["dimensions"]["pass"]
    assert summary["gates"]["duration"]["pass"]
    assert summary["gates"]["duration"]["actual"] == GOLDEN_ICONS_DURATION
    assert summary["gates"]["stills_render"]["pass"]
    assert summary["gates"]["stills_render"]["count"] > 0
    assert all(s["rendered"] for s in summary["filmstrip"]), \
        "a golden-icons filmstrip still failed to render"

    # The ripple anchors must drive the filmstrip set deterministically.
    zoom = _load(project / "videos" / "golden-icons" / "source" / "zoom_anchors.json")
    expected = vr.compute_filmstrip_frames(
        GOLDEN_ICONS_DURATION,
        FPS,
        timing=None,
        transcript=None,
        zoom=zoom,
        video_start_frame=0,
        max_stills=GOLDEN_ICONS_MAX_STILLS,
    )
    expected_frames = sorted(e["frame"] for e in expected)
    actual_frames = sorted(s["frame"] for s in summary["filmstrip"])
    assert actual_frames == expected_frames
    # Both committed anchors appear as zoom-labelled sample frames.
    zoom_labels = {e.get("zoom") for e in expected}
    assert {"ripple-left", "ripple-right"} <= zoom_labels


# golden-tts: the Slice A (TTS) showcase. A cut whose narration came from a
# Script: input — script_to_audio.py turned source/script.md into the committed
# OWNED fixture WAV, so this renders for real without ever calling ElevenLabs.
GOLDEN_TTS_DURATION = 255
GOLDEN_TTS_MAX_STILLS = 8
GOLDEN_TTS_TRANSCRIPT_START = 45


def test_golden_tts_renders_and_verifies(golden_installed):
    """The Script:-driven narration path bundles and renders for real: the OWNED
    fixture narration.wav rides through SafeAudio and the committed transcript
    drives the caption band. The filmstrip frame set is reproducible from the
    committed transcript.json."""
    project = golden_installed
    rc = vr.main([
        str(project), "golden-tts",
        "--expect-duration-frames", str(GOLDEN_TTS_DURATION),
        "--expect-width", str(WIDTH),
        "--expect-height", str(HEIGHT),
        "--scale", "0.5",
        "--max-stills", str(GOLDEN_TTS_MAX_STILLS),
        "--transcript-start-frame", str(GOLDEN_TTS_TRANSCRIPT_START),
    ])
    assert rc == 0, "verify_render did not exit 0 on golden-tts"

    summary = _load(project / "videos" / "golden-tts" / ".checks" / "verify-summary.json")
    assert summary["status"] == "pass"
    assert summary["gates"]["bundle"]["pass"]
    assert summary["gates"]["composition_exists"]["pass"]
    assert summary["gates"]["dimensions"]["pass"]
    assert summary["gates"]["duration"]["pass"]
    assert summary["gates"]["duration"]["actual"] == GOLDEN_TTS_DURATION
    assert summary["gates"]["stills_render"]["pass"]
    assert all(s["rendered"] for s in summary["filmstrip"]), \
        "a golden-tts filmstrip still failed to render"

    # The transcript must drive the filmstrip set deterministically.
    transcript = _load(project / "videos" / "golden-tts" / "source" / "transcript.json")
    expected = vr.compute_filmstrip_frames(
        GOLDEN_TTS_DURATION,
        FPS,
        timing=None,
        transcript=transcript,
        zoom=None,
        transcript_start_frame=GOLDEN_TTS_TRANSCRIPT_START,
        max_stills=GOLDEN_TTS_MAX_STILLS,
    )
    expected_frames = sorted(e["frame"] for e in expected)
    actual_frames = sorted(s["frame"] for s in summary["filmstrip"])
    assert actual_frames == expected_frames


def test_golden_tts_narration_fixture_is_owned_and_valid(golden_dir):
    """Guard the Slice A fixtures: the narration WAV is committed with a
    PROVENANCE note (OWNED, never ElevenLabs output) and the manifest validates
    against the narration schema — and the manifest never embeds a token."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    from schema_validate import validate

    wav = golden_dir / "public" / "golden-tts" / "narration.wav"
    prov = golden_dir / "public" / "golden-tts" / "PROVENANCE"
    manifest_path = golden_dir / "videos" / "golden-tts" / "source" / "narration.manifest.json"

    assert wav.is_file() and wav.stat().st_size > 0, "owned narration.wav fixture missing"
    assert prov.is_file(), "narration.wav needs a PROVENANCE note (OWNED/CC0)"
    prov_text = prov.read_text()
    assert "OWNED" in prov_text and "NOT ElevenLabs" in prov_text

    manifest = _load(manifest_path)
    validate(manifest, "narration", what="narration.manifest.json")
    assert manifest["provider"] == "elevenlabs"
    assert manifest["characters_used"] > 0
    body = manifest_path.read_text().lower()
    assert "token" not in body and "xi-api-key" not in body


# golden-fumble: the Slice B (fumble detection) showcase. A cast with a
# backspace fumble that gets cut — the fumble_regions[0] stretch (cast 1.0→3.6)
# is dropped like an idle_cut (IdleCutCard), so the rendered video skips the
# mistype and resumes on the corrected command.
GOLDEN_FUMBLE_DURATION = 246
GOLDEN_FUMBLE_MAX_STILLS = 8
GOLDEN_FUMBLE_TERMINAL_START = 45


def test_golden_fumble_renders_and_verifies(golden_installed):
    project = golden_installed
    rc = vr.main([
        str(project), "golden-fumble",
        "--expect-duration-frames", str(GOLDEN_FUMBLE_DURATION),
        "--expect-width", str(WIDTH),
        "--expect-height", str(HEIGHT),
        "--scale", "0.5",
        "--max-stills", str(GOLDEN_FUMBLE_MAX_STILLS),
        "--terminal-start-frame", str(GOLDEN_FUMBLE_TERMINAL_START),
    ])
    assert rc == 0, "verify_render did not exit 0 on golden-fumble"

    summary = _load(project / "videos" / "golden-fumble" / ".checks" / "verify-summary.json")
    assert summary["status"] == "pass"
    assert summary["gates"]["duration"]["actual"] == GOLDEN_FUMBLE_DURATION
    assert summary["gates"]["stills_render"]["pass"]
    assert all(s["rendered"] for s in summary["filmstrip"]), \
        "a golden-fumble filmstrip still failed to render"


def test_golden_fumble_timing_has_detected_fumble(golden_dir):
    """Guard the Slice B fixture: the committed timing.json carries exactly the
    detected fumble region, validated against the (updated) timing schema."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    from schema_validate import validate

    timing = _load(golden_dir / "videos" / "golden-fumble" / "source" / "timing.json")
    validate(timing, "timing", what="timing.json")
    assert len(timing["fumble_regions"]) == 1
    f = timing["fumble_regions"][0]
    assert f["kind"] == "fumble"
    assert f["backspaces"] >= 3
    assert f["start_frame"] < f["end_frame"]


def test_golden_lottie_renders_and_verifies(golden_installed):
    """The bring-your-own Lottie path bundles and renders for real: the owned,
    expression-free fixture loads via staticFile → fetch behind delayRender and
    renders deterministically through @remotion/lottie."""
    project = golden_installed
    rc = vr.main([
        str(project), "golden-lottie",
        "--expect-duration-frames", str(GOLDEN_LOTTIE_DURATION),
        "--expect-width", str(WIDTH),
        "--expect-height", str(HEIGHT),
        "--scale", "0.5",
        "--max-stills", str(GOLDEN_LOTTIE_MAX_STILLS),
    ])
    assert rc == 0, "verify_render did not exit 0 on golden-lottie"

    summary = _load(project / "videos" / "golden-lottie" / ".checks" / "verify-summary.json")
    assert summary["status"] == "pass"
    assert summary["gates"]["bundle"]["pass"]
    assert summary["gates"]["composition_exists"]["pass"]
    assert summary["gates"]["duration"]["pass"]
    assert summary["gates"]["duration"]["actual"] == GOLDEN_LOTTIE_DURATION
    assert summary["gates"]["stills_render"]["pass"]
    assert summary["gates"]["stills_render"]["count"] > 0
    assert all(s["rendered"] for s in summary["filmstrip"]), \
        "a golden-lottie filmstrip still failed to render"
