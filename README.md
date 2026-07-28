# Beaumont Historical Photo Catalog

**Live site: https://rise-o-matic.github.io/san-gorgonio-historical-photo-catalog/**

A zero-cost, static catalog for reviewing historical photographs for the Beaumont Library District timeline mural. The source collection is treated as read-only. The pipeline creates a portable JSON/CSV catalog, optimized site images, duplicate reports, print-viability estimates, a client selection portal, and a research-candidate workspace.

## Current inventory

- 348 unique candidate files across the non-overlapping scan roots
- 348 readable files; no Google Drive placeholders need to be made available offline
- 263 grouped historical-image records
- 17 curated `Mural Images` records, prominently flagged and initially selected
- Formats: 289 JPG, 35 JPEG, 19 PNG, 3 WebP, 1 HEIC, and 1 PDF
- Detected review pairs: 77 exact, 23 re-encoded/resized, 4 rotated/mirrored, and 2 probable

The two narrow historical-photo paths are beneath the broad `historical photos` root and are deliberately skipped as scan roots. Their membership and higher priority are still attached to files found inside them. Full results are in [`data/reports/inventory.json`](data/reports/inventory.json), [`data/reports/duplicate-review.csv`](data/reports/duplicate-review.csv), and [`data/reports/unreadable-files.csv`](data/reports/unreadable-files.csv).

## Run the catalog

Requirements: Python 3.10+ and Pillow. FFmpeg is optional but required for HEIC/AVIF decoding. Tesseract is optional for local OCR.

```powershell
python -m pip install -r requirements.txt
python scripts/catalog_pipeline.py
python -m http.server 8000 --directory site
```

Open `http://localhost:8000`. Do not open `site/index.html` directly with `file://`; browsers block its JSON request.

The pipeline capability-detects Tesseract. This machine does not currently have it, so the generated OCR objects explicitly say `unavailable`. Install Tesseract and rerun to populate visible-text suggestions, or use `--skip-ocr` to make that choice explicit. No cloud AI or paid service is required.

## What the pipeline does

- Prevents output paths from being placed inside any source tree.
- Avoids nested-source double scans while retaining source membership and priority.
- Creates stable file IDs from normalized paths and historical-image IDs from content hashes.
- Records SHA-256, file size, format, dimensions, frames, EXIF, filesystem dates (explicitly *not* historical dates), filename/folder suggestions, sidecars, website captions, OCR state, and provenance facts.
- Generates thumbnails and previews without copying or modifying originals.
- Compares exact hashes plus perceptual hashes across resize/re-encode, rotation/mirroring, and center-crop variants.
- Groups strong duplicate/version matches while leaving probable and related photos for manual review.
- Recommends a master from pixel area, measured edge detail, format/compression preference, completeness, and curated priority—not filename alone.
- Calculates crop- and quality-adjusted native print dimensions at 200, 150, 100, and 50 PPI. The portal lets reviewers change the quality factor among 100%, 75%, and 50%.

Perceptual matching is a review aid, not a final historical judgment. Inspect every non-exact group in the alternate-version comparison and duplicate CSV before production use.

## Client portal

The portal provides timeline and grid views, search, era/subject/location/print/research/selection filters, an undated section, editable working title/date/caption and quality factor, alternate-version comparison, local comments, persistent browser selections, and JSON download/copy reports. Low-resolution references remain visible.

### Mural sequence builder

From the selection page, **Arrange & preview mural** opens a mural-proof workspace: the selected photographs are laid out as a horizontal, left-to-right ribbon at a consistent frame height that mimics the wall, each frame showing its position number, estimated year, working title, caption, credit, and print classification/size. Frames default to timeline (chronological) order; **any frame can be dragged to reposition it**, and the manual order is saved to that browser's `localStorage` alongside the selections. A **Sort by date** button restores strict chronological order, an S/M/L control adjusts the preview frame height, the remove control drops a frame from the selection, and **Download sequence** exports the ordered list (position, id, title, year, caption, credit, print size, comment, and source paths) as JSON. Like the rest of the portal, this is browser-local until the sequence report is shared.

