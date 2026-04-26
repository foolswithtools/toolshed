#!/usr/bin/env python3
"""Parse a screen-recorder event stream into a flat zoom-anchor manifest.

Why this script exists: an MP4 alone tells us nothing about *where* the
user clicked, so auto-zoom needs structured event data. CleanShot X
burns its click highlights into the pixels and exports no sidecar — so
we can't drive auto-zoom from CleanShot output. The current ecosystem
schema with real, machine-readable click data is the polyrecorder-v2
format used by Screenize (open-source, MIT-equivalent macOS recorder),
which writes a `.screenize/recording/` package with separate JSON files
per event class.

This script accepts either:

  1. A polyrecorder-v2 package directory (the `recording/` folder
     containing `metadata.json` + `mouseclicks-*.json` etc.).
  2. A flat manual events file (see "Manual schema" below) for users
     who want to author zoom points by hand without recording with
     Screenize. Useful with CleanShot or QuickTime captures.

It normalizes to a single `zoom_anchors.json` consumed by the Remotion
side:

    {
      "source": "polyrecorder-v2" | "manual",
      "duration_s": float | null,        # null if not knowable from events
      "display": {"width_px": int, "height_px": int, "scale": float},
      "anchors": [
        {
          "t_s": 1.234,                   # click time in seconds from t=0
          "x": 0.42, "y": 0.58,           # NORMALIZED 0..1 (top-left origin)
          "button": "left",
          "label": "click on Run button"  # optional, from element_title
        }, ...
      ]
    }

Manual schema (flat events.json the user writes by hand):
    {
      "display": {"width_px": 1920, "height_px": 1080, "scale": 1},
      "clicks": [
        {"t_s": 12.0, "x": 0.42, "y": 0.58, "label": "open terminal"},
        {"t_s": 31.5, "x": 0.78, "y": 0.12, "label": "click run"}
      ]
    }
Coordinates here are already normalized 0..1.

Usage:
    parse_events.py <input> <output_dir> [--debounce-ms N]

`<input>` may be a directory (polyrecorder package) or a file (manual).
"""

import argparse
import json
import sys
from pathlib import Path


POLYRECORDER_FORMAT_VERSION = 2


