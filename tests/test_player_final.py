"""Playwright test: the final view (notebook left, workflow summary right)."""

import functools
import http.server
import os
import re
import threading

import pytest

pytest.importorskip("playwright")

from playwright.sync_api import sync_playwright  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8726


@pytest.fixture(scope="module")
def server():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=REPO)
    handler.log_message = lambda *a: None
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield httpd
    httpd.shutdown()


def open_final(browser, w, h):
    pg = browser.new_page(viewport={"width": w, "height": h})
    pg.goto(f"http://127.0.0.1:{PORT}/player.html?demo=mimic-clustering")
    pg.wait_for_selector("#transition-start-btn", state="visible", timeout=5000)
    pg.evaluate("() => { window.sleep = (ms) => new Promise(r => setTimeout(r, 0)); }")
    pg.click("#transition-start-btn")
    pg.wait_for_timeout(500)
    pg.click("#global-next-btn")
    n = pg.evaluate("demoConfig.stations.length")
    for s in range(1, n + 1):
        pg.wait_for_function(
            f"currentStation === {s} && isDisplayComplete === true", timeout=20000
        )
        pg.click("#global-next-btn")
    pg.wait_for_selector("#final-view", state="visible", timeout=5000)
    pg.wait_for_function(
        "Array.from(document.querySelectorAll('#final-view img')).every(i => i.complete && i.naturalWidth > 0)",
        timeout=10000,
    )
    pg.wait_for_timeout(1500)
    return pg


@pytest.mark.parametrize("viewport", [(1920, 1080), (1280, 720)])
def test_final_view_desktop(server, viewport):
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        pg = open_final(browser, *viewport)

        n_blocks = pg.evaluate(
            "demoConfig.stations.reduce((a, s) => a + s.blocks.length, 0)"
        )
        gutters = pg.eval_on_selector_all(
            "#fv-notebook .fv-gutter", "els => els.map(e => e.textContent.trim())"
        )
        assert gutters == [f"In [{i}]:" for i in range(1, n_blocks + 1)]

        font = pg.evaluate(
            "parseFloat(getComputedStyle(document.querySelector('.fv-code code')).fontSize)"
        )
        assert font >= 13

        side = pg.evaluate(
            """(() => { const r = document.getElementById('fv-side').getBoundingClientRect();
            const kids = Array.from(document.getElementById('fv-side').children).map(
                c => c.getBoundingClientRect());
            return {top: r.top, bottom: r.bottom, left: r.left, right: r.right,
                    kidsBottom: Math.max(...kids.map(k => k.bottom)),
                    w: innerWidth, h: innerHeight,
                    pageScroll: document.documentElement.scrollHeight > innerHeight}; })()"""
        )
        assert side["top"] >= 0 and side["right"] <= side["w"]
        assert side["bottom"] <= side["h"] and side["kidsBottom"] <= side["h"]
        assert not side["pageScroll"]

        text = pg.inner_text(".fv-takeaways")
        assert "{lines}" not in text
        assert re.search(r"\d+ lines of code", text)

        pg.click('.fv-node[data-step="5"]')
        pg.wait_for_timeout(1000)
        box = pg.evaluate(
            """(() => { const p = document.getElementById('fv-notebook').getBoundingClientRect();
            const h = document.querySelector('#fv-step-5 .fv-step-heading').getBoundingClientRect();
            return {pt: p.top, pb: p.bottom, ht: h.top, hb: h.bottom}; })()"""
        )
        assert box["ht"] >= box["pt"] - 1 and box["hb"] <= box["pb"]

        # Prev goes back to station 6 with the stations restored.
        pg.click("#global-prev-btn")
        pg.wait_for_timeout(500)
        assert not pg.is_visible("#final-view")
        assert pg.evaluate("currentStation") == 6
        assert pg.is_visible("#station-6")
        browser.close()


def test_final_view_stacks_when_narrow(server):
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        pg = open_final(browser, 1024, 576)
        pos = pg.evaluate(
            """(() => ({side: document.getElementById('fv-side').getBoundingClientRect(),
            nb: document.getElementById('fv-notebook').getBoundingClientRect()}))()"""
        )
        assert pos["side"]["bottom"] <= pos["nb"]["top"] + 1
        assert pg.evaluate("document.documentElement.scrollHeight > innerHeight")
        browser.close()
