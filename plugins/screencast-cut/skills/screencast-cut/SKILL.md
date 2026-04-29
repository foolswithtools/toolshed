---
name: screencast-cut
description: Use this skill when the user wants to "edit a screen recording", "turn a terminal cast into a video", "cut a tutorial from this .cast file", "make a video from this MP4", "auto-zoom on clicks in a screen capture", or pastes a path to a `.cast` / `.mp4` (often alongside an audio file or click-event log) and asks for a polished video. Speed-ramps idle gaps in terminal recordings, plans auto-zoom on click anchors for screen captures, transcribes audio with Whisper for word-level captions, and emits a Remotion project ready for the `remotion-video` plugin to preview and render. Reuses the active brand profile from the Remotion project (including its genre playbook for tutorial vs. shortform editing decisions) so output style matches the rest of the user's videos.
version: 0.4.0
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
| `zoom_factor` | `1.6` | Scale at the peak of an auto-zoom segment. |
| `zoom_ramp_in_ms` | `300` | Time to ramp from 1× up to `zoom_factor` before the click. |
| `zoom_hold_ms` | `1500` | Time held at `zoom_factor` after the click. |
| `zoom_ramp_out_ms` | `400` | Time to ramp from `zoom_factor` back to 1×. |
| `click_merge_window_ms` | `1500` | Click anchors within this window merge into one pan segment. |

User overrides per call:
- "use the karaoke captions" / "for TikTok" → `caption_style=karaoke`.
- "skip the intro" → `default_intro_frames=0`. Same shape for outro.
- "don't speed-ramp anything" → `idle_threshold_speedramp_seconds=999`.

**Precedence note:** several of these defaults — `default_intro_frames`, `default_outro_frames`, `caption_style`, and the cut-cadence heuristics — get overridden by the active profile's **playbook** for the detected genre (Phase 2, step 8 onward). Final precedence is **config defaults < playbook overrides < user prompt overrides**. The plan you surface in Phase 3 must label which source each decision came from so the user can push back on the right layer.

## The six-phase workflow

Same shape as the `remotion-video` skill so the user only learns one rhythm.

### Phase 1 — Locate the Remotion project

This skill's output is a *new video subdirectory* inside an existing Remotion project (the one `remotion-video` scaffolds). Resolve `output_root` against CWD the same way `remotion-video` does — default `./videos-studio`.

1. If `<project>/remotion.config.ts` (or `.mjs`/`.js`) does **not** exist, the project hasn't been scaffolded yet. Tell the user: "No Remotion project found at `<project>`. Run the `remotion-video` skill once first to scaffold one (it'll pick up the brand profile too), then re-run me." Do not scaffold the project from this skill — that's `remotion-video`'s job, and duplicating the scaffolding logic would diverge.
2. List existing videos under `<project>/videos/` so you can suggest a slug that won't collide.
3. Pick a slug from the user's prompt (kebab-case, short — e.g. `demo-cli-tutorial`).

### Phase 2 — Read brand profile + classify input + resolve playbook

1. List profiles: `ls <project>/src/brand/profiles/`.
2. Read `<project>/src/brand/active.ts` to learn which profile is active. If the user said "use the X profile" in this prompt, follow the same switch logic the `remotion-video` skill uses (copy the template if missing, rewrite `active.ts` to re-export from it). Tell the user you switched.
3. Read the active profile's `BRAND.md` so you know the typography, palette, motion vocabulary, and any promoted components.
4. **Classify the input** by extension:
   - `.cast` → asciinema path (Phase 3a).
   - `.mp4` / `.mov` → screen-capture path (Phase 3b).
   - Anything else → ask the user; don't guess.
