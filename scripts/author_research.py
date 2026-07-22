#!/usr/bin/env python3
"""Merge all authored research batches into the three editorial layers.

Canonical research data lives in per-batch JSON files under
data/research-authored/ (one file per research pass, filename-sorted; a later
batch wins when two batches carry the same record id). Each batch file:

  {
    "batch": "2026-07-20-mural-selects",
    "description": "...",
    "source_manifest": "path or URL of the research deliverable",
    "researched": "YYYY-MM-DD",          # default for entries lacking one
    "entries": {
      "img_<id>": {
        "position": 1,                    # optional mural select position
        "title": "Corrected display title",
        "original_title": "What the archive file was called",
        "caption": { caption, attribution, attribution_confidence,
                     caption_source, basis },          # optional
        "date": { date_start, date_end, display,
                  confidence, basis },                 # optional
        "rights_status": "Public domain | Copyrighted | Permission required | Unclear",
        "rights": "one-line rights note (holder / rationale / next action)",
        "holding": { institution, item_id, url } | null,
        "best_master": { location, pixels, note } | null,
        "description": "long researched description",
        "corrections": [ ... ],
        "evidence": [ {label, url}, ... ],
        "open_questions": [ ... ],
        "research_status": "Researched | Provenance verified",  # optional
        "researched": "YYYY-MM-DD",                             # optional
      }, ...
    }
  }

This script rebuilds data/editorial-research.json wholesale from the batches
and overlays each entry's caption/date onto data/editorial-captions.json and
data/editorial-overrides.json. Apply to the catalog afterwards with
scripts/apply_research.py (fast path) or a full catalog_pipeline.py rebuild.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
AUTHORED = DATA / "research-authored"


def load_batches() -> list[dict]:
    batches = []
    for path in sorted(AUTHORED.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        doc["_path"] = path
        batches.append(doc)
    return batches


def merge_captions(batches: list[dict]) -> int:
    path = DATA / "editorial-captions.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    captions = doc.setdefault("captions", {})
    n = 0
    for batch in batches:
        for rid, entry in batch["entries"].items():
            cap = entry.get("caption")
            if not cap:
                continue
            captions[rid] = dict(cap)
            n += 1
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return n


def merge_overrides(batches: list[dict]) -> int:
    path = DATA / "editorial-overrides.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    overrides = doc.setdefault("overrides", {})
    n = 0
    for batch in batches:
        for rid, entry in batch["entries"].items():
            date = entry.get("date")
            if not date:
                continue
            overrides[rid] = dict(date)
            n += 1
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return n


def write_research(batches: list[dict]) -> int:
    path = DATA / "editorial-research.json"
    entries: dict[str, dict] = {}
    for batch in batches:
        batch_manifest = batch.get("source_manifest", "")
        batch_date = batch.get("researched", "")
        for rid, entry in batch["entries"].items():
            merged = {
                "title": entry.get("title"),
                "original_title": entry.get("original_title"),
                "description": entry.get("description"),
                "corrections": entry.get("corrections", []),
                "evidence": entry.get("evidence", []),
                "rights": entry.get("rights"),
                "rights_status": entry.get("rights_status"),
                "holding": entry.get("holding"),
                "best_master": entry.get("best_master"),
                "open_questions": entry.get("open_questions", []),
                "research_status": entry.get("research_status", "Researched"),
                "researched": entry.get("researched", batch_date),
                "source_manifest": entry.get("source_manifest", batch_manifest),
            }
            if entry.get("position") is not None:
                merged["select_position"] = entry["position"]
            entries[rid] = merged
    doc = {
        "schema_version": "2.0.0",
        "description": (
            "Deep-research layer: corrected titles, long descriptions, corrections "
            "logs, per-claim evidence links, rights, holding institutions, "
            "best-known masters and open questions. Canonical source: the per-batch "
            "JSON files under data/research-authored/, merged by "
            "scripts/author_research.py. Applied to catalog.json by "
            "catalog_pipeline.apply_editorial_research."
        ),
        "entries": entries,
    }
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return len(entries)


def main() -> None:
    batches = load_batches()
    if not batches:
        raise SystemExit(f"No batch files found under {AUTHORED}")
    names = ", ".join(b.get("batch", b["_path"].stem) for b in batches)
    print(f"Batches loaded:   {len(batches)} ({names})")
    print(f"Captions merged:  {merge_captions(batches)} records -> data/editorial-captions.json")
    print(f"Dates merged:     {merge_overrides(batches)} records -> data/editorial-overrides.json")
    print(f"Research written: {write_research(batches)} entries -> data/editorial-research.json")
    print("Now run scripts/apply_research.py (or a full catalog_pipeline.py rebuild).")


if __name__ == "__main__":
    main()
