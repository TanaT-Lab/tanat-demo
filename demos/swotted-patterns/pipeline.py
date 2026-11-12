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

# MIMIC-IV demo: one row per coded procedure (ICD code + readable title)
procedures = pd.read_csv("data/mimic_procedures.csv", dtype=str)
procedures["time"] = pd.to_datetime(procedures["time"])
print(f"Loaded {len(procedures)} procedures for "
      f"{procedures['subject_id'].nunique()} patients")

# MIMIC shifts the dates of each patient at random: calendar dates are
# meaningless across patients. Align every patient on their first procedure
# (day 0) and keep the first year.
first = procedures.groupby("subject_id")["time"].transform("min")
procedures["day"] = (procedures["time"] - first).dt.days
procedures = procedures[procedures["day"] < 365]
titles = procedures.drop_duplicates("icd_code").set_index("icd_code")["long_title"]
print(f"First year after the first procedure: {len(procedures)} procedures")

# %% 1b
from tanat.sequence import build_events

# One event sequence per patient, time = days since the first procedure
pool = build_events(
    procedures[["subject_id", "day", "icd_code"]],
    id_column="subject_id",
    time_column="day",
)

# %% 2a
import polars as pl

from tanat.criterion import EntityCriterion, LengthCriterion

# Keep the 30 most frequent procedure codes
TOP_K = 30
top_codes = (
    pool.temporal_data()
    .groupby("icd_code")
    .size()
    .sort_values(ascending=False)
    .head(TOP_K)
    .index.tolist()
)
pool.filter_entities(
    EntityCriterion(query=pl.col("icd_code").is_in(top_codes)),
    inplace=True,
)

# Drop the patients left without any event
pool = pool.subset(pool.which(LengthCriterion(gt=0)))
print(f"Top procedures: {[f'{c} {titles[c][:28]}' for c in top_codes[:3]]}")
print("Pool size:", len(pool))

# %% 2b
# Project the sequences on a daily grid: (patients, days, codes)
pool.cast_features({"icd_code": pl.Categorical})
arr, ids, feature_names = pool.to_tensor(
    features="icd_code",
    bin_size=1,  # one bin = one day
    fill_value=0,
    ohe=True,
    overlap_rule="max",  # several codes on the same day: keep them all
)

print(f"Tensor shape   : {arr.shape}  (patients, days, codes)")
print(f"Non-zero cells : {(arr != 0).sum()}")
print(f"Sparsity       : {(arr == 0).mean():.4%} empty")

# %% 3a
import numpy as np
import torch
from omegaconf import OmegaConf
from torch.utils.data import DataLoader

from swotted import fastSWoTTeDDataset, fastSWoTTeDModule, fastSWoTTeDTrainer

# SWoTTeD wants (patients, codes, days)
X = torch.from_numpy(arr.transpose(0, 2, 1).astype(np.float32))

R = 5   # number of temporal patterns to discover
Tw = 7  # temporal window: a pattern spans 7 days
N_patients, K_codes, T_days = X.shape

swotted_cfg = OmegaConf.create(
    {
        "model": {
            "non_succession": True,
            "sparsity": 0.1,
            "rank": R,
            "twl": Tw,
            "N": K_codes,
            "metric": "Bernoulli",  # binary data
        },
        "training": {"batch_size": N_patients, "nepochs": 300, "lr": 1e-2},
        "predict": {"nepochs": 20, "lr": 1e-2},
    }
)

# %% 3b
# Reproducible: fixed seed, and one thread (multi-threaded sums are not
# bit-reproducible, which changes the patterns from one run to the next)
SEED = 0
torch.manual_seed(SEED)
np.random.seed(SEED)
torch.set_num_threads(1)

model = fastSWoTTeDModule(swotted_cfg)
loader = DataLoader(
    fastSWoTTeDDataset(X),
    batch_size=N_patients,
    shuffle=False,
    collate_fn=lambda x: x,
)
trainer = fastSWoTTeDTrainer(
    fast_dev_run=False,
    max_epochs=swotted_cfg.training.nepochs,
    accelerator="cpu",
    enable_progress_bar=False,  # the bar would end up in the shown output
    enable_model_summary=False,
    enable_checkpointing=False,
    logger=False,
)
trainer.fit(model=model, train_dataloaders=loader)

