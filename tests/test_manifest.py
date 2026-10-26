"""Tests for the demo manifest demos/index.json and the landing page.

Unit tests of the manifest writing use a tmp_path demos dir and need no TanaT.
The Playwright landing test (skipped via importorskip when playwright is not
installed) serves the real repo and checks the landing renders one card per
index.json entry and that clicking one opens the player with the title from
demo.json.
"""

import functools
import http.server
import json
import os
import sys
import threading

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import generate_all  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ═══════════════════════════════════════════════════════════════════════════════
# UNIT TESTS
# ═══════════════════════════════════════════════════════════════════════════════


def make_demo(demos_dir, demo_id, pipeline=True, demo_json=None):
    demo_dir = demos_dir / demo_id
    demo_dir.mkdir(parents=True, exist_ok=True)
    if pipeline:
        (demo_dir / "pipeline.py").write_text(
            "# %% 1a\nprint('ok')\n", encoding="utf-8"
        )
    if demo_json is not None:
        (demo_dir / "demo.json").write_text(
            json.dumps(demo_json), encoding="utf-8"
        )
    return demo_dir


def make_audio_manifest(demo_dir, sections):
    audio_dir = demo_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    (audio_dir / "manifest.json").write_text(
        json.dumps({"voice": "af_heart", "sections": sections}),
        encoding="utf-8",
    )


def test_manifest_writes_one_entry_per_demo_sorted_by_id(tmp_path):
    make_demo(
        tmp_path, "b-demo",
        demo_json={"id": "b-demo", "title": "B", "subtitle": "s",
                   "description": "d", "icon": "i", "tags": ["t"]},
    )
    make_demo(
        tmp_path, "a-demo",
        demo_json={"id": "a-demo", "title": "A", "subtitle": "s",
                   "description": "d", "icon": "i", "tags": []},
    )
    entries = generate_all.write_manifest(demos_dir=str(tmp_path))
    assert [e["id"] for e in entries] == ["a-demo", "b-demo"]
    assert entries[0]["title"] == "A"
    # No audio manifest -> duration is None
    assert entries[0]["duration"] is None


def test_manifest_duration_rounds_up_from_audio_manifest(tmp_path):
    demo_dir = make_demo(
        tmp_path, "a-demo",
        demo_json={"id": "a-demo", "title": "A", "subtitle": "s",
                   "description": "d", "icon": "i", "tags": []},
    )
    # 30 + 210 = 240s = exactly 4 min; plus a demo with a fractional total.
    make_audio_manifest(demo_dir, {"intro": {"duration": 30.0},
                                   "step1": {"duration": 210.0}})
    entries = generate_all.write_manifest(demos_dir=str(tmp_path))
    assert entries[0]["duration"] == "~4 min"

    demo_dir2 = make_demo(
        tmp_path, "b-demo",
        demo_json={"id": "b-demo", "title": "B", "subtitle": "s",
                   "description": "d", "icon": "i", "tags": []},
    )
    make_audio_manifest(demo_dir2, {"intro": {"duration": 1.0}})
    entries = generate_all.write_manifest(demos_dir=str(tmp_path))
    by_id = {e["id"]: e for e in entries}
    assert by_id["b-demo"]["duration"] == "~1 min"


def test_manifest_index_json_written_to_demos_dir(tmp_path):
    make_demo(
        tmp_path, "a-demo",
        demo_json={"id": "a-demo", "title": "A", "subtitle": "s",
                   "description": "d", "icon": "i", "tags": []},
    )
    generate_all.write_manifest(demos_dir=str(tmp_path))
    index_path = tmp_path / "index.json"
    assert index_path.exists()
    data = json.loads(index_path.read_text(encoding="utf-8"))
    assert data[0]["id"] == "a-demo"


def test_manifest_missing_demo_json_is_error(tmp_path):
    make_demo(tmp_path, "a-demo", pipeline=True, demo_json=None)
    with pytest.raises(RuntimeError, match="no demo.json"):
        generate_all.write_manifest(demos_dir=str(tmp_path))


# ═══════════════════════════════════════════════════════════════════════════════
# PLAYWRIGHT LANDING TEST
# ═══════════════════════════════════════════════════════════════════════════════

LANDING_PORT = 8730
_INDEX = os.path.join("demos", "index.json")


@pytest.fixture(scope="module")
def landing_server():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=REPO)
    handler.log_message = lambda *a: None
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", LANDING_PORT), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd
    httpd.shutdown()


def _demo_ids_and_titles():
    demos_dir = os.path.join(REPO, "demos")
    ids = []
    titles = {}
    for entry in sorted(os.listdir(demos_dir)):
        demo_dir = os.path.join(demos_dir, entry)
        demo_json = os.path.join(demo_dir, "demo.json")
        if not os.path.isdir(demo_dir) or not os.path.exists(demo_json):
            continue
        with open(demo_json, encoding="utf-8") as f:
            meta = json.load(f)
        ids.append(meta.get("id", entry))
        titles[meta.get("id", entry)] = meta["title"]
    return ids, titles


@pytest.fixture
def landing_index(landing_server):
    """Build the real demos/index.json (git-ignored build output, idempotent)."""
    _, titles = _demo_ids_and_titles()
    generate_all.write_manifest(demos_dir=os.path.join(REPO, "demos"))
    with open(os.path.join(REPO, _INDEX), encoding="utf-8") as f:
        entries = json.load(f)
    yield entries, titles


def test_landing_shows_one_card_per_entry_and_opens_player(
    landing_server, landing_index
):
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    entries, titles = landing_index
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--autoplay-policy=no-user-gesture-required"]
        )
        page = browser.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"http://127.0.0.1:{LANDING_PORT}/index.html")
        page.wait_for_selector(".demo-card", timeout=5000)
        cards = page.locator(".demo-card")
        assert cards.count() == len(entries)

        # Click the first card and expect navigation to the player with the
        # title taken from demo.json.
        first_id = entries[0]["id"]
        cards.first.click()
        page.wait_for_url(f"**/player.html?demo={first_id}", timeout=5000)
        page.wait_for_function(
            "document.getElementById('header-title').textContent !== 'Demo Title'",
            timeout=8000,
        )
        assert page.locator("#header-title").inner_text() == titles[first_id]
        assert not errors, f"JS errors: {errors}"
        browser.close()
