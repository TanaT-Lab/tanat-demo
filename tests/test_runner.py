"""Tests for the generic block runner in generate_all.py.

These use temporary fake pipelines, so no TanaT is required.
"""

import json
import os
import sys
import textwrap

import matplotlib

matplotlib.use("Agg")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import generate_all  # noqa: E402


def write_pipeline(demo_dir, source):
    demo_dir.mkdir(parents=True, exist_ok=True)
    path = demo_dir / "pipeline.py"
    path.write_text(textwrap.dedent(source), encoding="utf-8")
    return str(path)


def read_outputs(demo_dir):
    path = demo_dir / "outputs" / "outputs.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_print_capture_and_empty_output_null(tmp_path):
    source = """\
        # %% 1a
        print("hello world")
        # %% 2b
        x = 1
    """
    write_pipeline(tmp_path / "demo", source)
    assert generate_all.run_demo("demo", demos_dir=str(tmp_path)) is True

    out = read_outputs(tmp_path / "demo")
    assert out["demo"] == "demo"
    assert out["blocks"][0] == {
        "id": "1a",
        "code": 'print("hello world")',
        "output": "hello world",
        "figure": None,
    }
    assert out["blocks"][1]["id"] == "2b"
    assert out["blocks"][1]["code"] == "x = 1"
    assert out["blocks"][1]["output"] is None
    assert out["blocks"][1]["figure"] is None


def test_shared_namespace_between_blocks(tmp_path):
    source = """\
        # %% 1a
        value = 42
        # %% 2b
        print(value)
    """
    write_pipeline(tmp_path / "demo", source)
    assert generate_all.run_demo("demo", demos_dir=str(tmp_path)) is True

    out = read_outputs(tmp_path / "demo")
    assert out["blocks"][1]["output"] == "42"


def test_preamble_executed_but_not_exported(tmp_path):
    source = """\
        secret = "shh"
        # %% 1a
        print(secret)
    """
    write_pipeline(tmp_path / "demo", source)
    assert generate_all.run_demo("demo", demos_dir=str(tmp_path)) is True

    out = read_outputs(tmp_path / "demo")
    assert len(out["blocks"]) == 1
    assert out["blocks"][0]["code"] == "print(secret)"
    assert "shh" not in out["blocks"][0]["code"]
    assert out["blocks"][0]["output"] == "shh"


def test_one_figure_saved(tmp_path):
    source = """\
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        # %% 1a
        plt.figure()
        plt.plot([1, 2, 3])
    """
    write_pipeline(tmp_path / "demo", source)
    assert generate_all.run_demo("demo", demos_dir=str(tmp_path)) is True

    out = read_outputs(tmp_path / "demo")
    assert out["blocks"][0]["figure"] == "1a.png"
    assert (tmp_path / "demo" / "outputs" / "1a.png").exists()
    assert (tmp_path / "demo" / "outputs" / "1a.png").stat().st_size > 0


def test_two_figures_in_block_errors(tmp_path):
    source = """\
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        # %% 1a
        plt.figure()
        plt.figure()
    """
    write_pipeline(tmp_path / "demo", source)
    assert generate_all.run_demo("demo", demos_dir=str(tmp_path)) is False


def test_exception_fails_demo(tmp_path):
    source = """\
        # %% 1a
        raise RuntimeError("boom")
    """
    write_pipeline(tmp_path / "demo", source)
    assert generate_all.run_demo("demo", demos_dir=str(tmp_path)) is False


def test_traceback_line_numbers_match_pipeline(tmp_path, capsys):
    source = """\
        x = 1
        # %% 1a
        y = 2
        # %% 2b
        z = 3
        raise RuntimeError("kaboom")
    """
    write_pipeline(tmp_path / "demo", source)
    assert generate_all.run_demo("demo", demos_dir=str(tmp_path)) is False

    captured = capsys.readouterr()
    pipeline = tmp_path / "demo" / "pipeline.py"
    assert f'File "{pipeline}", line 6' in captured.err


def test_preamble_exception_fails_demo(tmp_path, capsys):
    source = """\
        raise RuntimeError("preamble boom")
        # %% 1a
        print("never")
    """
    write_pipeline(tmp_path / "demo", source)
    assert generate_all.run_demo("demo", demos_dir=str(tmp_path)) is False

    captured = capsys.readouterr()
    assert "Block 'preamble'" in captured.out
    assert "preamble boom" in captured.err
    assert not (tmp_path / "demo" / "outputs" / "outputs.json").exists()


def test_multiline_output_strips_trailing_newline(tmp_path):
    source = """\
        # %% 1a
        print("line1")
        print("line2")
    """
    write_pipeline(tmp_path / "demo", source)
    assert generate_all.run_demo("demo", demos_dir=str(tmp_path)) is True

    out = read_outputs(tmp_path / "demo")
    assert out["blocks"][0]["output"] == "line1\nline2"
    assert not out["blocks"][0]["output"].endswith("\n")


def test_parse_blocks_preamble_and_ids():
    source = textwrap.dedent(
        """\
            import matplotlib
            import matplotlib.pyplot as plt

            # %% 1a
            print("a")

            # %% 2b

            x = 1
        """
    )
    preamble, blocks = generate_all.parse_blocks(source)
    assert "import matplotlib" in preamble
    assert blocks[0][0] == "1a"
    assert blocks[0][1] == 5
    assert blocks[0][2] == 'print("a")'
    assert blocks[1][0] == "2b"
    assert blocks[1][1] == 9
    assert blocks[1][2] == "x = 1"
