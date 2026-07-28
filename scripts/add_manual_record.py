#!/usr/bin/env python3
"""Add a catalog record from a JSON metadata file (manual insertion).

Usage:
    python scripts/add_manual_record.py <record.json>

Records are normally *generated* by catalog_pipeline.py scanning a source
directory; the editorial layers only overlay onto records that already exist.
This tool is for the other case — a one-off "found" item (a Library of Congress
Sanborn sheet, a Calisphere scan, etc.) that is not in a scanned source dir.

It reproduces everything the pipeline would compute for that image — a files[]
entry with perceptual hashes, resized thumbnail (560px) and preview (1600px)
assets, and the print-viability math — then bakes a fully-authored record into
BOTH data/catalog.json and site/data/catalog.json, re-sorts chronologically,
updates the summary counts, and rewrites data/catalog.csv. Re-running with the
same image replaces the existing record/file in place (idempotent), so the JSON
is the source of truth: keep it under data/manual-records/.

Caveat: manual records are NOT re-scanned by a full catalog_pipeline.py rebuild,
so a rebuild would drop them — re-apply by re-running this script.

JSON fields (only `image` and `title` are required; everything else is
optional and falls back to a sensible default):

    {
      "image": "X:/path/to/image.png",          # required
      "title": "...",                             # required
      "original_title": "...",
      "date": {"start": 1895, "end": 1895,
               "display": "February 1895",
               "confidence": "high", "basis": "..."},
      "caption": "...",
      "description": "...",
      "attribution": "...", "attribution_confidence": "confirmed",
      "caption_source": "...",
      "rights_status": "Public domain",           # see RIGHTS_ALLOWED
      "rights_note": "...",
      "locations": [...], "people": [...],
      "subjects": [...], "search_terms": [...],
      "evidence": [{"label": "...", "url": "..."}],
      "holding": {"institution": "...", "item_id": "...", "url": "..."},
      "corrections": [...], "open_questions": [...],
      "provenance": "...",                         # who found it / where
      "researched": "2026-07-24",
      "curated": false, "selected_default": false,
      "source_key": "manual", "source_priority": 90,
      "research_status": "Researched"
    }
"""
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import catalog_pipeline as cp  # noqa: E402

DATA = REPO / "data"
SITE = REPO / "site"

# rights_status must be one of these EXACT strings or the site's colour-coded
# pill (RIGHTS_META in site/app.js) will not render.
RIGHTS_ALLOWED = {"Public domain", "Permission required", "Copyrighted", "Unclear"}
DEFAULT_RIGHTS_NOTE = "Do not infer reuse rights from age; verify against the holding institution or rights statement."
PD_RIGHTS_NOTE = "Public domain — free to use and reuse; verify the holding institution's statement for the specific item."

CSV_FIELDS = ["reference_number", "id", "title", "caption", "attribution", "attribution_confidence",
              "caption_source", "date_start", "date_end", "decade", "curated",
              "selected_default", "classification", "recommended_print",
              "master_file_id", "rights_status", "research_status", "evidence_urls"]


def tokenize(*values):
    words = set()
    for value in values:
        for token in re.findall(r"[a-z0-9]+", str(value).lower()):
            if len(token) > 1:
                words.add(token)
    return sorted(words)


