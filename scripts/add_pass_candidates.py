"""Add externally-sourced San Gorgonio Pass research candidates to the catalog.

These are historically relevant photographs found on the open internet (Calisphere:
Banning Library District Local History Collection; Pomona Public Library Frasher Foto
Collection; USC Digital Library / California Historical Society) that are NOT represented
in the current, Beaumont-town-centric image set. They fill real geographic and thematic
gaps: the town of Banning, Cabazon, the Colorado River Aqueduct, the Gilman Ranch
stage station, and Native leaders/artisans of the Pass (Serrano/Cahuilla).

Each is added as a research candidate kept separate from the masters (never silently
promoted). They carry no local record_id because they have no counterpart in the set.
Source of truth is config/catalog.config.json -> research_candidates, which the pipeline
re-emits to data/candidate-reviews.json and site/data/candidate-reviews.json on every run.
Run this to insert them and regenerate the candidate-review files without a full rebuild.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "catalog.config.json"
RETRIEVAL = "2026-07-10"

BANNING_RIGHTS = (
    "Copyright status unknown (Banning Library District Local History Collection via "
    "Calisphere). Some materials may be protected by U.S. copyright, gift/purchase terms, "
    "donor restrictions, or privacy/publicity rights; responsibility for any use rests "
    "with the user."
)


def banning(cid, ark, title, caption, dims, cban, date_display, place="Banning (Calif.)",
            confidence="high", notes=""):
    return {
        "id": cid,
        "record_id": "",
        "institution": "Banning Library District",
        "source_page": f"https://calisphere.org/item/ark:/13030/{ark}/",
        "asset_url": f"http://ark.cdlib.org/ark:/13030/{ark}",
        "retrieval_date": RETRIEVAL,
        "caption": caption,
        "dimensions": dims,
        "asset_hash": "",
        "match_classification": "new to collection",
        "match_confidence": confidence,
        "rights_status": "Unclear",
        "rights_statement": BANNING_RIGHTS,
        "validation_notes": (
            f"New subject not represented in the current catalog. {notes} "
            f"Banning Library District Local History Collection, id {cban}; "
            f"place: {place}; date: {date_display}. Title: \"{title}\"."
        ).strip(),
        "review_status": "pending",
    }


NEW = [
    # --- Town of Banning (absent from the catalog) ---
    banning(
        "candidate_cali_banning_sp_depot", "c8c53hwn",
        "The Banning Southern Pacific Railroad Depot",
        "The Banning Southern Pacific Railroad Depot: photographic postcard of the depot "
        "front and railroad tracks, 'Southern Pacific Depot early days,' circa 1910.",
        "Sepia-tone photographic postcard; 8.5 x 13.6 cm", "CBAN_003", "circa 1910",
        notes="Southern Pacific through the San Gorgonio Pass; complements the Beaumont "
              "depot records already in the set.",
    ),
    banning(
        "candidate_cali_banning_hotel", "c8v69k8c",
        "\"The Banning\" hotel (Bryant House / San Gorgonio Inn)",
        "'The Banning' hotel, formerly the 'Bryant House' and later the 'San Gorgonio Inn,' "
        "Banning, circa 1890.",
        "Sepia-tone photographic reprint; 10.16 x 15 cm", "CBAN_363", "circa 1890",
        notes="Landmark Banning hostelry that survives as the San Gorgonio Inn.",
    ),
    banning(
        "candidate_cali_banning_union_ice", "c8c82b11",
        "Union Ice Company delivery wagon in Banning",
        "Union Ice Company delivery wagon driven by George Bailiff, Banning, early 1900s. "
        "The town's ice plant began in an adobe on San Gorgonio near Livingston.",
        "Sepia-tone photographic postcard; 8.5 x 13.97 cm", "CBAN_349", "early 1900s",
        notes="Everyday commerce in early Banning.",
    ),
    banning(
        "candidate_cali_banning_fruit_drying", "c8cn71xn",
        "Banning fruit drying yard",
        "E. L. Robertson's fruit drying yard on 4th Street, Banning, with workers stacking "
        "prune-drying trays, circa 1910.",
        "Sepia-tone photograph; 11.43 x 17.1 cm", "CBAN_052", "circa 1910",
        notes="Pass-area deciduous-fruit agriculture (prunes/apricots/almonds).",
    ),
    # --- Cabazon (absent) ---
    banning(
        "candidate_cali_cabazon_sp_depot", "c83b60vc",
        "Cabazon Southern Pacific Railroad Depot in 1930",
        "Southern Pacific Railroad depot at Cabazon, September 1930, with members of the "
        "Bailiff family posed in front.",
        "Sepia-tone photograph; 7.62 x 12.7 cm", "CBAN_357", "1930-09",
        place="Cabazon (Calif.)",
        notes="Extends railroad coverage east through the Pass to Cabazon.",
    ),
    # --- Colorado River Aqueduct (major 1930s regional engineering; absent) ---
    banning(
        "candidate_cali_aqueduct_tunnel_cabazon", "c8cz37w8",
        "Inside the Colorado River Aqueduct tunnel during construction in Cabazon",
        "Inside the Colorado River Aqueduct tunnel under construction through San Jacinto "
        "Mountain at Cabazon, 1936. The 13-mile section took about five years and created "
        "thousands of post-Depression jobs in Banning.",
        "Sepia-tone photograph; 6.35 x 10 cm", "CBAN_226", "1936",
        notes="The Metropolitan Water District aqueduct that reshaped the Pass economy.",
    ),
    banning(
        "candidate_cali_aqueduct_sanjacinto_tunnel", "c8d50k00",
        "West approach to the San Jacinto tunnel (Colorado River Aqueduct)",
        "West approach to the San Jacinto tunnel of the Colorado River Aqueduct near "
        "Banning: men, buildings, and equipment, circa 1930s.",
        "Sepia-tone photograph; 8.89 x 14.5 cm", "CBAN_149", "circa 1930s",
        notes="Companion to the Cabazon tunnel-interior view.",
    ),
    # --- Gilman Ranch (historic Banning stage-stop ranch, now a county museum; absent) ---
    banning(
        "candidate_cali_gilman_ranch_house", "c84f1nrb",
        "The Gilman Ranch House in Banning",
        "The Gilman Ranch House (built 1897), Banning, with two women and a girl on the "
        "porch, circa 1900. The site is now the Gilman Historic Ranch and Wagon Museum.",
        "Sepia-tone photograph; 19.05 x 24.7 cm", "CBAN_179", "circa 1900",
        notes="Anchors early ranching/stagecoach history of the Pass.",
    ),
    banning(
        "candidate_cali_gilman_stage_station", "c8b27w15",
        "Pope adobe 'old stage station' on the Gilman Ranch",
        "The Pope adobe house, the 'old stage station,' on the Gilman Ranch, Banning; "
        "Ethel Gilman by the tree and Molly Rogers by the horse, circa 1890s.",
        "Sepia-tone photographic reprint; 12.7 x 15 cm", "CBAN_335", "circa 1890s",
        notes="Bradshaw Trail / overland stage era at the eastern Pass.",
    ),
    # --- Native peoples of the Pass (deepens beyond the catalog's Morongo Big House) ---
    banning(
        "candidate_cali_captain_john_morongo", "c8d798dr",
        "Portrait photograph of Captain John Morongo",
        "Portrait of Captain John Morongo, the Serrano leader instrumental in establishing "
        "San Gorgonio Pass settlements; the Morongo Indian Reservation is named for him, "
        "circa 1890.",
        "Black-and-white photographic print; 8.89 x 12.70 cm", "CBAN_120", "circa 1890",
        place="Morongo Indian Reservation (Calif.)",
        notes="Named individual behind the reservation the catalog already depicts.",
    ),
    banning(
        "candidate_cali_fig_tree_john", "c8k9388x",
        "Fig Tree John, Cahuilla tribal leader",
        "Fig Tree John (recorded as Captain Juanito Razon Agua Dulce Tuba), a Cahuilla "
        "tribal leader and familiar figure in Banning; died April 1927. Early 1900s.",
        "Sepia-tone photograph; 8.89 x 11.43 cm", "CBAN_382", "early 1900s",
        notes="Regionally famous Cahuilla figure of the desert edge of the Pass.",
    ),
    banning(
        "candidate_cali_morongo_basket_maker", "c8k07299",
        "Basket maker on the Morongo Indian Reservation",
        "Unidentified Cahuilla basket maker with a basket on the Morongo Indian Reservation "
        "bordering Banning, circa 1900.",
        "Sepia-tone slide", "CBAN_112", "circa 1900",
        place="Morongo Indian Reservation (Calif.)",
        notes="Documents Cahuilla basketry, absent from the current set.",
    ),
    # --- Beaumont subjects new to the catalog ---
    banning(
        "candidate_cali_beaumont_aerial_99_60", "c8rf5vqg",
        "Late-1950s aerial of downtown Beaumont at the 99/60 junction",
        "Aerial photographic postcard of downtown Beaumont before the I-10 Freeway, showing "
        "the junction of Highways 60 and 99, circa 1960.",
        "Sepia-tone photographic postcard; 8.5 x 13.97 cm", "CBAN_325", "circa 1960",
        place="Beaumont (Calif.)",
        notes="Mid-century townscape/highway view of Beaumont not otherwise in the set.",
    ),
    {
        "id": "candidate_cali_sangorgonio_catholic_church",
        "record_id": "",
        "institution": "Banning Library District",
        "source_page": "https://calisphere.org/item/ark:/13030/c889157p/",
        "asset_url": "http://ark.cdlib.org/ark:/13030/c889157p",
        "retrieval_date": RETRIEVAL,
        "caption": (
            "The newly built San Gorgonio Catholic Church, erected 1908 at 7th and Palm "
            "(southwest corner), Beaumont — the second Catholic church built in Beaumont."
        ),
        "dimensions": "Not verified (item page returned HTTP 403 at retrieval)",
        "asset_hash": "",
        "match_classification": "new to collection",
        "match_confidence": "medium",
        "rights_status": "Unclear",
        "rights_statement": BANNING_RIGHTS,
        "validation_notes": (
            "New subject. Metadata drawn from the Calisphere search-result preview; the full "
            "item page returned HTTP 403 on 2026-07-10, so date/format/dimensions should be "
            "reconfirmed on next access. Banning Library District Local History Collection; "
            "place: Beaumont (Calif.); date: 1908."
        ),
        "review_status": "pending",
    },
    # --- Pass geography from other open collections ---
    {
        "id": "candidate_frasher_pass_whitewater",
        "record_id": "",
        "institution": "Pomona Public Library (Frasher Foto Postcard Collection)",
        "source_page": "https://calisphere.org/item/ark:/13030/kt7g5020cv/",
        "asset_url": "http://ark.cdlib.org/ark:/13030/kt7g5020cv",
        "retrieval_date": RETRIEVAL,
        "caption": (
            "San Gorgonio Pass seen from the hills above Whitewater. Real-photo postcard by "
            "Burton Frasher Sr., 1947."
        ),
        "dimensions": "13 x 7.5 cm",
        "asset_hash": "",
        "match_classification": "new to collection",
        "match_confidence": "high",
        "rights_status": "Permission Required",
        "rights_statement": (
            "Pomona Public Library asserts no ownership of original copyrights; images are "
            "intended for personal or research use only. Other uses may be subject to "
            "additional restrictions; users are responsible for determining rights and "
            "obtaining permissions. Frasher Foto Postcard Collection, F6945."
        ),
        "validation_notes": (
            "New subject: a wide view of the Pass from its eastern (desert) end near "
            "Whitewater — a geographic vantage absent from the town-centric catalog. "
            "Contributing institution: Pomona Public Library; creator Burton Frasher Sr. "
            "(1888–1955); date 1947."
        ),
        "review_status": "pending",
    },
    {
        "id": "candidate_usc_chs_sangorgonio_summit_waterfall",
        "record_id": "",
        "institution": "California Historical Society Collection at Stanford / USC Digital Library",
        "source_page": "https://calisphere.org/item/dba6aef0b1f6e384e2c910ee5d279e4d/",
        "asset_url": "http://thumbnails.digitallibrary.usc.edu/CHS-43008.jpg",
        "retrieval_date": RETRIEVAL,
        "caption": (
            "Women beside a waterfall on the trail to the summit of San Gorgonio (Mount San "
            "Gorgonio), Riverside County, 1900–1915."
        ),
        "dimensions": "Photoprint, b&w; 18 x 25 cm",
        "asset_hash": "",
        "match_classification": "new to collection",
        "match_confidence": "high",
        "rights_status": "Public Domain",
        "rights_statement": (
            "Public Domain, released under CC BY 3.0 "
            "(http://creativecommons.org/licenses/by/3.0/). Credit both 'University of "
            "Southern California. Libraries' and 'California Historical Society.' Digitally "
            "reproduced by the USC Digital Library. DOI: 10.25549/chs-m2795."
        ),
        "validation_notes": (
            "New subject AND the only rights-clear item in this batch: CC BY / public domain, "
            "so it could be downloaded and added as an actual catalog record with attribution "
            "rather than kept as a pending candidate. Depicts the namesake San Gorgonio summit "
            "trail. USC/CHS identifier chs-m2795; thumbnail at "
            "http://thumbnails.digitallibrary.usc.edu/CHS-43008.jpg."
        ),
        "review_status": "pending",
    },
]


def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    existing = config.setdefault("research_candidates", [])
    have = {c.get("id") for c in existing}
    added = 0
    for cand in NEW:
        if cand["id"] in have:
            # refresh in place so re-runs stay idempotent
            for i, c in enumerate(existing):
                if c.get("id") == cand["id"]:
                    existing[i] = cand
                    break
        else:
            existing.append(cand)
            added += 1
    CONFIG.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    reviews = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "candidates": config["research_candidates"],
    }
    for path in (ROOT / "data" / "candidate-reviews.json",
                 ROOT / "site" / "data" / "candidate-reviews.json"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(reviews, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Added {added} new candidate(s); {len(config['research_candidates'])} total.")


if __name__ == "__main__":
    main()
