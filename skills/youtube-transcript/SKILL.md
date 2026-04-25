---
name: youtube-transcript
description: Use this skill whenever the user asks for a "youtube transcript", to "download subtitles from youtube", "get the transcript of <url>", "grab captions from youtube", "save subtitles for this video", or pastes a youtube.com / youtu.be URL and asks for its text. Downloads the .vtt subtitle file via yt-dlp and produces a cleaned .txt next to it. Apply even if the user does not say the word "transcript" explicitly — any request involving extracting the spoken content of a YouTube video qualifies.
version: 0.1.0
---

# YouTube Transcript Downloader

Download a YouTube video's subtitles and produce a clean text transcript.

## When this skill runs

The user has supplied (or implied) a YouTube URL and wants the spoken text saved locally.

## Steps

1. **Resolve the URL.** Extract the YouTube URL from the user's message. If multiple URLs, process each in turn.

2. **Load config.** Read `${CLAUDE_PLUGIN_ROOT}/skills/youtube-transcript/config.json` if present. Defaults if absent:
   - `output_root`: `./transcripts`
   - `subfolder_template`: `{channel}`
   - `language`: `en`

   If the user said "save to <path>" or "put it in <path>", that overrides `output_root` for this call only.

3. **Fetch metadata.** Capture stdout from:
   ```bash
   yt-dlp --print "%(channel)s|||%(uploader)s|||%(id)s|||%(title)s|||%(upload_date)s" --skip-download "<URL>"
   ```
   Split on `|||` to get `channel`, `uploader`, `id`, `title`, `upload_date` (YYYYMMDD; year is first 4 chars).

4. **Compute output dir.** Sanitize `channel` and `uploader` by replacing any of `/ \ : * ? " < > |` and control chars with `_`, then collapsing whitespace. Substitute `{channel}`, `{uploader}`, `{year}` into `subfolder_template`. If the template is `.`, use `output_root` directly.

   Final dir = `<resolved_output_root>/<rendered_subfolder>`. `mkdir -p` it.

5. **Download subs.**
   ```bash
   yt-dlp \
     --skip-download \
     --write-subs \
     --write-auto-subs \
     --sub-langs "<language>" \
     --sub-format vtt \
     --convert-subs vtt \
     -o "<dir>/%(title)s [%(id)s].%(ext)s" \
     "<URL>"
   ```
   yt-dlp writes `<dir>/<title> [<id>].<lang>.vtt`. If missing afterward, retry once with `--sub-langs "<language>.*"` (e.g. `en.*`) to catch variants like `en-orig`. If still missing, report no subs available and stop.

6. **Generate clean .txt.**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/youtube-transcript/scripts/vtt_to_text.py" "<vtt_path>"
   ```
   The script writes `<same-stem>.txt` next to the .vtt. Keep the .vtt — the user gets both files.

7. **Report.** Tell the user the channel, title, and absolute paths of both files.

## Error handling

- `yt-dlp` not on PATH: tell the user to install it (`brew install yt-dlp`).
- Private/age-gated/region-locked: surface yt-dlp's stderr verbatim.
- No subs in requested language even after the wildcard retry: report failure cleanly.

## Notes

- `${CLAUDE_PLUGIN_ROOT}` is set by Claude Code at load time. If unset, derive the path from this SKILL.md's location.
- The .vtt is preserved for re-processing or tools that want timed cues.
