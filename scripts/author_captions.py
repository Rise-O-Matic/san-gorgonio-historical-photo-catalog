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
