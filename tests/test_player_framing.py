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
import time

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


def goto_station(page, s):
    """From the transition screen, drive the player to station `s` (1-based)."""
    pg = page
    pg.wait_for_selector("#transition-start-btn", state="visible", timeout=5000)
    pg.evaluate(
        "() => { window.sleep = (ms) => new Promise(r => setTimeout(r, 0)); }"
    )
    pg.click("#transition-start-btn")
    pg.wait_for_timeout(500)
    pg.click("#global-next-btn")
    for _ in range(s - 1):
        pg.wait_for_function("currentStation >= 1")
        pg.click("#global-next-btn")
    wait_for_station_complete(pg, s)


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


def _fig_box(page, block_id):
    return page.evaluate(
        f"""(() => {{
            const el = document.getElementById('output-{block_id}');
            const r = el.getBoundingClientRect();
            const header = document.querySelector('.main-header');
            const headerBottom = header && header.getBoundingClientRect().height > 0
                ? header.getBoundingClientRect().bottom : 0;
            return {{ left: r.left, right: r.right, top: r.top, bottom: r.bottom,
                      headerBottom: headerBottom, innerHeight: window.innerHeight }};
        }})()"""
    )


@pytest.mark.parametrize("viewport", [(1280, 720), (1024, 576)])
def test_station4_figures_side_by_side_then_stack(server, viewport):
    """Station 4's two timeline figures (4a before, 4c after) sit side by side,
    bottom-aligned, at 1280x720 and stack into one column at the narrowest
    viewport (1024x576)."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--autoplay-policy=no-user-gesture-required"]
        )
        pg = browser.new_page(viewport={"width": viewport[0], "height": viewport[1]})
        pg.goto(f"http://127.0.0.1:{PORT}/player.html?demo=mimic-clustering")
        goto_station(pg, 4)

        a = _fig_box(pg, "4a")
        c = _fig_box(pg, "4c")

        if viewport == (1280, 720):
            # Side by side: 4c entirely to the right of 4a...
            assert c["left"] >= a["right"], (
                f"4c left {c['left']} must be >= 4a right {a['right']}"
            )
            # ...and the two figures bottom-aligned (tops within a few px).
            assert abs(a["top"] - c["top"]) <= 5, (
                f"figure tops differ too much: 4a {a['top']} vs 4c {c['top']}"
            )
            # Both fully visible between header and viewport bottom.
            assert a["top"] >= a["headerBottom"], (
                f"4a top {a['top']} above header bottom {a['headerBottom']}"
            )
            assert c["bottom"] <= c["innerHeight"], (
                f"4c bottom {c['bottom']} below viewport {c['innerHeight']}"
            )
        else:
            # Stacked: both figures start at the same left edge.
            assert a["left"] == c["left"], (
                f"4a left {a['left']} != 4c left {c['left']} at {viewport}"
            )

        browser.close()


# ═══════════════════════════════════════════════════════════════════════════════
# Reading-line framing while a station types
# ═══════════════════════════════════════════════════════════════════════════════
# While stations 1, 3 and 5 type (real typing, sampled every ~250 ms): once the
# page has started following, the bottom of the code being typed stays between
# framingBounds().top and the reading line + 1 line height (~30 px), never below
# the viewport; window.scrollY never decreases within a block. At each step
# start the station header's top is within 40 px of framingBounds().top.

TYPING_STATIONS = [1, 3, 5]


def _real_sleep(page):
    page.evaluate(
        "() => { window.sleep = (ms) => new Promise(r => setTimeout(r, ms)); }"
    )


def _instant_sleep(page):
    page.evaluate(
        "() => { window.sleep = (ms) => new Promise(r => setTimeout(r, 0)); }"
    )


def _typing_sample(page, s):
    """Sample the code element currently being typed in station `s` (the lowest
    non-empty code block's bottom), its scrollY, the framing bounds and the
    station header's top."""
    return page.evaluate(
        f"""(() => {{
            const st = document.getElementById('station-{s}');
            const codes = Array.from(st.querySelectorAll('pre code'));
            let best = null, bestBottom = -Infinity;
            for (const c of codes) {{
                if (!c.textContent.trim()) continue;
                const b = c.getBoundingClientRect().bottom;
                if (b > bestBottom) {{ bestBottom = b; best = c; }}
            }}
            const header = document.querySelector('.main-header');
            const headerBottom = header && header.getBoundingClientRect().height > 0
                ? header.getBoundingClientRect().bottom : 0;
            let bottom = window.innerHeight;
            if (window.matchMedia('(max-width: 767px)').matches) {{
                const nav = document.querySelector('.global-nav-controls');
                if (nav && nav.getBoundingClientRect().height > 0) {{
                    bottom = nav.getBoundingClientRect().top;
                }}
            }}
            const sHdr = st.querySelector('.station-header');
            return {{
                id: best ? best.id : null,
                bottom: bestBottom,
                scrollY: window.scrollY,
                boundsTop: headerBottom,
                boundsBottom: bottom,
                headerTop: sHdr ? sHdr.getBoundingClientRect().top : null,
            }};
        }})()"""
    )


def _assert_reading_line_while_typing(page, s, viewport):
    """Sample every ~250 ms while station `s` types and check the reading-line
    invariant and that scrollY never decreases within a block."""
    per_block = {}
    max_header_top = None
    bounds_top = None
    while page.evaluate(f"currentStation === {s} && !isDisplayComplete"):
        sample = _typing_sample(page, s)
        if sample["id"]:
            bottom = sample["bottom"]
            ft = sample["boundsTop"]
            fb = sample["boundsBottom"]
            reading_line = ft + 0.55 * (fb - ft)

            # The reading-line follow only ever scrolls the page down, so the
            # station header's top only moves up (smaller) as typing goes on.
            # Its step-start position (top of the visible area) is therefore the
            # largest top observed -- the first samples, before follow has scrolled
            # the header off-screen, sit closest to it.
            if sample["headerTop"] is not None:
                if max_header_top is None or sample["headerTop"] > max_header_top:
                    max_header_top = sample["headerTop"]
                bounds_top = ft

            blk = per_block.setdefault(
                sample["id"], {"started": False, "prevY": None, "below_since": None}
            )
            if blk["started"] and blk["prevY"] is not None:
                assert sample["scrollY"] >= blk["prevY"] - 0.5, (
                    f"window.scrollY decreased in station {s} block {sample['id']} "
                    f"({sample['scrollY']} < {blk['prevY']}) at {viewport}"
                )
            if bottom >= reading_line:
                in_band = ft <= bottom <= reading_line + 30
                if in_band:
                    blk["started"] = True
                    blk["below_since"] = None
                elif not blk["started"]:
                    # A block that starts typing right under a tall output is
                    # already below the line: the page is still catching up.
                    # That is allowed, but only for a bounded time.
                    now = time.monotonic()
                    if blk["below_since"] is None:
                        blk["below_since"] = now
                    assert now - blk["below_since"] <= 1.5, (
                        f"station {s} block {sample['id']} bottom {bottom} still "
                        f"outside [{ft}, {reading_line + 30}] (reading line "
                        f"{reading_line}) 1.5 s after crossing it at {viewport}"
                    )
                else:
                    raise AssertionError(
                        f"station {s} block {sample['id']} bottom {bottom} outside "
                        f"[{ft}, {reading_line + 30}] (reading line {reading_line}) "
                        f"at {viewport}"
                    )
                if blk["started"]:
                    assert bottom <= fb, (
                        f"station {s} block {sample['id']} bottom {bottom} below "
                        f"viewport bottom {fb} at {viewport}"
                    )
                    blk["prevY"] = sample["scrollY"]
        page.wait_for_timeout(250)
    assert max_header_top is not None, (
        f"station {s} never produced a typing sample at {viewport}"
    )
    assert abs(max_header_top - bounds_top) <= 40, (
        f"station {s} step-start header top {max_header_top} not within 40px of "
        f"framingBounds().top {bounds_top} at {viewport}"
    )


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_reading_line_while_typing(server, viewport):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--autoplay-policy=no-user-gesture-required"]
        )
        pg = browser.new_page(viewport={"width": viewport[0], "height": viewport[1]})
        pg.goto(f"http://127.0.0.1:{PORT}/player.html?demo=mimic-clustering")
        pg.wait_for_selector("#transition-start-btn", state="visible", timeout=5000)
        pg.click("#transition-start-btn")
        pg.wait_for_timeout(500)
        # The test drives the stations itself: without this, a narration that
        # ends between "station done" and the Next click auto-advances too, and
        # the click skips a station.
        pg.evaluate("audioElement.removeEventListener('ended', onAudioEnded)")
        pg.click("#global-next-btn")

        s = 1
        n = pg.evaluate("demoConfig.stations.length")
        while s <= n:
            pg.wait_for_function(
                f"currentStation === {s} && isDisplayComplete === true",
                timeout=240000,
            )
            nxt = s + 1
            if nxt > n:
                break
            target = nxt in TYPING_STATIONS
            if target:
                _real_sleep(pg)
            else:
                _instant_sleep(pg)
            pg.click("#global-next-btn")
            if target:
                pg.wait_for_function(
                    f"currentStation === {nxt} && isTyping === true && !isDisplayComplete",
                    timeout=10000,
                )
                _assert_reading_line_while_typing(pg, nxt, viewport)
            s = nxt

        browser.close()
