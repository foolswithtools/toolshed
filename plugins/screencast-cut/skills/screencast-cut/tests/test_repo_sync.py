"""Guards against two recurring drift classes the reviews kept catching.

1. SKILL.md frontmatter `version:` falling out of step with plugin.json `version`
   (it lagged three phases running). The skill descriptor advertises the version,
   so a stale one is a real inconsistency.
2. The golden project's COMMITTED copy of the `foolswithtools-brand` style guide
   silently drifting from the remotion-video template it was copied from (the
   golden project must be self-contained for its bundle, so the copy exists).

Both are byte/string comparisons — no heavy tools needed.
"""

import json
import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent          # skills/screencast-cut
PLUGIN_DIR = SKILL_DIR.parent.parent                        # plugins/screencast-cut
REPO = SKILL_DIR.parents[3]                                 # repo root


def _skill_version():
    text = SKILL_DIR.joinpath("SKILL.md").read_text(encoding="utf-8")
    m = re.search(r"^version:\s*(.+?)\s*$", text, re.MULTILINE)
    assert m, "no `version:` frontmatter in SKILL.md"
    return m.group(1).strip()


def _plugin_version():
    data = json.loads(PLUGIN_DIR.joinpath(".claude-plugin", "plugin.json").read_text())
    return str(data["version"]).strip()


def test_skill_md_version_matches_plugin_json():
    sv, pv = _skill_version(), _plugin_version()
    assert sv == pv, (
        f"version skew: SKILL.md frontmatter is {sv!r} but plugin.json is {pv!r} "
        f"— bump both together on every release."
    )


def test_golden_foolswithtools_brand_styleguide_matches_template():
    # foolswithtools-brand is a VERBATIM copy of the remotion-video template.
    # (The golden project's `default` profile is intentionally customized and is
    #  NOT mirrored here.)
    template = REPO / (
        "plugins/remotion-video/skills/remotion-video/templates/"
        "foolswithtools-brand/style-guide.ts"
    )
    copy = SKILL_DIR / (
        "tests/fixtures/golden-project/src/brand/profiles/"
        "foolswithtools-brand/style-guide.ts"
    )
    assert template.is_file() and copy.is_file(), "expected both template and copy to exist"
    assert copy.read_text(encoding="utf-8") == template.read_text(encoding="utf-8"), (
        "golden-project foolswithtools-brand/style-guide.ts drifted from the "
        "remotion-video template — re-sync the copy."
    )
