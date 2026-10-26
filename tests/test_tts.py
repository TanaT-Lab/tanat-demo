import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location("tts", Path(__file__).resolve().parent.parent / "tools" / "tts.py")
tts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tts)

SCRIPT = "preamble ignored\n\n## intro\nHello\nworld.\n\nSecond para.\n\n## end\nBye.\n"
SR = tts.SAMPLE_RATE


class Fake:
    calls: list[str] = []

    def __init__(self, voice):
        pass

    def synth(self, text):
        Fake.calls.append(text)
        return [0.0] * SR  # 1 s

    def write(self, path, parts, pause):
        path.write_bytes(b"x")


def setup(tmp_path, text=SCRIPT):
    d = tmp_path / "demo"
    d.mkdir(exist_ok=True)
    (d / "SCRIPT.md").write_text(text)
    Fake.calls = []
    return d


def go(d, force=False, budget=285, voice="af_heart"):
    return tts.run(d, voice, force, budget, backend_factory=Fake)


def test_parse():
    s = tts.parse_script(SCRIPT)
    assert s == {"intro": ["Hello world.", "Second para."], "end": ["Bye."]}


def test_hash_normalizes_and_depends_on_voice():
    assert tts.section_hash("v", ["a  b"]) == tts.section_hash("v", ["a b"])
    assert tts.section_hash("v", ["a"]) != tts.section_hash("w", ["a"])


def test_offsets_manifest_and_cache(tmp_path):
    d = setup(tmp_path)
    assert go(d) == 0
    m = json.loads((d / "audio/manifest.json").read_text())
    assert list(m["sections"]) == ["intro", "end"]
    assert m["voice"] == "af_heart"
    assert m["sections"]["intro"]["offsets"] == [0.0, 1.4]
    assert m["sections"]["intro"]["duration"] == 2.4
    assert len(Fake.calls) == 3
    go(d)
    assert len(Fake.calls) == 3  # cache hit
    go(d, force=True)
    assert len(Fake.calls) == 6


def test_changed_and_missing(tmp_path):
    d = setup(tmp_path)
    go(d)
    (d / "SCRIPT.md").write_text(SCRIPT.replace("Bye.", "Goodbye."))
    Fake.calls = []
    go(d)
    assert Fake.calls == ["Goodbye."]
    (d / "audio/intro.mp3").unlink()
    Fake.calls = []
    go(d)
    assert len(Fake.calls) == 2


def test_removed_section(tmp_path):
    d = setup(tmp_path)
    go(d)
    (d / "SCRIPT.md").write_text("## intro\nHello world.\n\nSecond para.\n")
    go(d)
    assert not (d / "audio/end.mp3").exists()
    assert "end" not in json.loads((d / "audio/manifest.json").read_text())["sections"]


def test_budget_exit_code(tmp_path):
    d = setup(tmp_path)
    assert go(d, budget=3) == 1
    assert go(d, budget=4) == 0
