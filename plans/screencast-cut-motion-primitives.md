# Plan: Motion primitives (animated icons) for screencast-cut

## Context

`screencast-cut` (in `plugins/screencast-cut/`) turns a terminal `.cast` / screen `.mp4` (+ audio) into a Remotion project. It was recently hardened: the fragile timing math now lives in tested twins (`scripts/timing_math.py` + `scene-templates/timing.ts`), there are JSON-schema contracts, a shared render-verification harness (`plugins/remotion-video/.../scripts/verify_render.py` + `_verify_helper.mjs`), a `RUBRIC.md`, and a committed **golden Remotion project** under `plugins/screencast-cut/skills/screencast-cut/tests/fixtures/golden-project/` that is rendered for real in pytest. Read `plans/screencast-cut-hardening.md` (or the git history of that work) before starting — this plan builds directly on that harness and reuses its patterns.

**Goal of this work:** add a small library of **animated icon / motion primitives** so cuts can be richer (a ✓ when a command succeeds, an arrow at terminal output, a ripple on a click, brand flourishes on cards) — *consistently and on-brand*, using the harness we already trust.

**The core design decision (settled):** animation is **code, not data**. We do NOT use Lottie in this work (Phase 1). Lottie animations are pre-made JSON "recipe" files, but (a) the big catalogs (LottieFiles, Lordicon, useAnimations) *forbid redistributing the JSON files* — fatal for a public OSS repo — and (b) Lottie is only conditionally frame-deterministic in Remotion (expression-driven files flicker in headless renders) and can't be recolored to a brand palette cleanly. So Phase 1 = animate permissive static SVGs ourselves with Remotion's frame-deterministic primitives. Lottie is deferred to **Phase 2** as a *bring-your-own* escape hatch only (never bundled).

**Why this fits:** Remotion ships the animation engine for free — `@remotion/paths` `evolvePath()` (deterministic stroke draw-on), `interpolatePath()` (morph), `getPointAtLength()` (trace), `@remotion/shapes` (parametric rings/bursts with built-in draw-on), and `spring()`/`interpolate()` (pop/rotate). Static icons come from permissive sets (Lucide ISC, Tabler MIT) that we *can* bundle and redistribute. No existing library does frame-deterministic animated icons for Remotion, so this fills a real gap.

## Decisions locked (from the design discussion)

- **(1+2) Sources = both, feeding one engine.** A small **curated local icon floor** (always-present, offline, brand-tuned) *plus* a **lightweight Iconify puller** (resolve `set:name` → fetch one SVG → save into the project → local/static forever; scoped to permissive sets only). The recipe engine consumes "an SVG" regardless of source.
- **(3) Theme-tunable motion.** A small `motion` block in each profile's `style-guide.ts` (default recipe, duration, easing reference, particle intensity), falling back to global `config.json` defaults. Custom/BYO themes get it for free. Precedence: **config default < profile `motion` < per-use override**.
- **(4) Two phases.** Phase 1 = SVG + recipes + theme-tuned motion. Phase 2 = Lottie BYO hatch. **Phase 1 ships and is signed off BEFORE Phase 2 is built.**
- **Recipes (~5):** `drawOn` (stroke reveal via `evolvePath`), `popIn` (spring scale), `spin` (rotate, for loaders), `burst`/`ripple` (particles via our own pure geometry + `@remotion/shapes`), `morph` (`interpolatePath` between two compatible icon paths).
- **Beachhead:** an animated **click-ripple on the MP4 zoom path**, driven by the `zoom_anchors.json` we already compute (`t_s`, `x`, `y`). It needs no icon set (just `@remotion/shapes` `Circle`), so it's the cheapest primitive that proves the whole pattern end-to-end.
- **Curated source:** prefer **Lucide (ISC)** as the primary (stroke-based, matches the brand aesthetic), **Tabler (MIT)** as secondary. Bundle a `THIRD-PARTY-NOTICES` file listing each set, license, and source URL.
- **Brand-claim guardrail (`CLAUDE.md`) still applies** — keep the two forbidden brand words far apart in any committed file; `CLAUDE.md` spells out the exact rule and the safe-token allowlist. Run `bash scripts/check-no-anthropic-remotion-claim.sh` before every push.

