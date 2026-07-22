# -*- coding: utf-8 -*-
"""Generate mural-module-panels-v2.svg — modular photo+label panels for the
Beaumont timeline mural. One SVG, 18 identical-footprint modules, each a named
group Illustrator imports as an editable object tree.

v2 (2026-07-21): DM Serif headers, Franklin Gothic/Libre Franklin body, panel
color #15424A; photos found in production-ready/ (matched by NN_ prefix) are
linked into their windows via relative <image> hrefs — others stay FPO rects.

Geometry (1 SVG unit = 1 pt; 72 pt = 1 in; designed at full print size):
  module (colored panel)   16.00 in wide, uniform height
  black matte (uniform)    14.75 x 13.00 in outer, min 1.0 in border
  photo opening            fit to each photo's aspect inside the matte
  text plate               14.75 in wide, uniform height (max of all modules)
Type sized for 1-3 ft viewing: title 34 pt, body 20/27, credit 14 pt.
"""
import os
import sys
from PIL import Image, ImageFont
sys.stdout.reconfigure(encoding="utf-8")

IN = 72.0
SELECTS = ("X:/My Drive/Projects/Beaumont Library District/projects/"
           "timeline-mural/2026-07-17_selects")
PROD_DIR = SELECTS + "/production-ready"

# ---------- palette ----------
PANEL   = "#15424A"   # deep teal backing panel (one global fill - easy to swap)
MATTE   = "#131313"   # black matte
PLATE   = "#FAF8F3"   # warm white text plate
ACCENT  = "#15424A"   # tag + accent strip (same as panel)
TITLE_C = "#1A1A1A"
BODY_C  = "#2B2B2B"
CRED_C  = "#6E6E6E"
FPO_BG  = "#C8C8C8"
FPO_LN  = "#A6A6A6"
FPO_TX  = "#5A5A5A"

# ---------- geometry ----------
MOD_W     = 16.0 * IN
PAD       = 0.625 * IN          # panel padding around matte / plate
MATTE_W   = MOD_W - 2 * PAD     # 14.75 in
MATTE_H   = 13.0 * IN
MIN_BORD  = 1.0 * IN            # minimum matte border -> max opening
GAP       = 0.375 * IN          # matte -> text plate
TPAD_X    = 0.6 * IN            # text plate side padding
COL_W     = MATTE_W - 2 * TPAD_X

COLS, GUTTER, MARGIN = 3, 1.5 * IN, 1.0 * IN

# ---------- type ----------
SERIF = "'DM Serif Text', 'DM Serif Display', Georgia, serif"
SANS  = "'Franklin Gothic Book', 'Libre Franklin', Arial, sans-serif"
SANSM = "'Franklin Gothic Medium', 'Libre Franklin', Arial, sans-serif"
LEAD_TITLE, LEAD_BODY, LEAD_CRED = 42, 27, 19

USERFONTS = "C:/Users/maxam/AppData/Local/Microsoft/Windows/Fonts"
ft_tag    = ImageFont.truetype("framd.ttf", 15)                      # FG Medium
ft_title  = ImageFont.truetype(USERFONTS + "/DMSerifText-Regular.ttf", 34)
ft_body   = ImageFont.truetype("FRABK.TTF", 20)                      # FG Book
ft_credit = ImageFont.truetype("FRABKIT.TTF", 14)                    # FG Book It

def wrap(text, font, maxw):
    lines, cur = [], ""
    for w in text.split():
        trial = (cur + " " + w).strip()
        if font.getlength(trial) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ---------- production-ready photos (matched by NN_ prefix) ----------
PHOTOS = {}
for f in sorted(os.listdir(PROD_DIR)):
    if f.lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp")):
        num = f.split("_", 1)[0]
        if num.isdigit() and num not in PHOTOS:
            with Image.open(os.path.join(PROD_DIR, f)) as im:
                PHOTOS[num] = (f, im.size[0], im.size[1])

