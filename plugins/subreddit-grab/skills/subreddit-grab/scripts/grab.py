#!/usr/bin/env python3
"""Grab a subreddit's posts and comments as JSONL.

Three acquisition paths, all emitting identical JSONL so downstream is uniform:

  * api  (default) — walk the arctic-shift archive (https://arctic-shift.photon-reddit.com).
                     No auth, no pip deps, no ~1000-item live-Reddit cap. Full history
                     or a --after/--before date range. Cursor pagination over created_utc;
                     on "Query timed out" it auto-narrows the date window, and if even a
                     tiny window keeps timing out it bails with torrent instructions.
  * top  (--sort top|hot|controversial|rising) — fetch by score/algorithm from live
                     Reddit's public .json endpoints (the only way to sort by score),
                     capped at Reddit's ~1000 limit. Comments are pulled per fetched post.
  * dump (--from-dump DIR) — read local Academic-Torrents per-subreddit .zst files
                     (<sub>_submissions.zst / <sub>_comments.zst). Decompresses by
                     shelling out to the `zstd` CLI with --long=31 (the 2 GiB window the
                     dumps need) — no `zstandard` pip dependency.

Writes <output_root>/<subreddit>/posts.jsonl, comments.jsonl, and _manifest.json
(provenance: source, range, counts, fetch date, archive-coverage caveat). The last
line of stdout is a JSON summary the skill parses.

Stdlib only: urllib, json, subprocess (zstd), argparse, datetime, time, pathlib.

Usage:
    grab.py <subreddit> \\
        --output-root ./reddit \\
        [--after 2020-01-01] [--before 2024-01-01] \\
        [--sort new|old|top|hot|controversial|rising] \\
        [--time all|year|month|week|day] \\
        [--limit N] \\
        [--from-dump <dir>] \\
        [--user-agent "..."]
"""

import argparse
import datetime as dt
import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ARCTIC_BASE = "https://arctic-shift.photon-reddit.com"
REDDIT_BASE = "https://www.reddit.com"
DEFAULT_UA = "toolshed-subreddit-grab/0.1 (+https://github.com/foolswithtools/toolshed)"
REQUEST_DELAY = 0.5          # polite floor between requests (~2 req/s)
MIN_WINDOW = 3600            # don't auto-narrow below 1 hour before bailing to a dump
REDDIT_EPOCH = 1119000000    # ~2005-06-17, just before Reddit launched; valid lower bound
                             # (the archive rejects after=0 as an invalid date)
ARCHIVE_NOTE = (
    "Source is the arctic-shift archive, which rebuilds Reddit history from bulk "
    "ingestion. Coverage has gaps (very recent posts may be missing; deleted content "
    "may persist or be absent). It is the most complete free source but is not a "
    "perfect mirror of live Reddit."
)

_last_request = [0.0]


class Timeout(Exception):
    """The archive reported a query timeout (or a 5xx) for this request."""


class DumpNeeded(Exception):
    """The subreddit is too large to walk via the API; the user must use --from-dump."""


# --------------------------------------------------------------------------- #
# HTTP                                                                         #
# --------------------------------------------------------------------------- #
def _throttle() -> None:
    elapsed = time.monotonic() - _last_request[0]
    if elapsed < REQUEST_DELAY:
        time.sleep(REQUEST_DELAY - elapsed)
    _last_request[0] = time.monotonic()


def http_get_json(url: str, user_agent: str, attempts: int = 4) -> tuple:
    """GET a URL and parse JSON. Returns (parsed, headers).

    Retries on 429 (honoring Retry-After / X-RateLimit-Reset) and transient
    network errors. Raises Timeout on 5xx so the caller can narrow its window.
    """
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    last_err = None
    for attempt in range(attempts):
        _throttle()
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                raw = resp.read()
                headers = resp.headers
            parsed = json.loads(raw.decode("utf-8"))
            if isinstance(parsed, dict) and "error" in parsed:
                msg = str(parsed.get("error", ""))
                if "tim" in msg.lower():  # "timed out" / "timeout"
                    raise Timeout(msg)
                raise RuntimeError(f"Archive error: {msg}")
            # Back off proactively if we're near the rate limit.
            remaining = headers.get("X-RateLimit-Remaining")
            if remaining is not None:
                try:
                    if float(remaining) <= 1:
                        reset = float(headers.get("X-RateLimit-Reset", "2"))
                        time.sleep(min(max(reset, 1.0), 30.0))
                except ValueError:
                    pass
            return parsed, headers
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code == 429:
                retry_after = e.headers.get("Retry-After")
                wait = float(retry_after) if retry_after and retry_after.isdigit() else 5.0
                time.sleep(min(wait, 30.0))
                continue
            if 500 <= e.code < 600:
                raise Timeout(f"HTTP {e.code}") from e
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            time.sleep(2.0 * (attempt + 1))
            continue
    raise RuntimeError(f"Request failed after {attempts} attempts: {url} ({last_err})")


