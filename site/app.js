'use strict';

/* Beaumont Timeline Builder — drag photographs from the chronological
   collection tray onto the timeline canvas, arrange, approve, export. */

const KEY = 'bld-timeline-builder-v2';
const BLANK = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const esc = value => String(value ?? '').replace(/[&<>'"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[c]));

let catalog = null, records = [], byId = new Map(), chrono = [];
let working = [], approved = [], approvedAt = null;
let trayRecords = [];
const loadedImgs = new Set();
let io = null;

boot();

async function boot() {
  try {
    const res = await fetch('data/catalog.json', { cache: 'no-store' });
    if (!res.ok) throw new Error(`Catalog request failed (${res.status})`);
    catalog = await res.json();
    records = catalog.records;
    byId = new Map(records.map(r => [r.id, r]));
    chrono = records.slice().sort(chronoCompare);
    loadState();
    bindEvents();
    applyFilters();
    renderTimeline();
    $('#loadVeil').classList.add('done');
    document.fonts?.ready.then(layoutScrubber);
  } catch (err) {
    $('#loadVeil').innerHTML = `<p>The catalog could not be loaded.<br><small>${esc(err.message)} — serve the site over HTTP after running the pipeline.</small></p>`;
  }
}

/* ————— State ————— */

function chronoCompare(a, b) {
  const ya = a.date?.start ?? 9999, yb = b.date?.start ?? 9999;
  return ya - yb || (a.date?.end ?? ya) - (b.date?.end ?? yb) || a.title.localeCompare(b.title);
}

function seedApproved() {
  /* The client's select set and order live in research.select_position
     (2026-07-17 selects); the curated flag tracks folder membership and lags. */
  const selects = records.filter(r => Number.isFinite(r.research?.select_position));
  if (selects.length) {
    return selects
      .sort((a, b) => a.research.select_position - b.research.select_position)
      .map(r => r.id);
  }
  return records.filter(r => r.curated).sort(chronoCompare).map(r => r.id);
}

function loadState() {
  let saved = null;
  try { saved = JSON.parse(localStorage.getItem(KEY)); } catch { /* corrupted state falls back to seed */ }
  const valid = ids => Array.isArray(ids) ? ids.filter(id => byId.has(id)) : null;
  approved = valid(saved?.approved) ?? seedApproved();
  working = valid(saved?.working) ?? approved.slice();
  approvedAt = saved?.approvedAt ?? null;
}

function persist() {
  localStorage.setItem(KEY, JSON.stringify({ working, approved, approvedAt }));
}

const startYear = r => r.date?.start ?? null;
const yearLabel = r => startYear(r) ? String(startYear(r)) : 'Undated';
const displayDate = r => r.date?.display || yearLabel(r);
const shortDate = r => (r.date?.display && r.date.display.length <= 15) ? r.date.display : yearLabel(r);

/* Previews/thumbs are regenerated under a stable file id, so an image swap or
   upgrade reuses the same URL and browsers serve the stale bytes. Keying a
   cache-bust query to the record's pixel dimensions refetches whenever the
   image actually changes (dims move on every swap/upscale). */
const assetVer = r => r.original_pixels ? `${r.original_pixels.width}x${r.original_pixels.height}` : '1';
const thumbSrc = r => `${encodeURI(r.thumbnail)}?v=${assetVer(r)}`;
const previewSrc = r => `${encodeURI(r.preview)}?v=${assetVer(r)}`;

/* ————— Events ————— */

function bindEvents() {
  let searchTimer = null;
  $('#searchInput').addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(applyFilters, 140);
  });
  ['viabilityFilter', 'rightsFilter'].forEach(id => $(`#${id}`).addEventListener('change', applyFilters));
  $('#hidePlaced').addEventListener('change', applyFilters);

  $('#sortBtn').addEventListener('click', () => {
    working.sort((a, b) => chronoCompare(byId.get(a), byId.get(b)));
    persist();
    flipCards($('#canvasRow'), renderTimeline);
  });
  $('#clearBtn').addEventListener('click', () => {
    if (!working.length) return;
    if (confirm('Remove every photograph from the timeline?')) {
      working = []; persist(); renderTimeline(); applyFilters();
    }
  });
  $('#approveBtn').addEventListener('click', () => {
    approved = working.slice();
    approvedAt = new Date().toISOString();
    persist(); updateStats();
    flashButton($('#approveBtn'), 'Approved ✓');
  });
  $('#revertBtn').addEventListener('click', () => {
    if (confirm('Discard changes and restore the last approved timeline?')) {
      working = approved.slice();
      persist();
      flipCards($('#canvasRow'), renderTimeline);
      applyFilters();
    }
  });
  $('#exportBtn').addEventListener('click', exportDoc);

  $('#canvasRow').addEventListener('click', event => {
    const remove = event.target.closest('[data-remove]');
    if (remove) { removeFromTimeline(remove.closest('.m-card').dataset.id); return; }
    const card = event.target.closest('.m-card');
    if (card) quickView(byId.get(card.dataset.id));
  });

  $('#trayRow').addEventListener('click', event => {
    const add = event.target.closest('[data-add]');
    const card = event.target.closest('.t-card');
    if (!card) return;
    const id = card.dataset.id;
    if (add) {
      if (working.includes(id)) removeFromTimeline(id);
      else addToTimeline(id);
      return;
    }
    quickView(byId.get(id));
  });
  $('#trayRow').addEventListener('dblclick', event => {
    const card = event.target.closest('.t-card');
    if (card && !working.includes(card.dataset.id)) addToTimeline(card.dataset.id);
  });

  // Reveal the full caption overlay only when the clamped text actually overflows
  $('#trayRow').addEventListener('mouseover', event => {
    const card = event.target.closest('.t-card');
    if (!card || card.dataset.ovChecked) return;
    card.dataset.ovChecked = '1';
    const cap = $('.t-cap', card), title = $('.t-title', card), more = $('.t-more', card);
    const clipped = el => el && el.scrollHeight > el.clientHeight + 1;
    if (more && (clipped(cap) || clipped(title))) more.classList.add('has-overflow');
  });

  $$('dialog [data-close]').forEach(btn => btn.addEventListener('click', () => btn.closest('dialog').close()));
  $('#quickView').addEventListener('click', event => { if (event.target === $('#quickView')) $('#quickView').close(); });

  bindDragAndDrop();
  bindScrubber();
  bindWheelScroll($('#canvasRow'));
  bindWheelScroll($('#trayRow'));

  let resizeTimer = null;
  addEventListener('resize', () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(layoutScrubber, 160); });
}

