#!/usr/bin/env python3
"""Upgrade site previews/thumbs from better masters than the pipeline sources.

Two master pools:
  A. The 2026-07-17 selects folder on Drive (already-downloaded masters,
     NN_ prefix maps to the mural-selects batch's position field).
  B. Calisphere /clip masters recorded as best_master URLs by the research
     campaign — downloaded (paced) into data/calisphere/masters/.

A master only replaces a record's preview when (1) it is perceptually the
same image (average-hash distance) and (2) it actually adds pixels. Previews
and thumbs are regenerated with the pipeline's own settings (1600px/560px,
JPEG q84) under the same file ids, so catalog data needs no changes.

Usage: python scripts/upgrade_previews_from_masters.py [--dry-run] [--skip-download]
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parents[1]
SITE = REPO / "site"
SELECTS_DIR = Path(r"X:\My Drive\Projects\Beaumont Library District\projects\timeline-mural\2026-07-17_selects\source-photos")
CLIP_DIR = REPO / "data" / "calisphere" / "masters"

PREVIEW_SIZE, THUMB_SIZE, QUALITY = 1600, 560, 84
HASH_THRESHOLD = 14  # of 256 bits; same image incl. crop/tone differences

DRY = "--dry-run" in sys.argv
SKIP_DL = "--skip-download" in sys.argv


def ahash(img: Image.Image, size: int = 16) -> int:
    g = img.convert("L").resize((size, size), Image.Resampling.LANCZOS)
    px = list(g.getdata())
    avg = sum(px) / len(px)
    bits = 0
    for p in px:
        bits = (bits << 1) | (1 if p >= avg else 0)
    return bits


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def regenerate(master: Image.Image, file_id: str) -> None:
    for sub, size in (("previews", PREVIEW_SIZE), ("thumbs", THUMB_SIZE)):
        out = SITE / "assets" / sub / f"{file_id}.jpg"
        rendered = master.copy()
        if rendered.mode not in ("RGB", "L"):
            rendered = rendered.convert("RGB")
        rendered.thumbnail((size, size), Image.Resampling.LANCZOS)
        rendered.save(out, "JPEG", quality=QUALITY, optimize=True, progressive=True)


def consider(rid: str, title: str, file_id: str, master_path: Path, results: list) -> None:
    preview_path = SITE / "assets" / "previews" / f"{file_id}.jpg"
    if not preview_path.exists():
        results.append((rid, title, "SKIP", f"no preview {preview_path.name}"))
        return
    try:
        master = Image.open(master_path)
        master.load()
    except OSError as exc:
        results.append((rid, title, "SKIP", f"unreadable master: {exc}"))
        return
    preview = Image.open(preview_path)
    dist = hamming(ahash(master), ahash(preview))
    m_area, p_area = master.width * master.height, preview.width * preview.height
    label = f"{master.width}x{master.height} vs preview {preview.width}x{preview.height}, dist={dist}"
    if dist > HASH_THRESHOLD:
        results.append((rid, title, "MISMATCH", f"{label} — different image? left untouched"))
        return
    if m_area <= p_area * 1.05:
        results.append((rid, title, "SKIP", f"{label} — no pixel gain"))
        return
    if not DRY:
        regenerate(master, file_id)
    results.append((rid, title, "UPGRADED" if not DRY else "WOULD-UPGRADE", label))


def main() -> None:
    catalog = json.loads((REPO / "data" / "catalog.json").read_text(encoding="utf-8"))
    records = {r["id"]: r for r in catalog["records"]}
    research = json.loads((REPO / "data" / "editorial-research.json").read_text(encoding="utf-8"))["entries"]
    results: list[tuple] = []

    # --- Pool A: selects folder, NN_ prefix -> mural-selects position ---
    selects = json.loads((REPO / "data" / "research-authored" / "2026-07-20-mural-selects.json").read_text(encoding="utf-8"))["entries"]
    by_position = {e["position"]: rid for rid, e in selects.items() if e.get("position")}
    files_by_pos: dict[int, list[Path]] = {}
    for path in sorted(SELECTS_DIR.glob("*.*")):
        m = re.match(r"(\d{2})[-_]", path.name)
        if m:
            files_by_pos.setdefault(int(m.group(1)), []).append(path)
    for pos, rid in sorted(by_position.items()):
        rec = records.get(rid)
        candidates = files_by_pos.get(pos, [])
        if not rec or not candidates:
            results.append((rid, f"select {pos:02d}", "SKIP", "no file with that prefix" if rec else "record missing"))
            continue
        # largest by pixel area wins when a position has several files
        best, best_area = None, -1
        for p in candidates:
            try:
                with Image.open(p) as im:
                    area = im.width * im.height
            except OSError:
                continue
            if area > best_area:
                best, best_area = p, area
        consider(rid, f"select {pos:02d} {best.name}", rec["master_file_id"], best, results)

    # --- Pool B: Calisphere /clip masters from best_master URLs ---
    CLIP_DIR.mkdir(parents=True, exist_ok=True)
    clip_targets = []
    for rid, entry in research.items():
        bm = entry.get("best_master") or {}
        m = re.search(r"https://calisphere\.org/clip/\S+", str(bm.get("location", "")))
        if m:
            clip_targets.append((rid, m.group(0).rstrip(")")))
    for rid, url in clip_targets:
        rec = records.get(rid)
        if not rec:
            results.append((rid, "?", "SKIP", "record missing"))
            continue
        dest = CLIP_DIR / f"{rid}.jpg"
        if not dest.exists() and not SKIP_DL and not DRY:
            proc = subprocess.run(["curl", "-sS", "-f", "-L", "-o", str(dest), url],
                                  capture_output=True, text=True, timeout=120)
            time.sleep(2.5)  # pace Calisphere
            if proc.returncode != 0:
                results.append((rid, rec["title"][:40], "DL-FAIL", proc.stderr.strip()[:120]))
                continue
        if dest.exists():
            consider(rid, rec["title"][:40], rec["master_file_id"], dest, results)
        else:
            results.append((rid, rec["title"][:40], "PENDING-DL", url[:80]))

    width = max((len(r[1]) for r in results), default=10)
    for rid, title, status, detail in results:
        print(f"{status:>13}  {title:<{width}}  {detail}")
    from collections import Counter
    print("\nSummary:", dict(Counter(r[2] for r in results)))


if __name__ == "__main__":
    main()
