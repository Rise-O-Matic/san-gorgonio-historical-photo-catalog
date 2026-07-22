#!/usr/bin/env python3
"""Author data/editorial-captions.json for every catalog record.

Every record is captioned and attributed. Captions and credit lines are pulled,
in priority order, from:

  1. The San Gorgonio Pass Historical Society timeline (httpssgphs.org) — its
     <figcaption> carries a published caption and an explicit credit line after
     the em dash.
  2. Provenance embedded in the original filenames (the collection's own working
     names routinely record "... from Beaumont Library District", "calisphere",
     "courtesy Steve Lech postcard collection", "leslie rios postcards", etc.).
  3. A descriptive caption written from the filename text and the researched
     date when no published caption exists.

Attribution is recorded honestly as "Unknown" when neither a holding
institution nor a creator can be established from any available source. This
script only writes the maintained JSON layer; catalog_pipeline.py re-applies it
on every run (apply_editorial_captions).
"""
from __future__ import annotations

import html
import json
import os
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CATALOG = REPO / "data" / "catalog.json"
TIMELINE = Path(r"C:\GitHub\httpssgphs.org\timeline.html")
OUT = REPO / "data" / "editorial-captions.json"

# --- Manual caption overrides ------------------------------------------------
# Records whose caption/attribution was refined by hand-research beyond what the
# filename + SGPHS timeline can yield (mirrors the O-dict pattern in
# author_date_overrides.py). Applied last in main(), so these win over the
# auto-generated layer and survive regeneration of editorial-captions.json.
MANUAL_OVERRIDES: dict[str, dict] = {
    # "Demonstration train" (Calisphere CBEA_005) — the foreground locomotive's
    # road number was read directly off the engine in three places that agree:
    # smokebox number plate (2789), headlight number board (278…), and the painted
    # last digit (9) on the smokebox shoulder. SP 2789 is an SP class C-9 Harriman
    # Common Standard 2-8-0 Consolidation (Baldwin ~1905).
    "img_07a9db15e22db499": {
        "caption": "Southern Pacific shop crew with locomotive No. 2789 — a C-9 "
                   "Harriman Common Standard 2-8-0 Consolidation — at the Beaumont "
                   "yard, c. 1905-1915",
        "attribution": "Beaumont Library District (Calisphere CBEA_005); also cited "
                       "as Banning Library District",
        "attribution_confidence": "medium",
        "caption_source": "Locomotive identified from external research (Calisphere CBEA_005)",
        "basis": "Foreground locomotive is Southern Pacific No. 2789, read directly "
                 "from the engine in three places that agree — the oval smokebox "
                 "number plate (2-7-8-9), the headlight number board (278…), and the "
                 "painted last digit (9) on the smokebox shoulder — on a "
                 "high-resolution Calisphere scan (item CBEA_005, ark:/13030/c8g1605q). "
                 "SP 2789 is in the C-9 Consolidation batch 2752-2830 (Baldwin ~1905), "
                 "a Harriman Common Standard 2-8-0; its shared Common-Standard front "
                 "end (tapered-base class lamps, handrail, riveted smokebox disc) "
                 "matches the class. Date c. 1905-1915: the class was built from "
                 "~1905, the high-mounted oil headlight predates SP's 1910s electric "
                 "conversions, and Calisphere dates the scene to the early 1900s "
                 "(superseding the SGPHS timeline's '1890s' caption). Holder differs "
                 "by source: Calisphere lists Beaumont Library District (CBEA_005); "
                 "the SGPHS timeline labels it 'from Banning Library District.' "
                 "Sources: Calisphere CBEA_005; espee.railfan.net SP C-9 roster; "
                 "utahrails.net (Harriman Common Standard).",
    },
    # --- Mural-select records re-grounded against Calisphere (2026-07-20) -------
    # Each below is the SAME photograph as the cited Calisphere Beaumont Library
    # District item (verified by eye). Calisphere is treated as ground truth,
    # superseding the SGPHS-timeline-derived captions.
    # 03 — "1860s stagecoach" is actually a 1907 Egan Ave livery-stable street scene.
    "img_650198dd9e4987ea": {
        "caption": "Egan Avenue at the granite Drew Frank Realty / Burt Carter's "
                   "Livery Stable block, with the livery's horse-drawn rigs lined up "
                   "along the street, 1907",
        "attribution": "Beaumont Library District, via Calisphere (CBEA_011, ark:/13030/c8tb167d)",
        "attribution_confidence": "high",
        "caption_source": "Calisphere Beaumont Library District collection (CBEA_011)",
        "basis": "Same photograph as Calisphere CBEA_011, 'Egan Ave, 1907-1908 "
                 "Granite Building. J. Drew Frank Realty and Burt Carter's Livery "
                 "Stable'; the mount is labeled 'Beaumont 1907'. The catalog's "
                 "'stagecoach, 1860' label is wrong — it is a 1907 Egan Ave street "
                 "scene of the livery stable's wagons.",
    },
    # 04 — Beaumont depot; Calisphere gives no date, catalog's '1875' is untenable.
    "img_6f833a14a7764e47": {
        "caption": "The Southern Pacific depot in Beaumont, looking east along the "
                   "platform, with a passenger train and the water tower beyond",
        "attribution": "Beaumont Library District, via Calisphere (CBEA_134, ark:/13030/c85x2881)",
        "attribution_confidence": "high",
        "caption_source": "Calisphere Beaumont Library District collection (CBEA_134)",
        "basis": "Same photograph as Calisphere CBEA_134, 'Southern Pacific Depot in "
                 "Beaumont, looking east.' Calisphere gives no date; the catalog's "
                 "'1875' is untenable (Beaumont was not platted until c.1887 and the "
                 "scene shows a large Edwardian-era crowd, a long train, and "
                 "telegraph/power poles), so the year is widened to c.1905-1915 on "
                 "visual grounds.",
    },
    # 07 — Stewart Ranch; Calisphere flags this item as Copyrighted (rights holder named).
    "img_c15c20a838d86c18": {
        "caption": "Stewart Ranch harvest — crop hands, horse teams and threshing "
                   "machines at work, looking south toward the railroad and the mountains",
        "attribution": "Beaumont Library District, via Calisphere (ark:/13030/c87p8xrn); "
                       "rights: Copyrighted, Laura May Stewart Trust",
        "attribution_confidence": "high",
        "caption_source": "Calisphere Beaumont Library District collection (ark c87p8xrn)",
        "basis": "Same photograph as Calisphere 'Stewart Ranch; men with horses and "
                 "thrashing machines. Looking south with the railroad, Stewart Ranch, "
                 "and the mountains in the background.' Calisphere gives no date "
                 "(catalog retains c.1883) and marks the item Copyrighted, held by the "
                 "Laura May Stewart Trust — clear rights before any reuse.",
    },
    # 10 — Beaumont 'boom' hotel (later Edinburgh Hotel), burned 16 Aug 1909.
    "img_b08de96dbf496fab": {
        "caption": "The Beaumont 'boom' hotel — the ornate Victorian resort hotel later "
                   "known as the Edinburgh Hotel, which burned on 16 August 1909",
        "attribution": "Beaumont Library District, via Calisphere (ark:/13030/c81v5d9b)",
        "attribution_confidence": "high",
        "caption_source": "Calisphere Beaumont Library District collection (ark c81v5d9b)",
        "basis": "Same photograph as Calisphere c81v5d9b, 'Beaumont boom hotel, burned "
                 "August 16, 1909. Became the Edinburgh Hotel.' Calisphere gives no "
                 "photo date; the hotel stood c.1887-1909, so the catalog's c.1890 is "
                 "plausible and is retained.",
    },
    # 11 — Beaumont Women's Clubhouse building.
    "img_96cb1ed10cb5a0fd": {
        "caption": "The Beaumont Women's Clubhouse building on 6th Street "
                   "(captioned on the mount 'Ladies' Club House, Beaumont')",
        "attribution": "Beaumont Library District, via Calisphere (ark:/13030/c80k27x4)",
        "attribution_confidence": "high",
        "caption_source": "Calisphere Beaumont Library District collection (ark c80k27x4)",
        "basis": "Same real-photo postcard as Calisphere c80k27x4, 'The Beaumont "
                 "Women's Clubhouse Building, 6th Street.' Calisphere gives no date; "
                 "the automobiles visible read as 1920s-30s, so the catalog's 1911 "
                 "(the club's founding year) likely predates the photograph.",
    },
    # 13 — A man and fruit tree.
    "img_a3f413e8c9ed23bb": {
        "caption": "A man standing beside a young fruit tree, a large building on the "
                   "rise behind him",
        "attribution": "Beaumont Library District, via Calisphere (ark:/13030/c83f4nzv)",
        "attribution_confidence": "high",
        "caption_source": "Calisphere Beaumont Library District collection (ark c83f4nzv)",
        "basis": "Same photograph as Calisphere c83f4nzv, 'A man and fruit tree.' "
                 "Calisphere gives no date (catalog retains c.1927); rights: copyright "
                 "status unknown.",
    },
    # 14 — Mellen Ranch orchard, 1909 (catalog's 'Cherry Tree Farm, 1930' is wrong).
    "img_a4ddc941e94d3eed": {
        "caption": "The Mellen Ranch orchard in bloom, Beaumont, 1909",
        "attribution": "Beaumont Library District, via Calisphere (ark:/13030/c8kh0mpc)",
        "attribution_confidence": "high",
        "caption_source": "Calisphere Beaumont Library District collection (ark c8kh0mpc)",
        "basis": "Calisphere item c8kh0mpc titles it 'Mellen Ranch, 1909'; the mount "
                 "carries two labels, 'BEAUMONT ORCHARD 1909' and 'MELLEN RANCH 1909'. "
                 "The catalog's 'Cherry Tree Farm, 1930' is wrong — it is the Mellen "
                 "Ranch orchard, 1909.",
    },
}