function flashButton(btn, text) {
  const old = btn.textContent;
  btn.textContent = text;
  setTimeout(() => { btn.textContent = old; }, 1500);
}

/* ————— Timeline mutations ————— */

function addToTimeline(id) { insertAt(id, working.length); }

function insertAt(id, index) {
  const without = working.filter(x => x !== id);
  index = Math.max(0, Math.min(index, without.length));
  without.splice(index, 0, id);
  working = without;
  persist();
  flipCards($('#canvasRow'), renderTimeline, id);
  $(`#canvasRow .m-card[data-id="${id}"]`)?.scrollIntoView({ behavior: 'smooth', inline: 'nearest', block: 'nearest' });
  applyFilters();
}

function removeFromTimeline(id) {
  working = working.filter(x => x !== id);
  persist();
  flipCards($('#canvasRow'), renderTimeline);
  applyFilters();
}

/* FLIP: measure card positions, mutate the DOM, then slide every surviving
   card from its old spot to its new one. Cards that didn't exist before —
   and the just-dropped card, which already rode in under the cursor — get
   the landing pulse instead. */
function flipCards(container, mutate, pulseId = null) {
  const before = new Map($$('.m-card', container).map(card => [card.dataset.id, card.getBoundingClientRect().left]));
  mutate();
  $$('.m-card', container).forEach(card => {
    if (card.classList.contains('drag-hidden')) return;
    const old = before.get(card.dataset.id);
    if (old == null || card.dataset.id === pulseId) {
      card.classList.add('just-dropped');
      card.addEventListener('animationend', () => card.classList.remove('just-dropped'), { once: true });
      return;
    }
    const dx = old - card.getBoundingClientRect().left;
    if (Math.abs(dx) < 1) return;
    card.style.transition = 'none';
    card.style.transform = `translateX(${dx}px)`;
    card.getBoundingClientRect(); // force reflow so the transition below animates
    card.style.transition = 'transform 260ms cubic-bezier(0.2, 0.72, 0.24, 1)';
    card.style.transform = '';
    card.addEventListener('transitionend', () => { card.style.transition = ''; }, { once: true });
  });
}

/* ————— Rendering ————— */

