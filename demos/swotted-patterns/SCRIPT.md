## intro

{#welcome}Welcome to this demonstration of tanat.

{#what}tanat, for Temporal Analysis of Trajectories, is a Python library for patient care pathways: irregular, symbolic sequences of events, the kind you actually find in health records. {#bridge}Today's question: how do you feed these trajectories to a machine learning model, and bring what it learns back? tanat is the bridge: trajectories in, tensors out, and patterns back in.

{#mimic}We use MIMIC-IV, a public database of real, de-identified hospital records from a Boston medical center, widely used in health research. {#open}Its open demo covers one hundred patients; here, we look at their procedures, such as a catheter placement or mechanical ventilation. {#model}The model is SWoTTeD, which learns recurring temporal patterns from a tensor. It runs on PyTorch, but any model that reads a tensor would do.

## step1

We start from a CSV of 722 procedures for 92 patients, each with its date and a readable title. MIMIC shifts each patient's dates to protect privacy, so we count days from each patient's first procedure, and keep the first year.

Then a single call, build events, turns these rows into a pool: one event sequence per patient.

## step2

Two hundred and eighty-six different procedures is a lot for so few patients. A criterion keeps the thirty most frequent ones, and a second one drops the patients left with nothing. Sixty-three patients remain.

## step3

Here is the bridge out of tanat. One call, to tensor, puts every patient on a grid: one row per day, one column per procedure.

It returns three things that stay in sync: the tensor itself, sixty-three patients by three hundred and forty-five days by thirty procedures; the patient ids; and the procedure names. That is exactly what a learning model needs, and what we will need to read its results.

## step4

The tensor goes straight into SWoTTeD; we only reorder its axes. We ask for five patterns, each spanning one week. Training takes less than half a minute on a laptop, no GPU needed.

## step5

Each pattern is a small picture: procedures over seven days. Because to tensor kept the procedure names, we can read them right away: central lines, breathing support, feeding.

A word of caution: sixty-three patients is a small cohort. These patterns illustrate the workflow; they are not a clinical finding.

## step6

Now, the bridge back. Each patient gets the pattern that fits them best, or no pattern at all, and this label goes back into the pool, like any other patient attribute. A quick check confirms that every label lands on the right patient.

From there, it is the usual tanat toolbox: one timeline per pattern, in a few chained calls. In color, the procedures of each patient's pattern; in grey, everything else.

## end

To wrap up: tanat turned care pathways into a tensor a model can learn from, then brought what the model learned back into the trajectories. Your data stays in tanat; your models plug right in.

Thank you for watching. To start your own analysis, visit the tanat documentation.
