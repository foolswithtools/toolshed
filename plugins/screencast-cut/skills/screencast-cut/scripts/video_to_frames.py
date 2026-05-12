#!/usr/bin/env python3
"""Detect idle stretches in a screen-recording MP4/MOV and emit a timing manifest.

Same downstream shape as `cast_to_frames.py`: the Remotion scene planner
treats the two timing manifests interchangeably. The difference is that
this script doesn't produce a PNG frame sequence — the renderer plays
the source MP4 directly via Remotion's `<OffthreadVideo>`, and idle
stretches are just timestamp ranges to speed-ramp or hard-cut.

Pipeline:
    .mp4 --[ffprobe: duration + dimensions]
         --[ffmpeg: fps, right-edge crop, freezedetect filter]
         --[parse freeze_start/_duration markers from stderr]
         --> timing.json

We use ffmpeg's `freezedetect` filter rather than sampling frames into
Python and computing pixel diffs — it does the same math natively and
is far faster on long inputs. The right-edge crop (default 40px) masks
out a ticking menubar clock or similar that would otherwise prevent
"static" detection on macOS recordings.

The freezedetect noise tolerance is expressed in dB:
    threshold_dB = 20 * log10(pixel_diff_threshold / 255)
Default pixel diff 2.0 → ~-42 dB. Lower threshold (more sensitive) means
smaller motion counts as still-frozen.

Usage:
    video_to_frames.py <input.mp4> <output_dir>
        [--sample-fps N]
        [--idle-speedramp SEC] [--idle-cut SEC]
        [--pixel-diff-threshold N]
        [--edge-mask-px N]

Outputs:
    <output_dir>/timing.json
        {
          "source_type": "video",
          "video_path": <absolute path>,
          "duration_s": float,
          "fps": float,
          "frame_count": int,
          "video_dimensions": {"w": int, "h": int},
          "idle_gaps": [{"start_s", "end_s", "duration_s", "kind"}, ...]
        }

Requires: `ffmpeg` and `ffprobe` on PATH.
"""

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path


FREEZE_START_RE = re.compile(r"lavfi\.freezedetect\.freeze_start: ([0-9.]+)")
FREEZE_DURATION_RE = re.compile(r"lavfi\.freezedetect\.freeze_duration: ([0-9.]+)")
FREEZE_END_RE = re.compile(r"lavfi\.freezedetect\.freeze_end: ([0-9.]+)")


def probe_video(path):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,nb_frames,duration",
        "-show_entries", "format=duration",
        "-of", "json",
        str(path),
    ]
    out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    data = json.loads(out)
    stream = (data.get("streams") or [{}])[0]
    fmt = data.get("format") or {}

    width = int(stream.get("width") or 0)
    height = int(stream.get("height") or 0)

    fr = stream.get("r_frame_rate") or "30/1"
    if "/" in fr:
        num, den = fr.split("/")
        fps = float(num) / float(den) if float(den) else 0.0
    else:
        fps = float(fr)

    duration = stream.get("duration") or fmt.get("duration") or 0
    duration = float(duration)

    frame_count = int(stream.get("nb_frames") or 0) or int(round(fps * duration))

    return {
        "width": width,
        "height": height,
        "fps": fps,
        "duration_s": duration,
        "frame_count": frame_count,
    }


def pixel_diff_to_db(threshold):
    """Convert a 0..255 pixel-diff threshold to ffmpeg freezedetect's dB form.

    0 dB == full scale (255). Smaller pixel-diff = lower dB (more sensitive).
    """
    if threshold <= 0:
        return -100.0
    return 20.0 * math.log10(threshold / 255.0)


