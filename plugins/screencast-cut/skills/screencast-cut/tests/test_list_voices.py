"""Tests for list_voices.py — voice listing + theme cross-reference (Slice A).

Network is mocked; no token or credits needed.
"""

import json

import list_voices as lv


def test_scan_theme_voices_reads_default_and_alternates(tmp_path):
    prof = tmp_path / "src" / "brand" / "profiles" / "thick-stroke-americana"
    prof.mkdir(parents=True)
    (prof / "style-guide.ts").write_text(
        'export const tts = {\n'
        '  voice: "Bill",\n'
        '  voice_id: "bill-id",\n'
        '  alternates: ["Matilda", "Bella"],\n'
        '};\n'
    )
    other = tmp_path / "src" / "brand" / "profiles" / "cinematic-noir"
    other.mkdir(parents=True)
    (other / "style-guide.ts").write_text('export const tts = { voice: "Daniel" };\n')

    m = lv.scan_theme_voices(tmp_path)
    assert ("thick-stroke-americana", "default") in m["bill"]
    assert ("thick-stroke-americana", "alternate") in m["matilda"]
    assert ("thick-stroke-americana", "alternate") in m["bella"]
    assert ("cinematic-noir", "default") in m["daniel"]


def test_scan_theme_voices_missing_project_is_empty(tmp_path):
    assert lv.scan_theme_voices(tmp_path / "nope") == {}


def test_main_json_lists_voices_and_themes(tmp_path, monkeypatch, capsys):
    # A tiny project referencing one of the account voices.
    prof = tmp_path / "src" / "brand" / "profiles" / "demo"
    prof.mkdir(parents=True)
    (prof / "style-guide.ts").write_text('export const tts = { voice: "Bill" };\n')

    monkeypatch.setattr(lv, "fetch_voices", lambda _k: [
        {"name": "Bill", "voice_id": "bill-id"},
        {"name": "Rachel", "voice_id": "rachel-id"},
    ])
    monkeypatch.setenv("ELEVENLABS_API_TOKEN", "tok")

    cache = tmp_path / "voices.json"
    lv.main(["--project", str(tmp_path), "--cache", str(cache), "--json"])

    rows = json.loads(capsys.readouterr().out)
    by_name = {r["name"]: r for r in rows}
    assert by_name["Bill"]["voice_id"] == "bill-id"
    assert {"theme": "demo", "role": "default"} in by_name["Bill"]["themes"]
    assert by_name["Rachel"]["themes"] == []
    # Cache was refreshed with both voices.
    assert json.loads(cache.read_text()) == {"bill": "bill-id", "rachel": "rachel-id"}
