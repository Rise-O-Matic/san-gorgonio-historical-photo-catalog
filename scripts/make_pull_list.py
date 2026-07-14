"""Generate a printable storage pull-list for the mural re-acquisition targets.

Kelly reports many original photos sit in an unindexed Library storage area. This
builds a one-card-per-target sheet — the low-res image (to match by eye) + date +
caption + keywords + checkboxes — so someone in that room can recognize the
physical original for each of the 9 unprintable picks.

Output: data/research-assets/pull-list.html  (open in a browser, print to PDF).
Reads only data/catalog.json and the site thumbnails. Self-contained: images are
embedded as data URIs so the file prints anywhere.
"""
import base64
import json
import mimetypes
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data" / "catalog.json"
SITE = ROOT / "site"
OUT = ROOT / "data" / "research-assets" / "pull-list.html"

# The 9 no-stand-in targets, matched by a distinctive title fragment.
TARGET_FRAGMENTS = [
    "Ceremonial Big House Morongo",
    "Weaver",
    "1860S Stagecoach",
    "Beaumont Train Depot Calisphere",
    "Post Office",
    "Traditional House On Morongo",
    "Morongo Band",
    "Expansion Mansard",
    "Beaumont Developments",
]


def data_uri(rel):
    p = SITE / rel
    if not p.exists():
        return ""
    mime = mimetypes.guess_type(str(p))[0] or "image/jpeg"
    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def keywords(rec):
    st = rec.get("search_terms") or []
    st = st if isinstance(st, list) else str(st).split()
    stop = {"the", "and", "of", "in", "at", "on", "a", "s", "from", "to", "for"}
    words = [w for w in st if w.lower() not in stop and len(w) > 1]
    return ", ".join(dict.fromkeys(words))[:120]


def main():
    recs = [r for r in json.loads(CATALOG.read_text(encoding="utf-8"))["records"]
            if r.get("curated")]

    cards = []
    seen = set()
    for frag in TARGET_FRAGMENTS:
        rec = next((r for r in recs if frag.lower() in r["title"].lower()
                    and r["id"] not in seen), None)
        if not rec:
            continue
        seen.add(rec["id"])
        img = data_uri(rec.get("thumbnail", ""))
        date = (rec.get("date") or {}).get("display", "?")
        cap = rec.get("caption", "")
        attr = rec.get("attribution", "Unknown")
        cards.append(f"""
      <div class="card">
        <div class="imgwrap">{'<img src="'+img+'">' if img else '<div class=noimg>no preview</div>'}</div>
        <div class="meta">
          <div class="date">{date}</div>
          <div class="title">{rec['title']}</div>
          <div class="cap">{cap}</div>
          <div class="kw"><b>Look for:</b> {keywords(rec)}</div>
          <div class="attr"><b>Known source:</b> {attr}</div>
          <div class="checks">
            <label>&#9744; Found in storage</label>
            <label>&#9744; Box / location: ______________</label>
            <label>&#9744; Format: print / neg / album</label>
            <label>&#9744; Scanned</label>
          </div>
        </div>
      </div>""")

    html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Mural re-acquisition pull-list</title>
<style>
  body{{font:13px/1.4 Georgia,serif;margin:24px;color:#111}}
  h1{{font-size:19px;margin:0 0 2px}}
  .sub{{color:#555;margin:0 0 16px}}
  .card{{display:flex;gap:14px;border:1px solid #bbb;border-radius:6px;
        padding:10px;margin-bottom:12px;page-break-inside:avoid}}
  .imgwrap{{flex:0 0 150px;height:150px;display:flex;align-items:center;
        justify-content:center;background:#f4f4f4;border:1px solid #ddd}}
  .imgwrap img{{max-width:100%;max-height:100%}}
  .noimg{{color:#999;font-size:11px}}
  .meta{{flex:1}}
  .date{{font-weight:bold;font-size:15px}}
  .title{{font-size:14px;margin:1px 0 4px}}
  .cap{{color:#333;margin-bottom:4px}}
  .kw,.attr{{font-size:12px;color:#444;margin-bottom:3px}}
  .checks{{margin-top:6px;display:flex;flex-wrap:wrap;gap:4px 16px;font-size:12px}}
  @media print{{body{{margin:10mm}}}}
</style></head><body>
<h1>Timeline mural &mdash; storage pull-list</h1>
<p class="sub">9 priority originals with no printable version in the catalog.
Match by the image and date; note where each is found. Native items (Morongo)
also require Malki Museum / Tribe consultation before use.</p>
{''.join(cards)}
</body></html>"""

    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} ({len(cards)} cards). "
          f"Open in a browser and print to PDF.")


if __name__ == "__main__":
    main()
