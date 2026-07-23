# Huntington Weinland additions (manual external acquisitions)

Five catalog records sourced from The Huntington Library's **William & Clara
Weinland Collection, photCL 39** (Potrero/Morongo album), CONTENTdm collection
`p15150coll2`, added 2026-07-22.

These were inserted **manually** into `data/catalog.json` (+ site copy + CSV),
NOT produced by `catalog_pipeline.py` — this directory is deliberately **not** a
configured pipeline source. IDs were still derived with the pipeline's scheme
(`file_id = stable_id("file", normalize_path(<this file>))`,
`record_id = stable_id("img", sha256(<this file>))`) so a future ingestion would
reproduce them if this dir is added to `config/catalog.config.json` sources.

- `NN_slug.jpg` — the cropped print (the catalog master; source for the IDs)
- `fullpages/<pointer>_fullpage.jpg` — pristine full IIIF album-page scan (provenance)

| NN | record_id | Huntington id | title |
|----|-----------|---------------|-------|
| 01 | img_c453ab61e0df544e | 13054 | Wickiup (arrowweed dwelling) |
| 02 | img_7235362ef72b0a0b | 13067 | Cooking shelter (G.P. Thresher, 1900) |
| 03 | img_9b7ed2e698bcc615 | 12895 | Rice and his children |
| 04 | img_0e0e59f901586c2a | 13001 | 'Old Maria' weaving a basket |
| 05 | img_c005864c8b7938d0 | 12417 | John Morongo's grandchildren, Potrero |

**Rights:** all `Permission required` — Huntington reproduction permission AND
Morongo Band cultural consultation are required before any publication or use.