The current 20-photo timeline builder also loads [`data/timeline-milestones.json`](data/timeline-milestones.json), a maintained one-to-one mapping from each selected record ID to the historical milestone headline that will sit above its photo/caption complex in the print mural. The published photo lineup is authoritative; milestone dates describe the represented event and may overlap where a thematically arranged photograph depicts an earlier event. Headlines, context, and citations appear in the builder, quick view, Word export, and embedded JSON manifest. A compact designer handoff is kept in [`data/timeline-milestone-handoff.md`](data/timeline-milestone-handoff.md).

Selections live in that browser's `localStorage`; they are not sent anywhere and require no client account. The client must download or copy a report to share the shortlist. A truly free form endpoint can be added later, but the default intentionally has no third-party data dependency.

### Timeline mural mockup

[`site/mural-mockup.html`](site/mural-mockup.html) is a standalone presentation proof
of the full mural as a single left-to-right timeline ribbon (1800–1988). It overlays
the two halves of the plan: **Ready** frames are the production-grade taste-match
stand-ins that can be printed today (full colour, print size shown), and **Gap** frames
are Kelly's curated picks that have no printable version — shown desaturated and marked
*To source*, each naming its re-acquisition track (A online / B Malki Museum + Morongo
Tribe / C Library storage). Every frame carries a one-line **rationale** for why the
image earns a place in a Beaumont timeline. The gaps cluster at the founding era (Native
and pioneer origins) and the modern tail, making the sourcing priorities self-evident.
The page is built by `python scripts/build_mural_mockup.py`, which reads the
taste-match core from `data/mural-shortlist.json` (see `scripts/score_taste_match.py`)
plus a hand-authored rationale/track layer and writes `data/mural-mockup.json` +
`site/data/mural-mockup.json`. Reachable from the catalog masthead.

For a presentation to library staff, `python scripts/build_mural_deck.py` renders the
same `data/mural-mockup.json` into an editable slide deck
(`data/research-assets/beaumont-mural-mockup.pptx`, 24 slides, 16:9): a title, a
how-to-read slide, one slide per frame in chronological order (gap images grayscaled
and flagged with their re-acquisition track), and a closing "what we need" ask
grouped by track. Images are embedded as bytes (via Pillow, capped at 1400 px) so no
hosting is needed; opening the `.pptx` in Google Slides gives an editable, co-ownable
deck. Regenerate after re-sourcing to refresh it — the deck never drifts from the data.

The separate [`site/research.html`](site/research.html) workspace prioritizes curated and low-resolution records, records source/asset URLs, dimensions, institution captions, match class, confidence, retrieval date, rights, and validation notes, and exports candidate-review JSON. Candidates stay separate until approved.

## Editable files and generated outputs

- `config/catalog.config.json`: paths, priorities, image sizes, crop allowance, PPI, quality factors, research sources, and seeded research candidates
- `data/catalog.json` / `data/catalog.csv`: consolidated portable catalog
- `data/files.csv`: source-file manifest
- `data/research-queue.json`: prioritized research queue
- `data/candidate-reviews.json`: source candidates kept separate from masters
- `data/reference-numbers.json`: permanent mapping from internal IDs to human-readable references
- `data/editorial-captions.json`: maintained caption + attribution layer (every record captioned and credited)
- `data/reports/`: inventory, duplicate-review, and unreadable-file reports
- `site/data/` and `site/assets/`: deployable portal data and optimized images

Generated catalog edits made in the browser are local review overrides. To make verified changes authoritative for every visitor, update the source metadata/configuration or edit the maintained editorial-override JSON layer before rerunning.

## Reference numbers

