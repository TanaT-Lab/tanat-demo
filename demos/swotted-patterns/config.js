/**
 * Trajectories to Tensors Demo Configuration (SWoTTeD patterns)
 *
 * Staging only, as for demos/mimic-clustering/config.js:
 * - Intro notes (timed from the narration anchors of SCRIPT.md)
 * - Station definitions (id, name, api, description, audio, shown block ids)
 * - Outro takeaways
 *
 * Block code/output/figure are NOT stored here. They come from
 * demos/swotted-patterns/outputs/outputs.json at load time. Blocks 1c, 4b, 5a
 * and 6c of pipeline.py run but are hidden: they are not listed below.
 */

const DEMO_CONFIG = {
    // Card metadata (title, subtitle, description, icon, tags) lives in
    // demos/swotted-patterns/demo.json. Only the id stays here.
    id: 'swotted-patterns',

    // ═══════════════════════════════════════════════════════════════════════════
    // INTRO CONTENT - Notepad style, notes timed from narration anchors
    // ═══════════════════════════════════════════════════════════════════════════
    intro: {
        audio: 'audio/intro.mp3',
        // `at` is an {#anchor} placed in SCRIPT.md, `delay` (seconds, optional)
        // shifts the note after the anchor. Times come from audio/manifest.json.
        notes: [
            // Paragraph 1: welcome
            { at: 'welcome', delay: 0.3, type: 'welcome', content: 'Welcome to this demonstration of <strong>TanaT</strong>' },

            // Paragraph 2: what TanaT is, and the question of the demo
            { at: 'what', delay: 2.0, type: 'tagline', content: 'Temporal Analysis of Trajectories' },
            { at: 'what', delay: 6.0, type: 'bullet', content: 'Python library for patient care pathways' },
            { at: 'bridge', delay: 0.5, type: 'divider' },
            { at: 'bridge', delay: 0.8, type: 'title', content: 'Trajectories to tensors, and back' },
            { at: 'bridge', delay: 6.8, type: 'svg', id: 'bridge-viz' },

            // Paragraph 3: the data and the model
            { at: 'mimic', delay: 0.5, type: 'divider' },
            { at: 'mimic', delay: 1.0, type: 'bullet', content: '<span><strong>MIMIC-IV</strong>: real, de-identified hospital records (Boston)</span>' },
            { at: 'open', delay: 0.5, type: 'bullet', content: 'Open demo: 100 patients, their procedures' },
            { at: 'model', delay: 0.5, type: 'bullet', content: '<span><strong>SWoTTeD</strong>: learns temporal patterns, runs on PyTorch</span>' },
            { at: 'model', delay: 7.5, type: 'detail', content: 'Any model that reads a tensor would do' },
        ],

        // SVG visualizations referenced by notes
        visualizations: {
            // Trajectories -> tensor -> model -> back into TanaT. Reuses the
            // fade-in classes of the workflow viz (inline delays stagger them).
            'bridge-viz': `
                <div class="workflow-viz-container">
                    <svg class="workflow-svg" style="max-width:720px" viewBox="0 0 640 170" role="img" aria-label="TanaT trajectories to a tensor, to a model, and back into TanaT">
                        <g class="workflow-db" style="animation-delay:0s">
                            <line x1="10" y1="40" x2="120" y2="40" stroke="#30363d" stroke-width="1"/>
                            <rect x="16" y="34" width="22" height="12" rx="2" fill="#ffdd00"/>
                            <rect x="52" y="34" width="34" height="12" rx="2" fill="#22c55e"/>
                            <rect x="98" y="34" width="16" height="12" rx="2" fill="#3b82f6"/>
                            <line x1="10" y1="68" x2="120" y2="68" stroke="#30363d" stroke-width="1"/>
                            <rect x="22" y="62" width="38" height="12" rx="2" fill="#a855f7"/>
                            <rect x="74" y="62" width="24" height="12" rx="2" fill="#ffdd00"/>
                            <line x1="10" y1="96" x2="120" y2="96" stroke="#30363d" stroke-width="1"/>
                            <rect x="14" y="90" width="26" height="12" rx="2" fill="#3b82f6"/>
                            <rect x="58" y="90" width="20" height="12" rx="2" fill="#22c55e"/>
                            <rect x="92" y="90" width="22" height="12" rx="2" fill="#ffdd00"/>
                            <text x="65" y="130" text-anchor="middle" fill="#e6edf3" font-size="14" font-weight="bold">Trajectories</text>
                            <text x="65" y="148" text-anchor="middle" fill="#8b949e" font-size="12">in TanaT</text>
                        </g>
                        <g class="workflow-db" style="animation-delay:0.8s">
                            <line x1="128" y1="68" x2="158" y2="68" stroke="#8b949e" stroke-width="2" stroke-dasharray="4,4"/>
                            <polygon points="158,63 168,68 158,73" fill="#8b949e"/>
                        </g>
                        <g class="workflow-db" style="animation-delay:1.4s">
                            <rect x="178" y="35" width="24" height="24" fill="#161b22" stroke="#30363d"/>
                            <rect x="202" y="35" width="24" height="24" fill="#ffdd00" fill-opacity="0.85" stroke="#30363d"/>
                            <rect x="226" y="35" width="24" height="24" fill="#161b22" stroke="#30363d"/>
                            <rect x="178" y="59" width="24" height="24" fill="#161b22" stroke="#30363d"/>
                            <rect x="202" y="59" width="24" height="24" fill="#161b22" stroke="#30363d"/>
                            <rect x="226" y="59" width="24" height="24" fill="#22c55e" fill-opacity="0.85" stroke="#30363d"/>
                            <rect x="178" y="83" width="24" height="24" fill="#3b82f6" fill-opacity="0.85" stroke="#30363d"/>
                            <rect x="202" y="83" width="24" height="24" fill="#161b22" stroke="#30363d"/>
                            <rect x="226" y="83" width="24" height="24" fill="#a855f7" fill-opacity="0.85" stroke="#30363d"/>
                            <text x="214" y="130" text-anchor="middle" fill="#e6edf3" font-size="14" font-weight="bold">Tensor</text>
                            <text x="214" y="148" text-anchor="middle" fill="#8b949e" font-size="12">to_tensor()</text>
                        </g>
                        <g class="workflow-db" style="animation-delay:2.0s">
                            <line x1="258" y1="68" x2="288" y2="68" stroke="#8b949e" stroke-width="2" stroke-dasharray="4,4"/>
                            <polygon points="288,63 298,68 288,73" fill="#8b949e"/>
                        </g>
                        <g class="workflow-db" style="animation-delay:2.6s">
                            <rect x="308" y="38" width="110" height="64" rx="10" fill="rgba(168,85,247,0.15)" stroke="#a855f7" stroke-width="2"/>
                            <circle cx="338" cy="58" r="6" fill="#a855f7"/>
                            <circle cx="338" cy="82" r="6" fill="#a855f7"/>
                            <circle cx="363" cy="70" r="6" fill="#a855f7"/>
                            <circle cx="388" cy="58" r="6" fill="#a855f7"/>
                            <circle cx="388" cy="82" r="6" fill="#a855f7"/>
                            <line x1="338" y1="58" x2="363" y2="70" stroke="#a855f7" stroke-width="1.5"/>
                            <line x1="338" y1="82" x2="363" y2="70" stroke="#a855f7" stroke-width="1.5"/>
                            <line x1="363" y1="70" x2="388" y2="58" stroke="#a855f7" stroke-width="1.5"/>
                            <line x1="363" y1="70" x2="388" y2="82" stroke="#a855f7" stroke-width="1.5"/>
                            <text x="363" y="130" text-anchor="middle" fill="#e6edf3" font-size="14" font-weight="bold">SWoTTeD</text>
                            <text x="363" y="148" text-anchor="middle" fill="#8b949e" font-size="12">learns patterns</text>
                        </g>
                        <g class="workflow-db" style="animation-delay:3.2s">
                            <line x1="426" y1="68" x2="456" y2="68" stroke="#8b949e" stroke-width="2" stroke-dasharray="4,4"/>
                            <polygon points="456,63 466,68 456,73" fill="#8b949e"/>
                        </g>
                        <g class="workflow-db" style="animation-delay:3.8s">
                            <line x1="476" y1="40" x2="630" y2="40" stroke="#30363d" stroke-width="1"/>
                            <rect x="484" y="34" width="22" height="12" rx="2" fill="#ffdd00"/>
                            <rect x="520" y="34" width="34" height="12" rx="2" fill="#6b7280"/>
                            <rect x="570" y="34" width="16" height="12" rx="2" fill="#ffdd00"/>
                            <line x1="476" y1="68" x2="630" y2="68" stroke="#30363d" stroke-width="1"/>
                            <rect x="490" y="62" width="38" height="12" rx="2" fill="#22c55e"/>
                            <rect x="544" y="62" width="24" height="12" rx="2" fill="#6b7280"/>
                            <line x1="476" y1="96" x2="630" y2="96" stroke="#30363d" stroke-width="1"/>
                            <rect x="482" y="90" width="26" height="12" rx="2" fill="#3b82f6"/>
                            <rect x="524" y="90" width="20" height="12" rx="2" fill="#6b7280"/>
                            <rect x="560" y="90" width="22" height="12" rx="2" fill="#3b82f6"/>
                            <text x="553" y="130" text-anchor="middle" fill="#e6edf3" font-size="14" font-weight="bold">Back in TanaT</text>
                            <text x="553" y="148" text-anchor="middle" fill="#8b949e" font-size="12">patterns as a feature</text>
                        </g>
                    </svg>
                </div>`
        }
    },

    // ═══════════════════════════════════════════════════════════════════════════
    // OUTRO CONTENT
    // ═══════════════════════════════════════════════════════════════════════════
    outro: {
        audio: 'audio/end.mp3',
        // {lines} = count of non-empty, non-comment code lines of all shown
        // blocks (computed by the player). No clinical claim.
        takeaways: [
            'Trajectories to a tensor in one call',
            'Learned patterns come back as a patient attribute',
            '{lines} lines of code, every output really ran'
        ]
    },

    // ═══════════════════════════════════════════════════════════════════════════
    // STATIONS (Pipeline Steps)
    // ═══════════════════════════════════════════════════════════════════════════
    // Each station carries its id, name, api, description, audio and the list
    // of shown block ids (hidden blocks 1c, 4b, 5a, 6c still run, unseen).
    stations: [
        {
            id: 1,
            name: 'Load',
            api: 'build_events()',
            description: 'CSV to Pool',
            audio: 'audio/step1.mp3',
            blocks: ['1a', '1b']
        },
        {
            id: 2,
            name: 'Filter',
            api: 'EntityCriterion',
            description: 'Frequent procedures',
            audio: 'audio/step2.mp3',
            blocks: ['2a']
        },
        {
            id: 3,
            name: 'To tensor',
            api: 'to_tensor()',
            description: 'Pool to tensor',
            audio: 'audio/step3.mp3',
            blocks: ['3a']
        },
        {
            id: 4,
            name: 'Learn',
            api: 'SWoTTeD',
            description: 'Temporal patterns',
            audio: 'audio/step4.mp3',
            blocks: ['4a', '4c']
        },
        {
            id: 5,
            name: 'Patterns',
            // The caution is staged here too: it shows in the sidebar and in
            // the station title (the 5b print says it as well).
            description: 'Illustration, not a finding',
            audio: 'audio/step5.mp3',
            blocks: ['5b', '5c']
        },
        {
            id: 6,
            name: 'Back to TanaT',
            api: 'add_static_features() + timeline().facet()',
            description: 'Patterns as a feature',
            audio: 'audio/step6.mp3',
            blocks: ['6a', '6b', '6d']
        }
    ]
};

// Export for use in player
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DEMO_CONFIG;
}
