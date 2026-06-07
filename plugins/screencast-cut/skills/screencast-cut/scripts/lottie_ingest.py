#!/usr/bin/env python3
"""Lottie BRING-YOUR-OWN ingest + vetting (screencast-cut Phase 2).

Lottie is a *second-class* citizen beside the SVG recipe engine. Two properties
make it dangerous to use blindly, and this module is the gate that defends both:

  1. DETERMINISM. After-Effects *expressions* (JS stored on an animated property
     under the `"x"` key) read time/wall-clock state and FLICKER in headless
     renders — two renders of the same frame differ. `find_expressions` /
     `assert_no_expressions` detect and reject them so only frame-deterministic
     files reach `@remotion/lottie`.

  2. LICENSING. The big Lottie catalogs forbid redistributing their JSON, so we
     NEVER bundle a third-party file. A user points us at THEIR file at render
     time; we vet it in place. `looks_like_lottie` powers the repo guardrail
     (tests/test_lottie_guardrail.py) that makes accidentally committing a
     third-party Lottie a test failure.

It also does BEST-EFFORT recolor of flat fills/strokes to a brand color (Lottie
can't be cleanly themed — gradients, animated colors and expression-driven color
are surfaced as "couldn't theme", never silently mangled). The richer,
library-backed recolor is `scripts/recolor_lottie.mjs` (uses @lottiefiles/
lottie-js, MIT); this pure-Python path is the offline-testable equivalent for
the flat-fill subset and produces the same result.

Everything here is pure/offline and unit-tested (`tests/test_lottie_ingest.py`).
The CLI is the BYO entry point:

    lottie_ingest.py SRC [--check-only] [--color '#22d3ee'] [--out OUT.json]
"""

import argparse
import copy
import json
import sys
from pathlib import Path

# Required top-level keys that mark a JSON blob as a Lottie animation. Kept
# strict so the guardrail does not false-positive on package.json/tsconfig/etc.
_LOTTIE_KEYS = ("v", "layers")


class LottieIngestError(Exception):
    """A vetting failure with a user-facing message (invalid / expression-driven)."""


def looks_like_lottie(data):
    """True if `data` (a parsed JSON value) has the shape of a Lottie animation.

    Discriminating signal: a `v`ersion string + a `layers` array + at least one
    of the Bodymovin timing keys (`fr`/`op`/`ip`). Strict on purpose — this is
    what the licensing guardrail uses to decide whether a committed JSON file
    needs an OWNED/CC0 provenance note.
    """
    if not isinstance(data, dict):
        return False
    if not all(k in data for k in _LOTTIE_KEYS):
        return False
    if not isinstance(data.get("layers"), list):
        return False
    return any(k in data for k in ("fr", "op", "ip"))


