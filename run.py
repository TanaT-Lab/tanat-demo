#!/usr/bin/env python3
"""
TanaT Demo Launcher

This script:
1. Checks if outputs (figures + outputs.json) exist
2. Generates them if needed
3. Starts the HTTP server
4. Opens the browser (optional)
"""

import os
import sys
import subprocess
import webbrowser
import time
import socket
import argparse

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PORT = 8503

# Check for demo outputs - each demo has its own outputs folder
DEMOS_DIR = os.path.join(SCRIPT_DIR, "demos")

# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════


def check_outputs_exist():
    """Check if all demos have their outputs generated."""
    missing = []

    if not os.path.exists(DEMOS_DIR):
        return ["demos/ directory not found"]

    for demo_id in os.listdir(DEMOS_DIR):
        demo_path = os.path.join(DEMOS_DIR, demo_id)
        if not os.path.isdir(demo_path):
            continue

        # Check if demo has a pipeline.py (meaning it needs outputs)
        if os.path.exists(os.path.join(demo_path, "pipeline.py")):
            outputs_dir = os.path.join(demo_path, "outputs")
            if not os.path.exists(outputs_dir) or not os.listdir(outputs_dir):
                missing.append(f"demos/{demo_id}/outputs/")

    return missing


def generate_outputs():
    """Run generate_all.py to create outputs for all demos."""
    print("Generating outputs for all demos...")
    script = os.path.join(SCRIPT_DIR, "generate_all.py")

    # Use the same Python interpreter
    result = subprocess.run(
        [sys.executable, script], cwd=SCRIPT_DIR, capture_output=False
    )

    if result.returncode != 0:
        print("Failed to generate outputs!")
        return False
    return True


def is_port_in_use(port):
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def find_available_port(start_port):
    """Find an available port starting from start_port."""
    port = start_port
    while is_port_in_use(port):
        print(f"   Port {port} in use, trying {port + 1}...")
        port += 1
        if port > start_port + 100:
            raise RuntimeError("No available port found")
    return port


def start_server(port, no_browser=False):
    """Start Python HTTP server."""
    url = f"http://localhost:{port}"

    print(f"\nStarting server on {url}")
    print("   Press Ctrl+C to stop\n")
    print("=" * 50)

    # Open browser after a short delay
    if not no_browser:

        def open_browser():
            time.sleep(0.5)
            webbrowser.open(url)

        import threading

        threading.Thread(target=open_browser, daemon=True).start()

    # Start server (this blocks)
    try:
        subprocess.run([sys.executable, "-m", "http.server", str(port)], cwd=SCRIPT_DIR)
    except KeyboardInterrupt:
        print("\n\nServer stopped")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(
        description="TanaT Demo Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py              # Check outputs, generate if needed, start server
  python run.py --port 9000  # Use custom port
  python run.py --regenerate # Force regenerate all outputs
  python run.py --no-browser # Don't open browser automatically
        """,
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to run server on (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--regenerate", "-r", action="store_true", help="Force regenerate all outputs"
    )
    parser.add_argument(
        "--no-browser",
        "-n",
        action="store_true",
        help="Don't open browser automatically",
    )
    parser.add_argument(
        "--check-only",
        "-c",
        action="store_true",
        help="Only check/generate outputs, don't start server",
    )

    args = parser.parse_args()

    print("\n" + "=" * 50)
    print("  TanaT Demo")
    print("=" * 50)

    # Check outputs
    missing = check_outputs_exist()

    if args.regenerate or missing:
        if missing:
            print(f"\nMissing files: {', '.join(missing)}")
        else:
            print("\nRegenerating outputs (--regenerate flag)")

        if not generate_outputs():
            sys.exit(1)
    else:
        print("\n✓ All demo outputs exist")

    if args.check_only:
        print("\n✓ Check complete (--check-only)")
        return

    # Find available port
    port = find_available_port(args.port)

    # Start server
    start_server(port, no_browser=args.no_browser)


if __name__ == "__main__":
    main()
