#!/usr/bin/env python3
"""Stage the static site into a directory for GitHub Pages.

Usage: python tools/build_site.py <out_dir>

Copies the front (index.html, player.html), core/, assets/, data/*.csv and the
demos/ tree (minus pipeline.py, SCRIPT.md and __pycache__) into <out_dir> after
wiping it. Fails with a clear message when demos/index.json or a demo's
outputs/outputs.json is missing (i.e. generate_all.py has not been run).

Standard library only.
"""

import argparse
import os
import shutil
import sys

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Source-only entries that must not be staged into the published site.
_DEMO_EXCLUDES = frozenset({"pipeline.py", "SCRIPT.md", "__pycache__"})


def _require(condition, message, hint=True):
    """Exit with a clear message when a required file/dir is missing.

    ``hint`` controls whether the "run generate_all.py first" suggestion is
    printed, which only makes sense for generated outputs (not for an unsafe
    out_dir or a missing repo dir).
    """
    if not condition:
        print(f"error: {message}", file=sys.stderr)
        if hint:
            print("Run `python generate_all.py` first.", file=sys.stderr)
        sys.exit(1)


def copy_tree(src, dst, excludes=frozenset()):
    """Recursively copy a directory, skipping entries in ``excludes``."""
    os.makedirs(dst, exist_ok=True)
    for entry in sorted(os.listdir(src)):
        if entry in excludes:
            continue
        s = os.path.join(src, entry)
        d = os.path.join(dst, entry)
        if os.path.isdir(s):
            copy_tree(s, d, excludes)
        else:
            shutil.copy2(s, d)


def build_site(out_dir, repo_dir=SCRIPT_DIR):
    """Stage the site into ``out_dir`` (wiping it first). Returns out_dir."""
    _require(os.path.isdir(repo_dir), f"repo dir not found: {repo_dir}")

    out_dir = os.path.abspath(out_dir)
    repo_dir = os.path.abspath(repo_dir)
    if out_dir == repo_dir or os.path.commonpath([out_dir, repo_dir]) == out_dir:
        _require(
            False,
            f"refusing to wipe the repo or a parent of it: {out_dir}",
            hint=False,
        )

    demos_src = os.path.join(repo_dir, "demos")
    index_json = os.path.join(demos_src, "index.json")
    _require(os.path.isfile(index_json), "missing demos/index.json (generate_all.py not run?)")

    # Validate every demo has outputs before touching the destination.
    for demo_id in sorted(os.listdir(demos_src)):
        demo_src = os.path.join(demos_src, demo_id)
        if not os.path.isdir(demo_src):
            continue
        outputs_json = os.path.join(demo_src, "outputs", "outputs.json")
        _require(
            os.path.isfile(outputs_json),
            f"demo '{demo_id}' has no outputs/outputs.json (generate_all.py not run?)",
        )

    # Wipe the destination.
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    # Top-level front files.
    for name in ("index.html", "player.html"):
        src = os.path.join(repo_dir, name)
        _require(os.path.isfile(src), f"missing {name}")
        shutil.copy2(src, os.path.join(out_dir, name))

    # Static front trees.
    for name in ("core", "assets"):
        src = os.path.join(repo_dir, name)
        _require(os.path.isdir(src), f"missing {name}/")
        copy_tree(src, os.path.join(out_dir, name))

    # Shared data: only data/*.csv is published.
    data_src = os.path.join(repo_dir, "data")
    if os.path.isdir(data_src):
        data_dst = os.path.join(out_dir, "data")
        os.makedirs(data_dst, exist_ok=True)
        copied = 0
        for entry in sorted(os.listdir(data_src)):
            if entry.endswith(".csv"):
                shutil.copy2(
                    os.path.join(data_src, entry), os.path.join(data_dst, entry)
                )
                copied += 1
        if copied == 0:
            print("warning: no data/*.csv to stage", file=sys.stderr)

    # Demos tree, excluding source-only files.
    copy_tree(demos_src, os.path.join(out_dir, "demos"), _DEMO_EXCLUDES)

    print(f"Site staged in {out_dir}")
    return out_dir


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Stage the static site into <out_dir> for GitHub Pages.",
        epilog="Fails when demos/index.json or a demo's outputs/outputs.json is missing.",
    )
    parser.add_argument("out_dir", help="output directory to stage the site into")
    args = parser.parse_args(argv)
    build_site(args.out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
