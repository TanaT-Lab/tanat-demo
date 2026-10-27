# ═══════════════════════════════════════════════════════════════════════════════
# HIDDEN PREAMBLE (not shown to the audience)
# ═══════════════════════════════════════════════════════════════════════════════
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

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

# %% 1a
import pandas as pd

# Load MIMIC-IV admissions data
admissions = pd.read_csv("data/mimic_admissions_pool.csv")
admissions["time"] = pd.to_datetime(admissions["time"])
admissions["endtime"] = pd.to_datetime(admissions["endtime"])
print(f"Loaded {len(admissions)} admission records")

# %% 1b
import polars as pl

from tanat.sequence import build_intervals

# Build a pool: one interval sequence per patient
pool = build_intervals(
    admissions,
    id_column="subject_id",
    start_column="time",
    end_column="endtime",
)

# Categorical is required by the metric/clustering modules
pool.cast_features({"admission_type": pl.Categorical}, is_static=False)
print(pool)

# %% 2a
# Consistent colour palette for every visualization
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

# %% 2b
from tanat.visualization import SequenceVisualizer

# Distribution of admission types across ALL patients
SequenceVisualizer.barplot(sort="descending") \
    .colors(ADMISSION_COLORS) \
    .title("Admission Type Distribution") \
    .draw(pool, entity_feature="admission_type")

# %% 3a
from tanat.criterion import EntityCriterion

# Keep only patients with at least one emergency admission
EMER = pl.col("admission_type").cast(pl.Utf8).str.contains("EMER")
ids = pool.which(EntityCriterion(query=EMER))
emergency_pool = pool.subset(ids)  # whole patients, full history kept
print(emergency_pool)

# %% 3b
# Compare cohort sizes
print(f"Before: {len(pool.unique_ids)} patients")
print(f"After:  {len(emergency_pool.unique_ids)} patients")
print(f"Retention: {100 * len(emergency_pool.unique_ids) / len(pool.unique_ids):.1f}%")

# %% 4a
# Define the reference date (T0) as each patient's first emergency admission
emergency_pool.set_t0(query=EMER, anchor="start")
print(f"T0 set for {len(emergency_pool.t0_data())} patients")

# %% 4b
# Timeline of the emergency cohort, aligned to T0
SequenceVisualizer.timeline(time_mode="relative", allow_large=True) \
    .colors(ADMISSION_COLORS) \
    .title("Emergency Cohort (Relative to T0)") \
    .x_axis(label="Relative time (days)") \
    .draw(emergency_pool, entity_feature="admission_type")

# %% 5a
from tanat.metric import EditSequenceMetric, HammingEntityMetric

# Entity-level: distance between two admissions at the same position
hamming = HammingEntityMetric(entity_feature="admission_type")

# Sequence-level: edit distance (Optimal Matching), normalized by length so
# that patients are compared on their pattern, not on how many admissions they have
seq_metric = EditSequenceMetric(entity_metric=hamming, normalize=True)
print(seq_metric)

# %% 5b
from tanat.clustering import HierarchicalClusterer

# Group patient sequences by similarity
clusterer = HierarchicalClusterer(
    metric=seq_metric,
    n_clusters=3,
    cluster_column="cluster",
)
clusterer.fit(emergency_pool)

# Cluster distribution (stored as a static feature)
print(emergency_pool.static_data()["cluster"].value_counts().sort_index())

# %% 6a
# Timelines by cluster, aligned to T0
SequenceVisualizer.timeline(time_mode="relative", allow_large=True) \
    .colors(ADMISSION_COLORS) \
    .title("Patient Timelines by Cluster") \
    .x_axis(label="Relative time (days)") \
    .facet(
        by="cluster",
        is_static=True,
        cols=2,
        share_x=False,
        share_y=False,
        title_template="Cluster {value}",
    ) \
    .draw(emergency_pool, entity_feature="admission_type")
