# youtube-transcript

A Claude Code plugin that downloads YouTube video transcripts. When you ask Claude to grab a transcript (or paste a YouTube URL), it shells out to `yt-dlp` and saves two files per video:

- `<title> [<id>].en.vtt` — the original WebVTT subtitle file
- `<title> [<id>].en.txt` — a cleaned plain-text transcript with timestamps, cue ids, inline tags, and rolling auto-subtitle duplicates stripped

## Requirements

- `yt-dlp` on PATH (`brew install yt-dlp`)
- `python3` on PATH (stdlib only)

## Install

From a Git remote (any machine):

```
/plugin marketplace add https://github.com/<user>/youtube-transcript.git
/plugin install youtube-transcript
```

Local iteration without GitHub:

```
/plugin marketplace add /path/to/this/repo
/plugin install youtube-transcript
```

A repo with `.claude-plugin/plugin.json` at its root is treated as a one-plugin marketplace automatically.

## Usage

In Claude Code, just ask:

```
please grab the transcript for https://www.youtube.com/watch?v=VIDEO_ID
```

By default, files land in `./transcripts/<channel>/` relative to your current working directory. Override per-call with phrases like `save to /tmp/yt-test`.

## Configuration

Edit `skills/youtube-transcript/config.json`:

| Field                | Default          | Notes                                                                                                                |
|----------------------|------------------|----------------------------------------------------------------------------------------------------------------------|
| `output_root`        | `./transcripts`  | Relative paths resolve from CWD when the skill runs; absolute paths honored as-is.                                   |
| `subfolder_template` | `{channel}`      | Tokens: `{channel}`, `{uploader}`, `{year}`. Combine like `{channel}/{year}`. Use `.` for a flat layout.             |
| `language`           | `en`             | yt-dlp `--sub-langs` value. Use `en.*` to match auto-generated variants like `en-orig`, `en-US`.                     |

The skill also auto-retries with `<language>.*` if the requested exact language isn't available.

## Layout

```
.
├── .claude-plugin/plugin.json
├── README.md
├── .gitignore
└── skills/
    └── youtube-transcript/
        ├── SKILL.md
        ├── config.json
        └── scripts/
            └── vtt_to_text.py
```