def build_file_entry(src: Path, spec: dict):
    normalized = cp.normalize_path(src)
    file_id = cp.stable_id("file", normalized)
    stat = src.stat()
    digest = cp.sha256_file(src)
    meta, image = cp.image_metadata(src)
    thumb_rel = f"assets/thumbs/{file_id}.jpg"
    preview_rel = f"assets/previews/{file_id}.jpg"
    cp.optimized_image(image, SITE / thumb_rel, 560, 84)
    cp.optimized_image(image, SITE / preview_rel, 1600, 84)

    suggestion = {
        "title": spec.get("original_title") or spec["title"], "caption": "",
        "date_start": (spec.get("date") or {}).get("start"),
        "date_end": (spec.get("date") or {}).get("end"),
        "decade": ((spec.get("date") or {}).get("start") or 0) // 10 * 10 or None,
        "locations": spec.get("locations", []), "people": spec.get("people", []),
        "subjects": spec.get("subjects", []), "visible_text": "",
        "search_terms": spec.get("search_terms", []), "confidence": "high",
        "review_note": "Manually added record; provenance verified in the metadata JSON.",
    }
    facts = [
        {"field": "source_path", "value": str(src), "source": "filesystem", "confidence": "certain"},
        {"field": "filename", "value": src.name, "source": "filesystem", "confidence": "certain"},
    ]
    if spec.get("provenance"):
        facts.append({"field": "provenance", "value": spec["provenance"],
                      "source": "editorial_research", "confidence": "provided"})
    entry = {
        "file_id": file_id, "path": str(src), "filename": src.name,
        "extension": src.suffix.lower(), "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "modified_at_is_historical_date": False, "sha256": digest,
        "source_key": spec.get("source_key", "manual"),
        "source_priority": int(spec.get("source_priority", 90)),
        "curated": bool(spec.get("curated", False)),
        "source_memberships": [spec.get("source_key", "manual")],
        "image": meta,
        "ocr": {"status": "unavailable", "text": "", "engine": None, "confidence": None},
        "suggestions": suggestion, "facts": facts,
        "thumbnail": thumb_rel, "preview": preview_rel,
    }
    return entry, meta, digest, suggestion, facts


def build_record(spec, file_entry, meta, digest, suggestion, facts):
    quality, factor = cp.quality_label(meta["sharpness_score"])
    file_id = file_entry["file_id"]
    record_id = cp.stable_id("img", digest)

    date_in = spec.get("date")
    if date_in and date_in.get("start"):
        start, end = date_in["start"], date_in.get("end", date_in["start"])
        date = {"start": start, "end": end,
                "display": date_in.get("display", str(start)),
                "confidence": date_in.get("confidence", "medium"),
                "editable": True, "source": "editorial_research",
                "basis": date_in.get("basis", "")}
        decade = start // 10 * 10
    else:
        date = {"start": None, "end": None, "display": "Undated",
                "confidence": "unknown", "editable": True}
        decade = None

    rights = spec.get("rights_status", "Unclear")
    if rights not in RIGHTS_ALLOWED:
        raise SystemExit(f"rights_status must be one of {sorted(RIGHTS_ALLOWED)}; got {rights!r}")
    rights_note = spec.get("rights_note") or (PD_RIGHTS_NOTE if rights == "Public domain" else DEFAULT_RIGHTS_NOTE)

    has_research = bool(spec.get("description") or spec.get("evidence"))
    research_status = spec.get("research_status") or ("Researched" if has_research else "Needs research")

    research = {}
    for key in ("select_position", "original_title", "description", "corrections",
                "evidence", "holding", "open_questions", "researched", "source_manifest"):
        value = spec.get(key)
        if value not in (None, [], "", {}):
            research[key] = value

    subjects = spec.get("subjects") or tokenize(spec["title"])
    search_terms = spec.get("search_terms") or tokenize(spec["title"], " ".join(subjects))

    return {
        "id": record_id, "title": spec["title"], "caption": spec.get("caption", ""),
        "date": date, "decade": decade,
        "locations": spec.get("locations", []), "people": spec.get("people", []),
        "subjects": subjects, "visible_text": "", "search_terms": search_terms,
        "research_status": research_status, "rights_status": rights, "rights_note": rights_note,
        "selected_default": bool(spec.get("selected_default", False)),
        "curated": bool(spec.get("curated", False)),
        "master_file_id": file_id,
        "master_reason": "Single-source manual addition via scripts/add_manual_record.py.",
        "version_file_ids": [file_id], "alternates": [],
        "quality": {"label": quality, "factor": factor, "editable": True},
        "print_viability": cp.print_metrics(meta["width"], meta["height"], factor, 0.10),
        "metadata_suggestions": [{"file_id": file_id, "suggestion": suggestion}],
        "facts": list(facts), "conflicts": [],
        "client": {"selected": bool(spec.get("selected_default", False)), "comment": ""},
        "thumbnail": file_entry["thumbnail"], "preview": file_entry["preview"],
        "original_pixels": {"width": meta["width"], "height": meta["height"]},
        "attribution": spec.get("attribution", "Unknown"),
        "attribution_confidence": spec.get("attribution_confidence", "unknown"),
        "caption_source": spec.get("caption_source", ""),
        "research": research or None,
    }


