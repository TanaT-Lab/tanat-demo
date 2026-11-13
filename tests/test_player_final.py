"""Playwright test: the final view, in two beats driven by the outro audio clock.

Beat 1 = recap (headline, steps light up), beat 2 = call to action (pip install,
docs, QR, takeaways), plus the Full code panel. The audio is served with Range
support (Chromium cannot seek a file served without it).
"""

import functools
import http.server
import io
import os
import re
import threading

import pytest

pytest.importorskip("playwright")

from playwright.sync_api import sync_playwright  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8726
DEMO = "mimic-clustering"
URL = f"http://127.0.0.1:{PORT}/player.html?demo={DEMO}"
FLAGS = ["--autoplay-policy=no-user-gesture-required"]


class RangeHandler(http.server.SimpleHTTPRequestHandler):
    """Static files with HTTP Range support (needed to seek the audio)."""

    def log_message(self, *args):
        pass

    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def send_head(self):
        rng = self.headers.get("Range")
        path = self.translate_path(self.path)
        match = re.match(r"bytes=(\d*)-(\d*)", rng or "")
        if not match or not os.path.isfile(path):
            return super().send_head()
        size = os.path.getsize(path)
        start = int(match[1] or 0)
        end = int(match[2]) if match[2] else size - 1
        with open(path, "rb") as f:
            f.seek(start)
            data = f.read(end - start + 1)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{start + len(data) - 1}/{size}")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        return io.BytesIO(data)


@pytest.fixture(scope="module")
def server():
    handler = functools.partial(RangeHandler, directory=REPO)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield httpd
    httpd.shutdown()


@pytest.fixture()
def browser(server):
    with sync_playwright() as p:
        b = p.chromium.launch(args=FLAGS)
        yield b
        b.close()


def force_t2(page, t2):
    """Serve a manifest whose `## end` 2nd paragraph starts at t2 (fast tests)."""

    def handle(route):
        resp = route.fetch()
        data = resp.json()
        data["sections"]["end"]["offsets"] = [0.0, t2]
        route.fulfill(response=resp, json=data)

    page.route(f"**/{DEMO}/audio/manifest.json", handle)


def open_final(browser, w, h, setup=None):
    """Play the demo to its final screen, fast (Next on each station)."""
    pg = browser.new_page(viewport={"width": w, "height": h})
    if setup:
        setup(pg)
    pg.goto(URL)
    pg.wait_for_selector("#transition-start-btn", state="visible", timeout=8000)
    pg.evaluate("() => { window.sleep = (ms) => new Promise(r => setTimeout(r, 0)); }")
    pg.click("#transition-start-btn")
    pg.wait_for_timeout(500)
    pg.click("#global-next-btn")
    n = pg.evaluate("demoConfig.stations.length")
    for s in range(1, n + 1):
        pg.wait_for_function(f"currentStation === {s} && currentLayout === 'demo'", timeout=20000)
        pg.click("#global-next-btn")
    pg.wait_for_selector("#final-view", state="visible", timeout=5000)
    pg.wait_for_function(
        "Array.from(document.querySelectorAll('#final-view img')).every(i => i.complete && i.naturalWidth > 0)",
        timeout=10000,
    )
    return pg


def beat(pg):
    return pg.get_attribute("#final-view", "data-beat")


def wait_beat(pg, n, timeout=5000):
    pg.wait_for_function(
        f"document.getElementById('final-view').dataset.beat === '{n}'", timeout=timeout
    )


def go_beat2(pg):
    """Jump the outro audio past the 2nd paragraph and let the transition end."""
    pg.evaluate("audioElement.currentTime = fvT2() + 0.2")
    wait_beat(pg, 2)
    pg.wait_for_timeout(700)


STAGE_REPORT = """(() => {
    const stage = document.getElementById('fv-stage');
    const r = stage.getBoundingClientRect();
    const k = r.width / 1920;
    const hidden = el => { for (let e = el; e && e !== stage; e = e.parentElement) {
        const c = getComputedStyle(e);
        if (c.display === 'none' || c.visibility === 'hidden' || parseFloat(c.opacity) === 0) return true;
    } return false; };
    let min = Infinity, who = '', outside = [];
    const walker = document.createTreeWalker(stage, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
        const node = walker.currentNode;
        const el = node.parentElement;
        if (!node.textContent.trim() || hidden(el)) continue;
        const px = parseFloat(getComputedStyle(el).fontSize) * k;
        if (px < min) { min = px; who = node.textContent.trim().slice(0, 30); }
        const b = el.getBoundingClientRect();
        if (b.left < r.left - 1 || b.right > r.right + 1 || b.top < r.top - 1 || b.bottom > r.bottom + 1)
            outside.push(node.textContent.trim().slice(0, 30));
    }
    return {min, who, outside, left: r.left, top: r.top, right: r.right, bottom: r.bottom,
            vw: innerWidth, vh: innerHeight,
            scrolls: document.documentElement.scrollHeight > innerHeight
                || document.documentElement.scrollWidth > innerWidth};
})()"""