# --- 1. Harvest the SGPHS timeline (caption + credit per image) --------------

def harvest_timeline() -> dict[str, dict[str, str]]:
    """Return {alt_text_lower: {caption, attribution, title}} from the timeline."""
    if not TIMELINE.exists():
        return {}
    content = TIMELINE.read_text(encoding="utf-8", errors="replace")
    by_alt: dict[str, dict[str, str]] = {}
    for m in re.finditer(r'<img\b[^>]*>', content, re.I | re.S):
        tag = m.group(0)
        alt = re.search(r'\balt=["\']([^"\']*)', tag, re.I)
        alt = html.unescape(alt.group(1)).strip() if alt else ""
        if not alt:
            continue
        seg = content[m.end():m.end() + 400]
        fc = re.search(r'<figcaption>(.*?)</figcaption>', seg, re.I | re.S)
        fc = html.unescape(re.sub(r'<[^>]+>', '', fc.group(1))).strip() if fc else ""
        h3 = re.search(r'<h3[^>]*>(.*?)</h3>', content[m.end():m.end() + 900], re.I | re.S)
        h3 = html.unescape(re.sub(r'<[^>]+>', '', h3.group(1))).strip() if h3 else ""
        caption, attribution = fc, ""
        if "—" in fc:  # em dash separates caption from credit
            caption, attribution = [x.strip() for x in fc.rsplit("—", 1)]
        by_alt[alt.lower()] = {"caption": caption, "attribution": attribution, "title": h3}
    return by_alt