def load_lottie(path):
    """Parse a Lottie JSON file; raise LottieIngestError if missing/invalid/not Lottie."""
    p = Path(path)
    if not p.is_file():
        raise LottieIngestError(f"file not found: {p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise LottieIngestError(f"not valid JSON: {p} ({e})") from e
    if not looks_like_lottie(data):
        raise LottieIngestError(
            f"does not look like a Lottie animation (need 'v' + 'layers' + a "
            f"timing key): {p}"
        )
    return data


def find_expressions(data):
    """Return a list of `(dotted_path, snippet)` for every AE expression found.

    A Lottie expression is a non-empty STRING stored under a property's `"x"`
    key. Bezier interpolation handles also use `"x"` but as arrays/numbers, so
    keying on `isinstance(value, str)` is the exact discriminator — no false
    positives on eased keyframes.
    """
    found = []

    def walk(node, path):
        if isinstance(node, dict):
            x = node.get("x")
            if isinstance(x, str) and x.strip():
                snippet = x.strip().replace("\n", " ")
                found.append((path + ".x", snippet[:80]))
            for k, v in node.items():
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")

    walk(data, "")
    return found


def assert_no_expressions(data):
    """Raise LottieIngestError if the file contains any AE expression."""
    exprs = find_expressions(data)
    if exprs:
        lines = "\n".join(f"  - {p}: {snip}" for p, snip in exprs[:8])
        more = "" if len(exprs) <= 8 else f"\n  … and {len(exprs) - 8} more"
        raise LottieIngestError(
            "Lottie file is EXPRESSION-DRIVEN and will flicker in headless "
            "renders (non-deterministic). Re-export it from After Effects with "
            "expressions baked/removed, or use the SVG recipe engine instead.\n"
            f"Expressions found:\n{lines}{more}"
        )


def _hex_to_rgba(hex_color):
    """'#rrggbb' or '#rrggbbaa' → [r, g, b, a] floats in 0..1 (Lottie color)."""
    h = hex_color.strip().lstrip("#")
    if len(h) not in (6, 8):
        raise LottieIngestError(f"color must be #rrggbb or #rrggbbaa, got {hex_color!r}")
    try:
        r = int(h[0:2], 16) / 255.0
        g = int(h[2:4], 16) / 255.0
        b = int(h[4:6], 16) / 255.0
        a = int(h[6:8], 16) / 255.0 if len(h) == 8 else 1.0
    except ValueError as e:
        raise LottieIngestError(f"invalid hex color {hex_color!r}") from e
    # 6 dp keeps it lossless-ish without trailing float noise.
    return [round(v, 6) for v in (r, g, b, a)]


# Shape types we recolor (flat solid color) vs. ones we cannot theme cleanly.
_FLAT_COLOR_SHAPES = {"fl": "fill", "st": "stroke"}
_GRADIENT_SHAPES = {"gf": "gradient-fill", "gs": "gradient-stroke"}


def recolor_flat_fills(data, hex_color):
    """Best-effort recolor of flat fills/strokes to `hex_color`.

    Returns `(new_data, report)`. `report` = {"recolored": int, "skipped":
    [{"kind", "reason"}]}. We ONLY touch flat (static, `a==0`) `fl`/`st` colors;
    animated colors, gradients and any expression-bearing color are left untouched
    and surfaced in `skipped` so the caller knows what it could not theme. The
    input is not mutated.
    """
    out = copy.deepcopy(data)
    rgba = _hex_to_rgba(hex_color)
    report = {"recolored": 0, "skipped": []}

    def walk(node):
        if isinstance(node, dict):
            ty = node.get("ty")
            if ty in _FLAT_COLOR_SHAPES:
                c = node.get("c")
                if isinstance(c, dict):
                    if isinstance(c.get("x"), str) and c["x"].strip():
                        report["skipped"].append(
                            {"kind": _FLAT_COLOR_SHAPES[ty], "reason": "expression-driven color"}
                        )
                    elif c.get("a") == 1:
                        report["skipped"].append(
                            {"kind": _FLAT_COLOR_SHAPES[ty], "reason": "animated color"}
                        )
                    else:
                        # Preserve a 4th alpha channel if the source had one.
                        old = c.get("k")
                        keep_alpha = (
                            rgba[3]
                            if not (isinstance(old, list) and len(old) >= 4)
                            else old[3]
                        )
                        c["k"] = [rgba[0], rgba[1], rgba[2], keep_alpha]
                        report["recolored"] += 1
            elif ty in _GRADIENT_SHAPES:
                report["skipped"].append(
                    {"kind": _GRADIENT_SHAPES[ty], "reason": "gradient (not themeable)"}
                )
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(out)
    return out, report


def ingest(src, *, color=None, check_only=False, out=None):
    """Vet a BYO Lottie (reject expressions), optionally recolor, optionally write.

    Returns a result dict. Never copies the file into a committed/bundled
    location — `out` is the caller's responsibility (the licensing rule is that
    BYO files live at the user's runtime path, never in the repo).
    """
    data = load_lottie(src)
    assert_no_expressions(data)  # raises on expression-driven files

    result = {"src": str(src), "expressions": False, "recolored": None, "out": None}
    if color:
        data, report = recolor_flat_fills(data, color)
        result["recolored"] = report
    if not check_only and out:
        Path(out).write_text(json.dumps(data, separators=(",", ":")) + "\n", encoding="utf-8")
        result["out"] = str(out)
    return result


def main(argv):
    ap = argparse.ArgumentParser(
        description="Vet a bring-your-own Lottie file (reject expression-driven, "
        "best-effort recolor flat fills). We NEVER bundle your file — keep it at "
        "your own runtime path."
    )
    ap.add_argument("src", help="path to the BYO Lottie JSON")
    ap.add_argument("--check-only", action="store_true",
                    help="vet only; do not write output")
    ap.add_argument("--color", default=None, help="recolor flat fills to '#rrggbb'")
    ap.add_argument("--out", default=None, help="write the vetted/themed JSON here")
    args = ap.parse_args(argv)

    try:
        res = ingest(args.src, color=args.color, check_only=args.check_only, out=args.out)
    except LottieIngestError as e:
        print(f"lottie_ingest: REJECTED\n{e}", file=sys.stderr)
        return 2

    print(f"lottie_ingest: OK — {args.src} is expression-free (deterministic).")
    if res["recolored"] is not None:
        r = res["recolored"]
        print(f"  recolored {r['recolored']} flat fill/stroke(s).")
        for s in r["skipped"]:
            print(f"  could NOT theme: {s['kind']} — {s['reason']}")
    if res["out"]:
        print(f"  wrote {res['out']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
