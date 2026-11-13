/**
 * Final view: shown after the last step, during the outro narration, in two
 * beats driven by the outro audio clock.
 *   Beat 1 (recap): the key message, then the steps light up one by one.
 *   Beat 2 (call to action, from the 2nd paragraph of `## end`): the steps
 *   fold into a strip, `pip install`, the docs address, a QR code, takeaways.
 * The notebook (one `In [n]` cell per shown block) is behind a "Full code"
 * button.
 *
 * Built once from what the player already has (demoConfig.stations with their
 * blocks filled from outputs.json, demoConfig.title) plus optional staging:
 *   station.api          key TanaT call shown under the step name
 *                        (split on " + " into lines)
 *   outro.takeaways      short strings; `{lines}` = non-empty, non-comment
 *                        code lines of all shown blocks (computed here);
 *                        the first one is the headline
 *   audio/manifest.json  sections.end.offsets[1] = start of the 2nd paragraph
 *                        = the beat switch (default: 60% of the audio duration)
 * Public hooks used by player.js: showFinalView(), hideFinalView(),
 * fvLoadOutroTiming().
 */

const FV_DOC_URL = 'https://tanat-lab.github.io/TanaT/';
const FV_DOC_LABEL = 'tanat-lab.github.io/TanaT';
const FV_GITHUB_URL = 'https://github.com/TanaT-Lab/TanaT';
const FV_GITHUB_LABEL = 'github.com/TanaT-Lab/TanaT';
const FV_QR_SRC = 'assets/qr-docs.svg';
const FV_OUTPUT_LINES = 8;
const FV_STAGE_W = 1920;
const FV_STAGE_H = 1008;
const FV_LIT_SPAN = 0.85;      // the last step lights at 85% of t2
const FV_T2_RATIO = 0.6;       // t2 when the manifest has no 2nd paragraph
const FV_T2_DEFAULT = 12;      // t2 (s) when nothing is known about the audio
const FV_TICK_MS = 100;

// Outro timing from audio/manifest.json: { t2, duration } (either may be null).
let fvTiming = null;
// Running state of the current view: clock, steps lit so far, beat.
const fv = { timer: null, wall: 0, last: 0, lit: 0, beat: 1, observer: null };

function fvEscape(text) {
    const d = document.createElement('div');
    d.textContent = text == null ? '' : String(text);
    return d.innerHTML;
}

function fvCountCodeLines() {
    let n = 0;
    demoConfig.stations.forEach(s => s.blocks.forEach(b => {
        (b.code || '').split('\n').forEach(line => {
            const t = line.trim();
            if (t && !t.startsWith('#')) n++;
        });
    }));
    return n;
}

function fvTakeaways() {
    const lines = fvCountCodeLines();
    const list = (demoConfig.outro && demoConfig.outro.takeaways) || [];
    return list.map(t => String(t).replace(/\{lines\}/g, lines));
}

/** Escaped headline; "N lines of code" is accented when present. */
function fvHeadlineHtml() {
    const first = fvTakeaways()[0] || demoConfig.title || '';
    return fvEscape(first).replace(/(\d+ lines of code)/, '<em>$1</em>');
}

// ═══════════════════════════════════════════════════════════════════════════════
// TIMING
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Read the outro section of <demoBasePath>audio/manifest.json (offsets of the
 * paragraphs, duration). A missing manifest is not an error here: the view
 * falls back to a share of the audio duration.
 */
async function fvLoadOutroTiming() {
    fvTiming = null;
    try {
        const track = (demoConfig.outro && demoConfig.outro.audio) || 'audio/end.mp3';
        const section = track.split('/').pop().replace(/\.[^.]+$/, '');
        const response = await fetch(`${demoBasePath}audio/manifest.json`);
        if (!response.ok) return;
        const manifest = await response.json();
        const sec = manifest.sections && manifest.sections[section];
        if (!sec) return;
        const t2 = Array.isArray(sec.offsets) && typeof sec.offsets[1] === 'number'
            ? sec.offsets[1] : null;
        fvTiming = { t2, duration: typeof sec.duration === 'number' ? sec.duration : null };
    } catch (e) {
        console.log('Outro timing unavailable:', e);
    }
}

function fvOutroAudioPlaying() {
    return !!(audioElement && demoConfig.outro && demoConfig.outro.audio
        && audioElement.src.endsWith(demoConfig.outro.audio)
        && !audioElement.error && audioElement.currentTime > 0);
}

function fvT2() {
    if (fvTiming && fvTiming.t2 != null) return fvTiming.t2;
    let duration = fvTiming && fvTiming.duration;
    if (!duration && fvOutroAudioPlaying() && isFinite(audioElement.duration)) {
        duration = audioElement.duration;
    }
    return duration ? duration * FV_T2_RATIO : FV_T2_DEFAULT;
}