def run_freezedetect(video_path, sample_fps, edge_mask_px, threshold_db,
                    min_idle_seconds):
    """Run ffmpeg with the freezedetect filter; return parsed freeze runs.

    Each run is a dict with start_s, end_s, duration_s. ffmpeg writes the
    metadata to stderr; we read it line-by-line and pair start with duration.
    """
    edge_mask_px = max(0, int(edge_mask_px))
    if edge_mask_px > 0:
        crop_filter = f"crop=iw-{edge_mask_px}:ih:0:0"
    else:
        crop_filter = "null"

    filter_chain = (
        f"fps={sample_fps},"
        f"{crop_filter},"
        f"freezedetect=n={threshold_db}dB:d={min_idle_seconds}"
    )

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-nostdin",
        "-i", str(video_path),
        "-vf", filter_chain,
        "-map", "0:v",
        "-f", "null",
        "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(
            f"ffmpeg freezedetect failed: {result.stderr.strip()[:500]}"
        )

    starts = []
    durations = []
    for line in result.stderr.splitlines():
        m = FREEZE_START_RE.search(line)
        if m:
            starts.append(float(m.group(1)))
            continue
        m = FREEZE_DURATION_RE.search(line)
        if m:
            durations.append(float(m.group(1)))

    runs = []
    for i, start in enumerate(starts):
        dur = durations[i] if i < len(durations) else None
        if dur is None or dur <= 0:
            continue
        runs.append({
            "start_s": round(start, 4),
            "end_s": round(start + dur, 4),
            "duration_s": round(dur, 4),
        })
    return runs


def classify_gaps(runs, speedramp_threshold, cut_threshold):
    """Tag each freeze run as kind=speedramp or kind=cut.

    `speedramp_threshold` is the floor for emitting anything (already
    applied by freezedetect's `d=` arg, but we re-filter defensively).
    `cut_threshold` is the upgrade point from speedramp to hard cut.
    """
    gaps = []
    for r in runs:
        if r["duration_s"] < speedramp_threshold:
            continue
        kind = "cut" if r["duration_s"] >= cut_threshold else "speedramp"
        gaps.append({**r, "kind": kind})
    return gaps


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--sample-fps", type=int, default=4,
                    help="Frames per second to feed freezedetect. Lower is faster.")
    ap.add_argument("--idle-speedramp", type=float, default=2.0,
                    help="Idle stretch >= this becomes a speed-ramp candidate.")
    ap.add_argument("--idle-cut", type=float, default=8.0,
                    help="Idle stretch >= this becomes a hard-cut candidate.")
    ap.add_argument("--pixel-diff-threshold", type=float, default=2.0,
                    help="Pixel diff (0..255) below which frames are considered static. "
                         "Mapped to dB internally for freezedetect.")
    ap.add_argument("--edge-mask-px", type=int, default=40,
                    help="Width in px of right-edge strip to ignore (menubar clock area). "
                         "Set to 0 to disable.")
    args = ap.parse_args(argv)

    if not args.video.is_file():
        raise SystemExit(f"not a file: {args.video}")
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            raise SystemExit(
                f"{tool} not found on PATH. On macOS: brew install ffmpeg"
            )
    if args.idle_cut < args.idle_speedramp:
        raise SystemExit(
            f"--idle-cut ({args.idle_cut}) must be >= --idle-speedramp "
            f"({args.idle_speedramp})"
        )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    probe = probe_video(args.video)

    threshold_db = pixel_diff_to_db(args.pixel_diff_threshold)
    runs = run_freezedetect(
        args.video,
        sample_fps=args.sample_fps,
        edge_mask_px=args.edge_mask_px,
        threshold_db=threshold_db,
        min_idle_seconds=args.idle_speedramp,
    )
    gaps = classify_gaps(runs, args.idle_speedramp, args.idle_cut)

    manifest = {
        "source_type": "video",
        "video_path": str(args.video.resolve()),
        "duration_s": round(probe["duration_s"], 4),
        "fps": round(probe["fps"], 4),
        "frame_count": probe["frame_count"],
        "video_dimensions": {"w": probe["width"], "h": probe["height"]},
        "idle_gaps": gaps,
        "detection": {
            "sample_fps": args.sample_fps,
            "edge_mask_px": args.edge_mask_px,
            "pixel_diff_threshold": args.pixel_diff_threshold,
            "threshold_db": round(threshold_db, 2),
        },
    }
    out_path = args.out_dir / "timing.json"
    out_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    n_speedramp = sum(1 for g in gaps if g["kind"] == "speedramp")
    n_cut = sum(1 for g in gaps if g["kind"] == "cut")
    print(f"timing:    {out_path}")
    print(f"duration:  {probe['duration_s']:.1f}s @ {probe['fps']:.1f}fps "
          f"({probe['width']}x{probe['height']})")
    print(f"idle gaps: {len(gaps)} ({n_cut} cuts, {n_speedramp} speed-ramps)")


if __name__ == "__main__":
    main(sys.argv[1:])
