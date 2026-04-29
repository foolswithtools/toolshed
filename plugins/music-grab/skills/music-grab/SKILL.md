---
name: music-grab
description: Use this skill when the user wants to "grab a music track from this URL", "download the audio from this YouTube video", "save just the audio of this SoundCloud track", "pull this song into my project", or pastes a YouTube/SoundCloud/direct-MP3 URL and asks for the audio (typically to use as background music in a Remotion video). Downloads audio via yt-dlp, saves it under a target directory (default `./public/music/`), and appends a `CREDITS.md` entry with source URL, license claim from the page description, and any attribution requirements the page declared. Warns when the source page does not contain explicit "free to use" / Creative Commons language but still proceeds — the user is responsible for license compliance.
version: 0.1.0
---

# Music Grab

Pull just the audio from a URL and log its source for credits.

## When this skill runs

The user has a URL (YouTube, SoundCloud, Pixabay, direct MP3, or anything else `yt-dlp` can resolve) and wants the audio saved locally — typically as a background track for a Remotion video. They do not want the video file itself, just the audio plus enough provenance to credit it later.

If the user is asking to *search* for music ("find me a synthwave track ~120 BPM"), that's a different (search-and-pick) plugin. This skill is URL-driven.

## What this skill does *not* do

- It does not search for music. Bring a URL.
- It does not generate music. No TTS, no AI synthesis.
- It does not normalize loudness or convert to a target format beyond extracting MP3. If the user wants `loudnorm` applied, do it as a separate `ffmpeg` step after grab.
- It does not bypass paywalls or DRM. If `yt-dlp` can't fetch the audio, surface its error.

## Prerequisites

| Tool | Used for | Install (macOS) |
|---|---|---|
| `yt-dlp` | resolve URL + extract audio | `brew install yt-dlp` |
| `ffmpeg` | audio extraction backend for yt-dlp | `brew install ffmpeg` |

Linux/Docker: `yt-dlp` via `pipx install yt-dlp` (or distro package); `ffmpeg` via the distro package manager.

## Configuration

Read `${CLAUDE_PLUGIN_ROOT}/skills/music-grab/config.json`. Defaults:

| Field | Default | Purpose |
|---|---|---|
| `output_root` | `./public/music` | Where the audio file lands. Resolved against CWD. |
| `audio_format` | `mp3` | Output extension. yt-dlp re-encodes via ffmpeg. |
| `audio_quality` | `0` | yt-dlp `--audio-quality` (0 = best for VBR codecs). |
| `credits_file` | `CREDITS.md` | Filename appended to inside `output_root`. |
| `license_required_phrases` | `["creative commons", "cc-by", "cc by", "public domain", "no copyright", "royalty free", "royalty-free", "free for use", "free to use", "free for commercial use", "pixabay license"]` | Page text searched for evidence of a permissive license. Match is case-insensitive. |

User overrides per call:
- "save it to `<path>`" → `output_root=<path>` for this call only.
- "save as `<filename>`" → use the given filename instead of the default `<artist>-<title>` slug.
- "grab the WAV" → `audio_format=wav`.

## Steps

1. **Resolve the URL.** Extract from the user's message. If multiple URLs, process each in turn — but ask the user up-front whether they all go to the same `output_root` or split.

2. **Load config.** Read `${CLAUDE_PLUGIN_ROOT}/skills/music-grab/config.json`. Apply user overrides from this prompt over the loaded config (per-call, do not write back).

3. **Run `grab.py`** for each URL. The script handles metadata probing, license-phrase matching, slug generation, collision avoidance, audio extraction, and credits-stanza append in one pass. Build the phrase list from `license_required_phrases` in config:

   ```bash
   PHRASES_ARGS=$(printf -- '--phrase %s ' "<each phrase from config>")
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/music-grab/scripts/grab.py" \
       "<URL>" \
       --output-dir "<resolved_output_root>" \
       --audio-format "<audio_format>" \
       --audio-quality "<audio_quality>" \
       --credits-file "<credits_file>" \
       $PHRASES_ARGS
   ```

   The script's last line of stdout is a JSON object: `{"audio_path", "credits_path", "license_matched", "license_phrase", "attribution_text", "uploader", "title"}`. Parse it.

4. **Surface the warning if license_matched is false.** Tell the user, in one short paragraph:
   > "No explicit free-use language found in the source page description. The track was downloaded and credited, but you should verify the license yourself before publishing. The credits file captured the first 200 characters of the page description verbatim — that's what to look at."

   If `license_matched` is true, just confirm the matched phrase to the user. Don't lecture.

5. **Surface the attribution requirement if any.** If `attribution_text` is non-empty, repeat it back to the user verbatim — they'll need that text in their video credits.

6. **Report.** Tell the user the absolute paths of the audio file and the credits file. Do not auto-open anything.

## Heuristics encoded

- One audio file per URL. Playlists are flattened (`--no-playlist`). If the user wants the whole playlist, they re-invoke per-track.
- License-phrase matching is generous (substring, case-insensitive). False positives are possible — that's why the credits file captures the *context* of the match for later review, not just the boolean.
- Default to `mp3` because Remotion `<Audio>` components handle it cleanly and file sizes stay reasonable. WAV is supported for users who want lossless.
- Re-grabbing the same URL produces a `<slug>-2.<ext>` file rather than overwriting. Idempotent in spirit, traceable in practice.

## Error handling

- **`yt-dlp` / `ffmpeg` missing.** Surface the install command for the platform and stop.
- **URL unresolvable.** Surface yt-dlp's error verbatim. Common cases: deleted video, geo-restriction, sign-in-required, private. Don't guess at workarounds.
- **Source has no audio stream.** yt-dlp will report it; pass through to the user.
- **Output file collision past `-9`.** Stop and tell the user something is off — likely the same URL has been grabbed many times and the credits file probably has the answer they want already.
- **Metadata probe returned empty fields.** Some sources don't expose `uploader` or `title`. Fall back to the URL's last path segment for the slug, and write `unknown` into the credits stanza for the missing field. Do not invent values.

## Notes

- `${CLAUDE_PLUGIN_ROOT}` is set by Claude Code at load time. If unset, derive paths from this SKILL.md's location.
- Why the warn-and-proceed policy: artists routinely post royalty-free tracks on YouTube and SoundCloud without a structured license tag, just a plain-English "free to use" line in the description. Refusing to download anything without a structured tag would block 80% of legitimate use. The credits file is the receipt.
- The credits file stays in version control with the project. Don't `.gitignore` `<output_root>` — the audio files might be too large for git, but the `CREDITS.md` is small and load-bearing.
- If the user wants to redact / re-license / replace a track later, the credits stanza tells them which file to swap and what to look for in a replacement.
