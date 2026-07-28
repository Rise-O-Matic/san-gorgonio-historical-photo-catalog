#!/usr/bin/env python3
"""Backfill stable human-readable references into all current catalog data."""

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import catalog_pipeline as cp  # noqa: E402

DATA = REPO / "data"
SITE_DATA = REPO / "site" / "data"
CONFIG = REPO / "config" / "catalog.config.json"


def main() -> None:
    data_catalog = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
    site_catalog = json.loads((SITE_DATA / "catalog.json").read_text(encoding="utf-8"))
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    records = data_catalog["records"]
    candidates = config.get("research_candidates", [])

    data_ids = {item["id"] for item in records}
    site_ids = {item["id"] for item in site_catalog["records"]}
    if data_ids != site_ids:
        raise SystemExit("data/catalog.json and site/data/catalog.json record IDs differ")

    registry = cp.assign_reference_numbers(records, candidates, DATA / "reference-numbers.json")
    by_record = registry["records"]
    for record in site_catalog["records"]:
        record["reference_number"] = by_record[record["id"]]

    cp.json_dump(DATA / "catalog.json", data_catalog)
    cp.json_dump(SITE_DATA / "catalog.json", site_catalog)
    cp.json_dump(SITE_DATA / "reference-numbers.json", registry)
    cp.json_dump(CONFIG, config)

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    candidate_doc = {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "candidates": candidates,
    }
    cp.json_dump(DATA / "candidate-reviews.json", candidate_doc)
    cp.json_dump(SITE_DATA / "candidate-reviews.json", candidate_doc)

    queue_path = DATA / "research-queue.json"
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    queue_by_id = {item["record_id"]: item for item in queue if item.get("record_id") in data_ids}
    for record in records:
        item = queue_by_id.get(record["id"])
        if item is None:
            item = cp.research_queue_entry(record, config.get("research_sources", []))
            queue.append(item)
        item["reference_number"] = record["reference_number"]
        item["title"] = record["title"]
    queue = [item for item in queue if item.get("record_id") in data_ids]
    queue.sort(key=lambda item: (-item["priority"], item["title"]))
    cp.json_dump(DATA / "research-queue.json", queue)
    cp.json_dump(SITE_DATA / "research-queue.json", queue)

    csv_path = DATA / "catalog.csv"
    with csv_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = [field for field in (reader.fieldnames or []) if field != "reference_number"]
    fields.insert(0, "reference_number")
    for row in rows:
        row["reference_number"] = by_record[row["id"]]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(
        f"Assigned {len(records)} catalog references (BLD-####) and "
        f"{len(candidates)} candidate references (BLD-C###)."
    )


if __name__ == "__main__":
    main()
