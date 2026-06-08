# How to use `screencast-cut`

You have a screen recording or terminal capture. You want a polished tutorial video out the other end. This guide walks you through it.

You don't need to read the SKILL.md, the playbook system, or any of the plumbing. Talk to Claude Code in plain English — the skill drives the workflow.

---

## Before you start (one time, ~5 min)

### 1. Install the prerequisites

You need four tools (plus `asciinema` if you'll record terminal sessions). What they do:

- `ffmpeg` — audio/video conversion
- `agg` — turns terminal `.cast` recordings into video frames
- `whisper.cpp` (provides the `whisper-cli` binary) — word-level caption transcription from your narration audio
- `node` 18+ — runs the Remotion renderer
- `asciinema` — *optional, only for the terminal-recording path*. Skip if you'll only ever use screen recordings (`.mp4` / `.mov`).

(No extra install for TTS — the `Script:` path uses the ElevenLabs HTTP API. You only need an `ELEVENLABS_API_TOKEN`; see "Narration: bring audio, or just write the script" below. Skip it entirely if you always bring your own `Audio:`.)

#### On Linux (Ubuntu / Debian)

The two easy ones from apt:

```
sudo apt update
sudo apt install -y ffmpeg asciinema build-essential cmake git curl
```

**Node 18+** — Ubuntu's apt usually ships an older node, so use NodeSource:

```
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

**`agg`** — not in apt. Easiest path is the prebuilt binary:

```
# Grab the latest release from https://github.com/asciinema/agg/releases
# pick the linux-x86_64 (or aarch64) tarball, then:
sudo install -m 755 agg /usr/local/bin/
```

(Or `cargo install --git https://github.com/asciinema/agg` if you have Rust.)

**`whisper.cpp`** — build from source. ~2 minutes:

```
git clone https://github.com/ggerganov/whisper.cpp ~/src/whisper.cpp
cd ~/src/whisper.cpp
make
sudo install -m 755 build/bin/whisper-cli /usr/local/bin/
sh ./models/download-ggml-model.sh base.en
sudo mkdir -p /usr/local/share/whisper-cpp
sudo install -m 644 models/ggml-base.en.bin /usr/local/share/whisper-cpp/
```

The skill looks for the model at `/usr/local/share/whisper-cpp/`, `/opt/homebrew/share/whisper-cpp/`, or `~/.cache/whisper.cpp/`. The third path means you can also drop the `.bin` under `~/.cache/whisper.cpp/` if you don't want to `sudo`.

#### On Linux (Fedora / Arch / others)

Same idea — use your distro's package manager for `ffmpeg`, `asciinema`, `nodejs`, plus a build toolchain (`gcc`, `make`, `cmake`, `git`). Then build `agg` and `whisper.cpp` exactly as above. On Arch, `agg-bin` and `whisper.cpp-git` exist in the AUR.

#### On macOS

```
brew install ffmpeg agg whisper-cpp node asciinema
```

#### Verifying the install

All five (or four) commands should resolve:

```
which ffmpeg agg whisper-cli node asciinema
```

If any one comes back empty, fix that before going further — the skill will fail later in a confusing way otherwise.

#### Recording your screen

The skill consumes whatever produces a `.mp4`, `.mov`, or `.cast` — it doesn't care how you made it.

- **Linux screen recording:** OBS Studio is the most common choice (X11 and Wayland), available in most distro repos. SimpleScreenRecorder, Kazam, or `wf-recorder` (Wayland) also work.
- **macOS screen recording:** QuickTime is built-in and free. CleanShot X, OBS, or Screenize also work.
- **Terminal recording (any OS):** `asciinema rec demo.cast`. Stop with `exit` or Ctrl-D. Tip: record with stdin captured (`asciinema rec --stdin demo.cast`) and the skill can also detect **fumbles** — places where you backspaced through a typo (or hit Ctrl-U / Ctrl-W) and retyped — and offer to cut them. Long idle pauses get speed-ramped or cut automatically; fumbles are surfaced for your approval in the planning step (Phase 3), never cut silently by default.

### 2. Make sure your toolshed plugins are up to date

This matters more than you'd expect. Plugins installed via the marketplace stay pinned to whatever version was current the day you installed them. Before reporting any bug — or starting fresh after a long gap — run:

```
/plugin marketplace update toolshed
```

inside Claude Code. If your version is behind, the SKILL.md Claude is reading is *literally a different document* than the current one. This is the single most common source of "it doesn't work like the docs say" confusion.

### 3. Have a Remotion project ready

`screencast-cut` writes a new video into an existing Remotion project. If you don't have one yet, ask Claude:

> "Use the remotion-video skill to scaffold a project at `~/videos-studio`."

That sets up the directory structure, brand profile system, and dependencies. You only do this once per studio. Future videos go into the same project.

---

## What you need for each video

Three things, in increasing order of "must-have":

| Asset | Required? | Notes |
|---|---|---|
| **A recording** | Yes | A `.cast` from `asciinema rec`, or an `.mp4` / `.mov` screen capture from anything (CleanShot, QuickTime, OBS, Screenize). |
| **Narration — audio OR a script** | Recommended | Either `Audio:` (a `.m4a`/`.mp3`/`.wav` you recorded) **or** `Script:` (a `.txt`/`.md` of narration text the plugin speaks with ElevenLabs TTS — see below). Either way you get word-level synced captions; without either you get a silent, caption-free video. |
| **Click-event data** | Optional, MP4 only | Only needed if you want auto-zoom on clicks for a screen recording. CleanShot doesn't export this; Screenize does. Without click data your MP4 still gets idle-trimmed and captioned — you just don't get the click-zoom layer. |

That's the whole input surface.

### Narration: bring audio, or just write the script

You have two ways to give a video its voiceover:

- **`Audio:` a file you recorded** — most control over performance. If you pass both `Audio:` and `Script:`, the audio wins (the script is ignored, with a heads-up).
- **`Script:` a text file** — the plugin generates the voiceover for you with **ElevenLabs** text-to-speech, levels it with `ffmpeg loudnorm`, and feeds it into the same captioning pipeline. No microphone, no recording take.

For the `Script:` path you need an **ElevenLabs API token**. The plugin looks for it, in order:

1. the `ELEVENLABS_API_TOKEN` environment variable,
2. any env file you point it at,
3. `~/.envrc`,
4. `~/.config/screencast-cut/secrets.env`.

Set it any one of those ways. The token is never printed, logged, or written into the project. (No token is needed if you use `Audio:`.)

**Picking a voice.** Each brand profile (theme) can declare its own default `voice` and an on-brand `alternates` roster in its `style-guide.ts` `tts` block; a video uses the active theme's voice unless you say `Voice: <name>` in the prompt. To see which voices your account has, ask the skill to run `list_voices.py`.

---

## The actual usage

Open Claude Code in your Remotion project directory and paste a prompt like one of these:

### Tutorial from a terminal recording

> "Use the screencast-cut skill. Source: `~/Recordings/demo.cast`. Audio: `~/Recordings/voiceover.m4a`. Make a tutorial showing how to use jq."

### Tutorial with narration generated from a script (no recording take)

> "Use the screencast-cut skill. Source: `~/Recordings/demo.cast`. Script: `~/notes/jq-script.md`. Voice: Bill. Make a 45-second jq tutorial."

(The plugin speaks `jq-script.md` with ElevenLabs, loudnorms it, and captions it — you never record a voice take. Drop `Voice:` to use the active theme's default voice.)

### Tutorial from a screen recording

> "Use the screencast-cut skill. Source: `~/Recordings/onboarding.mp4`. Audio: `~/Recordings/narration.m4a`. Cut this into a 60-second product walkthrough."

### Vertical short for TikTok / Reels / Shorts

> "Use the screencast-cut skill. Source: `~/Recordings/quick-tip.mp4`. Audio: `~/Recordings/voice.m4a`. Make this a 9:16 short for TikTok."

### Part of a series

> "Use the screencast-cut skill. Source: `~/Recordings/part2.cast`. Audio: `~/Recordings/voice.m4a`. This is part 2 of 5 in the 'Build a CLI in Go' series, chapter title 'Adding subcommands'."

(The "part 2 of 5" phrasing is what triggers chapter-aware framing — recap-and-continue intro, transitional outro pointing at part 3. Use "part 1" or "first lesson" or "the conclusion" / "final chapter" to signal first/last.)

---

## Animated icons (optional flourishes)

From 0.5.0, cuts can carry small **animated icons** — a ✓ when a command
succeeds, an arrow pointing at terminal output, sparkles on a card, a spinning
loader, or a ripple on a click. They're on-brand by default (recolored to your
active profile's accent) and rendered deterministically, so they look identical
every render. You don't configure anything — just ask:

> "Add a green check that draws on when the install finishes."

> "Put a click ripple on the button when the cursor lands there."

> "Spin a loader while the build runs, then pop in a ✓."

**What's available:**

- **Five motion styles** (recipes): `drawOn` (a stroke draws itself on), `popIn`
  (springs in), `spin` (rotates, for loaders), `burst` (sparkle particles), and
  `morph` (one shape becomes another).
- **A built-in icon set** (~14 common ones: check, x, arrow, terminal, bell,
  sparkles, download, folder, play, loader, …) that works offline.
- **Any other icon, pulled on demand.** Need one that isn't built in? Claude
  fetches it once from a permissively-licensed set (Lucide, Tabler, Phosphor,
  Heroicons, Material, …) into your project, after which it's local forever — no
  network on later renders. Just name it: *"use a rocket icon"*.

**Tuning the feel per brand.** Each brand profile has a small `motion` block in
its `style-guide.ts` (default recipe, duration, easing, particle intensity). Set
it once and every icon in that profile follows suit; a per-use request still
overrides it. The punk `foolswithtools-brand` profile, for instance, pops icons
in with a hand-drawn easing by default, while `default` draws them on. You
rarely need to touch this — it's there so icons match the rest of your videos.

**Per-theme example packs (from 0.7.0).** Each shipped demo theme ships a small
curated *example pack* — a handful of animated-icon usages tuned to that theme's
motion personality — so you have an on-brand starting point instead of a blank
page. The same pack reads differently under each theme: under `default` a check
strokes itself on with a springy `pop`; under `foolswithtools-brand` it pops in
with a hand-drawn `scribble` easing and a denser sparkle burst. Ask for it by
name — *"add the default theme's flourish pack to the success beat"* — or just
say *"give it some on-brand motion"* and Claude picks from the pack for your
active theme. The gallery and the worked `golden-themes` example live in the
plugin (`GALLERY-motion-themes.md`).

> Licensing note: only permissively-licensed icon sets are ever bundled or
> pulled, and each is attributed in a `THIRD-PARTY-NOTICES` file next to the
> icons.

### Bring-your-own Lottie (advanced, from 0.6.0)

If you already have a **Lottie** animation you have the rights to use, the cut
can render it too — but Lottie is a deliberate **second-class citizen** beside
the SVG icons above, with strict rules:

- **We never ship your Lottie.** Your file is read from **your** path at render
  time and is *never* copied into the repo or a plugin. The only Lottie files in
  this project are ones we authored ourselves (CC0/owned, with a provenance
  note). Pulling a file from LottieFiles/Lordicon/etc. and committing it is
  blocked — those catalogs forbid redistributing the JSON.
- **It must be expression-free.** After-Effects *expressions* read the clock and
  **flicker** in headless renders. The ingest check
  (`scripts/lottie_ingest.py`) **rejects** an expression-driven file with a clear
  message — re-export it with expressions baked out, or use the SVG recipes.
- **Recolor is best-effort.** Flat fills/strokes can be recolored to your brand
  accent (`scripts/recolor_lottie.mjs`, or the Python path); gradients and
  animated colors are left alone and reported as "couldn't theme". Lottie can't
  be cleanly themed the way the SVG icons can.

Ask for it by pointing at the file: *"render this Lottie at the end —
`~/anims/confetti.json` — recolored to the accent."* Claude vets it, themes what
it can, drops it in your project's `public/` (gitignored for your own files),
and wires it through `@remotion/lottie`. **Prefer the SVG recipes** for anything
they can do — Lottie is the escape hatch, not the default.

**Originated per-theme Lottie motifs (from 0.8.0).** Separately from the
bring-your-own hatch, the plugin ships one **signature Lottie motif per demo
theme — authored by us**, so it's license-clean to bundle and reuse (OWNED,
expression-free, deterministic). These are real Lottie (rendered through the same
`@remotion/lottie` path), but unlike a BYO file they're committed in the theme's
own palette, so there's nothing to recolor:

- `default` → **`default-orbit`** — a cyan accent dot orbiting a breathing indigo
  ring on near-black (the theme's calm, premium personality).
- `foolswithtools-brand` → **`foolswithtools-spark`** — a chunky acid-green star
  with a 2px charcoal ink border and a hot-orange core, spinning with a punchy
  bounce (the pop-art / punk-zine personality).

They live in `scene-templates/lottie/` (each with a `PROVENANCE` marking it
OWNED); the worked `golden-theme-lottie` example renders both side-by-side. Ask
for one by theme — *"drop the theme's signature Lottie motif on the outro."* To
tweak or add a motif, edit/extend `scripts/gen_theme_lottie.py` and regenerate —
it's hand-authored JSON (no After Effects), vetted expression-free on the way in.

---

## What you'll see, in order

The skill runs in seven phases. You don't drive them — Claude does — but knowing what's normal helps you tell *signal* from *something's wrong*.

| Phase | What's happening | What you should see |
|---|---|---|
| 1 | Locating your Remotion project | "Found project at `~/videos-studio`. Slug: `demo-tutorial`." |
| 2 | Reading your brand profile, classifying input, picking a playbook | A line naming your active profile and the detected genre (`tutorial` or `shortform`). |
| 3 | Planning beats | A numbered beat list with durations, plus a small "Decisions" table showing which value came from config vs. playbook vs. your prompt. **Pause here — say "approve" or push back.** |
| 4 | Building scene files + (if `Script:`) generating narration + transcribing audio | If you gave a `Script:`, ElevenLabs synthesizes the voiceover first (one network call), then Whisper transcribes it locally for captions. With `Audio:`, only Whisper runs (no network). Takes 10–60s depending on length. |
| 5 | Studio preview | Claude opens `localhost:3000` in your browser. **Important: don't render from inside Studio.** Hit spacebar to play, scrub the timeline, comment on what's wrong. |
| 6 | Render | One MP4 lands at `videos/<slug>/out.mp4`. Claude tells you the absolute path. |
| 7 | Capture-learning prompt | One question with three options. Pick "Save as a rule" if it's a pattern, "Just a note" if it's video-specific, or "Skip." |

Phase 3 is the only place you really need to push back. Once you approve the plan, the rest runs.

---

## Things that might trip you up

- **The Studio page loads and you think "now what?"** — Spacebar plays. The left sidebar lists your video. Scrub the timeline at the bottom to inspect frames. Edit a file under `videos/<slug>/scenes/` and Studio hot-reloads. To render the final MP4, leave Studio open and tell Claude "render it" — Claude runs the render command. You don't render from Studio.

- **"It can't find my recording."** — Use absolute paths in your prompt (`~/Recordings/demo.mp4`), not relative ones, unless you're already `cd`-ed into the directory holding the file.

- **Your audio is `.m4a` or `.mp3` and the transcription seems to fail silently.** — Should be auto-handled in screencast-cut 0.4.0+. If you're seeing it, run `/plugin marketplace update toolshed` — you're behind.

- **Screen recording, no auto-zoom on clicks.** — Most screen recorders (OBS, SimpleScreenRecorder, CleanShot, QuickTime) burn click highlights into the pixels but don't export click coordinates as a sidecar file. Without a sidecar, the skill can't auto-zoom on clicks. Two options: re-record with a tool that exports an event stream (Screenize on macOS is one), or hand-author a small `events.json` listing click timestamps and screen positions. Claude can walk you through the manual file. Without either, your MP4 is still **idle-trimmed** (long static dwells get speed-ramped or cut, just like a terminal recording's pauses) and captioned — you just don't get the click-zoom layer.

- **The video it generates looks generic, not your brand.** — The skill uses whatever profile is active in `<project>/src/brand/active.ts`. If that's `default`, you'll get default styling. Tell Claude "switch the active profile to `<your-profile>`" before kicking off, or include "use the `<profile>` profile" in your prompt.

- **Render is slow.** — Expect 30–120 seconds for a 1-minute video on a recent Mac. First render is slower because Remotion compiles the bundle.

---

## When something breaks

Three things to check, in order:

1. **Update the toolshed.** `/plugin marketplace update toolshed`. Re-run your prompt. Most "bugs" are version drift.
2. **Check the prereqs.** `which ffmpeg agg whisper-cli node` — all four should resolve. (Plus `which asciinema` if you're on the terminal-recording path.) If one's missing, the install step at the top is your fix.
3. **Show Claude the error.** Paste the actual error message and the prompt you used. The skill knows its own internals; if there's a real bug, Claude can usually narrow it down.

If after all three it's still stuck, file an issue at https://github.com/foolswithtools/toolshed with the error, your prompt, and the output of `cat ~/.claude/plugins/marketplaces/toolshed/plugins/screencast-cut/skills/screencast-cut/SKILL.md | head -5` (so I can see what version you're on).

---

## What this skill won't do

So you don't ask and get a polite "no":

- It won't record your screen for you. Use CleanShot, Screenize, asciinema, OBS, or QuickTime.
- It won't *write* your narration script for you — but if you hand it a `Script:`, it *will* generate the voiceover audio with ElevenLabs TTS (or bring your own with `Audio:`).
- It won't generate background music. Use the `music-grab` plugin (also in toolshed) for that.
- It won't render the final MP4 from inside Remotion Studio. Studio is for previewing. Claude runs the render via the CLI.
- It won't make a video from "just a topic" — it edits source material. For prompt-from-scratch motion graphics, that's the `remotion-video` skill.
