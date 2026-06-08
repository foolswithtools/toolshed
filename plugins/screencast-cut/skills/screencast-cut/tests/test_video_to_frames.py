"""Full-pipeline test for video_to_frames.py — ffmpeg-gated.

Synthesizes a tiny active→static→active MP4 with ffmpeg, runs the detector, and
asserts it finds the static stretch as an idle gap and the manifest validates
against the video_timing schema.
"""

import json
import subprocess
from pathlib import Path

import video_to_frames as v2f
from schema_validate import validate


def _make_video(path, *, active1=1, static=10, active2=1, size="320x180"):
    """active1s of motion, static s of a flat colour, active2s of motion."""
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "lavfi", "-t", str(active1), "-i", f"testsrc2=s={size}:r=30",
         "-f", "lavfi", "-t", str(static), "-i", f"color=c=0x1c2230:s={size}:r=30",
         "-f", "lavfi", "-t", str(active2), "-i", f"testsrc2=s={size}:r=30",
         "-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]",
         "-map", "[v]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
         str(path)],
        check=True,
    )


def test_detects_static_stretch_and_validates(tmp_path, ffmpeg_available):
    video = tmp_path / "rec.mp4"
    _make_video(video, active1=1, static=10, active2=1)
    out = tmp_path / "out"
    v2f.main([
        str(video), str(out),
        "--fps", "30", "--sample-fps", "4",
        "--idle-speedramp", "2", "--idle-cut", "8",
    ])
    manifest = json.loads((out / "timing.json").read_text())
    validate(manifest, "video_timing", what="timing.json")

    assert manifest["source_type"] == "video"
    assert manifest["duration_s"] == 12.0 or abs(manifest["duration_s"] - 12.0) < 0.2
    assert manifest["video_dimensions"] == {"w": 320, "h": 180}
    # The 10s static middle is a single cut gap.
    cuts = [g for g in manifest["idle_gaps"] if g["kind"] == "cut"]
    assert len(cuts) == 1
    cut = cuts[0]
    assert cut["start_s"] >= 0.9 and cut["start_s"] <= 1.5  # ~1s in
    assert cut["duration_s"] >= 8.0


def test_golden_video_idle_regenerates_to_committed_timing(tmp_path, ffmpeg_available):
    """Tie detection to the committed golden fixture the composition cuts on:
    re-running video_to_frames on the committed source.mp4 must reproduce the
    golden-video-idle idle_gaps EXACTLY, so the cut/ramp can't silently drift
    from what the detector actually finds (cf. the Slice B fumble tie)."""
    here = Path(__file__).resolve().parent
    mp4 = (here / "fixtures" / "golden-project" / "public" / "golden-video-idle"
           / "source.mp4")
    committed = json.loads(
        (here / "fixtures" / "golden-project" / "videos" / "golden-video-idle"
         / "source" / "timing.json").read_text()
    )
    out = tmp_path / "out"
    v2f.main([str(mp4), str(out)])
    gen = json.loads((out / "timing.json").read_text())
    assert gen["idle_gaps"] == committed["idle_gaps"], (
        "idle_gaps regenerated from the golden source.mp4 differ from the "
        "committed golden-video-idle timing.json the composition cuts on"
    )


def test_short_static_is_speedramp_not_cut(tmp_path, ffmpeg_available):
    video = tmp_path / "rec.mp4"
    _make_video(video, active1=1, static=3, active2=1)
    out = tmp_path / "out"
    v2f.main([str(video), str(out), "--sample-fps", "4",
              "--idle-speedramp", "2", "--idle-cut", "8"])
    manifest = json.loads((out / "timing.json").read_text())
    kinds = [g["kind"] for g in manifest["idle_gaps"]]
    assert "speedramp" in kinds
    assert "cut" not in kinds
