"""Assemble the mural-mockup dataset for site/mural-mockup.html.

The mockup overlays the two halves of the plan on one chronological ribbon:
  READY frames  = production-grade taste-match stand-ins we can print today.
  GAP frames    = Kelly's picks with no printable version; placeholders that name
                  the re-acquisition track (A online / B Malki+Tribe / C storage).

Every frame carries an authored `rationale` — why that image earns a place in a
Beaumont timeline mural — so the page reads as a story, not just a shelf. Rationale
and track are hand-written here (this is the editorial layer); everything else
(image, date, caption, credit, pixels) is pulled from data/catalog.json by id.

Output: data/mural-mockup.json and site/data/mural-mockup.json.
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data" / "catalog.json"
OUT = ROOT / "data" / "mural-mockup.json"
SITE_OUT = ROOT / "site" / "data" / "mural-mockup.json"

# READY: production-grade stand-ins (id -> rationale). Chosen for chronological
# spread and one image per story beat; ordered later by catalog date.
READY = {
    "img_68556e4afecfa748":
        "Ranch women in the saddle — the Stewart daughters put Beaumont's pioneer "
        "founding families on the wall, and a rare frame of frontier women who ran the land.",
    "img_9c26cfc39eca4fc9":
        "The Post Office at Fifth & Egan anchors the young town's civic core — the "
        "corner that was, for decades, the center of Beaumont's public life.",
    "img_50e61a8496f4bfd2":
        "The WCTU fountain is Beaumont's monument to the temperance movement — proof "
        "that national social currents ran straight through a small Pass town.",
    "img_4ec3e978a2772b6b":
        "Railroad crew with Luis Estrada — the Southern Pacific line built Beaumont, "
        "and this frame credits the Latino labor that laid and kept the track.",
    "img_092d2807a0231929":
        "Wellwood School — the arrival of formal education marks the town's shift from "
        "settlement to community raising its own.",
    "img_e8c5738ad26c5ffc":
        "The Cherry Festival Queen crowns Beaumont's identity as cherry country — the "
        "orchards were both the economy and the civic celebration.",
    "img_03ae9abaca02013c":
        "Inside the S&S Store on Fifth Street — Main Street commerce, the daily "
        "downtown that a wall of civic buildings alone would miss.",
    "img_ca02842503e130c9":
        "The Estrada family beside their Southern Pacific home — the railroad story "
        "carried forward a generation, from labor to a rooted Beaumont family.",
    "img_99f7111cab26b389":
        "Beaumont High School — education come of age, the institution that a whole "
        "mid-century generation of residents passed through.",
    "img_add874f3a7967842":
        "Sacred Heart barrio church — the faith and gathering place of Beaumont's "
        "Mexican-American community, and one of the few large-format survivors.",
    "img_2eee4fa95a275d4d":
        "The Dowling orchard and packing store at the industry's peak — dried fruit "
        "and fresh produce that shipped the Pass's name outward.",
    "img_9a697957b7ea88b0":
        "First Christian Church on Egan — the mainline civic congregation, paired with "
        "Sacred Heart to show a town of two communities worshiping side by side.",
}

# GAP: Kelly's picks with no printable version. id -> (track, source, rationale).
GAP = {
    "img_17d9fad337a3fded": ("B", "Malki Museum / Morongo Band (cultural consent required)",
        "The Ceremonial Big House opens the timeline before the town existed — the "
        "Pass as Native homeland, the story's necessary first word."),
    "img_c39e3df610ea24d9": ("A", "Calisphere / published portrait",
        "Pauline Weaver, frontier scout and namesake presence in the Pass — the human "
        "bridge between the Native era and Anglo settlement."),
    "img_650198dd9e4987ea": ("A", "Calisphere coll. 1828 / SGPHS",
        "A stagecoach on the dirt main street — Beaumont as a stop on the road west, "
        "before the railroad changed everything."),
    "img_6f833a14a7764e47": ("A", "Calisphere coll. 1828 (has CBAN/ARK — quick win)",
        "The 1875 depot is the hinge of the whole story: the moment the railroad "
        "arrived and the townsite was born. Non-negotiable on the wall."),
    "img_4e8d4526096e0dd7": ("A", "Beaumont Library District",
        "The earliest Post Office view — the founding-era civic seed that the c.1910 "
        "stand-in later grew from."),
    "img_45720d2a6586237d": ("B", "Malki Museum / NAA (cultural consent required)",
        "A traditional house on the Morongo Reservation, c.1900 — Native life "
        "continuing alongside the new town, not erased by it."),
    "img_72d13585ff607c22": ("B", "Malki Museum / USC / NAA (cultural consent required)",
        "The Morongo Band of Mission Indians, 1908 — a portrait of the Pass's original "
        "community as a living people, central to an honest timeline."),
    "img_b0c11e36c32bf11b": ("C", "Library storage / Record Gazette",
        "The 1960s mansard-roof expansion — postwar Beaumont modernizing, the town "
        "outgrowing its founding footprint."),
    "img_9537c0e4968709f8": ("C", "Library storage / Record Gazette",
        "Late-century development — the timeline's near end, Beaumont becoming the "
        "commuter town it is today."),
}

TRACK_LABEL = {
    "A": "Track A · online (Calisphere / OAC)",
    "B": "Track B · Malki Museum + Morongo Tribe consult",
    "C": "Track C · Library storage / newspaper morgue",
}

# Visitor-facing captions — museum-label voice, written for a general audience
# looking at the wall (what they are seeing and why it mattered), NOT the internal
# argument for inclusion. Draft; every caption needs human/rights confirmation. The
# curatorial argument lives separately in READY/GAP above and goes to the deck notes.
VISITOR = {
    # Ready stand-ins
    "img_68556e4afecfa748":
        "Clara and Laura May Stewart on the family ranch, around 1908. The Stewarts "
        "were among the pioneer families who worked the land in Beaumont's early "
        "years — and this rare frame keeps the women of the ranch in the picture.",
    "img_9c26cfc39eca4fc9":
        "The Beaumont Post Office at Fifth Street and Egan Avenue, about 1910. For "
        "decades this corner was the heart of the young town's public life — where "
        "residents collected mail, traded news, and crossed paths downtown.",
    "img_50e61a8496f4bfd2":
        "The Woman's Christian Temperance Union fountain, 1910. It offered clean water "
        "to people and horses alike, and stood as a very public sign that the era's "
        "great reform movements reached even a small Pass town.",
    "img_4ec3e978a2772b6b":
        "A Southern Pacific railroad crew around 1910, Luis Estrada fourth from the "
        "right. The railroad made Beaumont possible, and the Latino laborers who built "
        "and kept the line were central to the town's growth.",
    "img_092d2807a0231929":
        "Wellwood School, 1916. As Beaumont grew from scattered ranches into a "
        "community, it built schools to raise its own — the mark of families putting "
        "down roots.",
    "img_e8c5738ad26c5ffc":
        "The Cherry Festival Queen, 1919. Beaumont's orchards made it cherry country, "
        "and the annual festival turned the harvest into the town's signature "
        "celebration — a tradition that still shapes local identity.",
    "img_03ae9abaca02013c":
        "Inside George Sumner's S&S Store on Fifth Street in the 1920s. Beyond the "
        "civic buildings lay the everyday downtown — the counters where residents "
        "actually spent their days and their dollars.",
    "img_ca02842503e130c9":
        "The Estrada family beside their Southern Pacific home in the 1940s. A "
        "generation on from the railroad crews, the image shows a family rooted in "
        "Beaumont — the human story behind the town's founding industry.",
    "img_99f7111cab26b389":
        "Beaumont High School, 1942. By mid-century the town's schools had come of "
        "age, and generation after generation of residents passed through these halls.",
    "img_add874f3a7967842":
        "Sacred Heart church in the barrio, late 1940s. A center of faith and "
        "gathering for Beaumont's Mexican-American community, it anchored a "
        "neighborhood essential to the full story of the town.",
    "img_2eee4fa95a275d4d":
        "The Dowling orchard and packing store in the 1950s. At the fruit industry's "
        "height, Beaumont's fresh and dried produce carried the Pass's name far beyond "
        "the valley.",
    "img_9a697957b7ea88b0":
        "First Christian Church on Egan Avenue, about 1950. A mainline congregation at "
        "the town's civic center — shown alongside Sacred Heart to reflect a Beaumont "
        "of many communities worshiping side by side.",
    # Gaps to re-source
    "img_17d9fad337a3fded":
        "A ceremonial Big House on what is today the Morongo Reservation. Long before "
        "the town of Beaumont existed, the San Gorgonio Pass was — and remains — the "
        "homeland of the Cahuilla and Serrano peoples, with the Big House at the "
        "center of ceremonial and community life.",
    "img_c39e3df610ea24d9":
        "Pauline Weaver — scout, trapper, and one of the earliest non-Native figures "
        "to move through the San Gorgonio Pass. His presence bridges the era of Native "
        "homeland and the arrival of American settlers.",
    "img_650198dd9e4987ea":
        "A stagecoach on Beaumont's dirt main street, around 1860. Before the "
        "railroad, the Pass was a stop on the long road west, and the stagecoach was "
        "its lifeline to the wider world.",
    "img_6f833a14a7764e47":
        "The Beaumont train depot, 1875. The arrival of the Southern Pacific railroad "
        "is the hinge of the whole story — the moment a stretch of ranchland became a "
        "townsite with a future.",
    "img_4e8d4526096e0dd7":
        "One of Beaumont's earliest post offices. In a young town the post office was "
        "among the first institutions of civic life — proof that a scattering of "
        "settlers had become a community with a name and an address.",
    "img_45720d2a6586237d":
        "A traditional dwelling on the Morongo Reservation, around 1900. As the new "
        "town grew nearby, Native life in the Pass continued — a reminder that Beaumont "
        "grew up alongside, not in place of, the people who were here first.",
    "img_72d13585ff607c22":
        "Members of the Morongo Band of Mission Indians, 1908. A portrait of the "
        "Pass's original community as a living people — central to any honest telling "
        "of Beaumont's timeline.",
    "img_b0c11e36c32bf11b":
        "A new mansard-roofed building marks Beaumont's postwar expansion, 1965. As "
        "the mid-century town modernized, it began to outgrow its founding footprint.",
    "img_9537c0e4968709f8":
        "New development on the edge of Beaumont, 1988. Near the end of the timeline, "
        "the town starts its turn toward the growing commuter community it is today.",
}


def long_edge_in(rec, ppi="150"):
    try:
        p = rec["print_viability"]["ppi"][ppi]
        return round(max(p["width_inches"], p["height_inches"]), 1)
    except Exception:
        return 0.0


def frame(rec, kind, rationale, track=None, source=None):
    date = rec.get("date") or {}
    px = rec.get("original_pixels") or {}
    return {
        "id": rec["id"],
        "kind": kind,
        "year": date.get("start"),
        "year_display": date.get("display", "?"),
        "date_confidence": date.get("confidence", "low"),
        "title": rec.get("title", ""),
        "caption": rec.get("caption", ""),
        "credit": rec.get("attribution", "Unknown"),
        "thumbnail": rec.get("thumbnail", ""),
        "preview": rec.get("preview", ""),
        "pixels": f'{px.get("width","?")}×{px.get("height","?")}',
        "long_edge_in_150": long_edge_in(rec),
        # visitor_caption = public museum-label voice (shown on the wall / deck slide);
        # argument = internal case for inclusion (deck speaker notes). `rationale` is
        # kept as an alias of argument for backward compatibility with the web page.
        "visitor_caption": VISITOR.get(rec["id"], rec.get("caption", "")),
        "argument": rationale,
        "rationale": rationale,
        "track": track,
        "track_label": TRACK_LABEL.get(track) if track else None,
        "source": source,
    }


def main():
    recs = {r["id"]: r for r in json.loads(CATALOG.read_text(encoding="utf-8"))["records"]}

    frames = []
    for rid, why in READY.items():
        if rid in recs:
            frames.append(frame(recs[rid], "ready", why))
    for rid, (track, source, why) in GAP.items():
        if rid in recs:
            frames.append(frame(recs[rid], "gap", why, track, source))

    frames.sort(key=lambda f: (f["year"] if f["year"] is not None else 9999, f["title"]))

    payload = {
        "project": "Beaumont Timeline Mural — mockup",
        "note": ("Ready frames are production-grade stand-ins printable today. Gap "
                 "frames are Kelly's picks that must be re-sourced; each names its "
                 "re-acquisition track. Nothing is final until a human confirms the "
                 "image and clears rights."),
        "ready_count": sum(1 for f in frames if f["kind"] == "ready"),
        "gap_count": sum(1 for f in frames if f["kind"] == "gap"),
        "frames": frames,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    SITE_OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(OUT, SITE_OUT)
    print(f"Wrote {OUT.relative_to(ROOT)} and {SITE_OUT.relative_to(ROOT)}")
    print(f"{payload['ready_count']} ready + {payload['gap_count']} gap = {len(frames)} frames")


if __name__ == "__main__":
    main()