function applyFilters() {
  const q = $('#searchInput').value.trim().toLowerCase();
  const viability = $('#viabilityFilter').value;
  const rights = $('#rightsFilter').value;
  const hidePlaced = $('#hidePlaced').checked;
  const placed = new Set(working);
  trayRecords = chrono.filter(r => {
    if (hidePlaced && placed.has(r.id)) return false;
    if (viability && r.print_viability?.classification !== viability) return false;
    if (rights && r.rights_status !== rights) return false;
    if (q) {
      const hay = [r.title, r.caption, r.visible_text, ...(r.subjects || []), ...(r.people || []), ...(r.locations || []), ...(r.search_terms || [])].join(' ').toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
  renderTray();
}

function trayCard(r, placed) {
  return `<article class="t-card${placed ? ' placed' : ''}" draggable="true" data-id="${r.id}">
    <figure class="t-fig">
      <img src="${BLANK}" data-src="${thumbSrc(r)}" alt="${esc(r.title)}" draggable="false">
      <span class="t-year">${esc(yearLabel(r))}</span>
      ${placed ? '<span class="placed-flag">On timeline</span>' : ''}
    </figure>
    <div class="t-body">
      <h3 class="t-title">${esc(r.title)}</h3>
      <p class="t-cap">${esc(r.caption)}</p>
    </div>
    <div class="t-more"><div><p class="t-more-year">${esc(displayDate(r))}</p><p class="t-more-title">${esc(r.title)}</p><p class="t-more-cap">${esc(r.caption)}</p></div></div>
    <button class="t-add" type="button" data-add title="${placed ? 'Remove from timeline' : 'Add to end of timeline'}">${placed ? '−' : '+'}</button>
  </article>`;
}

function renderTray() {
  const row = $('#trayRow');
  const keep = row.scrollLeft;
  const placed = new Set(working);
  $('#trayCount').textContent = `${trayRecords.length} of ${records.length} photographs`;
  row.innerHTML = trayRecords.length
    ? trayRecords.map(r => trayCard(r, placed.has(r.id))).join('')
    : '<p class="tray-empty">No photographs match these filters.</p>';
  row.scrollLeft = keep;
  observeImages(row);
  layoutScrubber();
}

function muralCard(r, i) {
  return `<article class="m-card" draggable="true" data-id="${r.id}">
    <span class="m-pos">${String(i + 1).padStart(2, '0')}</span>
    <button class="m-remove" type="button" data-remove title="Remove from timeline">×</button>
    <div class="m-matte"><img src="${BLANK}" data-src="${thumbSrc(r)}" alt="${esc(r.title)}" draggable="false"></div>
    <div class="m-plate">
      <p class="m-year">${esc(shortDate(r))}</p>
      <h3 class="m-title">${esc(r.title)}</h3>
      <p class="m-cap">${esc(r.research?.description || r.caption)}</p>
    </div>
  </article>`;
}

function renderTimeline() {
  const row = $('#canvasRow');
  const keep = row.scrollLeft;
  if (!working.length) {
    row.innerHTML = `<div class="canvas-empty"><strong>An empty wall.</strong>Drag photographs up from the collection below to build the mural timeline.<br>Rearrange them at any time — everything is saved in this browser.</div>`;
  } else {
    row.innerHTML = working.map((id, i) => muralCard(byId.get(id), i)).join('');
    observeImages(row);
  }
  row.scrollLeft = keep;
  updateStats();
}

function updateStats() {
  const recs = working.map(id => byId.get(id));
  const years = recs.map(startYear).filter(Boolean);
  const span = years.length ? `${Math.min(...years)}–${Math.max(...years)}` : '';
  const n = working.length;
  $('#timelineStat').textContent = n ? `${n} photograph${n === 1 ? '' : 's'} on the timeline${span ? ` · ${span}` : ''}` : 'Timeline is empty';
  $('#canvasMeta').textContent = n
    ? `${n} placed${span ? ` · spanning ${span}` : ''} · drag to reorder · drag down to the collection to remove`
    : 'Drag photographs up from the collection to begin';
  const dirty = JSON.stringify(working) !== JSON.stringify(approved);
  $('#dirtyDot').hidden = !dirty;
  $('#revertBtn').disabled = !dirty;
  $('#approvedNote').textContent = approvedAt
    ? `Approved ${new Date(approvedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
    : 'Seeded from the client selects (2026-07-17)';
}

/* ————— Lazy loading ————— */

function observeImages(container) {
  if (!io) {
    io = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        const img = entry.target;
        io.unobserve(img);
        img.addEventListener('load', () => { img.classList.add('loaded'); loadedImgs.add(img.dataset.src); }, { once: true });
        img.src = img.dataset.src;
      }
    }, { rootMargin: '400px 1000px 400px 1000px' });
  }
  $$('img[data-src]', container).forEach(img => {
    if (loadedImgs.has(img.dataset.src)) { img.src = img.dataset.src; img.classList.add('loaded'); }
    else io.observe(img);
  });
}

/* ————— Drag & drop ————— */

let drag = null;
let slotEl = null;

function ensureSlot() {
  if (!slotEl) { slotEl = document.createElement('div'); slotEl.className = 'drop-slot'; }
  return slotEl;
}
function removeSlot() { slotEl?.remove(); }

function placeSlot(canvas, x) {
  const slot = ensureSlot();
  const cards = $$('.m-card:not(.dragging):not(.drag-hidden)', canvas);
  let target = null;
  for (const card of cards) {
    const rect = card.getBoundingClientRect();
    if (x < rect.left + rect.width / 2) { target = card; break; }
  }
  if (!slotMoved(canvas, target)) return;
  flipCards(canvas, () => {
    if (target) canvas.insertBefore(slot, target);
    else canvas.appendChild(slot);
  });
}

/* True when the slot is absent or not already sitting just before `target`
   (ignoring the collapsed dragged card), so we only re-insert on real moves. */
function slotMoved(canvas, target) {
  if (!slotEl || slotEl.parentNode !== canvas) return true;
  let sibling = slotEl.nextElementSibling;
  while (sibling && (sibling.classList.contains('dragging') || sibling.classList.contains('drag-hidden'))) sibling = sibling.nextElementSibling;
  return sibling !== target;
}

function slotIndex(canvas) {
  if (!slotEl || !slotEl.parentNode) return working.length;
  let i = 0;
  for (const child of canvas.children) {
    if (child === slotEl) return i;
    if (child.classList.contains('m-card') && !child.classList.contains('dragging') && !child.classList.contains('drag-hidden')) i++;
  }
  return i;
}

function autoScroll(el, x) {
  const rect = el.getBoundingClientRect(), edge = 90, speed = 16;
  if (x < rect.left + edge) el.scrollLeft -= speed;
  else if (x > rect.right - edge) el.scrollLeft += speed;
}

function bindDragAndDrop() {
  const canvas = $('#canvasRow');
  const trayZone = $('.tray-zone');

  document.addEventListener('dragstart', event => {
    const card = event.target.closest?.('.m-card, .t-card');
    if (!card) return;
    drag = { id: card.dataset.id, origin: card.classList.contains('m-card') ? 'timeline' : 'tray' };
    card.classList.add('dragging');
    event.dataTransfer.effectAllowed = 'move';
    try { event.dataTransfer.setData('text/plain', card.dataset.id); } catch { /* IE-era quirk guard */ }
    // Collapse the card's spot on the timeline so the row closes around it.
    // Deferred a tick: hiding the source synchronously would cancel the drag.
    setTimeout(() => {
      if (!drag) return;
      const twin = $(`#canvasRow .m-card[data-id="${drag.id}"]`);
      if (twin) flipCards(canvas, () => twin.classList.add('drag-hidden'));
    }, 0);
  });

  document.addEventListener('dragend', () => {
    $$('.dragging').forEach(el => el.classList.remove('dragging'));
    // Reopen any collapsed spot (drag cancelled or dropped elsewhere)
    if ($('.drag-hidden', canvas)) {
      flipCards(canvas, () => $$('.drag-hidden', canvas).forEach(el => el.classList.remove('drag-hidden')));
    }
    removeSlot();
    canvas.classList.remove('drop-ready');
    trayZone.classList.remove('remove-intent');
    drag = null;
  });

  canvas.addEventListener('dragover', event => {
    if (!drag) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
    canvas.classList.add('drop-ready');
    autoScroll(canvas, event.clientX);
    placeSlot(canvas, event.clientX);
  });

  canvas.addEventListener('dragleave', event => {
    if (!canvas.contains(event.relatedTarget)) {
      removeSlot();
      canvas.classList.remove('drop-ready');
    }
  });

  canvas.addEventListener('drop', event => {
    if (!drag) return;
    event.preventDefault();
    const index = slotIndex(canvas);
    removeSlot();
    canvas.classList.remove('drop-ready');
    insertAt(drag.id, index);
  });

  trayZone.addEventListener('dragover', event => {
    if (drag?.origin !== 'timeline') return;
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
    trayZone.classList.add('remove-intent');
  });

  trayZone.addEventListener('dragleave', event => {
    if (!trayZone.contains(event.relatedTarget)) trayZone.classList.remove('remove-intent');
  });

  trayZone.addEventListener('drop', event => {
    if (drag?.origin !== 'timeline') return;
    event.preventDefault();
    trayZone.classList.remove('remove-intent');
    removeFromTimeline(drag.id);
  });
}

