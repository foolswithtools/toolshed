---
name: screencast-cut
description: Use this skill when the user wants to "edit a screen recording", "turn a terminal cast into a video", "cut a tutorial from this .cast file", "make a video from this MP4", "auto-zoom on clicks in a screen capture", or pastes a path to a `.cast` / `.mp4` (often alongside an audio file, a narration script, or a click-event log) and asks for a polished video. Speed-ramps or cuts idle gaps in terminal recordings AND screen recordings (pixel-diff idle detection for video), flags backspace/Ctrl-U/Ctrl-W fumble-and-retype regions as cut candidates, plans auto-zoom on click anchors for screen captures, generates narration from a script via ElevenLabs TTS (loudnormed) when no audio is supplied, transcribes audio with Whisper for word-level captions, and emits a Remotion project ready for the `remotion-video` plugin to preview and render. Reuses the active brand profile from the Remotion project (including its genre playbook for tutorial vs. shortform editing decisions, and its per-theme voice) so output style matches the rest of the user's videos.
version: 0.11.0
---

# Screencast Cut

Turn a raw recording into a finished tutorial. The user gives you source material (a terminal `.cast`, a screen-recording `.mp4`, optionally a separate audio file). You produce a Remotion project — scene files, plan, captions — that the `remotion-video` plugin can preview and render.

> **If the user asks "how do I use this?" / "how does this work?" / "what do I need to send to my friend?"** — point them at `${CLAUDE_PLUGIN_ROOT}/USAGE.md`. That file is the human-facing onboarding guide (prereqs, example prompts, what-to-expect-each-phase, common pitfalls). Don't re-derive it from this SKILL.md — read it and surface the relevant section.

## When this skill runs

The user has source material to *edit*, not a video to *generate from a prompt*. Common shapes:

- "edit `/tmp/demo.cast` plus `/tmp/voiceover.m4a` into a tutorial"
- "cut this terminal recording into something watchable"
- "turn `~/Recordings/cleanshot-2026-04-26.mp4` into a 90-second tutorial"

If the user is asking for purely synthetic motion graphics (no source recording), that's the `remotion-video` skill, not this one.

## What this skill does *not* do

- It does not render the final MP4 — it scaffolds a Remotion project and hands off to the `remotion-video` workflow (Phase 5 preview, Phase 6 render). Do not duplicate render logic here.
- It does not generate music. Music comes from the user.
- It *can* generate **voiceover** from a narration **script** via ElevenLabs TTS (the `Script:` input, see Phase 1/2/4). If the user instead hands you pre-recorded `Audio:`, that wins — see "Narration: audio OR script" below.
- It does not invent its own terminal renderer. `agg` does that. This skill orchestrates.

## Prerequisites

Check up-front and stop with a clear install message if missing:

| Tool | Used for | Install (macOS) |
|---|---|---|
| `agg` | render `.cast` to GIF | `brew install agg` |
| `ffmpeg` + `ffprobe` | GIF → PNG sequence, MP4 probing, audio extraction | `brew install ffmpeg` |
| `whisper-cli` (whisper.cpp) | word-level transcription | `brew install whisper-cpp` |
| `node` 18+ / `npx` | Remotion project (only needed at Phase 5 hand-off) | `brew install node` |
| Python `numpy` | screen-recording idle detection (mean pixel-diff over sampled frames; only the `.mp4`/`.mov` idle-trim path) | `pip install numpy` |

For Linux / Docker: equivalent packages — `agg` via `cargo install --git https://github.com/asciinema/agg`, ffmpeg/whisper.cpp via the distro package manager.

A whisper ggml model (default `base.en`) must be on disk. `whisper-cli --model-download base.en` fetches it; the script also looks under `/opt/homebrew/share/whisper-cpp/` and `~/.cache/whisper.cpp/`.

**For the `Script:` (TTS) path only:** an ElevenLabs API token and network access. The token is resolved by `script_to_audio.py` in this order — `$ELEVENLABS_API_TOKEN` → any `--envrc` file you pass → `~/.envrc` → `~/.config/screencast-cut/secrets.env` → fail with an actionable message. **Never echo the token** (the script uses urllib, not shelled `curl`, and never logs or stores the value; the narration manifest contains no token). No token needed for the `Audio:` path.

## Narration: audio OR script

The narration track can come from either input — you do **not** need both:

- **`Audio:` <path>** — a pre-recorded `.m4a`/`.mp3`/`.wav`. Highest control. **`Audio:` wins** if both are supplied: use it and warn that `Script:` was ignored.
- **`Script:` <path>** — a `.txt`/`.md` of narration text. `script_to_audio.py` synthesizes it with ElevenLabs, `ffmpeg loudnorm`s it, and writes a 16 kHz mono `narration.wav` that drops straight into the existing audio path (transcribe → captions → render). No microphone required.

Both converge on the same `narration.wav`/audio file → `transcribe.py` → `Captions.tsx`. Whisper always drives the word-level caption timing regardless of which input produced the audio.

**Voice resolution (theme-tunable, precedence `config.json tts_* defaults < active theme `tts` block < per-prompt `Voice:` override`):**

