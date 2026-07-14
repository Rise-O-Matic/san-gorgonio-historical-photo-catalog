# San Gorgonio Pass — new external candidates (retrieved 2026-07-10)

Sixteen historically relevant photographs found on the open internet that are **not**
represented in the current image set. The existing catalog is almost entirely
Beaumont-town subjects; these fill real geographic and thematic gaps across the wider
Pass — the town of Banning, Cabazon, the Colorado River Aqueduct, the Gilman Ranch
stage station, and Native leaders/artisans of the Pass (Serrano/Cahuilla).

They are recorded as research candidates in `config/catalog.config.json`
(`research_candidates`) and mirrored to `data/candidate-reviews.json` and
`site/data/candidate-reviews.json` by the pipeline. They carry no local `record_id`
because they have no counterpart in the set, and none is promoted to a master — rights
must be cleared first (see below). Re-run `python scripts/add_pass_candidates.py` to
reapply without a full rebuild.

## Sources searched

- **Calisphere** — Banning Library District Local History Collection (collection 1582 /
  institution 46), which explicitly documents "the history of the San Gorgonio Pass from
  the 1880s to the Present … Banning, Beaumont, Cabazon, Cherry Valley." 381 items; the
  single richest open source for the Pass.
- **Calisphere** — Pomona Public Library, Frasher Foto Postcard Collection.
- **Calisphere** — USC Digital Library / California Historical Society Collection at Stanford.
- Also scanned: Library of Congress PPOC, Wikimedia Commons (`Category:San Gorgonio Pass`),
  Online Archive of California. Calisphere carried the strongest Pass-specific holdings.

## Rights tiers

| Tier | Count | Meaning |
|---|---:|---|
| Public Domain (CC BY) | 1 | Reusable with attribution — could be downloaded and added as a real record |
| Permission Required | 1 | Pomona/Frasher: personal or research use only |
| Unclear ("copyright status unknown") | 14 | Banning Library District statement; clear rights before any reuse |

The Banning Library District items all carry the collection's uniform "Copyright status
unknown" statement, so age alone is **not** treated as permission (matches the catalog's
default posture).

## Candidates

### Town of Banning (no Banning-town imagery previously in the set)
1. **The Banning Southern Pacific Railroad Depot** — c. 1910 — CBAN_003 — [item](https://calisphere.org/item/ark:/13030/c8c53hwn/)
2. **"The Banning" hotel (Bryant House / San Gorgonio Inn)** — c. 1890 — CBAN_363 — [item](https://calisphere.org/item/ark:/13030/c8v69k8c/)
3. **Union Ice Company delivery wagon** — early 1900s — CBAN_349 — [item](https://calisphere.org/item/ark:/13030/c8c82b11/)
4. **Banning fruit drying yard (E. L. Robertson's, 4th St.)** — c. 1910 — CBAN_052 — [item](https://calisphere.org/item/ark:/13030/c8cn71xn/)

### Cabazon
5. **Cabazon Southern Pacific Railroad Depot** — Sep 1930 — CBAN_357 — [item](https://calisphere.org/item/ark:/13030/c83b60vc/)

### Colorado River Aqueduct (1930s regional engineering; thousands of Pass jobs)
6. **Inside the aqueduct tunnel during construction, Cabazon** — 1936 — CBAN_226 — [item](https://calisphere.org/item/ark:/13030/c8cz37w8/)
7. **West approach to the San Jacinto tunnel** — c. 1930s — CBAN_149 — [item](https://calisphere.org/item/ark:/13030/c8d50k00/)

### Gilman Ranch (Banning stage-stop ranch, now a county museum)
8. **The Gilman Ranch House (built 1897)** — c. 1900 — CBAN_179 — [item](https://calisphere.org/item/ark:/13030/c84f1nrb/)
9. **Pope adobe "old stage station" on the Gilman Ranch** — c. 1890s — CBAN_335 — [item](https://calisphere.org/item/ark:/13030/c8b27w15/)

### Native peoples of the Pass (deepens beyond the catalog's Morongo Big House)
10. **Portrait of Captain John Morongo** (Serrano; reservation namesake) — c. 1890 — CBAN_120 — [item](https://calisphere.org/item/ark:/13030/c8d798dr/)
11. **Fig Tree John, Cahuilla tribal leader** — early 1900s — CBAN_382 — [item](https://calisphere.org/item/ark:/13030/c8k9388x/)
12. **Cahuilla basket maker, Morongo Indian Reservation** — c. 1900 — CBAN_112 — [item](https://calisphere.org/item/ark:/13030/c8k07299/)

### Beaumont subjects new to the catalog
13. **Late-1950s aerial of downtown Beaumont at the 99/60 junction** (pre I-10) — c. 1960 — CBAN_325 — [item](https://calisphere.org/item/ark:/13030/c8rf5vqg/)
14. **San Gorgonio Catholic Church, 7th & Palm** (built 1908) — 1908 — [item](https://calisphere.org/item/ark:/13030/c889157p/) — *item page returned HTTP 403 at retrieval; metadata from Calisphere search preview, reconfirm on next access.*

### Pass geography (other open collections)
15. **San Gorgonio Pass from the hills above Whitewater** — Burton Frasher Sr., 1947 — Pomona Public Library, F6945 — [item](https://calisphere.org/item/ark:/13030/kt7g5020cv/) — *Permission Required.*
16. **Women beside a waterfall on the trail to the summit of San Gorgonio** — 1900–1915 — USC/CHS chs-m2795 — [item](https://calisphere.org/item/dba6aef0b1f6e384e2c910ee5d279e4d/) — **Public Domain / CC BY**, credit "University of Southern California. Libraries" and "California Historical Society."

## Suggested next steps

- **#16 (summit waterfall)** is rights-clear (CC BY). It is the natural first acquisition:
  download from `http://thumbnails.digitallibrary.usc.edu/CHS-43008.jpg` (or request a
  higher-resolution master from USC), place it in a source folder, and rerun the pipeline
  to make it a real record with attribution.
- For the Banning Library District items, contact the district (the Calisphere "Contact
  Owner" link) to clear reuse before promoting any to masters.
- The Banning collection has ~365 more items across 1880s–1970s; a second pass could add
  Ramona Pageant, Stagecoach Days, citrus/almond industry, and additional Cahuilla/Serrano
  material if the mural scope wants them.