/* ————— Scrubber ————— */

function layoutScrubber() {
  const tray = $('#trayRow'), ticks = $('#scrubTicks');
  const sw = tray.scrollWidth, cw = tray.clientWidth;
  const scrollable = sw > cw + 4;
  $('#scrubber').style.visibility = scrollable ? 'visible' : 'hidden';
  if (!scrollable) { ticks.innerHTML = ''; return; }
  const seen = new Set();
  const minGap = (44 / Math.max(ticks.clientWidth, 1)) * 100; // keep labels from colliding
  let lastPct = -Infinity;
  let html = '';
  $$('.t-card', tray).forEach(card => {
    const record = byId.get(card.dataset.id);
    const year = startYear(record);
    if (year == null) return;
    const decade = Math.floor(year / 10) * 10;
    if (seen.has(decade)) return;
    seen.add(decade);
    const pct = (card.offsetLeft / sw) * 100;
    if (pct - lastPct < minGap) return;
    lastPct = pct;
    html += `<button class="scrub-tick" type="button" style="left:${pct.toFixed(2)}%" data-left="${card.offsetLeft}">${decade}s</button>`;
  });
  ticks.innerHTML = html;
  updateHandle();
}

function updateHandle() {
  const tray = $('#trayRow'), track = $('#scrubTrack'), handle = $('#scrubHandle');
  const sw = tray.scrollWidth, cw = tray.clientWidth, max = sw - cw;
  const width = Math.max(34, track.clientWidth * (cw / sw));
  handle.style.width = `${width}px`;
  const pct = max > 0 ? tray.scrollLeft / max : 0;
  handle.style.left = `${pct * (track.clientWidth - width)}px`;
}

function bindScrubber() {
  const tray = $('#trayRow'), track = $('#scrubTrack');
  let ticking = false;
  tray.addEventListener('scroll', () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => { updateHandle(); ticking = false; });
  });
  $('#scrubTicks').addEventListener('click', event => {
    const tick = event.target.closest('.scrub-tick');
    if (tick) tray.scrollTo({ left: Number(tick.dataset.left) - 26, behavior: 'smooth' });
  });
  let scrubbing = false;
  const scrubTo = event => {
    const handle = $('#scrubHandle');
    const rect = track.getBoundingClientRect(), hw = handle.offsetWidth;
    const pct = Math.min(1, Math.max(0, (event.clientX - rect.left - hw / 2) / (rect.width - hw)));
    tray.scrollLeft = pct * (tray.scrollWidth - tray.clientWidth);
  };
  track.addEventListener('pointerdown', event => {
    scrubbing = true;
    track.setPointerCapture(event.pointerId);
    scrubTo(event);
  });
  track.addEventListener('pointermove', event => { if (scrubbing) scrubTo(event); });
  track.addEventListener('pointerup', () => { scrubbing = false; });
  track.addEventListener('pointercancel', () => { scrubbing = false; });
}