- A theme's `tts` block in `style-guide.ts` declares its default `voice`, the canonical `voice_id`, an on-brand `alternates` roster, `model`, `loudnorm`, and `voice_settings`. Any field omitted falls through to the `config.json` `tts_*` defaults.
- `Voice: <name>` in the prompt overrides the theme default. If the chosen voice is **not** the theme's `voice` or in its `alternates`, still honor it but note in the Phase 3 Decisions table that it's outside the theme's approved roster.
- Names resolve to ids via ElevenLabs `/v1/voices`, cached at `~/.cache/screencast-cut/voices.json` (no per-render round-trip). Pass `--voice-id` to skip resolution. `list_voices.py` lists the account's voices and which themes reference each — use it when picking voices for a new theme.

> **Theme `tts` block lives in the user's studio, not in this repo.** Adding/editing a profile's `tts` export under `<project>/src/brand/profiles/<name>/style-guide.ts` is a studio edit — surface it for the user to run; don't treat it as plugin work.

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
| `screenshot_scale` | `0.25` | `--scale` for quick per-scene `npx remotion still` checks. |
| `verify_scale` | `0.5` | `--scale` for the Phase 4 `verify_render.py` filmstrip (0.25 is too small to read captions). |
| `agg_theme` | `"monokai"` | Pass-through to `agg --theme`. |
| `agg_font_size` | `14` | Pass-through to `agg --font-size`. |
| `whisper_model` | `"base.en"` | ggml model name. `small.en` is more accurate, slower. |
| `zoom_factor` | `1.6` | Scale at the peak of an auto-zoom segment. |
| `zoom_ramp_in_ms` | `300` | Time to ramp from 1× up to `zoom_factor` before the click. |
| `zoom_hold_ms` | `1500` | Time held at `zoom_factor` after the click. |
| `zoom_ramp_out_ms` | `400` | Time to ramp from `zoom_factor` back to 1×. |
| `click_merge_window_ms` | `1500` | Click anchors within this window merge into one pan segment. |
| `tts_provider` | `"elevenlabs"` | TTS backend for the `Script:` path. Only `elevenlabs` is implemented (the field is a seam for future providers). |
| `tts_default_voice` | `"Rachel"` | Fallback voice name when neither the theme `tts` block nor a `Voice:` override supplies one. |
| `tts_default_voice_id` | `"21m00Tcm4TlvDq8ikWAM"` | Canonical id used when no name resolves. |
| `tts_default_model` | `"eleven_multilingual_v2"` | ElevenLabs model id. |
| `tts_loudnorm` | `{I:-18,TP:-2,LRA:11}` | `ffmpeg loudnorm` target for generated narration. Theme `tts.loudnorm` overrides. |
| `tts_voice_settings` | `{stability,similarity_boost,style}` | ElevenLabs `voice_settings`. Theme `tts.voice_settings` overrides. |
| `fumble_min_backspaces` | `3` | A run of >= this many backspaces in the cast input stream is a fumble cut candidate. Fewer is too noisy to cut. Ctrl-U (kill-line) / Ctrl-W (kill-word) always trigger regardless of count. |
| `fumble_auto_cut` | `false` | If `false`, fumble regions are surfaced in the Phase 3 plan for per-region approval. If `true`, they're cut silently (brave/shortform themes only). |
| `video_idle_sample_fps` | `4` | Sample rate for screen-recording idle detection (`video_to_frames.py`). Higher = finer, slower. |
| `video_idle_pixel_diff_threshold` | `2.0` | Mean-abs grayscale diff (0–255) below which an MP4 frame pair is "static". Idle stretches reuse `idle_threshold_speedramp_seconds` / `idle_threshold_cut_seconds` / `speedramp_factor` for the actual trim — same cadence as casts. |

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
3. Read the active profile's `BRAND.md` so you know the typography, palette, and easing/spring presets (`easings`, `springs`). Note which components the profile actually ships under `components/` — the `default` profile ships none; `foolswithtools-brand` ships `WordmarkHero`, `TerminalChip`, etc. Reuse a profile component only when its file exists.
4. **Classify the input** by extension:
   - `.cast` → asciinema path (Phase 3a).
   - `.mp4` / `.mov` → screen-capture path (Phase 3b).
   - Anything else → ask the user; don't guess.
5. **Resolve the narration source** (see "Narration: audio OR script" above):
   - If the user provided `Audio:` (`.m4a`/`.mp3`/`.wav`), note its path — it wins. If a `Script:` was *also* given, warn that it's ignored.
   - Else if the user provided `Script:` (a `.txt`/`.md`), plan a **TTS pre-phase** (Phase 4 step 1 runs `script_to_audio.py` before transcription). Resolve the voice now: per-prompt `Voice:` → active theme's `tts.voice`/`voice_id` → `config.json` `tts_default_*`. Surface the chosen voice (and whether it's on the theme's approved roster) in the Phase 3 Decisions table.
   - Else if audio is embedded in the MP4, you'll extract it with ffmpeg in Phase 4.
   - Else there's no narration — the cut renders captions-free (terminal/video only).
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
   3. The `remotion-video` plugin's shipped template — resolve it by walking up from this SKILL.md's directory to the `plugins/` root, then `remotion-video/skills/remotion-video/templates/default/PLAYBOOK-<genre>.md`. (If `${CLAUDE_PLUGIN_ROOT_REMOTION_VIDEO}` is set, prefer it, but do not depend on it being defined.) Last resort; surface a note that the user should run the `remotion-video` skill once to scaffold the playbook into their project.

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
    --idle-cut "<idle_threshold_cut_seconds>" \
    --fumble-min-backspaces "<fumble_min_backspaces>"
