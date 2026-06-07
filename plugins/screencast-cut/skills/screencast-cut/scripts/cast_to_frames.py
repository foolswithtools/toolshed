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
          "duration_s": float,               # cast-clock duration
          "fps": int,
          "frame_count": int,                # == len(frame_times_s)
          "png_count": int,                  # PNGs on disk; asserted == frame_count
          "frame_times_s": [float, ...],     # GIF/PNG timestamp of each PNG
          "clock_drift_s": float,            # |GIF clock - cast clock| (diagnostic)
          "idle_gaps": [                     # frame indices collapse the two clocks
            {"start_s", "end_s", "duration_s", "kind", "start_frame", "end_frame"},
            ...
          ],
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

# timing_math lives beside this script; ensure it's importable whether run as a
# script (dir is sys.path[0]) or imported under test.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from timing_math import cast_time_to_frame_index
from schema_validate import validate, SchemaError


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


# agg defaults to capping idle gaps at 5s and holding the final frame ~3s.
# Both rewrite the timeline, which would put the GIF/PNG clock out of step with
# the cast-event clock. We disable them so the PNG sequence is faithful to real
# cast time — idle handling (speed-ramp / cut) is OUR job, done later in Remotion
# from the idle_gaps manifest, not agg's.
AGG_IDLE_TIME_LIMIT = 86400  # effectively uncapped


def render_with_agg(cast_path, gif_path, theme, font_size, fps):
    cmd = [
        "agg",
        "--theme", theme,
        "--font-size", str(font_size),
        "--fps-cap", str(fps),
        "--idle-time-limit", str(AGG_IDLE_TIME_LIMIT),
        "--last-frame-duration", "0",
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

    # --- Invariants: the two clocks (cast-event time vs GIF/PNG time) must stay
    # consistent, and the PNG sequence must line up 1:1 with frame_times. ---
    png_files = sorted(frames_dir.glob("*.png"))
    if len(png_files) != len(frame_times):
        raise SystemExit(
            f"frame desync: {len(png_files)} PNGs on disk vs {len(frame_times)} "
            f"frames from ffprobe. This usually means ffmpeg handled "
            f"'-fps_mode passthrough' differently than expected for this GIF."
        )
    if frame_times != sorted(frame_times):
        raise SystemExit("frame_times_s is not monotonically non-decreasing")

    # Collapse the two clocks at the manifest boundary: attach PNG indices to
    # each gap so the Remotion side reads frame indices, never re-interpolating
    # cast-seconds against GIF-seconds.
    for g in gaps:
        g["start_frame"] = cast_time_to_frame_index(g["start_s"], frame_times)
        g["end_frame"] = cast_time_to_frame_index(g["end_s"], frame_times)

    # Drift gauge: how far the GIF clock wandered from the cast clock.
    cast_dur = total_duration(events)
    gif_dur = frame_times[-1] if frame_times else 0.0
    clock_drift_s = round(abs(gif_dur - cast_dur), 3)
    drift_warn = clock_drift_s > max(0.5, 0.02 * cast_dur)

    output_count = sum(1 for (_, c, _) in events if c == "o")
    input_count = sum(1 for (_, c, _) in events if c == "i")

    manifest = {
        "cast_version": header.get("version"),
        "duration_s": round(cast_dur, 4),
        "fps": args.fps,
        "frame_count": len(frame_times),
        "png_count": len(png_files),
        "frame_times_s": frame_times,
        "clock_drift_s": clock_drift_s,
        "idle_gaps": gaps,
        "events_summary": {"output_count": output_count, "input_count": input_count},
        "terminal": {
            "cols": header.get("width") or (header.get("term") or {}).get("cols"),
            "rows": header.get("height") or (header.get("term") or {}).get("rows"),
        },
    }
    # Validate the manifest against its contract before writing, so a contract
    # regression fails here instead of as a KeyError on the Remotion side.
    try:
        validate(manifest, "timing", what="timing.json")
    except SchemaError as e:
        raise SystemExit(str(e))

    (args.out_dir / "timing.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print(f"frames: {frames_dir}/ ({len(frame_times)} png)")
    print(f"timing: {args.out_dir / 'timing.json'}")
    print(f"idle gaps: {len(gaps)} ({sum(1 for g in gaps if g['kind']=='cut')} cuts, "
          f"{sum(1 for g in gaps if g['kind']=='speedramp')} speed-ramps)")
    if drift_warn:
        print(
            f"WARNING: GIF clock drifted {clock_drift_s}s from the cast clock "
            f"(cast {round(cast_dur, 3)}s vs GIF {round(gif_dur, 3)}s). Beats are "
            f"anchored on frame indices so cuts still land correctly, but surface "
            f"this in the Phase 3 plan.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main(sys.argv[1:])
