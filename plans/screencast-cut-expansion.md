# screencast-cut expansion plan

Drafted 2026-05-12. Three slices the user wants to ship to bring more of the actual video pipeline inside the plugin (instead of as conventions living in `~/videos-studio/STARTHERE.md`).

**How to use this plan in a future session:**

1. Read this whole file end-to-end so you understand cross-slice coupling.
2. Pick *one* slice. Confirm the open decisions in its "Decisions to make" section with the user before coding.
3. Ship it (plugin version bump + marketplace.json entry + USAGE.md update + guardrail script run, per `CLAUDE.md` pre-push ritual).
4. Update this file: strike through the slice, append "shipped in commit `<sha>`."

The slices are roughly independent. Recommended order: **A → B → C** (TTS first because it's the most-requested capability gap; backspace detection is small and self-contained; screen-recording auto-trim is the largest scope and benefits from validating the playbook plumbing on the smaller slices first). User may reorder.

---

## Background (why we're doing this)

Two relevant facts from the 2026-05-12 conversation:

- The user already generates voiceovers with ElevenLabs end-to-end in `~/videos-studio/` — but it's a *recipe in `STARTHERE.md`*, not a plugin feature. A fresh user / fresh machine doesn't inherit it. We want to promote it.
- The user records terminal sessions live and frequently fumbles (backspacing through typos) and has long gaps between commands. Idle-gap collapse handles the gaps; nothing handles the fumbles. The user also wants to feed in screen recordings (desktop / browser) and have them edited the same way casts are.

These three slices together close the gap between "what `screencast-cut` does today" and "what the user's full workflow already does, plus what they'd like."

**Themes (brand profiles) are the central organizing concept.** Everything new in this plan should be configurable per-theme. A theme already controls visuals (palette, type, motion, layout via `style-guide.ts`); after this work it should also control:

- **Voice** — which ElevenLabs voice the narration uses, and any per-theme audio post-processing (loudnorm targets, etc.).
- **Cut cadence** — how aggressively idle gaps, fumbles, and video dwells get trimmed. A loud poster-style theme (`pop-maximalist`) wants different rhythm than a quiet documentary one (`cinematic-noir`).

The two existing thresholds in `config.json` (`idle_threshold_speedramp_seconds`, `idle_threshold_cut_seconds`) are global defaults today. After this work they remain global *defaults*, but a theme can override any of them. The precedence stays: `config.json` < `playbook` < theme overrides < per-video prompt. Document this clearly in `SKILL.md`.

The hard constraint from `CLAUDE.md` still applies: no committed file may state or imply that Anthropic uses Remotion. Run `bash scripts/check-no-anthropic-remotion-claim.sh` before every push.

---

## Slice A — ElevenLabs TTS inside screencast-cut

**What:** Accept a narration *script* (text) as an alternative to a narration *audio file*. If given a script, generate the audio via ElevenLabs, normalize it with `ffmpeg loudnorm`, then continue down the existing audio path (Whisper transcription → caption alignment → render).

**Why:** Today the user provides a pre-recorded `.m4a`. The full pipeline they actually run is "write script → generate audio with ElevenLabs → loudnorm → hand to `screencast-cut`." Steps 1–3 live as a recipe in `~/videos-studio/STARTHERE.md`. We want them as a first-class plugin capability so a fresh user can do the full flow from a single prompt.

### Inputs and prompt shape

New optional inputs the skill should accept:

- `Script:` — path to a `.txt` / `.md` file containing the narration text. Plain text; lines are concatenated into one sequence. Sentences become natural caption groupings, but Whisper still drives the word-level timing.
- `Voice:` — optional voice name override (e.g. `Voice: Bill`). If omitted, falls back to the active brand profile's `tts.voice` field (see schema below), then to a plugin default.

Existing `Audio:` input remains supported and takes precedence over `Script:` when both are present (user can pre-render audio for higher control).

**Decision to make with user:** what happens when both `Audio:` and `Script:` are passed? Options: (1) `Audio:` wins, warn that `Script:` was ignored; (2) error; (3) prefer `Script:`, treat audio as a fallback. Recommendation: option 1 — easiest to reason about, hardest to misuse.

### Theme schema additions

Each brand profile (theme) under `<project>/src/brand/profiles/<name>/` gets a new `tts` block in `style-guide.ts`, mirroring how `palette` and `layout` are already exported:

```ts
export const tts = {
  voice: "Bill",                          // ElevenLabs voice name (human-readable)
  voice_id: "pNInz6obpgDQGcFmaJgB",       // ElevenLabs voice ID (canonical)
  alternates: ["Matilda", "Bella"],       // theme-approved alternate voices the
                                          //   user can pick at prompt time
                                          //   (e.g. "Voice: Matilda")
  model: "eleven_multilingual_v2",        // ElevenLabs model
  loudnorm: { I: -18, TP: -2, LRA: 11 },  // theme-specific normalization target
  voice_settings: {                       // ElevenLabs voice_settings (optional)
    stability: 0.45,
    similarity_boost: 0.75,
    style: 0.0,
  },
};
```

Key concepts:

- **`voice` is the theme default** — used when the prompt doesn't specify a voice.
- **`alternates` is the theme-approved roster** — the user can pick any of these at prompt time (`Voice: Matilda`) and stay "on-brand." Picking a voice *not* in `voice` or `alternates` is allowed but the skill should call it out in the Phase 3 plan ("note: 'River' is outside this theme's approved roster").
- **`voice_id` is the source of truth** — `voice` and `alternates` are human-readable labels. The plugin resolves names → IDs via ElevenLabs' `/v1/voices` endpoint and caches the mapping at `~/.cache/screencast-cut/voices.json` so we don't round-trip on every render.
- **`loudnorm` and `voice_settings` are theme-tunable** — a loud theme can ride hotter; a quiet doc theme can sit at `-20 LUFS`. Falls back to plugin-wide defaults in `config.json` if omitted.

For `thick-stroke-americana`, seed with **Bill** as `voice` and **Matilda**, **Bella** as `alternates` (per `~/videos-studio/src/brand/profiles/thick-stroke-americana/BRAND.md:52`). For each of the other test-video themes (`cinematic-noir`, `period-display`, `paper-and-marker`, `print-decay`, `quiet-hud`, `pop-maximalist`, `cyberpunk-ui`, `grid-discipline`, `wood-type-loud`), pick a voice that matches the aesthetic — confirm choices with the user when shipping. Prior multi-theme runs used Daniel / Callum / Matilda / River / Jessica as a starting menu.

### CLI surface for theme voice management

To make picking voices ergonomic, ship a small helper script: `plugins/screencast-cut/skills/screencast-cut/scripts/list_voices.py`. Lists all ElevenLabs voices the API key has access to, plus which themes already reference each. Helps the user (or future Claude) pick alternates for new themes.

### Plumbing

New script: `plugins/screencast-cut/skills/screencast-cut/scripts/script_to_audio.py`

Responsibilities:

1. Read script file → strip whitespace → concatenate.
2. Resolve API key (see "API key handling" cross-cutting section below).
3. POST to `https://api.elevenlabs.io/v1/text-to-speech/<voice_id>` with the model + script. Stream the MP3 back.
4. Convert MP3 → loudnormed WAV via ffmpeg (Whisper wants WAV anyway, so do the conversion here and feed the same WAV to `transcribe.py`).
5. Write `narration.wav` next to wherever the script lived (or to a tmp dir if the script was under a read-only path).
6. Emit a small JSON manifest: `{voice, voice_id, model, characters_used, output_path}` for the Phase 3 "Decisions" table.

Skill changes:

- `SKILL.md` Phase 1: accept `Script:` alongside `Audio:`.
- `SKILL.md` Phase 2: when classifying input, if `Script:` is present, plan a "TTS generation" pre-phase before transcription. Surface voice choice in the Phase 3 decisions table.
- `SKILL.md` Phase 4: run `script_to_audio.py` before `transcribe.py`. The transcribe step is unchanged — it just reads the freshly-generated WAV.

### API key handling (also serves slice C and any future external API)

Resolution order:

1. `ELEVENLABS_API_TOKEN` env var if already set.
2. Source `/Users/t/_repos/foolswithtools/.envrc` if present (current user's setup; `STARTHERE.md` documents this).
3. Source `~/.envrc` if present.
4. Read from `~/.config/screencast-cut/secrets.env` (new, plugin-scoped fallback so portable users have one path).
5. Fail with an actionable message: "Set `ELEVENLABS_API_TOKEN` in your env, in `~/.envrc`, or in `~/.config/screencast-cut/secrets.env`."

**Hard rule:** never echo the token. `set +x` before any curl. Don't print env in error messages.

### Files touched

- `plugins/screencast-cut/skills/screencast-cut/SKILL.md` — input shape, Phase 2/4 changes.
- `plugins/screencast-cut/skills/screencast-cut/config.json` — add `tts_default_voice`, `tts_default_model`.
- `plugins/screencast-cut/skills/screencast-cut/scripts/script_to_audio.py` — new.
- `plugins/screencast-cut/USAGE.md` — add a "narration: audio OR script" subsection; document the API key resolution; remove the "It won't generate the voiceover audio" disclaimer.
- `plugins/screencast-cut/.claude-plugin/plugin.json` — version bump.
- `.claude-plugin/marketplace.json` — version bump.
- `~/videos-studio/src/brand/profiles/*/style-guide.ts` — add `tts` exports for at least `thick-stroke-americana` (others can follow). This edit lives in the user's studio, not in toolshed — flag it for the user to run separately.

### Acceptance test

In `~/videos-studio-fresh-test/`:

```
"Use the screencast-cut skill. Source: jq-tutorial.cast. Script: topic.md.
 Make a 45-second tutorial using the thick-stroke-americana profile."
```

Should produce `videos/jq-tutorial/out.mp4` with Bill-voiced narration, loudnormed, captions synced. No file at `~/Recordings/voice.m4a` needed.

### Decisions to make with user before coding

1. `Audio:` vs `Script:` precedence — see above.
2. Where to cache the voice-name→voice_id mapping. Recommendation: `~/.cache/screencast-cut/voices.json`.
3. Where the plugin-scoped secrets fallback file lives. Recommendation: `~/.config/screencast-cut/secrets.env`.
4. Should the plugin support other TTS providers (OpenAI, Cartesia, Azure)? Recommendation: not in this slice — ElevenLabs only. Add an abstraction seam (`tts_provider` field in config) but only implement ElevenLabs. Bias toward shipping.

---

## Slice B — Backspace / fumble detection in terminal casts

**What:** Detect "fumble-and-retype" regions in `.cast` event streams (sequences of backspace characters followed by retyping) and surface them as cut candidates alongside the existing idle-gap detection.

**Why:** Users recording live terminal sessions routinely make typos and backspace through them. Currently those regions play back at full speed because backspace events look like normal activity to the idle-gap detector. The user explicitly asked for this in the 2026-05-12 conversation.

### Detection algorithm

In `cast_to_frames.py`, add a new pass alongside `find_idle_gaps`:

```python
def find_fumble_regions(events, min_backspaces=3, lookahead_window_s=10):
    """Find stretches where the user typed, backspaced 3+ chars, then retyped.

    Returns list of {"start_s", "end_s", "duration_s", "kind": "fumble"}.
    """
```

Heuristic (adjust during implementation):

1. Walk input (`i`) events. A backspace is `\x7f` or `\b` (0x08).
2. Find runs of >=N consecutive backspaces (default N=3 — single-char corrections are too noisy to cut).
3. The fumble *start* = the timestamp of the keystroke immediately before the backspace run began (walk back through `i` events to find where the bad typing started — anchor at last shell prompt or last `\r`).
4. The fumble *end* = first non-backspace `i` event after the backspace run that produces at least N *different* characters (recovery typing).
5. Emit one region per fumble, marked with `kind="fumble"`.

This is intentionally a heuristic — false positives are fine because Phase 3 surfaces them to the user for approval. False negatives are also fine (just leaves the fumble in).

### Treatment

Fumble regions become **cut candidates** (not auto-cuts), surfaced in the Phase 3 plan alongside idle gaps. The user approves or rejects per-region. When approved, the cut is implemented exactly like an existing `idle_cut`: the frames between `start_s` and `end_s` are dropped, the surrounding terminal output appears to skip ahead.

Add config knobs (global defaults in `config.json`, overrideable per-theme in `style-guide.ts` under a new `editing` block — see "Themes are first-class" below):

- `fumble_min_backspaces` (default 3) — fewer than this isn't worth cutting.
- `fumble_auto_cut` (default `false`) — if `true`, skip the Phase 3 confirmation and cut automatically. Brave users only. A "fast-paced shortform" theme might set this to `true`; a careful tutorial theme keeps it `false`.

### Files touched

- `plugins/screencast-cut/skills/screencast-cut/scripts/cast_to_frames.py` — add `find_fumble_regions`, include in output JSON under a new `fumble_regions` key.
- `plugins/screencast-cut/skills/screencast-cut/config.json` — add the two knobs.
- `plugins/screencast-cut/skills/screencast-cut/SKILL.md` — Phase 3 plan now includes a fumble-cut section; document the config knobs.
- `plugins/screencast-cut/USAGE.md` — update the "no fumble detection" caveat to say "yes, but you confirm cuts in Phase 3."

### Acceptance test

Record a `.cast` of:

```
$ ehco hwllo  <BACKSPACE x9>  echo hello
```

Run `cast_to_frames.py` against it. Verify the output JSON contains one entry under `fumble_regions` covering the fumble + recovery, with `duration_s > 0`. Then run a full cut and verify the fumble is gone from the rendered video.

### Decisions to make with user before coding

1. Default for `fumble_auto_cut` — `false` (confirm in Phase 3) or `true` (silent)? Recommendation: `false`. Users can opt into silent mode per-profile or per-video.
2. Min backspaces threshold (3 vs 5 vs other). Recommendation: 3 — captures most real fumbles, single/double-char corrections stay in.
3. Should we also detect Ctrl-U (kill-line) and Ctrl-W (kill-word)? They serve the same purpose as a long backspace run. Recommendation: yes, add them as additional triggers in the same pass.

---

## Slice C — Screen-recording auto-trim (idle-frame detection for MP4/MOV)

**What:** Apply terminal-style "auto-trim idle stretches" editing to screen recordings (desktop / browser). Today the plugin accepts `.mp4` / `.mov` but only does auto-zoom on clicks (if a sidecar events.json exists). It does *not* speed-ramp or cut idle stretches. We add that.

**Why:** The user explicitly asked for "similar editing to what we're doing with terminal sessions" for screen recordings. Long static periods (reading a page, scrolling slowly, dwelling on a result) should compress the same way terminal pauses do.

### Detection algorithm

In a new script `plugins/screencast-cut/skills/screencast-cut/scripts/video_to_frames.py`:

1. Probe the input MP4 with ffprobe → duration, fps, dimensions.
2. Sample frames at low fps (default 4 fps — enough resolution for idle detection without being slow). Use ffmpeg's `-vf "fps=4"` to a temp dir, or pipe through pyav.
3. For each consecutive frame pair, compute a similarity score. Two reasonable choices:
   - **SSIM** (via ffmpeg `ssim` filter or `scikit-image`) — perceptually meaningful, slightly slower.
   - **Mean absolute pixel difference** on a downsampled (256×144) grayscale version — much faster, slightly cruder, fine for "is the screen static" detection.

   Recommendation: start with mean abs pixel diff; upgrade to SSIM only if false positives are a problem.
4. A frame pair with diff below `idle_pixel_diff_threshold` (default e.g. 2.0 on 0–255 grayscale) is "static."
5. Consecutive static frames covering >= `idle_threshold_speedramp_seconds` → speed-ramp candidate.
6. Consecutive static frames covering >= `idle_threshold_cut_seconds` → hard-cut candidate.
7. Emit the same `idle_gaps` JSON shape as `cast_to_frames.py` so the downstream Remotion scene-planning code can be shared.

The output format should mirror `timing.json` from `cast_to_frames.py`:

```json
{
  "source_type": "video",
  "duration_s": ...,
  "fps": 30,
  "frame_count": ...,
  "idle_gaps": [{"start_s", "end_s", "duration_s", "kind"}, ...],
  "video_path": "absolute path to source",
  "video_dimensions": {"w": 1920, "h": 1080}
}
```

The downstream `TerminalRun.tsx` style scene component for video is `VideoRun.tsx` (new — see below).

### Scene rendering changes

Today Phase 6 (render) uses `TerminalRun.tsx` for cast input and probably a different rectangle-of-pixels component for MP4 input. Audit the current state and:

- Confirm there's already a `VideoSpan.tsx` or similar for MP4 input. If yes, add speed-ramp support to it (just like `TerminalRun.tsx`'s speedramp_factor mapping). If no, write `VideoRun.tsx`: renders an `<OffthreadVideo>` clipped to `[start_s, end_s]` with optional `playbackRate` for speed-ramps.
- For hard-cut gaps, reuse the existing `IdleCutCard.tsx` "…" placeholder — same UX as terminal cuts.

### Click-event integration (already exists; touch only if needed)

Auto-zoom on clicks already works *if* a sidecar events.json is present. Keep that path. Slice C is purely additive (idle detection) — it doesn't change the click-zoom layer.

If the user has neither click events nor idle gaps, the video just plays full-frame full-speed with captions over it — same as today.

### Files touched

- `plugins/screencast-cut/skills/screencast-cut/scripts/video_to_frames.py` — new.
- `plugins/screencast-cut/skills/screencast-cut/SKILL.md` — Phase 2 input classification now invokes `video_to_frames.py` for `.mp4`/`.mov` sources; document the new config knobs.
- `plugins/screencast-cut/skills/screencast-cut/config.json` — add `video_idle_sample_fps` (4), `video_idle_pixel_diff_threshold` (2.0). Reuse existing `idle_threshold_speedramp_seconds` / `idle_threshold_cut_seconds` / `speedramp_factor` for the actual cuts (consistency between cast and video). All four are overrideable per-theme (see "Themes are first-class").
- Remotion-side scene components (in the user's `~/videos-studio/src/brand/` and/or the plugin's template if there is one) — `VideoRun.tsx` add or extend.
- `plugins/screencast-cut/USAGE.md` — remove the "screen recording plays full-frame" caveat, replace with "screen recording is auto-trimmed like a terminal cast."

### Acceptance test

Record a 90-second browser session that includes: 20s active browsing → 30s of dwelling on a single page (idle) → 40s more browsing. Feed to the skill with a script. Verify the rendered video is ~70s long (the 30s dwell speed-ramped 4× to ~7s, or hard-cut to a "…" beat depending on thresholds).

### Decisions to make with user before coding

1. SSIM vs mean-pixel-diff for similarity. Recommendation: start with mean-pixel-diff for speed.
2. What counts as "the cursor moving but nothing else changing"? On a desktop recording, a blinking cursor or a clock advancing in the menubar could defeat naive pixel-diff. Recommendation: mask out a 40px strip on the right edge (clock area) and a small region around the system cursor (if cursor position is available — usually not). If false positives bite, escalate to SSIM with a higher threshold.
3. Should idle-cut placeholders for video also be the "…" card, or a blurred-frozen-frame card with a "skipped ahead" hint? Recommendation: blurred-frozen-frame — terminal "…" looks weird over a video aesthetic.
4. Do we want to also auto-detect *scene changes* (a hard cut between two visually unrelated regions, e.g. switching between tabs) and treat them as chapter boundaries? Recommendation: not in this slice. Park as a future enhancement.

---

## Cross-cutting concerns

### Themes are first-class

This is the spine that ties the three slices together. Every editing decision the plugin makes — voice, cut cadence, fumble tolerance, video idle-trim aggressiveness — should be theme-tunable. The end state we want is: *swapping the active theme changes how the video sounds and how aggressively it's edited, not just how it looks.*

Concretely, each `style-guide.ts` gains two new exports alongside the existing `palette` / `layout` / `motion`:

```ts
export const tts = {
  voice: "Bill",
  voice_id: "pNInz6obpgDQGcFmaJgB",
  alternates: ["Matilda", "Bella"],
  model: "eleven_multilingual_v2",
  loudnorm: { I: -18, TP: -2, LRA: 11 },
  voice_settings: { stability: 0.45, similarity_boost: 0.75, style: 0.0 },
};

export const editing = {
  // Idle-gap trim (terminal casts + screen recordings both honor these)
  idle_threshold_speedramp_seconds: 2,
  idle_threshold_cut_seconds: 8,
  speedramp_factor: 4,

  // Fumble detection (terminal casts only)
  fumble_min_backspaces: 3,
  fumble_auto_cut: false,

  // Video idle detection (screen recordings only)
  video_idle_sample_fps: 4,
  video_idle_pixel_diff_threshold: 2.0,
};
```

Any field omitted from a theme falls through to the plugin's `config.json` default. Themes only need to declare deviations.

**Worked examples** (sketches — actual values to confirm with user per theme):

- `cinematic-noir` (slow, contemplative): `voice: "Daniel"`, `idle_threshold_speedramp_seconds: 4` (let pauses breathe longer), `speedramp_factor: 2` (gentler ramps).
- `pop-maximalist` (fast, loud): `voice: "Jessica"`, `idle_threshold_speedramp_seconds: 1` (cut everything), `speedramp_factor: 8`, `fumble_auto_cut: true`.
- `thick-stroke-americana` (confident, measured): `voice: "Bill"`, defaults for everything else.
- `quiet-hud` (precise, technical): `voice: "Callum"`, `loudnorm: { I: -20, TP: -2, LRA: 7 }` (quieter mix).

**Precedence (document in SKILL.md):**

```
plugin config.json defaults  <  active theme `editing`/`tts` overrides  <  user prompt overrides
```

The Phase 3 plan's "Decisions" table should show, for each value, which level it came from — so the user sees at a glance "this video uses Bill because the active theme is `thick-stroke-americana`" and "idle threshold is 1s because you said so in the prompt."

### Backwards compatibility

All three slices are additive. Existing prompts (`Source: foo.cast. Audio: bar.m4a`) must keep working without changes. The skill's Phase 1 input parsing should treat `Script:`, fumble detection, and video idle detection as opt-in defaults that activate based on input shape, not on a flag.

### Versioning

Each slice ships as its own version bump and its own commit:

- Slice A: `screencast-cut` 0.5.0 ("Add ElevenLabs TTS via `Script:` input").
- Slice B: 0.6.0 ("Detect fumble-and-retype regions in cast input").
- Slice C: 0.7.0 ("Auto-trim idle stretches in screen-recording input").

Update `.claude-plugin/marketplace.json` after every bump.

### Pre-push ritual (from `CLAUDE.md`)

Before every push:

```
bash scripts/check-no-anthropic-remotion-claim.sh
python3 -m json.tool plugins/screencast-cut/.claude-plugin/plugin.json > /dev/null
python3 -m json.tool plugins/screencast-cut/skills/screencast-cut/config.json > /dev/null
python3 -m json.tool .claude-plugin/marketplace.json > /dev/null
```

Re-read every edited Markdown file with the lens "does this imply Anthropic uses Remotion?"

### Documentation

After each slice, update both:

- `plugins/screencast-cut/USAGE.md` — the user-facing onboarding doc.
- `plugins/screencast-cut/skills/screencast-cut/SKILL.md` — the actionable playbook Claude reads at runtime.

If a slice changes Phase 2 / Phase 3 behavior visibly, the "What you'll see, in order" table in USAGE.md needs to reflect it.

### Memory

After shipping, save a project memory noting which slices landed in which commit so future sessions don't propose them again.