# --- 2. Attribution parsing from filename provenance -------------------------

# Ordered: first match wins. (pattern, credit, confidence)
ATTRIBUTION_RULES: list[tuple[str, str, str]] = [
    (r"frasher", "Frasher Foto Collection, Pomona Public Library", "high"),
    (r"leslie\s*a?\.?\s*rios|leslie rios", "Leslie A. Rios III Postcard Collection", "high"),
    (r"steve lech", "Steve Lech Postcard Collection", "high"),
    (r"stewart family", "Stewart family collection", "high"),
    (r"estrada", "Estrada family collection", "high"),
    (r"sumner noordman|karen sumner", "Karen Sumner Noordman", "high"),
    (r"banning library", "Banning Library District", "high"),
    (r"from beaumont water district|beaumont water district", "Beaumont-Cherry Valley Water District", "high"),
    (r"from beaumont library district|beaumont library district|beaumont library", "Beaumont Library District", "high"),
    # Every "calisphere" item in this catalog is a Beaumont subject, and the
    # Beaumont Library District Local History Collection (Calisphere collection
    # 1828, ~200 photos of depots, ranches, Summit House, downtown, etc.) is the
    # confirmed contributor for this region — verified against the collection and
    # the prior candidate-review match for the Beaumont depot item.
    (r"calisphere", "Beaumont Library District Local History Collection, via Calisphere", "medium"),
    (r"\bebay\b", "eBay postcard listing (original holder unknown)", "low"),
    (r"record-gazette", "Record-Gazette (Banning)", "high"),
    (r"gateway gazette", "Gateway Gazette (Beaumont)", "high"),
    (r"herald", "Los Angeles Herald", "high"),
    (r"\bgoogle\b", "Google Street View / Google Maps imagery (reference)", "low"),
]