/** The narration clock; a pause-aware wall clock until the outro audio runs. */
function fvClock() {
    const now = performance.now();
    if (!isPaused) fv.wall += (now - fv.last) / 1000;
    fv.last = now;
    return fvOutroAudioPlaying() ? audioElement.currentTime : fv.wall;
}

function fvTick() {
    const view = document.getElementById('final-view');
    if (!view) return;
    const t = fvClock();
    const t2 = fvT2();
    const n = demoConfig.stations.length;
    const lit = Math.min(n, Math.floor(t / (FV_LIT_SPAN * t2 / n) + 1e-9));
    if (lit > fv.lit) {
        fv.lit = lit;
        view.querySelectorAll('.fv-chip').forEach((chip, i) => {
            chip.classList.toggle('fv-lit', i < fv.lit);
        });
    }
    if (fv.beat === 1 && t >= t2) {
        fv.beat = 2;
        view.dataset.beat = '2';
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MARKUP
// ═══════════════════════════════════════════════════════════════════════════════

function fvNotebookHtml() {
    let n = 0;
    return demoConfig.stations.map(station => {
        const cells = station.blocks.map(block => {
            n++;
            let out = '';
            if (block.figure) {
                out = `<div class="fv-out fv-out-fig" id="fv-fig-${block.id}">
                    <img src="${demoBasePath}outputs/${block.figure}" alt="Output of cell ${n}"></div>`;
            } else if (block.output !== null && block.output !== undefined && block.output !== '') {
                const long = String(block.output).split('\n').length > FV_OUTPUT_LINES;
                out = `<div class="fv-out fv-out-text${long ? ' fv-collapsed' : ''}">
                    <pre class="fv-out-pre">${fvEscape(block.output)}</pre>
                    ${long ? '<button type="button" class="fv-toggle">show all</button>' : ''}</div>`;
            }
            const code = hljs.highlight(block.code || '', { language: 'python' }).value;
            return `<div class="fv-cell">
                <div class="fv-gutter">In [${n}]:</div>
                <div class="fv-cell-body">
                    <pre class="fv-code"><code class="hljs language-python">${code}</code></pre>
                    ${out}
                </div></div>`;
        }).join('');
        return `<section class="fv-step" id="fv-step-${station.id}">
            <h3 class="fv-step-heading">Step ${station.id} · ${fvEscape(station.name)}</h3>
            ${cells}</section>`;
    }).join('');
}

function fvRibbonHtml() {
    return demoConfig.stations.map(s => {
        const api = s.api ? String(s.api).split(' + ') : [];
        const apiHtml = api.length
            ? `<span class="fv-chip-api">${api.map(a => `<span>${fvEscape(a)}</span>`).join('')}</span>` : '';
        return `<li><button type="button" class="fv-chip" data-step="${s.id}"
                title="Show step ${s.id} in the full code">
            <span class="fv-chip-num">${s.id}</span>
            <span class="fv-chip-name">${fvEscape(s.name)}</span>${apiHtml}</button></li>`;
    }).join('');
}

function fvCtaHtml() {
    const takeaways = fvTakeaways();
    return `<div class="fv-cta-main">
            <p class="fv-thanks">Thank you · start your own analysis</p>
            <div class="fv-install"><code class="fv-pip">pip install tanat</code>
                <button type="button" class="fv-copy">Copy</button></div>
            <a class="fv-doc" href="${FV_DOC_URL}" target="_blank" rel="noopener">${FV_DOC_LABEL}</a>
            <a class="fv-gh" href="${FV_GITHUB_URL}" target="_blank" rel="noopener">GitHub · ${FV_GITHUB_LABEL}</a>
            ${takeaways.length ? `<ul class="fv-takeaways">${takeaways.map(t =>
                `<li>${fvEscape(t)}</li>`).join('')}</ul>` : ''}
        </div>
        <a class="fv-qr-link" href="${FV_DOC_URL}" target="_blank" rel="noopener">
            <span class="fv-qr-tile"><img class="fv-qr" src="${FV_QR_SRC}"
                alt="QR code: ${FV_DOC_LABEL}"></span>
            <span class="fv-qr-cap">Documentation</span>
        </a>`;
}

// ═══════════════════════════════════════════════════════════════════════════════
// FULL CODE PANEL
// ═══════════════════════════════════════════════════════════════════════════════

function fvHeading(id) {
    return document.querySelector('#fv-step-' + id + ' .fv-step-heading');
}

/** Scroll the notebook to an element, then flash it. */
function fvScrollTo(el) {
    const panel = document.getElementById('fv-notebook');
    const top = el.getBoundingClientRect().top - panel.getBoundingClientRect().top
        + panel.scrollTop - 8;
    panel.scrollTo({ top, behavior: 'auto' });
    el.classList.remove('fv-flash');
    void el.offsetWidth;
    el.classList.add('fv-flash');
}

function fvPanelOpen() {
    const panel = document.getElementById('fv-panel');
    return !!panel && !panel.hidden;
}

function fvOpenPanel(stepId) {
    const panel = document.getElementById('fv-panel');
    panel.hidden = false;
    if (stepId) {
        const heading = fvHeading(stepId);
        if (heading) fvScrollTo(heading);
    } else {
        document.getElementById('fv-notebook').scrollTop = 0;
    }
    panel.querySelector('.fv-panel-close').focus({ preventScroll: true });
}

function fvClosePanel() {
    const panel = document.getElementById('fv-panel');
    if (!panel || panel.hidden) return;
    panel.hidden = true;
    const btn = document.querySelector('.fv-fullcode');
    if (btn && btn.offsetParent !== null) btn.focus({ preventScroll: true });
}

// ═══════════════════════════════════════════════════════════════════════════════
// BUILD / SHOW / HIDE
// ═══════════════════════════════════════════════════════════════════════════════

function fvFit() {
    const view = document.getElementById('final-view');
    const stage = document.getElementById('fv-stage');
    if (!view || !stage || !view.clientWidth || !view.clientHeight) return;
    const k = Math.min(view.clientWidth / FV_STAGE_W, view.clientHeight / FV_STAGE_H);
    stage.style.setProperty('--fv-scale', k);
}

function buildFinalView() {
    if (document.getElementById('final-view')) return;
    const view = document.createElement('div');
    view.id = 'final-view';
    view.dataset.beat = '1';
    view.style.display = 'none';
    view.innerHTML = `<div class="fv-stage" id="fv-stage">
            <div class="fv-recap">
                <p class="fv-eyebrow">Recap · ${fvEscape(demoConfig.title || '')}</p>
                <h2 class="fv-headline">${fvHeadlineHtml()}</h2>
            </div>
            <ol class="fv-ribbon" id="fv-ribbon">${fvRibbonHtml()}</ol>
            <div class="fv-cta" id="fv-cta">${fvCtaHtml()}</div>
            <button type="button" class="fv-fullcode">&lt;/&gt; Full code</button>
        </div>
        <div class="fv-panel" id="fv-panel" hidden role="dialog" aria-label="Full code">
            <div class="fv-panel-bar">
                <span class="fv-panel-title">Full code</span>
                <button type="button" class="fv-panel-close">Close · Esc</button>
            </div>
            <div class="fv-notebook" id="fv-notebook">${fvNotebookHtml()}</div>
        </div>`;
    document.querySelector('.main-content').appendChild(view);

    view.addEventListener('click', e => {
        const chip = e.target.closest('.fv-chip');
        if (chip) return fvOpenPanel(chip.dataset.step);
        if (e.target.closest('.fv-fullcode')) return fvOpenPanel();
        if (e.target.closest('.fv-panel-close')) return fvClosePanel();
        const tog = e.target.closest('.fv-toggle');
        if (tog) {
            const box = tog.closest('.fv-out-text');
            const collapsed = box.classList.toggle('fv-collapsed');
            tog.textContent = collapsed ? 'show all' : 'show less';
            return;
        }
        const copy = e.target.closest('.fv-copy');
        if (copy) {
            const done = () => { copy.textContent = 'Copied'; setTimeout(() => { copy.textContent = 'Copy'; }, 1500); };
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText('pip install tanat').then(done, done);
            } else done();
        }
    });
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && fvPanelOpen()) {
            e.preventDefault();
            fvClosePanel();
        }
    });
    fv.observer = new ResizeObserver(fvFit);
    fv.observer.observe(view);
}

function showFinalView() {
    buildFinalView();
    const stations = document.getElementById('stations-container');
    if (stations) stations.style.display = 'none';
    const view = document.getElementById('final-view');

    // Replay from beat 1.
    fv.wall = 0;
    fv.last = performance.now();
    fv.lit = 0;
    fv.beat = 1;
    view.dataset.beat = '1';
    view.querySelectorAll('.fv-chip').forEach(chip => chip.classList.remove('fv-lit'));
    document.getElementById('fv-panel').hidden = true;
    document.getElementById('fv-notebook').scrollTop = 0;

    view.style.display = '';
    fvFit();
    clearInterval(fv.timer);
    fv.timer = setInterval(fvTick, FV_TICK_MS);
    fvTick();
}

function hideFinalView() {
    clearInterval(fv.timer);
    fv.timer = null;
    const view = document.getElementById('final-view');
    if (view) view.style.display = 'none';
    const stations = document.getElementById('stations-container');
    if (stations) stations.style.display = '';
}
