---
name: screencast-cut
description: Use this skill when the user wants to "edit a screen recording", "turn a terminal cast into a video", "cut a tutorial from this .cast file", "make a video from this MP4", or pastes a path to a `.cast` / `.mp4` (often alongside an audio file) and asks for a polished video. Speed-ramps idle gaps in terminal recordings, transcribes audio with Whisper for word-level captions, and emits a Remotion project ready for the `remotion-video` plugin to preview and render. Reuses the active brand profile from the Remotion project so output style matches the rest of the user's videos.
version: 0.1.0
---

# Screencast Cut

Turn a raw recording into a finished tutorial. The user gives you source material (a terminal `.cast`, a screen-recording `.mp4`, optionally a separate audio file). You produce a Remotion project — scene files, plan, captions — that the `remotion-video` plugin can preview and render.

## When this skill runs

The user has source material to *edit*, not a video to *generate from a prompt*. Common shapes:

- "edit `/tmp/demo.cast` plus `/tmp/voiceover.m4a` into a tutorial"
- "cut this terminal recording into something watchable"
- "turn `~/Recordings/cleanshot-2026-04-26.mp4` into a 90-second tutorial"

If the user is asking for purely synthetic motion graphics (no source recording), that's the `remotion-video` skill, not this one.

## What this skill does *not* do

- It does not render the final MP4 — it scaffolds a Remotion project and hands off to the `remotion-video` workflow (Phase 5 preview, Phase 6 render). Do not duplicate render logic here.
- It does not generate music or voiceover. Audio comes from the user.
- It does not invent its own terminal renderer. `agg` does that. This skill orchestrates.

## Prerequisites

Check up-front and stop with a clear install message if missing:

| Tool | Used for | Install (macOS) |
|---|---|---|
| `agg` | render `.cast` to GIF | `brew install agg` |
| `ffmpeg` + `ffprobe` | GIF → PNG sequence, MP4 probing, audio extraction | `brew install ffmpeg` |
| `whisper-cli` (whisper.cpp) | word-level transcription | `brew install whisper-cpp` |
| `node` 18+ / `npx` | Remotion project (only needed at Phase 5 hand-off) | `brew install node` |

For Linux / Docker: equivalent packages — `agg` via `cargo install --git https://github.com/asciinema/agg`, ffmpeg/whisper.cpp via the distro package manager.

A whisper ggml model (default `base.en`) must be on disk. `whisper-cli --model-download base.en` fetches it; the script also looks under `/opt/homebrew/share/whisper-cpp/` and `~/.cache/whisper.cpp/`.

## Configuration

Read `${CLAUDE_PLUGIN_ROOT}/skills/screencast-cut/config.json`. Defaults:

| Field | Default | Purpose |
|---|---|---|
| `idle_threshold_speedramp_seconds` | `2` | Idle gap >= this becomes a speed-ramp candidate. |
| `idle_threshold_cut_seconds` | `8` | Idle gap >= this becomes a hard-cut candidate (replaced with a "…" beat). |
| `speedramp_factor` | `4` | How aggressive the ramp is when applied. |
| `default_intro_frames` | `45` | Wordmark hero from the active profile (1.5s @ 30fps). |
| `default_outro_frames` | `60` | Outro card (2s @ 30fps). |
| `caption_style` | `"auto"` | `karaoke` (per-word reveal, shortform) / `band` (clean caption bar, tutorial) / `auto` picks by aspect ratio. |
| `fps` | `30` | Frames per second for the rendered project. |
| `agg_theme` | `"monokai"` | Pass-through to `agg --theme`. |
| `agg_font_size` | `14` | Pass-through to `agg --font-size`. |
| `whisper_model` | `"base.en"` | ggml model name. `small.en` is more accurate, slower. |

User overrides per call:
- "use the karaoke captions" / "for TikTok" → `caption_style=karaoke`.
- "skip the intro" → `default_intro_frames=0`. Same shape for outro.
- "don't speed-ramp anything" → `idle_threshold_speedramp_seconds=999`.

## The six-phase workflow

Same shape as the `remotion-video` skill so the user only learns one rhythm.

### Phase 1 — Locate the Remotion project

This skill's output is a *new video subdirectory* inside an existing Remotion project (the one `remotion-video` scaffolds). Resolve `output_root` against CWD the same way `remotion-video` does — default `./videos-studio`.

1. If `<project>/remotion.config.ts` (or `.mjs`/`.js`) does **not** exist, the project hasn't been scaffolded yet. Tell the user: "No Remotion project found at `<project>`. Run the `remotion-video` skill once first to scaffold one (it'll pick up the brand profile too), then re-run me." Do not scaffold the project from this skill — that's `remotion-video`'s job, and duplicating the scaffolding logic would diverge.
2. List existing videos under `<project>/videos/` so you can suggest a slug that won't collide.
3. Pick a slug from the user's prompt (kebab-case, short — e.g. `demo-cli-tutorial`).