Every catalog photograph has a stable reference in the form `BLD-0001`; every
external research candidate has a reference in the form `BLD-C001`. Use these
numbers in agent prompts, review notes, email, and selection discussions. The
opaque `img_…` and `candidate_…` IDs remain the machine identifiers.

Assignments live in `data/reference-numbers.json`. They are never renumbered or
reused, even if the chronological sort changes or an entry is removed. The full
pipeline and manual-record helper preserve the registry automatically. Run
`python scripts/assign_reference_numbers.py` to backfill or repair generated
catalog, CSV, research-queue, and candidate-review copies.

### Editorial date overrides

`data/editorial-overrides.json` is a maintained research layer that assigns a date range to every record the pipeline could not date on its own. The pipeline emits `Undated` for any group without a single unambiguous filename year; this layer carries the results of manual research — filename/masthead/postmark annotations, the [San Gorgonio Pass Historical Society timeline](https://httpssgphs.org), Beaumont institutional histories, and visual dating from vehicles, dress, architecture, and postcard format. Each entry records `date_start`, `date_end`, a human-readable `display`, a `confidence` level (`confirmed` / `high` / `medium` / `low`), and a one-line `basis`. `scripts/catalog_pipeline.py` re-applies this file on every run (see `apply_editorial_overrides`), so researched dates survive regeneration. All 164 previously undated records are now dated; edit the file and rerun, or run `python scripts/author_date_overrides.py` to reapply to the current catalog without a full rebuild.

### Editorial captions and attributions

`data/editorial-captions.json` is a maintained research layer that gives **every**
record a caption and an attribution — the project's standing requirement that
nothing is left uncaptioned or uncredited, with attribution recorded honestly as
`Unknown` when no holder or creator can be established. Sources, in priority
order: (1) the San Gorgonio Pass Historical Society timeline
([httpssgphs.org](https://httpssgphs.org)), whose `<figcaption>` carries a
published caption and an explicit credit line; (2) provenance embedded in the
original collection filenames (e.g. "… from Beaumont Library District",
"calisphere", "courtesy Steve Lech postcard collection", "leslie rios
postcards"); and (3) descriptive captions written from the filename text and the
researched date where no published caption exists. Each entry records `caption`,
`attribution`, an `attribution_confidence` (`confirmed` / `high` / `medium` /
`low` / `unknown`), a `caption_source`, and a one-line `basis`.

`scripts/catalog_pipeline.py` re-applies this file on every run (see
`apply_editorial_captions`), so captions and credits survive regeneration.
Regenerate the layer with `python scripts/author_captions.py`, then either rerun
the full pipeline or run `python scripts/apply_captions.py` to overlay it on the
current catalog (and refresh `data/catalog.csv`) without a full image rescan. All
263 records are captioned; 104 carry a named holder/creator and the remainder are
explicitly `Unknown`. The Calisphere items are credited to the Beaumont Library
District Local History Collection (Calisphere collection 1828), the confirmed
regional contributor. The client portal shows the caption and credit on every
card, exposes an editable **Attribution / credit** field in the detail view, and
includes both in the downloaded/copied selection report.

### Adding a found record (manual insertion)

Most records are *generated* by the pipeline scanning the source directories in
`config/catalog.config.json`; the editorial layers above only overlay onto
records that already exist. For a one-off **found item** that is not in a scanned
source dir — a Library of Congress Sanborn sheet, a Calisphere scan, a
newly-acquired print — use `scripts/add_manual_record.py`, which reproduces
everything the pipeline would compute for that image (a `files` entry with
perceptual hashes, a 560px thumbnail and 1600px preview under `site/assets/`, and
the print-viability math) and bakes a fully-authored record into **both**
`data/catalog.json` and `site/data/catalog.json`, re-sorts chronologically,
updates the summary counts, and rewrites `data/catalog.csv`.

Write a small metadata JSON (keep it under `data/manual-records/` so the record
can be re-applied), then run:

```
python scripts/add_manual_record.py data/manual-records/<name>.json
```

Only `image` and `title` are required; every other field is optional. `date`
(`start` / `end` / `display` / `confidence` / `basis`), `caption`,
`description`, `attribution`, `caption_source`, `evidence` (a list of
`{label, url}`), `holding`, `open_questions`, `subjects`, and `provenance` fill
out the card and its citations. **`rights_status` must be exactly one of
`Public domain`, `Permission required`, `Copyrighted`, or `Unclear`** or the
site's colour-coded rights pill will not render. Re-running with the same image
replaces the record in place (idempotent), so the JSON is the source of truth.

Caveat: manual records are not re-scanned by a full `catalog_pipeline.py`
rebuild, so a rebuild will drop them — re-apply by re-running the script.

Worked example: [`data/manual-records/beaumont-hotel-1895.json`](data/manual-records/beaumont-hotel-1895.json)
adds the February 1895 Sanborn fire-insurance sheet of Beaumont (showing "The
Beaumont Hotel"), pulled from the public-domain LOC Sanborn collection. LOC's
own pages sit behind a bot-check, but the tile server is open — a full sheet is
`https://tile.loc.gov/image-services/iiif/service:gmd:gmd436m:g4364m:g4364bm:g4364bm_g00411<YEAR>:00411_<YEAR>-000<SHEET>/full/pct:100/0/default.jpg`.

## Deployment

**Live site: https://rise-o-matic.github.io/san-gorgonio-historical-photo-catalog/**

The site is published to GitHub Pages by [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml), which uploads the `site/` subfolder as the Pages artifact on every push to `main` (`upload-pages-artifact` + `deploy-pages`). Because GitHub Pages does not publish an arbitrary subfolder except `docs/`, this Actions workflow is what lets `site/` be served without moving or duplicating it. Pages is configured with Actions as the build source (`build_type: workflow`). To update the live site, commit and push to `main`:

```powershell
git add -A; git commit -m "…"; git push
```

All asset and data references in the catalog are relative, so the site serves correctly from the repo-name subpath (`/san-gorgonio-historical-photo-catalog/`) with no base-URL configuration.

The `site/` directory is self-contained, so the same content can alternatively be published with Cloudflare Pages or Netlify: connect the repository, use no build command, and set the publish directory to `site`.

No source originals are deployed. This generated site is about 94 MB and contains only optimized previews/thumbnails plus metadata. Confirm rights before public deployment; every record defaults to `Unclear` and age alone is never treated as permission.

## Research notes

The first authoritative-source pass is seeded in `candidate-reviews.json`. It found the Beaumont Library District local-history page, a related Southern Pacific depot postcard held by Tyrrell Historical Library/UNT with IIIF support, and the Beaumont Woman's Club history page. Search results frequently confuse Beaumont, California with Beaumont, Texas; candidates therefore require place and composition validation before acceptance.

A second, Pass-wide pass (2026-07-10) added 16 externally sourced candidates for subjects **not** in the current, Beaumont-town-centric set: the town of Banning, Cabazon, the Colorado River Aqueduct, the Gilman Ranch stage station, and Native leaders/artisans of the Pass (Captain John Morongo, Fig Tree John, a Cahuilla basket maker). The richest open source is the **Banning Library District Local History Collection on Calisphere** (381 items covering Banning, Beaumont, Cabazon, and Cherry Valley from the 1880s on); single items also came from the Pomona Public Library Frasher Foto Collection and the USC / California Historical Society collection. Rights are tiered per item — one is Public Domain/CC BY (the USC summit-trail photo, the natural first real acquisition), one is permission-required (Frasher), and the fourteen Banning items carry the collection's uniform "copyright status unknown" statement, so none is promoted to a master until reuse is cleared. Full write-up and next steps: [`data/research-assets/san-gorgonio-pass-new-candidates.md`](data/research-assets/san-gorgonio-pass-new-candidates.md). Re-apply with `python scripts/add_pass_candidates.py`.
