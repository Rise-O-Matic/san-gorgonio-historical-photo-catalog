#!/usr/bin/env python3
"""Generate the client-facing rights report from data/catalog.json.

Outputs data/reports/rights-report.md (readable summary, grouped by status and
holder, with contacts and next actions) and rights-report.csv (one row per
record). The report exists so the client can clear everything under copyright
or permission-gates before mural/print use.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
REPORTS = DATA / "reports"

# Contact directory for holders that appear in rights notes. Extend as new
# holders enter the catalog.
CONTACTS = {
    "Beaumont Library District": "Beaumont Library District, 125 E. 8th St, Beaumont CA 92223 · (951) 845-1357 · beaumontlibrary.org",
    "Banning Library District": "Banning Library District, 21 W. Nicolet St, Banning CA 92220 · (951) 849-3192 · banninglibrarydistrict.org",
    "San Gorgonio Pass Historical Society": "San Gorgonio Pass Historical Society (SGPHS), Banning CA · sgphs.org",
    "Huntington Library": "Huntington Library, Art Museum, and Botanical Gardens — Reproductions: hdl.huntington.org / permissions@huntington.org",
    "Laura May Stewart Trust": "Laura May Stewart Trust (contact via the Calisphere record's noted trustee, Marilyn Vonderheide, through Beaumont Library District)",
    "Google": "Google LLC — Geo Guidelines: about.google/brand-resource-center/products-and-services/geo-guidelines/",
    "Record-Gazette": "Record-Gazette, Banning CA · recordgazette.net",
    "Estrada family": "Estrada family (collection donors) — via Beaumont Library District",
    "Pomona Public Library": "Pomona Public Library Special Collections (Frasher Foto archive) · pomonalibrary.org",
    "Arizona Historical Society": "Arizona Historical Society · ahsreference@azhs.gov",
    "Sharlot Hall Museum": "Sharlot Hall Museum, Prescott AZ · orderdesk@sharlot.org",
    "NASA": "NASA (public domain; credit required by convention)",
    "Malki Museum": "Malki Museum, Morongo Reservation, Banning CA · malkimuseum.org",
    "Pat Murkland": "Pat Murkland (photographer) — contact via SGPHS/BLD",
}


def contact_for(note: str) -> str:
    hits = [c for holder, c in CONTACTS.items() if holder.lower() in (note or "").lower()]
    return " | ".join(dict.fromkeys(hits))


def main() -> None:
    cat = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
    records = cat["records"]
    REPORTS.mkdir(parents=True, exist_ok=True)

    by_status: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_status[r.get("rights_status") or "Unclear"].append(r)

    rows = []
    for r in records:
        rows.append({
            "id": r["id"], "title": r["title"],
            "date_start": r["date"]["start"], "date_end": r["date"]["end"],
            "rights_status": r.get("rights_status", ""),
            "rights_note": r.get("rights_note", ""),
            "attribution": r.get("attribution", ""),
            "research_status": r.get("research_status", ""),
            "curated": r.get("curated", False),
            "contact": contact_for(r.get("rights_note", "")),
        })
    with (REPORTS / "rights-report.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    lines = [
        "# Rights report — San Gorgonio Pass historical photo catalog",
        "",
        f"Generated {date.today().isoformat()} from data/catalog.json "
        f"({len(records)} records). Statuses: "
        + ", ".join(f"{s}: {len(v)}" for s, v in sorted(by_status.items())) + ".",
        "",
        "Statuses mean: **Copyrighted** — a named holder's permission is legally required "
        "before print use. **Permission required** — the holding institution controls "
        "reproduction (copyright may or may not persist). **Public domain** — free to use "
        "(rationale per record). **Unclear** — determination pending; each record carries "
        "a concrete next action.",
        "",
    ]

    def group_by_holder(rs: list[dict]) -> dict[str, list[dict]]:
        g = defaultdict(list)
        for r in rs:
            note = r.get("rights_note") or ""
            holder = next((h for h in CONTACTS if h.lower() in note.lower()), None)
            g[holder or "(other / see notes)"].append(r)
        return g

    for status in ("Copyrighted", "Permission required", "Unclear", "Public domain"):
        rs = by_status.get(status, [])
        if not rs:
            continue
        lines.append(f"## {status} ({len(rs)})")
        lines.append("")
        if status in ("Copyrighted", "Permission required"):
            for holder, hrs in sorted(group_by_holder(rs).items(), key=lambda x: -len(x[1])):
                contact = CONTACTS.get(holder, "")
                lines.append(f"### {holder} — {len(hrs)} record{'s' if len(hrs) != 1 else ''}")
                if contact:
                    lines.append(f"*Contact:* {contact}")
                lines.append("")
                for r in sorted(hrs, key=lambda r: (not r.get('curated'), r['title'].lower())):
                    star = " ⭐(curated)" if r.get("curated") else ""
                    lines.append(f"- **{r['title']}**{star} ({r['id']}) — {r.get('rights_note','')}")
                lines.append("")
        elif status == "Unclear":
            for r in sorted(rs, key=lambda r: (not r.get('curated'), r['title'].lower())):
                star = " ⭐(curated)" if r.get("curated") else ""
                lines.append(f"- **{r['title']}**{star} ({r['id']}) — {r.get('rights_note','') or 'No note yet.'}")
            lines.append("")
        else:  # Public domain
            for r in sorted(rs, key=lambda r: r['title'].lower()):
                lines.append(f"- **{r['title']}** ({r['id']}) — {r.get('rights_note','')}")
            lines.append("")

    (REPORTS / "rights-report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"rights-report.md + .csv written to {REPORTS.relative_to(REPO)} "
          f"({len(records)} records; "
          + ", ".join(f"{s}: {len(v)}" for s, v in sorted(by_status.items())) + ")")


if __name__ == "__main__":
    main()