def _records(parsed) -> list:
    """Normalize an arctic-shift response to a list of records."""
    if isinstance(parsed, dict):
        data = parsed.get("data", parsed.get("results", []))
        return data if isinstance(data, list) else []
    if isinstance(parsed, list):
        return parsed
    return []


def _created(rec: dict) -> int:
    try:
        return int(float(rec.get("created_utc", 0)))
    except (TypeError, ValueError):
        return 0


# --------------------------------------------------------------------------- #
# arctic-shift cursor walk (the primary path)                                  #
# --------------------------------------------------------------------------- #
def arctic_url(kind: str, params: dict) -> str:
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    return f"{ARCTIC_BASE}/api/{kind}/search?{query}"


def walk(kind, base_params, after, before, ua, seen, sink,
         limit=None, counter=None, newest_first=False):
    """Cursor-paginate arctic-shift over [after, before), writing new records to sink.

    kind: "posts" or "comments". base_params carries subreddit OR link_id.
    newest_first=True walks newest→oldest (sort=desc, advancing `before` down) so a
    `limit` yields the most recent N; False walks oldest→newest (sort=asc, advancing
    `after` up) for stable full-history coverage.
    On Timeout, recursively split the window; if a sub-hour window still times out,
    raise DumpNeeded. Dedupes by id (handles same-second collisions). counter is a
    one-element list used only for limit enforcement.
    """
    lo, hi = after, before
    while True:
        if limit is not None and counter is not None and counter[0] >= limit:
            return
        params = dict(base_params)
        params.update({
            "after": lo, "before": hi,
            "sort": "desc" if newest_first else "asc",
            "limit": "auto",
        })
        try:
            parsed, _ = http_get_json(arctic_url(kind, params), ua)
        except Timeout:
            span = hi - lo
            if span <= MIN_WINDOW:
                raise DumpNeeded(
                    f"arctic-shift keeps timing out on r/{base_params.get('subreddit', '?')} "
                    f"even for a {span}s window — this subreddit is too large to walk via "
                    "the API."
                )
            mid = lo + span // 2
            # Recurse over both halves, doing the side the cursor faces first so a
            # `limit` still fills from the correct end.
            halves = [(mid, hi), (lo, mid)] if newest_first else [(lo, mid), (mid, hi)]
            for h_lo, h_hi in halves:
                walk(kind, base_params, h_lo, h_hi, ua, seen, sink,
                     limit, counter, newest_first)
            return
        page = _records(parsed)
        if not page:
            return
        c_min = hi
        c_max = lo
        for rec in page:
            rid = rec.get("id")
            c = _created(rec)
            c_min = min(c_min, c)
            c_max = max(c_max, c)
            if rid in seen:
                continue
            seen.add(rid)
            sink(rec)
            if counter is not None:
                counter[0] += 1
                if limit is not None and counter[0] >= limit:
                    return
        if newest_first:
            if c_min >= hi:  # no downward progress -> done
                return
            hi = c_min
        else:
            if c_max <= lo:  # no forward progress -> done
                return
            lo = c_max


# --------------------------------------------------------------------------- #
# live Reddit .json (the by-score "top" path)                                  #
# --------------------------------------------------------------------------- #
def reddit_listing(sub, sort, time_filter, limit, ua):
    """Page live Reddit's public .json listing. Returns up to `limit` posts
    (Reddit hard-caps this near 1000 regardless)."""
    posts = []
    after = None
    cap = min(limit, 1000) if limit else 1000
    while len(posts) < cap:
        params = {"limit": min(100, cap - len(posts)), "raw_json": 1, "t": time_filter}
        if after:
            params["after"] = after
        url = f"{REDDIT_BASE}/r/{sub}/{sort}.json?{urllib.parse.urlencode(params)}"
        parsed, _ = http_get_json(url, ua)
        data = parsed.get("data", {}) if isinstance(parsed, dict) else {}
        children = data.get("children", [])
        if not children:
            break
        for ch in children:
            posts.append(ch.get("data", {}))
        after = data.get("after")
        if not after:
            break
    return posts[:cap]


def comments_for_post(post_id, ua, seen, sink):
    """Pull all comments for one post id from arctic-shift (used by capped/top grabs)."""
    count = [0]
    now = int(time.time()) + 86400
    walk("comments", {"link_id": post_id}, REDDIT_EPOCH, now, ua, seen, sink, counter=count)
    return count[0]


