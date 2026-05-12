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
- **Terminal recording (any OS):** `asciinema rec demo.cast`. Stop with `exit` or Ctrl-D.

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
| **Narration** | Recommended | Either an audio file (`Audio: ~/path/voice.m4a`) *or* a script (`Script: ~/path/script.txt`). With a script, the skill generates the audio via ElevenLabs and loudnorms it before captioning. Without either, you get a silent video. Pass both and `Audio:` wins (the recorded file is hand-tuned). |
| **Click-event data** | Optional, MP4 only | Only needed if you want auto-zoom on clicks for a screen recording. CleanShot doesn't export this; Screenize does. Without click data, your MP4 plays full-frame (with idle stretches still auto-trimmed) and captions over it — still fine. |

That's the whole input surface.

### One-time setup for the `Script:` path

If you'll pass `Script:` instead of `Audio:`, the skill needs an ElevenLabs API key. Three ways to provide it; the skill checks in order:

1. `ELEVENLABS_API_TOKEN` in your shell environment.
2. `ELEVENLABS_API_KEY` (common alternate name).
3. A line `ELEVENLABS_API_TOKEN=...` in `~/.config/screencast-cut/secrets.env` (plugin-scoped fallback so you don't have to touch `.envrc`).

The skill never echoes the token. If it can't find one, it stops with an actionable message and tells you which paths it checked.

**No default voice.** The skill picks a voice from your prompt (`Voice: Bill`) or from your active profile's `tts.voice`. If neither is set, it stops — better than picking a voice for you. Run `python3 ~/.claude/plugins/marketplaces/toolshed/plugins/screencast-cut/skills/screencast-cut/scripts/list_voices.py` to see the voices your API key has access to.

---

## The actual usage

Open Claude Code in your Remotion project directory and paste a prompt like one of these:

### Tutorial from a terminal recording

> "Use the screencast-cut skill. Source: `~/Recordings/demo.cast`. Audio: `~/Recordings/voiceover.m4a`. Make a tutorial showing how to use jq."

### Tutorial from a terminal recording, narration generated from a script

> "Use the screencast-cut skill. Source: `~/Recordings/demo.cast`. Script: `~/Recordings/jq-narration.md`. Voice: Bill. Make a 45-second tutorial."

(`Voice:` is optional if your active profile already declares a `tts.voice`.)

### Tutorial from a screen recording

> "Use the screencast-cut skill. Source: `~/Recordings/onboarding.mp4`. Audio: `~/Recordings/narration.m4a`. Cut this into a 60-second product walkthrough."

### Vertical short for TikTok / Reels / Shorts

> "Use the screencast-cut skill. Source: `~/Recordings/quick-tip.mp4`. Audio: `~/Recordings/voice.m4a`. Make this a 9:16 short for TikTok."

### Part of a series

> "Use the screencast-cut skill. Source: `~/Recordings/part2.cast`. Audio: `~/Recordings/voice.m4a`. This is part 2 of 5 in the 'Build a CLI in Go' series, chapter title 'Adding subcommands'."

(The "part 2 of 5" phrasing is what triggers chapter-aware framing — recap-and-continue intro, transitional outro pointing at part 3. Use "part 1" or "first lesson" or "the conclusion" / "final chapter" to signal first/last.)

---

## What you'll see, in order

The skill runs in seven phases. You don't drive them — Claude does — but knowing what's normal helps you tell *signal* from *something's wrong*.

| Phase | What's happening | What you should see |
|---|---|---|
| 1 | Locating your Remotion project | "Found project at `~/videos-studio`. Slug: `demo-tutorial`." |
| 2 | Reading your brand profile, classifying input, picking a playbook | A line naming your active profile and the detected genre (`tutorial` or `shortform`). |
| 3 | Planning beats | A numbered beat list with durations, plus a small "Decisions" table showing which value came from config vs. playbook vs. your prompt. For terminal casts, any fumbles (backspace runs, Ctrl-U / Ctrl-W) are listed as cut candidates you can approve or reject one-by-one. **Pause here — say "approve" or push back.** |
| 4 | Building scene files + transcribing audio | Whisper runs locally (no network). Takes 10–60s depending on audio length. |
| 5 | Studio preview | Claude opens `localhost:3000` in your browser. **Important: don't render from inside Studio.** Hit spacebar to play, scrub the timeline, comment on what's wrong. |
| 6 | Render | One MP4 lands at `videos/<slug>/out.mp4`. Claude tells you the absolute path. |
| 7 | Capture-learning prompt | One question with three options. Pick "Save as a rule" if it's a pattern, "Just a note" if it's video-specific, or "Skip." |

Phase 3 is the only place you really need to push back. Once you approve the plan, the rest runs.

---

## Things that might trip you up

- **The Studio page loads and you think "now what?"** — Spacebar plays. The left sidebar lists your video. Scrub the timeline at the bottom to inspect frames. Edit a file under `videos/<slug>/scenes/` and Studio hot-reloads. To render the final MP4, leave Studio open and tell Claude "render it" — Claude runs the render command. You don't render from Studio.

- **"It can't find my recording."** — Use absolute paths in your prompt (`~/Recordings/demo.mp4`), not relative ones, unless you're already `cd`-ed into the directory holding the file.

- **Your audio is `.m4a` or `.mp3` and the transcription seems to fail silently.** — Should be auto-handled in screencast-cut 0.4.0+. If you're seeing it, run `/plugin marketplace update toolshed` — you're behind.

- **Fumble detection misses something / flags something that wasn't really a fumble.** — It's a heuristic and false positives are expected (you'd rather see them in Phase 3 and skip than have the skill silently drop something). If your active profile is "trust the heuristic, just cut it," set `fumble_auto_cut: true` in your profile's `editing` block. If it's catching too few, lower `fumble_min_backspaces` (default 3 — 2 will pick up shorter typos).

- **Video idle-trim cut the wrong stretches (or didn't cut anything).** — Idle detection for screen recordings uses ffmpeg's `freezedetect`. The two knobs are `video_idle_pixel_diff_threshold` (default 2.0 — lower = more sensitive, will trim quieter motion) and `video_idle_edge_mask_px` (default 40 — crops the right edge so a ticking menubar clock doesn't defeat detection). If a macOS recording's clock is wider than 40px (some larger displays), raise the mask to 80. If the whole video is incorrectly seen as static, you might have wallpaper animation or compression artefacts — raise the threshold to 5.0 and re-run.

- **Screen recording, no auto-zoom on clicks.** — Most screen recorders (OBS, SimpleScreenRecorder, CleanShot, QuickTime) burn click highlights into the pixels but don't export click coordinates as a sidecar file. Without a sidecar, the skill can't auto-zoom on clicks. Two options: re-record with a tool that exports an event stream (Screenize on macOS is one), or hand-author a small `events.json` listing click timestamps and screen positions. Claude can walk you through the manual file. Without either, your MP4 still plays full-frame with captions over it — you just don't get the zoom layer.

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
- It won't write your narration script. Bring your own words. (It *will* turn a script into audio via ElevenLabs if you pass `Script:` and have an API key set.)
- It won't generate background music. Use the `music-grab` plugin (also in toolshed) for that.
- It won't render the final MP4 from inside Remotion Studio. Studio is for previewing. Claude runs the render via the CLI.
- It won't make a video from "just a topic" — it edits source material. For prompt-from-scratch motion graphics, that's the `remotion-video` skill.