/* ————— Wheel → horizontal scroll ————— */

/* The timeline canvas and the collection tray are horizontal strips, but a
   plain mouse wheel reports vertical deltas. Translate a vertical-dominant
   wheel into horizontal scroll; real horizontal gestures (trackpads) are left
   to the browser so we never double them. */
function bindWheelScroll(el) {
  el.addEventListener('wheel', event => {
    if (el.scrollWidth <= el.clientWidth) return;                // nothing to scroll — let the page have it
    if (Math.abs(event.deltaX) > Math.abs(event.deltaY)) return; // native horizontal gesture
    if (!event.deltaY) return;
    event.preventDefault();
    const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? el.clientWidth : 1; // lines/pages → px
    el.scrollLeft += event.deltaY * unit;
  }, { passive: false });
}

/* ————— Quick view ————— */

/* Evidence links recorded by the research campaign — every record carries
   them; entries without a URL (offline sources) render as plain text. */
function sourceCitations(record) {
  return (record.research?.evidence || []).filter(e => e && (e.label || e.url));
}

function citationsBlock(record) {
  const sources = sourceCitations(record);
  if (!sources.length) return '';
  const items = sources.map(e => {
    const label = esc(e.label || e.url);
    return `<li>${e.url ? `<a href="${esc(e.url)}" target="_blank" rel="noopener">${label}</a>` : label}</li>`;
  }).join('');
  return `<details class="qv-sources"><summary>Sources &amp; citations (${sources.length})</summary><ul>${items}</ul></details>`;
}

function quickView(record) {
  const placed = working.includes(record.id);
  const research = record.research;
  $('#quickViewBody').innerHTML = `<div class="qv-grid">
    <div class="qv-photo">
      <img src="${previewSrc(record)}" alt="${esc(record.title)}" draggable="false">
      <span class="qv-zoom-hint">Scroll to zoom · drag to pan · double-click to reset</span>
      <button class="qv-zoom-reset" type="button" hidden></button>
    </div>
    <div class="qv-copy">
      <p class="qv-year">${esc(displayDate(record))}</p>
      <h3 class="qv-title">${esc(record.title)}</h3>
      <p class="qv-cap">${esc(record.caption)}</p>
      ${research?.description ? `<p class="qv-desc">${esc(research.description)}</p>` : ''}
      <p class="qv-facts">
        ${record.attribution ? `<strong>Credit</strong> ${esc(record.attribution)}<br>` : ''}
        <strong>Rights</strong> ${esc(record.rights_status || '—')}${record.rights_note ? ` — ${esc(record.rights_note)}` : ''}<br>
        ${record.caption_source ? `<strong>Caption source</strong> ${esc(record.caption_source)}<br>` : ''}
        <strong>Print</strong> ${esc(record.print_viability?.classification || '—')} · ${record.original_pixels.width.toLocaleString()} × ${record.original_pixels.height.toLocaleString()} px
      </p>
      ${citationsBlock(record)}
      <div class="qv-actions">
        <button class="btn ${placed ? 'outline' : 'brass'}" id="qvToggle" type="button">${placed ? 'Remove from timeline' : 'Add to timeline'}</button>
      </div>
    </div>
  </div>`;
  const dialog = $('#quickView');
  dialog.showModal();
  bindPhotoZoom($('.qv-photo', dialog));
  $('#qvToggle').addEventListener('click', () => {
    if (working.includes(record.id)) removeFromTimeline(record.id);
    else addToTimeline(record.id);
    dialog.close();
  });
}

/* Wheel/pinch to zoom toward the cursor, drag to pan, double-click or the
   chip to reset. State lives per open — the markup is rebuilt each view. */
