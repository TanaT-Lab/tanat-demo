
Welcome to this demonstration of tanat.

tanat, which stands for Temporal Analysis of Trajectories, is an extensible Python library designed for temporal sequence analysis, with a primary focus on patient care pathways.

The philosophy behind tanat is simple. We want to simplify temporal analysis of care pathways by providing useful, well-established features, while maintaining a clear, flexible, and explicit code syntax. Unlike traditional time series libraries, tanat handles irregularly sampled, symbolic data. This is exactly the kind of data you actually find in healthcare records.

To handle this complexity, our data model relies on a simple building block: the Entity. Think of an Entity as a single observation in a patient's journey—like a specific hospital visit or a clinical encounter. When we chain these Entities together for a given individual, we create a Sequence.

To capture the full diversity of temporal data, tanat allows you to navigate between three specialized formats: the EventSequence for precise timestamps, the StateSequence to follow successive conditions, and the IntervalSequence to analyze events with a specific duration.

It’s a powerful yet intuitive way to transform scattered medical observations into a structured analytical timeline.

To put this into practice, we’ll use tanat to analyze hospital readmission patterns from the MIMIC-IV dataset. We’re going to take raw, messy admission records and transform them into clear, clustered patient trajectories, illustrating one possible workflow with the library


Before any analysis, we need to understand our data. tanat provides a fluent API for visualization, where you simply chain method calls to configure your plot.

For example, this histogram shows the distribution of admission types across all patients. We can clearly see that emergency admissions—shown in yellow—dominate the dataset. This type of visual insight is key to helping scientists decide on the best analysis strategy.

With this understanding, let's now filter our cohort.



Clinical studies often focus on specific patient subgroups. tanat provides a criterion-based filtering system using pandas-like query syntax.

In this step, we filter to keep only patients who have at least one emergency admission. Notice that the filter operates at the sequence level. This means we keep entire patient sequence, not just individual observations. This reduces our cohort from 100 to 64 patients, while preserving their complete admission history.

Next, we need to align our sequences in time.



Temporal analysis often requires aligning sequences to a common reference point. In tanat, this is called T0, or the index date.

Here, we set T0 as the first emergency admission for each patient. After alignment, all timelines are expressed relative to this reference. Negative days represent time before the first emergency, and positive days represent time after.

The timeline visualization now shows patient sequences in relative time. This makes patterns much more comparable across patients who had different admission dates.

Now comes the interesting part: clustering.

To compare patient journeys, tanat uses a compositional approach to define similarity.

We build our metric in two layers: first, at the Entity level, we use a Hamming metric to compare the attributes of individual observations. Then, we plug this into an Edit Distance at the Sequence level to compare entire patient journey.

Once the distances are calculated, we apply a Hierarchical Clusterer. Assigning each patient to a cluster is then handled very easily through what we call static data. Here, these clusters are built taking into account both the nature of the events and their temporal order.


Finally, we visualize our results using faceted plots, showing one timeline per cluster. This is where the tanat API really shines: you can build a complex, publication-ready figure in just a few lines of code thanks to its intuitive and flexible design.As we look at the results, each cluster reveals a distinct readmission pattern. Some patients have single emergency visits, while others show repeated admissions over extended periods.  


To wrap up, in approximately 30 lines of code, we went from raw CSV data to meaningful patient clusters.

tanat makes this possible by providing a fluent API that abstracts the complexity of temporal analysis, keeping your workflow readable and fully reproducible. It’s an intuitive way to bridge the gap between raw medical records and actionable clinical insights.

Thank you for watching this demonstration. To learn more and start your own analysis, visit our documentation.