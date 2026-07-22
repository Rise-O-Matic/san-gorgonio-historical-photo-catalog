"""Apply all three editorial layers to the already-generated catalog.

Fast path after editing data/editorial-overrides.json, editorial-captions.json
or editorial-research.json (e.g. via scripts/author_select_research.py): the
source originals are read-only and catalog.json is a generated artifact, so
this overlays dates -> captions -> research onto data/catalog.json and
site/data/catalog.json without a full image rescan, re-sorts records
chronologically (research can move dates), then rewrites data/catalog.csv.
Run scripts/catalog_pipeline.py instead when you need a full rebuild.
"""
import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from catalog_pipeline import (  # noqa: E402
    apply_editorial_captions,
    apply_editorial_overrides,
    apply_editorial_research,
)

DATA = REPO / "data"
CSV_FIELDS = ["id", "title", "caption", "attribution", "attribution_confidence",
              "caption_source", "date_start", "date_end", "decade", "curated",
              "selected_default", "classification", "recommended_print",
              "master_file_id", "rights_status", "research_status",
              "evidence_urls"]


def ensure_fields(record):
    record.setdefault("attribution", "Unknown")
    record.setdefault("attribution_confidence", "unknown")
    record.setdefault("caption_source", "")


def main():
    for p in (DATA / "catalog.json", REPO / "site" / "data" / "catalog.json"):
        if not p.exists():
            continue
        doc = json.loads(p.read_text(encoding="utf-8"))
        records = doc["records"]
        for r in records:
            ensure_fields(r)
        n_dates = apply_editorial_overrides(records, DATA / "editorial-overrides.json")
        n_caps = apply_editorial_captions(records, DATA / "editorial-captions.json")
        n_res = apply_editorial_research(records, DATA / "editorial-research.json")
        records.sort(key=lambda it: (it["date"]["start"] is None,
                                     it["date"]["start"] or 9999,
                                     it["title"].lower()))
        p.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Applied {n_dates} dates, {n_caps} captions, {n_res} research entries -> {p.relative_to(REPO)}")

    cat = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
    rows = []
    for r in cat["records"]:
        evidence = (r.get("research") or {}).get("evidence", [])
        rows.append({
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
            "evidence_urls": "; ".join(e["url"] for e in evidence if e.get("url")),
        })
    csv_path = DATA / "catalog.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Rewrote data/catalog.csv ({len(rows)} rows, evidence_urls column included)")

    # Keep the research workbench honest: researched records leave the queue's
    # "Queued" state and drop to the bottom, and their titles track the catalog.
    by_id = {r["id"]: r for r in cat["records"]}
    for qp in (DATA / "research-queue.json", REPO / "site" / "data" / "research-queue.json"):
        if not qp.exists():
            continue
        queue = json.loads(qp.read_text(encoding="utf-8"))
        updated = 0
        for item in queue:
            record = by_id.get(item.get("record_id"))
            if not record:
                continue
            item["title"] = record["title"]
            status = record.get("research_status")
            reasons = {
                "Researched": "Researched — evidence-linked record in the catalog",
                "Provenance verified": "Provenance verified — modern record; source and rights documented",
            }
            if status in reasons and item.get("status") != status:
                item["status"] = status
                item["priority"] = 0
                item["reason"] = reasons[status]
                updated += 1
        queue.sort(key=lambda it: (-it.get("priority", 0), it.get("title", "").lower()))
        qp.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Refreshed {qp.relative_to(REPO)} ({updated} records marked Researched)")


if __name__ == "__main__":
    main()
