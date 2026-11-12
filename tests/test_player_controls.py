"""Playwright tests for TASK-021: player controls in the header, the narration
progress bar, and the keyboard shortcuts.

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
PORT = 8725

DESKTOP_VIEWPORTS = [(1920, 1080), (1280, 720)]


@pytest.fixture(scope="module")
def server():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=REPO)
    handler.log_message = lambda *a: None
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd
    httpd.shutdown()


def _rect(page, selector):
    return page.evaluate(
        f"""(() => {{
            const el = document.querySelector({selector!r});
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return {{ left: r.left, right: r.right, top: r.top, bottom: r.bottom,
                      width: r.width, height: r.height }};
        }})()"""
    )


def enter_demo(page):
    """From the transition screen, Start, then Next into the demo layout."""
    page.wait_for_selector("#transition-start-btn", state="visible", timeout=5000)
    page.evaluate(
        "() => { window.sleep = (ms) => new Promise(r => setTimeout(r, 0)); }"
    )
    page.click("#transition-start-btn")
    page.wait_for_timeout(400)
    page.click("#global-next-btn")


def wait_station_complete(page, s, timeout=20000):
    page.wait_for_function(
        f"currentStation === {s} && isDisplayComplete === true", timeout=timeout
    )
    page.wait_for_timeout(200)


def inside(a, b):
    return a["left"] >= b["left"] and a["right"] <= b["right"] and \
        a["top"] >= b["top"] and a["bottom"] <= b["bottom"]


def intersects(a, b):
    return not (a["right"] <= b["left"] or a["left"] >= b["right"] or
                a["bottom"] <= b["top"] or a["top"] >= b["bottom"])


def controls_clear_of_code(page):
    """The controls live in the fixed header, which inherently overlaps content
    that has scrolled up behind it. The meaningful guarantee is that they never
    cover code the presenter can actually read: i.e. no code block's on-screen,
    below-the-header portion overlaps the controls."""
    return page.evaluate(
        """(() => {
            const c = document.getElementById('global-nav-controls').getBoundingClientRect();
            const header = document.querySelector('.main-header').getBoundingClientRect();
            const headerBottom = header.bottom;
            const blocks = document.querySelectorAll('.code-block');
            for (const b of blocks) {
                const r = b.getBoundingClientRect();
                if (r.width === 0 && r.height === 0) continue; // hidden station
                // The part of the block the user can actually read: below the
                // header and inside the viewport.
                const top = Math.max(r.top, headerBottom, 0);
                const bottom = Math.min(r.bottom, window.innerHeight);
                if (bottom <= top) continue; // no readable part on screen
                const hit = !(c.right <= r.left || c.left >= r.right ||
                              c.bottom <= top || c.top >= bottom);
                if (hit) return false;
            }
            return true;
        })()"""
    )


@pytest.mark.parametrize("viewport", DESKTOP_VIEWPORTS)
def test_controls_in_header_during_station1(server, viewport):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--autoplay-policy=no-user-gesture-required"]
        )
        pg = browser.new_page(viewport={"width": viewport[0], "height": viewport[1]})
        pg.goto(f"http://127.0.0.1:{PORT}/player.html?demo=mimic-clustering")
        enter_demo(pg)
        wait_station_complete(pg, 1)

        header = _rect(pg, ".main-header")
        controls = _rect(pg, "#global-nav-controls")
        assert header and controls, "header or controls not present"
        assert inside(controls, header), (
            f"controls {controls} not inside header {header} at {viewport}"
        )
        assert controls_clear_of_code(pg), f"controls overlap a .code-block at {viewport}"
        browser.close()


@pytest.mark.parametrize("viewport", DESKTOP_VIEWPORTS)
def test_controls_in_header_at_end_of_station3(server, viewport):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--autoplay-policy=no-user-gesture-required"]
        )
        pg = browser.new_page(viewport={"width": viewport[0], "height": viewport[1]})
        pg.goto(f"http://127.0.0.1:{PORT}/player.html?demo=mimic-clustering")
        enter_demo(pg)
        for s in range(1, 4):
            wait_station_complete(pg, s)
            if s < 3:
                pg.click("#global-next-btn")

        header = _rect(pg, ".main-header")
        controls = _rect(pg, "#global-nav-controls")
        assert header and controls
        assert inside(controls, header), (
            f"controls {controls} not inside header {header} at {viewport}"
        )
        assert controls_clear_of_code(pg), f"controls overlap a .code-block at {viewport}"
        browser.close()


@pytest.mark.parametrize("viewport", DESKTOP_VIEWPORTS)
def test_controls_in_intro_clear_of_notepad(server, viewport):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--autoplay-policy=no-user-gesture-required"]
        )
        pg = browser.new_page(viewport={"width": viewport[0], "height": viewport[1]})
        pg.goto(f"http://127.0.0.1:{PORT}/player.html?demo=mimic-clustering")
        pg.wait_for_selector("#transition-start-btn", state="visible", timeout=5000)
        pg.evaluate(
            "() => { window.sleep = (ms) => new Promise(r => setTimeout(r, 0)); }"
        )
        pg.click("#transition-start-btn")
        pg.wait_for_timeout(500)
        assert pg.evaluate("document.body.classList.contains('layout-intro')")

        controls = _rect(pg, "#global-nav-controls")
        notepad = _rect(pg, ".intro-notepad-container")
        assert controls and notepad
        assert not intersects(controls, notepad), (
            f"intro controls {controls} overlap notepad {notepad} at {viewport}"
        )
        browser.close()


def test_arrow_right_reaches_station2(server):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--autoplay-policy=no-user-gesture-required"]
        )
        pg = browser.new_page(viewport={"width": 1280, "height": 720})
        pg.goto(f"http://127.0.0.1:{PORT}/player.html?demo=mimic-clustering")
        enter_demo(pg)
        wait_station_complete(pg, 1)
        pg.keyboard.press("ArrowRight")
        wait_station_complete(pg, 2)
        assert pg.evaluate("currentStation") == 2
        browser.close()


def test_space_toggles_pause(server):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--autoplay-policy=no-user-gesture-required"]
        )
        pg = browser.new_page(viewport={"width": 1280, "height": 720})
        pg.goto(f"http://127.0.0.1:{PORT}/player.html?demo=mimic-clustering")
        enter_demo(pg)
        wait_station_complete(pg, 1)
        pg.keyboard.press(" ")
        assert pg.evaluate("isPaused") is True
        pg.keyboard.press(" ")
        assert pg.evaluate("isPaused") is False
        browser.close()


def test_progress_bar_width_grows_with_audio(server):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--autoplay-policy=no-user-gesture-required"]
        )
        pg = browser.new_page(viewport={"width": 1280, "height": 720})
        pg.goto(f"http://127.0.0.1:{PORT}/player.html?demo=mimic-clustering")
        enter_demo(pg)
        wait_station_complete(pg, 1)

        # While the station's narration plays, currentTime advances and timeupdate
        # fires, so the bar's width should grow over real time.
        def bar_width():
            return pg.evaluate(
                "document.getElementById('progress-bar').getBoundingClientRect().width"
            )

        pg.wait_for_function(
            "document.getElementById('demo-audio').currentTime > 0", timeout=5000
        )
        w1 = bar_width()
        pg.wait_for_timeout(3000)
        w2 = bar_width()
        assert w2 > w1, (
            f"progress bar width did not grow ({w1} -> {w2}) while audio plays"
        )
        browser.close()


def test_mobile_footer_fits_screen_during_station1(server):
    """On mobile (390x844) the sticky footer controls must fit the screen width
    (Attempt 2 regression: icon + label per button overflowed, cutting Exit and
    Reveal off) and every button must stay inside the viewport."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--autoplay-policy=no-user-gesture-required"]
        )
        pg = browser.new_page(viewport={"width": 390, "height": 844})
        pg.goto(f"http://127.0.0.1:{PORT}/player.html?demo=mimic-clustering")
        enter_demo(pg)
        wait_station_complete(pg, 1)

        assert pg.evaluate("window.innerWidth") <= 767, "not a mobile viewport"

        metrics = pg.evaluate(
            """(() => {
                const c = document.getElementById('global-nav-controls');
                const cw = c.clientWidth, sw = c.scrollWidth;
                const buttons = Array.from(document.querySelectorAll('.global-nav-btn'))
                    .map(b => {
                        const r = b.getBoundingClientRect();
                        return { left: r.left, right: r.right,
                                 top: r.top, bottom: r.bottom,
                                 width: r.width, height: r.height };
                    });
                return { cw, sw, buttons, vw: window.innerWidth,
                         vh: window.innerHeight };
            })()"""
        )
        assert metrics["sw"] <= metrics["cw"], (
            f"footer overflows: scrollWidth {metrics['sw']} > clientWidth "
            f"{metrics['cw']} at 390x844"
        )
        for b in metrics["buttons"]:
            assert 0 <= b["left"] and b["right"] <= metrics["vw"], (
                f"button {b} outside viewport width at 390x844"
            )
            assert 0 <= b["top"] and b["bottom"] <= metrics["vh"], (
                f"button {b} outside viewport height at 390x844"
            )
            assert b["height"] >= 44, (
                f"button height {b['height']} < 44px touch target at 390x844"
            )
        browser.close()
