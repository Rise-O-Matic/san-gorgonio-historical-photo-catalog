#!/usr/bin/env python3
"""Join visually confirmed Calisphere matches with harvested item metadata.

Inputs:
  data/calisphere/matches-confirmed.json  (from the visual verification workflow)
  data/calisphere/item-metadata.json      (merged item-page harvest)
  data/catalog.json
Output:
  <scratchpad>/transcribe-prep.json — everything a transcription agent needs
  per confirmed record: local record state + Calisphere ground truth.
Records confirmed against more than one ark keep all confirmed arks (agents
pick the primary and cite the rest as related items).
"""
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SP = Path(os.path.expanduser(
    "~/AppData/Local/Temp/claude/C--GitHub-san-gorgonio-historical-photo-catalog/"
    "1d96bed5-715a-4851-b873-182aa3db052d/scratchpad"))


def main() -> None:
    confirmed = json.loads((REPO / "data" / "calisphere" / "matches-confirmed.json").read_text(encoding="utf-8"))
    meta = {m["ark"]: m for m in json.loads((REPO / "data" / "calisphere" / "item-metadata.json").read_text(encoding="utf-8")) if not m.get("error")}
    hashes = json.loads((REPO / "data" / "calisphere" / "calisphere_hashes.json").read_text(encoding="utf-8"))
    hashes.update(json.loads((REPO / "data" / "calisphere" / "banning-hashes.json").read_text(encoding="utf-8")))
    cat = json.loads((REPO / "data" / "catalog.json").read_text(encoding="utf-8"))
    recs = {r["id"]: r for r in cat["records"]}

    out, missing_meta = {}, []
    for c in confirmed:
        rid, ark = c["record_id"], c["ark"]
        r = recs.get(rid)
        m = meta.get(ark)
        if not m:
            missing_meta.append(ark)
            m = {"ark": ark, "note": "metadata not harvested — agent must flag as open question"}
        entry = out.setdefault(rid, {
            "record": {
                "title": r["title"], "caption": r.get("caption", ""),
                "attribution": r.get("attribution", ""),
                "caption_source": r.get("caption_source", ""),
                "date_start": r["date"]["start"], "date_end": r["date"]["end"],
                "preview": "site/" + r.get("preview", ""),
                "visible_text": (r.get("visible_text") or "")[:300],
                "original_pixels": r.get("original_pixels"),
                "research_status": r.get("research_status", ""),
            },
            "calisphere_matches": [],
        })
        hp = hashes.get(ark)
        entry["calisphere_matches"].append({
            "ark": ark,
            "confidence": c.get("confidence", ""),
            "match_note": c.get("note", ""),
            "item_url": f"https://calisphere.org/item/ark:/13030/{ark}/",
            "clip_master_url": f"https://calisphere.org/clip/2000x2000/{hp}" if hp else None,
            "metadata": m,
        })

    (SP / "transcribe-prep.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(out)} records with confirmed matches -> {SP / 'transcribe-prep.json'}")
    if missing_meta:
        print("arks missing metadata:", sorted(set(missing_meta)))


if __name__ == "__main__":
    main()