5. If the user provided a separate audio file (`.m4a`/`.mp3`/`.wav`) for narration, note its path. If audio is embedded in the MP4, you'll extract it with ffmpeg in Phase 4.
6. **For MP4 input, locate click-event data.** Check for any of the following alongside the MP4:
   - A sibling `.screenize/` directory (polyrecorder-v2 package from the [Screenize](https://github.com/syi0808/screenize) recorder).
   - A sibling `events.json` written by the user by hand (manual schema — see Phase 3b).
   - Nothing — fall back to manual-anchor mode in Phase 3b.

   **About CleanShot X specifically:** CleanShot X does *not* export click coordinates or timing. Its click highlights are rendered into the MP4 pixels, not a sidecar file. If the user supplies a CleanShot recording and expects auto-zoom on real clicks, tell them up-front: *either* re-record with a tool that exports an event stream (Screenize is one), *or* author a manual `events.json` with timestamps and approximate click positions. Computer-vision cursor tracking on raw MP4 is feasible but lands in a later slice.

7. **Detect the genre.** Two outcomes only: `tutorial` or `shortform`. Resolution order:
   - **Explicit user override** wins. Phrases like "for TikTok", "as a short", "vertical", "9:16" → `shortform`. "tutorial", "for YouTube", "long-form", "explainer", "16:9" → `tutorial`.
   - **Inferred from input shape.** Probe the source (cast width or MP4 dimensions via `ffprobe`) and known duration:
     - 9:16 master composition AND duration ≤ 60s → `shortform`.
     - 16:9 master composition AND duration > 60s → `tutorial`.
     - Anything ambiguous (e.g. 16:9 but 30s, or 9:16 but 4 minutes) → default `tutorial` and surface the assumption in the plan so the user can flip it.
8. **Detect the `chapter_position` parameter** from the prompt. Recognize from phrasing:
   - "chapter 1 of N", "first lesson", "intro to the series", "part 1" → `first`.
   - "chapter <N> of <M>" (with N strictly between 1 and M), "part 2 of 5", "next in the series" → `middle`.
   - "final chapter", "last lesson", "wrap-up", "the conclusion", "chapter <M> of <M>" → `last`.
   - No chapter language → `standalone` (the default).

   Also extract a **chapter title** if the prompt supplies one (e.g. "Chapter 3: Configuring the Database"). Save the title verbatim — it becomes the `ChapterCard.tsx` text in Phase 4.
9. **Resolve the playbook.** Look for `PLAYBOOK-<genre>.md` in this order, take the first that exists:
   1. `<project>/src/brand/profiles/<active>/PLAYBOOK-<genre>.md` — profile has its own playbook.
   2. `<project>/src/brand/profiles/default/PLAYBOOK-<genre>.md` — default profile's playbook (scaffolded by `remotion-video`).
   3. `${CLAUDE_PLUGIN_ROOT_REMOTION_VIDEO}/skills/remotion-video/templates/default/PLAYBOOK-<genre>.md` — plugin-shipped template (last resort; surface a note that the user should run the `remotion-video` skill once to scaffold the playbook into their project).

   If no playbook is found anywhere (only possible if the plugin install is broken), proceed with config defaults only and tell the user the playbook layer is unavailable.
10. **Parse the playbook's `## Decision overrides` block.** Read the file and extract every `- key: value # justification` line under that heading. Recognized keys (anything else is ignored with a one-line warning, since unknown keys mean a stale schema):
    - `intro_frames` → integer; replaces `default_intro_frames`.
    - `outro_frames` → integer; replaces `default_outro_frames`.
    - `cut_cadence_first_10s` → `aggressive` | `calm`; biases beat-length floor for the first 10s of content.
    - `cut_cadence_steady_state` → `aggressive` | `calm`; biases beat-length floor after the first 10s.
    - `caption_style` → `karaoke` | `band`; replaces config `caption_style` (overrides `auto`).
    - `cta_shape` → `question` | `next-steps` | `logo-card`; selects which outro template to use.
    - `max_duration_s` → integer; if the planned cut exceeds this, surface a warning in the plan but do not auto-truncate.

    Capture the inline justification verbatim — you'll surface it in the Phase 3 plan so the user sees *why* a decision was made.
11. **Compute final decisions.** Apply precedence: **config defaults → playbook overrides → user prompt overrides**. Then layer `chapter_position` modifiers on top of the resolved values:
    - `chapter_position = first` or `standalone` → no modification; resolved playbook values stand.
    - `chapter_position = middle`:
      - Replace the cold-open hook with a **recap-and-continue beat** of 7s (210 frames @ 30fps) before the first content beat. Voice and on-screen text reorient the viewer ("Last time we did X. Now we'll do Y.") rather than open cold.
      - Replace the outro with a **transitional outro** ("Next: Chapter <N+1>"), `cta_shape` forced to `logo-card`.
    - `chapter_position = last`:
      - Keep the cold-open hook (the conclusion deserves attention).
      - Force `cta_shape = logo-card` for a terminal/celebratory close (no question, no next-step ask — the series is done).
    - **If a chapter title was extracted in step 8**, plan an extra `ChapterCard.tsx` scene between the intro wordmark and the first content beat. Use the active profile's title-card component if one exists (`<project>/src/brand/profiles/<active>/components/ChapterCard.tsx` or `TitleCard.tsx`); otherwise scaffold a minimal one in Phase 4.

    Record the **source of every final decision** (`config` / `playbook` / `user` / `chapter_position`). Phase 3 surfaces this so the user can push back on the right layer.

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

Read `videos/<slug>/source/timing.json`. Translate it into a beat plan, using the **final decisions resolved in Phase 2** (config + playbook + user + chapter_position):

- **Intro beat** (`intro_frames` from resolved decisions) — the active profile's wordmark hero or title card. Skip if `intro_frames = 0` (shortform default).
- **Chapter card beat** — only if a chapter title was extracted in Phase 2 step 8. Insert between intro and first content beat. Duration ~2s.
- **Recap-and-continue beat** (only if `chapter_position = middle`) — 7s, replaces the cold-open hook. Voice text reorients the viewer, no cold-open shock cut.
- **Content beats**, alternating between:
  - *Run* beats — stretches between idle gaps, played 1× speed. Apply the `cut_cadence_first_10s` / `cut_cadence_steady_state` bias when planning hold-lengths inside long runs (aggressive = sub-2s holds, calm = 20–40s holds).
  - *Speedramp* beats — gaps with `kind="speedramp"`, played at `speedramp_factor` × speed.
  - *Cut* beats — gaps with `kind="cut"` get replaced with a 1.0s "…" caption card (don't show frozen terminal for 8+ seconds).
- **Outro beat** (`outro_frames` from resolved decisions, shaped by `cta_shape`) — the active profile's outro card. `cta_shape = next-steps` → next-action text card; `cta_shape = question` → on-screen question card; `cta_shape = logo-card` → wordmark with no text ask.

**Surface the plan to the user as a numbered list** with, per beat: duration, brand element used, and — for any beat whose shape came from the playbook — the playbook's inline justification. At the top of the plan, print a small "Decisions" table listing every key from step 11 with its **value** and **source** (`config` / `playbook` / `user` / `chapter_position`). Example:

```
Decisions for this cut:
  intro_frames        45        (playbook: default/tutorial)
  outro_frames        90        (playbook: default/tutorial)
  caption_style       band      (playbook: default/tutorial)
  cta_shape           logo-card (chapter_position: last)
  max_duration_s      600       (playbook: default/tutorial)
```

Use **AskUserQuestion** for ambiguous high-level choices:
- Aspect ratio if the cast width doesn't match the project default (terminals are wide; 9:16 needs a center-crop policy).
- Whether to keep the long idle gaps as speed-ramps or cut entirely (offer both for any gap that straddles the threshold).
- Whether to caption the terminal output too, or only the audio narration.

Wait for "approve" before writing scene code.

### Phase 3b — Plan beats (MP4 path)

The MP4 path centers on **auto-zoom on click anchors**, with audio-driven captions over the top. Auto-zoom needs structured click data — without it, you have a video and no idea where the user pointed.

#### Probe the MP4

```bash
ffprobe -v error -select_streams v:0 \
    -show_entries stream=width,height,r_frame_rate,duration \
    -of json "<input.mp4>"
```

Note the dimensions, fps, and duration. If the dimensions don't match the project's composition (terminals are usually 16:9; the project might be 9:16), surface this and ask whether to letterbox, center-crop, or change the composition aspect ratio for this video.

#### Resolve click anchors

Run the events parser if the user has a structured event source:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/screencast-cut/scripts/parse_events.py" \
    "<events-input>" \
    "<project>/videos/<slug>/source/" \
    --debounce-ms 250
```

`<events-input>` is one of:
- A `.screenize/` package directory from Screenize (polyrecorder-v2).
- A flat manual `events.json` the user wrote (schema below).

The parser writes `<project>/videos/<slug>/source/zoom_anchors.json` with normalized 0..1 coordinates.

**Manual `events.json` schema** — when the user has a CleanShot or QuickTime MP4 and wants auto-zoom, walk them through authoring this file (or generate it via AskUserQuestion if you have a frame-by-frame inspection of the video):

```json
{
  "display": {"width_px": 1920, "height_px": 1080, "scale": 1},
  "duration_s": 92.4,
  "clicks": [
    {"t_s": 12.0, "x": 0.42, "y": 0.58, "label": "open terminal"},
    {"t_s": 31.5, "x": 0.78, "y": 0.12, "label": "click run"}
  ]
}
```

`x`/`y` here are normalized 0..1 (top-left origin). For users who only know pixel coordinates, give them the formula: `x = px / display.width_px`. The `label` is optional but good for chapter cards.

**No click data at all?** Skip the auto-zoom layer entirely — the MP4 plays full-frame with captions over it. Tell the user that's what they're getting and offer the manual-anchor escape hatch.

#### Plan beats

Use the **final decisions resolved in Phase 2** for intro/outro/captions/cta_shape and the cadence biases — not raw config. The plan must surface the same Decisions table described in Phase 3a so the user can see which layer set each value.

- **Intro beat** (`intro_frames` from resolved decisions) — wordmark hero from the active profile. Skip if `intro_frames = 0`.
- **Chapter card beat** — only if a chapter title was extracted in Phase 2 step 8. Insert between intro and first content beat. Duration ~2s.
- **Recap-and-continue beat** (only if `chapter_position = middle`) — 7s, replaces the cold-open hook for chapters in the middle of a series.
- **Content beats** built from the MP4 plus zoom anchors:
  - Default: the MP4 plays at 1× behind the active profile's caption layer.
  - For each click anchor, plan a *zoom segment*: zoom-in starting **300ms before** the click, hold at the active zoom for **1.5s**, zoom-out **400ms** after. Use the active profile's easing presets (e.g. `easings.zoomIn`, `easings.zoomOut` if defined; else `Easing.bezier(0.4, 0, 0.2, 1)`).
  - Zoom level: 1.6× by default (configurable via `zoom_factor` in config). Center the zoom on the click coordinate, clamping the visible window so it doesn't drift outside the source frame.
  - Adjacent click anchors within 1.5s of each other → merge into one zoom segment that pans between the two anchor points.
- **Outro beat** (`outro_frames` from resolved decisions, shaped by `cta_shape`) — call-to-action card from the active profile.

Surface the plan as a numbered list including each click anchor's `t_s` and `label`. Print the Decisions table at the top (same format as Phase 3a). Use **AskUserQuestion** for:
- "These two clicks are 800ms apart — merge into one pan, or two separate zooms?"
- "The zoom on the click at 31.5s would clip the right edge — center it differently, reduce zoom to 1.3×, or skip the zoom?"

Wait for "approve" before writing scene code.

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

   The scene shapes you'll typically need (asciinema path):
   - `IntroCard.tsx` — wraps `WordmarkHero` (or whatever the active profile exposes) for the opener. Omit if `intro_frames = 0`.
   - `ChapterCard.tsx` — only when a chapter title was extracted in Phase 2. Reuse the active profile's title-card component if one exists at `<project>/src/brand/profiles/<active>/components/ChapterCard.tsx` or `TitleCard.tsx`; otherwise scaffold a minimal local version that types out the chapter title in the profile's display face.
   - `RecapCard.tsx` — only when `chapter_position = middle`. 7s beat that says "Last time: <X>. Now: <Y>." in the profile's voice. Plain text on the profile's background; this is a reorientation moment, not a hook.
   - `TerminalRun.tsx` — renders the PNG sequence between two timestamps. Use `<Img src={staticFile(\`<slug>/frames/\${pad(n)}.png\`)} />` driven by current frame mapped through `frame_times_s` from `timing.json`. For speed-ramped beats, scale the time mapping by `speedramp_factor`.
   - `IdleCutCard.tsx` — the "…" placeholder for cut gaps.
   - `Captions.tsx` — reads `transcript.json`. Use the **resolved `caption_style`** from Phase 2 (not raw config). For `band`, render a single two-line caption bar at the active word; for `karaoke`, render the active word highlighted in the profile's accent against a slightly dimmer baseline.
   - `OutroCard.tsx` — closing card shaped by the **resolved `cta_shape`**:
     - `next-steps` → "Now do X" with one concrete next-action line.
     - `question` → on-screen question that invites a comment reply.
     - `logo-card` → wordmark-only, no text ask (used by `chapter_position = last` and middle-chapter transitional outros).

   Additional scenes for the MP4 path:
   - `ScreenPlayback.tsx` — `<OffthreadVideo src={staticFile(\`<slug>/source.mp4\`)} startFrom={...} endAt={...} />`. Copy the MP4 once into `<project>/public/<slug>/source.mp4` so `staticFile()` resolves it.
   - `ZoomedSection.tsx` — wraps `ScreenPlayback` in a transform that interpolates `scale` from 1 → `zoom_factor` → 1 around a click anchor, with `translateX`/`translateY` set so the click point stays centered (clamp the offset so the visible window stays inside the source). Read anchor `t_s` and `x`/`y` from `zoom_anchors.json`. Use the active profile's easings.
   - The same `Captions.tsx` used on the asciinema path works here too — `transcript.json` is the source of truth regardless of input shape.

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

### Phase 7 — Capture a learning

Right after you report the render path, the user has fresh muscle memory about what worked and what fought them. That window closes fast — once they move to the next task, the lesson is gone. Phase 7 captures one learning before the session ends.

**Single AskUserQuestion, three options.** Don't wizard this — multi-step prompts after a render feel like homework and the user will dismiss them. One question, three buttons, then move on.

The prompt:

> "Anything from this cut worth remembering? *(picks the right place to save it)*
> - **Save as a rule** — this is a pattern to apply to every `<active-profile>` `<genre>` cut from now on.
> - **Just a note** — specific to this video, save under `videos/<slug>/NOTES.md`.
> - **Skip** — nothing to capture this time."

Then:

1. **"Save as a rule" → append to the playbook's Learnings section.**
   - If the active profile already has its own `PLAYBOOK-<genre>.md` (the resolution in Phase 2 step 9 found it at the profile path, not the default path), append directly to that file's `## Learnings` section.
   - If the active profile is **inheriting from default** (Phase 2 step 9 fell through to a `default/` or plugin path), this is the **graduation moment**: copy the resolved playbook into `<project>/src/brand/profiles/<active>/PLAYBOOK-<genre>.md` first, *then* append the learning. Tell the user "this profile just graduated to its own `<genre>` playbook — future cuts will use it as the base." That copy is a one-time event per profile+genre.
   - Replace the `_None yet._` placeholder on the first append.
   - Entry format, exactly:

     ```
     - YYYY-MM-DD — <slug> — <rule>. Why: <reason>.
     ```

     Use today's date, the cut's slug, the rule the user gave you (rephrase to imperative if they framed it as a complaint), and a one-line "why" the user said or implied. If they didn't give a "why", ask one short follow-up to capture it — Learnings without justification rot fast because nobody remembers why they were added.

2. **"Just a note" → write `<project>/videos/<slug>/NOTES.md`.**
   - Single markdown file scoped to the cut. If it doesn't exist, create it with a one-line header `# Notes for <slug>`. Append a dated bullet: `- YYYY-MM-DD — <note text>`.
   - Don't promote to the playbook later automatically — if the user wants the note to graduate to a rule, they re-run Phase 7 on a future cut and pick "Save as a rule."

3. **"Skip" → say nothing else and stop.**
   - No follow-up. The friction budget is small; respect it.

**Hard rules for Phase 7:**

- **Do not invent learnings.** If the user picks "Save as a rule" but doesn't give a clear rule, ask one short clarifying question, then either capture what they say or fall back to "Just a note" with their raw text. Never fabricate the rule from inference.
- **Do not run Phase 7 on failed renders.** If Phase 6 surfaced a render error, skip Phase 7 entirely — the user is in a debugging headspace, not a reflection one.
- **Do not stack questions.** Single AskUserQuestion with three options. The "why" follow-up only happens if option (a) is picked and the user didn't volunteer a reason.
- **Decision-override edits live in their own pass, not Phase 7.** If the user wants to change a key in `## Decision overrides` (e.g. "always use `cta_shape: question` for this profile"), that's a deliberate playbook edit, not a Learnings append. Tell them "that's a playbook change — open the file and edit the override directly," then capture the rationale as a Learnings entry that references the override.

## Heuristics encoded

These are the defaults the skill applies without asking. The user can override any of them; surface them in the plan so they have something to push back on. Anything labeled **(playbook-driven)** comes from the active profile's `PLAYBOOK-<genre>.md` and the playbook's value wins over the config default.

- Idle gap >= `idle_threshold_speedramp_seconds` (default 2s) → speed-ramp at `speedramp_factor` (default 4×).
- Idle gap >= `idle_threshold_cut_seconds` (default 8s) → hard cut, replaced with a 1s "…" beat.
- Click anchor → zoom segment: 300ms ramp-in, 1.5s hold at `zoom_factor` (default 1.6×), 400ms ramp-out, recentered on the click point.
- Click anchors within 1.5s of each other → merge into one pan-between-points segment.
- **Genre detection** (Phase 2 step 7):
  - Explicit user phrasing wins.
  - 9:16 + duration ≤ 60s → `shortform`.
  - 16:9 + duration > 60s → `tutorial`.
  - Ambiguous → `tutorial` (default), surface the assumption.
- **Caption style** *(playbook-driven)*: comes from playbook `caption_style` first; if config is left at `auto` and no playbook is found, fall back to `band` for 16:9 / `karaoke` for 9:16.
- **Intro length** *(playbook-driven)*: tutorial playbook → ~1.5s wordmark; shortform playbook → 0 frames (no intro at all). Config `default_intro_frames` is the last-resort fallback.
- **Outro length and shape** *(playbook-driven)*: tutorial → ~3s logo card with next-steps text; shortform → ~1.2s question card.
- **Cut cadence** *(playbook-driven)*: `cut_cadence_first_10s` and `cut_cadence_steady_state` bias hold-length floors during run beats — `aggressive` keeps holds under 2s, `calm` allows 20–40s holds.
- **Chapter position modifiers** (Phase 2 step 11): `middle` swaps the cold-open hook for a 7s recap-and-continue beat and forces the outro to a transitional logo-card; `last` keeps the hook but forces `cta_shape = logo-card`; `first` and `standalone` apply the playbook unmodified.
- If the cast has zero `o` events (input-only or empty), stop and report — there's nothing to render.
- If the MP4 has no resolvable click data (no Screenize package, no manual `events.json`), skip the auto-zoom layer and play the MP4 1× behind captions — don't fabricate zoom points from nothing.
- If no `PLAYBOOK-<genre>.md` resolves anywhere (broken plugin install), proceed with raw config defaults and tell the user the playbook layer is unavailable.

## Error handling

- **Playbook resolution failed.** All three playbook paths missed (profile, project default, plugin template). Proceed with config defaults only and tell the user "no playbook found — running on raw config; run the `remotion-video` skill to scaffold default playbooks into your project." Do not fabricate a playbook.
- **Unknown decision-override key in playbook.** The playbook had a `key: value` line under `## Decision overrides` with a key the parser doesn't recognize. Skip that line, surface a one-line warning, and continue. Don't silently accept new keys — they signal schema drift.
- **`agg` / `ffmpeg` / `whisper-cli` missing.** Surface the exact install command for the user's platform and stop.
- **Cast file unreadable / wrong version.** `cast_to_frames.py` accepts v1, v2, and v3; anything else → tell the user to re-record with a recent asciinema and stop.
- **Whisper model missing.** The `transcribe.py` script lists the paths it searched. Tell the user to download with `whisper-cli --model-download <name>` and retry.
- **Audio drift.** If the audio duration differs from the cast duration by more than a few percent, warn the user — typically means they recorded narration separately and didn't sync. Offer to either trim audio or stretch terminal playback.
- **No Remotion project.** Phase 1 already handles this — point the user at the `remotion-video` skill and stop, don't scaffold from here.
- **MP4 with no event data.** Tell the user up-front. CleanShot X, QuickTime, and the macOS Screenshot app don't export click coordinates. Two paths: re-record with a tool that does (Screenize is one), or have them author a manual `events.json` from memory or by stepping through the MP4. Don't silently skip — offer the choice.
- **`parse_events.py` formatVersion mismatch.** The polyrecorder schema is young and will move. Surface the actual `formatVersion` you got vs. the one expected and tell the user to either update their recorder or downgrade. Don't try to interpret an unknown schema version.
- **Zoom would clip the visible window.** Pre-validate before writing scenes: for each anchor, check that a window of size `1/zoom_factor` centered on `(x, y)` stays inside `[0, 1]`. If not, ask the user (via AskUserQuestion) whether to recenter, reduce zoom, or skip that anchor.

## Notes

- `${CLAUDE_PLUGIN_ROOT}` is set by Claude Code at load time. If unset, derive paths from this SKILL.md's location.
- `${CLAUDE_PLUGIN_ROOT_REMOTION_VIDEO}` (used in Phase 2 step 9 for the playbook fallback) resolves the same way — Claude Code exposes one such variable per installed plugin. If it's not set, derive the path by walking up from this SKILL.md to the plugins root and appending `remotion-video/skills/remotion-video/templates/default/`.
- The split between this skill (cuts source material into a project) and the `remotion-video` skill (renders projects, owns the brand profile system) is deliberate. **Do not merge their SKILL.md files.** They share the same project directory and brand-profile system, but the workflows are different shapes — prompt-to-video vs. recording-to-video.
- Per-video subdirectories (`videos/<slug>/`) keep PLAN, scenes, source-frames, transcript, screenshot checks under `.checks/`, and the rendered MP4 colocated. The top-level `src/Root.tsx` is the registry.
- Frames live under `<project>/public/<slug>/frames/` so `staticFile()` resolves them. The duplicated PNGs under `videos/<slug>/source/frames/` are kept as the working copy in case you want to re-render or hand-tweak.
- Resist editing the active profile's `style-guide.ts` mid-cut. Promotions happen in Phase 6, after a successful render.