def parse_attribution(text: str) -> tuple[str, str]:
    low = text.lower()
    # explicit "photo credit is X" / "photo by X"
    m = re.search(r"photo credit is\s+([a-z][a-z .'-]+)", low)
    if m:
        return f"{m.group(1).strip().title()} (photo credit)", "high"
    m = re.search(r"\bphoto by\s+([a-z][a-z .'-]+)", low)
    if m:
        return f"{m.group(1).strip().title()}", "high"
    m = re.search(r"courtesy(?:\s+of)?\s+([a-z][a-z .&'-]+?)(?:\s+(?:postcard|collection|photos?)\b|$)", low)
    if m:
        name = m.group(1).strip().title()
        return f"{name} (courtesy)", "high"
    for pat, credit, conf in ATTRIBUTION_RULES:
        if re.search(pat, low):
            return credit, conf
    return "Unknown", "unknown"


# --- 3. Caption cleanup from filename ----------------------------------------

# Provenance / administrative tails to strip from the descriptive caption.
STRIP_PATTERNS = [
    r"\bfrom (?:beaumont|banning) library district\b.*$",
    r"\b(?:beaumont|banning) library district\b.*$",
    r"\bfrom beaumont water district\b.*$",
    r"\bfr(?:om)? karen sumner noordman\b.*$",
    r"\bphoto credit is\b.*$",
    r"\bphoto by\b.*$",
    r"\bcourtesy\b.*$",
    r"\bcalisphere\b",
    r"\bleslie(?: a\.?)?(?: rios)?(?: iii)? (?:postcards?|collection)\b.*$",
    r"\bleslie rios postcards?\b.*$",
    r"\bleslie a?\.? ?rios.*$",
    r"\bsteve lech postcard collection\b.*$",
    r"\bebay\b.*$",
    r"\s*-\s*copy\b",
    r"\bclose up\b",
    r"\bpostcard front\b.*$",
    r"\bscan\b.*$",
    r"\bdate unknown\b.*$",
    r"\bundated(?: photo)?\b",
    r"\bgoogle(?:\s+(?:image|photo|street\s*view))?(?:\s+\d{4})?\b",  # google map refs
    r"\b\d{1,2}-\d{1,2}-\d{2,4}\b",   # embedded date codes like 1-12-23
    r"\b\d{1,2}-\d{2}\b",             # 5-22
    r"\s*\(\d+\)\s*$",                # trailing (1) (2) disambiguators
    r"\s+[a-e]$",                      # trailing single-letter disambiguators (a/b/c)
]

# Known mojibake fixes carried in from the source catalog's filename decoding.
MOJIBAKE = {"Ramona�s": "Ramona's", "Caf�": "Café", "�": "'"}

# Person-name records: subject year ranges in the filename (1859-1935) etc.
YEARS_RE = re.compile(r"\b1[89]\d{2}\b")

# Words kept lowercase in title-casing (unless first word).
SMALL_WORDS = {"a", "an", "and", "at", "by", "for", "from", "in", "of", "on",
               "or", "the", "to", "with", "near", "over"}
# Tokens forced upper/proper regardless of position.
FORCE_CASE = {"bhs": "BHS", "sp": "S.P.", "u.s.": "U.S.", "nasa": "NASA",
              "morongo": "Morongo", "cahuilla": "Cahuilla", "beaumont": "Beaumont",
              "banning": "Banning", "cabazon": "Cabazon", "egan": "Egan"}


def smart_titlecase(text: str) -> str:
    words = text.split(" ")
    out = []
    for i, w in enumerate(words):
        low = w.lower()
        if low in FORCE_CASE:
            out.append(FORCE_CASE[low])
        elif i != 0 and low in SMALL_WORDS:
            out.append(low)
        elif w and w[0].isalpha():
            out.append(w[0].upper() + w[1:])
        else:
            out.append(w)
    return " ".join(out)


def clean_caption(stem: str) -> str:
    text = stem.strip()
    for bad, good in MOJIBAKE.items():
        text = text.replace(bad, good)
    all_lower = text == text.lower()
    text = re.sub(r"[_]+", " ", text)
    # split Name-Name and slug-style hyphenation into spaces
    text = re.sub(r"(?<=[A-Za-z])-(?=[A-Za-z])", " ", text)
    # drop a leading standalone year/decade token (the date is appended separately)
    text = re.sub(r"^(1[89]\d{2}s?|c\.?\s*1[89]\d{2}s?)\s+", "", text)
    for pat in STRIP_PATTERNS:
        text = re.sub(pat, "", text, flags=re.I).strip()
    # drop a trailing standalone modern year that duplicates the appended date
    text = re.sub(r"\s+(19|20)\d{2}s?$", "", text).strip()
    text = re.sub(r"\s{2,}", " ", text)
    text = text.strip(" ,.-—")
    if not text:
        text = re.sub(r"[_-]+", " ", stem).strip()
    if all_lower:
        text = smart_titlecase(text)
    elif text and text[0].islower():
        text = text[0].upper() + text[1:]
    # Always normalize known proper nouns, even inside mixed-case stems.
    text = " ".join(FORCE_CASE.get(w.lower(), w) for w in text.split(" "))
    return text