---

# PHASE 1 — SVG motion primitives (EXECUTE THIS)

## Definition of rock solid (Phase 1 exit condition)

The loop stops Phase 1 when ALL hold:

1. **`pytest plugins/screencast-cut` green, 0 unexpected skips** — existing suite + new motion-math twin tests + Iconify-puller resolver tests.
2. **Recipe/motion math twins are bit-identical** — `timing_math.py` and `timing.ts` agree on every shared function (parity asserted in tests; half-up rounding preserved as established in the hardening).
3. **The golden `golden-icons` composition builds and renders for real** — actual `bundle()` + `renderStill()`, not stubbed.
4. **`verify_render.py` exits 0 on `golden-icons`** (bundle + duration gate + every filmstrip still renders).
5. **Filmstrip vision pass clean** against `RUBRIC.md` plus the new icon checks: each recipe is visibly mid-animation at its sampled frame, the brand recolor is applied (not default color), nothing clips the frame, no blank/black icon, and the click-ripple is centered on its anchor.
6. **Theme-tunability proven** — the `motion` block resolves with correct precedence (config < profile < per-use), shown by a test; switching the active profile changes a sampled icon's motion.
7. **Licensing + pre-push clean** — curated SVGs carry `THIRD-PARTY-NOTICES`; the Iconify puller refuses non-permissive sets; `tsc --noEmit` clean in the golden project; brand-claim guardrail passes; every touched JSON valid; version bump + `marketplace.json` + `USAGE.md` updated.

## Milestones (dependency order). Each has a **Gate**.

### P1-M1 — Motion math in the tested twins (+ unit tests)
Add the *pure* geometry/timing helpers our recipes need to **both** `plugins/screencast-cut/skills/screencast-cut/scripts/timing_math.py` and `scene-templates/timing.ts` (the established twin pair — same copy/verify machinery). `spring()`, `evolvePath()`, `interpolatePath()` are Remotion built-ins used directly in TS; do NOT reimplement them. The twin functions are the bits *we* own:
- `animation_phase(frame, start_frame, duration_frames)` → clamped progress 0..1.
- `staggered_progress(progress, index, count, overlap)` → per-element progress for multi-path draw-on stagger.
- `burst_particles(count, progress, max_radius)` → deterministic list of `{x, y, scale, opacity}` (angle = `i/count * 2π`; pure function of progress).
- `ripple_geometry(progress, max_radius)` → `{radius, opacity}`.
Keep half-up rounding (`_round_half_up` / `Math.round`) where indices are produced. Mirror VERBATIM across the twins.
**Gate:** `pytest scripts/test_timing_math.py` green, including new parity/regression cases for each function (e.g. `burst_particles` angles, `animation_phase` clamping at boundaries, ripple opacity monotonic).

