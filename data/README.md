# data/mimic_admissions_pool.csv — provenance

`mimic_admissions_pool.csv` is a small extraction of the **MIMIC-IV Clinical
Database Demo** used by the demo pipeline. This file documents where the data
comes from, how it is rebuilt, and under what licence it is distributed.

## Source

**MIMIC-IV Clinical Database Demo, version 2.2**, published on PhysioNet:
https://physionet.org/content/mimic-iv-demo/2.2/
(DOI [10.13026/dp1f-ex47](https://doi.org/10.13026/dp1f-ex47)).

> "Here, we have provided an openly-available demo of MIMIC-IV containing a
> subset of 100 patients."
> — PhysioNet, MIMIC-IV Clinical Database Demo, Abstract.

The CSV has 306 rows for the 100 demo patients: their 275 admissions
(`hosp/admissions`) plus one `DEATH` row for each of the 31 patients whose date
of death is recorded (`hosp/patients.dod`). Times are truncated to the day.

## How it is rebuilt

`data/build_csv.py` rebuilds the CSV from the copy of the demo that TanaT
provides as an SQLite database (`tanat.dataset.access("mimic4")`):

```sql
-- every admission, timestamps truncated to the day
SELECT subject_id, substr(admittime, 1, 10), substr(dischtime, 1, 10),
       admission_type, admission_location
FROM "hosp/admissions"
ORDER BY subject_id, admittime;
```

then, for each patient whose `"hosp/patients".dod` is set, appends one row
`subject_id, <dod-date>, <dod-date>, DEATH,` after that patient's admissions.

From the repo root:

```bash
# (re)write data/mimic_admissions_pool.csv
uv run -q --no-project --with-requirements requirements.txt python data/build_csv.py
# compare with the versioned file without writing (exit 0 if equal)
uv run -q --no-project --with-requirements requirements.txt python data/build_csv.py --check
```

## Licence

The MIMIC-IV Clinical Database Demo is distributed under the **Open Data
Commons Open Database License v1.0 (ODbL v1.0)**:

> "Anyone can access the files, as long as they conform to the terms of the
> specified license. License: Open Data Commons Open Database License v1.0"
> — PhysioNet, MIMIC-IV Clinical Database Demo, Access section.

This extraction is a derived database and is redistributed under the same
licence: ODbL v1.0 (https://opendatacommons.org/licenses/odbl/1-0/).

## Citation

Johnson, A., Bulgarelli, L., Pollard, T., Horng, S., Celi, L. A., & Mark, R.
(2023). MIMIC-IV Clinical Database Demo (version 2.2). *PhysioNet*.
https://doi.org/10.13026/dp1f-ex47