def load_polyrecorder(rec_dir):
    """Load metadata + click events from a polyrecorder-v2 recording dir."""
    meta_path = rec_dir / "metadata.json"
    if not meta_path.is_file():
        raise SystemExit(f"missing {meta_path}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    fmt = meta.get("formatVersion")
    if fmt != POLYRECORDER_FORMAT_VERSION:
        raise SystemExit(
            f"polyrecorder formatVersion mismatch: expected "
            f"{POLYRECORDER_FORMAT_VERSION}, got {fmt!r}. "
            f"Re-export with a compatible recorder, or add a migration."
        )

    clicks = []
    # Files chunked as mouseclicks-0.json, mouseclicks-1.json, ...
    for clicks_file in sorted(rec_dir.glob("mouseclicks-*.json")):
        events = json.loads(clicks_file.read_text(encoding="utf-8"))
        for ev in events:
            if ev.get("type") != "mouseDown":
                continue
            clicks.append(ev)

    t0_ms = meta.get("processTimeStartMs")
    if t0_ms is None:
        # Fall back: anchor t=0 to the earliest click.
        t0_ms = min((ev.get("processTimeMs", 0) for ev in clicks), default=0)
    t_end_ms = meta.get("processTimeEndMs")

    display = meta.get("display") or {}
    return {
        "meta": meta,
        "t0_ms": t0_ms,
        "t_end_ms": t_end_ms,
        "display": display,
        "clicks_raw": clicks,
    }


def normalize_polyrecorder(loaded, debounce_ms):
    display = loaded["display"]
    w_px = float(display.get("widthPx") or 0)
    h_px = float(display.get("heightPx") or 0)
    if w_px <= 0 or h_px <= 0:
        raise SystemExit(
            "polyrecorder metadata missing display.widthPx / heightPx — "
            "can't normalize click coordinates."
        )

    t0 = loaded["t0_ms"]
    anchors = []
    last_t_ms = -10_000
    for ev in loaded["clicks_raw"]:
        t_ms = ev.get("processTimeMs")
        if t_ms is None:
            continue
        if t_ms - last_t_ms < debounce_ms:
            continue
        last_t_ms = t_ms
        x_px = float(ev.get("x", 0))
        y_px = float(ev.get("y", 0))
        label = (
            ev.get("elementTitle")
            or ev.get("elementRole")
            or None
        )
        anchors.append({
            "t_s": round((t_ms - t0) / 1000.0, 3),
            "x": round(max(0.0, min(1.0, x_px / w_px)), 4),
            "y": round(max(0.0, min(1.0, y_px / h_px)), 4),
            "button": ev.get("button", "left"),
            "label": label,
        })

    duration_s = None
    if loaded["t_end_ms"] is not None:
        duration_s = round((loaded["t_end_ms"] - t0) / 1000.0, 3)

    return {
        "source": "polyrecorder-v2",
        "duration_s": duration_s,
        "display": {
            "width_px": int(w_px),
            "height_px": int(h_px),
            "scale": float(display.get("scaleFactor") or 1),
        },
        "anchors": anchors,
    }


def normalize_manual(path, debounce_ms):
    raw = json.loads(path.read_text(encoding="utf-8"))
    display = raw.get("display") or {}
    w_px = int(display.get("width_px") or 1920)
    h_px = int(display.get("height_px") or 1080)
    scale = float(display.get("scale") or 1)

    anchors = []
    last_t_ms = -10_000
    for click in raw.get("clicks", []):
        t_s = float(click["t_s"])
        t_ms = int(t_s * 1000)
        if t_ms - last_t_ms < debounce_ms:
            continue
        last_t_ms = t_ms
        x = float(click.get("x", 0.5))
        y = float(click.get("y", 0.5))
        anchors.append({
            "t_s": round(t_s, 3),
            "x": round(max(0.0, min(1.0, x)), 4),
            "y": round(max(0.0, min(1.0, y)), 4),
            "button": click.get("button", "left"),
            "label": click.get("label"),
        })

    return {
        "source": "manual",
        "duration_s": raw.get("duration_s"),
        "display": {"width_px": w_px, "height_px": h_px, "scale": scale},
        "anchors": anchors,
    }


def detect_input(path):
    if path.is_dir():
        # Polyrecorder package: either the .screenize root (which contains a
        # `recording/` subdir) or the `recording/` dir itself.
        if (path / "metadata.json").is_file():
            return "polyrecorder", path
        if (path / "recording" / "metadata.json").is_file():
            return "polyrecorder", path / "recording"
        raise SystemExit(
            f"{path} is a directory but doesn't look like a polyrecorder "
            f"package (no metadata.json found at root or under recording/)."
        )
    if path.is_file():
        return "manual", path
    raise SystemExit(f"input not found: {path}")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path,
                    help="polyrecorder package dir, or flat manual events.json")
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--debounce-ms", type=int, default=250,
                    help="Drop clicks within N ms of the previous click "
                         "(double-clicks don't deserve two zoom anchors).")
    args = ap.parse_args(argv)

    kind, target = detect_input(args.input)

    if kind == "polyrecorder":
        loaded = load_polyrecorder(target)
        manifest = normalize_polyrecorder(loaded, args.debounce_ms)
    else:
        manifest = normalize_manual(target, args.debounce_ms)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / "zoom_anchors.json"
    out_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(str(out_path))
    print(f"source: {manifest['source']}")
    print(f"anchors: {len(manifest['anchors'])}")
    if manifest["duration_s"]:
        print(f"duration_s: {manifest['duration_s']}")


if __name__ == "__main__":
    main(sys.argv[1:])
