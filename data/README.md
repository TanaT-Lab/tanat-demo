# data/*.csv — provenance

`mimic_admissions_pool.csv` and `mimic_procedures.csv` are small extractions of
the **MIMIC-IV Clinical Database Demo** used by the demo pipelines. This file
documents where the data comes from, how it is rebuilt, and under what licence
it is distributed. Both files share the same source and licence.

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

## mimic_procedures.csv

The 722 coded procedures (`hosp/procedures_icd`) of the 92 demo patients who
have at least one, one row per event: `subject_id, time (day), icd_code,
icd_version, long_title`. `long_title` comes from `hosp/d_icd_procedures`,
joined on `(icd_code, icd_version)` (ICD-9 and ICD-10 codes share the column).
Read `icd_code` and `subject_id` as strings: `0331` is not a number.

```sql
SELECT p.subject_id, substr(p.chartdate, 1, 10), p.icd_code, p.icd_version,
       COALESCE(d.long_title, '')
FROM "hosp/procedures_icd" p
LEFT JOIN "hosp/d_icd_procedures" d
  ON d.icd_code = p.icd_code AND d.icd_version = p.icd_version
ORDER BY p.subject_id, p.chartdate, CAST(p.hadm_id AS INTEGER), CAST(p.seq_num AS INTEGER);
```

```bash
uv run -q --no-project --with-requirements requirements.txt python data/build_procedures_csv.py
uv run -q --no-project --with-requirements requirements.txt python data/build_procedures_csv.py --check
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