function bindPhotoZoom(stage) {
  const img = $('img', stage);
  const resetChip = $('.qv-zoom-reset', stage);
  const MAX_SCALE = 8;
  let scale = 1, tx = 0, ty = 0, drag = null;

  const apply = () => {
    img.style.transform = `translate(${tx}px, ${ty}px) scale(${scale})`;
    stage.classList.toggle('zoomed', scale > 1);
    resetChip.hidden = scale <= 1;
    if (!resetChip.hidden) resetChip.textContent = `${Math.round(scale * 100)}% · Reset`;
  };

  const clampPan = () => {
    const boundX = Math.max(0, (img.offsetWidth * scale - stage.clientWidth) / 2);
    const boundY = Math.max(0, (img.offsetHeight * scale - stage.clientHeight) / 2);
    tx = Math.min(boundX, Math.max(-boundX, tx));
    ty = Math.min(boundY, Math.max(-boundY, ty));
  };

  const animate = () => {
    stage.classList.add('anim');
    img.addEventListener('transitionend', () => stage.classList.remove('anim'), { once: true });
  };

  const reset = () => { scale = 1; tx = 0; ty = 0; animate(); apply(); };

  const zoomAt = (clientX, clientY, factor) => {
    const rect = stage.getBoundingClientRect();
    const px = clientX - rect.left - rect.width / 2;
    const py = clientY - rect.top - rect.height / 2;
    const next = Math.min(MAX_SCALE, Math.max(1, scale * factor));
    if (next === scale) return;
    tx = px - (next / scale) * (px - tx);
    ty = py - (next / scale) * (py - ty);
    scale = next;
    if (scale === 1) { tx = 0; ty = 0; }
    clampPan();
    apply();
  };

  stage.addEventListener('wheel', event => {
    event.preventDefault();
    /* ctrlKey marks a trackpad pinch, whose deltas are much finer */
    zoomAt(event.clientX, event.clientY, Math.exp(-event.deltaY * (event.ctrlKey ? 0.01 : 0.0022)));
  }, { passive: false });

  stage.addEventListener('dblclick', event => {
    if (scale > 1) reset();
    else { animate(); zoomAt(event.clientX, event.clientY, 2.5); }
  });

  stage.addEventListener('pointerdown', event => {
    if (scale <= 1 || event.button !== 0 || event.target === resetChip) return;
    drag = { x: event.clientX, y: event.clientY };
    stage.classList.add('dragging');
    stage.setPointerCapture(event.pointerId);
  });
  stage.addEventListener('pointermove', event => {
    if (!drag) return;
    tx += event.clientX - drag.x;
    ty += event.clientY - drag.y;
    drag = { x: event.clientX, y: event.clientY };
    clampPan();
    apply();
  });
  const endDrag = () => { drag = null; stage.classList.remove('dragging'); };
  stage.addEventListener('pointerup', endDrag);
  stage.addEventListener('pointercancel', endDrag);

  resetChip.addEventListener('click', reset);
}

/* ————— Export ————— */

async function exportDoc() {
  if (!working.length) { alert('The timeline is empty — add photographs before exporting.'); return; }
  const btn = $('#exportBtn');
  const old = btn.textContent;
  btn.disabled = true;
  try {
    const recs = working.map(id => byId.get(id));
    const thumbs = [];
    for (let i = 0; i < recs.length; i++) {
      btn.textContent = `Embedding ${i + 1}/${recs.length}…`;
      thumbs.push(await renderThumb(previewSrc(recs[i])));
    }
    btn.textContent = 'Writing document…';
    const stamp = new Date();
    const blob = buildDocx(recs, thumbs, stamp);
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `beaumont-timeline-${stamp.toISOString().slice(0, 10)}.docx`;
    link.click();
    URL.revokeObjectURL(url);
  } finally {
    btn.textContent = old;
    btn.disabled = false;
  }
}

/* Draw the preview onto a size-capped canvas; return the JPEG data URI plus the
   thumbnail's pixel dimensions (needed to set the picture's aspect ratio). */
function renderThumb(src) {
  return new Promise(resolve => {
    const img = new Image();
    img.onload = () => {
      const MAX = 1000;
      const scale = Math.min(1, MAX / Math.max(img.naturalWidth, img.naturalHeight));
      const w = Math.max(1, Math.round(img.naturalWidth * scale));
      const h = Math.max(1, Math.round(img.naturalHeight * scale));
      const canvas = document.createElement('canvas');
      canvas.width = w; canvas.height = h;
      canvas.getContext('2d').drawImage(img, 0, 0, w, h);
      try { resolve({ dataUri: canvas.toDataURL('image/jpeg', 0.82), w, h }); }
      catch { resolve(null); }
    };
    img.onerror = () => resolve(null);
    img.src = encodeURI(src);
  });
}

/* ——— Minimal .docx (Office Open XML) writer ———
   The export must open natively in Word / Google Docs, show every photo so the
   client can QC the sequence, and let the exact order be rebuilt from the file.
   A real .docx (not HTML-saved-as-.doc) renders embedded images reliably; the
   ordered manifest rides along as beaumont-timeline.json inside the package,
   and every entry also prints its catalog ID as a human-readable fallback. */

const EMU_PER_IN = 914400;
const MAX_IMG_IN = 6.0;                 // fits US Letter with 1" margins
const utf8 = str => new TextEncoder().encode(str);

const CONTENT_TYPES = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="jpeg" ContentType="image/jpeg"/><Default Extension="json" ContentType="application/json"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>`;

const ROOT_RELS = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>`;

