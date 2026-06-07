"""Unit tests for the Lottie BYO ingest/vetting (Phase 2, P2-M2).

All offline and pure — they exercise the expression-determinism guard, the
best-effort flat-fill recolor, and the Lottie-shape detector against committed,
self-authored fixtures. The library-backed recolor (recolor_lottie.mjs, uses
@lottiefiles/lottie-js) is node-gated and asserted to agree with the Python path.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

import lottie_ingest as li

HERE = Path(__file__).resolve().parent
LOTTIE_FIX = HERE / "fixtures" / "lottie"
OWNED = HERE / "fixtures" / "golden-project" / "public" / "lottie" / "owned-pulse.json"
HAS_EXPR = LOTTIE_FIX / "has-expressions.json"
GRADIENT = LOTTIE_FIX / "gradient-fill.json"

ACCENT = "#22d3ee"


# --- shape detection ---------------------------------------------------------

def test_looks_like_lottie_true_for_real_files():
    for p in (OWNED, HAS_EXPR, GRADIENT):
        assert li.looks_like_lottie(json.loads(p.read_text())), p


def test_looks_like_lottie_false_for_non_lottie():
    assert not li.looks_like_lottie({"name": "pkg", "version": "1.0.0"})
    assert not li.looks_like_lottie({"v": "5", "layers": "not-a-list", "fr": 30})
    assert not li.looks_like_lottie([1, 2, 3])
    assert not li.looks_like_lottie("string")


def test_load_lottie_rejects_non_lottie(tmp_path):
    p = tmp_path / "pkg.json"
    p.write_text('{"name":"x","version":"1"}')
    with pytest.raises(li.LottieIngestError):
        li.load_lottie(p)


# --- expression-determinism guard --------------------------------------------

def test_clean_file_has_no_expressions():
    data = li.load_lottie(OWNED)
    assert li.find_expressions(data) == []
    li.assert_no_expressions(data)  # must not raise


def test_eased_keyframes_are_not_flagged_as_expressions():
    """The owned fixture uses bezier i/o handles whose `x` is an ARRAY — those
    must not be mistaken for an expression (which is a `x` STRING)."""
    data = li.load_lottie(OWNED)
    # sanity: the fixture really does have i/o.x arrays
    s_keyframes = data["layers"][0]["ks"]["s"]["k"]
    assert any("x" in kf.get("i", {}) for kf in s_keyframes if isinstance(kf, dict))
    assert li.find_expressions(data) == []


def test_expression_file_is_detected_and_rejected():
    data = li.load_lottie(HAS_EXPR)
    exprs = li.find_expressions(data)
    assert exprs, "expected the AE expression to be detected"
    assert any("$bm_rt" in snip for _, snip in exprs)
    with pytest.raises(li.LottieIngestError, match="EXPRESSION-DRIVEN"):
        li.assert_no_expressions(data)


def test_ingest_check_only_rejects_expression_file():
    with pytest.raises(li.LottieIngestError):
        li.ingest(HAS_EXPR, check_only=True)


def test_cli_rejects_expression_file(capsys):
    rc = li.main([str(HAS_EXPR), "--check-only"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "REJECTED" in err


def test_cli_accepts_clean_file(capsys):
    rc = li.main([str(OWNED), "--check-only"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "expression-free" in out


# --- best-effort recolor -----------------------------------------------------

def test_recolor_flat_fill_changes_color():
    data = li.load_lottie(OWNED)
    out, report = li.recolor_flat_fills(data, "#ff8800")
    assert report["recolored"] == 1
    assert report["skipped"] == []
    fill = out["layers"][0]["shapes"][0]["it"][1]["c"]["k"]
    assert fill == pytest.approx([1.0, 0.533333, 0.0, 1.0], abs=1e-5)
    # input not mutated
    assert data["layers"][0]["shapes"][0]["it"][1]["c"]["k"][0] != 1.0


def test_recolor_surfaces_gradient_as_unthemable():
    data = li.load_lottie(GRADIENT)
    out, report = li.recolor_flat_fills(data, "#ff8800")
    assert report["recolored"] == 0
    assert any(s["kind"] == "gradient-fill" for s in report["skipped"])


def test_hex_parsing_validates():
    with pytest.raises(li.LottieIngestError):
        li._hex_to_rgba("nope")
    assert li._hex_to_rgba("#000000") == [0.0, 0.0, 0.0, 1.0]
    assert li._hex_to_rgba("#ffffffff")[3] == 1.0


def test_ingest_writes_recolored_output(tmp_path):
    out_path = tmp_path / "themed.json"
    res = li.ingest(OWNED, color=ACCENT, out=str(out_path))
    assert res["out"] == str(out_path)
    assert res["recolored"]["recolored"] == 1
    written = json.loads(out_path.read_text())
    assert li.looks_like_lottie(written)


# --- library-backed recolor (node-gated) must agree with the Python path ------

@pytest.mark.skipif(shutil.which("node") is None, reason="node not on PATH")
def test_lib_recolor_agrees_with_python(golden_installed, tmp_path):
    """recolor_lottie.mjs (@lottiefiles/lottie-js) recolors the same flat fill to
    the same rgba as the pure-Python path — the named-library recolor is wired
    and equivalent for flat fills."""
    project = golden_installed  # ensures @lottiefiles/lottie-js is installed
    script = HERE.parent / "scripts" / "recolor_lottie.mjs"
    out_path = tmp_path / "lib-themed.json"
    proc = subprocess.run(
        ["node", str(script), str(OWNED), "#ff8800", str(out_path)],
        cwd=str(project),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"recolor_lottie.mjs failed:\n{proc.stderr}"
    report = json.loads(proc.stdout)
    assert report["recolored"] == 1
    lib_fill = json.loads(out_path.read_text())["layers"][0]["shapes"][0]["it"][1]["c"]["k"]

    py_out, _ = li.recolor_flat_fills(li.load_lottie(OWNED), "#ff8800")
    py_fill = py_out["layers"][0]["shapes"][0]["it"][1]["c"]["k"]
    assert lib_fill == pytest.approx(py_fill, abs=1e-5)
