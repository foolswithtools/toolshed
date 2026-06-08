#!/usr/bin/env python3
"""Generate the per-theme ORIGINAL Lottie motifs (screencast-cut Phase 4).

These are *authored in-repo* — one signature animation per shipped demo theme,
in that theme's palette/personality. Because we author them ourselves they are
OWNED (license-clean to bundle and redistribute) and we vet them to be
EXPRESSION-FREE so they render deterministically headlessly via the Phase-2
`@remotion/lottie` / `LottieIcon` path. This is the licensing-clean alternative
to pulling third-party Lottie (which the catalogs forbid redistributing).

Every value below is a static number or keyframe array — there are NO
After-Effects expressions (no string `"x"` keys). `scripts/lottie_ingest.py`
asserts that; `tests/test_theme_lottie.py` re-vets the emitted files.

Run it to (re)generate the committed JSON:

    python3 scripts/gen_theme_lottie.py

It writes each motif into BOTH the shippable template area
(`scene-templates/lottie/`) and the golden project's `public/lottie/` (where the
`golden-theme-lottie` composition renders them for real).
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
TEMPLATE_DIR = SKILL / "scene-templates" / "lottie"
GOLDEN_DIR = (
    SKILL / "tests" / "fixtures" / "golden-project" / "public" / "lottie"
)

# ---------------------------------------------------------------------------
# Palette → Lottie color (r, g, b, a) floats in 0..1, taken verbatim from each
# theme's style-guide.ts so the motif is authored DIRECTLY in the theme palette
# (no recolor pass needed — that is the whole point of an originated per-theme
# Lottie).
# ---------------------------------------------------------------------------

def rgba(r, g, b, a=1.0):
    return [round(r / 255.0, 6), round(g / 255.0, 6), round(b / 255.0, 6), a]


# default theme (dark / premium / cyan accent)
DEF_ACCENT = rgba(0x22, 0xD3, 0xEE)   # #22d3ee
DEF_INDIGO = rgba(0x63, 0x66, 0xF1)   # #6366f1 (accentSweep tail)

# foolswithtools-brand (pop-art / punk-zine — acid green on cream, charcoal ink)
FWT_ACID = rgba(0xCC, 0xFF, 0x00)     # #CCFF00
FWT_CHARCOAL = rgba(0x1A, 0x1A, 0x1A) # #1A1A1A
FWT_ORANGE = rgba(0xF5, 0x47, 0x1D)   # #F5471D


# ---------------------------------------------------------------------------
# Small builders for the handful of Lottie primitives we use. Keeping these as
# functions makes the motifs readable and keeps every emitted number explicit.
# ---------------------------------------------------------------------------

# Ease-in-out keyframe handles (same family as owned-pulse.json). For a 1-D
# property (rotation) the handle arrays are length-1; for a 3-D property
# (scale) they are length-3. Plain bezier handles — arrays, never strings —
# so the expression detector never trips.
def _handles(dims):
    return (
        {"x": [0.42] * dims, "y": [1.0] * dims},   # i (in)
        {"x": [0.58] * dims, "y": [0.0] * dims},   # o (out)
    )


def kf(stops, dims):
    """Build an animated property value (`{"a":1,"k":[...]}`) from
    `[(t, [vals]), ...]`. The last stop is a bare hold keyframe."""
    i, o = _handles(dims)
    out = []
    for idx, (t, s) in enumerate(stops):
        if idx == len(stops) - 1:
            out.append({"t": t, "s": s})
        else:
            out.append({"t": t, "s": s, "i": i, "o": o})
    return {"a": 1, "k": out}


def static(v):
    return {"a": 0, "k": v}


def fill(color, opacity=100):
    return {"ty": "fl", "nm": "fill", "c": static(color), "o": static(opacity), "r": 1}


def stroke(color, width, opacity=100):
    return {
        "ty": "st", "nm": "stroke", "c": static(color), "o": static(opacity),
        "w": static(width), "lc": 2, "lj": 2,
    }


def ellipse(size, pos=(0, 0)):
    return {"ty": "el", "nm": "ellipse", "p": static(list(pos)), "s": static(list(size))}


def star(points, outer, inner, rotation=0, pos=(0, 0)):
    # ty:"sr" sy:1 = star (sy:2 = polygon). Parametric, expression-free —
    # rendered natively by lottie-web.
    return {
        "ty": "sr", "nm": "star", "sy": 1,
        "pt": static(points), "p": static(list(pos)), "r": static(rotation),
        "or": static(outer), "ir": static(inner), "os": static(0), "is": static(0),
    }


def group(name, items, *, rotation=None, pos=(0, 0), anchor=(0, 0), scale=(100, 100)):
    tr = {
        "ty": "tr",
        "p": static(list(pos)),
        "a": static(list(anchor)),
        "s": static(list(scale)),
        "r": rotation if rotation is not None else static(0),
        "o": static(100),
    }
    return {"ty": "gr", "nm": name, "it": [*items, tr]}


def layer(ind, name, shapes, *, pos=(100, 100), rotation=None, scale=None):
    ks = {
        "o": static(100),
        "r": rotation if rotation is not None else static(0),
        "p": static([pos[0], pos[1], 0]),
        "a": static([0, 0, 0]),
        "s": scale if scale is not None else static([100, 100, 100]),
    }
    return {
        "ddd": 0, "ind": ind, "ty": 4, "nm": name, "sr": 1,
        "ks": ks, "ao": 0, "shapes": shapes, "ip": 0, "op": 60, "st": 0, "bm": 0,
    }


def comp(name, layers):
    return {
        "v": "5.9.0", "fr": 30, "ip": 0, "op": 60, "w": 200, "h": 200,
        "nm": name, "ddd": 0, "assets": [], "layers": layers,
    }


# ---------------------------------------------------------------------------
# default-orbit — premium dark/cyan signature: a soft cyan ring that breathes
# while a bright accent dot orbits it. Matches the `default` theme's calm,
# camera-eased personality.
# ---------------------------------------------------------------------------

def default_orbit():
    # A dot orbiting the centre: a group whose transform ROTATES 0→360 while its
    # ellipse sits at radius 64. Continuous rotation = clean loop.
    orbit_dot = layer(
        1, "orbit-dot",
        [group(
            "orbit",
            [ellipse((24, 24), pos=(64, 0)), fill(DEF_ACCENT)],
            rotation=kf([(0, [0]), (60, [360])], 1),
        )],
    )
    # A soft ring that pulses scale (breathing). Indigo→accent gives the
    # accentSweep flavour: ring in indigo, dot in cyan.
    ring = layer(
        2, "ring",
        [group(
            "ring",
            [ellipse((150, 150)), stroke(DEF_INDIGO, 10, opacity=70)],
        )],
        scale=kf([(0, [92, 92, 100]), (30, [108, 108, 100]), (60, [92, 92, 100])], 3),
    )
    return comp("default-orbit", [orbit_dot, ring])


# ---------------------------------------------------------------------------
# foolswithtools-spark — punk/pop signature: a chunky acid-green star with a
# 2px charcoal ink border (the site's border convention) and a hot-orange core,
# spinning with a punchy scale bounce. Loud, hand-made energy.
# ---------------------------------------------------------------------------

def foolswithtools_spark():
    spark = layer(
        1, "spark",
        [
            # Shapes render top-of-list first → core dot sits ON TOP of the
            # star, reading as a hot-orange pop accent in the acid-green spark.
            group("core", [ellipse((34, 34)), fill(FWT_ORANGE), stroke(FWT_CHARCOAL, 6)]),
            group("star", [
                star(6, 80, 34),
                fill(FWT_ACID),
                stroke(FWT_CHARCOAL, 8),
            ]),
        ],
        rotation=kf([(0, [0]), (60, [360])], 1),
        scale=kf([(0, [90, 90, 100]), (30, [114, 114, 100]), (60, [90, 90, 100])], 3),
    )
    return comp("foolswithtools-spark", [spark])


MOTIFS = {
    "default-orbit.json": default_orbit(),
    "foolswithtools-spark.json": foolswithtools_spark(),
}


def main():
    for d in (TEMPLATE_DIR, GOLDEN_DIR):
        d.mkdir(parents=True, exist_ok=True)
        for fname, data in MOTIFS.items():
            (d / fname).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            print(f"wrote {d / fname}")


if __name__ == "__main__":
    main()
