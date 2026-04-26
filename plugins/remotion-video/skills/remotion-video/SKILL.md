---
name: remotion-video
description: Use this skill when the user asks to "make a video", "create a motion graphics video", "build a launch video / intro / outro / explainer with Remotion", or describes a video they want generated from a prompt. Scaffolds (or reuses) a long-lived Remotion project, installs Remotion's official agent skills, plans the video beat-by-beat with the user, builds scenes with screenshot verification, iterates in the Studio preview, and renders to MP4. Maintains a persistent brand style guide so successive videos in the same project stay visually consistent.
version: 0.1.0
---

# Remotion Video Studio

Prompt-driven motion-graphics video creation. The user describes the video, you produce it, they react, you revise — until they say ship.

## When this skill runs

The user wants a motion-graphics video built from a prompt. They might say "make me a launch video for X", "build a 15-second intro", "create a vertical short about Y", or just paste a description. They are **not** asking to edit existing recorded footage — that's a separate problem (raw-footage trimming + transcript-driven captions are out of scope for this skill).

## Prerequisites

- **Node.js** on PATH (`node --version` should print 18+).
- **`npx`** available (ships with Node).
- For rendering, Remotion's bundled Chromium will be downloaded on first render — that's fine, just mention it to the user the first time.

If `node` is missing, tell the user to install it (`brew install node`) and stop.

## Configuration

Read `${CLAUDE_PLUGIN_ROOT}/skills/remotion-video/config.json`. Defaults if absent:

| Field | Default | Purpose |
|---|---|---|
| `output_root` | `./videos-studio` | Where the long-lived Remotion project lives. Resolved against CWD. |
| `fps` | `30` | Frames per second for new compositions. |
| `width` | `1920` | Default composition width (16:9 1080p). |
| `height` | `1080` | Default composition height. |
| `install_official_skills` | `true` | Run `npx remotion skills add` on a fresh project. |
| `auto_start_studio` | `true` | Auto-launch `npx remotion studio` for preview. |
| `screenshot_scale` | `0.25` | `--scale` for `npx remotion still` verification PNGs. |

User overrides per call:
- "save to /path" → override `output_root`.
- "9:16 vertical" → 1080×1920. "1:1 square" → 1080×1080. "4K" → 3840×2160.
- "60fps" → override `fps`.

## The six-phase workflow

Walk the user through these — do not collapse them into one shot. The iteration is the point.

### Phase 1 — Locate or scaffold the project

1. Resolve `output_root` against the CWD. Call this `<project>`.
2. If `<project>/remotion.config.ts` (or `.mjs`/`.js`) exists, the project is already set up — skip to Phase 2's "returning project" branch.
3. Otherwise, scaffold it non-interactively:
   ```bash
   npx --yes create-video@latest --yes --blank --no-tailwind <project>
   ```
   Then `cd <project>` for everything that follows.
4. Tell the user where the project lives and that future videos will reuse it.

### Phase 2 — Bootstrap rules + brand

**Fresh project (first run):**

1. Install Remotion's official agent skills so subsequent edits in this folder follow Remotion conventions:
   ```bash
   npx --yes remotion skills add
   ```
   This populates `<project>/.claude/skills/` with rules covering animations, sequencing, timing, transitions, audio, captions, fonts, and asset handling. **Defer to those rules for code patterns** — don't restate them here.

2. Copy the persistent style guide into the project:
   ```bash
   mkdir -p <project>/src/brand
   cp ${CLAUDE_PLUGIN_ROOT}/skills/remotion-video/templates/style-guide.ts <project>/src/brand/style-guide.ts
   cp ${CLAUDE_PLUGIN_ROOT}/skills/remotion-video/templates/BRAND.md     <project>/src/brand/BRAND.md
   ```

3. Add the helper packages most videos need:
   ```bash
   (cd <project> && npx --yes remotion add @remotion/transitions @remotion/media)
   ```
   Add `@remotion/captions` later only if a video actually needs captions.

**Returning project:**

1. Read `<project>/src/brand/BRAND.md` so you have the established style in working context. Note any promoted components in `<project>/src/brand/components/`.
2. List existing videos: `ls <project>/videos/` so you can suggest reusing patterns from neighbors.

### Phase 3 — Plan the video (and wait for approval)

Translate the user's prompt into a beat-by-beat plan **before writing any code**. For each beat:

- Title (e.g. `intro-glow`, `feature-callout-1`, `cta-final`).
- One-sentence anchor idea or on-screen text.
- Duration in frames (use `durations.beat` from the style guide as the default; intros/outros can use `durations.intro`/`durations.outro`).
- Transition into the beat (`fade`, `slide-from-bottom`, `wipe-from-left`, or "hard cut").
- Which `src/brand/` elements it reuses, and which (if any) new elements it would introduce.

Surface the plan as a numbered list to the user. Use **AskUserQuestion** for ambiguous high-level choices that affect the whole video:

- Aspect ratio (16:9 / 9:16 / 1:1) if the user hasn't specified.
- Total target length if it's open-ended.
- Vibe-shifting choices (e.g. "playful pop" vs "restrained corporate") that change which springs/easings get used.

Then ask plainly: **"Approve this plan, or tell me what to change?"** Do not start writing scene code until they approve. Iterate on the plan as long as the user wants.

