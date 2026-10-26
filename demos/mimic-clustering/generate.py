#!/usr/bin/env python3
"""
MIMIC-IV Clustering Demo - Output Generator

Generates all outputs (figures + terminal outputs) for this demo.
Each demo has its own generate.py that knows how to produce its outputs.
"""

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
import sys
import json

# ═══════════════════════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════════════════════

DEMO_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(DEMO_DIR))
DATA_PATH = os.path.join(ROOT_DIR, "data", "mimic_admissions_pool.csv")
OUTPUTS_DIR = os.path.join(DEMO_DIR, "outputs")

# ═══════════════════════════════════════════════════════════════════════════════
# DARK THEME
# ═══════════════════════════════════════════════════════════════════════════════


def set_dark_figure_style():
    """Configure matplotlib with dark theme matching terminal."""
    plt.rcParams.update(
        {
            "figure.facecolor": "#0d1117",
            "axes.facecolor": "#161b22",
            "axes.edgecolor": "#30363d",
            "axes.labelcolor": "#8b949e",
            "text.color": "#c9d1d9",
            "xtick.color": "#8b949e",
            "ytick.color": "#8b949e",
            "grid.color": "#21262d",
            "legend.facecolor": "#161b22",
            "legend.edgecolor": "#30363d",
            "font.family": "monospace",
            "font.size": 8,
            "axes.titlesize": 9,
            "axes.labelsize": 8,
            "savefig.facecolor": "#0d1117",
            "savefig.edgecolor": "#0d1117",
        }
    )


# ═══════════════════════════════════════════════════════════════════════════════
# COLOR PALETTE
# ═══════════════════════════════════════════════════════════════════════════════

