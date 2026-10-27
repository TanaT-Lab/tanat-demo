"""Unit tests for tools/build_site.py.

Uses a tmp_path fake repo (no TanaT, no network) to check staging content,
exclusions and the failure mode when outputs are missing.
"""

import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "tools"))
import build_site  # noqa: E402


def make_fake_repo(tmp_path):
    """Create a minimal fake repo layout and return (root, out_dir)."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / "index.html").write_text("<html></html>", encoding="utf-8")
    (root / "player.html").write_text("<html></html>", encoding="utf-8")

    (root / "core").mkdir()
    (root / "core" / "styles.css").write_text("body{}", encoding="utf-8")

    (root / "assets").mkdir()
    (root / "assets" / "logo.png").write_bytes(b"\x89PNG")

    (root / "data").mkdir()
    (root / "data" / "mimic.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (root / "data" / "notes.txt").write_text("not published", encoding="utf-8")

    demo = root / "demos" / "demo1"
    (demo / "outputs").mkdir(parents=True)
    (demo / "pipeline.py").write_text("# %% 1a\n", encoding="utf-8")
    (demo / "SCRIPT.md").write_text("## intro\n", encoding="utf-8")
    (demo / "config.js").write_text("const DEMO_CONFIG={};", encoding="utf-8")
    (demo / "demo.json").write_text('{"id":"demo1"}', encoding="utf-8")
    (demo / "outputs" / "outputs.json").write_text('{"demo":"demo1"}', encoding="utf-8")
    (demo / "outputs" / "1a.png").write_bytes(b"\x89PNG")
    (demo / "__pycache__").mkdir()
    (demo / "__pycache__" / "x.pyc").write_bytes(b"\x00")

    (root / "demos" / "index.json").write_text('[{"id":"demo1"}]', encoding="utf-8")

    out = tmp_path / "site"
    return root, out


def test_stages_expected_content(tmp_path):
    root, out = make_fake_repo(tmp_path)
    build_site.build_site(str(out), repo_dir=str(root))

    assert (out / "index.html").is_file()
    assert (out / "player.html").is_file()
    assert (out / "core" / "styles.css").is_file()
    assert (out / "assets" / "logo.png").is_file()
    assert (out / "data" / "mimic.csv").is_file()
    assert (out / "demos" / "index.json").is_file()
    assert (out / "demos" / "demo1" / "config.js").is_file()
    assert (out / "demos" / "demo1" / "demo.json").is_file()
    assert (out / "demos" / "demo1" / "outputs" / "outputs.json").is_file()
    assert (out / "demos" / "demo1" / "outputs" / "1a.png").is_file()


def test_excludes_source_only_and_non_csv(tmp_path):
    root, out = make_fake_repo(tmp_path)
    build_site.build_site(str(out), repo_dir=str(root))

    assert not (out / "demos" / "demo1" / "pipeline.py").exists()
    assert not (out / "demos" / "demo1" / "SCRIPT.md").exists()
    assert not (out / "demos" / "demo1" / "__pycache__").exists()
    assert not (out / "data" / "notes.txt").exists()


def test_fails_when_demo_outputs_missing(tmp_path, capsys):
    root, out = make_fake_repo(tmp_path)
    (root / "demos" / "demo1" / "outputs" / "outputs.json").unlink()
    with pytest.raises(SystemExit):
        build_site.build_site(str(out), repo_dir=str(root))
    assert "outputs/outputs.json" in capsys.readouterr().err
    assert not (out / "demos" / "demo1").exists()


def test_fails_when_index_json_missing(tmp_path, capsys):
    root, out = make_fake_repo(tmp_path)
    (root / "demos" / "index.json").unlink()
    with pytest.raises(SystemExit):
        build_site.build_site(str(out), repo_dir=str(root))
    assert "demos/index.json" in capsys.readouterr().err


def test_refuses_out_dir_inside_repo(tmp_path, capsys):
    root, out = make_fake_repo(tmp_path)
    for bad in (str(root), str(root.parent), str(tmp_path)):
        with pytest.raises(SystemExit):
            build_site.build_site(bad, repo_dir=str(root))
        assert "refusing to wipe" in capsys.readouterr().err
    # The repo content must be untouched.
    assert (root / "index.html").is_file()
    assert (root / "demos" / "index.json").is_file()