def check_stage(pg):
    rep = pg.evaluate(STAGE_REPORT)
    assert rep["min"] >= 16, f"text {rep['who']!r} renders at {rep['min']:.1f}px"
    assert rep["outside"] == []
    assert rep["left"] >= -1 and rep["top"] >= -1
    assert rep["right"] <= rep["vw"] + 1 and rep["bottom"] <= rep["vh"] + 1
    assert not rep["scrolls"]


def inside_viewport(pg, selector):
    box = pg.eval_on_selector(
        selector,
        """el => { const r = el.getBoundingClientRect();
        return {l: r.left, t: r.top, r: r.right, b: r.bottom, w: innerWidth, h: innerHeight}; }""",
    )
    assert box["l"] >= -1 and box["t"] >= -1 and box["r"] <= box["w"] + 1 and box["b"] <= box["h"] + 1


@pytest.mark.parametrize("viewport", [(1920, 1080), (1280, 720)])
def test_two_beats_desktop(browser, viewport):
    pg = open_final(browser, *viewport)

    # Beat 1: recap.
    assert beat(pg) == "1"
    assert pg.is_visible("#final-view") and not pg.is_visible(".sidebar")
    assert pg.is_disabled("#global-next-btn")
    lines = pg.evaluate("fvCountCodeLines()")
    headline = pg.inner_text(".fv-headline")
    assert f"{lines} lines of code" in headline and "{lines}" not in headline
    assert pg.inner_text(".fv-headline em") == f"{lines} lines of code"
    assert pg.text_content(".fv-eyebrow") == "Recap · Hospital Readmission Patterns"
    n = pg.evaluate("demoConfig.stations.length")
    assert pg.locator(".fv-chip").count() == n
    # api lines: the step-5 chip has two (split on " + ")
    assert pg.locator('.fv-chip[data-step="5"] .fv-chip-api span').count() == 2
    assert not pg.is_visible(".fv-cta")
    pg.wait_for_timeout(500)
    check_stage(pg)

    # Beat 2: call to action.
    go_beat2(pg)
    assert pg.locator(".fv-chip.fv-lit").count() == n
    assert pg.is_visible(".fv-cta")
    inside_viewport(pg, ".fv-cta")
    assert "pip install tanat" in pg.inner_text(".fv-cta")
    assert "tanat-lab.github.io/TanaT" in pg.inner_text(".fv-cta")
    assert pg.get_attribute(".fv-doc", "href") == "https://tanat-lab.github.io/TanaT/"
    assert pg.eval_on_selector(".fv-qr", "i => i.complete && i.naturalWidth > 0")
    takeaways = pg.eval_on_selector_all(".fv-takeaways li", "els => els.map(e => e.textContent)")
    assert len(takeaways) == 3 and not any("{lines}" in t for t in takeaways)
    assert not pg.is_visible(".fv-recap")
    # steps folded into a strip: names only
    assert not pg.is_visible(".fv-chip-api")
    check_stage(pg)


def test_full_code_prev_and_replay(browser):
    pg = open_final(browser, 1280, 720)
    go_beat2(pg)

    pg.click(".fv-fullcode")
    assert pg.is_visible("#fv-panel")
    n_blocks = pg.evaluate("demoConfig.stations.reduce((a, s) => a + s.blocks.length, 0)")
    gutters = pg.eval_on_selector_all(
        "#fv-notebook .fv-gutter", "els => els.map(e => e.textContent.trim())"
    )
    assert gutters == [f"In [{i}]:" for i in range(1, n_blocks + 1)]
    assert pg.is_visible("#fv-notebook .fv-code")
    assert not pg.evaluate("audioElement.paused")  # opening it does not stop the audio

    pg.keyboard.press("Escape")
    assert not pg.is_visible("#fv-panel")

    # A step in the strip opens the panel scrolled to that step.
    pg.click('.fv-chip[data-step="5"]')
    pg.wait_for_timeout(300)
    box = pg.evaluate(
        """(() => { const p = document.getElementById('fv-notebook').getBoundingClientRect();
        const h = document.querySelector('#fv-step-5 .fv-step-heading').getBoundingClientRect();
        return {pt: p.top, pb: p.bottom, ht: h.top, hb: h.bottom}; })()"""
    )
    assert pg.is_visible("#fv-panel")
    assert box["ht"] >= box["pt"] - 1 and box["hb"] <= box["pb"]
    pg.click(".fv-panel-close")
    assert not pg.is_visible("#fv-panel")

    # Prev goes back to station 6 with the stations restored.
    pg.click("#global-prev-btn")
    pg.wait_for_timeout(500)
    assert not pg.is_visible("#final-view") and pg.is_visible("#station-6")
    assert pg.evaluate("currentStation") == 6
    assert pg.is_visible(".sidebar")

    # Reaching the final view again replays from beat 1.
    pg.click("#global-next-btn")
    pg.wait_for_selector("#final-view", state="visible")
    assert beat(pg) == "1"
    pg.wait_for_timeout(300)
    assert pg.locator(".fv-chip.fv-lit").count() == 0


