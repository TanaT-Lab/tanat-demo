"""Unit tests for the checks in run.py (no server, no browser).

These exercise check_outputs_exist() against a temporary demos/ layout so no
HTTP server, browser or TanaT are required.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import run  # noqa: E402


def make_demos(tmp_path, with_outputs=False, with_index=False):
    demos_dir = tmp_path / "demos"
    demo = demos_dir / "mimic-clustering"
    demo.mkdir(parents=True)
    (demo / "pipeline.py").write_text("# %% 1a\n", encoding="utf-8")
    if with_outputs:
        out = demo / "outputs"
        out.mkdir()
        (out / "outputs.json").write_text("{}", encoding="utf-8")
    if with_index:
        (demos_dir / "index.json").write_text("[]", encoding="utf-8")
    return demos_dir


def test_missing_index_json_is_reported(tmp_path, monkeypatch):
    demos_dir = make_demos(tmp_path, with_outputs=True, with_index=False)
    monkeypatch.setattr(run, "DEMOS_DIR", str(demos_dir))
    assert "demos/index.json" in run.check_outputs_exist()


def test_missing_outputs_and_index_reported(tmp_path, monkeypatch):
    demos_dir = make_demos(tmp_path, with_outputs=False, with_index=False)
    monkeypatch.setattr(run, "DEMOS_DIR", str(demos_dir))
    missing = run.check_outputs_exist()
    assert "demos/index.json" in missing
    assert "demos/mimic-clustering/outputs/" in missing


def test_nothing_missing_when_all_present(tmp_path, monkeypatch):
    demos_dir = make_demos(tmp_path, with_outputs=True, with_index=True)
    monkeypatch.setattr(run, "DEMOS_DIR", str(demos_dir))
    assert run.check_outputs_exist() == []


def test_missing_demos_dir(tmp_path, monkeypatch):
    missing_dir = tmp_path / "does-not-exist"
    monkeypatch.setattr(run, "DEMOS_DIR", str(missing_dir))
    assert run.check_outputs_exist() == ["demos/ directory not found"]
