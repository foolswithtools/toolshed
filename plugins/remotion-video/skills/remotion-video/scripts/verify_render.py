#!/usr/bin/env python3
"""Render-verification loop for a Remotion project — the shared "render → look →
fix" harness used by both remotion-video and screencast-cut.

It runs deterministic gates that need no human eye, then renders a fixed
"filmstrip" of stills (computed reproducibly from the cut's manifests) for a
vision pass against RUBRIC.md.

Two halves:
  - THIS file (orchestrator): CLI, locate manifests, compute the filmstrip frame
    set + per-frame expectations, drive `_verify_helper.mjs`, assemble outputs,
    decide the exit code.
  - `_verify_helper.mjs` (Node): bundle() once, getCompositions(), then
    renderStill() each frame. It only knows "render these frames".

Deterministic gates (D1–D5 set the exit code; D6/D7 are config-derived
expectations the vision pass checks):
  D1 bundle()           — the project compiles & bundles
  D2 composition exists — `<comp_id>` is registered
  D3 dimensions         — width/height == --expect-width/--expect-height
  D4 duration           — durationInFrames == --expect-duration-frames
  D5 stills render       — every filmstrip still renders (a SafeImg/SafeVideo
                          cancelRender() turns a missing asset into a failure)

Outputs (under <project>/videos/<slug>/.checks/):
  filmstrip/frame-NNNNNN.png   the stills
  filmstrip.md                 embeds each PNG + its expectation (for the eye)
  verify-summary.json          machine-readable gate + still results

Exit codes:
  0  all deterministic gates pass (vision pass still pending)
  2  a deterministic gate or a still failed
  3  environment / invocation error (node missing, no entry point, Remotion not
     installed, manifests missing, helper crashed)

CLI:
  verify_render.py <project> <comp_id>
      [--video-slug SLUG]
      [--expect-duration-frames N] [--expect-width N] [--expect-height N]
      [--scale F] [--max-stills N] [--stills-only]
      [--transcript-start-frame N] [--video-start-frame N]
      [--terminal-start-frame N]
      [--json]
"""

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HELPER = Path(__file__).resolve().parent / "_verify_helper.mjs"


def _r(x):
    """Round half-up (matches JS Math.round); inputs here are non-negative."""
    return math.floor(x + 0.5)


def _load_json(path):
    if path and path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def compute_filmstrip_frames(
    duration_frames,
    fps,
    *,
    timing=None,
    transcript=None,
    zoom=None,
    transcript_start_frame=0,
    video_start_frame=0,
    terminal_start_frame=0,
    max_words=4,
    max_stills=12,
):
    """Deterministically pick the filmstrip output-frame set + expectations.

    Pure function so the e2e test can recompute the exact same set from the
    committed manifests. Returns a list of dicts sorted by `frame`, each with a
    `frame` key plus whatever expectation keys apply (anchor/beat/word/zoom).

    Manifest time values are in cast/source seconds; the offsets map them into
    the OUTPUT timeline (an intro card shifts narration, etc.). Defaults of 0
    suit a layout with no pre-roll. Beat seams use a realtime assumption purely
    for SAMPLING — the even-coverage backbone backstops any layout skew.
    """
    if duration_frames <= 0:
        return []
    last = duration_frames - 1
    picks = {}

    def add(f, **exp):
        f = max(0, min(int(f), last))
        slot = picks.setdefault(f, {"frame": f})
        for k, v in exp.items():
            if v is not None:
                slot[k] = v

    add(0, anchor="first")
    add(last, anchor="last")

    if timing:
        for g in timing.get("idle_gaps", []):
            add(terminal_start_frame + _r(g["start_s"] * fps), beat=f"into-{g['kind']}")
            add(terminal_start_frame + _r(g["end_s"] * fps), beat=f"out-of-{g['kind']}")

    if transcript:
        words = [
            w
            for s in transcript.get("segments", [])
            for w in s.get("words", [])
            if w.get("start_s") is not None
        ]
        if words:
            n = min(max_words, len(words))
            for i in range(n):
                idx = (i * (len(words) - 1)) // (n - 1) if n > 1 else 0
                w = words[idx]
                add(
                    transcript_start_frame + _r(w["start_s"] * fps),
                    word=w["text"],
                )

    if zoom:
        for a in zoom.get("anchors", []):
            add(
                video_start_frame + _r(a["t_s"] * fps),
                zoom=(a.get("label") or "anchor"),
            )

    # Even-coverage backbone: fill until we reach max_stills (priority frames
    # above are always kept).
    target = min(max_stills, duration_frames)
    if len(picks) < target and target > 1:
        for i in range(target):
            f = _r(i * last / (target - 1))
            if f not in picks:
                add(f, anchor="coverage")
            if len(picks) >= target:
                break

    return [picks[f] for f in sorted(picks)]


