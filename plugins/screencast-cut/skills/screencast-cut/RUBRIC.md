# Screencast-cut verification rubric

The bar a cut must clear before it ships. Two sections:

- **DETERMINISTIC (D1–D7)** — checked by `verify_render.py`, no human eye needed.
  D1–D5 set the exit code; they map 1:1 to keys in `verify-summary.json`. D6–D7
  are config-derived *expectations* the vision pass confirms.
- **VISION (V1–V8)** — judged by reading `filmstrip.md`. Each item names which
  frames to look at, the pass/fail call, and what "good" looks like. **Zero
  V-failures is required to pass.** A deterministic pass alone is NOT victory.

The fresh-eyes subagent (from iteration 2 on) gets ONLY `filmstrip.md` and this
file — no project context — and returns a verdict per V-item.

---

## DETERMINISTIC (verify_render.py → verify-summary.json)

| ID | Check | Pass condition | summary key |
|----|-------|----------------|-------------|
| D1 | Bundle | `bundle()` succeeds — the project compiles | `gates.bundle.pass` |
| D2 | Composition exists | `<comp_id>` is registered | `gates.composition_exists.pass` |
| D3 | Dimensions | `width/height` == `--expect-width/--expect-height` | `gates.dimensions.pass` |
| D4 | Duration | `durationInFrames` == `--expect-duration-frames` (the planned `computeMasterDuration`) | `gates.duration.pass` |
| D5 | Stills render | every filmstrip still renders (a `SafeImg`/`SafeVideo` `cancelRender()` fails this) | `gates.stills_render.pass` |
| D6 | Intro/outro present-iff-config | if `intro_frames>0` an intro card is expected (and `outro_frames>0` an outro); confirmed visually at the first/last frames | `expectations` + V7 |
| D7 | Chapter card iff title | a `ChapterCard` is expected exactly when a chapter title was extracted | `expectations` + V8 |

If D1–D5 don't all pass, `status` is `fail` and the exit code is `2` — fix the
single failing gate and re-run before touching anything visual.

---

## VISION (judge filmstrip.md against these)

Each frame in `filmstrip.md` carries an **Expect:** line (anchor / beat kind /
caption word / zoom target). Compare the image to its expectation.

- **V1 — Caption overflow.** Look at every frame with a caption word. *Fail* if
  text runs off the frame edge, is clipped by the safe area, or (on a 9:16
  crop) spills outside the visible vertical band. *Good:* caption fully inside
  the frame with margin, legible at filmstrip scale.

- **V2 — Blank terminal frame.** Look at `beat=into-*` / `out-of-*` and coverage
  frames over the terminal. *Fail* if the terminal area is empty/black when it
  should show rendered output (a dropped PNG that didn't trigger cancelRender,
  or a wrong frame index). *Good:* terminal shows plausible text content.

- **V3 — Brand not applied.** Any frame. *Fail* if colors/typography are
  obviously default-browser (Times New Roman, pure white bg, unstyled) instead
  of the active profile's palette/fonts. *Good:* the profile's background,
  accent, and display face are visibly in use.

- **V4 — Zoom clip / mis-center.** Look at `zoom on "…"` frames. *Fail* if the
  zoomed view shows out-of-frame black gutters, or the zoom is centered away
  from the labeled click target. *Good:* the click region fills the frame, no
  empty edges (the `clampZoomWindow` invariant held).

- **V5 — Frozen frame where a ramp was expected.** Compare the two frames around
  a `speedramp` beat (`into-speedramp` vs `out-of-speedramp`). *Fail* if they
  are pixel-identical (the ramp isn't advancing the PNG sequence). *Good:* the
  terminal content differs between them.

- **V6 — Wrong word captioned.** Look at each caption-word frame. *Fail* if the
  on-screen caption clearly doesn't match the **Expect** word (off-by-a-line
  sync, or the whole transcript is shifted). *Good:* the displayed text contains
  or is near the expected word.

- **V7 — Intro/outro present-iff-config.** First frame (`anchor=first`) and last
  (`anchor=last`). *Fail* if config expected an intro/outro card but the frame
  shows raw terminal/video instead (or vice-versa: a card when none was
  expected). *Good:* matches the D6 expectation.

- **V8 — Chapter title content.** If a `ChapterCard` was expected (D7), the
  frame after the intro should show the chapter title text. *Fail* if it's
  missing, truncated, or shows a placeholder. *Good:* the verbatim chapter
  title, styled in the profile's display face. (If no chapter title was
  extracted, V8 is N/A — do not flag.)

### Animated icons / motion primitives (V9–V12)

