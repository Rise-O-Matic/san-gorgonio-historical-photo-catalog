#!/usr/bin/env python3
"""Phase-0 match sweep: score every non-researched catalog record against the
Calisphere Beaumont (1828) and Banning (1582) collection item lists.

Token-overlap scoring with boosts for distinctive tokens (proper-ish nouns,
numbers, rare words). Output: data/calisphere/match-candidates.json with the
top-scoring candidates per record, for LLM plausibility review + visual
verification. Purely mechanical — asserts nothing into the catalog.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"

STOP = set("""a an and at by for from in into of on or the to with near adjacent
photo photograph photographic photographed picture image postcard mounted view views
looking early late circa california calif ca beaumont banning cabazon whitewater
idyllwild street streets st ave avenue blvd road rd city town area showing shown
during between his her their two three four five several group large small old new
""".split())

WORD = re.compile(r"[a-z0-9']+")


def tokens(text: str) -> set[str]:
    seq = WORD.findall(text.lower().replace("’", "'"))
    toks = set(seq)
    # joined adjacent-word bigrams so "round house" matches "roundhouse",
    # "club house" matches "clubhouse", etc.
    toks.update(a + b for a, b in zip(seq, seq[1:]) if len(a) + len(b) <= 14)
    return {t for t in toks if t not in STOP and len(t) > 2 and not t.startswith("'")}


def main() -> None:
    cat = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
    records = [r for r in cat["records"] if r.get("research_status") != "Researched"]

    items = []
    for name, coll in (("beaumont-1828", "1828"), ("banning-1582", "1582")):
        for it in json.loads((DATA / "calisphere" / f"{name}.json").read_text(encoding="utf-8")):
            items.append({"ark": it["ark"], "coll": coll, "title": it["title"],
                          "toks": tokens(it["title"])})

    # idf-ish rarity over the calisphere corpus
    df = Counter(t for it in items for t in it["toks"])

    out = {}
    for r in records:
        rtoks = tokens(" ".join(filter(None, [
            r.get("title", ""), r.get("caption", ""),
            " ".join(r.get("subjects", []) or []),
            " ".join(r.get("search_terms", []) or []),
            " ".join(r.get("locations", []) or []),
        ])))
        scored = []
        for it in items:
            common = rtoks & it["toks"]
            if not common:
                continue
            score = sum(1.0 / (1 + 0.3 * (df[t] - 1)) for t in common)
            denom = max(2.0, len(it["toks"]) * 0.55)
            scored.append((round(score / denom, 3), round(score, 2), it))
        scored.sort(key=lambda x: -x[0])
        top = [{"ark": it["ark"], "coll": it["coll"], "title": it["title"],
                "norm": ns, "raw": raw}
               for ns, raw, it in scored[:6] if ns >= 0.18]
        if top:
            out[r["id"]] = {
                "record_title": r.get("title", ""),
                "record_caption": (r.get("caption") or "")[:200],
                "date_start": r["date"]["start"], "date_end": r["date"]["end"],
                "candidates": top,
            }

    path = DATA / "calisphere" / "match-candidates.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    n_str = sum(1 for v in out.values() if v["candidates"][0]["norm"] >= 0.5)
    print(f"{len(records)} records swept; {len(out)} with candidates >= 0.18; "
          f"{n_str} with a strong (>=0.5) top candidate -> {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
