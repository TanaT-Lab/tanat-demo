# data/mimic_admissions_pool.csv — provenance

`mimic_admissions_pool.csv` is a small extraction of the **MIMIC-IV Clinical
Database Demo** that the demo pipeline consumes. This file documents where the
data comes from, how it is rebuilt, and under what licence it is distributed.

## Origin

- **Dataset:** MIMIC-IV Clinical Database Demo
  ([PhysioNet page](https://physionet.org/content/mimic-iv-demo/)).
  > "Here, we have provided an openly-available demo of MIMIC-IV containing a
  > subset of 100 patients."
  > — PhysioNet, MIMIC-IV Clinical Database Demo, Abstract.
- **Version:** not stated by the Zenodo record (its description only says it
  "contains the demo dataset" and links the MIMIC-IV project). The database
  uses the `hosp/` module layout introduced in MIMIC-IV 2.0, so it is most
  likely the latest demo, **version 2.2**
  (DOI [10.13026/dp1f-ex47](https://doi.org/10.13026/dp1f-ex47)), to confirm
  with the record's author.
- **Distribution used by TanaT:** the SQLite database served by
  `tanat.dataset.access("mimic4")`, downloaded from
  [Zenodo record 16368465](https://zenodo.org/records/16368465)
  ("TanaT - MIMIC4 database", published 2025-07-23, creator Arnaud Duvermy).

The CSV has 306 rows for 100 patients. It matches the admissions of the 100
demo patients plus one synthetic `DEATH` row per patient whose date of death is
recorded (31 patients), which is why the row count (306) exceeds the 275
admissions in the demo's `hosp/admissions` table.

## The query used

`data/build_csv.py` rebuilds the CSV from the SQLite database returned by
`tanat.dataset.access("mimic4")`:

```sql
-- every admission, timestamps truncated to the day
SELECT subject_id, substr(admittime, 1, 10), substr(dischtime, 1, 10),
       admission_type, admission_location
FROM "hosp/admissions"
ORDER BY subject_id, admittime;
```

then, for each patient whose `"hosp/patients".dod` is set, appends one row

```
subject_id, <dod-date>, <dod-date>, DEATH,
```

after that patient's admissions.

## How to rebuild

From the repo root:

```bash
uv run -q --no-project --with-requirements requirements.txt python data/build_csv.py
```

This writes `data/mimic_admissions_pool.csv`. To verify it matches the
versioned file without overwriting it:

```bash
uv run -q --no-project --with-requirements requirements.txt python data/build_csv.py --check
```

`--check` exits 0 only if the rebuilt rows equal the versioned CSV (same
columns, same rows after sorting).

## Licence

Two licences apply to the sources of this file, as stated by each provider:

- **Zenodo record 16368465** ("TanaT - MIMIC4 database", the SQLite bundle that
  TanaT downloads) declares in its record metadata a licence of
  **Creative Commons Attribution 4.0 International (CC-BY-4.0)**:
  `"license": {"id": "cc-by-4.0"}` (from
  https://zenodo.org/api/records/16368465).
- **PhysioNet** for the underlying MIMIC-IV Clinical Database Demo declares the
  **Open Data Commons Open Database License v1.0 (ODbL v1.0)**:
  > "Anyone can access the files, as long as they conform to the terms of the
  > specified license. License: Open Data Commons Open Database License v1.0"
  > — PhysioNet, MIMIC-IV Clinical Database Demo, Access section (same
  > licence for versions 1.0 and 2.2).

Both providers should be cited when using the data. Suggested citations:

- Johnson, A., Bulgarelli, L., Pollard, T., Horng, S., Celi, L. A., & Mark, R.
  (2023). MIMIC-IV Clinical Database Demo (version 2.2). *PhysioNet*.
  https://doi.org/10.13026/dp1f-ex47
- Duvermy, A. TanaT - MIMIC4 database. *Zenodo*.
  https://doi.org/10.5281/zenodo.16368465