def _run_helper(project, comp_id, scale, frames, still_dir):
    """Invoke the Node helper; return (parsed_result | None, raw_stdout, raw_stderr)."""
    if shutil.which("node") is None:
        return None, "", "node not found on PATH (brew install node)"
    if not HELPER.is_file():
        return None, "", f"helper missing: {HELPER}"

    still_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False, encoding="utf-8"
    ) as tf:
        json.dump({"scale": scale, "outDir": str(still_dir), "frames": frames}, tf)
        req_path = tf.name

    try:
        proc = subprocess.run(
            ["node", str(HELPER), str(project), comp_id, req_path],
            capture_output=True,
            text=True,
        )
    finally:
        Path(req_path).unlink(missing_ok=True)

    out = proc.stdout.strip()
    if not out:
        return None, proc.stdout, proc.stderr
    try:
        # The helper emits one JSON object; tolerate stray log lines around it.
        start = out.index("{")
        end = out.rindex("}") + 1
        return json.loads(out[start:end]), proc.stdout, proc.stderr
    except (ValueError, json.JSONDecodeError):
        return None, proc.stdout, proc.stderr


def _write_filmstrip_md(md_path, comp_id, expectations, helper, still_dir, rubric_hint):
    lines = [
        f"# Filmstrip — `{comp_id}`",
        "",
        "Deterministic gates passed; this is the VISION pass. Judge each frame "
        "against `RUBRIC.md` (V1–V8). The *expectation* under each image says "
        "what should be on screen — flag any mismatch.",
        "",
    ]
    by_frame = {s["frame"]: s for s in helper.get("stills", [])}
    for exp in expectations:
        f = exp["frame"]
        still = by_frame.get(f)
        rel = None
        if still and still.get("ok"):
            rel = Path(still["path"]).relative_to(still_dir.parent).as_posix()
        bits = []
        if "anchor" in exp:
            bits.append(f"anchor={exp['anchor']}")
        if "beat" in exp:
            bits.append(f"beat={exp['beat']}")
        if "word" in exp:
            bits.append(f"caption word ≈ \"{exp['word']}\"")
        if "zoom" in exp:
            bits.append(f"zoom on \"{exp['zoom']}\"")
        expectation = "; ".join(bits) or "general coverage"
        lines.append(f"### frame {f}")
        if rel:
            lines.append(f"![frame {f}]({rel})")
        else:
            err = (still or {}).get("error", "not rendered")
            lines.append(f"_(still did not render: {err})_")
        lines.append(f"**Expect:** {expectation}")
        lines.append("")
    if rubric_hint:
        lines.append(f"> Rubric: {rubric_hint}")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", type=Path)
    ap.add_argument("comp_id")
    ap.add_argument("--video-slug", default=None,
                    help="videos/<slug>/ holding source manifests + .checks. "
                         "Defaults to comp_id.")
    ap.add_argument("--expect-duration-frames", type=int, default=None)
    ap.add_argument("--expect-width", type=int, default=None)
    ap.add_argument("--expect-height", type=int, default=None)
    ap.add_argument("--scale", type=float, default=0.5)
    ap.add_argument("--max-stills", type=int, default=12)
    ap.add_argument("--stills-only", action="store_true",
                    help="Re-render the filmstrip for a vision re-check; do not "
                         "treat a duration/dimension mismatch as fatal.")
    ap.add_argument("--transcript-start-frame", type=int, default=0)
    ap.add_argument("--video-start-frame", type=int, default=0)
    ap.add_argument("--terminal-start-frame", type=int, default=0)
    ap.add_argument("--json", action="store_true",
                    help="Print verify-summary.json to stdout as well.")
    args = ap.parse_args(argv)

    slug = args.video_slug or args.comp_id
    # Resolve to an absolute path: the Node helper's createRequire() and
    # bundle() entryPoint both require absolute paths.
    project = args.project.resolve()
    if not project.is_dir():
        print(f"error: project dir not found: {project}", file=sys.stderr)
        return 3

    source_dir = project / "videos" / slug / "source"
    checks_dir = project / "videos" / slug / ".checks"
    still_dir = checks_dir / "filmstrip"

    timing = _load_json(source_dir / "timing.json")
    transcript = _load_json(source_dir / "transcript.json")
    zoom = _load_json(source_dir / "zoom_anchors.json")

    # We need a duration + fps to compute frames. Prefer the expected duration
    # (the planned truth); fall back to whatever the helper reports after bundle.
    # fps comes from timing.json, else assume 30.
    fps = (timing or {}).get("fps", 30)

    # First helper pass needs SOME frames; if we know duration up front, compute
    # now, else do a probe pass (no frames) to learn duration, then a real pass.
    def build_frames(duration_frames):
        return compute_filmstrip_frames(
            duration_frames,
            fps,
            timing=timing,
            transcript=transcript,
            zoom=zoom,
            transcript_start_frame=args.transcript_start_frame,
            video_start_frame=args.video_start_frame,
            terminal_start_frame=args.terminal_start_frame,
            max_stills=args.max_stills,
        )

    if args.expect_duration_frames:
        expectations = build_frames(args.expect_duration_frames)
        frames = [e["frame"] for e in expectations]
    else:
        # Probe: bundle + getCompositions only (no stills), learn duration.
        probe, _so, _se = _run_helper(project, args.comp_id, args.scale, [], still_dir)
        if probe is None:
            print(f"error: verify helper produced no result. stderr:\n{_se}",
                  file=sys.stderr)
            return 3
        if probe.get("envError"):
            print(f"error (environment): {probe.get('error')}", file=sys.stderr)
            return 3
        if not probe.get("target"):
            print(f"error: {probe.get('error') or 'composition not found'}",
                  file=sys.stderr)
            # bundle/comp failure → real gate fail
            return 2
        expectations = build_frames(probe["target"]["durationInFrames"])
        frames = [e["frame"] for e in expectations]

    helper, raw_out, raw_err = _run_helper(
        project, args.comp_id, args.scale, frames, still_dir
    )
    if helper is None:
        print(f"error: verify helper produced no parseable result.\n"
              f"stdout:\n{raw_out}\nstderr:\n{raw_err}", file=sys.stderr)
        return 3
    if helper.get("envError"):
        print(f"error (environment): {helper.get('error')}", file=sys.stderr)
        return 3

    # --- Deterministic gates ---
    target = helper.get("target")
    stills = helper.get("stills", [])
    gates = {}

    # D1 bundle: helper.ok is set True only after bundle + getCompositions both
    # succeed. A bundle/compile error leaves ok=False with stage "bundle".
    gates["bundle"] = {
        "pass": bool(helper.get("ok")),
        "stage": helper.get("stage"),
        "error": helper.get("error"),
    }

    gates["composition_exists"] = {
        "pass": target is not None,
        "available": [c["id"] for c in helper.get("compositions", [])],
    }

    gates["dimensions"] = {"checked": False, "pass": True}
    if target and args.expect_width and args.expect_height:
        ok = target["width"] == args.expect_width and target["height"] == args.expect_height
        gates["dimensions"] = {
            "checked": True,
            "pass": ok,
            "actual": {"width": target.get("width"), "height": target.get("height")},
            "expected": {"width": args.expect_width, "height": args.expect_height},
        }

    gates["duration"] = {"checked": False, "pass": True}
    if target and args.expect_duration_frames:
        ok = target["durationInFrames"] == args.expect_duration_frames
        gates["duration"] = {
            "checked": True,
            "pass": ok,
            "actual": target.get("durationInFrames"),
            "expected": args.expect_duration_frames,
        }

    rendered_ok = bool(stills) and all(s.get("ok") for s in stills)
    gates["stills_render"] = {
        "pass": rendered_ok,
        "count": len(stills),
        "failed": [s for s in stills if not s.get("ok")],
    }

    # Hard gates that set the exit code. Under --stills-only, dimension/duration
    # mismatches are not fatal (you're iterating on vision).
    hard = ["bundle", "composition_exists", "stills_render"]
    if not args.stills_only:
        hard += ["dimensions", "duration"]
    all_pass = all(gates[g]["pass"] for g in hard)

    summary = {
        "comp_id": args.comp_id,
        "slug": slug,
        "scale": args.scale,
        "status": "pass" if all_pass else "fail",
        "vision_pending": all_pass,  # deterministic pass != victory; vision next
        "gates": gates,
        "expectations": {
            # D6/D7: config-derived expectations the vision pass confirms.
            "has_transcript": transcript is not None,
            "has_zoom_anchors": zoom is not None,
            "idle_gap_count": len((timing or {}).get("idle_gaps", [])),
        },
        "target": target,
        "filmstrip": [
            {**e, "rendered": next((s.get("ok") for s in stills if s["frame"] == e["frame"]), False)}
            for e in expectations
        ],
        "manifests_found": {
            "timing": timing is not None,
            "transcript": transcript is not None,
            "zoom_anchors": zoom is not None,
        },
    }

    checks_dir.mkdir(parents=True, exist_ok=True)
    (checks_dir / "verify-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    _write_filmstrip_md(
        checks_dir / "filmstrip.md",
        args.comp_id,
        expectations,
        helper,
        still_dir,
        "zero V1–V8 failures required to pass the vision check",
    )

    # Human-readable line.
    print(f"verify: {summary['status']}  "
          f"(bundle={gates['bundle']['pass']} comp={gates['composition_exists']['pass']} "
          f"dims={gates['dimensions']['pass']} dur={gates['duration']['pass']} "
          f"stills={gates['stills_render']['pass']} [{len(stills)}])")
    print(f"  filmstrip: {checks_dir / 'filmstrip.md'}")
    print(f"  summary:   {checks_dir / 'verify-summary.json'}")
    if args.json:
        print(json.dumps(summary, indent=2))

    return 0 if all_pass else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
