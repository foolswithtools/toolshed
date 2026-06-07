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

---

## Verdict format (subagent → loop)

Return, per V-item: `PASS` / `FAIL` / `N/A`, and for any `FAIL` the frame
number(s) and a one-line reason. The loop fixes the smallest thing per failing
V-item, re-runs `verify_render.py --stills-only`, and re-judges. The same V-item
failing on the same frame twice → escalate to the user.
