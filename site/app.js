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
      <img src="${BLANK}" data-src="${encodeURI(r.thumbnail)}" alt="${esc(r.title)}" draggable="false">
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
    <div class="m-matte"><img src="${BLANK}" data-src="${encodeURI(r.thumbnail)}" alt="${esc(r.title)}" draggable="false"></div>
    <div class="m-plate">
      <p class="m-year">${esc(shortDate(r))}</p>
      <h3 class="m-title">${esc(r.title)}</h3>
      <p class="m-cap">${esc(r.caption)}</p>
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
      <img src="${encodeURI(record.preview)}" alt="${esc(record.title)}" draggable="false">
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
    const images = [];
    for (let i = 0; i < recs.length; i++) {
      btn.textContent = `Embedding ${i + 1}/${recs.length}…`;
      images.push(await imageDataUri(recs[i].preview));
    }
    btn.textContent = 'Writing document…';
    const blob = new Blob([exportHtml(recs, images)], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `beaumont-timeline-${new Date().toISOString().slice(0, 10)}.html`;
    link.click();
    URL.revokeObjectURL(url);
  } finally {
    btn.textContent = old;
    btn.disabled = false;
  }
}

function imageDataUri(src) {
  return new Promise(resolve => {
    const img = new Image();
    img.onload = () => {
      const MAX = 1200;
      const scale = Math.min(1, MAX / Math.max(img.naturalWidth, img.naturalHeight));
      const canvas = document.createElement('canvas');
      canvas.width = Math.max(1, Math.round(img.naturalWidth * scale));
      canvas.height = Math.max(1, Math.round(img.naturalHeight * scale));
      canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height);
      try { resolve(canvas.toDataURL('image/jpeg', 0.85)); } catch { resolve(null); }
    };
    img.onerror = () => resolve(null);
    img.src = encodeURI(src);
  });
}

function exportHtml(recs, images) {
  const today = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  const years = recs.map(startYear).filter(Boolean);
  const span = years.length ? `${Math.min(...years)} – ${Math.max(...years)}` : '—';
  const entries = recs.map((r, i) => {
    const sources = sourceCitations(r);
    return `
    <article class="entry">
      <header><span class="pos">${i + 1}</span><span class="year">${esc(displayDate(r))}</span></header>
      ${images[i] ? `<img src="${images[i]}" alt="${esc(r.title)}">` : '<p class="missing">[This image could not be embedded]</p>'}
      <h2>${esc(r.title)}</h2>
      <p class="cap">${esc(r.caption)}</p>
      ${r.research?.description ? `<p class="desc">${esc(r.research.description)}</p>` : ''}
      <p class="credit">Credit: ${esc(r.attribution || 'Unknown')} · Rights: ${esc(r.rights_status || 'Undetermined')}${r.caption_source ? ` · Caption source: ${esc(r.caption_source)}` : ''}</p>
      ${sources.length ? `<div class="sources"><p class="sources-head">Sources &amp; citations</p><ol>${sources.map(e => `<li>${esc(e.label || '')}${e.url ? `${e.label ? ' — ' : ''}<a href="${esc(e.url)}">${esc(e.url)}</a>` : ''}</li>`).join('')}</ol></div>` : ''}
    </article>`;
  }).join('\n');

  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Beaumont in Pictures — Timeline Sequence</title>
<style>
  body { margin: 0; background: #f6f0e2; color: #23282a; font-family: Georgia, "Times New Roman", serif; line-height: 1.55; }
  .doc { max-width: 780px; margin: 0 auto; padding: 56px 32px 72px; }
  .cover { text-align: center; border-bottom: 3px double #b09a5e; padding-bottom: 34px; margin-bottom: 12px; }
  .cover .rule { font-size: 11px; letter-spacing: .3em; text-transform: uppercase; color: #8c5a1c; margin: 0 0 14px; font-family: "Franklin Gothic Medium", "Helvetica Neue", sans-serif; }
  .cover h1 { font-size: 40px; font-weight: normal; margin: 0 0 8px; }
  .cover h1 em { color: #8c5a1c; }
  .cover p { margin: 4px 0; color: #55504a; font-size: 14px; }
  .entry { border-top: 1px solid #d8ccae; padding: 34px 0 26px; page-break-inside: avoid; break-inside: avoid; }
  .entry:first-of-type { border-top: none; }
  .entry header { display: flex; align-items: baseline; gap: 14px; margin-bottom: 14px; font-family: "Franklin Gothic Medium", "Helvetica Neue", sans-serif; }
  .entry .pos { background: #15424a; color: #f2e9d8; font-size: 12px; padding: 3px 9px; border-radius: 2px; letter-spacing: .08em; }
  .entry .year { font-size: 13px; letter-spacing: .18em; text-transform: uppercase; color: #8c5a1c; font-weight: bold; }
  .entry img { max-width: 100%; max-height: 540px; display: block; margin: 0 auto 16px; box-shadow: 0 4px 18px rgba(35,40,42,.25); background: #0b0b0a; padding: 8px; box-sizing: border-box; }
  .entry h2 { font-size: 22px; font-weight: normal; margin: 0 0 8px; }
  .entry .cap { margin: 0 0 10px; font-size: 15px; }
  .entry .desc { margin: 0 0 10px; font-size: 13.5px; color: #55504a; }
  .entry .credit { margin: 0; font-size: 12px; color: #7a736a; font-style: italic; }
  .entry .sources { margin-top: 10px; }
  .entry .sources-head { margin: 0 0 4px; font-size: 10.5px; letter-spacing: .14em; text-transform: uppercase; color: #8c5a1c; font-family: "Franklin Gothic Medium", "Helvetica Neue", sans-serif; }
  .entry .sources ol { margin: 0; padding-left: 18px; font-size: 11px; line-height: 1.6; color: #7a736a; }
  .entry .sources a { color: #8c5a1c; overflow-wrap: anywhere; }
  .missing { color: #a33; font-style: italic; }
  footer { border-top: 3px double #b09a5e; margin-top: 20px; padding-top: 18px; text-align: center; font-size: 12px; color: #7a736a; }
  @media print { body { background: #fff; } .doc { padding: 24px 0; } .entry img { box-shadow: none; } }
</style>
</head>
<body>
<div class="doc">
  <header class="cover">
    <p class="rule">Beaumont Library District · Timeline Mural</p>
    <h1>Beaumont <em>in Pictures</em></h1>
    <p>Approved timeline sequence — ${recs.length} photograph${recs.length === 1 ? '' : 's'}, spanning ${esc(span)}</p>
    <p>Prepared ${esc(today)}</p>
  </header>
  ${entries}
  <footer>
    <p>Generated from the Beaumont historical photo catalog. Photographs run in mural order, left to right.<br>
    Dates marked “c.” are estimates; credits and rights determinations are recorded per photograph above.</p>
  </footer>
</div>
</body>
</html>`;
}