ADMISSION_COLORS = {
    "EW EMER.": "#ffdd00",
    "DIRECT EMER.": "#ffe066",
    "EU OBSERVATION": "#ff6b6b",
    "OBSERVATION ADMIT": "#ff9ff3",
    "DIRECT OBSERVATION": "#f368e0",
    "AMBULATORY OBSERVATION": "#00d2d3",
    "URGENT": "#a855f7",
    "ELECTIVE": "#22c55e",
    "SURGICAL SAME DAY ADMISSION": "#3b82f6",
    "DEATH": "#94a3b8",
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN GENERATION
# ═══════════════════════════════════════════════════════════════════════════════


def generate():
    """Generate all outputs for this demo. Returns True on success."""

    print(f"  [mimic-clustering] Starting generation...")

    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    outputs = {}

    # Import TanaT
    try:
        from tanat.sequence import IntervalSequencePool, IntervalSequenceSettings
        from tanat.visualization.sequence import SequenceVisualizer
        from tanat.criterion import QueryCriterion
        from tanat.metric.entity import HammingEntityMetric, HammingEntityMetricSettings
        from tanat.metric.sequence import EditSequenceMetric, EditSequenceMetricSettings
        from tanat.clustering import (
            HierarchicalClusterer,
            HierarchicalClustererSettings,
        )
    except ImportError as e:
        print(f"  [mimic-clustering] ERROR: TanaT not installed: {e}")
        return False

    # Check data file
    if not os.path.exists(DATA_PATH):
        print(f"  [mimic-clustering] ERROR: Data file not found: {DATA_PATH}")
        return False

    # ─────────────────────────────────────────────────────────────────────
    # Station 1: Load
    # ─────────────────────────────────────────────────────────────────────
    admissions = pd.read_csv(DATA_PATH)
    outputs["1a"] = f"Loaded {len(admissions)} admission records"

    settings = IntervalSequenceSettings(
        id_column="subject_id",
        start_column="time",
        end_column="endtime",
        entity_features=["admission_type", "admission_location"],
    )
    pool = IntervalSequencePool(sequence_data=admissions, settings=settings)
    outputs["1b"] = repr(pool)

    # ─────────────────────────────────────────────────────────────────────
    # Station 2: Visualize - Histogram
    # ─────────────────────────────────────────────────────────────────────
    set_dark_figure_style()
    result = (
        SequenceVisualizer.histogram(bar_order="descending")
        .colors(ADMISSION_COLORS)
        .title("Admission Type Distribution")
        .draw(pool, entity_features=["admission_type"])
    )
    plt.tight_layout()
    result.fig.savefig(
        os.path.join(OUTPUTS_DIR, "2b.png"), dpi=150, bbox_inches="tight"
    )
    plt.close(result.fig)
    outputs["2b"] = None  # Figure

    # ─────────────────────────────────────────────────────────────────────
    # Station 3: Filter
    # ─────────────────────────────────────────────────────────────────────
    criterion = QueryCriterion(query="admission_type.str.contains('EMER')")
    emergency_pool = pool.filter(criterion, level="sequence")
    outputs["3a"] = repr(emergency_pool)

    retention = 100 * len(emergency_pool.unique_ids) / len(pool.unique_ids)
    outputs["3b"] = (
        f"Before: {len(pool.unique_ids)} patients\nAfter:  {len(emergency_pool.unique_ids)} patients\nRetention: {retention:.1f}%"
    )

    # ─────────────────────────────────────────────────────────────────────
    # Station 4: Align
    # ─────────────────────────────────────────────────────────────────────
    emergency_pool.zero_from_query(query="admission_type.str.contains('EMER')")
    outputs["4a"] = f"T0 set for {len(emergency_pool.t_zero)} patients"

    set_dark_figure_style()
    result = (
        SequenceVisualizer.timeline(
            relative_time=True, granularity="day", stacking_mode="flat"
        )
        .colors(ADMISSION_COLORS)
        .title("Emergency Cohort (Relative to T0)")
        .xlabel("Relative time (days)")
        .draw(emergency_pool, entity_features=["admission_type"])
    )
    plt.tight_layout()
    result.fig.savefig(
        os.path.join(OUTPUTS_DIR, "4b.png"), dpi=150, bbox_inches="tight"
    )
    plt.close(result.fig)
    outputs["4b"] = None  # Figure

    # ─────────────────────────────────────────────────────────────────────
    # Station 5: Cluster
    # ─────────────────────────────────────────────────────────────────────
    hamming = HammingEntityMetric(
        settings=HammingEntityMetricSettings(default_value=0.0)
    )
    seq_metric = EditSequenceMetric(
        settings=EditSequenceMetricSettings(entity_metric=hamming)
    )
    outputs["5a"] = repr(seq_metric)

    cluster_settings = HierarchicalClustererSettings(
        metric=seq_metric, n_clusters=4, cluster_column="cluster"
    )
    clusterer = HierarchicalClusterer(settings=cluster_settings)
    clusterer.fit(emergency_pool)

    cluster_counts = emergency_pool.static_data["cluster"].value_counts().sort_index()
    cluster_lines = [f"Cluster {c}: {n} patients" for c, n in cluster_counts.items()]
    outputs["5b"] = "\n".join(cluster_lines)

    # ─────────────────────────────────────────────────────────────────────
    # Station 6: Analyze - Faceted clusters
    # ─────────────────────────────────────────────────────────────────────
    set_dark_figure_style()
    result = (
        SequenceVisualizer.timeline(
            relative_time=True, granularity="day", stacking_mode="flat"
        )
        .colors(ADMISSION_COLORS)
        .title("Patient Timelines by Cluster")
        .xlabel("Relative time (days)")
        .x_axis(autofmt_xdate=False)
        .facet(
            by="cluster",
            cols=2,
            share_x=False,
            share_y=False,
            title_template="Cluster {value}",
        )
        .draw(emergency_pool, entity_features=["admission_type"])
    )
    plt.tight_layout()
    result.fig.savefig(
        os.path.join(OUTPUTS_DIR, "6a.png"), dpi=150, bbox_inches="tight"
    )
    plt.close(result.fig)
    outputs["6a"] = None  # Figure

    # ─────────────────────────────────────────────────────────────────────
    # Save outputs metadata
    # ─────────────────────────────────────────────────────────────────────
    with open(os.path.join(OUTPUTS_DIR, "outputs.json"), "w", encoding="utf-8") as f:
        json.dump(outputs, f, indent=2, ensure_ascii=False)

    print(f"  [mimic-clustering] ✓ Generated 3 figures + outputs.json")
    return True


if __name__ == "__main__":
    success = generate()
    sys.exit(0 if success else 1)