function buildDocx(recs, thumbs, stamp) {
  const media = [], rels = [], thumbPaths = [];
  const body = [coverXml(recs, stamp)];
  recs.forEach((r, i) => {
    const thumb = thumbs[i];
    let img = null;
    if (thumb) {
      const idx = media.length + 1;
      const name = `image${idx}.jpeg`;
      media.push({ name, bytes: dataUriToBytes(thumb.dataUri) });
      const relId = `rIdImg${idx}`;
      rels.push(`<Relationship Id="${relId}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/${name}"/>`);
      img = { relId, id: 100 + idx, w: thumb.w, h: thumb.h };
      thumbPaths.push(`word/media/${name}`);
    } else thumbPaths.push(null);
    body.push(entryXml(r, i, img));
  });

  const documentXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><w:body>${body.join('')}<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr></w:body></w:document>`;
  const documentRels = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">${rels.join('')}</Relationships>`;

  return zip([
    { name: '[Content_Types].xml', data: utf8(CONTENT_TYPES) },
    { name: '_rels/.rels', data: utf8(ROOT_RELS) },
    { name: 'word/document.xml', data: utf8(documentXml) },
    { name: 'word/_rels/document.xml.rels', data: utf8(documentRels) },
    { name: 'beaumont-timeline.json', data: utf8(manifestJson(recs, thumbPaths, stamp)) },
    ...media.map(m => ({ name: `word/media/${m.name}`, data: m.bytes })),
  ]);
}

/* ——— WordprocessingML paragraph / run builders ———
   sz is half-points (28 = 14pt); paragraph spacing is twentieths of a point
   (240 = 12pt); run spacing (spc) is character spacing in twips. */
function rp(o = {}) {
  return `<w:rPr>${o.font ? `<w:rFonts w:ascii="${o.font}" w:hAnsi="${o.font}"/>` : ''}${o.b ? '<w:b/>' : ''}${o.i ? '<w:i/>' : ''}${o.caps ? '<w:caps/>' : ''}${o.color ? `<w:color w:val="${o.color}"/>` : ''}${o.sz ? `<w:sz w:val="${o.sz}"/><w:szCs w:val="${o.sz}"/>` : ''}${o.spc ? `<w:spacing w:val="${o.spc}"/>` : ''}</w:rPr>`;
}
function pp(o = {}) {
  return `<w:pPr>${o.keepNext ? '<w:keepNext/>' : ''}${o.border || ''}<w:spacing w:before="${o.before || 0}" w:after="${o.after == null ? 120 : o.after}"/>${o.align ? `<w:jc w:val="${o.align}"/>` : ''}</w:pPr>`;
}
const rn = (text, rPr = '') => `<w:r>${rPr}<w:t xml:space="preserve">${esc(text)}</w:t></w:r>`;
const pgraph = (runs, pPr = '') => `<w:p>${pPr}${runs}</w:p>`;

function coverXml(recs, stamp) {
  const years = recs.map(startYear).filter(Boolean);
  const span = years.length ? `${Math.min(...years)} – ${Math.max(...years)}` : '—';
  const date = stamp.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  return [
    pgraph(rn('Beaumont Library District · Timeline Mural', rp({ font: 'Libre Franklin', b: true, caps: true, sz: 18, color: '8C5A1C', spc: 40 })), pp({ after: 80, align: 'center' })),
    pgraph(rn('Beaumont ', rp({ font: 'Georgia', sz: 52, color: '23282A' })) + rn('in Pictures', rp({ font: 'Georgia', i: true, sz: 52, color: '8C5A1C' })), pp({ after: 80, align: 'center' })),
    pgraph(rn(`Approved timeline sequence — ${recs.length} photograph${recs.length === 1 ? '' : 's'}, spanning ${span}`, rp({ font: 'Georgia', sz: 22, color: '55504A' })), pp({ after: 40, align: 'center' })),
    pgraph(rn(`Prepared ${date}`, rp({ font: 'Georgia', sz: 20, color: '7A736A' })), pp({ after: 100, align: 'center' })),
    pgraph(rn('Photographs run in mural order, left to right. Each entry lists its catalog ID for reference.', rp({ font: 'Libre Franklin', i: true, sz: 16, color: '7A736A' })), pp({ after: 240, align: 'center' })),
  ].join('');
}

function entryXml(r, i, img) {
  const border = i === 0 ? '' : '<w:pBdr><w:top w:val="single" w:sz="6" w:space="10" w:color="D8CCAE"/></w:pBdr>';
  const out = [
    pgraph(
      rn(String(i + 1).padStart(2, '0'), rp({ font: 'Libre Franklin', b: true, sz: 24, color: '15424A' })) +
      rn('     ', rp({ sz: 24 })) +
      rn(displayDate(r), rp({ font: 'Libre Franklin', b: true, caps: true, sz: 18, color: '8C5A1C', spc: 30 })),
      pp({ keepNext: true, border, before: i === 0 ? 0 : 240, after: 100 })
    ),
    img
      ? pgraph(pictureXml(img, r), pp({ keepNext: true, after: 100 }))
      : pgraph(rn('[This image could not be embedded]', rp({ font: 'Georgia', i: true, sz: 20, color: 'A33333' })), pp({ after: 100 })),
    pgraph(rn(r.title, rp({ font: 'Georgia', sz: 30, color: '23282A' })), pp({ keepNext: true, after: 60 })),
  ];
  if (r.caption) out.push(pgraph(rn(r.caption, rp({ font: 'Georgia', sz: 22, color: '23282A' })), pp({ after: 60 })));
  if (r.research?.description) out.push(pgraph(rn(r.research.description, rp({ font: 'Georgia', sz: 20, color: '55504A' })), pp({ after: 60 })));
  out.push(pgraph(rn(`Credit: ${r.attribution || 'Unknown'} · Rights: ${r.rights_status || 'Undetermined'}${r.caption_source ? ` · Caption source: ${r.caption_source}` : ''}`, rp({ font: 'Georgia', i: true, sz: 18, color: '7A736A' })), pp({ after: 40 })));
  const sources = sourceCitations(r);
  if (sources.length) {
    out.push(pgraph(rn('Sources & citations', rp({ font: 'Libre Franklin', b: true, caps: true, sz: 15, color: '8C5A1C', spc: 20 })), pp({ before: 40, after: 20 })));
    sources.forEach(e => {
      const line = e.label ? (e.url ? `${e.label} — ${e.url}` : e.label) : (e.url || '');
      out.push(pgraph(rn(`•  ${line}`, rp({ font: 'Georgia', sz: 16, color: '7A736A' })), pp({ after: 10 })));
    });
  }
  out.push(pgraph(rn(`Catalog ID: ${r.id}`, rp({ font: 'Consolas', sz: 15, color: 'A79D8E' })), pp({ before: 40, after: 80 })));
  return out.join('');
}

