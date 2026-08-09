# Beaumont Library / photo catalog — backlog

Claude's open work for this project. Migrated out of Todoist on 2026-08-08 (Todoist now carries only work that needs Steven, or that has a due date).

Conventions: one block per item, highest priority first. Deep detail belongs in the design doc an item points to, not inline. **Prune when you touch this file** — an item whose premise no longer matches the code gets deleted, not left to rot.


## P2

- [ ] **Audit low-provenance photo records for appearance-vs-label mismatches**
      Client directive (2026-07-23): scrutinize catalog images whose caption/title rests only on a filename or "Provenance review" (no institutional source), assume some are mislabeled, and re-evaluate on appearance.

      **Repo:** C:\GitHub\san-gorgonio-historical-photo-catalog

      **Template already done — the Estrada cluster (4 records):** "Luis Estrada statue" records turned out to be the CSRM life-size exhibit FIGURE of Estrada, created 2005 (finding aid MS 871, [Luis M. Estrada membership cards and pins, 1923, 1962 - OAC](https://oac.cdlib.org/findaid/ark:/13030/c8ns123w/\).) The flagged close-up (img_99913db9881316f3) is the figure's face, not a living man. See memory: estrada-csrm-figure-cluster.md.

      **METHOD LESSON (important):** appearance alone misleads. My first read of the close-up was "unmistakably a living man" — wrong; it was a hyperrealistic museum figure. Re-evaluate on appearance to CATCH a suspected mismatch, then VERIFY against a source (Calisphere, institutional finding aid, web) BEFORE rewriting.

      **Triage — candidate records:** caption_source contains "Provenance review" and/or attribution_confidence in (unknown, probable) with no holding institution and no evidence URL. ~245 non-select records remain (see memory: collection-research-campaign.md). View each preview at site/assets/previews/file_<master_file_id>.jpg and compare to its title/caption.

      **Where to fix (source of truth, then regenerate):**
      1. Edit data/research-authored/*.json (title/caption/date/description/evidence). Also author_date_overrides.py O-dict and author_captions.py MANUAL_OVERRIDES where relevant.
      2. Regenerate: python scripts/author_date_overrides.py  →  python scripts/author_research.py  →  python scripts/apply_research.py (updates both catalog.json copies + csv).

      **Deliverable:** a shortlist of suspected mismatches for client review BEFORE any mass edits. Can run inline or as a multi-agent sweep to cover all 268 thoroughly.

      **NOTE:** the Estrada fix is complete on disk but was left UNCOMMITTED as of 2026-07-23 (regenerated data files in working tree) — commit or review before starting fresh work.

- [ ] **Pull full-res Beaumont Train Depot (1875) master + ARK from Calisphere coll. 1828**
      Quick win — the one re-acquisition target already known to be online. Confirms the Calisphere→candidate→master pipeline end-to-end. Use Chrome MCP (navigate + get_page_text), not curl. See data/research-assets/mural-reacquisition-plan.md Track A1.


## P3

- [ ] **Apply selects research corrections to catalog.json (author_captions MANUAL_OVERRIDES + date overrides)**
      New findings to fold into the san-gorgonio catalog: 09 = Capt. John Morongo c.1890 (d. July 1898 — LA Herald 7/21/1898); 11 clubhouse dedicated 5/11/1917 (kill 1911); 12 = CBEA_108 Funk Building/Beaumont Bank 1911, library ground floor not basement; 05 = CBEA_146 San Gorgonio Mercantile; 08 = CBAN_093 c.1900; 13 = H. L. Priest; 01 = Huntington Weinland Council house c.1890s; 16 mansard photo c.1978-2008. Full evidence: 2026-07-17_selects/selects-manifest.md

- [ ] **Fix non-idempotent caption_basis facts in apply scripts**
      scripts/catalog_pipeline.py apply_editorial_captions() does record.setdefault("facts",[]).append({field:"caption_basis",...}) on every run without deduping. apply_captions.py and apply_research.py therefore append a duplicate caption_basis fact to every record each time they run.

      The committed catalog already carries ~11 duplicate caption_basis facts per record from prior runs (data/catalog.json + site/data/catalog.json). Not user-facing (the site quickview/export don't render record.facts), but it bloats the catalogs and makes apply-script diffs touch all 263 records.

      Fix: clear existing caption_basis facts before appending (or dedupe), then run a one-time cleanup pass to collapse the accumulated duplicates. Discovered 2026-07-23 while swapping the mansard-roof reconstruction image (had to revert an apply_research.py run and patch the single record surgically to keep the commit clean).

- [ ] **Pull 4 remaining non-Calisphere masters (Huntington IIIF, Portal to Texas History, 2× CDNC via browser)**
      Calisphere /clip masters are done (data/calisphere/masters/, 28 previews upgraded). Remaining best_master URLs: Huntington IIIF (Capt. John Morongo record is permission-gated — check before use), Portal to Texas History 1500px card, and 2 CDNC newspaper pages that are bot-blocked (needs a real browser session). Then rerun scripts/upgrade_previews_from_masters.py. See data/research-authored/CAMPAIGN-STATE.md.

- [ ] **Regenerate mural-mockup page from refreshed catalog**
      data/mural-mockup.json is stale: still shows the council house as 253×199 px with the old "Ceremonial Big House Morongo, 1800" caption. Catalog dims were synced 2026-07-22 (scripts/sync_catalog_dims.py, 26 records). Rerun scripts/build_mural_mockup.py and sanity-check its other inputs before publishing.

- [ ] **Search Calisphere 1828/1582 + OAC + Record Gazette for 5 non-Native mural targets**
      Targets: Pauline Weaver (1850s), stagecoach downtown (1860), Post Office 5th & Egan (1879/1890s), Expansion/Mansard building (1965), Beaumont Developments (1988). Record ARK, pixel dims, rights, caption per hit. See mural-reacquisition-plan.md Track A.

