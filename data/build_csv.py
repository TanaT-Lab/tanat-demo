#!/usr/bin/env python3
"""Rebuild data/mimic_admissions_pool.csv from the MIMIC-IV demo database.

Source: MIMIC-IV Clinical Database Demo 2.2 (PhysioNet, ODbL v1.0), read from
the SQLite copy provided by ``tanat.dataset.access("mimic4")``. Each row of the
``"hosp/admissions"`` table is kept (dates truncated to the day), plus one
synthetic ``DEATH`` row per patient whose ``"hosp/patients".dod`` is set (the
date of death, with an empty admission location).

Usage:
  python data/build_csv.py            # (re)write data/mimic_admissions_pool.csv
  python data/build_csv.py --check    # compare without writing; exit 0 if equal
"""

from __future__ import annotations

import argparse
import csv
import os
import sqlite3
import sys
from typing import Iterable

from tanat.dataset import access

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(SCRIPT_DIR, "data", "mimic_admissions_pool.csv")
COLUMNS = ["subject_id", "time", "endtime", "admission_type", "admission_location"]

_ADMISSIONS_SQL = (
    'SELECT subject_id, substr(admittime, 1, 10), substr(dischtime, 1, 10), '
    'admission_type, admission_location '
    'FROM "hosp/admissions" ORDER BY subject_id, admittime'
)


def load_rows(db_path: str) -> list[tuple[str, str, str, str, str]]:
    """Read the SQLite db and return the CSV rows in canonical order."""
    con = sqlite3.connect(db_path)
    try:
        cur = con.cursor()
        admissions = cur.execute(_ADMISSIONS_SQL).fetchall()
        dod = dict(cur.execute('SELECT subject_id, dod FROM "hosp/patients"').fetchall())
    finally:
        con.close()

    by_subject: dict[str, list] = {}
    for row in admissions:
        by_subject.setdefault(row[0], []).append(row)

    subjects = sorted(set(by_subject) | {s for s, d in dod.items() if d})

    rows: list[tuple[str, str, str, str, str]] = []
    for subject in subjects:
        rows.extend(by_subject.get(subject, []))
        death = dod.get(subject)
        if death:
            day = death[:10]
            rows.append((subject, day, day, "DEATH", ""))
    return rows


def read_csv(path: str) -> list[tuple[str, str, str, str, str]]:
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
    from collections import Counter

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

    db_path = str(access("mimic4"))
    rebuilt = load_rows(db_path)

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