### Phase 2 — Read brand profile + classify input

1. List profiles: `ls <project>/src/brand/profiles/`.
2. Read `<project>/src/brand/active.ts` to learn which profile is active. If the user said "use the X profile" in this prompt, follow the same switch logic the `remotion-video` skill uses (copy the template if missing, rewrite `active.ts` to re-export from it). Tell the user you switched.
3. Read the active profile's `BRAND.md` so you know the typography, palette, motion vocabulary, and any promoted components.
4. **Classify the input** by extension:
   - `.cast` → asciinema path (Phase 3a).
   - `.mp4` / `.mov` → screen-capture path (Phase 3b).
   - Anything else → ask the user; don't guess.
5. If the user provided a separate audio file (`.m4a`/`.mp3`/`.wav`) for narration, note its path. If audio is embedded in the MP4, you'll extract it with ffmpeg in Phase 4.

### Phase 3a — Plan beats (asciinema path)

Run the cast-to-frames pipeline up-front in *dry-run-ish* mode — actually, just run it for real. It's idempotent and the timing manifest is what you need to plan from:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/screencast-cut/scripts/cast_to_frames.py" \
    "<input.cast>" \
    "<project>/videos/<slug>/source/" \
    --fps "<fps>" \
    --theme "<agg_theme>" \
    --font-size "<agg_font_size>" \
    --idle-speedramp "<idle_threshold_speedramp_seconds>" \
    --idle-cut "<idle_threshold_cut_seconds>"
```

Read `videos/<slug>/source/timing.json`. Translate it into a beat plan:

- **Intro beat** (`default_intro_frames` frames) — the active profile's wordmark hero or title card. Skip if `default_intro_frames=0`.
- **Content beats**, alternating between:
  - *Run* beats — stretches between idle gaps, played 1× speed.
  - *Speedramp* beats — gaps with `kind="speedramp"`, played at `speedramp_factor` × speed.
  - *Cut* beats — gaps with `kind="cut"` get replaced with a 1.0s "…" caption card (don't show frozen terminal for 8+ seconds).
- **Outro beat** (`default_outro_frames` frames) — the active profile's outro / call-to-action card.

Surface the plan to the user as a numbered list with per-beat duration and what brand element it uses. Use **AskUserQuestion** for ambiguous high-level choices:
- Aspect ratio if the cast width doesn't match the project default (terminals are wide; 9:16 needs a center-crop policy).
- Whether to keep the long idle gaps as speed-ramps or cut entirely (offer both for any gap that straddles the threshold).
- Whether to caption the terminal output too, or only the audio narration.

Wait for "approve" before writing scene code.

### Phase 3b — Plan beats (MP4 path)

For now (Slice 2): not yet implemented. Tell the user "the MP4 path lands in the next slice — for this version, please use a `.cast` file." A later slice adds the MP4 input adapter, CleanShot X click-event reader, and auto-zoom planner.

### Phase 4 — Build scenes

Write the plan first to `<project>/videos/<slug>/PLAN.md`, then build:

1. **Transcribe audio** if the user provided one:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/screencast-cut/scripts/transcribe.py" \
       "<audio>" "<project>/videos/<slug>/source/transcript.json" \
       --model "<whisper_model>"
   ```
   Copy the audio file into `<project>/public/<slug>/voiceover.<ext>` so `staticFile()` can find it.

2. **Copy frames** so Remotion can resolve them via `staticFile()`:
   ```bash
   mkdir -p <project>/public/<slug>/frames
   cp <project>/videos/<slug>/source/frames/*.png <project>/public/<slug>/frames/
   ```

3. **Build scene components** under `<project>/videos/<slug>/scenes/`. Drive everything from `useCurrentFrame()` and `useVideoConfig()`. Import colors, fonts, easings, and durations from `src/brand/active` — never hardcode. Reuse promoted components from `<project>/src/brand/profiles/<active>/components/` when applicable.

   The scene shapes you'll typically need:
   - `IntroCard.tsx` — wraps `WordmarkHero` (or whatever the active profile exposes) for the opener.
   - `TerminalRun.tsx` — renders the PNG sequence between two timestamps. Use `<Img src={staticFile(\`<slug>/frames/\${pad(n)}.png\`)} />` driven by current frame mapped through `frame_times_s` from `timing.json`. For speed-ramped beats, scale the time mapping by `speedramp_factor`.
   - `IdleCutCard.tsx` — the "…" placeholder for cut gaps.
   - `Captions.tsx` — reads `transcript.json`. For `caption_style="band"`, render a single line at the active word; for `karaoke`, render the segment with the active word highlighted in the profile's accent.
   - `OutroCard.tsx` — call-to-action / closing card from the active profile.

