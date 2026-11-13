"""The swotted-patterns demo is staged consistently with what really ran.

Static checks read config.js / SCRIPT.md / audio/manifest.json / outputs.json
(generate_all.py and tools/tts.py output); the Playwright test plays the demo
to its final screen and checks the state counts. Without generated outputs or
playwright the corresponding tests are skipped.
"""

import functools
import http.server
import json
import os
import re
import threading

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(REPO, "demos", "swotted-patterns")
PORT = 8731

# Blocks of pipeline.py that run but are never shown (not listed in config.js).
HIDDEN = {"1c", "4b", "5a", "6c"}
STATION_BLOCKS = [["1a", "1b"], ["2a"], ["3a"], ["4a", "4c"], ["5b", "5c"], ["6a", "6b", "6d"]]


def read(*parts):
    with open(os.path.join(DEMO, *parts), encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def config_js():
    return read("config.js")


@pytest.fixture(scope="module")
def outputs():
    path = os.path.join(DEMO, "outputs", "outputs.json")
    if not os.path.exists(path):
        pytest.skip("run generate_all.py first (outputs.json missing)")
    return json.loads(read("outputs", "outputs.json"))


@pytest.fixture(scope="module")
def manifest():
    return json.loads(read("audio", "manifest.json"))


def listed_blocks(config_js):
    return [re.findall(r"'([0-9][a-z])'", m) for m in re.findall(r"blocks:\s*\[([^\]]*)\]", config_js)]


def test_stations_list_the_planned_blocks(config_js):
    assert listed_blocks(config_js) == STATION_BLOCKS


def test_every_listed_block_exists_and_no_hidden_block_is_listed(config_js, outputs):
    ids = {b["id"] for b in outputs["blocks"]}
    listed = {b for blocks in listed_blocks(config_js) for b in blocks}
    assert listed <= ids
    assert HIDDEN <= ids  # hidden blocks still run
    assert not listed & HIDDEN
    # every non-hidden block of the pipeline is shown
    assert ids - HIDDEN == listed


def test_intro_anchors_exist_in_the_audio_manifest(config_js, manifest):
    anchors = manifest["sections"]["intro"]["anchors"]
    used = set(re.findall(r"at:\s*'([^']+)'", config_js))
    assert used and used <= set(anchors)
    assert set(anchors) == {"welcome", "what", "bridge", "mimic", "open", "model"}
    # every note stays inside the intro audio
    duration = manifest["sections"]["intro"]["duration"]
    for at, delay in re.findall(r"at:\s*'([^']+)',\s*delay:\s*([0-9.]+)", config_js):
        assert anchors[at] + float(delay) < duration


def test_every_audio_file_of_the_stations_exists(config_js, manifest):
    audio = re.findall(r"audio:\s*'audio/([a-z0-9]+)\.mp3'", config_js)
    assert sorted(audio) == sorted(["intro", "end"] + [f"step{i}" for i in range(1, 7)])
    for name in audio:
        assert os.path.exists(os.path.join(DEMO, "audio", f"{name}.mp3"))
        assert name in manifest["sections"]


def test_audio_budget(manifest):
    total = sum(s["duration"] for s in manifest["sections"].values())
    assert total <= 285


def test_script_numbers_match_outputs(outputs):
    script = read("SCRIPT.md")
    by_id = {b["id"]: b["output"] for b in outputs["blocks"]}
    assert "722 procedures for 92 patients" in by_id["1a"]
    assert "722 procedures for 92 patients" in script
    assert "Pool size: 63" in by_id["2a"]
    assert "Sixty-three patients remain" in script
    assert "(63, 345, 30)" in by_id["3a"]
    assert "sixty-three patients by three hundred and forty-five days by thirty procedures" in script
    assert "Illustration only: 5 patterns" in by_id["5b"]


# ═══════════════════════════════════════════════════════════════════════════════
# PLAYWRIGHT: the demo plays to its final screen
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def server():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=REPO)
    handler.log_message = lambda *a: None
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield httpd
    httpd.shutdown()


