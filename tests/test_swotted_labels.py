"""The pattern labels added to the pool in swotted-patterns must be the model's own.

The tensor axis 0 follows ``to_tensor``'s ids; ``add_static_features`` joins by
subject_id. Both must agree: runs the real pipeline, so it needs swotted and
torch (skipped otherwise; CI installs them for this demo).
"""

import contextlib
import io
import os
import runpy

import pytest

pytest.importorskip("tanat")
pytest.importorskip("swotted")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPELINE = os.path.join(REPO, "demos", "swotted-patterns", "pipeline.py")


@pytest.fixture(scope="module")
def ns():
    import matplotlib.pyplot as plt

    previous = os.getcwd()
    os.chdir(REPO)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            return runpy.run_path(PIPELINE)
    finally:
        os.chdir(previous)
        plt.close("all")


def test_static_labels_match_tensor_ids(ns):
    static = ns["pool"].static_data()
    on_pool = dict(zip(static["subject_id"], static["pattern"]))
    expected = {pid: ns["names"][p] for pid, p in ns["patient_patterns"].items()}
    assert on_pool == expected


def test_labels_follow_the_activations(ns):
    """Each labelled patient has the pattern with the largest total activation."""
    total = ns["pathways"].sum(axis=2)
    static = ns["pool"].static_data()
    on_pool = dict(zip(static["subject_id"], static["pattern"]))
    for i, pid in enumerate(ns["ids"]):
        if total[i].max() < 1e-3:
            assert on_pool[pid] == "No pattern"
        else:
            assert on_pool[pid] == f"Pattern {total[i].argmax() + 1}"
