"""Tests for script_to_audio.py — the Script: → narration WAV path (Slice A).

The ElevenLabs network is ALWAYS mocked here: no test spends credits or needs a
token. The only real external tool is ffmpeg (gated by the `ffmpeg_available`
fixture), used to exercise the genuine loudnorm/transcode and the full main()
flow with a synthesized MP3 standing in for the API response.
"""

import json
import subprocess
from pathlib import Path

import pytest

import script_to_audio as s2a
from schema_validate import validate, SchemaError


# --------------------------------------------------------------------------- #
# read_script
# --------------------------------------------------------------------------- #
def test_read_script_collapses_lines(tmp_path):
    f = tmp_path / "topic.md"
    f.write_text("# Title\n\nFirst line.\n  Second line.  \n\n\nThird.\n")
    assert s2a.read_script(f) == "# Title First line. Second line. Third."


def test_read_script_empty_is_empty(tmp_path):
    f = tmp_path / "empty.txt"
    f.write_text("\n\n   \n")
    assert s2a.read_script(f) == ""


# --------------------------------------------------------------------------- #
# resolve_api_key — order, and NEVER echoing the value
# --------------------------------------------------------------------------- #
def test_api_key_from_env_wins():
    key = s2a.resolve_api_key(env={s2a.ENV_VAR: "env-secret"})
    assert key == "env-secret"


def test_api_key_from_envrc_export_form(tmp_path):
    envrc = tmp_path / ".envrc"
    envrc.write_text('export ELEVENLABS_API_TOKEN="file-secret"  # mine\n')
    key = s2a.resolve_api_key(env={}, envrc_paths=[envrc], secrets_path=tmp_path / "none")
    assert key == "file-secret"


def test_api_key_from_secrets_plain_form(tmp_path):
    secrets = tmp_path / "secrets.env"
    secrets.write_text("ELEVENLABS_API_TOKEN=plain-secret\n")
    key = s2a.resolve_api_key(env={}, secrets_path=secrets)
    assert key == "plain-secret"


def test_api_key_env_precedes_files(tmp_path):
    envrc = tmp_path / ".envrc"
    envrc.write_text("export ELEVENLABS_API_TOKEN=from-file\n")
    key = s2a.resolve_api_key(env={s2a.ENV_VAR: "from-env"}, envrc_paths=[envrc])
    assert key == "from-env"


def test_api_key_missing_message_lists_paths_not_values(tmp_path):
    secrets = tmp_path / "secrets.env"
    with pytest.raises(SystemExit) as ei:
        s2a.resolve_api_key(env={}, secrets_path=secrets)
    msg = str(ei.value)
    # The message names the env var and the searched paths so the user can act,
    # without ever revealing a value (there is none to reveal here).
    assert s2a.ENV_VAR in msg
    assert str(secrets) in msg


def test_parse_dotenv_ignores_comments_and_other_keys(tmp_path):
    f = tmp_path / ".envrc"
    f.write_text(
        "# a comment\n"
        "OTHER=nope\n"
        "export ELEVENLABS_API_TOKEN=yes-this\n"
    )
    assert s2a._parse_dotenv_value(f, "ELEVENLABS_API_TOKEN") == "yes-this"
    assert s2a._parse_dotenv_value(f, "MISSING") is None


# --------------------------------------------------------------------------- #
# resolve_voice_id — cache + fetch, no network on hit
# --------------------------------------------------------------------------- #
def test_voice_id_explicit_wins_no_network(tmp_path):
    def boom(_key):  # must not be called
        raise AssertionError("network called despite explicit voice_id")

    vid = s2a.resolve_voice_id(
        "Rachel", "explicit-id", api_key="k",
        cache_path=tmp_path / "voices.json", fetch=boom,
    )
    assert vid == "explicit-id"


def test_voice_id_none_when_nothing_given(tmp_path):
    vid = s2a.resolve_voice_id(
        None, None, api_key="k", cache_path=tmp_path / "voices.json",
        fetch=lambda _k: [],
    )
    assert vid is None


def test_voice_id_cache_hit_skips_fetch(tmp_path):
    cache = tmp_path / "voices.json"
    cache.write_text(json.dumps({"bill": "cached-bill-id"}))

    def boom(_key):
        raise AssertionError("fetch called on a cache hit")

    vid = s2a.resolve_voice_id("Bill", None, api_key="k", cache_path=cache, fetch=boom)
    assert vid == "cached-bill-id"


def test_voice_id_cache_miss_fetches_and_persists(tmp_path):
    cache = tmp_path / "voices.json"
    calls = []

    def fake_fetch(_key):
        calls.append(1)
        return [{"name": "Matilda", "voice_id": "matilda-id"}]

    vid = s2a.resolve_voice_id("matilda", None, api_key="k", cache_path=cache, fetch=fake_fetch)
    assert vid == "matilda-id"
    assert calls == [1]
    # Cache persisted lowercased.
    assert json.loads(cache.read_text())["matilda"] == "matilda-id"


def test_voice_id_matches_short_name_before_dash(tmp_path):
    # The real ElevenLabs API returns decorated names; the bare label must still
    # resolve via the short-name alias.
    cache = tmp_path / "voices.json"

    def fake_fetch(_key):
        return [{"name": "Rachel - Social Media Narrator", "voice_id": "rachel-id"}]

    vid = s2a.resolve_voice_id("Rachel", None, api_key="k", cache_path=cache, fetch=fake_fetch)
    assert vid == "rachel-id"
    persisted = json.loads(cache.read_text())
    # Both the full decorated key and the short alias are cached.
    assert persisted["rachel"] == "rachel-id"
    assert persisted["rachel - social media narrator"] == "rachel-id"