4. **Wire the master** at `<project>/videos/<slug>/Root.tsx` using `<TransitionSeries>` from `@remotion/transitions`. Compute `durationInFrames` as the sum of beat durations minus transition overlaps.

5. **Register** the master composition in `<project>/src/Root.tsx` with composition `id` = the slug.

6. **PNG-verify** each scene with `npx remotion still <slug> --frame=<midpoint> --scale=0.25 --output=videos/<slug>/.checks/<scene>.png` and read the PNG. Fix off-screen elements / text-overflow before moving on.

### Phase 5 — Iterate in Studio

Hand off to the `remotion-video` rhythm: the user previews in `npx remotion studio` (already running, or launch it now), comments drive scene-file edits, hot reload, repeat. Studio is shared between every video in the project — no need to re-launch.

Common feedback to expect on cut tutorials:
- "Speed-ramp this section harder — 8× not 4×." → bump `speedramp_factor` for that one beat.
- "The captions are clipping the terminal — move them to the top." → caption position is in the profile; either tweak locally or promote a profile-level caption-position option.
- "Cut the first 4 seconds — I fumbled the start." → adjust the first content beat's `start_s`.
- "Add a chapter card before the install step." → insert a beat using the profile's title-card component.

### Phase 6 — Render and promote

Use `remotion-video`'s render command — don't duplicate it:

```bash
(cd <project> && npx remotion render <slug> videos/<slug>/out.mp4)
```

Tell the user the absolute path. Then ask: "Anything from this cut worth saving as a brand element for next time?" Promotion goes into the **active profile**, never a global folder, exactly like `remotion-video`'s Phase 6:

- Reusable scene → `<project>/src/brand/profiles/<active>/components/<Name>.tsx`, update imports.
- New caption style or speed-ramp shape → add to `<project>/src/brand/profiles/<active>/style-guide.ts` only if it'll genuinely reuse.
- Log it in the active profile's `BRAND.md` Promotion log with date, slug, what, why.

For source-constrained profiles (where `BRAND.md` says only certain values are allowed), don't promote off-source values — match the profile's rules.

## Heuristics encoded

These are the defaults the skill applies without asking. The user can override any of them; surface them in the plan so they have something to push back on:

- Idle gap >= `idle_threshold_speedramp_seconds` (default 2s) → speed-ramp at `speedramp_factor` (default 4×).
- Idle gap >= `idle_threshold_cut_seconds` (default 8s) → hard cut, replaced with a 1s "…" beat.
- Caption style:
  - `auto` + 16:9 master → `band` (clean caption bar at the bottom safe-zone).
  - `auto` + 9:16 master → `karaoke` (per-word reveal in the profile accent).
- Default intro: 1.5s wordmark hero from the active profile.
- Default outro: 2s call-to-action card from the active profile.
- If the cast has zero `o` events (input-only or empty), stop and report — there's nothing to render.

## Error handling

- **`agg` / `ffmpeg` / `whisper-cli` missing.** Surface the exact install command for the user's platform and stop.
- **Cast file unreadable / wrong version.** `cast_to_frames.py` accepts v1, v2, and v3; anything else → tell the user to re-record with a recent asciinema and stop.
- **Whisper model missing.** The `transcribe.py` script lists the paths it searched. Tell the user to download with `whisper-cli --model-download <name>` and retry.
- **Audio drift.** If the audio duration differs from the cast duration by more than a few percent, warn the user — typically means they recorded narration separately and didn't sync. Offer to either trim audio or stretch terminal playback.
- **No Remotion project.** Phase 1 already handles this — point the user at the `remotion-video` skill and stop, don't scaffold from here.

## Notes

- `${CLAUDE_PLUGIN_ROOT}` is set by Claude Code at load time. If unset, derive paths from this SKILL.md's location.
- The split between this skill (cuts source material into a project) and the `remotion-video` skill (renders projects, owns the brand profile system) is deliberate. **Do not merge their SKILL.md files.** They share the same project directory and brand-profile system, but the workflows are different shapes — prompt-to-video vs. recording-to-video.
- Per-video subdirectories (`videos/<slug>/`) keep PLAN, scenes, source-frames, transcript, screenshot checks under `.checks/`, and the rendered MP4 colocated. The top-level `src/Root.tsx` is the registry.
- Frames live under `<project>/public/<slug>/frames/` so `staticFile()` resolves them. The duplicated PNGs under `videos/<slug>/source/frames/` are kept as the working copy in case you want to re-render or hand-tweak.
- Resist editing the active profile's `style-guide.ts` mid-cut. Promotions happen in Phase 6, after a successful render.
