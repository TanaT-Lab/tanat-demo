/**
 * MIMIC-IV Clustering Demo Configuration
 * 
 * This file contains all content specific to this demo:
 * - Metadata (title, description)
 * - Code snippets and outputs
 * - Station definitions
 * - Intro/outro content
 * - Audio track mappings
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
    stations: [
        {
            id: 1,
            name: 'Load',
            description: 'CSV to Pool',
            audio: 'audio/step1.mp3',
            blocks: [
                {
                    id: '1a',
                    code: `import pandas as pd
from tanat.sequence import IntervalSequencePool, IntervalSequenceSettings

# Load MIMIC-IV admissions data
admissions = pd.read_csv("data/mimic_admissions_pool.csv")
print(f"Loaded {len(admissions)} admission records")`,
                    output: 'Loaded 306 admission records'
                },
                {
                    id: '1b',
                    code: `# Create sequence pool (collection of all patient sequences)
settings = IntervalSequenceSettings(
    id_column="subject_id",
    start_column="time",
    end_column="endtime",
    entity_features=["admission_type", "admission_location"]
)

pool = IntervalSequencePool(sequence_data=admissions, settings=settings)
print(pool)  # POOL-LEVEL: view of all patients`,
                    output: `┌──────────────────────────────────────────────────┐
│           IntervalSequencePool summary           │
└──────────────────────────────────────────────────┘

STATISTICS
─────────────────────────
  Total sequences    100            
  Average length     3.1            
  Minimum length     1              
  Maximum length     20             
  Vocabulary size    30             

DATA PREVIEW
─────────────────────────
  Sequence Data:
     subject_id       time    endtime admission_type     admission_location
       10000032 2180-05-06 2180-05-07         URGENT TRANSFER FROM HOSPITAL
       10000032 2180-06-26 2180-06-27       EW EMER.         EMERGENCY ROOM
       10000032 2180-07-23 2180-07-25       EW EMER.         EMERGENCY ROOM

  Static Data:
    None

  Metadata:
    Temporal:
      Type: datetime
      Granularity: DAY
    
    Entity Features (2):
      - admission_type: categorical
      - admission_location: categorical
    
    Static Features (0):
      (none)`
                }
            ]
        },
        {
            id: 2,
            name: 'Visualize',
            description: 'Histogram',
            audio: 'audio/step2.mp3',
            blocks: [
                {
                    id: '2b',
                    code: `from tanat.visualization.sequence import SequenceVisualizer

# POOL-LEVEL: Visualize distribution across ALL patients
SequenceVisualizer.histogram(bar_order="descending") \\
    .colors(ADMISSION_COLORS) \\
    .title("Admission Type Distribution") \\
    .draw(pool, entity_features=["admission_type"])`,
                    output: null,
                    outputType: 'figure'
                }
            ]
        },
        {
            id: 3,
            name: 'Filter',
            description: 'Criterion',
            audio: 'audio/step3.mp3',
            blocks: [
                {
                    id: '3a',
                    code: `from tanat.criterion import QueryCriterion

# POOL-LEVEL: Filter to keep only patients with emergency admissions
criterion = QueryCriterion(query="admission_type.str.contains('EMER')")
emergency_pool = pool.filter(criterion, level="sequence")
print(emergency_pool)`,
                    output: `┌──────────────────────────────────────────────────┐
│           IntervalSequencePool summary           │
└──────────────────────────────────────────────────┘

STATISTICS
─────────────────────────
  Total sequences    64             
  Average length     3.9            
  Minimum length     1              
  Maximum length     20             
  Vocabulary size    29             

DATA PREVIEW
─────────────────────────
  Sequence Data:
     subject_id       time    endtime admission_type     admission_location
       10000032 2180-05-06 2180-05-07         URGENT TRANSFER FROM HOSPITAL
       10000032 2180-06-26 2180-06-27       EW EMER.         EMERGENCY ROOM
       10000032 2180-07-23 2180-07-25       EW EMER.         EMERGENCY ROOM

  Static Data:
    None

  Metadata:
    Temporal:
      Type: datetime
      Granularity: DAY
    
    Entity Features (2):
      - admission_type: categorical
      - admission_location: categorical
    
    Static Features (0):
      (none)`
                },
                {
                    id: '3b',
                    code: `# Compare cohort sizes
print(f"Before: {len(pool.unique_ids)} patients")
print(f"After:  {len(emergency_pool.unique_ids)} patients")
print(f"Retention: {100*len(emergency_pool.unique_ids)/len(pool.unique_ids):.1f}%")`,
                    output: 'Before: 100 patients\nAfter:  64 patients\nRetention: 64.0%'
                }
            ]
        },
        {
            id: 4,
            name: 'Align',
            description: 'T0 Reference',
            audio: 'audio/step4.mp3',
            blocks: [
                {
                    id: '4a',
                    code: `# POOL-LEVEL: Define reference date (T0) for filtered cohort
# T0 = first emergency admission for each patient
emergency_pool.zero_from_query(query="admission_type.str.contains('EMER')")
print(f"T0 set for {len(emergency_pool.t_zero)} patients")`,
                    output: 'T0 set for 64 patients'
                },
                {
                    id: '4b',
                    code: `# Timeline of filtered cohort in relative time
SequenceVisualizer.timeline(relative_time=True, granularity="day", stacking_mode="flat") \\
    .colors(ADMISSION_COLORS) \\
    .title("Emergency Cohort (Relative to T0)") \\
    .xlabel("Relative time (days)") \\
    .draw(emergency_pool, entity_features=["admission_type"])`,
                    output: null,
                    outputType: 'figure'
                }
            ]
        },
        {
            id: 5,
            name: 'Cluster',
            description: 'Edit Distance',
            audio: 'audio/step5.mp3',
            blocks: [
                {
                    id: '5a',
                    code: `from tanat.metric.entity import HammingEntityMetric, HammingEntityMetricSettings
from tanat.metric.sequence import EditSequenceMetric, EditSequenceMetricSettings

# Entity-level metric (compare individual admissions)
hamming = HammingEntityMetric(
    settings=HammingEntityMetricSettings(default_value=0.0)
)

# Sequence-level metric: Edit distance (Optimal Matching)
seq_metric = EditSequenceMetric(
    settings=EditSequenceMetricSettings(entity_metric=hamming)
)
print(seq_metric)`,
                    output: `┌──────────────────────────────────────────────────┐
│                EditSequenceMetric                │
└──────────────────────────────────────────────────┘

Settings
─────────────────────────
  entity_metric      HammingEntityMetric
  distance_matrix    Memory (float32)
  indel_cost         1.0            
  normalize          False          `
                },
                {
                    id: '5b',
                    code: `from tanat.clustering import HierarchicalClusterer, HierarchicalClustererSettings

# POOL-LEVEL: Cluster patient sequences by similarity
settings = HierarchicalClustererSettings(
    metric=seq_metric,
    n_clusters=4,
    cluster_column="cluster"
)

clusterer = HierarchicalClusterer(settings=settings)
clusterer.fit(emergency_pool)  # Operates on filtered cohort

# View cluster distribution
print(emergency_pool.static_data["cluster"].value_counts().sort_index())`,
                    output: 'Cluster 0: 2 patients\nCluster 1: 9 patients\nCluster 2: 52 patients\nCluster 3: 1 patients'
                }
            ]
        },
        {
            id: 6,
            name: 'Analyze',
            description: 'Faceted Viz',
            audio: 'audio/step6.mp3',
            blocks: [
                {
                    id: '6a',
                    code: `# Post-clustering visualization: timeline by cluster
SequenceVisualizer.timeline(relative_time=True, granularity="day", stacking_mode="flat") \\
    .colors(ADMISSION_COLORS) \\
    .title("Patient Timelines by Cluster") \\
    .xlabel("Relative time (days)") \\
    .x_axis(autofmt_xdate=False) \\
    .facet(by="cluster", cols=2, share_x=False, share_y=False, title_template="Cluster {value}") \\
    .draw(emergency_pool, entity_features=["admission_type"])`,
                    output: null,
                    outputType: 'figure'
                }
            ]
        }
    ],
    
    // ═══════════════════════════════════════════════════════════════════════════
    // SHARED RESOURCES (like color palettes)
    // ═══════════════════════════════════════════════════════════════════════════
    resources: {
        colorPalette: {
            name: 'ADMISSION_COLORS',
            code: `# Define color palette for consistent visualization
ADMISSION_COLORS = {
    "EW EMER.": "#ffdd00",           # Flashy yellow
    "DIRECT EMER.": "#ffe066",       # Light yellow
    "EU OBSERVATION": "#ff6b6b",     # Coral red
    "OBSERVATION ADMIT": "#ff9ff3",  # Hot pink
    "DIRECT OBSERVATION": "#f368e0", # Magenta
    "AMBULATORY OBSERVATION": "#00d2d3", # Cyan
    "URGENT": "#a855f7",             # Purple
    "ELECTIVE": "#22c55e",           # Green
    "SURGICAL SAME DAY ADMISSION": "#3b82f6", # Blue
    "DEATH": "#94a3b8",              # Slate
}`
        }
    }
};

// Export for use in player
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DEMO_CONFIG;
}
