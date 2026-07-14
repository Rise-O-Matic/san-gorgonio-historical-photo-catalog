# Re-acquisition search plan — Kelly's unprintable mural picks

**Goal:** find a production-grade source (≥ ~3600 px on the long edge, i.e. ≥ 24″
at 150 PPI) for the 9 photographs Kelly loves that the catalog holds only as
low-resolution web/design scans, and for which **no printable stand-in exists in
the collection**. These 9 are the founding-era and Native-heritage heart of the
mural, so substitution is not an option — a better source is the only path.

**The core problem.** 7 of the 9 exist only as Kelly's design comps in
`…\timeline-mural\Design Files\Mural Images\` (typically 500–1024 px). Those are
working files, not scans of originals. Kelly reports that **many original prints
and photos sit in a hard-to-access Library storage area, unindexed** — nobody
currently knows which originals are there. So this plan has to bridge a digital
catalog to a physical shelf: it must let someone standing in that storage room
*recognize* the specific original when they see it.

---

## The 9 priority targets

Each row carries everything we know that helps identify the physical original or
find it online. "Comp only" = we hold just Kelly's low-res design file.

| # | Subject | Date (working) | Best known source | Long-edge px now |
|---|---------|----------------|-------------------|------------------|
| 1 | **Ceremonial Big House, Morongo** | c. 1800 (nominal) | Comp only — Native, likely Malki Museum / ethnographic | ~250–500 |
| 2 | **Pauline Weaver** (pioneer, d.1867) | c. 1850s–60s | Comp only — a known figure; portrait likely published | ~500 |
| 3 | **Stagecoach, downtown Beaumont** | c. 1860 | Comp only — likely Calisphere BLD or SGPHS | ~500 |
| 4 | **Beaumont Train Depot** | 1875 | **Calisphere, BLD Local History Coll.** (has a CBAN id) | ~1024 |
| 5 | **Post Office, Fifth & Egan** | 1879 / 1890s | **Beaumont Library District** (institutional) | ~500 |
| 6 | **Traditional house, Morongo Reservation** | c. 1900 | Comp only — Native, Malki / NAA | ~500 |
| 7 | **Morongo Band of Mission Indians** | 1908 | Comp only — Native, Malki / NAA / USC | ~500 |
| 8 | **"Expansion / Mansard Roof" building** | 1965 | Comp only — likely BLD or *Record Gazette* | ~500 |
| 9 | **Beaumont Developments** | 1988 | Comp only — likely BLD or *Record Gazette* | ~500 |

Full per-record provenance (filenames, captions, attributions) is in
`data/catalog.json` under `curated: true`; the caption layer is
`data/editorial-captions.json`.

---

## Track A — Online institutional search (do first; cheapest)

Desk research using the project's proven Calisphere method (Chrome MCP:
`navigate` → wait 1–2 s → `get_page_text`; **not** curl/WebFetch — Calisphere is a
bot-protected SPA). Space requests out to avoid per-item 403s.

**A1. Calisphere — Beaumont Library District Local History Collection (coll. 1828)
and Banning Library District (coll. 1582).**
- Target #4 Depot is already known to live here — pull its full-resolution master
  and the CBAN/ARK identifier (the item page exposes both).
- Search each remaining subject in-collection:
  `https://calisphere.org/collections/1828/?q=<term>` and `/1582/?q=<term>`.
  Terms: `depot`, `post office`, `stagecoach`, `morongo`, `mission indians`,
  `weaver`. Record each hit's ARK, pixel dimensions, rights statement, and caption.

**A2. Online Archive of California (OAC)** — finding aids for BLD, SGPHS, Riverside
County collections that may not be digitized on Calisphere. Good for #5, #8, #9.

**A3. Local newspaper morgue** — the *Record Gazette* (Beaumont) for #8 and #9
(1965 / 1988 development). Check the paper's own archive and the Riverside County
library microfilm holdings; a press print may exist.

**A4. USC Digital Library / California Historical Society** — already yielded one
clean acquisition this project (summit-trail photo). Worth a pass for #7.

