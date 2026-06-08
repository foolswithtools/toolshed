"""Shared pytest fixtures for the screencast-cut suite.

Pure-function tests import the script modules directly (we put scripts/ on the
path). Tests that need heavy tools (agg/ffmpeg/whisper-cli/node) use the
`*_available` fixtures, which `pytest.skip` when the tool is absent so the suite
stays green on a machine without them.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent  # .../skills/screencast-cut
SCRIPTS_DIR = SKILL_DIR / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
GOLDEN = FIXTURES / "golden-project"

# Make the script modules importable as top-level modules.
sys.path.insert(0, str(SCRIPTS_DIR))

# The verifier lives in the remotion-video plugin; expose it too.
PLUGINS_ROOT = SKILL_DIR.parents[2]  # .../plugins
VERIFY_DIR = PLUGINS_ROOT / "remotion-video" / "skills" / "remotion-video" / "scripts"
sys.path.insert(0, str(VERIFY_DIR))


@pytest.fixture(scope="session")
def fixtures_dir():
    return FIXTURES


@pytest.fixture(scope="session")
def golden_dir():
    return GOLDEN


def _require(tool):
    if shutil.which(tool) is None:
        pytest.skip(f"{tool} not on PATH — skipping tool-gated test")


@pytest.fixture
def agg_available():
    _require("agg")
    _require("ffmpeg")
    _require("ffprobe")


@pytest.fixture
def ffmpeg_available():
    _require("ffmpeg")
    _require("ffprobe")


@pytest.fixture
def whisper_available():
    _require("whisper-cli")


@pytest.fixture(scope="session")
def node_available():
    if shutil.which("node") is None:
        pytest.skip("node not on PATH — skipping e2e render test")
    return True


@pytest.fixture(scope="session")
def golden_installed(node_available, golden_dir):
    """Ensure the golden project's node_modules exist (run `npm ci` once).

    node_modules is intentionally NOT committed. If it's already present (a
    previous run, or a manual install) we reuse it. Skips if npm is missing.
    """
    if shutil.which("npm") is None:
        pytest.skip("npm not on PATH — skipping e2e render test")
    if not golden_dir.is_dir():
        pytest.skip(f"golden project not found at {golden_dir}")
    node_modules = golden_dir / "node_modules"
    bundler = node_modules / "@remotion" / "bundler"
    if not bundler.is_dir():
        lock = golden_dir / "package-lock.json"
        cmd = ["npm", "ci"] if lock.is_file() else ["npm", "install"]
        proc = subprocess.run(cmd, cwd=str(golden_dir), capture_output=True, text=True)
        if proc.returncode != 0:
            pytest.skip(
                f"`{' '.join(cmd)}` failed in golden project "
                f"(network?):\n{proc.stderr[-2000:]}"
            )
    return golden_dir