# ---------- content ----------
# (num, slug, tag, title, body, credit, (px_w, px_h), fpo_note)
BLD = "Courtesy of the Beaumont Library District Local History Collection"
MODULES = [
 ("01", "council-house", "01 · C. 1890S",
  "Council House (Kishumnawat), Morongo Reservation",
  "The ceremonial big house — kishumnawat — of the Morongo (Potrero) Reservation: a long council house of pole framework and brush thatch, an elder seated by its plank door. In Cahuilla tradition the big house stood at the center of the village, home of the sacred ceremonial bundle and of the hereditary clan leader.",
  "Courtesy of The Huntington Library, San Marino, California",
  (3000, 2858), None),

 ("02", "pauline-weaver", "02 · POSTHUMOUS SKETCH",
  "Pauline Weaver",
  "No photograph of Pauline Weaver (c. 1797–1867) is known to exist; this crosshatched sketch is an imagined likeness drawn long after his death. Tennessee-born trapper, scout and prospector, Weaver took possession of the abandoned Rancho San Gorgonio in 1845 and ran cattle in the pass for a decade — the first settler of the San Gorgonio Pass.",
  "Artist unknown",
  (188, 268), "low-res source — re-source before print"),

 ("03", "egan-avenue-1907", "03 · 1907",
  "Egan Avenue, Beaumont",
  "Teamsters' wagons line the dirt roadway of Egan Avenue near the railroad crossing in 1907 — the two-story livery stable at center, the porch-fronted Funk Realty Co. office beside it, and the young town's false-front blocks beyond. George Egan had laid out the townsite, first called San Gorgonio, only twenty-three years earlier.",
  BLD, (1024, 803), None),

 ("04", "sp-depot", "04 · C. 1905–1915",
  "Southern Pacific Depot",
  "An Edwardian crowd fills the platform of the Southern Pacific depot, built in 1887, looking east down the main line toward the water tower and oil tanks of the yard. Under the station board, a Sunset Route mileage sign points the other way down the line: TO NEW ORLEANS.",
  BLD, (1024, 831), None),

 ("05", "fifth-and-egan", "05 · 1890S",
  "Fifth Street & Egan Avenue",
  "Beaumont's main business corner in the 1890s: the false-front San Gorgonio Mercantile Company at center — still wearing the town's pre-1887 name — the small post office at far left, and the pool hall at right. The post office had operated out of corners of the town's general stores since 1884.",
  BLD + " · © Laura May Stewart Trust", (1024, 728), None),

 ("06", "locomotive-2789", "06 · C. 1905–1915",
  "Shop Crew with Locomotive No. 2789",
  "A Southern Pacific shop crew poses on the pilot of locomotive No. 2789 at the Beaumont yard — a Harriman Common Standard 2-8-0 Consolidation, identified from the engine's own number plates and period locomotive rosters — with a whaleback oil tender and the yard's 30,000-gallon oil tank behind.",
  BLD, (1024, 801), None),

 ("07", "stewart-ranch", "07 · C. 1884–1900S",
  "Stewart Ranch Grain Harvest",
  "Crop hands pause with their horse teams and harvesting machinery in a cut grain field on the Stewart Ranch, the railroad line and the San Jacinto foothills beyond. Reznor Perry Stewart homesteaded at Beaumont in 1883 and built a grain and hay ranch that grew to some 2,200 acres.",
  BLD + " · © Laura May Stewart Trust", (1024, 818), None),

 ("08", "kish-morongo", "08 · C. 1900",
  "A Summer House (Kish), Morongo Reservation",
  "A woman sits at the entrance of a brush-thatched summer house — a Cahuilla kish — her cook-pot beside her on the swept ground, the reservation's fields and the mountain wall of the pass behind. Ethnographers visiting the pass in this era recorded the airy brush house still in everyday use.",
  "Courtesy of the Banning Library District Local History Collection",
  (1024, 686), None),

 ("09", "capt-john-morongo", "09 · C. 1890",
  "Captain John Morongo",
  "Captain John Morongo (c. 1843–1898), hereditary leader of the Serrano Maarrenga'yam clan and the first recognized captain of the Potrero Reservation. He served for years on the U.S. Indian police, campaigned for public schooling, and is the leader whose family name the reservation and the Morongo Band formally adopted.",
  "Courtesy of The Huntington Library, San Marino, California",
  (382, 500), "await Huntington portrait master"),

 ("10", "beaumont-hotel", "10 · C. 1895",
  "The Beaumont Hotel",
  "Guests pose along the wraparound veranda of the Beaumont Hotel, the $40,000 Queen Anne showpiece raised in 1887 to sell boom-time land buyers on the pass. Empty for years after the bust of 1888, it reopened in 1907 as the Hotel Edinburgh — and burned to the ground in August 1909.",
  "Photograph by C. C. Pierce & Co. · " + BLD.replace("Courtesy of the ", ""),
  (1024, 805), None),

 ("11", "womans-club", "11 · DEDICATED 1917",
  "Beaumont Woman's Club",
  "Members' automobiles nose in under the street trees at the Beaumont Woman's Club clubhouse on Sixth Street. The club — organized in 1908, and the founding force behind Beaumont's public library — dedicated this hall on May 11, 1917. It still occupies the site today.",
  BLD, (1024, 645), None),

 ("12", "beaumont-bank-library", "12 · BUILT 1911",
  "The Beaumont Bank — First Home of the Library",
  "The brand-new Beaumont Bank, built in 1911 as the Funk Building. When Beaumont voted itself a library district that August — the only one of its kind in the state at the time — the library opened in two rented ground-floor rooms here, at ten dollars a month, and stayed until the Carnegie building opened in 1914.",
  BLD, (1024, 645), None),

 ("13", "hl-priest", "13 · C. 1900S–1910S",
  "H. L. Priest and His Fruit Tree",
  "H. L. Priest — bowler hat, walrus mustache, waistcoat and rolled sleeves — stands beside a young fruit tree in freshly worked ground, photographed, in the words of the library's record, “in the early days.” Beaumont's promoters were then selling the pass to the world as an orchard paradise.",
  BLD, (749, 1024), None),

 ("14", "mellen-ranch", "14 · 1909",
  "Mellen Ranch Orchard in Bloom",
  "Rows of fruit trees in full blossom stripe the ploughed ground of the Mellen Ranch in 1909. The album page it comes from was assembled by the Beaumont Land and Water Company, whose promotional albums sold the San Gorgonio Pass as an orchard paradise; Mellen's fruit took prizes at local exhibitions in these same years.",
  BLD, (1024, 928), None),

 ("15", "carnegie-addition", "15 · C. 1966–1977",
  "The Carnegie Library, Enlarged",
  "The 1914 Carnegie library — a $10,000 grant, its cornerstone laid in February 1914 — behind the low modern entrance wing added in the mid-1960s, which more than doubled its floor space. The arched windows and cypresses of the original building rise behind the new lettered façade.",
  "From a period printed publication · Beaumont Library District",
  (644, 425), "low-res halftone — re-scan original before print"),

 ("16", "mansard-roof", "16 · C. 1978–2008",
  "Under the Mansard Roof",
  "The Carnegie building wearing the shallow tile mansard added in 1977/78 to unify it with its modern addition. The mansard came off in 2008, when the original parapet roofline was restored — the building still serves today as Riverside County's last operating Carnegie library.",
  "Photographer unknown · Beaumont Library District collection",
  (250, 131), "low-res source — re-scan original before print"),

 ("17", "aerial-1982", "17 · 1982",
  "Beaumont from the Air",
  "Looking north across Beaumont to the San Gorgonio foothills in 1982: the original townsite grid is still an island of trees and rooftops along the Interstate 10 corridor, with open grain land and scattered ranchettes where the subdivisions would later spread. The city counted fewer than 7,000 residents.",
  "Beaumont Library District collection", (3258, 2482), None),

 ("18", "aerial-2010", "18 · 2010",
  "Beaumont from the Air",
  "The same view in 2010, after the boom: red-roofed master-planned communities blanket the old ranchland to the foothills, and distribution warehouses line the freeway corridor. Between the 2000 and 2010 censuses Beaumont more than tripled, from about 11,000 residents to nearly 37,000.",
  "Beaumont Library District collection", (3093, 2151), None),
]

