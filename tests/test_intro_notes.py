"""Playwright tests: intro notes are timed from the narration anchors.

Notes in config.js use `at: '<anchor>'` (+ optional `delay`); player.js resolves
them from audio/manifest.json. The real files are never modified: the failure
cases rewrite config.js / manifest.json on the fly through Playwright routes.

The plain pytest run (without playwright installed) skips these tests.
"""

import functools
import http.server
import json
import os
import threading

import pytest

pytest.importorskip("playwright")

from playwright.sync_api import sync_playwright  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(REPO, "demos", "mimic-clustering")
PORT = 8723
URL = f"http://127.0.0.1:{PORT}/player.html?demo=mimic-clustering"


@pytest.fixture(scope="module")
def server():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=REPO)
    handler.log_message = lambda *a: None
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd
    httpd.shutdown()


@pytest.fixture
def browser(server):
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        yield b
        b.close()


# Records, for each element added to the notepad, the audio time seen at the
# next animation frame (the player itself polls on animation frames).
OBSERVER = """
window.__seen = [];
(function poll() {
  const pad = document.getElementById('intro-notepad');
  const a = document.getElementById('demo-audio');
  if (pad && a)
    while (window.__seen.length < pad.children.length)
      window.__seen.push(a.currentTime);
  requestAnimationFrame(poll);
})();
"""


def test_intro_notes_follow_resolved_anchor_times(browser):
    page = browser.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.add_init_script(OBSERVER)
    page.goto(URL)
    page.wait_for_selector("#transition-start-btn", state="visible", timeout=5000)

    # Resolved note times, in the order the player will show them.
    notes = page.evaluate("DEMO_CONFIG.intro.notes.map(n => ({time: n.time, type: n.type, at: n.at || null, id: n.id || null}))")
    assert notes and all(isinstance(n["time"], (int, float)) for n in notes)
    assert [n["time"] for n in notes] == sorted(n["time"] for n in notes)

    # Every `at` is an anchor of the real manifest; the time is anchor + delay.
    with open(os.path.join(DEMO, "audio", "manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    anchors = manifest["sections"]["intro"]["anchors"]
    duration = manifest["sections"]["intro"]["duration"]
    raw = page.evaluate("DEMO_CONFIG.intro.notes.filter(n => n.at).map(n => [n.at, n.delay || 0, n.time])")
    assert raw
    for at, delay, time in raw:
        assert time == pytest.approx(anchors[at] + delay)
        assert time < duration

    page.click("#transition-start-btn")
    page.evaluate(
        "document.getElementById('demo-audio').playbackRate = 8"
    )
    page.wait_for_function(
        f"document.getElementById('intro-notepad').children.length === {len(notes)}",
        timeout=30000,
    )

    seen = page.evaluate("window.__seen")
    assert len(seen) == len(notes)
    for note, t in zip(notes, seen):
        # shown once the audio reached its time, and not long after (rate 8)
        assert t >= note["time"] - 0.05, (note, t)
        assert t <= note["time"] + 3, (note, t)
    assert seen == sorted(seen)

    # the two SVG visualizations appeared, once each
    assert page.locator("#intro-notepad .sequence-viz-container").count() == 1
    assert page.locator("#intro-notepad .workflow-viz-container").count() == 1
    svg_order = page.evaluate(
        "[...document.querySelectorAll('#intro-notepad > *')]"
        ".map(e => e.querySelector('.sequence-viz-container') ? 'seq' : "
        "e.querySelector('.workflow-viz-container') ? 'wf' : null).filter(Boolean)"
    )
    assert svg_order == ["seq", "wf"]
    assert not errors, f"JS errors: {errors}"
    page.close()


def failed_to_load(page):
    page.wait_for_function(
        "document.getElementById('transition-text').textContent === 'Failed to load demo'",
        timeout=5000,
    )


def test_unknown_anchor_in_config_fails_visibly(browser):
    with open(os.path.join(DEMO, "config.js"), encoding="utf-8") as f:
        config = f.read()
    bad = config + "\nDEMO_CONFIG.intro.notes.push({ at: 'no-such-anchor', type: 'bullet', content: 'x' });\n"

    page = browser.new_page()
    logs = []
    page.on("console", lambda m: logs.append(m.text))
    page.route(
        "**/demos/mimic-clustering/config.js",
        lambda route: route.fulfill(body=bad, content_type="application/javascript"),
    )
    page.goto(URL)
    failed_to_load(page)
    assert any("no-such-anchor" in line for line in logs), logs
    page.close()


def test_anchor_missing_from_manifest_fails_visibly(browser):
    with open(os.path.join(DEMO, "audio", "manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    anchors = manifest["sections"]["intro"]["anchors"]
    anchors.pop(next(iter(anchors)))

    page = browser.new_page()
    page.route(
        "**/demos/mimic-clustering/audio/manifest.json",
        lambda route: route.fulfill(body=json.dumps(manifest), content_type="application/json"),
    )
    page.goto(URL)
    failed_to_load(page)
    page.close()


def test_missing_manifest_fails_visibly(browser):
    page = browser.new_page()
    page.route(
        "**/demos/mimic-clustering/audio/manifest.json",
        lambda route: route.fulfill(status=404, body="nope"),
    )
    page.goto(URL)
    failed_to_load(page)
    page.close()