def shown_code_lines(outputs):
    n = 0
    for b in outputs["blocks"]:
        if b["id"] in HIDDEN:
            continue
        n += sum(1 for line in b["code"].splitlines() if line.strip() and not line.strip().startswith("#"))
    return n


def test_demo_plays_to_the_final_screen(server, outputs):
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        pg = browser.new_page(viewport={"width": 1920, "height": 1080})
        pg.on("pageerror", lambda e: errors.append(str(e)))

        def short_outro(route):  # 2nd paragraph of `## end` at 2 s: beat 2 comes fast
            resp = route.fetch()
            data = resp.json()
            data["sections"]["end"]["offsets"] = [0.0, 2.0]
            route.fulfill(response=resp, json=data)

        pg.route("**/swotted-patterns/audio/manifest.json", short_outro)
        pg.goto(f"http://127.0.0.1:{PORT}/player.html?demo=swotted-patterns")
        pg.wait_for_selector("#transition-start-btn", state="visible", timeout=8000)

        # state counts
        assert pg.evaluate("demoConfig.stations.length") == 6
        assert pg.evaluate("demoConfig.stations.map(s => s.blocks.map(b => b.id))") == STATION_BLOCKS
        assert pg.evaluate("demoConfig.intro.notes.every(n => typeof n.time === 'number')")
        assert pg.evaluate("demoConfig.intro.notes.filter(n => n.type === 'svg').length") == 1

        pg.evaluate("() => { window.sleep = (ms) => new Promise(r => setTimeout(r, 0)); }")
        pg.click("#transition-start-btn")
        pg.wait_for_timeout(500)
        pg.click("#global-next-btn")
        for s in range(1, 7):
            pg.wait_for_function(f"currentStation === {s} && isDisplayComplete === true", timeout=30000)
            pg.click("#global-next-btn")
        pg.wait_for_selector("#final-view", state="visible", timeout=8000)
        pg.wait_for_function(
            "Array.from(document.querySelectorAll('#final-view img')).every(i => i.complete && i.naturalWidth > 0)",
            timeout=10000,
        )

        # beat 1: headline (no {lines} in the first takeaway) and the 6 steps;
        # step 5 has no api line, step 6 has two
        assert pg.inner_text(".fv-headline") == "Trajectories to a tensor in one call"
        assert pg.locator(".fv-chip").count() == 6
        assert pg.locator('.fv-chip[data-step="5"] .fv-chip-api').count() == 0
        assert pg.locator('.fv-chip[data-step="6"] .fv-chip-api span').count() == 2

        # beat 2: takeaways with the computed line count
        pg.wait_for_function("document.getElementById('final-view').dataset.beat === '2'", timeout=8000)
        takeaways = pg.eval_on_selector_all(".fv-takeaways li", "els => els.map(e => e.textContent)")
        assert len(takeaways) == 3
        assert any(f"{shown_code_lines(outputs)} lines of code" in t for t in takeaways)
        assert not any("{lines}" in t for t in takeaways)

        # Full code panel: one In [n] cell per shown block
        pg.click(".fv-fullcode")
        gutters = pg.eval_on_selector_all("#fv-notebook .fv-gutter", "els => els.length")
        assert gutters == sum(len(b) for b in STATION_BLOCKS)
        assert pg.is_visible("#fv-notebook .fv-gutter")
        browser.close()
    assert not errors, errors


def test_landing_shows_both_demo_cards(server):
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    import sys

    sys.path.insert(0, REPO)
    import generate_all

    generate_all.write_manifest(demos_dir=os.path.join(REPO, "demos"))  # index.json: build output
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": 1920, "height": 1080})
        pg.goto(f"http://127.0.0.1:{PORT}/index.html")
        pg.wait_for_selector(".demo-card", timeout=8000)
        titles = pg.eval_on_selector_all(".demo-card", "els => els.map(e => e.textContent)")
        browser.close()
    assert len(titles) == 2
    assert any("Hospital Readmission Patterns" in t for t in titles)
    assert any("From trajectories to tensors" in t for t in titles)
