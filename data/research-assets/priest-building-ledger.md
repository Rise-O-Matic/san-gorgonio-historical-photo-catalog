# Facts ledger — the hilltop building behind H. L. Priest

**Record:** `img_a3f413e8c9ed23bb` · Calisphere CBEA_064 · BLD accession 89-01-74 ·
title "A man and fruit tree" · BLD caption "H. L. Priest is shown standing next to his
fruit tree in the early days."
**Question:** identify the long, low, single-storey institutional building on the knoll behind him.
**Status:** UNIDENTIFIED.

Working master: `data/masters/img_a3f413e8c9ed23bb.jpg`, 749×1024 (Calisphere `/clip` derivative).
Best enlargements for eyeballing: `data/research-assets/priest-building-crops/`.

### The 749×1024 ceiling is PROVEN, not assumed (tested 2026-07-24 b)
- `calisphere.org/clip/{1024,2000,4000,8000}²/1828/76d5d94e…` all return **the identical 229,949-byte
  file** — the derivative is hard-capped.
- No IIIF route exists: `/iiif/2/{hash}/info.json`, `/iiif/{hash}/…`, `/{hash}/…`,
  `iiif.ucldc.cdlib.org` all 404. (`/iiif/*` does reach a Cantaloupe server but the identifier space
  is not the clip hash.)
- **The client's own files are worse:** both `file_348736affdb526d1` and `file_229b9a6950a74027` are
  the same 366×500 JPEG (sha 6fb77572…), `X:\…\Mural Images\1927 man and fruit tree.jpeg`.
- **Internet Archive / California Revealed:** `archive.org/details/beaumontlibrarydistrict` exists as
  a *California Revealed collection shell* but contains **zero items**; californiarevealed.org
  returns no Beaumont results. No master deposited anywhere public.

⇒ **A fresh high-resolution scan of the original print at BLD (accession 89-01-74) is the only way
to get more pixels, and is the single highest-value action available.** The building is ~200 px wide
in every copy that exists online.

---

## 1. Measured constraints (do not re-derive)

| # | Constraint | How obtained | Session |
|---|---|---|---|
| C1 | Sun is to image-**left**; cast shadows run image-**right** and slightly toward camera | shadow + modelling on the plate | 2026-07-24 a, re-derived independently 2026-07-24 b |
| C2 | Shadow length ≈ 0.29 × subject height ⇒ solar elevation ≈ 70–75° ⇒ within ~1.5 h of solar noon, May–July ⇒ sun azimuth near S | photogrammetry | 2026-07-24 b |
| C3 | **Camera bearing ≈ W (WSW–WNW).** C1+C2 combined; also the one bearing in the Pass with neither San Gorgonio (NE) nor San Jacinto (SE) in a normal-lens frame. ⇒ **the building lies W-to-SW of the camera** | — | both |
| C4 | Skyline is a *near* bare rounded knoll at ~camera eye level, not a far horizon. Sky luminance holds flat 209–214 then drops within ~12 rows ⇒ empty horizon is genuine, not an orthochromatic wash-out | sky-luminance profile | 2026-07-24 a |
| C5 | Camera ≈ 10 ft from Priest (he subtends 615 px for ~71 in) | assumes ~normal lens, ~40° h-FOV | 2026-07-24 b |
| C6 | **Building ≈ 800 ft (~250 m) from camera; ≈ 160–200 ft long; wall ~15 ft** (1 storey + parapet) | same scale chain as C5 | 2026-07-24 b |
| C7 | Terrain: camera sits in a **swale between two bare knolls**; the building's knoll rises only a few degrees above camera level; slope below it is freshly graded/benched | plate | 2026-07-24 b |
| C8 | Foreground is freshly graded, disced ground. No other trees, fences, houses, or planted rows in frame | plate | both |

**C6 matters:** this is a substantial 6–10-room institution, *not* a one-room rural schoolhouse.

### Building form, read at 9× with local-contrast normalisation
Stepped rooflines, flat parapets with a thin cornice band throughout, light stucco/concrete.
- **Left:** wing projecting toward camera, deep flat overhanging eave, one large dark opening.
- **Centre:** raised pavilion fronted by a **colonnade / pergola of ~7–8 slender posts** carrying a
  horizontal beam, with vines or shrubs grown through it.
- **Right:** long wing with a **continuous ribbon of ~8 multi-pane sash**, a door at its left end,
  and a bright continuous base band (concrete base wall or walk).
- Low picket-like line (fence, balustrade or shrub row) along the front.

Type: 1910s–20s institutional. School or small sanatorium/hospital most likely; the pergola argues
for a building meant to be pleasant, so not industrial.

### Is it International Style? (raised by Steven, 2026-07-24)
**Reads that way, but almost certainly isn't — and the distinction matters because it sets the date.**

*For:* flat parapet roof, long horizontal ribbon glazing, plain unornamented light planar walls,
asymmetric stepped massing, an apparently cantilevered flat canopy on the left wing.

