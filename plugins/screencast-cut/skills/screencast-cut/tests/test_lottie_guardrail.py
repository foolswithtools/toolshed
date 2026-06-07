"""Licensing guardrail: no third-party Lottie JSON may be committed (Phase 2,
P2-M3).

The big Lottie catalogs forbid redistributing their JSON, so the rule is
absolute: the ONLY Lottie files in this repo are ones we authored ourselves (or
explicit CC0), each sitting next to a PROVENANCE/LICENSE note that says OWNED or
CC0. A user's own Lottie is read from THEIR path at render time and is never
copied in.

This test enforces that by scanning every *tracked* JSON file (via `git
ls-files`, so node_modules and render artifacts are excluded), flagging any that
has Lottie shape but lacks an owned-provenance marker in its directory. Make it
impossible to accidentally commit a pulled Lottie: drop one in and this fails.
"""

import json
import subprocess
from pathlib import Path

import pytest

import lottie_ingest as li

HERE = Path(__file__).resolve().parent
OWNED = HERE / "fixtures" / "golden-project" / "public" / "lottie" / "owned-pulse.json"
HAS_EXPR = HERE / "fixtures" / "lottie" / "has-expressions.json"

PROVENANCE_FILES = ("PROVENANCE", "LICENSE", "LICENSE.txt", "NOTICE", "THIRD-PARTY-NOTICES")
OWNED_MARKERS = ("OWNED", "CC0")


def _repo_root():
    d = HERE
    for parent in [d, *d.parents]:
        if (parent / ".git").exists() or (parent / ".claude-plugin").is_dir():
            return parent
    return d


REPO_ROOT = _repo_root()


def _tracked_json():
    proc = subprocess.run(
        ["git", "ls-files", "*.json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        pytest.skip("git ls-files unavailable")
    return [REPO_ROOT / line for line in proc.stdout.splitlines() if line.strip()]


def _has_owned_provenance(path):
    """True if `path`'s directory carries a provenance note marking it OWNED/CC0."""
    for name in PROVENANCE_FILES:
        f = path.parent / name
        if f.is_file():
            text = f.read_text(errors="ignore").upper()
            if any(m in text for m in OWNED_MARKERS):
                return True
    return False


def test_no_unowned_lottie_committed():
    offenders = []
    for p in _tracked_json():
        if not p.is_file():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if li.looks_like_lottie(data) and not _has_owned_provenance(p):
            offenders.append(str(p.relative_to(REPO_ROOT)))
    assert not offenders, (
        "Lottie JSON committed without an OWNED/CC0 provenance note "
        "(third-party Lottie must never be bundled): " + ", ".join(offenders)
    )


def test_owned_fixtures_are_recognized():
    """Positive control: our authored fixtures DO carry provenance."""
    assert _has_owned_provenance(OWNED)
    assert _has_owned_provenance(HAS_EXPR)


def test_guardrail_flags_missing_provenance(tmp_path):
    """Negative control: a Lottie-shaped file with no provenance note is flagged —
    proving the guardrail can actually fail (a check that can't fail proves
    nothing)."""
    stray = tmp_path / "pulled-from-lottiefiles.json"
    stray.write_text(json.dumps({"v": "5.9.0", "fr": 30, "op": 30, "layers": []}))
    assert li.looks_like_lottie(json.loads(stray.read_text()))
    assert not _has_owned_provenance(stray)
