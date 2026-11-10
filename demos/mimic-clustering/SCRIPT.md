## intro

{#welcome}Welcome to this demonstration of tanat.

{#what}tanat, for Temporal Analysis of Trajectories, is a Python library for temporal sequence analysis, with a focus on patient care pathways. {#syntax}It brings well-established methods behind a clear, explicit and flexible syntax. {#data}Unlike time series libraries, it handles irregular, symbolic data: the kind you actually find in health records.

{#entity}Everything starts from one building block, the entity: a single observation in a patient's journey, like a hospital stay. {#sequence}Chained together for one patient, entities form a sequence. {#types}tanat offers three kinds: event sequences for timestamps, state sequences for successive conditions, and interval sequences for events with a duration.

{#mimic}Let's put this into practice on MIMIC-IV, a public database of real, de-identified hospital records from a Boston medical center, widely used in health research. {#open}Its open demo covers one hundred patients: every hospital stay, with its admission type, such as emergency, elective or observation. {#turn}We will turn these raw records into clusters of patient trajectories.

## step1

We start from a plain CSV of 306 admission records: one row per stay, with its start date, end date and admission type. Pandas loads it as usual.

Then a single call, build intervals, turns these rows into a pool: one interval sequence per patient, 100 in total. We declare the admission type as categorical, as the metrics will need it later. Printing the pool gives a quick summary of its sequences and features.

## step2

Before any analysis, let's look at the data. Visualizations use a fluent API: you chain methods to set colors and a title, then draw.

This bar plot shows admission types across all patients. Emergency admissions, in yellow, clearly dominate: that is where we will focus.

## step3

Clinical studies often target a subgroup. In tanat, a criterion describes it with a Polars expression: here, patients with at least one emergency admission.

The criterion selects patients, not single admissions, so each patient keeps their complete history. The cohort goes from 100 to 64 patients.

## step4

First, the cohort on the calendar. Journeys are scattered across a whole century: MIMIC shifts each patient's dates into the future to protect privacy, so calendar dates cannot be compared between patients.

To compare journeys, we align them on a common reference point, called T zero: each patient's first emergency admission.

On the aligned timeline, negative days come before that emergency, positive days after. Every journey now starts from the same point, and patterns become visible.

## step5

Now, clustering. To compare patients, tanat builds a similarity in two layers. At the entity level, a Hamming metric compares two admissions by their type. At the sequence level, an edit distance compares whole journeys, normalized by their length, so that patients are compared on their pattern rather than on their number of stays.

A hierarchical clusterer then groups the 64 patients into three clusters, stored with each patient as static data.

## step6

Finally, one timeline per cluster, faceted in a few chained calls. Three profiles stand out: patients seen once for an emergency, patients with a few stays, sometimes ending in death, and patients readmitted again and again. This is exactly the kind of readmission pattern clinicians want to spot.

## end

To wrap up: in about sixty lines of code, we went from a raw CSV to meaningful patient clusters, with a workflow that stays readable and reproducible.

Thank you for watching. To start your own analysis, visit the tanat documentation.
