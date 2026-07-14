"""Score production-grade records by resemblance to Kelly's 17 curated "Mural Images".

Kelly (Beaumont Library District) hand-picked 17 records as the mural set. Those
picks are low-resolution web scans (<=1024px long edge) and none are printable at
mural size. This script finds the records that ARE production-grade and reads like
Kelly's taste, so we have a mural we can actually print today.

Taste is learned from the 17, not asserted:
  - THEME weights come from how often each theme appears in Kelly's set.
  - ERA weight rewards the founding-era center of gravity of her picks.
  - A subject-identity bonus rewards a printable frame of a subject Kelly
    explicitly chose (Post Office, Depot, Stewart, a civic institution, ...).

Output: data/mural-shortlist.json + a ranked table on stdout.
Zero-cost, reads only data/catalog.json. Nothing here is authoritative until a
human confirms it; this is a selection aid, matching the project's posture.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data" / "catalog.json"
OUT = ROOT / "data" / "mural-shortlist.json"

# Minimum printable long edge (inches) at 150 PPI to count as production-grade.
PRINT_BAR_IN = 24.0

# Theme families -> keyword patterns matched against title + search_terms text.
# Weights are seeded below from Kelly's actual 17, not guessed.
THEMES = {
    "native_heritage": r"morongo|mission indian|cahuilla|ceremonial|reservation|basket|cabazon",
    "pioneer_family": r"stewart|weaver|dowling|estrada|stagecoach|\branch\b|pioneer|mccoy",
    "civic_institution": r"post office|library|woman.?s club|wctu|city hall|fire depart|police|"
                         r"\bschool\b|grammar|\bchurch\b|presbyterian|christian|sacred heart|cemetery",
    "rail_transport": r"depot|\btrain\b|railroad|southern pacific|\bstation\b",
    "agriculture": r"cherry|fruit|orchard|\btree\b|\bfarm\b|produce|festival|pomegranate",
    "downtown_street": r"fifth st|5th st|sixth st|6th st|egan|main street|\bcafe\b|\bhotel\b|"
                       r"\bstore\b|fountain|downtown",
    "development": r"expansion|mansard|develop|subdivision|growth",
}

# Records that are large only because they are recent digital photos: down-weight
# hard. A historical mural does not want "church today" reshoots, road signs, etc.
MODERN_MARKERS = r"today|road sign|memorial|statue|balingit|caldwell dyson|img_\d|" \
                 r"work and dress uniform|badge|rocks\b|looking (south|west)"


def load_records():
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    return data["records"]


def text_of(rec):
    st = rec.get("search_terms") or []
    st = st if isinstance(st, str) else " ".join(st)
    return (rec.get("title", "") + " " + st + " " + rec.get("caption", "")).lower()


def long_edge_in(rec, ppi="150"):
    try:
        p = rec["print_viability"]["ppi"][ppi]
        return max(p["width_inches"], p["height_inches"])
    except Exception:
        return 0.0


def themes_hit(text):
    return {name for name, pat in THEMES.items() if re.search(pat, text)}


def era_weight(year):
    """Reward Kelly's founding-era center of gravity; allow later with decay."""
    if year is None:
        return 0.4
    if year <= 1935:
        return 1.0
    if year <= 1960:
        return 0.6
    if year <= 1990:
        return 0.3
    return 0.05


def learn_theme_weights(curated):
    """Theme weight = share of Kelly's 17 that touch that theme (min floor 0.2)."""
    counts = {name: 0 for name in THEMES}
    for r in curated:
        for t in themes_hit(text_of(r)):
            counts[t] += 1
    n = max(1, len(curated))
    return {name: max(0.2, counts[name] / n) for name in THEMES}, counts


def learn_subject_families(curated):
    """Which themes Kelly explicitly chose -> printable frames of them earn a bonus."""
    fams = set()
    for r in curated:
        fams |= themes_hit(text_of(r))
    return fams


def main():
    recs = load_records()
    curated = [r for r in recs if r.get("curated")]
    theme_w, theme_counts = learn_theme_weights(curated)
    kelly_families = learn_subject_families(curated)

    prod = [r for r in recs if long_edge_in(r) >= PRINT_BAR_IN and not r.get("curated")]

    scored = []
    for r in prod:
        text = text_of(r)
        year = (r.get("date") or {}).get("start")
        hits = themes_hit(text)
        theme_score = sum(theme_w[t] for t in hits)
        era = era_weight(year)
        modern = bool(re.search(MODERN_MARKERS, text)) and (year is None or year > 1990)
        modern_pen = 0.15 if modern else 1.0
        identity_bonus = 1.0 + (0.5 if hits & kelly_families else 0.0)
        # Confidence in the date we would print under the photo.
        conf = (r.get("date") or {}).get("confidence", "low")
        conf_w = {"confirmed": 1.0, "high": 0.9, "medium": 0.75, "low": 0.6}.get(conf, 0.6)

        score = theme_score * era * modern_pen * identity_bonus * conf_w
        scored.append({
            "id": r["id"],
            "title": r["title"],
            "year": (r.get("date") or {}).get("display"),
            "year_start": year,
            "date_confidence": conf,
            "long_edge_in_150": round(long_edge_in(r), 1),
            "themes": sorted(hits),
            "modern_only": modern,
            "score": round(score, 3),
            "attribution": r.get("attribution"),
            "attribution_confidence": r.get("attribution_confidence"),
        })

    scored.sort(key=lambda x: (-x["score"], x["year_start"] or 9999))

    core = [s for s in scored if s["score"] > 0 and not s["modern_only"]]

    OUT.write_text(json.dumps({
        "generated_from": "data/catalog.json",
        "print_bar_inches_at_150ppi": PRINT_BAR_IN,
        "kelly_theme_counts": theme_counts,
        "kelly_theme_weights": {k: round(v, 3) for k, v in theme_w.items()},
        "kelly_subject_families": sorted(kelly_families),
        "production_grade_pool": len(prod),
        "shortlist": core,
        "all_scored": scored,
    }, indent=2), encoding="utf-8")

    print(f"Kelly theme counts (of 17): {theme_counts}")
    print(f"Production-grade pool (>= {PRINT_BAR_IN:.0f}in @150, non-curated): {len(prod)}")
    print(f"Taste-match core (historic + on-theme): {len(core)}\n")
    print(f"{'score':>6}  {'year':<10} {'in':>4} {'conf':<8} themes / title")
    print("-" * 92)
    for s in core:
        print(f"{s['score']:>6.2f}  {str(s['year'])[:10]:<10} {s['long_edge_in_150']:>4.0f} "
              f"{s['date_confidence']:<8} {','.join(t.split('_')[0] for t in s['themes']):<28} "
              f"{s['title'][:34]}")
    print(f"\nWrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