# %% 4a
patterns, pathways = model.reorderPhenotypes(model.Ph.detach().cpu(), tw=Tw)
patterns = patterns.detach().numpy()  # (R, K, Tw): signature of each pattern
pathways = pathways.detach().numpy()  # (N, R, T'): activation per patient

# Read the patterns: the codes that weigh most in each one
codes = [name.removeprefix("icd_code_") for name in feature_names]
code_weights = patterns.sum(axis=-1)  # (R, K)
for r in range(R):
    top = np.argsort(code_weights[r])[::-1][:3]
    print(f"Pattern {r + 1}:")
    for i in top:
        print(f"  {codes[i]:>8}  {titles[codes[i]][:48]}")

# %% 4b
# Each pattern as a heatmap: its 6 heaviest codes (rows) over its 7 days (columns)
PATTERN_COLORS = ["#ffdd00", "#ff6b6b", "#22c55e", "#3b82f6", "#a855f7"]
short = lambda code: f"{code} {titles[code][:26]}"

fig, axes = plt.subplots(3, 2, figsize=(8, 7.5), sharex=True)
for r, ax in enumerate(axes.flat[:R]):
    top = np.argsort(code_weights[r])[::-1][:6]
    ax.imshow(patterns[r][top], aspect="auto", cmap="magma", vmin=0)
    ax.set_yticks(range(len(top)), [short(codes[i]) for i in top], fontsize=6)
    ax.set_xticks(range(Tw), range(1, Tw + 1))
    ax.set_title(f"Pattern {r + 1}", color=PATTERN_COLORS[r])
axes.flat[R].axis("off")
fig.supxlabel("Day of the pattern window")
fig.subplots_adjust(hspace=0.3, wspace=1.2)

# %% 5a
# Assign each patient to the pattern with the largest total activation
total = pathways.sum(axis=2)  # (N, R)
dominant = total.argmax(axis=1) + 1
dominant[total.max(axis=1) < 1e-3] = 0  # no pattern active for this patient

patient_patterns = dict(zip(ids, dominant.tolist()))
print("Patients per pattern (0 = none):",
      dict(sorted(pd.Series(dominant).value_counts().items())))

# %% 5b
# Round trip: the pattern becomes a static feature of the TanaT pool
names = {0: "No pattern", **{r: f"Pattern {r}" for r in range(1, R + 1)}}
labels = pd.DataFrame({
    "subject_id": ids,
    "pattern": [names[p] for p in dominant],
})
pool.add_static_features(labels)

# Same patients, same labels as the tensor axis
static = pool.static_data()
on_pool = dict(zip(static["subject_id"], static["pattern"]))
print("Labels on the right patients:",
      on_pool == {i: names[p] for i, p in patient_patterns.items()})

# %% 5c
from tanat.visualization import SequenceVisualizer

# Colour each code with the pattern it weighs most in
CODE_COLORS = {
    codes[i]: PATTERN_COLORS[code_weights[:, i].argmax()] for i in range(len(codes))
}

# One timeline per pattern, days since the first procedure
SequenceVisualizer.timeline(allow_large=True) \
    .figsize(7, 7) \
    .colors(CODE_COLORS) \
    .legend_off() \
    .title("Patient Timelines by Pattern") \
    .x_axis(label="Days since the first procedure") \
    .facet(
        by="pattern",
        is_static=True,
        cols=2,
        share_x=False,
        share_y=False,
        title_template="{value}",
    ) \
    .draw(pool, entity_feature="icd_code")

# %% 5d
# How strongly each patient activates each pattern (patients sorted by label)
order = np.argsort(dominant, kind="stable")
fig, ax = plt.subplots(figsize=(4, 7))
im = ax.imshow(total[order], aspect="auto", cmap="magma", vmin=0)
ax.set_xticks(range(R), [f"P{r}" for r in range(1, R + 1)])
ax.set_ylabel("Patients, sorted by dominant pattern")
ax.set_title("Pattern activation per patient")
fig.colorbar(im, ax=ax, label="Total activation")