# --------------------------------------------------------------------------- #
# dump path (local .zst via the zstd CLI)                                      #
# --------------------------------------------------------------------------- #
def find_dump_file(directory: Path, sub: str, kind: str) -> Path:
    """kind in {"submissions", "comments"}. Case-insensitive match within dir."""
    sub_l = sub.lower()
    candidates = [
        p for p in directory.glob("*.zst")
        if sub_l in p.name.lower() and kind in p.name.lower()
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda p: len(p.name))[0]


def stream_dump(path: Path, sub: str, after: int, before: int, sink) -> int:
    """Decompress a per-subreddit .zst NDJSON file via the zstd CLI and emit
    matching records. --long=31 is mandatory: the dumps use a 2 GiB window."""
    cmd = ["zstd", "-dc", "--long=31", str(path)]
    written = 0
    sub_l = sub.lower()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(rec.get("subreddit", "")).lower() != sub_l:
                continue
            c = _created(rec)
            if after and c < after:
                continue
            if before and c >= before:
                continue
            sink(rec)
            written += 1
    finally:
        proc.stdout.close()
        ret = proc.wait()
    if ret != 0:
        err = proc.stderr.read()
        sys.stderr.write(err)
        if "Frame requires too much memory" in err or "window" in err.lower():
            sys.stderr.write(
                "\nzstd refused the large window. Ensure you passed a real per-subreddit "
                "dump and that your zstd build supports --long=31 (brew install zstd).\n"
            )
        raise RuntimeError(f"zstd exited with code {ret} on {path}")
    return written


# --------------------------------------------------------------------------- #
# date parsing                                                                 #
# --------------------------------------------------------------------------- #
def parse_date(value):
    """Accept epoch seconds, YYYY-MM-DD, or YYYY-MM-DDTHH:MM:SS. Returns epoch int."""
    if value is None:
        return None
    value = str(value).strip()
    if value.isdigit():
        return int(value)
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return int(dt.datetime.strptime(value, fmt).replace(tzinfo=dt.timezone.utc).timestamp())
        except ValueError:
            continue
    raise SystemExit(f"Could not parse date: {value!r} (use epoch, YYYY-MM-DD, or ISO).")