def best_stem(stems: list[str]) -> str:
    """Prefer the most descriptive human name (has a space, most words, no slug)."""
    def score(s: str) -> tuple:
        words = len(s.split())
        is_slug = 1 if re.fullmatch(r"[a-z0-9-]+", s) else 0
        return (words, -is_slug, len(s))
    return max(stems, key=score)


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    records = catalog["records"]
    timeline = harvest_timeline()

    captions: dict[str, dict] = {}
    for r in records:
        stems, website_caption = [], ""
        for f in r.get("facts", []):
            if f.get("field") == "filename":
                stems.append(os.path.splitext(f["value"])[0])
            elif f.get("field") == "website_caption" and not website_caption:
                website_caption = f["value"]

        date_display = (r.get("date") or {}).get("display", "")

        # Priority 1: SGPHS timeline published caption + credit
        tl = None
        if website_caption:
            alt = website_caption.split(" | ")[0].strip().lower()
            tl = timeline.get(alt)
        if tl and tl["caption"]:
            captions[r["id"]] = {
                "caption": tl["caption"],
                "attribution": tl["attribution"] or "San Gorgonio Pass Historical Society",
                "attribution_confidence": "confirmed" if tl["attribution"] else "high",
                "caption_source": "San Gorgonio Pass Historical Society timeline (httpssgphs.org)",
                "basis": f"Published caption and credit line from the SGPHS timeline entry “{tl['title']}”.",
            }
            continue

        # Priority 2/3: descriptive caption from filename + embedded provenance
        stem = best_stem(stems) if stems else r["title"]
        caption = clean_caption(stem)
        attribution, conf = parse_attribution(" || ".join(stems))
        # Append date when the caption doesn't already state a year/decade.
        if date_display and date_display != "Undated" and not YEARS_RE.search(caption):
            caption = f"{caption}, {date_display}"
        captions[r["id"]] = {
            "caption": caption,
            "attribution": attribution,
            "attribution_confidence": conf,
            "caption_source": "Original filename / collection working title" if attribution == "Unknown"
                              else "Provenance embedded in original filename",
            "basis": f"Descriptive caption derived from the collection filename “{stem}”"
                     + ("." if attribution == "Unknown"
                        else f"; credit parsed from filename provenance."),
        }

    # Manual research overrides win over the auto-generated layer.
    for rid, ov in MANUAL_OVERRIDES.items():
        if rid in captions:
            captions[rid].update(ov)
        else:
            captions[rid] = ov

    doc = {
        "schema_version": "1.0.0",
        "description": (
            "Maintained caption + attribution layer. Every record is captioned and "
            "attributed. Sources, in priority order: SGPHS timeline figcaptions "
            "(caption + credit), provenance embedded in original collection "
            "filenames, and descriptive captions written from filename text and the "
            "researched date. Attribution is 'Unknown' only when no holder or creator "
            "can be established. Re-applied every pipeline run by apply_editorial_captions."
        ),
        "attribution_confidence_levels": {
            "confirmed": "explicit published credit line (e.g. SGPHS timeline figcaption)",
            "high": "named collection/institution/newspaper recorded in the source filename",
            "medium": "aggregator platform named (e.g. Calisphere) but contributing institution not yet resolved",
            "low": "weak provenance hint (e.g. eBay listing) — holder not established",
            "unknown": "no holder or creator identifiable from any available source",
        },
        "captions": captions,
    }
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    n_unknown = sum(1 for v in captions.values() if v["attribution"] == "Unknown")
    n_tl = sum(1 for v in captions.values() if "timeline" in v["caption_source"])
    print(f"Wrote {len(captions)} caption entries to {OUT}")
    print(f"  timeline-sourced: {n_tl}")
    print(f"  attribution known: {len(captions) - n_unknown}  unknown: {n_unknown}")


if __name__ == "__main__":
    main()