```

Read `videos/<slug>/source/timing.json`. It carries two cut sources: `idle_gaps` (no output for a while) and **`fumble_regions`** (the user typed, backspaced ≥ `fumble_min_backspaces`, or hit Ctrl-U/Ctrl-W, then retyped — detected from the `i` input stream; a cast recorded without stdin has none). Translate it into a beat plan, using the **final decisions resolved in Phase 2** (config + playbook + user + chapter_position):

- **Intro beat** (`intro_frames` from resolved decisions) — the active profile's wordmark hero or title card. Skip if `intro_frames = 0` (shortform default).
- **Chapter card beat** — only if a chapter title was extracted in Phase 2 step 8. Insert between intro and first content beat. Duration ~2s.
- **Recap-and-continue beat** (only if `chapter_position = middle`) — 7s, replaces the cold-open hook. Voice text reorients the viewer, no cold-open shock cut.
- **Content beats**, alternating between:
  - *Run* beats — stretches between idle gaps, played 1× speed. Apply the `cut_cadence_first_10s` / `cut_cadence_steady_state` bias when planning hold-lengths inside long runs (aggressive = sub-2s holds, calm = 20–40s holds).
  - *Speedramp* beats — gaps with `kind="speedramp"`, played at `speedramp_factor` × speed.
  - *Cut* beats — gaps with `kind="cut"` get replaced with a 1.0s "…" caption card (don't show frozen terminal for 8+ seconds).
  - *Fumble cut* beats — each entry in `fumble_regions` is a **cut candidate**, not an auto-cut. Unless `fumble_auto_cut` is true (config default `false`; a theme `editing.fumble_auto_cut` or the user prompt can flip it), surface each fumble in the Phase 3 plan for per-region approval ("cut the fumble at 1.0–3.6s? [keep / cut]"). When approved (or when auto-cut is on), implement it **exactly like an `idle_cut`**: drop the frames in `[start_frame, end_frame]` and stand an `IdleCutCard` ("…") in their place, so the terminal appears to skip from the mistype straight to the corrected command. The fumble's `triggers`/`backspaces` are useful context to show in the plan.
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
- **Each `fumble_regions` entry** (unless `fumble_auto_cut` is on): "cut the fumble at `<start>`–`<end>`s (`<backspaces>` backspaces / `<triggers>`)? [keep / cut]". Default to offering the cut; a kept fumble just plays through at 1×.
- Whether to caption the terminal output too, or only the audio narration.

Wait for "approve" before writing scene code.

### Phase 3b — Plan beats (MP4 path)

The MP4 path has two additive layers: **idle-trim** (always available — compresses static dwells like a terminal cast) and **auto-zoom on click anchors** (needs structured click data). Either can be absent; with neither, the MP4 plays full-frame, full-speed, captions over the top.

#### Probe the MP4

```bash
ffprobe -v error -select_streams v:0 \
    -show_entries stream=width,height,r_frame_rate,duration \
    -of json "<input.mp4>"
```

Note the dimensions, fps, and duration. If the dimensions don't match the project's composition (terminals are usually 16:9; the project might be 9:16), surface this and ask whether to letterbox, center-crop, or change the composition aspect ratio for this video.

#### Detect idle stretches (screen-recording idle-trim)

Run the video idle detector — it samples the MP4 cheaply and finds static dwells (reading a page, dwelling on a result) the same way `cast_to_frames.py` finds terminal idle gaps:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/screencast-cut/scripts/video_to_frames.py" \
    "<input.mp4>" \
    "<project>/videos/<slug>/source/" \
    --fps "<fps>" \
    --sample-fps "<video_idle_sample_fps>" \
    --pixel-diff-threshold "<video_idle_pixel_diff_threshold>" \
    --idle-speedramp "<idle_threshold_speedramp_seconds>" \
    --idle-cut "<idle_threshold_cut_seconds>"
```

It writes `source/timing.json` (the **video** variant — `source_type: "video"`, validated against `schemas/video_timing.schema.json`) whose `idle_gaps` use the **same `{start_s,end_s,duration_s,kind}` shape as the cast path**, so the beat-planning logic is shared. How it works (resolved decisions): mean-absolute pixel diff on a downsampled grayscale (ffmpeg does the `fps,scale,format=gray`), with the **top-right menubar-clock box masked** so a ticking clock doesn't read as activity; SSIM is the documented escalation only if false positives bite. There is **no** scene-change/chapter detection in this layer. Static stretches reuse the cast cadence thresholds: ≥ `idle_threshold_speedramp_seconds` → speedramp, ≥ `idle_threshold_cut_seconds` → cut. These are the same global/playbook/theme/prompt-overridable values as the cast path.

#### Resolve click anchors

Run the events parser if the user has a structured event source:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/screencast-cut/scripts/parse_events.py" \
    "<events-input>" \
    "<project>/videos/<slug>/source/" \
    --debounce-ms 250
