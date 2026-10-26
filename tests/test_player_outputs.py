"""Playwright tests verifying the player renders what really ran (outputs.json).

The plain pytest run (without playwright installed) skips these tests via
pytest.importorskip, so the rest of the suite still passes.
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
OUTPUTS_PATH = os.path.join(REPO, "demos", "mimic-clustering", "outputs", "outputs.json")
PORT = 8722


@pytest.fixture(scope="module")
def server():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=REPO)
    handler.log_message = lambda *a: None
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd
    httpd.shutdown()


@pytest.fixture(scope="module")
def outputs():
    with open(OUTPUTS_PATH, encoding="utf-8") as f:
        return json.load(f)


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


def reach_first_station(page):
    page.click("#transition-start-btn")
    page.wait_for_timeout(1500)
    page.click("#global-next-btn")
    page.wait_for_timeout(1500)


def shown_blocks_per_station(page):
    return page.evaluate(
        "demoConfig.stations.map(s => ({ id: s.id, blocks: s.blocks.map(b => b.id) }))"
    )


def test_rendered_outputs_match_outputs_json(page, outputs):
    """For every shown block, Reveal renders outputs.json 'code', the terminal
    text equals 'output', and each figure <img> actually loads."""
    errors = []
    http_errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on(
        "response",
        lambda r: http_errors.append(r.status) if r.status >= 400 else None,
    )

    expected = {b["id"]: b for b in outputs["blocks"]}
    stations = shown_blocks_per_station(page)
    assert stations, "no stations loaded"

    reach_first_station(page)

    for i, station in enumerate(stations):
        sid = station["id"]
        page.wait_for_selector(f"#station-{sid}", state="visible", timeout=5000)
        page.click("#global-skip-btn")  # reveal the current station instantly
        page.wait_for_timeout(300)

        for bid in station["blocks"]:
            exp = expected[bid]
            code_el = page.query_selector(f"#code-{bid}")
            assert code_el is not None, f"missing code element for {bid}"
            rendered_code = page.evaluate(
                f"document.getElementById('code-{bid}').textContent"
            )
            assert rendered_code == exp["code"], f"code mismatch for block {bid}"

            output_el = page.query_selector(f"#output-{bid}")
            if exp["figure"]:
                assert output_el is not None, f"figure block {bid} has no output area"
                natural_width = page.evaluate(
                    f"document.getElementById('output-{bid}')"
                    f".querySelector('img').naturalWidth"
                )
                assert natural_width > 0, (
                    f"figure {bid} did not load (naturalWidth={natural_width})"
                )
            elif exp["output"]:
                assert output_el is not None, f"text block {bid} has no output area"
                rendered_output = page.evaluate(
                    f"document.getElementById('output-{bid}').textContent"
                )
                assert rendered_output == exp["output"], (
                    f"output mismatch for block {bid}"
                )
            else:
                assert output_el is None, f"block {bid} should have no output area"

        if i < len(stations) - 1:
            page.click("#global-next-btn")
            page.wait_for_timeout(800)

    assert not errors, f"JS errors: {errors}"
    assert not http_errors, f"HTTP >= 400 responses: {http_errors}"
