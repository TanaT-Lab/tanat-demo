/**
 * Final view: shown after the last step, during the outro narration.
 * Left: the whole pipeline as a scrollable notebook (one `In [n]` cell per
 * shown block). Right: clickable workflow SVG, final figure, key messages, CTA.
 *
 * Built once from what the player already has (demoConfig.stations with their
 * blocks filled from outputs.json) plus optional staging fields:
 *   station.api          key TanaT call shown in the diagram node
 *   outro.takeaways      short strings; `{lines}` = non-empty, non-comment
 *                        code lines of all shown blocks (computed here)
 * Public hooks used by player.js: showFinalView(), hideFinalView().
 */

const FV_DOC_URL = 'https://tanat-lab.github.io/TanaT/';
const FV_GITHUB_URL = 'https://github.com/TanaT-Lab/TanaT';
const FV_OUTPUT_LINES = 8;

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

function fvDiagramSvg() {
    const stations = demoConfig.stations;
    const cols = Math.min(3, stations.length);
    const rows = Math.ceil(stations.length / cols);
    const w = 150, h = 72, gx = 28, gy = 34;
    const W = cols * w + (cols - 1) * gx, H = rows * h + (rows - 1) * gy;
    const pos = i => ({ x: (i % cols) * (w + gx), y: Math.floor(i / cols) * (h + gy) });
    let arrows = '', nodes = '';
    stations.forEach((s, i) => {
        const p = pos(i);
        if (i + 1 < stations.length) {
            const q = pos(i + 1);
            const d = q.y === p.y
                ? `M${p.x + w + 3},${p.y + h / 2} L${q.x - 5},${q.y + h / 2}`
                : `M${p.x + w / 2},${p.y + h + 2} V${p.y + h + gy / 2} H${q.x + w / 2} V${q.y - 5}`;
            arrows += `<path class="fv-arrow" d="${d}" marker-end="url(#fv-arrowhead)"/>`;
        }
        const api = s.api ? String(s.api).split(' + ') : [];
        const apiText = api.map((line, k) =>
            `<text class="fv-node-api" x="${p.x + w / 2}" y="${p.y + 52 + k * 12}" text-anchor="middle">${fvEscape(line)}</text>`
        ).join('');
        nodes += `<g class="fv-node" data-step="${s.id}" style="--i:${i}" tabindex="0" role="button"
                aria-label="Step ${s.id}: ${fvEscape(s.name)}">
            <rect x="${p.x}" y="${p.y}" width="${w}" height="${h}" rx="8"/>
            <text class="fv-node-num" x="${p.x + 10}" y="${p.y + 18}">${s.id}</text>
            <text class="fv-node-name" x="${p.x + w / 2}" y="${p.y + (api.length ? 34 : 44)}" text-anchor="middle">${fvEscape(s.name)}</text>
            ${apiText}</g>`;
    });
    return `<svg class="fv-diagram" viewBox="-2 -2 ${W + 4} ${H + 4}" role="group" aria-label="Workflow">
        <defs><marker id="fv-arrowhead" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
            <path d="M0,0 L10,5 L0,10 z" class="fv-arrowhead"/></marker></defs>
        ${arrows}${nodes}</svg>`;
}

function fvRightHtml() {
    const stations = demoConfig.stations;
    let figId = null;
    const last = stations[stations.length - 1];
    if (last) last.blocks.forEach(b => { if (b.figure) figId = b.id; });
    const fig = figId ? last.blocks.find(b => b.id === figId) : null;
    const lines = fvCountCodeLines();
    const takeaways = (demoConfig.outro && demoConfig.outro.takeaways) || [];
    return `
        ${fvDiagramSvg()}
        ${fig ? `<button type="button" class="fv-thumb" data-target="fv-fig-${fig.id}" title="Show in the notebook">
            <img src="${demoBasePath}outputs/${fig.figure}" alt="Final figure"></button>` : ''}
        ${takeaways.length ? `<ul class="fv-takeaways">${takeaways.map(t =>
            `<li>${fvEscape(String(t).replace(/\{lines\}/g, lines))}</li>`).join('')}</ul>` : ''}
        <div class="fv-cta">
            <div class="fv-install"><code>pip install tanat</code>
                <button type="button" class="fv-copy">Copy</button></div>
            <div class="fv-links">
                <a href="${FV_DOC_URL}" target="_blank" rel="noopener">Documentation</a>
                <a href="${FV_GITHUB_URL}" target="_blank" rel="noopener">GitHub</a>
            </div>
        </div>`;
}

function fvHeading(id) {
    return document.querySelector('#fv-step-' + id + ' .fv-step-heading');
}

/** Scroll the notebook (or the page when stacked) to an element, then flash it. */
function fvScrollTo(el) {
    const panel = document.getElementById('fv-notebook');
    const scrollable = panel.scrollHeight > panel.clientHeight &&
        getComputedStyle(panel).overflowY !== 'visible';
    if (scrollable) {
        const top = el.getBoundingClientRect().top - panel.getBoundingClientRect().top
            + panel.scrollTop - 8;
        panel.scrollTo({ top, behavior: 'smooth' });
    } else {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    el.classList.remove('fv-flash');
    void el.offsetWidth;
    el.classList.add('fv-flash');
}

function buildFinalView() {
    if (document.getElementById('final-view')) return;
    const view = document.createElement('div');
    view.id = 'final-view';
    view.style.display = 'none';
    view.innerHTML = `<div class="fv-notebook" id="fv-notebook">${fvNotebookHtml()}</div>
        <aside class="fv-side" id="fv-side">${fvRightHtml()}</aside>`;
    document.querySelector('.main-content').appendChild(view);

    view.addEventListener('click', e => {
        const node = e.target.closest('.fv-node');
        if (node) return fvScrollTo(fvHeading(node.dataset.step));
        const thumb = e.target.closest('.fv-thumb');
        if (thumb) return fvScrollTo(document.getElementById(thumb.dataset.target));
        const tog = e.target.closest('.fv-toggle');
        if (tog) {
            const box = tog.closest('.fv-out-text');
            const collapsed = box.classList.toggle('fv-collapsed');
            tog.textContent = collapsed ? 'show all' : 'show less';
            return;
        }
        if (e.target.closest('.fv-copy')) {
            const btn = e.target.closest('.fv-copy');
            const done = () => { btn.textContent = 'Copied'; setTimeout(() => { btn.textContent = 'Copy'; }, 1500); };
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText('pip install tanat').then(done, done);
            } else done();
        }
    });
    view.addEventListener('keydown', e => {
        const node = e.target.closest && e.target.closest('.fv-node');
        if (node && (e.key === 'Enter' || e.key === ' ')) {
            e.preventDefault();
            fvScrollTo(fvHeading(node.dataset.step));
        }
    });
}

function showFinalView() {
    buildFinalView();
    const stations = document.getElementById('stations-container');
    if (stations) stations.style.display = 'none';
    const view = document.getElementById('final-view');
    view.style.display = '';
    view.classList.remove('fv-animate');
    void view.offsetWidth;
    view.classList.add('fv-animate');
    document.getElementById('fv-notebook').scrollTop = 0;
}

function hideFinalView() {
    const view = document.getElementById('final-view');
    if (view) view.style.display = 'none';
    const stations = document.getElementById('stations-container');
    if (stations) stations.style.display = '';
}