*Against:* the **vine-grown pergola/colonnade** is a Craftsman/Mission garden device the
International Style explicitly rejected; the sash are **small-pane grids** (industrial steel or
muntined wood), not the large undivided lights IS favoured; there is a **banded cornice line**
below the parapet. And chronology — IS is a post-1932 label in America, by which date Priest was 70+.

*Working conclusion:* it is **proto-modern, not modernist** — the "open-air institutional" type of
c. 1915–1925, which arrived at a modern-looking envelope for functional reasons (classrooms and
wards needed continuous daylight and cross-ventilation; the **April 1918 San Jacinto earthquake**
pushed the Pass toward single-storey light construction — the same quake condemned Beaumont's
original Wellwood School). Prairie/Mission-modern school architects produced exactly this look.

### ⚠️ Alternative reading raised by the 1938 negative — it may not be institutional at all
The aerial sweep (§4c) found no institution near Beaumont. That makes it worth taking seriously that
the "institution" reading is an artefact of 200 px. A **poultry laying house** has the same
signature at this resolution: very long and low, a continuous row of large multi-pane window/screen
openings along the sunny side, a light-painted wall, a flat or shallow shed roof — and Beaumont had
commercial poultry ranches from about 1909. On that reading the "raised central pavilion with
pergola" would be a feed/water-tank house with a shade arbour, and the "banded cornice" a plate line.
This would explain the total documentary silence, since no record names an ordinary ranch building.
**Not resolvable at 749×1024 — this is the strongest single argument for the rescan.**

*Live alternative worth one check:* if the building really is 1930s, the best fit becomes a
**Field Act school (1934–40)** — one storey, flat roof, plain stucco, ribbon steel sash, covered
walkways on slender posts, brand-new graded site. Argued against by Priest's apparent age, the
**bowler hat** and rolled shirtsleeves (1900s–20s dress), the rounded-corner postcard mask, and
BLD's "in the early days".

---

## 2. The man — SETTLED

**Herbert Loren "Pete" Priest, 11 Jan 1862 – 31 Aug 1946.** Previously a single unverified
genealogy site; now confirmed from primary sources:

- **San Bernardino Sun, 3 Sept 1946, p.10** — "Funeral Services This Morning for Herbert L.
  Priest": *Herbert Loren Priest, 84, for 35 years a newspaper writer and civic leader in
  Beaumont*; services Allen chapel, Dr. David McMartin; burial Mountain View cemetery; **born in
  Michigan**, taught in Michigan and Minnesota, **YMCA secretary in France in WWI**, **several
  years clerk in the Beaumont post office**. `cdnc.ucr.edu/?a=d&d=SBS19460903.1.10`
- **Daily Gazette (Beaumont), 15 Nov 1928** — "J. V. R. Priest, father of H. L. Priest, assistant
  postmaster, is celebrating his ninety-first birthday" — confirms the Joshua Van Renssalaer
  Priest link and Priest's day job.

**He is "Prof. H. L. Priest"** — a career schoolteacher — in every 1917–21 notice.

**Movements (CDNC, `"H. L. Priest"` 1908–1927, 51 hits):**
- Aug 1916, Jan 1917 (RDP): "**H. L. Priest of Minneapolis, Minn.**, who has been visiting…" — he was
  still a Minnesotan; his **parents J. V. R. Priest & wife were already Beaumont residents**.
- Jun 1917: "J. V. R. Priest and son, Prof. H. L. Priest, autoed to **Calexico**."
- Jan 1918: organising the **local Y.M.C.A.** in Beaumont; sailed for **France** (Y.M.C.A.) May 1918;
  home Jun 1919; lectured on France through 1919.
- Jan 1920: "Will Teach in **Mexico**." Feb 1921: "Teacher Arrives — H. L. Priest arrived home Friday
  from **Cloudcroft, N. M.**"
- From 1922 on he is a fixture of Beaumont civic life; **assistant postmaster** by Nov 1928.

**⇒ DATE FLOOR: the photo is c. 1917 or later** (he did not live in Beaumont before then). The
obituary's "35 years" is loose. Age 55–65 in the photo ⇒ **c. 1917–1927**, consistent with the
collection filename "1927".

He was a **town man — teacher, newspaperman, postal clerk, never a farmer** — so the tree is a
dooryard/garden or small-acreage tree, not commercial orchard work. (Corroborated: Gazette 1945 ad,
"Gorgeous Tulips from the garden of H. L. Priest"; 1938, book donations to the Beaumont library.)

---

## 2b. Costume + apparent age — dates the plate to **c. 1917–1922**

Read off the master at 5–9× (crops in scratchpad: `hat_head`, `collar_vest`, `torso`, `legs`).

