#!/usr/bin/env python3
"""Sync catalog original_pixels/print_viability with upgraded masters.

upgrade_previews_from_masters.py regenerates previews/thumbs from better
masters but leaves catalog.json untouched, so original_pixels (shown on the
site) and print_viability (drives the viability filter) go stale. This script
walks the same two master pools, applies the same same-image hash guard, and
where a matching master out-resolves the recorded original_pixels it rewrites
original_pixels and recomputes print_viability with the pipeline's own
print_metrics (keeping the record's existing quality factor and crop
allowance). Updates data/catalog.json, site/data/catalog.json, and the
classification/recommended_print columns of data/catalog.csv.

Usage: python scripts/sync_catalog_dims.py [--dry-run]
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog_pipeline import print_metrics
from upgrade_previews_from_masters import HASH_THRESHOLD, SELECTS_DIR, ahash, hamming

REPO = Path(__file__).resolve().parents[1]
SITE = REPO / "site"
CLIP_DIR = REPO / "data" / "calisphere" / "masters"
CROP_DIR = REPO / "data" / "masters"  # hand-verified per-record crops, named {rid}.jpg

DRY = "--dry-run" in sys.argv


def master_candidates(records: dict) -> dict[str, Path]:
    """rid -> best master path, same pools/selection as the upgrade script."""
    out: dict[str, Path] = {}
    selects = json.loads((REPO / "data" / "research-authored" / "2026-07-20-mural-selects.json").read_text(encoding="utf-8"))["entries"]
    by_position = {e["position"]: rid for rid, e in selects.items() if e.get("position")}
    files_by_pos: dict[int, list[Path]] = {}
    for path in sorted(SELECTS_DIR.glob("*.*")):
        m = re.match(r"(\d{2})[-_]", path.name)
        if m:
            files_by_pos.setdefault(int(m.group(1)), []).append(path)
    for pos, rid in by_position.items():
        best, best_area = None, -1
        for p in files_by_pos.get(pos, []):
            try:
                with Image.open(p) as im:
                    area = im.width * im.height
            except OSError:
                continue
            if area > best_area:
                best, best_area = p, area
        if best is not None:
            out[rid] = best
    for path in CLIP_DIR.glob("img_*.jpg"):
        rid = path.stem
        if rid in records:
            # a selects-folder master wins only if it has more pixels
            if rid in out:
                with Image.open(out[rid]) as a, Image.open(path) as b:
                    if a.width * a.height >= b.width * b.height:
                        continue
            out[rid] = path
    # hand-verified crops override both pools: they carry the genuine pixels
    # of crops whose parent scans fail the same-image check (album pages, mounts)
    for path in CROP_DIR.glob("img_*.jpg"):
        if path.stem in records:
            out[path.stem] = path
    return out


def main() -> None:
    catalog_path = REPO / "data" / "catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    records = {r["id"]: r for r in catalog["records"]}
    changed: list[tuple[str, str, str, str]] = []

    for rid, master_path in sorted(master_candidates(records).items()):
        rec = records[rid]
        preview_path = SITE / "assets" / "previews" / f"{rec['master_file_id']}.jpg"
        if not preview_path.exists():
            continue
        try:
            master = Image.open(master_path)
            master.load()
        except OSError:
            continue
        preview = Image.open(preview_path)
        if hamming(ahash(master), ahash(preview)) > HASH_THRESHOLD:
            continue  # different image (e.g. a reference sketch) — leave alone
        old = rec["original_pixels"]
        if master.width * master.height <= old["width"] * old["height"] * 1.05:
            continue
        factor = rec["quality"]["factor"]
        crop = rec["print_viability"]["crop_allowance_percent"] / 100
        old_class = rec["print_viability"]["classification"]
        rec["original_pixels"] = {"width": master.width, "height": master.height}
        rec["print_viability"] = print_metrics(master.width, master.height, factor, crop)
        changed.append((rid, rec["title"][:44],
                        f"{old['width']}x{old['height']} -> {master.width}x{master.height}",
                        f"{old_class} -> {rec['print_viability']['classification']}"))

    for rid, title, dims, cls in changed:
        print(f"{title:<46} {dims:<26} {cls}")
    print(f"\n{len(changed)} record(s) updated" + (" (dry run, nothing written)" if DRY else ""))
    if DRY or not changed:
        return

    payload = json.dumps(catalog, indent=2, ensure_ascii=False)
    catalog_path.write_text(payload, encoding="utf-8")
    (SITE / "data" / "catalog.json").write_text(payload, encoding="utf-8")

    csv_path = REPO / "data" / "catalog.csv"
    with csv_path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
        fieldnames = rows[0].keys() if rows else []
    for row in rows:
        rec = records.get(row["id"])
        if rec:
            row["classification"] = rec["print_viability"]["classification"]
            row["recommended_print"] = rec["print_viability"]["recommended"]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