# ---------- measure text, find uniform plate height ----------
def module_lines(m):
    _, _, _, title, body, credit, _, _ = m
    return (wrap(title, ft_title, COL_W),
            wrap(body, ft_body, COL_W),
            wrap(credit, ft_credit, COL_W))

PAD_TOP, STRIP_H = 42, 4
plate_hts, all_lines = [], []
for m in MODULES:
    tl, bl, cl = module_lines(m)
    all_lines.append((tl, bl, cl))
    y = STRIP_H + PAD_TOP + 13                    # tag baseline
    y += 48 + (len(tl) - 1) * LEAD_TITLE          # title baselines
    y += 46 + (len(bl) - 1) * LEAD_BODY           # body baselines
    y += 40 + (len(cl) - 1) * LEAD_CRED           # credit baselines
    plate_hts.append(y + 14 + 34)                 # descender + pad bottom
PLATE_H = max(plate_hts)
MOD_H = PAD + MATTE_H + GAP + PLATE_H + PAD

# ---------- layout ----------
LEGEND_H = 170
ROWS = (len(MODULES) + COLS - 1) // COLS
SVG_W = 2 * MARGIN + COLS * MOD_W + (COLS - 1) * GUTTER
SVG_H = MARGIN + LEGEND_H + ROWS * MOD_H + (ROWS - 1) * GUTTER + MARGIN