| Feature observed | Period signal |
|---|---|
| **Bowler/derby** with a tall domed crown and a narrow, sharply up-curled brim | 1900–1915 shape; bowlers largely gone from US casual wear by the mid-1920s |
| **Tall stiff white detachable turndown collar** | 1900–1918; collar heights collapsed and soft collars took over after WWI |
| Narrow **four-in-hand** with a small knot, apparent stickpin | 1900–1925 |
| **Striped shirt**, sleeves rolled thick below the elbow, no jacket | 1900–1925 |
| Single-breasted **lapelled waistcoat** worn as outerwear, 5 buttons, welt pockets, light object (pencil/cigar) in the left breast welt | 1900–1920s |
| **Narrow, plain-bottom (uncuffed) trousers**, c. 16–17 in at the hem | pre-1920 predominant; 1920s trousers are wider and turn-ups became near-universal |
| Full drooping grey **walrus moustache** | man born mid-19thC; unfashionable by the 1920s but persistent in older men |
| **Round light lapel button** pinned to the waistcoat | unresolvable at 1024 px — but a war-service / Y.M.C.A. / Liberty Loan button would point hard at 1917–19 |

**Face:** lean, hollow-cheeked, deep nasolabial folds, slack jaw, heavy brow — reads **late 50s to
mid 60s**, not 70+.

**Costume centroid c. 1908–1918**, with a tail into the early 1920s for a conservative older man.
Intersected with the hard constraint that Priest did not live in Beaumont before c. 1917, and with
b. 1862 (so 55–60 in 1917–22):

> ### ⇒ REVISED DATE: **c. 1917–1922** (probably 1917–20), replacing c. 1915–1930.

**Consequences for the building hunt — it must have been standing by c. 1917–22:**
- kills **Beaumont High School 1928** outright (too late);
- kills the **Field Act school (1934–40)** alternative raised by the International-Style reading;
- puts the target squarely in the **1918 San Jacinto earthquake rebuild wave (1918–1922)**, which
  fits the single-storey, light, flat-roofed form and the freshly graded site;
- ⇒ search Beaumont-area construction news **1917–1922** (RDP, Enterprise/MPE and Record-Gazette/BRG
  all carry dense Beaumont columns in exactly those years).

## 2c. Where the Priests lived — first hard location (2026-07-24 b)

CDNC, `"J. V. R. Priest"`, 38 hits:
- **Daily Gazette (Beaumont), 1 June 1916:** "J. V. R. Priest **has broken ground on Walnut street**"
  — i.e. the family was building on a new lot in mid-1916, immediately before Herbert arrived from
  Minneapolis. A brand-new lot is exactly the raw, freshly graded ground in the photograph.
- **Daily Gazette, 12 July 1928:** "…her father and brother, J. V. R. Priest and **Bert Priest on
  Wellwood ave.**" Also Gazette 6 Dec 1928 ("seriously ill at his home on Wellwood") and San
  Bernardino Sun 3 Jul 1930 ("at his home on Wellwood").
- Herbert lived **with his father**; the household is "J. V. R. Priest and son" throughout.
- Family also had strong Calexico/Imperial Valley ties (daughter Mrs. C. H. Hevener), which explains
  Herbert's 1917–19 trips there. Imperial Valley is flat and below sea level ⇒ **not** the photo site.

**Wellwood Avenue is on Beaumont's WEST edge** (OSM: c. 33.9307/-116.9835 and 33.9277/-116.9858, vs
Beaumont Ave at c. -116.977) — i.e. ~600–800 m west of the main street, right where the town grid
meets the falling ground toward the SP corridor. That is the same quadrant as the measured camera
bearing (C3).

⚠️ Caveat: the Wellwood Ave address is documented for 1928–30, ten-plus years after the photo; the
1916 "Walnut street" ground-breaking is the contemporaneous one. **Neither street has yet been tied
to a knoll.** Next step is a 1916–22 Beaumont plat/assessor map or a Great Register entry.

## 3. Ruled out

### Buildings compared image-to-image
| Candidate | Why rejected |
|---|---|
| Wellwood School 1910 | **image checked 2026-07-24 b** (Calisphere 1828/87ee54f9…): wood-frame, clapboard, hipped/gabled shingle roofs, shingled bell cupola, mature trees. Nothing like it |
| Wellwood School 1921 | **primary source, Enterprise (Riverside) 14 Jul 1921 `MPE19210714.2.33`: $49,000 bond, Witmer & Watson of Los Angeles, "Spanish court style", reinforced concrete, TILE ROOF, eight rooms, built on the site of the existing school which was razed.** Wrong roof, wrong site, in town. (2026-07-23 ID withdrawn 07-24; now closed with documentation) |
| "Beaumont Hospital" | Mrs. E. A. Zook's small private hospital, **201 Fifth Street, in town**, 1930s (Gazette ads 1933–39). Not an isolated 200-ft building |
| Beaumont Grammar School 1911 | wood bell cupola |
| Beaumont High School 1912, 600 Magnolia | shingled Craftsman, pagoda cupola, 2 storeys |
| Beaumont High School 1928, 500 E. 6th | tiled gable pediment + oculus + auditorium fly tower; flat in-town lot |
| Beaumont Woman's Club 1917, 6th & Euclid | hipped shingle roof; in town |
| Cherry Valley School c.1908 | gabled wood + belfry (Beaumont Heights & Farms brochure) |
| Highland Springs Resort pool house | cobblestone, tile roof, arched openings |
| Highland Home / Highland Springs Hotel | 3-storey Victorian |
| Banning High School 1918 | 2-storey brick |
| Banning High School (Moderne, 1930s–40s) | wrong date and style |
| **St. Boniface Indian Industrial School, Banning** | **eliminated in an earlier session — do not re-open** |

