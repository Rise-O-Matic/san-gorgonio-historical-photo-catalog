"""Apply data/editorial-captions.json to the already-generated catalog.

Mirrors scripts/author_date_overrides.py: the source originals are read-only and
catalog.json is a generated artifact, so this overlays the maintained caption +
attribution layer onto data/catalog.json and site/data/catalog.json without a
full image rescan, then rewrites data/catalog.csv with the caption/attribution
columns. Run scripts/catalog_pipeline.py instead when you need a full rebuild;
this is the fast path used after editing editorial-captions.json.
"""
import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from catalog_pipeline import apply_editorial_captions  # noqa: E402

CAPTIONS = REPO / "data" / "editorial-captions.json"
CSV_FIELDS = ["reference_number", "id", "title", "caption", "attribution", "attribution_confidence",
              "caption_source", "date_start", "date_end", "decade", "curated",
              "selected_default", "classification", "recommended_print",
              "master_file_id", "rights_status", "research_status"]


def ensure_fields(record):
    record.setdefault("attribution", "Unknown")
    record.setdefault("attribution_confidence", "unknown")
    record.setdefault("caption_source", "")


def main():
    for p in (REPO / "data" / "catalog.json", REPO / "site" / "data" / "catalog.json"):
        if not p.exists():
            continue
        doc = json.loads(p.read_text(encoding="utf-8"))
        for r in doc["records"]:
            ensure_fields(r)
        n = apply_editorial_captions(doc["records"], CAPTIONS)
        p.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Applied {n} caption entries -> {p.relative_to(REPO)}")

    cat = json.loads((REPO / "data" / "catalog.json").read_text(encoding="utf-8"))
    rows = []
    for r in cat["records"]:
        rows.append({
            "reference_number": r.get("reference_number", ""),
            "id": r["id"], "title": r["title"], "caption": r.get("caption", ""),
            "attribution": r.get("attribution", "Unknown"),
            "attribution_confidence": r.get("attribution_confidence", "unknown"),
            "caption_source": r.get("caption_source", ""),
            "date_start": r["date"]["start"], "date_end": r["date"]["end"],
            "decade": r["decade"], "curated": r["curated"],
            "selected_default": r["selected_default"],
            "classification": r["print_viability"]["classification"],
            "recommended_print": r["print_viability"]["recommended"],
            "master_file_id": r["master_file_id"], "rights_status": r["rights_status"],
            "research_status": r["research_status"],
        })
    csv_path = REPO / "data" / "catalog.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Rewrote data/catalog.csv with caption/attribution columns ({len(rows)} rows)")


if __name__ == "__main__":
    main()
