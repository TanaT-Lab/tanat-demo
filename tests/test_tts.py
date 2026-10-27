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
    by_words = False  # True: duration = words / 4 seconds
    written: list = []

    def __init__(self, voice):
        pass

    def synth(self, text):
        Fake.calls.append(text)
        return [0.0] * int(SR * len(text.split()) / 4 if Fake.by_words else SR)  # 1 s

    def write(self, path, paragraphs, pause):
        Fake.written = paragraphs
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


ANCHORED = (
    "## intro\n"
    "{#hello}One two three four. {#mid}Five six. Seven eight {#late}nine ten.\n\n"
    "{#second}Alpha beta gamma delta.\n"
)


def test_strip_and_split():
    assert tts.strip_anchors("a {#x}b{#y-1} c") == "a b c"
    assert tts.split_chunks("{#a}One. {#b}Two {#c}{#d}three.") == [
        (["a"], "One."),
        (["b"], "Two"),
        (["c", "d"], "three."),
    ]
    assert tts.split_chunks("Plain text.") == [([], "Plain text.")]
    assert tts.split_chunks("End {#z}") == [([], "End"), (["z"], "")]


def test_anchors_not_spoken_and_timed(tmp_path):
    d = setup(tmp_path, ANCHORED)
    Fake.by_words = True
    try:
        assert go(d) == 0
    finally:
        Fake.by_words = False
    assert Fake.calls == [
        "One two three four.",   # 1.0 s
        "Five six. Seven eight",  # 1.0 s
        "nine ten.",              # 0.5 s
        "Alpha beta gamma delta.",  # 1.0 s
    ]
    assert not any("{#" in c for c in Fake.calls)
    e = json.loads((d / "audio/manifest.json").read_text())["sections"]["intro"]
    # anchors at the start of the chunk that follows; no pause inside a paragraph
    assert e["anchors"] == {"hello": 0.0, "mid": 1.0, "late": 2.0, "second": 2.9}
    assert e["offsets"] == [0.0, 2.9]
    assert e["duration"] == 3.9
    # chunks of one paragraph are written together (joined without pause)
    assert [len(p) for p in Fake.written] == [3, 1]


def test_anchor_cache_and_changes(tmp_path):
    d = setup(tmp_path, ANCHORED)
    go(d)
    n = len(Fake.calls)
    go(d)
    assert len(Fake.calls) == n  # cache hit with anchors
    (d / "SCRIPT.md").write_text(ANCHORED.replace("{#mid}", "{#middle}"))
    go(d)
    assert len(Fake.calls) == 2 * n  # anchor name is part of the hash
    m = json.loads((d / "audio/manifest.json").read_text())["sections"]["intro"]
    assert "middle" in m["anchors"] and "mid" not in m["anchors"]


def test_old_manifest_without_anchors_is_regenerated(tmp_path):
    d = setup(tmp_path)
    go(d)
    mpath = d / "audio/manifest.json"
    m = json.loads(mpath.read_text())
    for e in m["sections"].values():
        del e["anchors"]
    mpath.write_text(json.dumps(m))
    Fake.calls = []
    go(d)
    assert len(Fake.calls) == 3
    assert "anchors" in json.loads(mpath.read_text())["sections"]["end"]


def test_duplicate_anchor_is_an_error(tmp_path):
    import pytest

    d = setup(tmp_path, "## intro\n{#a}One. {#a}Two.\n")
    with pytest.raises(ValueError, match="duplicate"):
        go(d)
    assert Fake.calls == []
