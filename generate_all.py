#!/usr/bin/env python3
"""
TanaT Demo - Master Output Generator

Discovers demos/*/pipeline.py and runs each block by block.

A demo pipeline is a single Python file split into blocks with marker lines
`# %% <id>`. The runner executes the preamble (code before the first marker,
never exported) then each block in file order inside ONE shared namespace, with
cwd set to the repo root (so 'data/x.csv' paths work). For every block it
captures stdout, saves any open matplotlib figure to
demos/<id>/outputs/<block_id>.png, and records {id, code, output, figure}. The
results are written to demos/<id>/outputs/outputs.json.

Usage:
    python generate_all.py              # Generate all demos
    python generate_all.py mimic-clustering  # Generate specific demo
    python generate_all.py --list       # List available demos
"""

import argparse
import contextlib
import io
import json
import os
import re
import sys
import traceback
from importlib import metadata

# ═══════════════════════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════════════════════

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEMOS_DIR = os.path.join(SCRIPT_DIR, "demos")

# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK PARSING
# ═══════════════════════════════════════════════════════════════════════════════

BLOCK_MARKER = re.compile(r"^# %% (\S+)\s*$")


def _strip_blank_lines(lines):
    """Remove leading and trailing blank (whitespace-only) lines in place.

    ``lines`` is a list of (lineno, text) pairs.
    """
    while lines and not lines[0][1].strip():
        lines.pop(0)
    while lines and not lines[-1][1].strip():
        lines.pop()
    return lines


def _make_block(lines):
    """Convert raw (lineno, text) pairs into (start_lineno, code)."""
    _strip_blank_lines(lines)
    if not lines:
        return None, ""
    return lines[0][0], "\n".join(text for _, text in lines)


def parse_blocks(source):
    """
    Split pipeline source into (preamble, [(block_id, start_lineno, code), ...]).

    A line matching '^# %% (\\S+)\\s*$' starts block <id>. Code before the first
    marker is the preamble. Each block's code is the lines between its marker
    and the next marker, with leading/trailing blank lines stripped.
    ``start_lineno`` is the 1-based line of the first non-blank code line in the
    original file, used to keep tracebacks aligned with pipeline.py.
    """
    preamble = []
    blocks = []
    current_id = None
    current_lines = []

    for lineno, line in enumerate(source.splitlines(), start=1):
        match = BLOCK_MARKER.match(line)
        if match:
            if current_id is not None:
                blocks.append((current_id,) + _make_block(current_lines))
            current_id = match.group(1)
            current_lines = []
        elif current_id is None:
            preamble.append(line)
        else:
            current_lines.append((lineno, line))

    if current_id is not None:
        blocks.append((current_id,) + _make_block(current_lines))

    return "\n".join(preamble), blocks


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO DISCOVERY
# ═══════════════════════════════════════════════════════════════════════════════


def discover_demos():
    """Discover all demos that have a pipeline.py script."""
    demos = {}

    if not os.path.exists(DEMOS_DIR):
        return demos

    for entry in os.listdir(DEMOS_DIR):
        demo_path = os.path.join(DEMOS_DIR, entry)
        pipeline_script = os.path.join(demo_path, "pipeline.py")

        if os.path.isdir(demo_path) and os.path.exists(pipeline_script):
            demos[entry] = pipeline_script

    return demos


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO MANIFEST
# ═══════════════════════════════════════════════════════════════════════════════