def test_alias_map_first_wins_on_short_collision():
    m = s2a.alias_map([
        {"name": "Bill - Wise", "voice_id": "bill-1"},
        {"name": "Bill - Other", "voice_id": "bill-2"},
    ])
    assert m["bill"] == "bill-1"  # first wins
    assert m["bill - wise"] == "bill-1"
    assert m["bill - other"] == "bill-2"


def test_voice_id_unknown_name_raises_with_available(tmp_path):
    with pytest.raises(SystemExit) as ei:
        s2a.resolve_voice_id(
            "Nonexistent", None, api_key="k", cache_path=tmp_path / "v.json",
            fetch=lambda _k: [{"name": "Bill", "voice_id": "b"}],
        )
    assert "Bill" in str(ei.value)


# --------------------------------------------------------------------------- #
# manifest
# --------------------------------------------------------------------------- #
def test_build_manifest_is_schema_valid():
    m = s2a.build_manifest(
        provider="elevenlabs", voice="Bill", voice_id="b-id",
        model="eleven_multilingual_v2", characters_used=42,
        output_path="/x/narration.wav",
        loudnorm={"I": -18, "TP": -2, "LRA": 11},
        voice_settings={"stability": 0.4},
        on_brand=True,
    )
    validate(m, "narration", what="narration.manifest.json")
    assert m["characters_used"] == 42
    assert "token" not in json.dumps(m).lower()


def test_manifest_schema_rejects_bad_provider():
    with pytest.raises(SchemaError):
        validate(
            {"provider": "openai", "voice": None, "voice_id": "x",
             "model": "m", "characters_used": 1, "output_path": "/x"},
            "narration", what="narration.manifest.json",
        )


# --------------------------------------------------------------------------- #
# ffmpeg loudnorm + full main() (network mocked, ffmpeg real)
# --------------------------------------------------------------------------- #
def _make_mp3_bytes(tmp_path, seconds=2):
    """Synthesize a short MP3 with ffmpeg to stand in for an API response."""
    out = tmp_path / "src.mp3"
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "lavfi", "-i", f"sine=frequency=220:duration={seconds}",
         str(out)],
        check=True,
    )
    return out.read_bytes()


def test_mp3_to_loudnorm_wav_produces_16k_mono(tmp_path, ffmpeg_available):
    mp3 = _make_mp3_bytes(tmp_path)
    wav = tmp_path / "narration.wav"
    s2a.mp3_to_loudnorm_wav(mp3, wav, {"I": -18, "TP": -2, "LRA": 11})
    assert wav.is_file() and wav.stat().st_size > 0
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=sample_rate,channels", "-of", "json", str(wav)],
        capture_output=True, text=True, check=True,
    )
    stream = json.loads(probe.stdout)["streams"][0]
    assert int(stream["sample_rate"]) == 16000
    assert int(stream["channels"]) == 1


def test_main_end_to_end_mocked_network(tmp_path, ffmpeg_available, monkeypatch):
    script = tmp_path / "topic.md"
    script.write_text("Hello from the script. This becomes narration.\n")
    out_dir = tmp_path / "source"

    captured = {}

    def fake_synth(text, voice_id, *, model, voice_settings, api_key):
        captured["text"] = text
        captured["voice_id"] = voice_id
        captured["model"] = model
        return _make_mp3_bytes(tmp_path)

    monkeypatch.setattr(s2a, "synthesize", fake_synth)
    monkeypatch.setenv(s2a.ENV_VAR, "unit-test-token")

    s2a.main([
        str(script), str(out_dir),
        "--voice-id", "test-voice-id",
        "--model", "eleven_multilingual_v2",
    ])

    wav = out_dir / "narration.wav"
    manifest_path = out_dir / "narration.manifest.json"
    assert wav.is_file()
    assert manifest_path.is_file()

    manifest = json.loads(manifest_path.read_text())
    validate(manifest, "narration", what="narration.manifest.json")
    assert manifest["voice_id"] == "test-voice-id"
    assert manifest["provider"] == "elevenlabs"
    assert manifest["characters_used"] == len(captured["text"])
    # The token must never appear in the manifest.
    assert "unit-test-token" not in manifest_path.read_text()
    # The script text was passed verbatim (collapsed).
    assert captured["text"] == "Hello from the script. This becomes narration."


def test_main_rejects_non_elevenlabs_provider(tmp_path, monkeypatch):
    script = tmp_path / "t.md"
    script.write_text("x\n")
    monkeypatch.setenv(s2a.ENV_VAR, "tok")
    with pytest.raises(SystemExit) as ei:
        s2a.main([str(script), str(tmp_path / "o"), "--provider", "openai"])
    assert "elevenlabs" in str(ei.value)


def test_main_empty_script_errors(tmp_path, monkeypatch):
    script = tmp_path / "blank.md"
    script.write_text("\n  \n")
    monkeypatch.setenv(s2a.ENV_VAR, "tok")
    with pytest.raises(SystemExit) as ei:
        s2a.main([str(script), str(tmp_path / "o")])
    assert "empty" in str(ei.value).lower()