### Sources exhausted with no match
- **Whole project catalog (269 records)** contact-sheeted 2026-07-24 — the building appears in no
  other photo we hold.
- **Calisphere, Beaumont Library District collection (id 1828), all 187 item titles reviewed** — no match.
- Calisphere Banning Library District collection (id 1582) — schools subset (65 items) reviewed, no match.
- **Sanborn**: LOC has Beaumont 1895/1900/1907/1915/1926/1932; the 1915 sheets map only the dense
  core (pop. 1200). A building alone on graded outskirts is **off-map** — wrong tool.
- **Historic Aerials**: 1961+ only, watermarked.
- **Google Lens on the full frame**: useless — matches the "man posing with an orange tree" genre,
  not the building. Would need a crop hosted at a public URL to be worth repeating.

### Closed by newspaper search (2026-07-24 b)
- **Beaumont Union High School has no intermediate building.** `"union high school" building` +
  Beaumont, 1917–1928, 373 hits: nothing between the 1912 Magnolia building and the 1928 E. 6th
  building. The hypothesis that a new BUHS went up in the 1918-earthquake window is dead.
- **Cherry Valley School** is a single small "school house" used as the district's community hall
  right through the 1920s–30s (691 hits, all social/meeting notices). Not a 200-ft institution.
- `Beaumont "new school building"` 1915–1930 (49 hits) surfaces only the 1921 Wellwood job.
- `Beaumont "will be erected"` 1916–1923 (85 hits) — no large institution near Beaumont.
- `Beaumont pergola` 1908–1935 (156 hits) — nothing architectural.
- `"school on the hill"` in BMTG — no results.
- `"orange tree" Priest` 1915–1940 — nothing; the tree was never a news item.

### Sanatorium leads chased and downgraded
- **"Southland Sanitarium"**, Daily Gazette 12 Nov 1908 (`BMTG19081112.2.35`): P. M. Maher bought
  land "in the foothills **north** of town", "sheltered valley"; 75–100 rooms, $50,000, "patent
  ventilated cottages" during construction. **The name never appears again anywhere in CDNC** ⇒
  almost certainly never built. Also wrong bearing.
- **Riverside Daily Press 25 Nov 1914** (`RDP19141125.2.26`): Gilbert Tompkins bought the Jackson
  **5-acre** orchard tract at Cherry & Dutton, Cherry Valley, for a sanitarium — he had asthma
  himself. 5 acres ⇒ too small for C6.
- **"Beaumont Open Air Sanitarium"**, Mr & Mrs M. M. Steele, Cherry Valley — 24 CDNC hits, **all in
  1928**. Tent/cottage scale ("exchange Wedgewood range for tent"). Not a 200-ft masonry building.

---

## 4. Tooling that works (save re-discovery)

**CDNC (`cdnc.ucr.edu`)** — Cloudflare-gated to curl *and* WebFetch (403), but **passes
automatically in Chrome**; just wait ~4 s after navigating.
- Search: `?a=q&hs=1&r=1&results=1&txq=<terms>&txf=txIN&ssnip=txt&puq=<CODE>&dafyq=<y1>&datyq=<y2>&so=byDA&e=-------en--50--1--txt-txIN--------`
- Article: `?a=d&d=<CODE><YYYYMMDD>.<sec>.<art>`
- Publication codes: **BMTG** Daily Gazette (Beaumont) · **RDP** Riverside Daily Press ·
  **MPE** Enterprise (Riverside) · **SBS** San Bernardino Sun · **BRG** Record-Gazette (Banning,
  ≥1916–1923, a local Pass weekly — *still barely mined*).
- The **Riverside Daily Press and the Enterprise both ran dense daily/weekly "In Neighboring Towns —
  BEAUMONT" columns** through 1914–1925. This is the richest untapped seam for 1917–22 construction.
- BMTG's digitised run is patchy: 1908–09, 1915–16, 1920, then dense 1928+.
- `get_page_text` returns only the header on article pages. To read OCR: `find` the term →
  `computer scroll_to` that ref → screenshot the left text pane. `javascript_tool` is blocked on
  CDNC (query-string/cookie guard).

**Calisphere** — item pages load fine in Chrome; `curl` works on
`https://calisphere.org/clip/{W}x{H}/{collectionId}/{hash}` (collection 1828 caps ~1024 px;
1582 goes to 3000 px). Get hashes from search-result thumbnail `src`s via `javascript_tool`
(**output truncates ~1000 chars — request in slices**). Collection list view + `get_page_text`
gives all titles 100 at a time (`?view_format=list&rows=100&start=N`).

