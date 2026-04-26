#!/usr/bin/env python3
"""Render an asciinema .cast file to a PNG sequence + timing manifest.

Pipeline:
    .cast --[agg]--> intermediate.gif --[ffmpeg]--> frames/00001.png ...

We don't write our own VT/terminal renderer — `agg` (asciinema's official
Rust renderer) handles cast v1/v2/v3, font shaping, and theming. ffmpeg
explodes the GIF into a PNG sequence preserving per-frame timing.

Idle-gap detection runs against the cast event stream directly so the
timing is exact (GIF frame quantization would lose sub-frame precision).

Usage:
    cast_to_frames.py <input.cast> <output_dir> [--fps N] [--theme NAME]
                                                [--font-size N]
                                                [--idle-speedramp SEC]
                                                [--idle-cut SEC]

Outputs:
    <output_dir>/frames/00001.png ...
    <output_dir>/timing.json
        {
          "cast_version": 2 | 3,
          "duration_s": float,
          "fps": int,
          "frame_count": int,
          "frame_times_s": [float, ...],     # cast-time of each PNG
          "idle_gaps": [{"start_s", "end_s", "duration_s"}, ...],
          "events_summary": {"output_count": int, "input_count": int}
        }

Requires: `agg` and `ffmpeg` on PATH. `brew install agg ffmpeg` on macOS.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def parse_cast(cast_path):
    """Return (header, events) where events is a list of (t_abs, code, data).

    Auto-detects v2 (absolute timestamps in event[0]) vs v3 (intervals).
    Both share the NDJSON shape: line 1 = header object, rest = arrays.
    """
    raw_lines = cast_path.read_text(encoding="utf-8").splitlines()
    lines = [ln for ln in raw_lines if ln.strip()]
    if not lines:
        raise SystemExit(f"empty cast: {cast_path}")

    header = json.loads(lines[0])
    version = header.get("version")
    if version not in (1, 2, 3):
        raise SystemExit(f"unsupported cast version: {version!r}")

    events = []
    if version == 1:
        # v1 stored events under header["stdout"] as [delay, data] pairs.
        t = 0.0
        for ev in header.get("stdout", []):
            t += float(ev[0])
            events.append((t, "o", ev[1]))
        return header, events

    if version == 2:
        for line in lines[1:]:
            ev = json.loads(line)
            events.append((float(ev[0]), str(ev[1]), ev[2]))
        return header, events

    # v3: first element is interval since previous event.
    t = 0.0
    for line in lines[1:]:
        ev = json.loads(line)
        t += float(ev[0])
        events.append((t, str(ev[1]), ev[2]))
    return header, events


def find_idle_gaps(events, speedramp_threshold, cut_threshold):
    """Idle gap = stretch with no `o` (output) event for >= threshold seconds.

    Returns list of {"start_s", "end_s", "duration_s", "kind"}.
    `kind` is "speedramp" if speedramp_threshold <= dur < cut_threshold,
    else "cut".
    """
    output_times = [t for (t, code, _) in events if code == "o"]
    if not output_times:
        return []

    gaps = []
    prev = output_times[0]
    for t in output_times[1:]:
        dur = t - prev
        if dur >= speedramp_threshold:
            kind = "cut" if dur >= cut_threshold else "speedramp"
            gaps.append({
                "start_s": round(prev, 4),
                "end_s": round(t, 4),
                "duration_s": round(dur, 4),
                "kind": kind,
            })
        prev = t
    return gaps


def total_duration(events):
    if not events:
        return 0.0
    return float(events[-1][0])


def render_with_agg(cast_path, gif_path, theme, font_size, fps):
    cmd = [
        "agg",
        "--theme", theme,
        "--font-size", str(font_size),
        "--fps-cap", str(fps),
        str(cast_path),
        str(gif_path),
    ]
    subprocess.run(cmd, check=True)


def explode_to_pngs(gif_path, frames_dir):
    frames_dir.mkdir(parents=True, exist_ok=True)
    # -fps_mode passthrough preserves the GIF's per-frame delays — one PNG
    # per source GIF frame, no resampling.
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(gif_path),
        "-fps_mode", "passthrough",
        str(frames_dir / "%05d.png"),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def probe_frame_times(gif_path):
    """Return per-frame cumulative timestamp in seconds (matches PNG order)."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "frame=pkt_pts_time,best_effort_timestamp_time",
        "-of", "json",
        str(gif_path),
    ]
    out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    data = json.loads(out)
    times = []
    for fr in data.get("frames", []):
        t = fr.get("best_effort_timestamp_time") or fr.get("pkt_pts_time")
        if t is None:
            continue
        times.append(round(float(t), 4))
    return times


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cast", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--theme", default="monokai")
    ap.add_argument("--font-size", type=int, default=14)
    ap.add_argument("--idle-speedramp", type=float, default=2.0,
                    help="Idle gap >= this many seconds becomes a speed-ramp candidate.")
    ap.add_argument("--idle-cut", type=float, default=8.0,
                    help="Idle gap >= this many seconds becomes a hard-cut candidate.")
    args = ap.parse_args(argv)

    if not args.cast.is_file():
        raise SystemExit(f"not a file: {args.cast}")
    for tool in ("agg", "ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            raise SystemExit(
                f"{tool} not found on PATH. On macOS: brew install agg ffmpeg"
            )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = args.out_dir / "frames"
    gif_path = args.out_dir / "_cast.gif"

    header, events = parse_cast(args.cast)
    gaps = find_idle_gaps(events, args.idle_speedramp, args.idle_cut)

    render_with_agg(args.cast, gif_path, args.theme, args.font_size, args.fps)
    explode_to_pngs(gif_path, frames_dir)
    frame_times = probe_frame_times(gif_path)

    output_count = sum(1 for (_, c, _) in events if c == "o")
    input_count = sum(1 for (_, c, _) in events if c == "i")

    manifest = {
        "cast_version": header.get("version"),
        "duration_s": round(total_duration(events), 4),
        "fps": args.fps,
        "frame_count": len(frame_times),
        "frame_times_s": frame_times,
        "idle_gaps": gaps,
        "events_summary": {"output_count": output_count, "input_count": input_count},
        "terminal": {
            "cols": header.get("width") or (header.get("term") or {}).get("cols"),
            "rows": header.get("height") or (header.get("term") or {}).get("rows"),
        },
    }
    (args.out_dir / "timing.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print(f"frames: {frames_dir}/ ({len(frame_times)} png)")
    print(f"timing: {args.out_dir / 'timing.json'}")
    print(f"idle gaps: {len(gaps)} ({sum(1 for g in gaps if g['kind']=='cut')} cuts, "
          f"{sum(1 for g in gaps if g['kind']=='speedramp')} speed-ramps)")


if __name__ == "__main__":
    main(sys.argv[1:])
