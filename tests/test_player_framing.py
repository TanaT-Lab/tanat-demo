"""Playwright test: after each station finishes displaying, its newest output is
fully framed -- its bounding box lies entirely between the fixed header and the
bottom of the viewport -- whatever the screen size / zoom.

Skips when playwright is not installed (like the other player tests), so the
plain pytest run still passes.
"""

import functools
import http.server
import os
import threading

import pytest

pytest.importorskip("playwright")

from playwright.sync_api import sync_playwright  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8723

# 1280x720 at 125% zoom ~= 1024x576, so the third size also covers a zoom case.
VIEWPORTS = [(1920, 1080), (1280, 720), (1024, 576)]


@pytest.fixture(scope="module")
def server():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=REPO)
    handler.log_message = lambda *a: None
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd
    httpd.shutdown()


def wait_for_station_complete(page, s, timeout=20000):
    page.wait_for_function(
        f"currentStation === {s} && isDisplayComplete === true", timeout=timeout
    )
    # Give any figure images time to decode so the layout is stable.
    page.wait_for_function(
        f"""(() => {{
            const imgs = document.querySelectorAll('#station-{s} img');
            return Array.from(imgs).every(i => i.complete && i.naturalWidth > 0);
        }})()""",
        timeout=10000,
    )
    page.wait_for_timeout(300)


def newest_output_box(page, s):
    return page.evaluate(
        f"""(() => {{
            const st = document.getElementById('station-{s}');
            const outs = Array.from(st.querySelectorAll('.terminal-output, .figure-output'))
                .filter(o => o.style.visibility !== 'hidden');
            const newest = outs[outs.length - 1];
            const r = newest.getBoundingClientRect();
            const header = document.querySelector('.main-header');
            const headerBottom = header && header.getBoundingClientRect().height > 0
                ? header.getBoundingClientRect().bottom : 0;
            return {{
                id: newest.id,
                top: r.top,
                bottom: r.bottom,
                headerBottom: headerBottom,
                innerHeight: window.innerHeight,
            }};
        }})()"""
    )


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_newest_output_framed_after_each_station(server, viewport):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--autoplay-policy=no-user-gesture-required"]
        )
        pg = browser.new_page(viewport={"width": viewport[0], "height": viewport[1]})
        pg.goto(f"http://127.0.0.1:{PORT}/player.html?demo=mimic-clustering")
        pg.wait_for_selector("#transition-start-btn", state="visible", timeout=5000)

        # Speed up the player's internal sleeps so typing completes quickly while
        # still running the full goToStation flow, including its scroll framing.
        pg.evaluate(
            "() => { window.sleep = (ms) => new Promise(r => setTimeout(r, 0)); }"
        )

        # Enter the demo; goToStation(1) starts shortly after.
        pg.click("#transition-start-btn")
        pg.wait_for_timeout(500)
        pg.click("#global-next-btn")

        n = pg.evaluate("demoConfig.stations.length")
        for s in range(1, n + 1):
            wait_for_station_complete(pg, s)
            box = newest_output_box(pg, s)
            assert box["top"] >= box["headerBottom"], (
                f"station {s} newest output {box['id']} top {box['top']} is above "
                f"the header bottom {box['headerBottom']} at {viewport}"
            )
            assert box["bottom"] <= box["innerHeight"], (
                f"station {s} newest output {box['id']} bottom {box['bottom']} is "
                f"below the viewport bottom {box['innerHeight']} at {viewport}"
            )
            if s < n:
                pg.click("#global-next-btn")

        browser.close()
