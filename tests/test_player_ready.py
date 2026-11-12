"""Playwright test: the Start button appears only once the demo is really ready
-- the intro narration and every figure are preloaded -- never on a fixed
timer, and only after the transition screen has been up for at least 800 ms.

Skips when playwright is not installed (like the other player tests), so the
plain pytest run still passes.
"""

import functools
import http.server
import os
import threading
import time

import pytest

pytest.importorskip("playwright")

from playwright.sync_api import sync_playwright  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8724


@pytest.fixture(scope="module")
def server():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=REPO)
    handler.log_message = lambda *a: None
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd
    httpd.shutdown()


def _new_page(p, delay_audio_ms=0):
    browser = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
    pg = browser.new_page()
    if delay_audio_ms:
        def slow_audio(route):
            # Blocking handler: hold the intro mp3 for delay_audio_ms before
            # resuming it. This reliably delays the narration preload (the
            # async variant deadlocks in sync mode).
            time.sleep(delay_audio_ms / 1000.0)
            route.continue_()

        pg.route("**/intro.mp3", slow_audio)
    # wait_until="domcontentloaded" so goto returns before the delayed narration
    # finishes loading: with the default "load" the browser may block on the
    # <audio preload> and the button would already be visible by the time goto
    # returns.
    pg.goto(
        f"http://127.0.0.1:{PORT}/player.html?demo=mimic-clustering",
        wait_until="domcontentloaded",
    )
    return browser, pg


def test_start_button_without_delay_appears_within_3s(server):
    with sync_playwright() as p:
        browser, pg = _new_page(p)
        try:
            # No artificial delay: local assets load fast, so the buttons must
            # appear well within the 8 s safety net.
            pg.wait_for_selector("#transition-start-btn", state="visible", timeout=3000)
        finally:
            browser.close()


def test_start_button_waits_for_slow_intro_audio(server):
    with sync_playwright() as p:
        browser, pg = _new_page(p, delay_audio_ms=2000)
        try:
            # The narration mp3 is held for 2 s, so at 1.5 s the demo is still
            # not ready and the Start button must be hidden (instead of showing
            # on a fixed 1.5 s timer). time.sleep (not page.wait_for_timeout)
            # so the test thread itself advances while the route handler blocks.
            time.sleep(1.5)
            assert not pg.is_visible("#transition-start-btn")

            # Once the audio has actually loaded, the button must appear.
            pg.wait_for_selector("#transition-start-btn", state="visible", timeout=5000)
            assert pg.is_visible("#transition-start-btn")
        finally:
            browser.close()
