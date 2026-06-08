#!/usr/bin/env python3
"""Detect idle stretches in a screen recording (.mp4/.mov) and emit a timing
manifest in the SAME `idle_gaps` shape as the terminal-cast path (Slice C).

Today the plugin auto-zooms MP4s on clicks but plays them full-speed. This adds
terminal-style idle-trim: long static stretches (reading a page, dwelling on a
result) become speed-ramp or hard-cut candidates the Remotion side trims exactly
like a cast idle gap.

How (resolved decisions): sample the video at a low fps, downsample each frame
to a small grayscale (done inside ffmpeg via `fps,scale,format=gray`), mask the
top-right menubar-clock box, then take the mean-absolute pixel diff between
adjacent samples. A run of sub-threshold (static) diffs that lasts long enough
is an idle gap. Mean-abs diff is the deliberate choice over SSIM — fast and good
enough; escalate to SSIM only if false positives bite.

Usage:
    video_to_frames.py <input.(mp4|mov)> <out_dir> [options]

Writes <out_dir>/timing.json:
    {
      "source_type": "video",
      "duration_s": float,
      "fps": int,                       # render fps (matches the cast path)
      "sample_fps": int,
      "sample_count": int,
      "idle_gaps": [{"start_s","end_s","duration_s","kind"}, ...],
      "video_path": "<absolute source path>",
      "video_dimensions": {"w": int, "h": int},
      "pixel_diff_threshold": float
    }

Options:
    --fps N                       render fps recorded in the manifest (default 30)
    --sample-fps N                idle-detection sample rate (default 4)
    --pixel-diff-threshold F      mean-abs diff (0..255) below which a frame pair
                                  is "static" (default 2.0)
    --idle-speedramp SEC          static stretch >= this → speed-ramp (default 2)
    --idle-cut SEC                static stretch >= this → hard cut (default 8)
    --mask-top-frac F             menubar-clock mask height fraction (default 0.08)
    --mask-right-frac F           menubar-clock mask width fraction (default 0.12)
    --sample-width / --sample-height   downsample size (default 256x144)

Requires: `ffmpeg` + `ffprobe` on PATH.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from video_idle import detect_idle_gaps, downsample_mask, frame_diffs
from schema_validate import validate, SchemaError


def probe_video(path):
    """Return (duration_s, fps, width, height) via ffprobe."""
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate",
        "-show_entries", "format=duration",
        "-of", "json", str(path),
    ]
    out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    data = json.loads(out)
    stream = (data.get("streams") or [{}])[0]
    width = int(stream.get("width") or 0)
    height = int(stream.get("height") or 0)
    rfr = stream.get("r_frame_rate") or "0/1"
    num, _, den = rfr.partition("/")
    src_fps = (float(num) / float(den)) if den and float(den) else 0.0
    duration = float((data.get("format") or {}).get("duration") or 0.0)
    return duration, src_fps, width, height


def sample_gray_frames(path, sample_fps, sample_w, sample_h):
    """Return an (N, h, w) uint8 array of downsampled grayscale samples.

    ffmpeg does the heavy lifting: `fps` resamples to `sample_fps`, `scale`
    downsamples, `format=gray` flattens to one channel; rawvideo to stdout.
    """
    vf = f"fps={sample_fps},scale={sample_w}:{sample_h},format=gray"
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-i", str(path),
        "-vf", vf,
        "-f", "rawvideo", "-pix_fmt", "gray", "-",
    ]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        raise SystemExit(
            f"ffmpeg failed to sample frames from {path}:\n"
            f"{proc.stderr.decode('utf-8', 'replace')}"
        )
    raw = proc.stdout
    frame_size = sample_w * sample_h
    if frame_size == 0 or len(raw) < frame_size:
        raise SystemExit(
            f"ffmpeg produced no usable frames from {path} "
            f"({len(raw)} bytes, frame size {frame_size})."
        )
    n = len(raw) // frame_size
    arr = np.frombuffer(raw[: n * frame_size], dtype=np.uint8)
    return arr.reshape(n, sample_h, sample_w)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--sample-fps", type=int, default=4)
    ap.add_argument("--pixel-diff-threshold", type=float, default=2.0)
    ap.add_argument("--idle-speedramp", type=float, default=2.0)
    ap.add_argument("--idle-cut", type=float, default=8.0)
    ap.add_argument("--mask-top-frac", type=float, default=0.08)
    ap.add_argument("--mask-right-frac", type=float, default=0.12)
    ap.add_argument("--sample-width", type=int, default=256)
    ap.add_argument("--sample-height", type=int, default=144)
    args = ap.parse_args(argv)

    if not args.video.is_file():
        raise SystemExit(f"not a file: {args.video}")
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            raise SystemExit(f"{tool} not found on PATH. On macOS: brew install ffmpeg")

    duration, _src_fps, width, height = probe_video(args.video)
    frames = sample_gray_frames(
        args.video, args.sample_fps, args.sample_width, args.sample_height
    )
    masked = [
        downsample_mask(
            f, mask_top_frac=args.mask_top_frac, mask_right_frac=args.mask_right_frac
        )
        for f in frames
    ]
    diffs = frame_diffs(masked)
    gaps = detect_idle_gaps(
        diffs,
        args.sample_fps,
        pixel_diff_threshold=args.pixel_diff_threshold,
        speedramp_threshold=args.idle_speedramp,
        cut_threshold=args.idle_cut,
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source_type": "video",
        "duration_s": round(duration, 4),
        "fps": args.fps,
        "sample_fps": args.sample_fps,
        "sample_count": int(len(frames)),
        "idle_gaps": gaps,
        "video_path": str(args.video.resolve()),
        "video_dimensions": {"w": width, "h": height},
        "pixel_diff_threshold": args.pixel_diff_threshold,
    }
    try:
        validate(manifest, "video_timing", what="timing.json")
    except SchemaError as e:
        raise SystemExit(str(e))

    (args.out_dir / "timing.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print(f"timing: {args.out_dir / 'timing.json'}")
    print(f"sampled {len(frames)} frames @ {args.sample_fps}fps; "
          f"idle gaps: {len(gaps)} "
          f"({sum(1 for g in gaps if g['kind']=='cut')} cuts, "
          f"{sum(1 for g in gaps if g['kind']=='speedramp')} speed-ramps)")


if __name__ == "__main__":
    main(sys.argv[1:])
