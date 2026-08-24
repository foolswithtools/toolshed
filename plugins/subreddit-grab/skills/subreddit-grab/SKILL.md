---
name: subreddit-grab
description: Use this skill when the user wants to "pull a subreddit", "download all the posts from r/X", "archive a subreddit", "grab every comment from a subreddit", "scrape r/X to JSON", "get the full history of a subreddit", or pastes a subreddit name / reddit.com/r/<sub> URL and asks for its posts and comments saved locally. Walks the arctic-shift archive (no auth, no pip deps, no live-Reddit ~1000-item cap) for full history or a date range, falls back to live Reddit's public .json for by-score top/hot grabs, and reads local Academic-Torrents per-subreddit .zst dumps for subreddits too large to walk over the API. Saves posts.jsonl, comments.jsonl, and a provenance _manifest.json under a target directory (default `./reddit/<sub>/`). Apply even if the user does not say "scrape" — any request to capture a subreddit's posts/comments locally qualifies.
version: 0.1.0
---

# Subreddit Grab

Pull a subreddit's posts and comments to local JSONL, with full-history reach the live Reddit API can't give.

## When this skill runs

The user names a subreddit (or pastes a `reddit.com/r/<sub>` URL) and wants its content saved locally — posts, comments, and metadata — typically to analyze, archive, or feed into something else. They want the *data*, not a rendered page.

If the user wants to *download media* (images/videos) from posts, that's a different job — this skill captures text + metadata (and the media URLs inside each record), not the binaries. If they want a single thread, point them at the post URL + `.json`; this skill is subreddit-scoped.

## What this skill does *not* do

- It does not download media files. Each record keeps the post's `url` / gallery data; fetching the binaries is a separate step (e.g. `yt-dlp` / `gallery-dl`).
- It does not use the official Reddit API or PRAW. As of late 2025 those require app pre-approval even for personal scripts, and they cap any listing at ~1000 items. We avoid that path entirely.
- It does not guarantee a perfect mirror. The arctic-shift archive has coverage gaps (very recent posts, some deleted content). The `_manifest.json` records this caveat.
- It does not bypass the ~1000-item cap on *live* Reddit. The by-score `top`/`hot` path is inherently capped by Reddit; full history comes from the archive or a dump, not from live listings.

## Prerequisites

| Tool | Used for | Install (macOS) |
|---|---|---|
| `python3` | the grab script (standard library only — no `pip install`) | preinstalled on macOS; else `brew install python` |
| `zstd` | decompress local `.zst` dumps — **only** needed for the `--from-dump` path | `brew install zstd` |

The default arctic-shift path and the live-Reddit `top` path need nothing beyond `python3`. Linux/Docker: `zstd` via the distro package manager.

## Configuration

Read `${CLAUDE_PLUGIN_ROOT}/skills/subreddit-grab/config.json`. Defaults:

| Field | Default | Purpose |
|---|---|---|
| `output_root` | `./reddit` | Parent dir for output. The script nests per-subreddit: `<output_root>/<sub>/`. Resolved against CWD. |
| `default_sort` | `full` | `full`/`new`/`old` walk the archive by time; `top`/`hot`/`controversial`/`rising` use live Reddit (by score, capped ~1000). |
| `default_time` | `all` | Time window for the live-Reddit score sorts (`all`/`year`/`month`/`week`/`day`). |
| `user_agent` | `toolshed-subreddit-grab/0.1 (+…)` | Sent on every request. A descriptive UA avoids live-Reddit 403s. |

User overrides per call (apply over config, do not write back):
- "save it to `<path>`" → `--output-root <path>`.
- "just 2023" / "since Jan 2024" → `--after` / `--before` (epoch, `YYYY-MM-DD`, or ISO).
- "top 500 of all time" → `--sort top --time all --limit 500`.
- "newest 200" → `--sort new --limit 200`.

## Steps

1. **Resolve the subreddit.** Extract the bare name from the user's message or a `reddit.com/r/<sub>` URL (strip any `r/` prefix). If they name several, process each in turn.

2. **Load config.** Read `${CLAUDE_PLUGIN_ROOT}/skills/subreddit-grab/config.json`. Apply this prompt's overrides over it (per-call, do not write back).