def test_steps_light_up_with_the_audio_clock(browser):
    pg = open_final(browser, 1280, 720)
    pg.evaluate("audioElement.pause()")  # freeze the clock, then drive it
    n = pg.evaluate("demoConfig.stations.length")
    t2 = pg.evaluate("fvT2()")
    for i in (1, n // 2, n):
        t = i / n * 0.85 * t2 + 0.05
        pg.evaluate(f"audioElement.currentTime = {t}")
        pg.wait_for_function(f"document.querySelectorAll('.fv-chip.fv-lit').length >= {i}")
        assert pg.locator(".fv-chip.fv-lit").count() == i
        assert beat(pg) == "1"


@pytest.mark.parametrize("audio_ok", [True, False])
def test_pause_freezes_the_sequence(browser, audio_ok):
    def setup(pg):
        force_t2(pg, 2.0)
        if not audio_ok:
            pg.route("**/audio/end.mp3", lambda route: route.abort())

    pg = open_final(browser, 1280, 720, setup)
    assert pg.evaluate("fvT2()") == 2.0
    pg.click("#global-pause-btn")
    lit = pg.locator(".fv-chip.fv-lit").count()
    pg.wait_for_timeout(3200)  # t2 + 1 s of wall time
    assert beat(pg) == "1"
    assert pg.locator(".fv-chip.fv-lit").count() == lit

    pg.click("#global-pause-btn")  # resume
    if audio_ok:
        pg.evaluate("audioElement.currentTime = fvT2() + 0.2")
    wait_beat(pg, 2, timeout=4000)


def test_audio_blocked_falls_back_to_the_wall_clock(browser):
    def setup(pg):
        force_t2(pg, 2.0)
        pg.route("**/audio/end.mp3", lambda route: route.abort())

    pg = open_final(browser, 1280, 720, setup)
    assert beat(pg) == "1"
    wait_beat(pg, 2, timeout=(2.0 + 2) * 1000)
    assert pg.locator(".fv-chip.fv-lit").count() == pg.evaluate("demoConfig.stations.length")
    assert pg.is_visible(".fv-cta")


def test_reduced_motion_cuts_instead_of_fading(server):
    with sync_playwright() as p:
        b = p.chromium.launch(args=FLAGS)
        ctx = b.new_context(viewport={"width": 1280, "height": 720}, reduced_motion="reduce")
        pg = ctx.new_page()
        pg.goto(URL)
        pg.wait_for_selector("#transition-start-btn", state="visible", timeout=8000)
        pg.click("#transition-start-btn")
        pg.wait_for_timeout(500)
        pg.click("#global-next-btn")
        n = pg.evaluate("demoConfig.stations.length")
        for s in range(1, n + 1):
            pg.wait_for_function(f"currentStation === {s} && currentLayout === 'demo'", timeout=20000)
            pg.click("#global-next-btn")
        pg.wait_for_selector("#final-view", state="visible")
        pg.evaluate("audioElement.currentTime = fvT2() + 0.2")
        wait_beat(pg, 2)
        # no waiting for a transition: the CTA is there at once
        assert pg.is_visible(".fv-cta")
        assert pg.eval_on_selector(".fv-ribbon", "e => getComputedStyle(e).transitionDuration") == "0s"
        b.close()


def test_final_view_stacks_on_a_phone(browser):
    pg = open_final(browser, 390, 844)
    assert beat(pg) == "1"
    assert pg.eval_on_selector("#fv-stage", "e => getComputedStyle(e).transform") == "none"
    assert pg.evaluate("document.documentElement.scrollWidth <= innerWidth")
    go_beat2(pg)
    assert pg.evaluate("document.documentElement.scrollWidth <= innerWidth")
    pg.locator(".fv-qr").scroll_into_view_if_needed()
    assert pg.is_visible(".fv-qr") and pg.is_visible(".fv-pip")
    box = pg.eval_on_selector(".fv-cta", "e => { const r = e.getBoundingClientRect(); return [r.left, r.right]; }")
    assert box[0] >= 0 and box[1] <= 390  # no horizontal overflow of the CTA block
    pg.evaluate("window.scrollTo(0, 0)")
    pg.click(".fv-fullcode")
    assert pg.is_visible("#fv-panel")