def _format_duration(total_seconds):
    """Format a total duration (seconds) as a human string like '~4 min'."""
    minutes = -(-int(total_seconds) // 60)  # ceil division to the minute
    return f"~{minutes} min"


def _demo_duration(demo_dir):
    """Total narration duration from audio/manifest.json, else None.

    A static site cannot measure an audio folder, so the duration is derived
    from the per-demo audio manifest written by tools/tts.py. When that
    manifest is absent the duration is None (the landing hides it).
    """
    manifest_path = os.path.join(demo_dir, "audio", "manifest.json")
    if not os.path.exists(manifest_path):
        return None
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    total = sum(
        section.get("duration", 0)
        for section in manifest.get("sections", {}).values()
    )
    return _format_duration(total)


def _read_demo_metadata(demo_dir, demo_id):
    """Read the single-source card metadata from demos/<id>/demo.json."""
    demo_json = os.path.join(demo_dir, "demo.json")
    if not os.path.exists(demo_json):
        raise RuntimeError(
            f"Demo '{demo_id}' has a pipeline.py but no demo.json; "
            "add the card metadata in demos/<id>/demo.json"
        )
    with open(demo_json, encoding="utf-8") as f:
        return json.load(f)


def write_manifest(demos_dir=DEMOS_DIR):
    """
    Rewrite demos/index.json from every demos/*/demo.json, sorted by id.

    Runs on every generate_all.py run (but not --list), even when only some
    demos are generated. A demo folder with pipeline.py but no demo.json is an
    error.
    """
    entries = []
    for entry in os.listdir(demos_dir):
        demo_dir = os.path.join(demos_dir, entry)
        if not os.path.isdir(demo_dir):
            continue
        if not os.path.exists(os.path.join(demo_dir, "pipeline.py")):
            continue
        meta = _read_demo_metadata(demo_dir, entry)
        entries.append({
            "id": meta.get("id", entry),
            "title": meta.get("title", ""),
            "subtitle": meta.get("subtitle", ""),
            "description": meta.get("description", ""),
            "icon": meta.get("icon", ""),
            "tags": meta.get("tags", []),
            "duration": _demo_duration(demo_dir),
        })
    entries.sort(key=lambda e: e["id"])
    index_path = os.path.join(demos_dir, "index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    return entries


# ═══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════════════════════════


def _tanat_version():
    """Return the installed tanat version, or None if not installed."""
    try:
        return metadata.version("tanat")
    except metadata.PackageNotFoundError:
        return None


def _save_figures(block_id, outputs_dir):
    """Save the single figure open after a block, else None. Error if >1."""
    import matplotlib.pyplot as plt

    open_figures = plt.get_fignums()
    if not open_figures:
        return None
    if len(open_figures) > 1:
        for num in open_figures:
            plt.close(num)
        raise RuntimeError(
            f"Block '{block_id}' left {len(open_figures)} figures open, "
            f"expected at most 1"
        )
    fig = plt.figure(open_figures[0])
    path = os.path.join(outputs_dir, f"{block_id}.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return f"{block_id}.png"


def run_demo(demo_id, demos_dir=DEMOS_DIR):
    """
    Run one demo's pipeline.py block by block and write outputs.json.

    Returns True on success, False if any block raised an exception.
    """
    demo_dir = os.path.join(demos_dir, demo_id)
    pipeline_path = os.path.join(demo_dir, "pipeline.py")

    if not os.path.exists(pipeline_path):
        return False

    outputs_dir = os.path.join(demo_dir, "outputs")
    os.makedirs(outputs_dir, exist_ok=True)

    with open(pipeline_path, encoding="utf-8") as f:
        source = f.read()

    preamble, blocks = parse_blocks(source)
    namespace = {}

    previous_cwd = os.getcwd()
    os.chdir(SCRIPT_DIR)
    try:
        try:
            if preamble.strip():
                exec(compile(preamble, pipeline_path, "exec"), namespace)
        except Exception:
            print(f"  [{demo_id}] Block 'preamble' raised an exception:")
            traceback.print_exc()
            return False

        results = []
        for block_id, start_lineno, code in blocks:
            stdout_buf = io.StringIO()
            try:
                padded = ("\n" * (start_lineno - 1)) + code if start_lineno else code
                with contextlib.redirect_stdout(stdout_buf):
                    exec(compile(padded, pipeline_path, "exec"), namespace)

                output = stdout_buf.getvalue()
                if output.endswith("\n"):
                    output = output[:-1]
                if output == "":
                    output = None

                figure = _save_figures(block_id, outputs_dir)
            except Exception:
                print(f"  [{demo_id}] Block '{block_id}' raised an exception:")
                traceback.print_exc()
                return False

            results.append(
                {"id": block_id, "code": code, "output": output, "figure": figure}
            )
    finally:
        os.chdir(previous_cwd)

    outputs = {
        "demo": demo_id,
        "tanat_version": _tanat_version(),
        "blocks": results,
    }

    with open(os.path.join(outputs_dir, "outputs.json"), "w", encoding="utf-8") as f:
        json.dump(outputs, f, indent=2, ensure_ascii=False)

    return True


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(
        description="TanaT Demo - Master Output Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python generate_all.py                    # Generate all demos
    python generate_all.py mimic-clustering   # Generate specific demo
    python generate_all.py --list             # List available demos
        """,
    )
    parser.add_argument(
        "demos",
        nargs="*",
        help="Specific demo(s) to generate. If empty, generates all.",
    )
    parser.add_argument(
        "--list", "-l", action="store_true", help="List available demos and exit"
    )

    args = parser.parse_args()

    available_demos = discover_demos()

    if not available_demos:
        print("No demos found in demos/ directory.")
        print("Each demo should have a pipeline.py file.")
        return 1

    if args.list:
        print("Available demos:")
        for demo_id in sorted(available_demos):
            print(f"  - {demo_id}")
        return 0

    if args.demos:
        demos_to_run = []
        for demo_id in args.demos:
            if demo_id in available_demos:
                demos_to_run.append(demo_id)
            else:
                print(f"Warning: Demo '{demo_id}' not found, skipping.")

        if not demos_to_run:
            print("No valid demos specified.")
            return 1
    else:
        demos_to_run = sorted(available_demos)

    print("=" * 60)
    print("TanaT Demo - Generating Outputs")
    print("=" * 60)
    print(f"\nDemos to generate: {', '.join(demos_to_run)}\n")

    results = {}

    for demo_id in demos_to_run:
        print(f"\n[{demo_id}]")
        print("-" * 40)

        try:
            results[demo_id] = run_demo(demo_id)
        except Exception as e:
            print(f"  [ERROR] Generation failed: {e}")
            results[demo_id] = False

    # Rewrite demos/index.json from every demos/*/demo.json (single source of
    # truth for the landing), even when only some demos were generated.
    write_manifest()

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    success_count = sum(1 for s in results.values() if s)
    total_count = len(results)

    for demo_id, success in sorted(results.items()):
        status = "✓" if success else "✗"
        print(f"  {status} {demo_id}")

    print(f"\n{success_count}/{total_count} demos generated successfully")

    return 0 if success_count == total_count else 1


if __name__ == "__main__":
    sys.exit(main())
