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


SAMPLER = """
(() => {
  window.__samples = [];
  window.__readyAt = null;
  const origLog = console.log;
  console.log = function (...args) {
    if (window.__readyAt === null && args[0] === '=== Player Ready ===') {
      window.__readyAt = performance.now();
    }
    return origLog.apply(this, args);
  };
  const tick = () => {
    const el = document.getElementById('transition-actions');
    let visible = false;
    if (el) {
      const cs = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      visible = cs.display !== 'none' && parseFloat(cs.opacity) > 0
        && r.width > 0 && r.height > 0;
    }
    window.__samples.push([performance.now(), visible]);
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
})();
"""


def test_buttons_never_visible_before_ready(server):
    """The Back / Start buttons must not flash while the config is still
    loading: they are hidden from the very first frame (the critical CSS must
    not be overridden by core/styles.css), shown once when the demo is ready,
    and never go visible -> hidden -> visible."""
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        pg = browser.new_page()
        pg.add_init_script(SAMPLER)

        def slow_config(route):
            # Hold config.js ~1 s so the window before the script hides/shows
            # the buttons is wide and deterministic.
            time.sleep(1.0)
            route.continue_()

        pg.route("**/mimic-clustering/config.js", slow_config)
        try:
            pg.goto(
                f"http://127.0.0.1:{PORT}/player.html?demo=mimic-clustering",
                wait_until="domcontentloaded",
            )
            pg.wait_for_function("window.__readyAt !== null", timeout=10000)
            # Let the fadeIn finish and a few more frames be sampled.
            pg.wait_for_timeout(800)
            ready_at = pg.evaluate("window.__readyAt")
            samples = pg.evaluate("window.__samples")
        finally:
            browser.close()

    assert len(samples) > 20, "sampler produced too few frames"
    early = [t for t, v in samples if v and t < ready_at]
    assert not early, (
        f"buttons visible before ready: first at {early[0]:.0f} ms, "
        f"{len(early)} frames, ready at {ready_at:.0f} ms"
    )
    assert samples[-1][1], "buttons not visible after ready"

    states = [v for _, v in samples]
    transitions = sum(1 for a, b in zip(states, states[1:]) if a != b)
    assert transitions == 1, f"visibility toggled {transitions} times, expected 1"