3. **Pick the path and run `grab.py`.** One script handles all three acquisition paths, cursor pagination, auto-narrowing on archive timeouts, and JSONL + manifest output in one pass.

   **Default — full history or a date range (arctic-shift, no setup):**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/subreddit-grab/scripts/grab.py" \
       "<subreddit>" \
       --output-root "<resolved_output_root>" \
       --user-agent "<user_agent>" \
       [--after "<date>"] [--before "<date>"]
   ```

   **By-score slice (live Reddit, capped ~1000):**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/subreddit-grab/scripts/grab.py" \
       "<subreddit>" --output-root "<resolved_output_root>" --user-agent "<user_agent>" \
       --sort top --time all --limit 500
   ```

   **Large subreddit from a local dump (after the user has the `.zst` files):**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/subreddit-grab/scripts/grab.py" \
       "<subreddit>" --output-root "<resolved_output_root>" \
       --from-dump "<dir with <sub>_submissions.zst / <sub>_comments.zst>" \
       [--after "<date>"] [--before "<date>"]
   ```

   The script's last line of stdout is a JSON object: `{"subreddit", "source", "posts", "comments", "posts_path", "comments_path", "manifest_path"}`. Parse it.

4. **Handle the "too large" bail (exit code 4).** If the default arctic-shift walk keeps timing out even after auto-narrowing the date window, the script stops with exit code 4 and prints the dump instructions. Relay them to the user: download `<sub>_submissions.zst` and `<sub>_comments.zst` from the Academic Torrents per-subreddit dump, `brew install zstd`, then re-run with `--from-dump <dir>`. Do not silently retry the API.

5. **Report.** Tell the user the post and comment counts, the absolute paths of `posts.jsonl` / `comments.jsonl` / `_manifest.json`, and which `source` produced them. If `source` is `arctic-shift`, mention the archive-coverage caveat from the manifest in one sentence (recent posts may be missing; it's not a perfect mirror).

## Heuristics encoded

- **arctic-shift is the default** because it's the only free path to a subreddit's *full* history — live Reddit (and PRAW) cap every listing at ~1000 items. The walk pages by advancing the `after` cursor over `created_utc` and dedupes by `id` to handle items sharing the same second.
- **`top`/`hot`/`controversial`/`rising` go to live Reddit** because arctic-shift's search sorts by time, not score. These are inherently capped near 1000 — good for "top N", not for full history.
- **Auto-narrow, then bail.** On an archive `"Query timed out"`, the walk splits the date window in half and retries; if even a sub-hour window times out, it bails to the dump path rather than looping forever.
- **Comment scope tracks the posts pulled.** A full/date-range grab also walks the full comment stream for the window. A capped grab (`--limit`, or any `top`/`hot` slice) fetches only the comments belonging to the posts it actually pulled — so comments always correspond to posts on disk.
- **Dumps decompress via the `zstd` CLI, not a pip package.** The per-subreddit `.zst` dumps use a 2 GiB window; the script shells out to `zstd -dc --long=31` so there's no `zstandard` dependency.
- **Fresh grab overwrites.** Re-running truncates `posts.jsonl` / `comments.jsonl` for that subreddit rather than appending duplicates.

## Error handling

- **`zstd` missing (dump path only).** Surface `brew install zstd` and stop. The default path never needs it.
- **`zstd` refuses the window.** If you see a "Frame requires too much memory" / window error, the file isn't a real per-subreddit dump or the local `zstd` is too old — the script surfaces zstd's stderr verbatim.
- **No dump files found.** With `--from-dump`, if no `<sub>_*submissions*.zst` / `*comments*.zst` match in the directory, the script names what it looked for and exits (code 2).
- **Archive timeouts (exit 4).** See Step 4 — relay the dump instructions, don't retry the API in a loop.
- **Live-Reddit 403 / rate limit.** The descriptive User-Agent avoids most 403s; the script honors `Retry-After` and backs off on 429. If Reddit still blocks the `top` path, suggest the arctic-shift default instead.
- **Empty result.** A subreddit with no posts in the window (or a misspelled name) yields zero records and an empty JSONL — tell the user; don't invent data.

## Notes

- `${CLAUDE_PLUGIN_ROOT}` is set by Claude Code at load time. If unset, derive paths from this SKILL.md's location.
- Why no official API: Reddit's 2023 pricing change plus the 2025 "Responsible Builder" pre-approval flow make even a personal read-only script high-friction, and it still can't exceed ~1000 items per listing. arctic-shift is free, auth-free, and uncapped — at the cost of being an archive (coverage gaps), which the manifest discloses.
- The `_manifest.json` is small and load-bearing — it records the source, range, counts, and fetch date so a JSONL dump is self-describing later. Keep it alongside the data.
- JSONL records are the archive's/Reddit's raw objects, preserved as-is, so all metadata (score, author, flair, timestamps, gallery/media URLs) survives for downstream processing.
