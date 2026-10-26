/**
 * MIMIC-IV Clustering Demo Configuration
 * 
 * This file contains all content specific to this demo:
 * - Metadata (title, description)
 * - Station definitions (id, name, description, audio, shown block ids)
 * - Intro/outro content
 * - Audio track mappings
 *
 * Staging only: block code/output/figure are NOT stored here. They come from
 * demos/mimic-clustering/outputs/outputs.json at load time.
 */

const DEMO_CONFIG = {
    // ═══════════════════════════════════════════════════════════════════════════
    // METADATA
    // ═══════════════════════════════════════════════════════════════════════════
    id: 'mimic-clustering',
    title: 'Hospital Readmission Pattern Analysis',
    subtitle: 'with MIMIC-IV Dataset',
    description: 'Analyze hospital readmission patterns using TanaT clustering capabilities',
    
    // ═══════════════════════════════════════════════════════════════════════════
    // INTRO CONTENT - Notepad style with timed notes
    // ═══════════════════════════════════════════════════════════════════════════
    intro: {
        audio: 'audio/intro.mp3',
        // Notes appear at specific timestamps (in seconds) synchronized with audio
        // Adjust these timings to match your audio narration
        notes: [
            // ─────────────────────────────────────────────────────────────────
            // PART 1: Introduction to TanaT (0s - ~48s)
            // ─────────────────────────────────────────────────────────────────
            { time: 0.5, type: 'welcome', content: 'Welcome to this demonstration of <strong>TanaT</strong>' },
            { time: 4, type: 'tagline', content: 'Temporal Analysis of Trajectories' },
            { time: 8, type: 'bullet', content: 'Python library for temporal sequence analysis' },
            { time: 14, type: 'bullet', content: 'Focus: patient care pathways' },
            { time: 25, type: 'bullet', content: 'Clear, flexible, explicit code syntax' },
            { time: 30, type: 'bullet', content: 'Handles irregular, symbolic data' },
            { time: 40, type: 'divider' },
            { time: 42, type: 'bullet', content: 'Building block: the <strong>Entity</strong>' },
            { time: 44, type: 'bullet', content: 'A single observation in a patient journey' },
            { time: 46, type: 'detail', content: 'e.g. hospital visit, clinical encounter, lab result' },
            
            // ─────────────────────────────────────────────────────────────────
            // PART 2: Sequence Types Animation (~48s - ~70s)
            // ─────────────────────────────────────────────────────────────────
            { time: 54, type: 'divider' },
            { time: 56, type: 'svg', id: 'sequence-types-viz' },
            
            // ─────────────────────────────────────────────────────────────────
            // PART 3: MIMIC Workflow Animation (~70s - ~90s)
            // ─────────────────────────────────────────────────────────────────
            { time: 81, type: 'divider' },
            { time: 81, type: 'title', content: 'Demo: MIMIC-IV Analysis' },
            { time: 82, type: 'svg', id: 'workflow-viz' },
        ],
        
        // SVG visualizations referenced by notes
        visualizations: {
            'sequence-types-viz': `
                <div class="sequence-viz-container">
                    <h4>Sequence Types</h4>
                    <div class="sequence-types-grid">
                        <div class="sequence-type-card">
                            <div class="sequence-type-label">EventSequence</div>
                            <div class="sequence-type-desc">precise timestamps</div>
                            <svg class="sequence-svg" viewBox="0 0 300 60">
                                <line x1="20" y1="30" x2="280" y2="30" stroke="#30363d" stroke-width="2"/>
                                <circle cx="50" cy="30" r="8" fill="#ffdd00" class="entity-dot anim-1"/>
                                <circle cx="120" cy="30" r="8" fill="#ff6b6b" class="entity-dot anim-2"/>
                                <circle cx="180" cy="30" r="8" fill="#22c55e" class="entity-dot anim-3"/>
                                <circle cx="240" cy="30" r="8" fill="#3b82f6" class="entity-dot anim-4"/>
                            </svg>
                        </div>
                        <div class="sequence-type-card">
                            <div class="sequence-type-label">StateSequence</div>
                            <div class="sequence-type-desc">contiguous states, no gaps</div>
                            <svg class="sequence-svg" viewBox="0 0 300 60">
                                <rect x="30" y="20" width="60" height="20" fill="#ffdd00" class="entity-bar anim-1"/>
                                <rect x="90" y="20" width="50" height="20" fill="#3b82f6" class="entity-bar anim-2"/>
                                <rect x="140" y="20" width="70" height="20" fill="#22c55e" class="entity-bar anim-3"/>
                                <rect x="210" y="20" width="50" height="20" fill="#a855f7" class="entity-bar anim-4"/>
                                <rect x="30" y="20" width="230" height="20" fill="none" stroke="#8b949e" stroke-width="1" rx="0"/>
                            </svg>
                        </div>
                        <div class="sequence-type-card">
                            <div class="sequence-type-label">IntervalSequence</div>
                            <div class="sequence-type-desc">events with duration</div>
                            <svg class="sequence-svg" viewBox="0 0 300 60">
                                <line x1="20" y1="30" x2="280" y2="30" stroke="#30363d" stroke-width="2"/>
                                <rect x="35" y="20" width="50" height="20" rx="4" fill="#3b82f6" class="entity-bar anim-1"/>
                                <rect x="100" y="20" width="40" height="20" rx="4" fill="#a855f7" class="entity-bar anim-2"/>
                                <rect x="160" y="20" width="55" height="20" rx="4" fill="#22c55e" class="entity-bar anim-3"/>
                                <rect x="235" y="20" width="35" height="20" rx="4" fill="#ff6b6b" class="entity-bar anim-4"/>
                            </svg>
                        </div>
                    </div>
                    <div class="concepts-legend">
                        <div class="legend-item">
                            <span class="legend-text"><strong>Entity</strong> = single observation</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-text"><strong>Sequence</strong> = chain of entities for one patient</span>
                        </div>
                    </div>
                </div>`,
            'workflow-viz': `
                <div class="workflow-viz-container">
                    <svg class="workflow-svg" viewBox="0 0 600 200">
                        <g class="workflow-db anim-fade-in">
                            <rect x="20" y="60" width="100" height="80" rx="8" fill="#3b82f6" stroke="#60a5fa" stroke-width="2"/>
                            <rect x="30" y="70" width="80" height="8" rx="2" fill="#1e3a5f"/>
                            <rect x="30" y="82" width="80" height="8" rx="2" fill="#1e3a5f"/>
                            <rect x="30" y="94" width="80" height="8" rx="2" fill="#1e3a5f"/>
                            <rect x="30" y="106" width="80" height="8" rx="2" fill="#1e3a5f"/>
                            <rect x="30" y="118" width="80" height="8" rx="2" fill="#1e3a5f"/>
                            <text x="70" y="155" text-anchor="middle" fill="#e6edf3" font-size="12" font-weight="bold">MIMIC-IV</text>
                        </g>
                        <g class="workflow-arrow-1 anim-fade-in">
                            <line x1="130" y1="100" x2="180" y2="100" stroke="#8b949e" stroke-width="2" stroke-dasharray="4,4"/>
                            <polygon points="180,95 190,100 180,105" fill="#8b949e"/>
                        </g>
                        <g class="workflow-patients anim-fade-in">
                            <line x1="200" y1="50" x2="330" y2="50" stroke="#30363d" stroke-width="1"/>
                            <rect x="210" y="44" width="25" height="12" rx="2" fill="#ffdd00"/>
                            <rect x="250" y="44" width="35" height="12" rx="2" fill="#22c55e"/>
                            <rect x="300" y="44" width="20" height="12" rx="2" fill="#ffdd00"/>
                            <line x1="200" y1="80" x2="330" y2="80" stroke="#30363d" stroke-width="1"/>
                            <rect x="205" y="74" width="40" height="12" rx="2" fill="#ffdd00"/>
                            <rect x="260" y="74" width="30" height="12" rx="2" fill="#ffdd00"/>
                            <rect x="305" y="74" width="20" height="12" rx="2" fill="#a855f7"/>
                            <line x1="200" y1="110" x2="330" y2="110" stroke="#30363d" stroke-width="1"/>
                            <rect x="220" y="104" width="45" height="12" rx="2" fill="#22c55e"/>
                            <rect x="280" y="104" width="40" height="12" rx="2" fill="#3b82f6"/>
                            <line x1="200" y1="140" x2="330" y2="140" stroke="#30363d" stroke-width="1"/>
                            <rect x="215" y="134" width="30" height="12" rx="2" fill="#ffdd00"/>
                            <rect x="260" y="134" width="25" height="12" rx="2" fill="#ffdd00"/>
                            <rect x="300" y="134" width="25" height="12" rx="2" fill="#ffdd00"/>
                            <text x="265" y="175" text-anchor="middle" fill="#8b949e" font-size="11">Patient Trajectories</text>
                        </g>
                        <g class="workflow-arrow-2 anim-fade-in">
                            <line x1="340" y1="100" x2="390" y2="100" stroke="#8b949e" stroke-width="2" stroke-dasharray="4,4"/>
                            <polygon points="390,95 400,100 390,105" fill="#8b949e"/>
                        </g>
                        <g class="workflow-clusters anim-fade-in">
                            <ellipse cx="470" cy="65" rx="55" ry="35" fill="rgba(255,221,0,0.15)" stroke="#ffdd00" stroke-width="2" stroke-dasharray="4,4"/>
                            <circle cx="455" cy="60" r="6" fill="#ffdd00"/>
                            <circle cx="475" cy="55" r="6" fill="#ffdd00"/>
                            <circle cx="485" cy="70" r="6" fill="#ffdd00"/>
                            <ellipse cx="540" cy="130" rx="45" ry="30" fill="rgba(34,197,94,0.15)" stroke="#22c55e" stroke-width="2" stroke-dasharray="4,4"/>
                            <circle cx="530" cy="125" r="6" fill="#22c55e"/>
                            <circle cx="550" cy="135" r="6" fill="#22c55e"/>
                            <text x="500" y="185" text-anchor="middle" fill="#8b949e" font-size="11">Clusters</text>
                        </g>
                    </svg>
                </div>`
        }
    },
    
    // ═══════════════════════════════════════════════════════════════════════════
    // OUTRO CONTENT
    // ═══════════════════════════════════════════════════════════════════════════
    outro: {
        audio: 'audio/end.mp3'
    },
    
    // ═══════════════════════════════════════════════════════════════════════════
    // STATIONS (Pipeline Steps)
    // ═══════════════════════════════════════════════════════════════════════════
    // Staging only: each station carries its id, name, description, audio and
    // the list of shown block ids. The actual code, output and figure for each
    // shown block come from outputs.json at load time (single source of truth).
    stations: [
        {
            id: 1,
            name: 'Load',
            description: 'CSV to Pool',
            audio: 'audio/step1.mp3',
            blocks: ['1a', '1b']
        },
        {
            id: 2,
            name: 'Visualize',
            description: 'Histogram',
            audio: 'audio/step2.mp3',
            blocks: ['2b']
        },
        {
            id: 3,
            name: 'Filter',
            description: 'Criterion',
            audio: 'audio/step3.mp3',
            blocks: ['3a', '3b']
        },
        {
            id: 4,
            name: 'Align',
            description: 'T0 Reference',
            audio: 'audio/step4.mp3',
            blocks: ['4a', '4b']
        },
        {
            id: 5,
            name: 'Cluster',
            description: 'Edit Distance',
            audio: 'audio/step5.mp3',
            blocks: ['5a', '5b']
        },
        {
            id: 6,
            name: 'Analyze',
            description: 'Faceted Viz',
            audio: 'audio/step6.mp3',
            blocks: ['6a']
        }
    ]
};

// Export for use in player
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DEMO_CONFIG;
}
