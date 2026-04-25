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

## Layout

```
.
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   └── youtube-transcript/
│       ├── .claude-plugin/
│       │   └── plugin.json
│       └── skills/
│           └── youtube-transcript/
│               ├── SKILL.md
│               ├── config.json
│               └── scripts/
│                   └── vtt_to_text.py
├── README.md
└── .gitignore
```

## Adding a new plugin

1. Create `plugins/<name>/.claude-plugin/plugin.json` with at minimum `name`, `version`, `description`.
2. Add whatever components the plugin needs under `plugins/<name>/` (skills, commands, agents, hooks, mcpServers).
3. Add an entry to the `plugins` array in `.claude-plugin/marketplace.json` with `name`, `source: "./plugins/<name>"`, and a one-line `description`.
4. Bump the plugin's `version` whenever you want users on auto-update to pick up your changes.