```

`<events-input>` is one of:
- A `.screenize/` package directory from Screenize (polyrecorder-v2). **⚠ The polyrecorder-v2 field names are UNVERIFIED** — they haven't been checked against a real Screenize export. The parser validates defensively and marks output `"source": "polyrecorder-v2"`, but sanity-check the resulting anchors. The manual path is the verified one.
- A flat manual `events.json` the user wrote.

The parser writes `<project>/videos/<slug>/source/zoom_anchors.json` (validated against `${CLAUDE_PLUGIN_ROOT}/skills/screencast-cut/schemas/zoom_anchors.schema.json`) with normalized 0..1 coordinates.

**Manual `events.json` schema** — the single source of truth is `${CLAUDE_PLUGIN_ROOT}/skills/screencast-cut/schemas/events.input.schema.json`. Read it rather than relying on this prose; `parse_events.py` validates the user's file against it on read and surfaces a precise location on any error. When the user has a CleanShot or QuickTime MP4 and wants auto-zoom, walk them through authoring a file shaped like:

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

`x`/`y` are normalized 0..1 (top-left origin); only `t_s` is required per click. For users who only know pixel coordinates, give them the formula: `x = px / display.width_px`. The `label` is optional but good for chapter cards. (The authoritative field list, types, and which fields are required live in the schema file above — don't let this example drift from it.)

**No click data at all?** Skip the auto-zoom layer entirely — the MP4 plays full-frame with captions over it. Tell the user that's what they're getting and offer the manual-anchor escape hatch.

#### Plan beats

Use the **final decisions resolved in Phase 2** for intro/outro/captions/cta_shape and the cadence biases — not raw config. The plan must surface the same Decisions table described in Phase 3a so the user can see which layer set each value.

- **Intro beat** (`intro_frames` from resolved decisions) — wordmark hero from the active profile. Skip if `intro_frames = 0`.
- **Chapter card beat** — only if a chapter title was extracted in Phase 2 step 8. Insert between intro and first content beat. Duration ~2s.
- **Recap-and-continue beat** (only if `chapter_position = middle`) — 7s, replaces the cold-open hook for chapters in the middle of a series.
- **Content beats** built from the MP4 plus its `idle_gaps` and zoom anchors:
  - Default: the MP4 plays at 1× behind the active profile's caption layer, via `VideoRun` (one per active span).
  - **Idle-trim beats** from `timing.json` `idle_gaps` (the video variant): a `speedramp` gap plays its source span at `speedramp_factor` via `VideoRun` (OffthreadVideo `playbackRate`); a `cut` gap is dropped and replaced with a **`BlurredFrozenFrameCard`** (a blurred frozen frame of the recording + a "skipped ahead" hint — **not** the terminal "…" card, which reads wrong over a screen aesthetic). Split the MP4 into active `VideoRun` spans separated by these trimmed gaps. The beat's output length is `videoBeatOutputFrames(startS, endS, fps, factor)` from `./timing` — don't hand-compute it.
  - For each click anchor, plan a *zoom segment*: zoom-in starting **300ms before** the click, hold at the active zoom for **1.5s**, zoom-out **400ms** after. Use a profile easing for the camera move — `easings.camera` (present in every profile) is ideal; `easings.apple` if the profile defines it; else `easings.softInOut`, falling back to `Easing.bezier(0.4, 0, 0.2, 1)`.
  - Zoom level: 1.6× by default (configurable via `zoom_factor` in config). Center the zoom on the click coordinate, clamping the visible window so it doesn't drift outside the source frame.
  - Adjacent click anchors within 1.5s of each other → merge into one zoom segment that pans between the two anchor points.
- **Outro beat** (`outro_frames` from resolved decisions, shaped by `cta_shape`) — call-to-action card from the active profile.

Surface the plan as a numbered list including each click anchor's `t_s` and `label`. Print the Decisions table at the top (same format as Phase 3a). Use **AskUserQuestion** for:
- "These two clicks are 800ms apart — merge into one pan, or two separate zooms?"
- "The zoom on the click at 31.5s would clip the right edge — center it differently, reduce zoom to 1.3×, or skip the zoom?"

Wait for "approve" before writing scene code.

### Phase 4 — Build scenes

Write the plan first to `<project>/videos/<slug>/PLAN.md`, then build:

1. **Generate narration from a script** (only when the resolved source in Phase 2 step 5 is `Script:`, not `Audio:`). Run *before* transcription — it produces the WAV the transcribe step reads:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/screencast-cut/scripts/script_to_audio.py" \
       "<script.md>" "<project>/videos/<slug>/source/" \
       --voice "<resolved voice name>" \
       --model "<theme tts.model or config tts_default_model>"
   # (or --voice-id <id> to skip name resolution; --loudnorm / --voice-settings
   #  as JSON to apply theme overrides; --envrc <path> to point at a token file.)
   ```
   This writes `source/narration.wav` (16 kHz mono, loudnormed) and `source/narration.manifest.json` (provider/voice/model/character count — surface its voice in the Phase 3 Decisions table). **Never echo the token.** Then continue exactly as the `Audio:` path: treat `source/narration.wav` as `<audio>` below.

