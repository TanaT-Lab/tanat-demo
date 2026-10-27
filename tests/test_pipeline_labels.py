"""The cluster labels shown in step 6a must be the clusterer's own labels.

tanat 0.10.4 + polars 2 attached static features to the wrong patients
(LEFT JOIN without maintain_order), which silently scrambled the 6a facets.
Runs the real pipeline, so it needs tanat (skipped otherwise).
"""

import contextlib
import io
import os
import runpy

import pytest

pytest.importorskip("tanat")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPELINE = os.path.join(REPO, "demos", "mimic-clustering", "pipeline.py")


def test_static_cluster_labels_match_clusterer(monkeypatch):
    import matplotlib.pyplot as plt

    monkeypatch.chdir(REPO)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            ns = runpy.run_path(PIPELINE)
    finally:
        plt.close("all")  # the pipeline draws figures; do not leak them to other tests

    static = ns["emergency_pool"].static_data()
    labels = dict(zip(static["subject_id"].astype(int), static["cluster"]))
    expected = {
        int(item): cluster.id
        for cluster in ns["clusterer"].clusters
        for item in cluster.items
    }

    assert labels == expected
