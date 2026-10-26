"""Playwright-based navigation tests for the demo player.

The plain pytest run (without playwright installed) skips these tests via
pytest.importorskip, so the rest of the suite still passes.
"""

import functools
import http.server
import os
import threading

import pytest

pytest.importorskip("playwright")

from playwright.sync_api import sync_playwright  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8721


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
def page(server):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--autoplay-policy=no-user-gesture-required"]
        )
        pg = browser.new_page()
        pg.goto(f"http://127.0.0.1:{PORT}/player.html?demo=mimic-clustering")
        pg.wait_for_selector("#transition-start-btn", state="visible", timeout=5000)
        yield pg
        browser.close()


def fast_forward_intro_audio(page, timeout=15000):
    """Speed up the intro audio so it ends quickly.

    Python's http.server does not honour HTTP Range requests, so the media is
    not seekable and `currentTime` cannot be used to jump to the end. Instead we
    crank the playback rate: the ~96 s intro ends in ~6 s at rate 16.
    """
    page.evaluate(
        "(() => { const a = document.getElementById('demo-audio');"
        "a.playbackRate = 16; })()"
    )
    page.wait_for_function(
        "(() => { const a = document.getElementById('demo-audio');"
        "return a.ended || a.currentTime >= a.duration; })()",
        timeout=timeout,
    )


def wait_for_layout(page, layout, timeout=8000):
    page.wait_for_function(
        f"document.body.classList.contains('layout-{layout}')", timeout=timeout
    )


def wait_for_current_station(page, station, timeout=8000):
    page.wait_for_function(
        f"currentStation === {station}", timeout=timeout
    )


def reveal_and_next(page, station):
    page.wait_for_selector(f"#station-{station}", state="visible", timeout=5000)
    page.click("#global-skip-btn")
    page.wait_for_timeout(300)
    code = page.inner_text(f"#station-{station} code")
    assert len(code) > 20
    page.click("#global-next-btn")
    page.wait_for_timeout(800)


def test_full_flow_transition_intro_stations_script(page):
    """Reference smoke scenario: transition -> intro -> stations -> full script."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    page.click("#transition-start-btn")
    page.wait_for_timeout(1500)
    assert page.is_visible("#intro-screen")
    page.wait_for_function(
        "document.querySelectorAll('#intro-notepad > *').length > 0", timeout=5000
    )

    page.click("#global-next-btn")
    page.wait_for_timeout(1500)
    assert page.evaluate("document.body.classList.contains('layout-demo')")

    n = page.evaluate("DEMO_CONFIG.stations.length")
    for s in range(1, n + 1):
        reveal_and_next(page, s)

    assert page.evaluate("document.body.classList.contains('full-script-view')")

    page.click("#global-prev-btn")
    page.wait_for_timeout(500)
    assert not page.evaluate("document.body.classList.contains('full-script-view')")

    assert not errors, f"JS errors: {errors}"


def test_bug_a_start_sets_intro_state_and_advances(page):
    """Start -> intro (currentStation==0); intro audio ends -> station 1."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    page.click("#transition-start-btn")
    page.wait_for_timeout(500)
    assert page.is_visible("#intro-screen")
    assert page.evaluate("currentStation") == 0

    fast_forward_intro_audio(page)

    wait_for_layout(page, "demo")
    wait_for_current_station(page, 1)
    page.wait_for_selector("#station-1", state="visible", timeout=5000)

    assert not errors, f"JS errors: {errors}"


def test_bug_b_prev_from_station1_resets_intro_and_advances_to_1(page):
    """Reach station 1, Prev -> intro (currentStation==0); audio ends -> station 1 (not 2)."""
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    page.click("#transition-start-btn")
    page.wait_for_timeout(500)
    page.click("#global-next-btn")
    page.wait_for_timeout(1500)
    assert page.evaluate("document.body.classList.contains('layout-demo')")
    page.wait_for_selector("#station-1", state="visible", timeout=5000)

    # Prev from station 1 -> back to intro
    page.click("#global-prev-btn")
    page.wait_for_timeout(500)
    assert page.is_visible("#intro-screen")
    assert page.evaluate("currentStation") == 0

    fast_forward_intro_audio(page)

    wait_for_layout(page, "demo")
    wait_for_current_station(page, 1)
    page.wait_for_selector("#station-1", state="visible", timeout=5000)

    assert not errors, f"JS errors: {errors}"
