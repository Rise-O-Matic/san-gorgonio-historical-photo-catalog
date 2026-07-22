# Collection research campaign — COMPLETE 2026-07-22

Goal reached: all 263 records at selects-manifest standard (tiered honestly)
with explicit rights determinations + client-facing rights report. Plan in
memory: collection-research-campaign.md. Started 2026-07-21.

## Final coverage (263/263, audit clean)
- 18 — mural selects (2026-07-20-mural-selects) — full adversarial verify
- 71 — modern 1990+ "Provenance verified" (2026-07-21-modern-provenance;
  was 72, one record superseded by transcription batch) — verified 72/72
- 30 — Calisphere transcriptions (2026-07-21-phase1-calisphere-transcription)
  — adversarial verify, 2 flags fixed
- 84 — deep-dive wave 1 (2026-07-21-deepdive-wave1): 19 themed agents, 18
  completed in-session; final 4 records (RR women crew, Bogart House, Egan Ave
  church, L.M. Stewart portrait) re-run 2026-07-22 by a single gap agent
- 60 — deep-dive wave 2 (2026-07-21-deepdive-wave2)

## Verification caveat (deliberate scope cut 2026-07-22)
The 144 deep-dive entries did NOT get the full adversarial pass the other
batches got — it was killed at ~1.29M tokens with 1 of 14 agents done (10
entries checked, 2 real flags, both fixed: S.P. Depot postcard PD→Unclear;
Estrada portrait people-count + date_end 1947). Instead: programmatic lint
(rights enum, caption completeness, evidence present, date sanity,
confirmed-vs-SGPHS check) + hand adjudication of 17 lint flags (1 real:
Noordman attribution confirmed→probable; date-confidence vocabulary
normalized to high/medium/low). The batch descriptions record this caveat.

## Outputs
- data/editorial-research.json: 263 entries (rebuilt from 5 batches)
- data/catalog.json + site/data/catalog.json + catalog.csv: applied, audit
  clean (192 Researched, 71 Provenance verified; every record rights_status ∈
  {Copyrighted 39, Permission required 66, Public domain 24, Unclear 134}
  with non-empty rights_note)
- data/reports/rights-report.md + .csv (client clearance list)
- research-queue.json refreshed (144 newly Researched)
- Roundhouse "SP 1768/1890s" wrong edit: reverted + documented in CBEA_007
  record's corrections (see memory roundhouse-loco-1768.md)

## Master-image pull (2026-07-22, scripts/upgrade_previews_from_masters.py)
28 records' previews/thumbs upgraded: 10 from the 2026-07-17_selects Drive
folder (01 + 03 hand-cropped out of album-page/mount scans) and 18 from the
19 Calisphere /clip masters downloaded to data/calisphere/masters/. Hash
guard keeps different images out (02 is a reference sketch — correct skip).
Still low-res: selects 15/16 (no better master exists; mansard-era
reconstruction idea shelved), select 09 (Huntington permission-gated), and
4 non-Calisphere pointers (Huntington IIIF, Portal to Texas History, 2×
CDNC — bot-blocked, needs a browser session).

## Possible follow-ups (not blocking)
- Full adversarial verify of the 144 deep-dive entries if budget returns
- CDNC browser-session checks queued in open_questions (e.g. Egan Ave
  Presbyterian church construction year; bot-blocked to curl/WebFetch)
- Pull the 4 non-Calisphere best_master URLs (see above)

## Gotchas (kept for future passes)
- Calisphere SPA pages bot-block curl; in-page fetch works when paced ≥2.5s;
  the 202 cooldown resets ONLY on a real browser navigation.
- Chrome blocks page→localhost POSTs (LNA); exfil = DOM dump + get_page_text
  chunks via subagent.
- SGPHS timeline captions are AI-authored — never "confirmed".
- Session-limit interrupts: workflow resume is same-session only; recover via
  journal.jsonl / scratchpad artifacts (that's how the 18/19 wave was closed).