out = []
out.append('<?xml version="1.0" encoding="UTF-8"?>')
out.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
           f'xmlns:xlink="http://www.w3.org/1999/xlink" width="{SVG_W:.0f}pt" '
           f'height="{SVG_H:.0f}pt" viewBox="0 0 {SVG_W:.0f} {SVG_H:.0f}">')

def text_block(x, y0, lines, fam, weight, size, fill, leading,
               anchor="start", style=None, spacing=None):
    sty = f' font-style="{style}"' if style else ""
    wgt = f' font-weight="{weight}"' if weight != "normal" else ""
    spc = f' letter-spacing="{spacing}"' if spacing else ""
    anc = f' text-anchor="{anchor}"' if anchor != "start" else ""
    t = [f'<text font-family="{fam}"{wgt}{sty} font-size="{size}" '
         f'fill="{fill}"{spc}{anc}>']
    for i, ln in enumerate(lines):
        t.append(f'  <tspan x="{x:.1f}" y="{y0 + i * leading:.1f}">{esc(ln)}</tspan>')
    t.append('</text>')
    return t

# legend
lx, ly = MARGIN, MARGIN
out.append('<g id="legend-delete-before-print">')
out += text_block(lx, ly + 20, ["BEAUMONT TIMELINE MURAL — MODULE SYSTEM · v2"],
                  SANSM, "normal", 18, TITLE_C, 24, spacing=2)
legend_lines = [
    "Designed at full print size: each module is %.2f × %.2f in. Type for 1–3 ft viewing: DM Serif headers, Franklin Gothic/Libre Franklin body (20 pt)." % (MOD_W / IN, MOD_H / IN),
    "Every module is identical: colored panel, fixed 14.75 × 13.0 in black matte (opening varies per photo, min 1 in border), warm-white text plate.",
    "Photos in production-ready/ are LINKED into their windows (keep this SVG beside that folder). Gray FPO rects await the rest — clip photos to them.",
    "Recolor all panels at once: Select > Same > Fill Color.",
]
out += text_block(lx, ly + 52, legend_lines, SANS, "normal", 14, BODY_C, 22)
for i, (c, lab) in enumerate([(PANEL, "panel"), (MATTE, "matte"), (PLATE, "plate")]):
    sx = lx + i * 150
    out.append(f'<rect x="{sx}" y="{ly + 138}" width="24" height="24" fill="{c}" stroke="#999" stroke-width="0.5"/>')
    out += text_block(sx + 32, ly + 155, [f"{lab}  {c}"], SANS, "normal", 12, CRED_C, 14)
out.append('</g>')