2. **Transcribe audio** if there is a narration track (a user `Audio:` file, the just-generated `narration.wav`, or audio embedded in the MP4):
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/screencast-cut/scripts/transcribe.py" \
       "<audio>" "<project>/videos/<slug>/source/transcript.json" \
       --model "<whisper_model>"
   ```
   Copy the audio file into `<project>/public/<slug>/voiceover.<ext>` (or `narration.wav`) so `staticFile()` can find it, and play it through `SafeAudio`.

3. **Copy frames** so Remotion can resolve them via `staticFile()`:
   ```bash
   mkdir -p <project>/public/<slug>/frames
   cp <project>/videos/<slug>/source/frames/*.png <project>/public/<slug>/frames/
   ```

4. **Build scene components** under `<project>/videos/<slug>/scenes/`. Drive everything from `useCurrentFrame()` and `useVideoConfig()`. Import colors, fonts, easings, and durations from `src/brand/active` — never hardcode.

   **Two kinds of scene, two ways of building them:**

   **(a) Copy-and-adapt the reference scenes** for the timing-fragile beats. These ship tested in `${CLAUDE_PLUGIN_ROOT}/skills/screencast-cut/scene-templates/` and exist so the fragile frame/zoom/caption math is **imported, never re-derived freehand each run** (that re-derivation was the root cause of run-to-run drift). Copy the whole set into `videos/<slug>/scenes/` and adapt props — do not retype the math:
       ```bash
       cp "${CLAUDE_PLUGIN_ROOT}/skills/screencast-cut/scene-templates/"{timing.ts,TerminalRun.tsx,Captions.tsx,ZoomedSection.tsx,SafeImg.tsx,SafeVideo.tsx} \
          "<project>/videos/<slug>/scenes/"
       ```
       - `timing.ts` — the tested twin of `scripts/timing_math.py`. Every reference scene imports its math from here. **Never inline frame mapping, speed-ramp, zoom-clamp, or caption-timing arithmetic in a scene** — call the helper. If you think you need new math, add it to *both* `timing_math.py` and `timing.ts` with a test, don't sneak it into a `.tsx`.
       - `TerminalRun.tsx` — plays the PNG sequence for one beat. Pass `frameTimesS` (from `timing.json`), `beatStartS` (cast-clock start), and `factor` (1 = realtime run beat, `speedramp_factor` = ramped beat). Mapping is time-based via `castTimeToFrameIndex`, so it holds the correct PNG across the non-uniform GIF frame spacing.
       - `Captions.tsx` — reads `transcript.json`. Pass the **resolved `caption_style`** from Phase 2 (not raw config): `band` = clean caption bar, `karaoke` = per-word accent reveal. Works identically on the asciinema and MP4 paths — `transcript.json` is the source of truth regardless of input shape.
       - `ZoomedSection.tsx` (MP4 path) — wraps the screen MP4 with one auto-zoom segment, centred on a `zoom_anchors.json` anchor via `clampZoomWindow` so the window never drifts outside the frame. Mount one per zoom segment in `Root.tsx`. Copy the MP4 once into `<project>/public/<slug>/source.mp4`.
       - `VideoRun.tsx` (MP4 idle-trim path) — plays one source span of the screen MP4 for a beat, at `factor` 1 (realtime) or `speedramp_factor` (OffthreadVideo `playbackRate`). Lay out one per active span between the trimmed `idle_gaps`; the beat length is `videoBeatOutputFrames(startS, endS, fps, factor)` from `./timing`. Add it to the copy set when the source is an MP4 with idle gaps: `cp "${CLAUDE_PLUGIN_ROOT}/skills/screencast-cut/scene-templates/"{VideoRun.tsx,BlurredFrozenFrameCard.tsx} "<project>/videos/<slug>/scenes/"`.
       - `BlurredFrozenFrameCard.tsx` (MP4 idle-CUT placeholder) — the video equivalent of `IdleCutCard`: a blurred frozen frame of the recording (`<Freeze>` on one source frame inside the cut) with a "skipped ahead" hint. Use it for `kind="cut"` video idle gaps instead of the terminal "…" card.
       - Check the import path at the top of each copied scene (`../../../src/brand/active`) resolves from `videos/<slug>/scenes/`; fix the depth if your project nests differently.

   **(b) Author the card scenes freehand** — they have no fragile timing, so they stay simple local components. Reuse a profile component **only if the file exists** at `<project>/src/brand/profiles/<active>/components/<Name>.tsx`; the `default` profile ships none, so a default-profile cut scaffolds these fresh:
       - `IntroCard.tsx` — wraps `WordmarkHero` (or whatever the active profile exposes) for the opener. Omit if `intro_frames = 0`.
       - `ChapterCard.tsx` — only when a chapter title was extracted in Phase 2. Reuse `<active>/components/ChapterCard.tsx` or `TitleCard.tsx` if present; else scaffold a minimal version that types the chapter title in the profile's display face.
       - `RecapCard.tsx` — only when `chapter_position = middle`. 7s "Last time: <X>. Now: <Y>." reorientation beat in the profile's voice.
       - `IdleCutCard.tsx` — the "…" placeholder for cut gaps.
       - `OutroCard.tsx` — shaped by the **resolved `cta_shape`**: `next-steps` → one concrete next-action line; `question` → on-screen question; `logo-card` → wordmark-only (used by `chapter_position = last` and middle-chapter transitional outros).

   **(c) Add animated icons / motion primitives** when a beat wants a flourish — a ✓ when a command succeeds, an arrow at terminal output, sparkles on a card, a spinning loader, or a ripple on a click. Animation here is **code, not data**: permissive static SVGs animated with Remotion's frame-deterministic primitives. (SVG recipes are the default; **Lottie** is a separate, second-class *bring-your-own* hatch — see the Lottie bullet below.) Copy the engine in alongside the reference scenes:
       ```bash
       cp -r "${CLAUDE_PLUGIN_ROOT}/skills/screencast-cut/scene-templates/"{recipes.ts,AnimatedIcon.tsx,ClickRipple.tsx,icons} \
          "<project>/videos/<slug>/scenes/"
       ```
       - **Recipes (5):** `drawOn` (stroke reveal via `evolvePath`, staggered + eased), `popIn` (spring scale), `spin` (rotate, for loaders), `burst` (particles via our pure geometry + `@remotion/shapes`), `morph` (`interpolatePath` between two structurally-compatible single-path icons). `popIn`/`spin`/`burst` work on ANY icon; `drawOn` needs path data (it falls back to `popIn` for a pathless icon); `morph` needs a compatible `morphTo`.
       - **Icons:** `<AnimatedIcon icon={icons["check"]} recipe="popIn" color={palette.accent} />`. The curated floor (`scenes/icons/index.ts`, Lucide ISC, ~14 icons) is the **offline baseline**. Need one that isn't there? Pull it once into the project, then it's local forever:
         ```bash
         python3 "${CLAUDE_PLUGIN_ROOT}/skills/screencast-cut/scripts/fetch_icon.py" \
             lucide:rocket --icons-dir "<project>/videos/<slug>/scenes/icons"
         ```
         The puller only accepts permissively-licensed sets (ISC/MIT/Apache: lucide, tabler, ph, heroicons, mdi, …) and records each in `THIRD-PARTY-NOTICES`; it refuses anything else.
       - **Click ripple (beachhead):** on the MP4 zoom path, mount `<ClickRipple x={anchor.x} y={anchor.y} color={palette.accentGlow} />` from the same `zoom_anchors.json` anchor the zoom uses — no icon needed.
       - **Theme-tunable motion, precedence `config < profile < per-use`.** Defaults come from the active profile's `motion` block in `style-guide.ts` (`defaultRecipe`, `durationInFrames`, `easing` — a key of the profile `easings` — and `particleIntensity`), which itself falls back to the global `config.json` `"motion"` defaults; any per-use prop on `<AnimatedIcon>` wins. Swapping the active profile changes icon motion without touching a scene. Keep it theme-level — do **not** build a per-icon-per-theme matrix.
       - **Per-theme example packs (reference).** Each shipped demo theme (`default`, `foolswithtools-brand`) has a small curated *example pack* — a handful of `<AnimatedIcon>` usages tuned to that theme's `motion` personality — in `GALLERY-motion-themes.md`. Use it as a starting palette when a beat wants on-brand flourishes; the same pack reads differently under each theme (e.g. `default` strokes a check on with the `pop` easing, `foolswithtools-brand` pops it in with the hand-drawn `scribble` easing and a denser burst). For rendering the same pack under multiple themes in one composition, `<AnimatedIcon>` accepts an optional `theme={{ motion, easings }}` prop that overrides the active-profile defaults (precedence unchanged); with no `theme` prop it reads `src/brand/active` exactly as before. The golden project's `golden-themes` composition + the `theme-pack-*` probes are the worked example.
       - **Bring-your-own Lottie (escape hatch — prefer the SVG recipes above).** When the user supplies a Lottie file *they* have the rights to, render it with `@remotion/lottie` via `scene-templates/LottieIcon.tsx` (copy it in alongside the recipes). Lottie is **second-class**: it can't be cleanly theme-recolored and is only conditionally deterministic. Three hard rules, all enforced:
         1. **Never bundle a third-party Lottie.** The only Lottie committed to this repo is one we authored ourselves (CC0/owned, with a `PROVENANCE` note). A user's file is read from **their** path at render time and copied only into the project's `public/` (their own, typically gitignored) — never into the plugin or a committed fixture. The guardrail (`tests/test_lottie_guardrail.py`) fails the build if a Lottie-shaped JSON is committed without an OWNED/CC0 provenance note.
         2. **Vet first — reject expressions.** Run `python3 "${CLAUDE_PLUGIN_ROOT}/skills/screencast-cut/scripts/lottie_ingest.py" <file> --check-only` (optionally `--color '#22d3ee' --out themed.json`). After-Effects expressions flicker headlessly, so an expression-driven file is **rejected** with a clear message — re-export with expressions baked out, or use the SVG recipes.
         3. **Recolor is best-effort.** Flat fills/strokes recolor to the brand accent (`scripts/recolor_lottie.mjs` via `@lottiefiles/lottie-js`, or the Python path in `lottie_ingest.py`); gradients/animated colors are left alone and reported. Load the vetted file with `<LottieIcon src="lottie/<file>.json" />` (served from `public/`, fetched behind `delayRender`) so it renders deterministically.
       - **Originated per-theme Lottie motifs (owned, bundleable — the licensing-clean way to ship Lottie).** Distinct from the BYO hatch: `scene-templates/lottie/` ships one **original** Lottie motif per demo theme, authored in-repo by `scripts/gen_theme_lottie.py` — `default-orbit` (cyan dot orbiting an indigo ring) for `default`, `foolswithtools-spark` (acid star + charcoal ink border + orange core) for `foolswithtools-brand`. Because we authored them they're OWNED (each dir has a `PROVENANCE`), they're vetted expression-free, and they're already in each theme's palette (no recolor). Copy the chosen `.json` into the project's `public/lottie/` and render it the same way: `<LottieIcon src="lottie/<motif>.json" />`. The worked example is the golden project's `golden-theme-lottie` composition. To add/tweak a motif, edit `scripts/gen_theme_lottie.py` (hand-authored shape JSON, no After Effects) and regenerate; it's vetted expression-free on the way in.

   **cancelRender convention (load-bearing — do not skip).** Every visual asset (PNG frame, MP4) must be rendered through the `SafeImg` / `SafeVideo` wrappers you copied in (a), which call `cancelRender()` from `remotion` in `onError`. This converts "missing asset → silent black frame" (which a vision check might wave through) into a **deterministic `renderStill` failure** the Phase-4 verify loop catches every time. Audio is the one exception: use `SafeAudio` (in `SafeVideo.tsx`), which **warns only** — a missing voiceover should still ship a render. The card scenes you author freehand must use these wrappers too for any image/video they pull in. This requirement is mirrored in the `remotion-video` SKILL.md Phase 4 (the scene-authoring authority).

5. **Wire the master** at `<project>/videos/<slug>/Root.tsx` using `<TransitionSeries>` from `@remotion/transitions`. Compute `durationInFrames` with `computeMasterDuration(beatDurations, transitionFrames)` from `./timing` — do not hand-add the overlaps (that arithmetic is the tested helper's job). For speed-ramped beats, the beat's output length is `speedrampOutputFrames(startIdx, endIdx, factor)`, also from `./timing`.

6. **Register** the master composition in `<project>/src/Root.tsx` with composition `id` = the slug.

7. **PNG-verify** each scene as you build it with `npx remotion still <slug> --frame=<midpoint> --scale=<screenshot_scale> --output=videos/<slug>/.checks/<scene>-<frame>.png` and read the PNG. Fix off-screen elements / text-overflow before moving on. This is the quick per-scene check; the whole-composition verify loop is step 8.

8. **Run the bounded verify loop** once the master is wired. This is the shared render-verification harness (`render → look at the image → fix`), the single most important guard against run-to-run quality drift.

   ```bash
   python3 "<remotion-video plugin>/skills/remotion-video/scripts/verify_render.py" \
       "<project>" "<slug>" \
       --expect-duration-frames <computeMasterDuration result> \
       --expect-width <w> --expect-height <h> \
       --scale <verify_scale> --json
   ```
   Resolve the `verify_render.py` path the same way you resolve the playbook fallback (Phase 2 step 9): walk up from this SKILL.md to `plugins/`, then `remotion-video/skills/remotion-video/scripts/verify_render.py`. It reads the manifests under `videos/<slug>/source/`, renders a filmstrip into `videos/<slug>/.checks/`, and writes `verify-summary.json` + `filmstrip.md`.

   **Loop (hard cap `MAX_VERIFY_ITERS = 3`):**
   1. Run `verify_render.py`. Exit `3` = environment error (node/Remotion/manifests) — fix the environment, not the cut. Exit `2` = a deterministic gate or a still failed (`status: fail`): **fix the single failing gate** named in `verify-summary.json` (e.g. duration mismatch → recheck `computeMasterDuration`; a still failure → the `cancelRender` fired on a missing asset, fix the `staticFile` path/copy), then re-run the **full** check. If the *same* gate fails twice → escalate to the user with the summary.
   2. When gates pass (exit `0`, `status: pass`), **judge the filmstrip against `RUBRIC.md`** (V1–V8). From iteration 2 on, hand this to a **fresh-eyes subagent** that receives ONLY `filmstrip.md` and `RUBRIC.md` (no project context) and returns a per-V verdict. Zero V-failures → **success**. Otherwise make the **smallest fix per V-item**, re-run `verify_render.py --stills-only`, re-judge. The *same* V-item on the *same* frame twice → escalate.
   3. **Pass = `status: pass` AND zero V-failures.** A deterministic pass alone is not victory. On hitting `MAX_VERIFY_ITERS`, stop and escalate with the current summary, the outstanding failures, and the fixes you tried.

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
- **Fumble cut**: a run of ≥ `fumble_min_backspaces` (default 3) backspaces, or any Ctrl-U/Ctrl-W kill, in the cast input stream → a cut **candidate** spanning the mistyped line through the recovery keystroke. Surfaced for approval in Phase 3 (`fumble_auto_cut` default `false`); when approved it's dropped like an `idle_cut`. Theme-overridable via an `editing` block in `style-guide.ts` (`editing.fumble_min_backspaces`, `editing.fumble_auto_cut`), precedence **config < theme `editing` < user prompt** — same shape as the `tts`/`motion` blocks; a per-theme `editing` edit is a studio change, flag it for the user.
- **Screen-recording idle-trim**: a static stretch in an MP4/MOV (mean-abs grayscale pixel diff < `video_idle_pixel_diff_threshold`, default 2.0, sampled at `video_idle_sample_fps`, with the top-right menubar-clock box masked) reuses the cast cadence — ≥ `idle_threshold_speedramp_seconds` → speed-ramp (OffthreadVideo `playbackRate`), ≥ `idle_threshold_cut_seconds` → cut (a blurred frozen-frame card, not "…"). Same `idle_gaps` shape as the cast path. No scene-change/chapter detection.
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
- If the MP4 has no resolvable click data (no Screenize package, no manual `events.json`), skip the auto-zoom layer and play the MP4 1× behind captions — don't fabricate zoom points from nothing. The idle-trim layer is independent and still runs.
- Idle-trim and auto-zoom are independent additive layers on the MP4 path: a recording can be idle-trimmed with no clicks, zoomed with no idle gaps, both, or neither.
- If no `PLAYBOOK-<genre>.md` resolves anywhere (broken plugin install), proceed with raw config defaults and tell the user the playbook layer is unavailable.

## Error handling

- **Playbook resolution failed.** All three playbook paths missed (profile, project default, plugin template). Proceed with config defaults only and tell the user "no playbook found — running on raw config; run the `remotion-video` skill to scaffold default playbooks into your project." Do not fabricate a playbook.
- **Unknown decision-override key in playbook.** The playbook had a `key: value` line under `## Decision overrides` with a key the parser doesn't recognize. Skip that line, surface a one-line warning, and continue. Don't silently accept new keys — they signal schema drift.
- **`agg` / `ffmpeg` / `whisper-cli` missing.** Surface the exact install command for the user's platform and stop.
- **Cast file unreadable / wrong version.** `cast_to_frames.py` accepts v1, v2, and v3; anything else → tell the user to re-record with a recent asciinema and stop.
- **Whisper model missing.** The `transcribe.py` script lists the paths it searched. Tell the user to download with `whisper-cli --model-download <name>` and retry.
- **ElevenLabs token missing (Script: path only).** `script_to_audio.py` lists the resolution order it tried (`$ELEVENLABS_API_TOKEN` → `--envrc` files → `~/.envrc` → `~/.config/screencast-cut/secrets.env`). Tell the user to set the token one of those ways and retry. **Never print the token.** If the user only has pre-recorded audio, they can use `Audio:` instead and skip TTS entirely.
- **ElevenLabs voice name not found.** `script_to_audio.py` lists the account's available voice names. Pick one from the list, pass `--voice-id` directly, or adjust the theme's `tts` block / `Voice:` override.
- **Audio drift.** If the audio duration differs from the cast duration by more than a few percent, warn the user — typically means they recorded narration separately and didn't sync. Offer to either trim audio or stretch terminal playback.
- **No Remotion project.** Phase 1 already handles this — point the user at the `remotion-video` skill and stop, don't scaffold from here.
- **MP4 with no event data.** Tell the user up-front. CleanShot X, QuickTime, and the macOS Screenshot app don't export click coordinates. Two paths: re-record with a tool that does (Screenize is one), or have them author a manual `events.json` from memory or by stepping through the MP4. Don't silently skip — offer the choice.
- **`parse_events.py` formatVersion mismatch.** The polyrecorder schema is young and will move. Surface the actual `formatVersion` you got vs. the one expected and tell the user to either update their recorder or downgrade. Don't try to interpret an unknown schema version.
- **Zoom would clip the visible window.** Pre-validate before writing scenes: for each anchor, check that a window of size `1/zoom_factor` centered on `(x, y)` stays inside `[0, 1]`. If not, ask the user (via AskUserQuestion) whether to recenter, reduce zoom, or skip that anchor.

## Notes

- `${CLAUDE_PLUGIN_ROOT}` is set by Claude Code at load time. If unset, derive paths from this SKILL.md's location.
- `${CLAUDE_PLUGIN_ROOT_REMOTION_VIDEO}` (referenced in Phase 2 step 9 for the playbook fallback) may not be defined — do not depend on it. The reliable path is to walk up from this SKILL.md to the `plugins/` root and append `remotion-video/skills/remotion-video/templates/default/`. Prefer the env var only if it happens to be set.
- The split between this skill (cuts source material into a project) and the `remotion-video` skill (renders projects, owns the brand profile system) is deliberate. **Do not merge their SKILL.md files.** They share the same project directory and brand-profile system, but the workflows are different shapes — prompt-to-video vs. recording-to-video.
- Per-video subdirectories (`videos/<slug>/`) keep PLAN, scenes, source-frames, transcript, screenshot checks under `.checks/`, and the rendered MP4 colocated. The top-level `src/Root.tsx` is the registry.
- Frames live under `<project>/public/<slug>/frames/` so `staticFile()` resolves them. The duplicated PNGs under `videos/<slug>/source/frames/` are kept as the working copy in case you want to re-render or hand-tweak.
- Resist editing the active profile's `style-guide.ts` mid-cut. Promotions happen in Phase 6, after a successful render.