def upsert(record, file_entry):
    config = json.loads((REPO / "config" / "catalog.config.json").read_text(encoding="utf-8"))
    registry = cp.assign_reference_numbers(
        [record], config.get("research_candidates", []), DATA / "reference-numbers.json"
    )
    cp.json_dump(SITE / "data" / "reference-numbers.json", registry)
    sort_key = lambda it: (it["date"]["start"] is None, it["date"]["start"] or 9999, it["title"].lower())
    for cat_path in (DATA / "catalog.json", SITE / "data" / "catalog.json"):
        doc = json.loads(cat_path.read_text(encoding="utf-8"))
        doc["records"] = [r for r in doc["records"] if r["id"] != record["id"]]
        doc["files"] = [f for f in doc["files"] if f["file_id"] != file_entry["file_id"]]
        doc["records"].append(json.loads(json.dumps(record)))
        doc["files"].append(json.loads(json.dumps(file_entry)))
        doc["records"].sort(key=sort_key)
        s = doc.setdefault("summary", {})
        s["readable_files"] = len(doc["files"])
        s["historical_records"] = len(doc["records"])
        s["curated_records"] = sum(1 for r in doc["records"] if r.get("curated"))
        s["selected_by_default"] = sum(1 for r in doc["records"] if r.get("selected_default"))
        fmts = {}
        for f in doc["files"]:
            fmts[f["extension"]] = fmts.get(f["extension"], 0) + 1
        s["formats"] = dict(sorted(fmts.items()))
        cat_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  {cat_path.relative_to(REPO)}: {len(doc['records'])} records, {len(doc['files'])} files")

    for queue_path in (DATA / "research-queue.json", SITE / "data" / "research-queue.json"):
        queue = json.loads(queue_path.read_text(encoding="utf-8"))
        queue = [item for item in queue if item.get("record_id") != record["id"]]
        queue.append(cp.research_queue_entry(record, config.get("research_sources", [])))
        queue.sort(key=lambda item: (-item["priority"], item["title"]))
        cp.json_dump(queue_path, queue)


def rewrite_csv():
    cat = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
    rows = []
    for r in cat["records"]:
        ev = (r.get("research") or {}).get("evidence", [])
        rows.append({
            "reference_number": r.get("reference_number", ""),
            "id": r["id"], "title": r["title"], "caption": r.get("caption", ""),
            "attribution": r.get("attribution", "Unknown"),
            "attribution_confidence": r.get("attribution_confidence", "unknown"),
            "caption_source": r.get("caption_source", ""),
            "date_start": r["date"]["start"], "date_end": r["date"]["end"], "decade": r["decade"],
            "curated": r["curated"], "selected_default": r["selected_default"],
            "classification": r["print_viability"]["classification"],
            "recommended_print": r["print_viability"]["recommended"],
            "master_file_id": r["master_file_id"], "rights_status": r["rights_status"],
            "research_status": r["research_status"],
            "evidence_urls": "; ".join(e["url"] for e in ev if e.get("url")),
        })
    with (DATA / "catalog.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"  data/catalog.csv: {len(rows)} rows")


def main(argv):
    if len(argv) != 2:
        raise SystemExit(__doc__)
    spec = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    for field in ("image", "title"):
        if not spec.get(field):
            raise SystemExit(f"metadata JSON is missing required field: {field!r}")
    src = Path(spec["image"])
    if not src.exists():
        raise SystemExit(f"image not found: {src}")

    file_entry, meta, digest, suggestion, facts = build_file_entry(src, spec)
    record = build_record(spec, file_entry, meta, digest, suggestion, facts)
    print(f"master: {meta['width']}x{meta['height']} ({meta['megapixels']} MP) {meta['format']}; "
          f"classification={record['print_viability']['classification']}")
    upsert(record, file_entry)
    rewrite_csv()
    print(f"\nOK  id={record['id']}  file_id={file_entry['file_id']}  \"{record['title']}\"")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