When approved, write the plan to `<project>/videos/<slug>/PLAN.md` so future revisions and future videos can reference it.

### Phase 4 — Build scene-by-scene with screenshot checks

For each beat in the approved plan:

1. Create `<project>/videos/<slug>/scenes/<Name>.tsx` as an `AbsoluteFill`-rooted React component. Drive all animation from `useCurrentFrame()` and `useVideoConfig()`. **Import colors, fonts, easings, and durations from `src/brand/style-guide.ts` — never hardcode brand values.** Reuse any promoted component from `src/brand/components/` when applicable.

2. Wire scenes into a per-video master in `<project>/videos/<slug>/Root.tsx`:
   - Use `<TransitionSeries>` from `@remotion/transitions` with the per-beat transitions from the plan.
   - Compute `durationInFrames` for the master as the sum of beat durations minus transition overlaps (`TransitionSeries` shortens total duration by each transition's frames).

3. Register the master composition in the project's top-level `src/Root.tsx`. Composition `id` should be `<slug>` (kebab-case slug of the video title).

4. After finishing each scene, **PNG-verify it**:
   ```bash
   (cd <project> && npx remotion still <slug> --frame=<midpoint-frame> --scale=<screenshot_scale> --output=videos/<slug>/.checks/<scene>-<frame>.png)
   ```
   Read the resulting PNG to confirm layout, alignment, and text legibility. Fix obvious issues before moving to the next scene — this catches off-screen elements, color clashes, and font issues without burning a full render.

### Phase 5 — Iterate in Studio

1. If `auto_start_studio` is true, launch the Studio in the background once the first scene exists:
   ```bash
   (cd <project> && npx remotion studio)   # run_in_background
   ```
   It serves on `http://localhost:3000` by default. Tell the user the URL and the composition `id` so they can preview.

2. Accept comment-driven revisions and edit the relevant scene file(s). Examples of the kind of feedback to expect:
   - "Beat 1's card is covering my logo — shrink it 80% and shift right."
   - "Hold the final beat 2 seconds longer."
   - "Kill the grid background — it's distracting."
   - "Swap the wipe on beat 3 for a fade."

   Studio hot-reloads. After each edit, re-run `npx remotion still` for the affected scene and read the PNG so you don't rely solely on the user's eyes.

3. Loop. Don't ask "is this done?" every iteration — let the user say "ship it" / "render it" / "looks good, render".

### Phase 6 — Render and promote

1. Render the MP4:
   ```bash
   (cd <project> && npx remotion render <slug> videos/<slug>/out.mp4)
   ```
   For 9:16 verticals, the same command works — Remotion uses the composition's dimensions.

2. Tell the user the absolute path to the rendered file.

3. **Promote.** Ask: "Anything from this video worth saving as a brand element for the next one?" If yes:
   - Move the reusable component to `<project>/src/brand/components/<Name>.tsx` and update its imports.
   - Add a line to `<project>/src/brand/BRAND.md`'s **Promotion log** with the date, video slug, what was promoted, and why.
   - If a new color/easing/duration earned its place, add it to `style-guide.ts` (don't bloat the style guide with one-offs that didn't reuse).

That's the cycle. Video #2 starts at Phase 1 → "returning project" → Phase 3, with a head start.

## Useful Remotion CLI commands

(For reference — defer to Remotion's installed skills for full options.)

- `npx remotion studio` — preview server (hot reload).
- `npx remotion still <CompId> --frame=N --scale=0.25 --output=path.png` — single-frame PNG. Cheap layout check.
- `npx remotion render <CompId> [out.mp4]` — final MP4. Add `--codec=h264` (default) or `--codec=vp9` if needed.
- `npx remotion compositions` — list available composition IDs.
- `npx remotion add @remotion/<package>` — add an official Remotion package (transitions, media, captions, three, etc.).

## Error handling

- **`node` not on PATH:** tell the user to install Node (`brew install node`) and stop.
- **`npx remotion skills add` fails** (e.g. offline): proceed without it, but warn the user that scene quality is now reliant entirely on this skill's instructions and the official Remotion docs they may want to pull in manually later.
- **Render fails (Chromium download stuck, codec missing, OOM):** surface the stderr verbatim. For OOM on 4K, suggest re-running with `--concurrency=1`.
- **Studio port in use:** Studio picks a free port automatically; just relay whichever port it printed.

## Notes

- `${CLAUDE_PLUGIN_ROOT}` is set by Claude Code when the plugin loads. If unset, derive paths from this SKILL.md's location.
- We deliberately do **not** generate music. If the user wants a soundtrack, point them to Suno/Udio/etc., have them drop the mp3 into `<project>/public/`, and wire it up with `<Audio src={staticFile("…")} />` from `@remotion/media`.
- Per-video subdirectories (`videos/<slug>/`) keep scene files, the per-video `Root.tsx`, the `PLAN.md`, screenshot checks under `.checks/`, and the rendered MP4 colocated. The top-level `src/Root.tsx` is the registry that imports each video's master composition.
- Resist editing `src/brand/style-guide.ts` mid-video. Promotions happen in Phase 6, after a successful render — that's how the style guide stays trustworthy across projects.