**USGS historic topos** — TNM API `datasets=Historical Topographic Maps` + bbox. Best available
for this area: San Gorgonio 1:125,000 **1902** (too early) and Beaumont / El Casco 1:24,000
**1953** (probably too late). GeoPDFs have no text layer; render with PyMuPDF.

---

## 4b. Applied to the catalog (2026-07-24 b)

Edited `data/research-authored/2026-07-20-mural-selects.json` → `scripts/author_research.py` →
`scripts/apply_research.py`. Record `img_a3f413e8c9ed23bb` now carries:
**date c. 1917–1922 (medium)** (was c. 1915–1930), the primary-source identification of Priest, the
photometry/photogrammetry corrections, and evidence links to the Sun obituary, the Gazette notice,
the Minneapolis residence notices and the 1921 Wellwood article. Caption rewritten.

## 4c. 1938 aerial sweep — an important negative (2026-07-24 b)

UCSB **FrameFinder** (`mil.library.ucsb.edu/ap_indexes/FrameFinder/`) works with no login. Its
"Near Me" tool, searched on *Walnut St, Beaumont, CA*, returns pre-war coverage:

| Flight | Frame | Date | Scale | Distance from Walnut St | Free scan |
|---|---|---|---|---|---|
| **AXM_1938A** | 61-70 | 24 May 1938 (print stamped 7-4-38) | 1:20,000 | 0.65 mi | `https://mil.library.ucsb.edu/ap_images/axm-1938a/axm-1938a_61-70.tif` (23.6 MB) |
| **AXM_1938A** | 61-71 | 24 May 1938 | 1:20,000 | 0.70 mi | `…/axm-1938a_61-71.tif` (23.9 MB) |
| **C_1940D** | D-18 | 1940 | — | 0.38 mi | `…/c-1940d/c-1940d_d-18.tif` (**242 MB**) |
| **C_1940D** | D-17 | 1940 | — | 0.71 mi | `…/c-1940d/c-1940d_d-17.tif` (**242 MB**) |

Both 1938 frames pulled (5483×4309 and 5505×4332). Ground scale ≈ 0.37 px/ft, so a 200-ft building
is ≈ 73 px — easily visible. Frame 61-70 covers ≈ 2.8 mi square centred just west of Beaumont.

**Swept the whole of 61-70 in four quadrants. Result: there is NO large, isolated, institutional
building on a knoll anywhere around Beaumont in 1938.** The NW quadrant is chaparral canyons; the
SW quadrant (the badlands, the direction the camera faces) is empty grazing land with no structures
at all; the substantial buildings are all inside the town grid, and the only big light-roofed
complex is the 1928 high school.

### The sweep was then widened — all of it negative

**Query the index directly, no browser needed.** FrameFinder is an ArcGIS Web AppBuilder app;
`…/FrameFinder/config.json` → `map.itemId = 0fe449f9e40b48e591e3f99bc42d7f35` →
`https://ucsb.maps.arcgis.com/sharing/rest/content/items/<itemId>/data?f=json` → the layer:

```
https://services1.arcgis.com/4TXrdeWh0RyCqPgB/arcgis/rest/services/All_Flights_Merge/FeatureServer/0/query
  ?geometry=<xmin,ymin,xmax,ymax>&geometryType=esriGeometryEnvelope&inSR=4326
  &where=BeginDate < DATE '1946-01-01'&outFields=FlightID,Frame,Scale,BeginDate,Scan&f=json
```
Fields: `FlightID, Frame, Scale, BeginDate, Scan` (Scan holds the download `<a href>`).
48 pre-1946 frames cover the Pass — flights **AXM_1938A**, **AXL_1938**, **C_4058** (1936),
**C_5750** (1939), **C_1940D**.

**Frames examined (all AXM_1938A, 1:20,000, free scans):**

| Frame | Date | Ground covered | Result |
|---|---|---|---|
| 61-70 | 7-4-38 | Beaumont + ~1 mi all round | town only; no isolated institution |
| 61-71 | 7-4-38 | Beaumont NW + badlands | nothing |
| 61-68 | 7-4-38 3:49pm | SE Beaumont toward Banning, San Gorgonio wash | orchards/fields only |
| 61-72 | 7-4-38 | San Timoteo badlands | empty, dissected, a few ranch sites |
| 61-73 | 7-4-38 | San Timoteo badlands (further NW) | empty |
| 53-89 | 6-16-38 | **Cherry Valley, dead centre** | cherry/olive orchards, Noble Creek, ranch complexes only |
| 53-88 | 6-16-38 | Cherry Valley E | — |

**⇒ There is no 200-ft isolated institutional building anywhere on the ground around Beaumont,
Cherry Valley, the Banning approach, or the San Timoteo corridor in 1938.** This also kills the
earlier session's "San Timoteo / Badlands corridor toward Redlands" hypothesis outright.

*(The C_1940D frames were NOT pulled: at 242 MB each they are 5× the size quoted, and being dated
**after** 1938 they cannot test the "demolished before 1938" branch — they would add nothing.)*

## 4e. TWO CORRECTIONS THAT REFRAME THE WHOLE SEARCH (2026-07-24 b, late)

