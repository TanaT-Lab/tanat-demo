#!/usr/bin/env python3
"""
TanaT Demo - Master Output Generator

This script discovers and runs all demo generation scripts.
Each demo folder should contain a generate.py file with a generate() function.

Usage:
    python generate_all.py              # Generate all demos
    python generate_all.py mimic-clustering  # Generate specific demo
    python generate_all.py --list       # List available demos
"""

import os
import sys
import importlib.util
import argparse

# ═══════════════════════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════════════════════

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEMOS_DIR = os.path.join(SCRIPT_DIR, "demos")

# ═══════════════════════════════════════════════════════════════════════════════
# DEMO DISCOVERY
# ═══════════════════════════════════════════════════════════════════════════════


def discover_demos():
    """
    Discover all demos that have a generate.py script.
    Returns a dict: {demo_id: path_to_generate.py}
    """
    demos = {}

    if not os.path.exists(DEMOS_DIR):
        return demos

    for entry in os.listdir(DEMOS_DIR):
        demo_path = os.path.join(DEMOS_DIR, entry)
        generate_script = os.path.join(demo_path, "generate.py")

        if os.path.isdir(demo_path) and os.path.exists(generate_script):
            demos[entry] = generate_script

    return demos


def load_demo_generator(demo_id, script_path):
    """
    Dynamically load a demo's generate.py and return its generate() function.
    """
    spec = importlib.util.spec_from_file_location(f"demo_{demo_id}", script_path)
    module = importlib.util.module_from_spec(spec)

    try:
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"  [ERROR] Failed to load {demo_id}/generate.py: {e}")
        return None

    if not hasattr(module, "generate"):
        print(f"  [ERROR] {demo_id}/generate.py has no generate() function")
        return None

    return module.generate


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

    # Discover demos
    available_demos = discover_demos()

    if not available_demos:
        print("No demos found in demos/ directory.")
        print("Each demo should have a generate.py file.")
        return 1

    # List mode
    if args.list:
        print("Available demos:")
        for demo_id in sorted(available_demos.keys()):
            print(f"  - {demo_id}")
        return 0

    # Determine which demos to generate
    if args.demos:
        demos_to_run = {}
        for demo_id in args.demos:
            if demo_id in available_demos:
                demos_to_run[demo_id] = available_demos[demo_id]
            else:
                print(f"Warning: Demo '{demo_id}' not found, skipping.")

        if not demos_to_run:
            print("No valid demos specified.")
            return 1
    else:
        demos_to_run = available_demos

    # Run generation
    print("=" * 60)
    print("TanaT Demo - Generating Outputs")
    print("=" * 60)
    print(f"\nDemos to generate: {', '.join(demos_to_run.keys())}\n")

    results = {}

    for demo_id, script_path in sorted(demos_to_run.items()):
        print(f"\n[{demo_id}]")
        print("-" * 40)

        generate_fn = load_demo_generator(demo_id, script_path)

        if generate_fn is None:
            results[demo_id] = False
            continue

        try:
            success = generate_fn()
            results[demo_id] = success
        except Exception as e:
            print(f"  [ERROR] Generation failed: {e}")
            results[demo_id] = False

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
