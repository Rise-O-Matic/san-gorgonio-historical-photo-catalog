#!/usr/bin/env python3
"""Build the visual-verification pair list for the phase-0 match sweep.

Joins data/calisphere/match-plausible.json (plausible record<->ark pairs) with
local preview images and downloaded Calisphere comparison images, writing
<scratchpad>/verify-pairs.json for the verification workflow. Pairs whose
comparison image is missing are listed separately so nothing drops silently.
"""
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SP = Path(os.path.expanduser(
    "~/AppData/Local/Temp/claude/C--GitHub-san-gorgonio-historical-photo-catalog/"
    "1d96bed5-715a-4851-b873-182aa3db052d/scratchpad"))


def main() -> None:
    cat = json.loads((REPO / "data" / "catalog.json").read_text(encoding="utf-8"))
    recs = {r["id"]: r for r in cat["records"]}
    pl = json.loads((REPO / "data" / "calisphere" / "match-plausible.json").read_text(encoding="utf-8"))
    titles = {}
    for name in ("beaumont-1828", "banning-1582"):
        for it in json.loads((REPO / "data" / "calisphere" / f"{name}.json").read_text(encoding="utf-8")):
            titles[it["ark"]] = it["title"]

    pairs, missing = [], []
    for rid, v in pl.items():
        r = recs.get(rid)
        if not r:
            continue
        for c in v["plausible"]:
            img = SP / "cali_img" / f"{c['ark']}.jpg"
            entry = {
                "record_id": rid,
                "record_title": r["title"],
                "record_caption": (r.get("caption") or "")[:250],
                "date_start": r["date"]["start"], "date_end": r["date"]["end"],
                "preview": str(REPO / "site" / r["preview"]),
                "ark": c["ark"], "coll": c["coll"],
                "cali_title": titles.get(c["ark"], ""),
                "cali_img": str(img),
                "text_confidence": c.get("confidence", ""),
            }
            if img.exists() and img.stat().st_size > 3000:
                pairs.append(entry)
            else:
                missing.append(entry)

    out = {"pairs": pairs, "missing_image": missing}
    (SP / "verify-pairs.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(pairs)} pairs ready, {len(missing)} missing comparison image -> {SP / 'verify-pairs.json'}")
    if missing:
        print("missing arks:", sorted({m['ark'] for m in missing}))


if __name__ == "__main__":
    main()