# --------------------------------------------------------------------------- #
# main                                                                         #
# --------------------------------------------------------------------------- #
def main() -> int:
    p = argparse.ArgumentParser(description="Grab a subreddit's posts and comments as JSONL.")
    p.add_argument("subreddit", help="Subreddit name (no r/ prefix).")
    p.add_argument("--output-root", default="./reddit")
    p.add_argument("--after", default=None, help="Epoch / YYYY-MM-DD / ISO. Inclusive lower bound.")
    p.add_argument("--before", default=None, help="Epoch / YYYY-MM-DD / ISO. Exclusive upper bound.")
    p.add_argument(
        "--sort",
        default="full",
        choices=["full", "new", "old", "top", "hot", "controversial", "rising"],
        help="full/new/old walk the archive by time; top/hot/controversial/rising use live Reddit.",
    )
    p.add_argument("--time", default="all", choices=["all", "year", "month", "week", "day"],
                   help="Time window for live-Reddit score sorts.")
    p.add_argument("--limit", type=int, default=None, help="Cap the number of posts fetched.")
    p.add_argument("--from-dump", default=None, metavar="DIR",
                   help="Read local <sub>_submissions.zst / <sub>_comments.zst from this dir.")
    p.add_argument("--user-agent", default=DEFAULT_UA)
    args = p.parse_args()

    sub = args.subreddit.strip().lstrip("/").removeprefix("r/").strip("/")
    after = parse_date(args.after)
    after = REDDIT_EPOCH if after is None else after
    before = parse_date(args.before) or (int(time.time()) + 86400)
    ua = args.user_agent

    out_dir = (Path(args.output_root).expanduser() / sub).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    posts_path = out_dir / "posts.jsonl"
    comments_path = out_dir / "comments.jsonl"
    manifest_path = out_dir / "_manifest.json"

    post_count = [0]
    comment_count = [0]
    live_source = args.sort in ("top", "hot", "controversial", "rising")

    with posts_path.open("w", encoding="utf-8") as pf, \
         comments_path.open("w", encoding="utf-8") as cf:

        def write_post(rec):
            pf.write(json.dumps(rec, ensure_ascii=False) + "\n")
            post_count[0] += 1

        def write_comment(rec):
            cf.write(json.dumps(rec, ensure_ascii=False) + "\n")
            comment_count[0] += 1

        try:
            if args.from_dump:
                source = "dump"
                ddir = Path(args.from_dump).expanduser().resolve()
                if not ddir.is_dir():
                    sys.stderr.write(f"--from-dump path is not a directory: {ddir}\n")
                    return 2
                subs_file = find_dump_file(ddir, sub, "submissions")
                cmts_file = find_dump_file(ddir, sub, "comments")
                if not subs_file and not cmts_file:
                    sys.stderr.write(
                        f"No '{sub}' .zst dump files found in {ddir}.\n"
                        f"Expected e.g. {sub}_submissions.zst and {sub}_comments.zst from the "
                        "Academic Torrents per-subreddit dump.\n"
                    )
                    return 2
                if subs_file:
                    sys.stderr.write(f"$ zstd -dc --long=31 {subs_file.name} | filter posts\n")
                    stream_dump(subs_file, sub, after, before, write_post)
                if cmts_file:
                    sys.stderr.write(f"$ zstd -dc --long=31 {cmts_file.name} | filter comments\n")
                    stream_dump(cmts_file, sub, after, before, write_comment)

            elif live_source:
                source = f"reddit:{args.sort}"
                sys.stderr.write(
                    f"$ GET {REDDIT_BASE}/r/{sub}/{args.sort}.json (t={args.time}, "
                    f"limit={args.limit or 1000})\n"
                )
                try:
                    posts = reddit_listing(sub, args.sort, args.time, args.limit, ua)
                except urllib.error.HTTPError as e:
                    if e.code in (403, 429):
                        sys.stderr.write(
                            f"\nLive Reddit blocked the request (HTTP {e.code}). Reddit "
                            "throttles non-browser clients aggressively.\n"
                            "The by-score top/hot path depends on live Reddit; for a "
                            "full grab use the default archive path instead (drop --sort), "
                            "which doesn't touch live Reddit.\n"
                        )
                        return 5
                    raise
                seen_c = set()
                for post in posts:
                    write_post(post)
                    pid = post.get("id")
                    if pid:
                        comments_for_post(pid, ua, seen_c, write_comment)

            else:
                source = "arctic-shift"
                sys.stderr.write(
                    f"$ walking arctic-shift posts for r/{sub} "
                    f"[{after} .. {before}]{' limit ' + str(args.limit) if args.limit else ''}\n"
                )
                newest_first = args.sort == "new"
                # When capped to N posts, collect their ids in memory (the file is
                # still open for writing, so we can't re-read it) to fetch only their
                # comments — keeping comments tied to the posts actually pulled.
                if args.limit:
                    pulled = []

                    def post_sink(rec):
                        write_post(rec)
                        if rec.get("id"):
                            pulled.append(rec["id"])

                    # `walk`'s counter is separate from post_count to avoid double-counting.
                    walk("posts", {"subreddit": sub}, after, before, ua, set(),
                         post_sink, limit=args.limit, counter=[0], newest_first=newest_first)
                    seen_c = set()
                    for pid in pulled:
                        comments_for_post(pid, ua, seen_c, write_comment)
                else:
                    # Uncapped: walk the full post stream and the full comment stream.
                    walk("posts", {"subreddit": sub}, after, before, ua, set(),
                         write_post, newest_first=newest_first)
                    sys.stderr.write(f"$ walking arctic-shift comments for r/{sub}\n")
                    walk("comments", {"subreddit": sub}, after, before, ua, set(),
                         write_comment)

        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", "replace")[:300]
            except Exception:
                pass
            sys.stderr.write(f"\nArchive/API request failed: HTTP {e.code}. {body}\n")
            return 1
        except RuntimeError as e:
            sys.stderr.write(f"\n{e}\n")
            return 1
        except DumpNeeded as e:
            sys.stderr.write(
                f"\n{e}\n\n"
                "Switch to the bulk-dump path:\n"
                "  1. From the Academic Torrents per-subreddit dump "
                "(https://academictorrents.com/details/3e3f64dee22dc304cdd2546254ca1f8e8ae542b4),\n"
                f"     download just {sub}_submissions.zst and {sub}_comments.zst.\n"
                "  2. brew install zstd   (needed for the 2 GiB --long=31 window)\n"
                f"  3. Re-run with:  --from-dump <dir containing those .zst files>\n"
            )
            return 4

    fetched_at = dt.datetime.now(dt.timezone.utc).date().isoformat()
    manifest = {
        "subreddit": sub,
        "source": source,
        "sort": args.sort,
        "time_filter": args.time if live_source else None,
        "after": after,
        "before": before,
        "limit": args.limit,
        "posts": post_count[0],
        "comments": comment_count[0],
        "fetched_at": fetched_at,
        "output_dir": str(out_dir),
        "tool": "toolshed/subreddit-grab",
        "note": ARCHIVE_NOTE if source in ("arctic-shift",) else None,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    summary = {
        "subreddit": sub,
        "source": source,
        "posts": post_count[0],
        "comments": comment_count[0],
        "posts_path": str(posts_path),
        "comments_path": str(comments_path),
        "manifest_path": str(manifest_path),
    }
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