# modules
placed = []
for idx, m in enumerate(MODULES):
    num, slug, tag, title, body, credit, (pw, ph), note = m
    if num in PHOTOS:
        fname, pw, ph = PHOTOS[num]
    tl, bl, cl = all_lines[idx]
    col, row = idx % COLS, idx // COLS
    x0 = MARGIN + col * (MOD_W + GUTTER)
    y0 = MARGIN + LEGEND_H + row * (MOD_H + GUTTER)

    out.append(f'<g id="module-{num}-{slug}">')
    out.append(f'  <rect id="m{num}-panel" x="{x0:.1f}" y="{y0:.1f}" '
               f'width="{MOD_W:.1f}" height="{MOD_H:.1f}" fill="{PANEL}"/>')

    # matte + opening
    mx, my = x0 + PAD, y0 + PAD
    asp = pw / ph
    ww = min(MATTE_W - 2 * MIN_BORD, (MATTE_H - 2 * MIN_BORD) * asp)
    wh = ww / asp
    if wh > MATTE_H - 2 * MIN_BORD:
        wh = MATTE_H - 2 * MIN_BORD; ww = wh * asp
    wx, wy = mx + (MATTE_W - ww) / 2, my + (MATTE_H - wh) / 2
    out.append(f'  <g id="m{num}-matte">')
    out.append(f'    <rect x="{mx:.1f}" y="{my:.1f}" width="{MATTE_W:.1f}" '
               f'height="{MATTE_H:.1f}" fill="{MATTE}"/>')
    out.append(f'  </g>')
    if num in PHOTOS:
        placed.append(f"{num} <- {fname}")
        href = f"production-ready/{fname}"
        out.append(f'  <g id="m{num}-photo">')
        out.append(f'    <image x="{wx:.1f}" y="{wy:.1f}" width="{ww:.1f}" '
                   f'height="{wh:.1f}" xlink:href="{href}" href="{href}"/>')
        out.append(f'  </g>')
    else:
        out.append(f'  <g id="m{num}-photo-fpo">')
        out.append(f'    <rect id="m{num}-clip-rect" x="{wx:.1f}" y="{wy:.1f}" '
                   f'width="{ww:.1f}" height="{wh:.1f}" fill="{FPO_BG}"/>')
        out.append(f'    <line x1="{wx:.1f}" y1="{wy:.1f}" x2="{wx + ww:.1f}" '
                   f'y2="{wy + wh:.1f}" stroke="{FPO_LN}" stroke-width="1"/>')
        out.append(f'    <line x1="{wx + ww:.1f}" y1="{wy:.1f}" x2="{wx:.1f}" '
                   f'y2="{wy + wh:.1f}" stroke="{FPO_LN}" stroke-width="1"/>')
        cx, cy = wx + ww / 2, wy + wh / 2
        fpo_lines = [f"FPO · PHOTO {num}", f"source {pw} × {ph} px"]
        if note: fpo_lines.append(note.upper())
        fy0 = cy - (len(fpo_lines) - 1) * 11
        out += ["    " + s for s in text_block(cx, fy0, fpo_lines, SANSM,
                                               "normal", 14, FPO_TX, 22,
                                               anchor="middle")]
        out.append(f'  </g>')

    # text plate
    px_, py_ = x0 + PAD, my + MATTE_H + GAP
    out.append(f'  <g id="m{num}-label">')
    out.append(f'    <rect x="{px_:.1f}" y="{py_:.1f}" width="{MATTE_W:.1f}" '
               f'height="{PLATE_H:.1f}" fill="{PLATE}"/>')
    out.append(f'    <rect x="{px_:.1f}" y="{py_:.1f}" width="{MATTE_W:.1f}" '
               f'height="{STRIP_H}" fill="{ACCENT}"/>')
    tx = px_ + TPAD_X
    yb = py_ + STRIP_H + PAD_TOP + 13
    out += ["    " + s for s in text_block(tx, yb, [tag], SANSM, "normal", 15,
                                           ACCENT, 20, spacing=2.5)]
    yb += 48
    out += ["    " + s for s in text_block(tx, yb, tl, SERIF, "normal", 34,
                                           TITLE_C, LEAD_TITLE)]
    yb += (len(tl) - 1) * LEAD_TITLE + 46
    out += ["    " + s for s in text_block(tx, yb, bl, SANS, "normal", 20,
                                           BODY_C, LEAD_BODY)]
    yb += (len(bl) - 1) * LEAD_BODY + 40
    out += ["    " + s for s in text_block(tx, yb, cl, SANS, "normal", 14,
                                           CRED_C, LEAD_CRED, style="italic")]
    out.append('  </g>')
    out.append('</g>')

out.append('</svg>')

dest = SELECTS + "/mural-module-panels-v2.svg"
with open(dest, "w", encoding="utf-8") as f:
    f.write("\n".join(out))

import xml.etree.ElementTree as ET
ET.parse(dest)  # raises if malformed
print(f"OK  {dest}")
print(f"canvas {SVG_W/IN:.1f} x {SVG_H/IN:.1f} in  |  module {MOD_W/IN:.2f} x {MOD_H/IN:.2f} in ({MOD_H:.0f} pt)")
print(f"text plate {MATTE_W/IN:.2f} x {PLATE_H/IN:.2f} in (uniform)")
print("photos linked:", ", ".join(placed) if placed else "none")
for m, (tl, bl, cl) in zip(MODULES, all_lines):
    print(f"  {m[0]}: title {len(tl)}L, body {len(bl)}L, credit {len(cl)}L")