function pictureXml(img, r) {
  const w = Math.round(MAX_IMG_IN * EMU_PER_IN);
  const h = Math.round(w * (img.h / img.w));
  const alt = esc(r.title);
  return `<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="${w}" cy="${h}"/><wp:docPr id="${img.id}" name="Photograph ${img.id}" descr="${alt}"/><wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr id="${img.id}" name="image${img.id}.jpeg" descr="${alt}"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="${img.relId}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="${w}" cy="${h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>`;
}

/* The manifest is the source of truth for rebuilding the sequence: order[].id,
   in position order, IS the timeline. */
function manifestJson(recs, thumbPaths, stamp) {
  const years = recs.map(startYear).filter(Boolean);
  return JSON.stringify({
    kind: 'beaumont-timeline',
    version: 2,
    exportedAt: stamp.toISOString(),
    localStorageKey: KEY,
    count: recs.length,
    span: years.length ? [Math.min(...years), Math.max(...years)] : null,
    note: 'order[].id, in position order, is the timeline. Rebuild by setting the working array to these ids.',
    order: recs.map((r, i) => ({
      position: i + 1,
      id: r.id,
      title: r.title,
      date: displayDate(r),
      date_start: startYear(r),
      caption: r.caption || '',
      attribution: r.attribution || '',
      rights: r.rights_status || '',
      thumbnail: thumbPaths[i],
    })),
  }, null, 2);
}

/* ——— ZIP container (STORED / no compression) ——— */
function dataUriToBytes(dataUri) {
  const bin = atob(dataUri.slice(dataUri.indexOf(',') + 1));
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes;
}

const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
    t[n] = c >>> 0;
  }
  return t;
})();
function crc32(bytes) {
  let c = 0xFFFFFFFF;
  for (let i = 0; i < bytes.length; i++) c = CRC_TABLE[(c ^ bytes[i]) & 0xFF] ^ (c >>> 8);
  return (c ^ 0xFFFFFFFF) >>> 0;
}

function zip(files) {
  const encoder = new TextEncoder();
  const chunks = [], central = [];
  let offset = 0;
  const DOS_TIME = 0, DOS_DATE = 0x5021;   // 2020-01-01, fixed for reproducibility
  const u16 = n => new Uint8Array([n & 0xFF, (n >>> 8) & 0xFF]);
  const u32 = n => new Uint8Array([n & 0xFF, (n >>> 8) & 0xFF, (n >>> 16) & 0xFF, (n >>> 24) & 0xFF]);
  const push = arr => { chunks.push(arr); offset += arr.length; };

  for (const f of files) {
    const nameBytes = encoder.encode(f.name);
    const crc = crc32(f.data);
    const size = f.data.length;
    central.push({ nameBytes, crc, size, offset });
    push(u32(0x04034b50));
    push(u16(20)); push(u16(0x0800)); push(u16(0));      // version needed, UTF-8 flag, method: stored
    push(u16(DOS_TIME)); push(u16(DOS_DATE));
    push(u32(crc)); push(u32(size)); push(u32(size));
    push(u16(nameBytes.length)); push(u16(0));
    push(nameBytes); push(f.data);
  }

  const cdStart = offset;
  for (const c of central) {
    push(u32(0x02014b50));
    push(u16(20)); push(u16(20)); push(u16(0x0800)); push(u16(0));
    push(u16(DOS_TIME)); push(u16(DOS_DATE));
    push(u32(c.crc)); push(u32(c.size)); push(u32(c.size));
    push(u16(c.nameBytes.length)); push(u16(0)); push(u16(0));
    push(u16(0)); push(u16(0)); push(u32(0));
    push(u32(c.offset));
    push(c.nameBytes);
  }
  const cdSize = offset - cdStart;
  push(u32(0x06054b50));
  push(u16(0)); push(u16(0));
  push(u16(central.length)); push(u16(central.length));
  push(u32(cdSize)); push(u32(cdStart)); push(u16(0));

  return new Blob(chunks, { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
}