### P1-M2 — Recipe components + `AnimatedIcon` + `ClickRipple`
New under `scene-templates/`:
- `recipes.ts` (or per-recipe files) implementing `drawOn`, `popIn`, `spin`, `burst`, `morph` as frame-deterministic helpers built on `@remotion/paths` (`evolvePath`, `interpolatePath`), `@remotion/shapes`, `spring`, `interpolate`, and the M1 twin math. Add `@remotion/paths` / `@remotion/shapes` to the project's deps (they're part of the Remotion install).
- `AnimatedIcon.tsx` — takes an icon (resolved to its SVG `path` `d` string(s)), a recipe name, `color`/`strokeWidth` (from `src/brand/active`), `startFrame`, `durationInFrames`; renders the animated SVG. **Implementation note:** `popIn`/`spin`/`burst` wrap the whole `<svg>` in a transform/opacity → work on ANY icon. `drawOn` needs path `d` strings (apply `evolvePath` per `<path>`, staggered via M1 `staggered_progress`); for icons that aren't path-only, `drawOn` falls back to a clip-wipe or `popIn` — document the fallback. `morph` requires two structurally-compatible paths.
- `ClickRipple.tsx` (the beachhead) — `@remotion/shapes` `Circle` driven by `ripple_geometry` around an anchor frame; reads anchor `x`/`y` from `zoom_anchors.json`, positioned at the click point. Recolor from brand accent.
- Recolor: icons render with `stroke="currentColor"` / `fill="currentColor"`; the component passes the brand color, so a single prop themes the icon.
**Gate:** `tsc --noEmit` clean; a scripted `npx remotion still` of a tiny test composition renders each recipe without throwing (read at least one PNG to confirm it's not blank).

### P1-M3 — Curated local icon floor + license notices
- Add ~12–15 SVGs under `scene-templates/icons/` chosen for screencast/tutorial work: e.g. `check`, `x`, `arrow-right`, `mouse-pointer-click`, `terminal`, `loader`, `bell`, `sparkles`, `download`, `play`, `folder`, `copy`, `chevron-right`, `alert-triangle`. Source from **Lucide (ISC)** primarily. Normalize draw-on candidates to `<path>`-only where practical (convert `<line>`/`<circle>`/`<polyline>` primitives to paths) so `drawOn` works.
- A small registry (`icons/index.ts` or `icons.json`) mapping name → SVG (path `d`(s) + viewBox).
- A `THIRD-PARTY-NOTICES` (or `LICENSES/`) file listing each icon set, its license (ISC/MIT), and source URL, kept next to the bundled SVGs.
**Gate:** every curated icon resolves through `AnimatedIcon`; notices file present and accurate; a still renders a curated icon recolored to a brand color.

### P1-M4 — Iconify puller (fetch-once-then-local)
New `scripts/fetch_icon.py` (or `.mjs`): given `set:name` (e.g. `lucide:rocket`), resolve the SVG and write it into the project's icon area as a local static file, plus append the source set's license to `THIRD-PARTY-NOTICES`.
- **Permissive-set allowlist** — only ISC/MIT/Apache sets (lucide, tabler, ph, heroicons, mdi, …). Refuse anything else with a clear message. The allowlist + the per-set license metadata are the safety mechanism.
- **Fetch mechanism:** Iconify public API (`https://api.iconify.design/<set>/<name>.svg`) at *fetch* time, OR `@iconify/json` if added as a devDep — recommend the API to avoid a tens-of-MB dependency. Either way the result is written into the project and is **local/static thereafter** (one network call the first time, then offline/reproducible).
- **Tests:** unit-test the resolver/allowlist/SVG-emit logic against committed fixtures (offline). Gate the *live network* path behind a skip marker (like the node-gated e2e), so CI/offline runs don't depend on the network.
**Gate:** `pytest` puller tests green (allowlist refuses a disallowed set; a fixture `set:name` produces a valid SVG + a notice entry).

### P1-M5 — Theme-tunable motion block
- Add a `motion` block to `plugins/remotion-video/skills/remotion-video/templates/default/style-guide.ts` (and `foolswithtools-brand/style-guide.ts`): keys like `defaultRecipe` (`drawOn|popIn|...`), `durationInFrames`, `easing` (reference an existing profile easing, e.g. `camera`/`pop`), `particleIntensity`. Document each.
- Add matching global defaults to `plugins/screencast-cut/skills/screencast-cut/config.json` so a profile only declares deviations.
- Wire `AnimatedIcon`/recipes to read defaults from `src/brand/active`'s `motion` block, overridable per-use. Document the precedence (**config < profile < per-use**) in `SKILL.md` (a new "Animated icons / motion primitives" subsection in Phase 4 scene-building).
**Gate:** a test asserts precedence resolution; `tsc --noEmit` clean; SKILL.md updated. Keep the surface SMALL — theme-level defaults only, no per-icon-per-theme matrix.

### P1-M6 — Golden `golden-icons` composition + e2e + verify
- Add a new composition `golden-icons` to the golden project (register in its `src/Root.tsx`, add `videos/golden-icons/Root.tsx` + scenes) that exercises **every recipe** (draw-on check, pop-in, spin loader, burst/sparkle, morph, and the `ClickRipple`) with a brand recolor. Commit any needed source manifest (e.g. a small `zoom_anchors.json` for the ripple) so the e2e is offline-deterministic — use **curated local icons only** (no network in the golden render).
- Extend `tests/test_verify_render_e2e.py` (or a new `test_icons_e2e.py`) to run `verify_render.py` against `golden-icons`: assert exit 0, `status:pass`, duration gate matches, every still renders, and the filmstrip index set is reproducible.
- Add icon-specific vision items to `RUBRIC.md` (recipe visibly animating mid-frame, recolor applied, no clip/blank, ripple centered).
**Gate:** `golden-icons` renders for real; `verify_render.py` exits 0; filmstrip vision pass clean.

### P1-M7 — Docs, version, marketplace, pre-push
- `USAGE.md`: a short "Animated icons" section (what's available, local vs. pulled, how to ask for one in a prompt).
- Version bump: `screencast-cut` → `0.5.0` (new feature); bump `remotion-video` if its templates changed (the `motion` block / any shared bits). Update `.claude-plugin/marketplace.json` if needed. **Reconcile versioning:** the expansion plan reserved `0.5.0` for a TTS slice — renumber that reservation (TTS → later) and note it, so numbers don't collide.
- Pre-push ritual: `bash scripts/check-no-anthropic-remotion-claim.sh`; `python3 -m json.tool` on every touched JSON; `tsc --noEmit` in the golden project; full `pytest`.
**Gate:** the entire **Definition of rock solid (Phase 1)** checklist passes.

## Loop protocol (Phase 1)

Maintain the `## PROGRESS — PHASE 1` section at the bottom. Each iteration:
1. Read `## PROGRESS — PHASE 1`; pick the lowest-numbered milestone not yet `[done]`.
2. Do its tasks; run its **Gate**.
3. Mark `[done]` with a one-line note, or `[blocked: <reason>]` and continue with an offline-gated fallback where possible. Escalate to the human ONLY if truly blocked on something external (e.g. a live network call a test genuinely needs).
4. When P1-M1…M7 are all `[done]`, run the full **Definition of rock solid (Phase 1)**. If all 7 pass → **STOP and report. DO NOT begin Phase 2.** Phase 2 requires explicit human sign-off.

The heavy tools (agg, ffmpeg, whisper-cli, node, npx) are installed — do the **real** end-to-end render; do not stub it. Run with permissive permissions (the session will run `npm ci`/`pytest`/`remotion`/a network fetch for one puller test).

---

# PHASE 1.1 — Golden-icons sampling rigor (quick fix; run FIRST this round)

The Phase-1 review noted the `golden-icons` filmstrip can sample frames in a recipe's hold/plateau window, so a recipe broken ONLY mid-animation could pass the deterministic gate and lean entirely on the human vision pass — the same shape as the earlier `ZoomedSection` gutter bug. Close that.

## Definition of rock solid (Phase 1.1)
1. For every recipe (`drawOn`, `popIn`, `spin`, `burst`, `morph`) + `ClickRipple` in `golden-icons`, the e2e renders a frame **guaranteed to be mid-animation** (not in the start/hold/end plateau).
2. A deterministic **motion assertion** proves each recipe actually animates: render start / mid / end stills for the recipe and assert they are **not all identical** (a static or fallen-flat recipe → identical frames → hard failure). Limitation to document: this catches "no motion", not "wrong-but-still-moving recipe" — recipe *correctness* stays with the vision/RUBRIC pass.
3. `pytest` green; pre-push green.

## Milestone
- **P1.1-M1** — Make the `golden-icons` sampling include a computed mid-animation frame per recipe beat (extend `verify_render`'s frame computation, or pass explicit probe frames from the composition layout), and add a test that renders start/mid/end per recipe scene and asserts pixel non-identity (PNG byte/hash compare). Update RUBRIC if needed.
**Gate:** the motion-assertion test is green AND demonstrably catches a broken recipe — temporarily swap one recipe for a static placeholder, confirm the test FAILS, then revert. (Mutation sanity-check: a gate that can't fail proves nothing.)

---

# PHASE 2 — Lottie bring-your-own hatch (ACTIVE THIS ROUND, after Phase 1.1)

> The human has signed off Phase 1 and activated Phase 2. This round: run **Phase 1.1, then Phase 2**, and **STOP at the Phase 2 gate**. Phases 3 and 4 below are DEFERRED — do not start them.

## Scope
A *bring-your-own* path: the user points the plugin at a Lottie file **they** have the rights to; we render it locally with `@remotion/lottie` and **never bundle or redistribute the JSON**. Lottie is a second-class citizen — it cannot be cleanly theme-recolored and is only conditionally deterministic, so it sits beside the SVG system, not inside it.

## Definition of rock solid (Phase 2 exit condition)
1. `pytest` green incl. a Lottie path that renders a **minimal Lottie fixture we AUTHOR ourselves** (owned → license-clean to bundle; a CC0 file is also fine — never a pulled third-party one) deterministically.
2. The golden project gains a `golden-lottie` composition (the self-authored fixture, **vetted to contain no After-Effects expressions**) that renders for real; `verify_render.py` exits 0.
3. **Expression-determinism guard**: an ingest check flags/rejects expression-driven Lottie files (which flicker headlessly) with a clear message.
4. **Licensing guardrail enforced**: a check + docs make it impossible to accidentally commit third-party Lottie JSON; only CC0/user-supplied-at-runtime files are allowed.
5. Recolor-where-feasible via `@lottiefiles/lottie-js` (MIT) for flat-fill files, documented as best-effort (gradients/expressions excluded).
6. Pre-push clean (guardrail, JSON, tsc, pytest); `USAGE.md` documents the BYO flow and the "we never ship your Lottie" rule.

## Milestones (outline)
- **P2-M1** — `@remotion/lottie` wiring + a `LottieIcon` scene that maps `useCurrentFrame()` deterministically; load JSON via `delayRender`/`continueRender`.
- **P2-M2** — Ingest vetting: detect expressions; recolor via `@lottiefiles/lottie-js` for flat-fill; surface what couldn't be themed.
- **P2-M3** — Licensing guardrail (no bundled third-party JSON; CC0 fixture only in-repo; BYO files read from the user's path at runtime) + docs.
- **P2-M4** — `golden-lottie` composition + e2e + verify + RUBRIC items; version bump + marketplace + USAGE.

## Loop protocol (Phase 2)
This round is active. After Phase 1.1, add a `## PROGRESS — PHASE 2` section, execute P2-M1…M4 with gates, run **Definition of rock solid (Phase 2)**, then **STOP and report**. Do NOT start Phase 3 or Phase 4 — each needs its own explicit go-ahead.

---

# PHASE 3 — Per-theme example animation packs (our engine; DEFERRED — needs explicit go-ahead)

> Confirmed reframe: built with the **Phase-1 SVG engine**, NOT Lottie — bundleable, deterministic, theme-aware. (Originated Lottie per theme is Phase 4.)

## Scope
For each shipped demo theme (default, foolswithtools-brand, and any other demo themes the project ships), a small curated **example pack** — a set of `AnimatedIcon`/recipe usages tuned to that theme's motion personality via its `motion` block — that shows off the theme. Swapping the active theme changes the pack's motion. These are reference/demo compositions + a short gallery doc the skill can draw on when assembling a cut.

## Definition of rock solid (Phase 3)
1. An example pack exists for **every** shipped demo theme; each renders for real via a golden composition; `verify_render.py` exits 0; vision pass clean.
2. **Theme-tunability demonstrated, not just asserted** — switching the theme visibly changes the same pack's motion (e.g. side-by-side stills differ in timing/easing/intensity).
3. `pytest` green; gallery/SKILL docs updated; pre-push green.

## Milestones (outline)
- **P3-M1** — enumerate shipped demo themes; spec a small example-pack per theme (which icons/recipes, tuned by that theme's `motion` block).
- **P3-M2** — a `golden-themes` (or per-theme) showcase composition rendering each pack; e2e + verify + RUBRIC items.
- **P3-M3** — gallery doc + SKILL.md note on per-theme example packs; version bump + marketplace + USAGE.

---

# PHASE 4 — Originated Lottie per demo theme (DEFERRED — needs explicit go-ahead; depends on Phase 2)

> The licensing-clean way to ship per-theme Lottie: we **author** one original Lottie motif per theme, so we OWN it (bundleable) and vet it expression-free (deterministic via Phase 2's `@remotion/lottie` path). This is NOT pulling third-party Lottie.

## Scope
One signature, original Lottie animation per shipped demo theme, in that theme's palette/personality, committed as an owned/CC0 asset, rendered through the Phase-2 `LottieIcon` integration.

**Authoring approach:** prefer **programmatic/hand-authored simple Lottie JSON** (shape + keyframes, no expressions) generated in-repo — fully owned, deterministic, no After Effects needed. (AE + Bodymovin would allow richer motifs but is outside an autonomous loop's reach; note it as a manual upgrade path.) No recolor needed — authored directly in each theme's palette.

## Definition of rock solid (Phase 4)
1. One **original, owned, expression-free** Lottie per shipped demo theme, in that theme's palette, committed with a provenance/LICENSE note marking it an original work (distinct from BYO third-party Lottie).
2. Each renders **deterministically** via the Phase-2 `LottieIcon` path; a golden composition renders them all for real; `verify_render.py` exits 0; vision pass clean.
3. `pytest` green; pre-push green; version bump + marketplace + USAGE.

## Milestones (outline)
- **P4-M1** — per-theme Lottie motif spec; a small generator (or hand-authored JSON) emitting owned, expression-free Lottie in each theme's palette.
- **P4-M2** — golden composition rendering each theme's Lottie via `LottieIcon`; e2e + verify + RUBRIC + provenance note.
- **P4-M3** — docs + version + marketplace + pre-push.

---

## Verification (end-to-end, Phase 1)

```
cd /Users/t/_repos/foolswithtools/toolshed
python3 -m pytest plugins/screencast-cut -q        # all green, incl. golden-icons e2e

# the icon e2e gate (needs node; runs npm ci once in the golden project)
python3 plugins/remotion-video/skills/remotion-video/scripts/verify_render.py \
    plugins/screencast-cut/skills/screencast-cut/tests/fixtures/golden-project golden-icons \
    --expect-duration-frames <known> --expect-width <W> --expect-height <H> --json
# expect exit 0, status:pass; then read .checks/filmstrip.md and judge vs RUBRIC.md

# pre-push ritual
bash scripts/check-no-anthropic-remotion-claim.sh
python3 -m json.tool plugins/screencast-cut/.claude-plugin/plugin.json > /dev/null
python3 -m json.tool plugins/screencast-cut/skills/screencast-cut/config.json > /dev/null
python3 -m json.tool .claude-plugin/marketplace.json > /dev/null
(cd plugins/screencast-cut/skills/screencast-cut/tests/fixtures/golden-project && npx tsc --noEmit)
```

## Critical files (Phase 1)

- `plugins/screencast-cut/skills/screencast-cut/scripts/timing_math.py` + `scene-templates/timing.ts` — add the pure motion math (twins, parity-tested).
- `plugins/screencast-cut/skills/screencast-cut/scripts/test_timing_math.py` — new motion-math tests.
- `plugins/screencast-cut/skills/screencast-cut/scene-templates/{recipes.ts,AnimatedIcon.tsx,ClickRipple.tsx,icons/…}` — new; the engine + curated floor.
- `plugins/screencast-cut/skills/screencast-cut/scripts/fetch_icon.py` (+ tests) — Iconify puller.
- `plugins/screencast-cut/skills/screencast-cut/THIRD-PARTY-NOTICES` — icon license attributions.
- `plugins/remotion-video/skills/remotion-video/templates/default/style-guide.ts` (+ `foolswithtools-brand/…`) — the `motion` block.
- `plugins/screencast-cut/skills/screencast-cut/config.json` — global motion defaults.
- `plugins/screencast-cut/skills/screencast-cut/SKILL.md` + `USAGE.md` — usage + precedence docs.
- `plugins/screencast-cut/skills/screencast-cut/RUBRIC.md` — icon vision checks.
- `…/tests/fixtures/golden-project/` (+ `src/Root.tsx`, `videos/golden-icons/…`) — the showcase composition.
- `…/tests/test_verify_render_e2e.py` (or `test_icons_e2e.py`) — the icon e2e gate.
- `plugins/screencast-cut/.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` — version bump.
- `plans/screencast-cut-expansion.md` — renumber the TTS `0.5.0` reservation.

## Notes

- Reuse the hardening harness — do not invent a parallel one. The `motion` math goes in the existing `timing` twins; the showcase goes in the existing golden project; verification goes through the existing `verify_render.py` + `RUBRIC.md`.
- Keep it SMALL (the human's explicit steer): 5 recipes, ~12 curated icons, theme-level motion defaults only. The Iconify puller is the long-tail widener; the curated floor is the offline baseline.
- `drawOn` only works on path-based SVGs — handle the fallback explicitly; don't let a non-path icon silently fail to animate.
- After Phase 1 ships: save a project memory noting the motion-primitives slice landed (commit shas), how to use it, and that Phase 2 (Lottie) is planned but not built.

## PROGRESS — PHASE 1

- [done] P1-M1 — Motion math in timing twins + tests — added `animation_phase`/`staggered_progress`/`burst_particles`/`ripple_geometry` to `timing_math.py` + verbatim TS twin in `timing.ts`; 57 tests green (boundary clamping, stagger windows, burst angles, ripple monotonicity).
- [done] P1-M2 — Recipe components + AnimatedIcon + ClickRipple — `recipes.ts`/`AnimatedIcon.tsx`/`ClickRipple.tsx` in scene-templates; added `@remotion/paths`+`@remotion/shapes` 4.0.473 to golden project; `icon-smoke` smoke composition (inline icons) tsc-clean and renders all 5 recipes + ripple mid-animation, brand-recolored, non-blank (verified by eye at frame 12).
- [done] P1-M3 — Curated local icon floor + license notices — 14 Lucide (ISC) SVGs under `scene-templates/icons/` + `icons.json` registry (generated by new `scripts/icon_svg.py` normalizer, primitive→path so drawOn always works) + typed `index.ts` + `THIRD-PARTY-NOTICES`. Verified by eye: every curated icon resolves through `AnimatedIcon`, drawn-on + recolored to brand accent.
- [done] P1-M4 — Iconify puller (fetch-once-then-local) + tests — `scripts/fetch_icon.py`: `set:name` → Iconify API → normalized local SVG + icons.json entry + idempotent THIRD-PARTY-NOTICES line. Permissive allowlist (ISC/MIT/Apache only) refuses others. 40 tests green incl. live-network fetch (ran for real) + offline fixture path.
- [done] P1-M5 — Theme-tunable motion block + precedence — `motion` block in default + foolswithtools-brand templates + golden default profile; `config.json` `"motion"` defaults; `resolve_motion`/`resolveMotion` + `DEFAULT_MOTION` twins; `AnimatedIcon` resolves config<profile<per-use, easing drives draw/morph, particleIntensity scales burst. SKILL.md Phase-4 subsection added. Precedence + config-mirror + profile-differ tests green (127 passed).
- [done] P1-M6 — Golden `golden-icons` composition + e2e + verify — `videos/golden-icons/` showcase (every recipe + ClickRipple, curated icons only, brand-recolored, committed `zoom_anchors.json`) registered as `golden-icons`; `icon-smoke` scaffold removed. `verify_render.py` exits 0; new e2e test green (3 e2e pass, 7s). Vision pass clean by eye: recipes mid-animation, recolored, no clip/blank, both ripples centered on anchors. RUBRIC V9–V12 added.
- [done] P1-M7 — Docs + version + marketplace + pre-push — USAGE.md "Animated icons" section; `screencast-cut` 0.5.0, `remotion-video` 0.7.1; marketplace.json + plugin.json descriptions mention animated icons; TTS reservation renumbered (A→0.6.0, B→0.7.0, C→0.8.0) in `screencast-cut-expansion.md`. Pre-push ritual all green: guardrail OK, every touched JSON valid, tsc clean, `pytest plugins/screencast-cut` = 130 passed / 0 skips.

### Definition of rock solid (Phase 1) — ALL PASS
1. pytest green, 0 skips — ✓ 130 passed.
2. Motion-math twins mirrored verbatim, half-up preserved; new parity/regression tests green — ✓.
3. `golden-icons` builds + renders for real (bundle + renderStill) — ✓.
4. `verify_render.py` exits 0 on `golden-icons` — ✓.
5. Filmstrip vision pass clean (recipes mid-animation, recolor applied, no clip/blank, ripples centered on anchors) — ✓ judged by eye.
6. Theme precedence (config<profile<per-use) + profile-switch-changes-motion proven by tests — ✓.
7. Licensing + pre-push clean (THIRD-PARTY-NOTICES, puller refuses non-permissive, tsc, guardrail, JSON, version+marketplace+USAGE) — ✓.

**Phase 1 COMPLETE. Stopped before Phase 2 (Lottie) — requires explicit human go-ahead.**

## PROGRESS — PHASE 1.1

- [done] P1.1-M1 — Mid-animation sampling + per-recipe motion assertion (mutation-checked) — added `videos/golden-icons/MotionProbe.tsx` (6 single-primitive probe comps `motion-probe-{drawOn,popIn,spin,burst,morph,ripple}`, no Loop, 30-frame beat) registered in `src/Root.tsx`; `tests/test_icons_motion.py` renders frames 0/15/30 per probe and asserts non-identity + mid≠start (frame 15 = guaranteed progress 0.5). Mutation sanity-check: swapping drawOn → static placeholder made the test FAIL (1 distinct hash), reverted. RUBRIC V9 notes the deterministic backstop. tsc clean; 6 motion + 3 e2e tests green.

## PROGRESS — PHASE 2

- [done] P2-M1 — `@remotion/lottie` wiring + `LottieIcon` scene (frame-deterministic) — added `@remotion/lottie@4.0.473` dep; `scene-templates/LottieIcon.tsx` (+ golden copy) supports `animationData` (in-repo) or `src` (BYO, staticFile→fetch behind `delayRender`/`continueRender`); `<Lottie>` maps useCurrentFrame so expression-free files render bit-identically. `golden-lottie` composition renders the owned-pulse fixture for real — verify_render exits 0, eyeballed: brand-cyan pulsing circle, non-blank. tsc clean.
- [done] P2-M2 — Expression vetting + best-effort recolor via `@lottiefiles/lottie-js` — `scripts/lottie_ingest.py`: `find_expressions`/`assert_no_expressions` (rejects AE expressions — `x`-string discriminator, eased keyframes not flagged), `recolor_flat_fills` (flat `fl`/`st` → brand color, surfaces gradients/animated/expression colors as un-themable), CLI. `scripts/recolor_lottie.mjs` = the named-lib path (`@lottiefiles/lottie-js`, resolved from project root via createRequire). 14 ingest tests green incl. node-gated parity (lib recolor == python recolor → `[1,0.533,0,1]`).
- [done] P2-M3 — Licensing guardrail (no bundled third-party JSON; self-authored/CC0 only) + docs — `tests/test_lottie_guardrail.py` scans tracked JSON via `git ls-files`, fails any Lottie-shaped file lacking an OWNED/CC0 `PROVENANCE` note (positive + negative controls green). owned-pulse + test fixtures carry PROVENANCE. USAGE.md "Bring-your-own Lottie" section ("we never ship your Lottie" + expression/recolor rules); SKILL.md Phase-4 Lottie escape-hatch bullet.
- [ ] P2-M4 — `golden-lottie` composition + e2e + verify + RUBRIC; version + marketplace + USAGE

<!-- Phases 3 and 4 are DEFERRED: do not add their PROGRESS sections or execute them until explicitly activated. This round stops at the Phase 2 gate. -->

