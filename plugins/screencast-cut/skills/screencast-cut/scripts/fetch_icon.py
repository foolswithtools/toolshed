#!/usr/bin/env python3
"""Iconify puller — fetch one icon ONCE, then keep it local/static forever.

Given `set:name` (e.g. `lucide:rocket`), resolve the SVG via the Iconify public
API, normalize it through `icon_svg.parse_svg`, and write it into a project's
icon area as:

  - `<icons_dir>/<name>.svg`            the raw source (human-auditable),
  - an entry in `<icons_dir>/icons.json` (same shape as the curated floor),
  - a line appended to `<icons_dir>/THIRD-PARTY-NOTICES` recording the set,
    its license, and the source URL.

After that first fetch the icon is local and reproducible — no network on any
later render. The ONE network call is isolated here.

SAFETY: only ISC/MIT/Apache-2.0 icon sets are allowed (`PERMISSIVE_SETS`). A
non-permissive or unknown set is refused with a clear message, because the
license metadata that the notices file records is only trustworthy for sets we
have vetted. This allowlist + per-set license is the redistribution safeguard.

The network is reached only from `_http_get`; every other function is pure and
unit-tested offline (the resolver, allowlist, registry/notice emit).
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from icon_svg import parse_svg  # noqa: E402

# Permissive Iconify sets we are willing to bundle/redistribute. set prefix ->
# (human name, SPDX license, homepage). Restricted to ISC/MIT/Apache-2.0.
PERMISSIVE_SETS = {
    "lucide": ("Lucide", "ISC", "https://lucide.dev"),
    "tabler": ("Tabler Icons", "MIT", "https://tabler.io/icons"),
    "ph": ("Phosphor Icons", "MIT", "https://phosphoricons.com"),
    "heroicons": ("Heroicons", "MIT", "https://heroicons.com"),
    "feather": ("Feather", "MIT", "https://feathericons.com"),
    "bi": ("Bootstrap Icons", "MIT", "https://icons.getbootstrap.com"),
    "octicon": ("Octicons", "MIT", "https://primer.style/octicons"),
    "fluent": ("Fluent UI System Icons", "MIT", "https://github.com/microsoft/fluentui-system-icons"),
    "mdi": ("Material Design Icons", "Apache-2.0", "https://pictogrammers.com/library/mdi"),
    "material-symbols": ("Material Symbols", "Apache-2.0", "https://fonts.google.com/icons"),
    "ri": ("Remix Icon", "Apache-2.0", "https://remixicon.com"),
    "carbon": ("Carbon Icons", "Apache-2.0", "https://carbondesignsystem.com/guidelines/icons/library"),
}

_SPEC_RE = re.compile(r"^([a-z0-9]+(?:-[a-z0-9]+)*):([a-z0-9]+(?:-[a-z0-9]+)*)$")


class IconFetchError(Exception):
    """A puller failure with a user-facing message (bad spec / disallowed set)."""


def parse_set_name(spec):
    """Split `set:name` into `(set, name)`; raise IconFetchError if malformed."""
    m = _SPEC_RE.match((spec or "").strip())
    if not m:
        raise IconFetchError(
            f"invalid icon spec {spec!r}; expected `set:name`, e.g. `lucide:rocket`"
        )
    return m.group(1), m.group(2)


def is_allowed(icon_set):
    """True iff `icon_set` is on the permissive allowlist."""
    return icon_set in PERMISSIVE_SETS


def require_allowed(icon_set):
    """Raise IconFetchError if `icon_set` is not permissively licensed."""
    if not is_allowed(icon_set):
        allowed = ", ".join(sorted(PERMISSIVE_SETS))
        raise IconFetchError(
            f"icon set {icon_set!r} is not on the permissive allowlist and will "
            f"NOT be pulled (only ISC/MIT/Apache-2.0 sets may be redistributed). "
            f"Allowed sets: {allowed}"
        )


def iconify_url(icon_set, name):
    """Iconify API URL for a single SVG."""
    return f"https://api.iconify.design/{icon_set}/{name}.svg"


def build_entry(icon_set, parsed):
    """Registry entry from a parsed SVG + its set. strokeWidth defaults to 2."""
    _, license_id, _ = PERMISSIVE_SETS[icon_set]
    sw = parsed.get("strokeWidth")
    return {
        "viewBox": parsed["viewBox"],
        "paths": parsed["paths"],
        "strokeWidth": sw if isinstance(sw, (int, float)) else 2,
        "set": icon_set,
        "license": license_id,
    }


def update_registry(icons_json, name, entry):
    """Merge `entry` under `name` into the icons.json at `icons_json` (created
    if absent). Returns the full registry dict."""
    reg = {}
    if icons_json.is_file():
        reg = json.loads(icons_json.read_text(encoding="utf-8"))
    reg[name] = entry
    icons_json.write_text(
        json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return reg


_PULLED_HEADER = "Pulled icons (added by scripts/fetch_icon.py)"


def notice_line(icon_set, name):
    human, license_id, _ = PERMISSIVE_SETS[icon_set]
    return f"- {human} ({icon_set}, {license_id}): {name}  —  {iconify_url(icon_set, name)}"


def append_notice(notices_path, icon_set, name):
    """Append a one-line attribution for a pulled icon, idempotently. Ensures a
    'Pulled icons' section header exists exactly once and never duplicates a
    line."""
    line = notice_line(icon_set, name)
    existing = notices_path.read_text(encoding="utf-8") if notices_path.is_file() else ""
    if line in existing:
        return existing
    if _PULLED_HEADER not in existing:
        sep = "\n" if existing and not existing.endswith("\n") else ""
        block = (
            f"{sep}\n"
            "---------------------------------------------------------------------------\n\n"
            f"{_PULLED_HEADER}\n\n"
        )
        existing = existing + block
    if not existing.endswith("\n"):
        existing += "\n"
    existing += line + "\n"
    notices_path.write_text(existing, encoding="utf-8")
    return existing


def fetch_icon(spec, icons_dir, *, svg_text=None, fetcher=None):
    """Resolve `set:name` into `icons_dir`, writing the SVG + registry + notice.

    `svg_text` lets a caller (or a test) supply the SVG directly and skip the
    network entirely; `fetcher` overrides the HTTP getter. Returns the registry
    entry. Raises IconFetchError for a bad spec or a disallowed set.
    """
    icon_set, name = parse_set_name(spec)
    require_allowed(icon_set)

    if svg_text is None:
        get = fetcher or _http_get
        svg_text = get(iconify_url(icon_set, name))

    parsed = parse_svg(svg_text)
    entry = build_entry(icon_set, parsed)

    icons_dir = Path(icons_dir)
    icons_dir.mkdir(parents=True, exist_ok=True)
    (icons_dir / f"{name}.svg").write_text(svg_text, encoding="utf-8")
    update_registry(icons_dir / "icons.json", name, entry)
    append_notice(icons_dir / "THIRD-PARTY-NOTICES", icon_set, name)
    return entry


def _http_get(url, timeout=15):
    """Fetch a URL as text. Isolated so the rest of the module stays offline."""
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": "screencast-cut/fetch_icon"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status != 200:
            raise IconFetchError(f"icon fetch failed: HTTP {resp.status} for {url}")
        return resp.read().decode("utf-8")


def main(argv):
    ap = argparse.ArgumentParser(description="Pull one Iconify icon into a project.")
    ap.add_argument("spec", help="icon spec `set:name`, e.g. lucide:rocket")
    ap.add_argument(
        "--icons-dir",
        required=True,
        type=Path,
        help="target icons directory (holds icons.json + THIRD-PARTY-NOTICES)",
    )
    args = ap.parse_args(argv)
    try:
        entry = fetch_icon(args.spec, args.icons_dir)
    except IconFetchError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except Exception as e:  # network / parse
        print(f"error: could not fetch {args.spec}: {e}", file=sys.stderr)
        return 1
    print(
        f"pulled {args.spec} → {args.icons_dir} "
        f"({len(entry['paths'])} path(s), set={entry['set']}, {entry['license']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
