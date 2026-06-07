"""Tests for the Iconify puller (`fetch_icon.py`).

Offline by default: the resolver, allowlist, and registry/notice emit are tested
with a committed fixture SVG injected via `svg_text=`. One live-network test is
gated to skip when the API is unreachable (offline CI stays green).
"""

import json
import urllib.error
from pathlib import Path

import pytest

import fetch_icon as fi

FIXTURES = Path(__file__).resolve().parent / "fixtures"
ROCKET_SVG = (FIXTURES / "icons" / "lucide-rocket.svg").read_text()


# --- resolver -----------------------------------------------------------------

def test_parse_set_name_valid():
    assert fi.parse_set_name("lucide:rocket") == ("lucide", "rocket")
    assert fi.parse_set_name("material-symbols:home-rounded") == (
        "material-symbols",
        "home-rounded",
    )


@pytest.mark.parametrize("bad", ["", "rocket", "lucide:", ":rocket", "lucide/rocket", "Lucide:Rocket"])
def test_parse_set_name_rejects_malformed(bad):
    with pytest.raises(fi.IconFetchError):
        fi.parse_set_name(bad)


# --- allowlist ----------------------------------------------------------------

@pytest.mark.parametrize("s", ["lucide", "tabler", "ph", "heroicons", "mdi", "material-symbols", "ri", "carbon"])
def test_allowlist_accepts_permissive(s):
    assert fi.is_allowed(s)
    fi.require_allowed(s)  # does not raise


@pytest.mark.parametrize("s", ["twemoji", "noto", "fa6-brands", "openmoji", "made-up-set"])
def test_allowlist_refuses_others(s):
    assert not fi.is_allowed(s)
    with pytest.raises(fi.IconFetchError):
        fi.require_allowed(s)


def test_iconify_url():
    assert (
        fi.iconify_url("lucide", "rocket")
        == "https://api.iconify.design/lucide/rocket.svg"
    )


# --- offline fetch via injected svg -------------------------------------------

def test_fetch_icon_offline_writes_everything(tmp_path):
    entry = fi.fetch_icon("lucide:rocket", tmp_path, svg_text=ROCKET_SVG)

    # registry entry shape
    assert entry["set"] == "lucide"
    assert entry["license"] == "ISC"
    assert len(entry["paths"]) == 3
    assert entry["strokeWidth"] == 2

    # raw svg written
    assert (tmp_path / "rocket.svg").read_text() == ROCKET_SVG

    # icons.json updated
    reg = json.loads((tmp_path / "icons.json").read_text())
    assert "rocket" in reg
    assert reg["rocket"]["set"] == "lucide"

    # notice appended
    notices = (tmp_path / "THIRD-PARTY-NOTICES").read_text()
    assert "Pulled icons" in notices
    assert "lucide" in notices and "rocket" in notices and "ISC" in notices


def test_fetch_icon_refuses_disallowed_set_writes_nothing(tmp_path):
    with pytest.raises(fi.IconFetchError):
        fi.fetch_icon("twemoji:rocket", tmp_path, svg_text=ROCKET_SVG)
    assert not (tmp_path / "icons.json").exists()
    assert not (tmp_path / "rocket.svg").exists()


def test_fetch_icon_merges_into_existing_registry(tmp_path):
    fi.fetch_icon("lucide:rocket", tmp_path, svg_text=ROCKET_SVG)
    check_svg = (
        '<svg viewBox="0 0 24 24"><path stroke-width="2" d="M20 6L9 17l-5-5"/></svg>'
    )
    fi.fetch_icon("lucide:check", tmp_path, svg_text=check_svg)
    reg = json.loads((tmp_path / "icons.json").read_text())
    assert set(reg) == {"rocket", "check"}


def test_notice_is_idempotent_and_single_header(tmp_path):
    fi.fetch_icon("lucide:rocket", tmp_path, svg_text=ROCKET_SVG)
    fi.fetch_icon("lucide:rocket", tmp_path, svg_text=ROCKET_SVG)  # again
    fi.fetch_icon("tabler:circle", tmp_path, svg_text='<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/></svg>')
    notices = (tmp_path / "THIRD-PARTY-NOTICES").read_text()
    # exactly one section header even after a repeat + a second set
    assert notices.count("Pulled icons (added by scripts/fetch_icon.py)") == 1
    # the rocket line appears once, not twice
    assert notices.count("lucide, ISC): rocket") == 1
    # the second permissive set was recorded too
    assert "tabler" in notices


def test_fetch_uses_injected_fetcher_not_network(tmp_path):
    calls = {}

    def fake_fetcher(url):
        calls["url"] = url
        return ROCKET_SVG

    fi.fetch_icon("lucide:rocket", tmp_path, fetcher=fake_fetcher)
    assert calls["url"] == "https://api.iconify.design/lucide/rocket.svg"


def test_build_entry_defaults_strokewidth(tmp_path):
    # an SVG with no stroke-width should default to 2 in the registry
    svg = '<svg viewBox="0 0 24 24"><path d="M0 0L1 1"/></svg>'
    entry = fi.fetch_icon("lucide:line", tmp_path, svg_text=svg)
    assert entry["strokeWidth"] == 2


# --- live network (gated) -----------------------------------------------------

def test_fetch_icon_live_network(tmp_path):
    """Real Iconify API call. Skips (not fails) when the network is unreachable
    so offline runs stay green; runs for real when connectivity exists."""
    try:
        entry = fi.fetch_icon("lucide:rocket", tmp_path)
    except (urllib.error.URLError, OSError) as e:
        pytest.skip(f"network unavailable for live Iconify fetch: {e}")
    assert entry["set"] == "lucide"
    assert len(entry["paths"]) >= 1
    assert (tmp_path / "rocket.svg").is_file()
    reg = json.loads((tmp_path / "icons.json").read_text())
    assert "rocket" in reg