**Rights note:** capture rights status per item. Age is never treated as
permission on this project; nothing is promoted to a printable master until reuse
is cleared. Track A items still need a rights decision even when found large.

## Track B — Native-heritage items (special handling for #1, #6, #7)

Native images route to different institutions **and** carry cultural-permission
obligations beyond copyright.

- **Malki Museum** (on the Morongo Reservation, Banning) — the primary regional
  holder of Cahuilla/Serrano/Morongo photographs. Contact directly; this is a
  relationship, not a database query.
- **Smithsonian NAA** (National Anthropological Archives) and **USC** ethnographic
  collections — for c.1900–1908 reservation photographs.
- **Consult the Morongo Band of Mission Indians** on use of #1/#6/#7 regardless of
  who holds the physical print. Cultural sensitivity and tribal consent should gate
  inclusion, not just legal rights. Flag these for Kelly to raise with the Tribe
  before they go on a public wall.

## Track C — Physical Library storage (the big unknown; highest potential payoff)

Kelly says the originals are there but unindexed. Make that tractable instead of a
needle-in-haystack by turning our digital knowledge into a **field pull-list** and
a capture protocol.

**C1. Produce a printed pull-list.** One page per target from the table above, each
showing: the low-res image itself (so it can be matched by eye), the working
caption, the date, any name/place keywords, and a checkbox. Sorted by the two
things a person in a storage room can actually navigate by: **date** and **subject
keyword**. This is the artifact that converts "no idea which ones" into "look for a
1908 group portrait of the Morongo Band" — generate it from
`data/mural-shortlist.json` + the 9 targets (script below).

**C2. Scope the storage in one triage pass.** Before hunting individuals, spend one
session characterizing what's there: rough count, how it's organized (by donor? by
box? loose?), formats (prints, negatives, glass plates, albums), and condition.
This tells us whether a full digitization project is warranted or a targeted grab.

**C3. Targeted retrieval.** Walk the pull-list against whatever finding order the
storage has. Prioritize the 9; opportunistically flag any original that matches one
of Kelly's other 8 picks or a high-value low-res catalog record while there.

**C4. Capture protocol** (turns a found original into a production-grade master):
- Flatbed scan at **≥ 600 PPI** for anything up to 8×10; larger prints on a copy
  stand with even light. A 4×5 print at 600 PPI = 2400×3000 px — comfortably past
  the 3600 px bar once printed at reasonable mural scale, and headroom for Gigapixel
  upscaling if needed.
- Save a **lossless TIFF master** plus a JPEG derivative; include a color/scale
  reference in one frame. Note any caption written on the print's back.
- **Do not modify originals**, and per project rules (`copy-before-modify`) never
  edit binaries in place on `X:\My Drive\` — new files only, versioned.

## Intake back into the catalog

Anything found (Track A/B/C) enters as a **research candidate**, not a master:
1. Add to `config/catalog.config.json → research_candidates` with source URL/box
   location, dimensions, institution caption, match class, rights, retrieval date
   (mirror `scripts/add_pass_candidates.py`).
2. On rights clearance, promote to master and let it supersede Kelly's low-res comp
   for the same subject; record the researched date/caption in the editorial layers
   (`editorial-overrides.json`, `editorial-captions.json`) so it survives a rebuild.
3. Re-run the taste-match scorer — a re-acquired original should now clear the
   print bar and rank into the printable core.

---

## Prioritized next actions

1. **Track A quick win:** pull the full-res Depot (#4) master + ARK from Calisphere
   coll. 1828 — the one target we know is online. Confirms the pipeline end-to-end.
2. **Run the remaining 5 non-Native subjects** (#2,#3,#5,#8,#9) through Calisphere
   1828/1582 + OAC + Record Gazette.
3. **Generate the printed pull-list** for the storage visit (script below).
4. **Kelly:** schedule storage access + open the Malki Museum / Morongo Tribe
   conversation for the three Native images.
5. **Triage the storage** (C2) on the first visit; decide targeted-grab vs. full
   digitization.

*Nothing here is authoritative until a human confirms the match and rights. This is
a search plan, consistent with the project's posture that a candidate stays
separate from a master until reuse is cleared.*