### (i) There is no "knoll". The terrain is a gentle fan — measured.
Every session so far, mine included, has described a "distinct knoll", a "swale between two bare
knolls", "dissected badlands". **That was never measured.** Reading the sky/land boundary off the
plate and converting to angles (portrait frame, long axis vertical, ≈50° vertical FOV over 1024 px;
horizon ≈ Priest's eye level, y≈250):

- left skyline ≈ 1° **below** eye level · building's ridge crest ≈ 1.5° **above** eye level
- **total skyline relief across the entire frame ≈ 2–3°**

At ~800 ft, 1.5° is **≈ 20 ft** of rise — a **~2.5 % slope**. That is an alluvial fan or a gently
sloping bench, **not knoll country**. This invalidates the "San Timoteo / Badlands corridor"
hypothesis at its root and explains why sweeping dissected terrain in the aerials found nothing —
wrong landform. A 2.5 % fan is, however, *classic citrus siting*.

### (ii) Steven's argument — and it defeats my own poultry hypothesis too
> "The facility should have shown up on the aerial photos regardless of what kind of facility it was."

Correct, and decisive. A 160–200 ft building is ~73 px at 1:20,000; it registers whether it is a
school, a sanatorium or a laying house. **So §4d's poultry-house reading does not actually solve the
problem** — it was constructed to explain *documentary* silence, but it cannot explain *aerial*
absence. Treat §4d as weakened, not as the answer.

Only two explanations survive:
- **(a) the building was demolished between c. 1922 and 1938**, or
- **(b) the photograph is not near Beaumont at all** — the BLD provenance shows where the print
  ended up, not where the shutter was pressed.

Correction (i) independently supports (b).

### Cleared up along the way
- **"Will Teach in Mexico"** (Enterprise, 10 Jan 1920, `MPE19200110.2.69`) is the paper's own
  headline error. The text reads: Priest "left Sunday for **Alamogordo, New Mexico**" — which is why
  he returns from **Cloudcroft, N.M.** in Feb 1921 (Cloudcroft is the resort above Alamogordo).
  He taught in New Mexico c. 1920–21. **No citrus at 4,300 ft**, so not the photo site.
- **"El Retiro on the Mesa"** — chased and closed. Daily Gazette 6 Apr 1916 (`BMTG19160406.2.7`):
  "El Retiro, on the Mesa, **the home of Mrs. A. G. Royce**". A private house, not an institution.
- **"the Mesa"** is a real Beaumont district name (orchards, residents, cherry trees, and the
  Beaumont Land & Water Co.'s "La Mesa Miravilla" tract). Recurs in headlines 1917–20.
- **Citrus research facility (Steven's hypothesis, 2026-07-24)** — a good fit for a 2.5 % fan, newly
  graded experimental plots and a young grafted citrus. UC's Citrus Experiment Station, Riverside is
  excluded: both the 1907 Mt. Rubidoux site and the 1917 Box Springs campus sit against a mountain
  front, which would fill the sky behind the building; our frame has bare sky. Other candidates are
  unexplored — see open leads.

## 4d. Best-supported reading — a hypothesis, now WEAKENED by §4e(ii)

Five independent silences now have to be explained at once. The building appears in **no photograph**
in either the Beaumont or Banning library collections (187 + 381 items reviewed); in **no
newspaper** (CDNC, exhaustively searched 1908–1940); on **no map** (Sanborn, 1902 and 1953 topos);
in **no 1938 aerial** of Beaumont, Cherry Valley, Banning-side or San Timoteo; and Beaumont's entire
institutional building stock of the period is accounted for and none of it matches.

A genuine 160–200 ft public institution in a town of ~1,500 could not be that invisible. The reading
that explains all five silences simultaneously is that **it is not an institution at all, but a
large agricultural building — most probably a commercial poultry laying house.**

The signature fits without strain: very long, single storey, light-painted, a continuous row of
regularly spaced multi-pane openings along one sunny side, low roof, no landscaping, sited alone on
a well-drained rise for air and sun, on raw graded ground. Beaumont had commercial poultry ranches
from about 1909. Such buildings were never named in the press, never photographed for the record,
and were gone by the 1930s — which is exactly the evidence pattern we observe. On this reading the
"raised central pavilion with pergola" is a feed/tank house with a shade arbour, and the "cornice"
is a plate line.

**Confidence: moderate, and explicitly unverified.** It is a hypothesis that fits the evidence,
not a determination — and it is deliberately NOT written into the catalog, which still says the
building is unidentified. It is not resolvable at 749×1024: the distinction between a cornice and a
plate line, or a pergola and a shade arbour, is below the resolution of every copy that exists.

**What would settle it:** the rescan (§ header). At 1200 dpi from the print, glazing pattern, wall
construction and roof framing would all be legible, and the institution-vs-poultry-house question
answers itself in one look.

## 4f. Where the search stands after the reframe

**Closed today:** "El Retiro" (a private house); "the Mesa" as a lead (a residential district — the
Beaumont Land & Water Co.'s **La Mesa Miravilla**, whose CDNC footprint is 984 hits that are almost
entirely *delinquent-tax lot listings*, i.e. an ordinary residential subdivision with no institutional
building); Alamogordo/Cloudcroft NM (no citrus at 4,300 ft).

**The revised target profile** — this is what a future session should hunt, and it is materially
different from what the last three sessions hunted:

| was assumed | actually measured / argued |
|---|---|
| distinct knoll, dissected badlands | **~2.5 % fan slope; ~20 ft rise at ~900 ft** |
| large public institution | **unknown function** — the aerial argument kills the "invisible institution" premise |
| Beaumont outskirts | **probably not Beaumont**, or else demolished pre-1938 |
| ~200 ft | **~160 ft long, ~15 ft wall, ~900 ft from camera** (±, depends on lens FOV assumption) |

**A reading that has NOT been tested and now deserves to be:** a large **private estate house** on a
citrus ranch. A 1910s Craftsman/Prairie house explains every element without strain — a **pergola**
across the front (near-universal on the type), a long **glazed sleeping porch or sun room** reading
as the "continuous ribbon of multi-pane sash", a projecting wing with a deep flat eave, light stucco,
sited on a low swell above its own grove. Crucially it explains **both** silences at once in a way
the poultry house cannot: a private house is *present* on a 1938 aerial but indistinguishable from
hundreds of others, and never named in a newspaper. It would also make the frame legible as what it
probably is — a man photographed with his tree, on his own or a friend's place.

## 4g. What to ask BLD (they invite it)

`mybld.org/local-history` states that the district digitised "about **200 photographs**" under a
Local History Digital Resources Project grant with Califa — i.e. **Calisphere collection 1828 IS the
whole digitised set**; there is no separate BLD database to mine, which closes that route. The same
page says: *"If there are some faces that you recognize in some of the photographs don't hesitate to
contact the library — we would be greatly interested to know!"* They actively want identifications.

Three things to ask for, in order of value:
1. **A high-resolution rescan of accession 89-01-74** (see header) — settles it outright.
2. **Does the photo appear in "Images of America: Beaumont" (2007)?** — see lead 5b; the caption may
   simply name the building.
3. **Is there a donor file or accession record for 89-01-74?** The accession prefix "89-" implies a
   1989 donation; a donor name and any accompanying note would say whose place this was, which
   answers the location question even if the building stays nameless.

## 4h. Citrus WAS grown at Beaumont — the location objection collapses

**Los Angeles Herald, 7 March 1909, "ORANGES GROW BESIDE APPLES — Beaumont Furnishes Fine
Illustration"** (`LAH19090307.2.110.57`):

> "…an orange tree seventeen years old now growing nearby an apple tree **in the town of Beaumont**,
> and both bearing fine, sweet fruit. The position occupied by the orange tree is a **sheltered**
> one, but the fact that orange trees and apples both grow in Beaumont constitutes an almost
> unparalleled horticultural paradox." Lemon, grapefruit, pomegranate and fig "are also successfully
> grown there."

This kills the standing argument (carried since 2026-07-24 a) that a citrus tree argues *against*
Beaumont. Citrus at Beaumont was a **booster novelty, deliberately photographed as proof of
climate** — the Herald ran a "cut" of one. **"H. L. Priest and his fruit tree" now reads naturally
as exactly that genre**, and Priest was a newspaperman, which makes him the obvious subject for it.
(The article also names **Mr. and Mrs. Royce**, of "El Retiro on the Mesa" — see §4e.)

⇒ Beaumont is back **in** scope. The tension with the 1938 aerial negative (§4c) is unresolved and
is now the sharpest open contradiction in this file.

**The Gazette ran its own illustrated version** — "ORANGES AND APPLES GROW SIDE BY SIDE IN BEAUMONT",
Daily Gazette 25 Feb 1909 (`BMTG19090225.2.9`), by the same writer, John D. Reavis — and the cut is
captioned: **"Seventeen-Year-Old Orange Tree in Grounds of R. T. Jenkins."** The illustration was
viewed: a large, mature, densely-foliaged tree in a garden setting. **It is NOT our photograph** —
ours is a young tree on open graded ground with a man beside it. Different tree, different scene.

**But the name matters.** R. T. Jenkins was in the Priests' immediate circle: San Bernardino Sun,
7 Aug 1930, lists "Beaumont's six survivors" of the Civil War as **J. V. R. Priest, R. T. Jenkins**,
G. W. Mathers and others; the two appear together again on a Cherry Valley library committee
(Gazette, 20 Jun 1935). So the one *documented* citrus site in the town of Beaumont belonged to a
close associate of Herbert Priest's father, and was already a booster subject.

**Tested 2026-07-24 b and it does not resolve from CDNC:** `"Jenkins" orange Beaumont place` in BMTG
1908–35 returns only 8 hits, none of which give Jenkins an address. The Gazette never locates his
place. To pursue it needs a Riverside County deed index or a Great Register entry, not newspapers.

**Lead as originally framed: locate R. T. Jenkins' place in the town of Beaumont.** If the
Priest photograph belongs to the same booster series (a plausible reading — Priest was a newspaper
writer), the Jenkins connection is the thread to pull, and whatever stands ~900 ft west of that lot
is the building. Jenkins' tree was planted c. 1892 and cannot be the tree in our frame, so this is a
lead about the *milieu and the site*, not about the tree itself.

## 4i. Wellwood 1921 re-tested at matched scale — still out, but for the right reason

The 2026-07-24 rejection rested partly on "the Wellwood site is not on a distinct knoll" — a reason
**§4e(i) disproved**, since there is no knoll anywhere in this photograph. So the candidate was
re-tested properly: the Wellwood photo was downsampled so the building spans the same ~215 px our
building spans, then both were enlarged 8× identically.

**Result: decisively different.** Wellwood presents a large steeply-raked **gable end with an
oculus** and an arched niche, a low **tile-roofed arched entrance portal**, and a **tile-roofed**
arcade. Our building has no gable, no oculus, no arch, and no tile anywhere. **Ruled out on form,
verified at matched resolution.**

## 4j. Best look yet at the building (8× + autocontrast, `scratchpad/ours_8x.png`)

- **Left:** projecting wing, flat roof, deep flat canopy/overhang, dark opening beneath.
- **Centre:** a **long open framework** — regularly spaced posts, a horizontal beam, and what read as
  rafters or lattice above, with vines or shrubs growing through. It runs most of the frontage.
- **Right:** solid wall with a **continuous ribbon of ~5–6 large multi-pane sash** (each roughly a
  4×3 grid of small panes), a **doorway** at that run's left end, a thin projecting **cornice**
  above, and a light solid **base band** below.
- Flat rooflines throughout, stepped in height. Light stucco or concrete.

**A third functional reading, untested:** a **commercial nursery / greenhouse range**. The open
framework reads equally well as a **lath (shade) house**, and the multi-pane bands as glazing. That
would explain the young grafted citrus and the freshly graded ground directly — a nursery is exactly
where one photographs a man with a new grafted tree. Beaumont-area nurseries are documented
(Enterprise, 20 Jan 1909: a Glendora pioneer takes a large Cherry Valley holding and "will conduct
nursery"). Against it: the right-hand run has a solid wall with cornice above and solid base below,
where a glasshouse would be glazed to the ground under a pitched roof.

**Tested and it does not land.** BMTG 1908–32, `nursery trees` (153 hits): the only real operation is
the **Beaumont Nursery Company** (Burson & Mears), advertising 1908–09 from **Egan Avenue south of
the railroad** — i.e. the *low* ground, wrong side, wrong height. Its business was **eucalyptus**
(an order for one million seedlings, 30 Jul 1908), not citrus, and it predates Priest's arrival by
nearly a decade. A second small dealer, W. J. Baker at Sixth and Edgar, likewise sells eucalyptus.
Neither implies a 160-ft glazed range. **The nursery reading has no candidate behind it.**

## 5. Open leads

1. **Record-Gazette (Banning)** in CDNC — a local Pass weekly, ≥1913–1922, never searched.
2. **Where Priest lived / owned land.** At ~250 m the building was effectively his neighbour.
   Routes: 1920/1930 census, Riverside County deeds, Beaumont city directories, Gazette locals.
3. **La Mesa Miravilla** (Beaumont Land & Water Co. tract) — promotional photo "Road through
   subdivision no. 2" shows exactly this dissected, freshly graded terrain, and the brochure cover
   is drawn *through a pergola*. Where was the tract? Anything built on it?
4. **Widen the 1938 aerial sweep** beyond Beaumont — see §4c. FrameFinder needs no login and the
   scans are free; the neighbouring AXM_1938A frames cover Banning, Cherry Valley and San Timoteo.
5. **Re-scan the original print at BLD** (see header) — the single highest-value action available.
5b. **"Images of America: Beaumont"** (Arcadia Publishing, 2007), Jeff Fox & Kenneth M. Holtzclaw,
   128 pp., ISBN 9780738547138 — 180–240 captioned B&W photographs, almost certainly drawn from the
   same BLD holdings. **Arcadia captions routinely carry local knowledge that never reached
   Calisphere's one-line descriptions.** Not searchable online (no Internet Archive scan; Open
   Library has the record but `ia: None`; Arcadia titles are "no preview" in Google Books), so this
   has to be done with a physical copy — BLD and the SGPHS museum will both hold one. **If this
   photograph is in the book, its caption is the cheapest possible route to the answer.**
6. **Question the Beaumont assumption.** §4c is the first real evidence against it. Priest was
   mobile (Minneapolis to 1917; Calexico/Imperial Valley 1917–19 via his sister Mrs. C. H. Hevener;
   "will teach in Mexico" 1920; Cloudcroft, N.M. 1921). Imperial Valley is flat and Cloudcroft has no
   citrus, so neither fits — but the possibility that the plate is not a Beaumont scene at all is now
   live and should be tested rather than assumed away.
