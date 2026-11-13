#!/usr/bin/env python3
"""Rebuild data/mimic_procedures.csv from the MIMIC-IV demo database.

Source: MIMIC-IV Clinical Database Demo 2.2 (PhysioNet, ODbL v1.0), read from
the SQLite copy provided by ``tanat.dataset.access("mimic4")``. Each row of the
``"hosp/procedures_icd"`` table is kept (one event per coded procedure, dated
to the day), with the readable ``long_title`` joined from
``"hosp/d_icd_procedures"`` on ``(icd_code, icd_version)``.

Usage:
  python data/build_procedures_csv.py            # (re)write data/mimic_procedures.csv
  python data/build_procedures_csv.py --check    # compare without writing; exit 0 if equal
"""

from __future__ import annotations

import argparse
import csv
import os
import sqlite3
import sys
from collections import Counter
from typing import Iterable

from tanat.dataset import access

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(SCRIPT_DIR, "data", "mimic_procedures.csv")
COLUMNS = ["subject_id", "time", "icd_code", "icd_version", "long_title"]

# ICD-9 and ICD-10 codes live in the same column: the version disambiguates
# them, so the join must use both. seq_num / hadm_id only fix a stable order.
_PROCEDURES_SQL = (
    "SELECT p.subject_id, substr(p.chartdate, 1, 10), p.icd_code, "
    "p.icd_version, COALESCE(d.long_title, '') "
    'FROM "hosp/procedures_icd" p '
    'LEFT JOIN "hosp/d_icd_procedures" d '
    "ON d.icd_code = p.icd_code AND d.icd_version = p.icd_version "
    "ORDER BY p.subject_id, p.chartdate, CAST(p.hadm_id AS INTEGER), "
    "CAST(p.seq_num AS INTEGER)"
)


def load_rows(db_path: str) -> list[tuple[str, str, str, str, str]]:
    """Read the SQLite db and return the CSV rows in canonical order."""
    con = sqlite3.connect(db_path)
    try:
        return [tuple(r) for r in con.execute(_PROCEDURES_SQL).fetchall()]
    finally:
        con.close()


def read_csv(path: str) -> list[tuple[str, ...]]:
    """Read the versioned CSV back into rows (header stripped)."""
    with open(path, newline="", encoding="utf-8") as fh:
        return [tuple(row) for row in csv.reader(fh)][1:]


def write_csv(path: str, rows: Iterable[tuple[str, ...]]) -> None:
    """Write rows to ``path`` with the canonical header and \\n line endings."""
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(COLUMNS)
        writer.writerows(rows)


def _diff(versioned: list, rebuilt: list) -> None:
    print(f"versioned rows: {len(versioned)}", file=sys.stderr)
    print(f"rebuilt rows:   {len(rebuilt)}", file=sys.stderr)
    v, r = Counter(versioned), Counter(rebuilt)
    for row, count in (v - r).items():
        print(f"missing in rebuilt: {row} x{count}", file=sys.stderr)
    for row, count in (r - v).items():
        print(f"extra in rebuilt:   {row} x{count}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare the rebuilt rows to the versioned CSV without writing",
    )
    args = parser.parse_args(argv)

    rebuilt = load_rows(str(access("mimic4")))

    if args.check:
        if not os.path.isfile(CSV_PATH):
            print(f"error: versioned CSV not found: {CSV_PATH}", file=sys.stderr)
            return 1
        versioned = read_csv(CSV_PATH)
        # Contract: equal columns and equal rows after sorting.
        if sorted(versioned) == sorted(rebuilt):
            print("ok: rebuilt rows match the versioned CSV")
            return 0
        print("mismatch: rebuilt rows differ from the versioned CSV", file=sys.stderr)
        _diff(versioned, rebuilt)
        return 1

    write_csv(CSV_PATH, rebuilt)
    print(f"wrote {len(rebuilt)} rows to {CSV_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
