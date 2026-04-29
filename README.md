# toolshed

A Claude Code plugin marketplace. A grab bag of small, useful tools — each plugin does one job and gets out of the way.

Part of [foolswithtools](https://github.com/foolswithtools).

## Install the marketplace

```
/plugin marketplace add https://github.com/foolswithtools/toolshed.git
```

Then install whichever plugins you want:

```
/plugin install youtube-transcript@toolshed
```

Local iteration without GitHub:

```
/plugin marketplace add /path/to/toolshed
/plugin install youtube-transcript@toolshed
```

To update later:

```
/plugin marketplace update toolshed
```

> **Run `/plugin marketplace update toolshed` before reporting any bug.** Plugins do not auto-update — once installed, your local copy stays pinned to whatever commit was current at install time. If a skill is doing something that doesn't match what you expect, the most likely cause is that you're running an older version. Update first; then if it still misbehaves, file the issue.

## Plugins

### youtube-transcript

Downloads a YouTube video's transcripts via `yt-dlp`. Saves two files per video:

- `<title> [<id>].en.vtt` — the original WebVTT subtitle file
- `<title> [<id>].en.txt` — a cleaned plain-text transcript (timestamps, cue ids, and inline tags stripped; rolling auto-subtitle duplicates collapsed)

**Requirements:** `yt-dlp` and `python3` on PATH (`brew install yt-dlp`).

**Use it:**

```
please grab the transcript for https://www.youtube.com/watch?v=VIDEO_ID
```

By default, files land in `./transcripts/<channel>/` relative to your current working directory. Override per-call with phrases like `save to /tmp/yt-test`.

**Configure** by editing `plugins/youtube-transcript/skills/youtube-transcript/config.json`:

| Field                | Default          | Notes                                                                                                                |
|----------------------|------------------|----------------------------------------------------------------------------------------------------------------------|
| `output_root`        | `./transcripts`  | Relative paths resolve from CWD when the skill runs; absolute paths honored as-is.                                   |
| `subfolder_template` | `{channel}`      | Tokens: `{channel}`, `{uploader}`, `{year}`. Combine like `{channel}/{year}`. Use `.` for a flat layout.             |
| `language`           | `en`             | yt-dlp `--sub-langs` value. Use `en.*` to match auto-generated variants like `en-orig`, `en-US`.                     |

The skill auto-retries with `<language>.*` if the requested exact language isn't available.

### remotion-video

Prompt-driven motion-graphics video creation with [Remotion](https://www.remotion.dev/). Walks an iteration loop: plan the video beat-by-beat → build scenes (with screenshot verification after each) → preview in Remotion Studio → revise from your comments → render to MP4. Maintains a persistent brand style guide so successive videos in the same project stay visually consistent.

**Requirements:** `node` 18+ (`brew install node`). Remotion's renderer downloads its own Chromium on first render.

**Use it:**

```
make me a 15-second launch video introducing the foolswithtools org with a glowing teal accent
```

```
build a 9:16 vertical short explaining what a Claude Code skill is
```

The first invocation in a folder scaffolds a long-lived Remotion project under `videos-studio/` (configurable). Subsequent videos land as subfolders inside it (`videos-studio/videos/<slug>/`) and reuse the established style.

**Configure** by editing `plugins/remotion-video/skills/remotion-video/config.json`:

| Field                      | Default            | Notes                                                                                            |
|----------------------------|--------------------|--------------------------------------------------------------------------------------------------|
| `output_root`              | `./videos-studio`  | Where the long-lived Remotion project lives. Resolved against CWD.                               |
| `fps`                      | `30`               | Frames per second for new compositions.                                                          |
| `width` / `height`         | `1920` / `1080`    | Default composition dimensions. Override per-call ("9:16 vertical", "1:1 square", "4K").         |
| `install_official_skills`  | `true`             | Run `npx remotion skills add` on a fresh project so Remotion's own agent skills land in `.claude/skills/`. |
| `auto_start_studio`        | `true`             | Auto-launch `npx remotion studio` for live preview during iteration.                             |
| `screenshot_scale`         | `0.25`             | `--scale` for `npx remotion still` PNG verification frames.                                       |

The persistent brand style guide lives in `<project>/src/brand/profiles/<name>/` and is selected by `<project>/src/brand/active.ts`. The skill seeds the `default` profile on first run, plus any additional profile you ask for (e.g. `foolswithtools-brand`, the project's own pop-art / punk-zine maker-blog brand pulled from [`foolswith.tools`](https://foolswith.tools/)). Switch profiles per video by saying "use the `<name>` profile". Build your own profile by copying any of the bundled ones and customizing.

## Layout

```
.
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   ├── youtube-transcript/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── skills/
│   │       └── youtube-transcript/
│   │           ├── SKILL.md
│   │           ├── config.json
│   │           └── scripts/
│   │               └── vtt_to_text.py
│   └── remotion-video/
│       ├── .claude-plugin/
│       │   └── plugin.json
│       └── skills/
│           └── remotion-video/
│               ├── SKILL.md
│               ├── config.json
│               └── templates/
│                   ├── default/
│                   │   ├── style-guide.ts
│                   │   └── BRAND.md
│                   └── foolswithtools-brand/
│                       ├── style-guide.ts
│                       ├── BRAND.md
│                       └── components/  (8 brand primitives)
├── README.md
└── .gitignore
```

## Adding a new plugin

1. Create `plugins/<name>/.claude-plugin/plugin.json` with at minimum `name`, `version`, `description`.
2. Add whatever components the plugin needs under `plugins/<name>/` (skills, commands, agents, hooks, mcpServers).
3. Add an entry to the `plugins` array in `.claude-plugin/marketplace.json` with `name`, `source: "./plugins/<name>"`, and a one-line `description`.
4. Bump the plugin's `version` whenever you want users on auto-update to pick up your changes.