Apply these only to cuts that use animated icons (e.g. the `golden-icons`
showcase). On a cut with no icons, V9–V12 are N/A — do not flag.

- **V9 — Recipe visibly animating.** Look at the recipe icons across the
  filmstrip (drawOn / popIn / spin / burst / morph). *Fail* if a recipe is
  frozen in a fully-static end-state on every sampled frame (e.g. a draw-on that
  is always 100% drawn, a spinner at the same angle), i.e. no motion is evident.
  *Good:* at least one sampled frame shows each recipe mid-animation — a
  partially-drawn stroke, an in-between scale, a rotated spinner, particles in
  flight, or an intermediate morph shape.

  *Deterministic backstop (Phase 1.1):* `tests/test_icons_motion.py` already
  proves each recipe is **in motion** — it renders a guaranteed mid-animation
  frame (progress 0.5) on a per-recipe probe composition and fails if the
  start/mid/end stills are identical. So V9 here is only about recipe
  *correctness* (does the motion read as the right gesture); "is it moving at
  all" is machine-checked, not left to the eye.

- **V10 — Brand recolor applied.** Any icon frame. *Fail* if an icon renders in
  a default color (black/white) instead of the active profile's accent, or the
  stroke is the library default rather than the themed color. *Good:* every icon
  is stroked in the profile palette (accent/glow), matching the rest of the cut.

- **V11 — No clip / no blank icon.** Any icon frame. *Fail* if an icon is cut off
  by the frame edge, overflows its cell into a neighbour, or an icon cell is
  blank/black where the registry says an icon exists (a bad path or failed
  resolve). *Good:* each icon sits fully inside its cell, legible at filmstrip
  scale.

- **V12 — Ripple centered on its anchor.** Look at `zoom on "ripple-*"` (or any
  click-ripple) frames. *Fail* if the ripple ring is drawn away from the labeled
  click point (wrong x/y), or is missing entirely at its anchor sample frame.
  *Good:* the ring is concentric on the anchor's normalized (x, y) position.

### Bring-your-own Lottie (V13)

Apply only to cuts that render a Lottie animation (e.g. the `golden-lottie`
showcase). On a cut with no Lottie, V13 is N/A — do not flag.

- **V13 — Lottie renders and is on-brand.** Look at the Lottie frames. *Fail* if
  the Lottie cell is blank/black (failed to load — a bad `src`/`delayRender`
  that never resolved), or renders in a colour clearly off the active palette
  when the file was meant to be recolored. *Good:* the Lottie shape is visible,
  recoloured toward the brand accent for flat-fill files (gradients excepted —
  those are documented as not themeable), and looks consistent frame-to-frame
  (no flicker — an expression-driven file that slipped the ingest guard would
  jitter between renders; the deterministic check `test_icons_motion.py ::
  test_golden_lottie_is_deterministic_and_animates` is the machine backstop for
  that).

### Per-theme example packs (V14–V15)

Apply only to cuts that render the per-theme example packs (e.g. the
`golden-themes` showcase). On a cut without them, V14–V15 are N/A — do not flag.

- **V14 — Each theme's pack is on-brand.** Look at the `golden-themes` frames.
  *Fail* if a theme panel renders the icons in a colour clearly off that theme's
  accent (e.g. cyan icons on the `foolswithtools-brand` cream panel, or
  acid-green on the `default` dark panel), on the wrong canvas background, or
  with a blank/black icon cell. *Good:* the left panel is the `default` theme
  (cyan on near-black), the right is `foolswithtools-brand` (acid-green on
  cream), each icon recoloured to its own theme accent, nothing clipped.

- **V15 — Switching the theme visibly changes the motion.** Compare the same
  icon cell across the two panels (the showcase) or across the two neutral probe
  comps. *Fail* if the two themes render the pack identically (same recipe, same
  draw progress, same particle density) — that would mean the `motion` block is
  not driving the pack. *Good:* the difference is legible — e.g. the `sparkles`
  cell is further drawn under `default` (`pop` easing) than under
  `foolswithtools-brand` (`scribble` easing), and the `bell` burst is denser
  under `foolswithtools-brand` (higher `particleIntensity`). The deterministic
  backstop is `test_themes_e2e.py :: test_themes_differ_so_switching_changes_motion`
  (neutral palette held constant → any byte difference is motion).

---

## Verdict format (subagent → loop)

Return, per V-item: `PASS` / `FAIL` / `N/A`, and for any `FAIL` the frame
number(s) and a one-line reason. The loop fixes the smallest thing per failing
V-item, re-runs `verify_render.py --stills-only`, and re-judges. The same V-item
failing on the same frame twice → escalate to the user.
