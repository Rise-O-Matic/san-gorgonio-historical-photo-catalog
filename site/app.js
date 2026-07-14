const STORAGE_KEY = 'bld-historical-catalog-v1';
const state = { catalog: null, records: [], filtered: [], view: 'timeline', limit: 80, filters: {}, saved: loadSaved() };
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const escapeHtml = value => String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));

function loadSaved() { try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || { records: {} }; } catch { return { records: {} }; } }
function persist() { localStorage.setItem(STORAGE_KEY, JSON.stringify(state.saved)); updateCounts(); }
function savedFor(record) { return state.saved.records[record.id] || { selected: record.selected_default, comment: '', edits: {} }; }
function updateSaved(record, patch) { state.saved.records[record.id] = { ...savedFor(record), ...patch }; persist(); }
function isSelected(record) { return Boolean(savedFor(record).selected); }
function edited(record, field, fallback) { return savedFor(record).edits?.[field] ?? fallback; }
function effectiveDate(record) { const value = edited(record, 'date', record.date.start); return value === '' || value == null ? null : Number(value); }
function effectiveQuality(record) { return Number(edited(record, 'quality', record.quality.factor)); }
function calculatedPrint(record, ppi = 100) { const crop = 1 - record.print_viability.crop_allowance_percent / 100; const factor = effectiveQuality(record); return { width: Math.round(record.original_pixels.width * crop * factor / ppi * 10) / 10, height: Math.round(record.original_pixels.height * crop * factor / ppi * 10) / 10 }; }
function effectiveClassification(record) { const size = calculatedPrint(record); const shortSide = Math.min(size.width, size.height); return shortSide >= 16 ? 'Production Ready' : shortSide >= 8 ? 'Potentially Usable' : 'Reference Only'; }
function byChrono(a, b) { const ya = effectiveDate(a), yb = effectiveDate(b); if (ya == null && yb == null) return edited(a,'title',a.title).localeCompare(edited(b,'title',b.title)); if (ya == null) return 1; if (yb == null) return -1; return ya - yb || edited(a,'title',a.title).localeCompare(edited(b,'title',b.title)); }
function orderedSelection() { const selected = state.records.filter(isSelected); const byId = new Map(selected.map(r => [r.id, r])); const ordered = []; (state.saved.sequence || []).forEach(id => { if (byId.has(id)) { ordered.push(byId.get(id)); byId.delete(id); } }); return [...ordered, ...[...byId.values()].sort(byChrono)]; }
function saveSequence(ids) { state.saved.sequence = ids; persist(); }

async function init() {
  try {
    const response = await fetch('data/catalog.json', { cache: 'no-store' });
    if (!response.ok) throw new Error(`Catalog request failed (${response.status})`);
    state.catalog = await response.json(); state.records = state.catalog.records;
    seedDefaults(); populateFilters(); bindEvents(); applyFilters();
    $('#catalogNotice').hidden = true;
  } catch (error) {
    $('#catalogNotice').innerHTML = `<strong>Catalog data could not be loaded.</strong><br>${escapeHtml(error.message)}<br><small>Serve the site over HTTP after running the ingestion pipeline.</small>`;
  }
}

function seedDefaults() {
  let changed = false;
  state.records.forEach(record => { if (!state.saved.records[record.id] && record.selected_default) { state.saved.records[record.id] = { selected: true, comment: '', edits: {} }; changed = true; } });
  if (changed) persist();
}

function populateFilters() {
  const decades = [...new Set(state.records.map(r => r.decade).filter(Boolean))].sort();
  const subjectStopwords = new Set(['about','after','and','are','as','at','back','between','by','circa','copy','courtesy','dated','during','for','from','front','image','late','left','new','old','photo','right','scan','the','with']);
  const subjects = [...new Set(state.records.flatMap(r => r.subjects || []).filter(value => value.length > 2 && !subjectStopwords.has(value.toLowerCase()) && !/^\d/.test(value)))].sort((a,b) => a.localeCompare(b)).slice(0, 250);
  const locations = [...new Set(state.records.flatMap(r => r.locations || []))].sort((a,b) => a.localeCompare(b));
  decades.forEach(value => $('#dateFilter').insertAdjacentHTML('beforeend', `<option value="${value}">${value}s</option>`));
  subjects.forEach(value => $('#subjectFilter').insertAdjacentHTML('beforeend', `<option>${escapeHtml(value)}</option>`));
  locations.forEach(value => $('#locationFilter').insertAdjacentHTML('beforeend', `<option>${escapeHtml(value)}</option>`));
}

function bindEvents() {
  $('#search').addEventListener('input', applyFilters);
  ['dateFilter','subjectFilter','locationFilter','resolutionFilter','researchFilter','selectionFilter'].forEach(id => $(`#${id}`).addEventListener('change', applyFilters));
  $('#filterToggle').addEventListener('click', () => { const panel = $('#filterPanel'); panel.hidden = !panel.hidden; $('#filterToggle').setAttribute('aria-expanded', String(!panel.hidden)); });
  $('#clearFilters').addEventListener('click', () => { $('#search').value = ''; $$('#filterPanel select').forEach(select => select.value = ''); applyFilters(); });
  $$('.view-switcher button').forEach(button => button.addEventListener('click', () => setView(button.dataset.view)));
  $('#loadMore').addEventListener('click', () => { state.limit += 80; render(); });
  $('#catalog').addEventListener('click', catalogClick);
  $('#reviewSelected').addEventListener('click', showSelectionPage);
  $('#backToCatalog').addEventListener('click', showCatalogPage);
  $('#openMural').addEventListener('click', showMuralPage);
  $('#backFromMural').addEventListener('click', showSelectionPage);
  $('#sortChrono').addEventListener('click', () => { saveSequence(orderedSelection().sort(byChrono).map(r => r.id)); renderMural(); });
  $('#downloadMural').addEventListener('click', downloadMural);
  $$('#muralPage .height-switcher button').forEach(button => button.addEventListener('click', () => {
    $$('#muralPage .height-switcher button').forEach(b => b.classList.remove('active')); button.classList.add('active');
    $('#muralRibbon').style.setProperty('--frame-h', `${button.dataset.frameHeight}px`);
  }));
  bindMuralInteractions();
  $('#downloadReport').addEventListener('click', downloadReport);
  $('#copyReport').addEventListener('click', copyReport);
  $('#clearSelection').addEventListener('click', () => { if (confirm('Remove all photographs from the selection?')) { state.records.forEach(r => updateSaved(r, { selected: false })); showSelectionPage(); } });
  $('#selectedGrid').addEventListener('input', event => { const area = event.target.closest('textarea[data-id]'); if (area) { const record = recordById(area.dataset.id); updateSaved(record, { comment: area.value }); } });
  $('#selectedGrid').addEventListener('click', event => { const button = event.target.closest('[data-remove]'); if (button) { const record = recordById(button.dataset.remove); updateSaved(record, { selected: false }); showSelectionPage(); } });
  $$('dialog [data-close]').forEach(button => button.addEventListener('click', () => button.closest('dialog').close()));
  $$('dialog').forEach(dialog => dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); }));
}

function setView(view) { state.view = view; $$('.view-switcher button').forEach(button => { const active = button.dataset.view === view; button.classList.toggle('active', active); button.setAttribute('aria-pressed', String(active)); }); render(); }
function recordById(id) { return state.records.find(record => record.id === id); }
function fileById(id) { return state.catalog.files.find(file => file.file_id === id); }

function applyFilters() {
  const query = $('#search')?.value.trim().toLowerCase() || '';
  const values = {
    date: $('#dateFilter')?.value || '', subject: $('#subjectFilter')?.value || '', location: $('#locationFilter')?.value || '',
    resolution: $('#resolutionFilter')?.value || '', research: $('#researchFilter')?.value || '', selection: $('#selectionFilter')?.value || ''
  };
  state.filters = values; state.limit = 80;
  state.filtered = state.records.filter(record => {
    const year = effectiveDate(record);
    const haystack = [edited(record,'title',record.title), edited(record,'caption',record.caption), edited(record,'attribution',record.attribution), record.visible_text, ...(record.subjects||[]), ...(record.locations||[]), ...(record.people||[]), ...(record.search_terms||[])].join(' ').toLowerCase();
    return (!query || haystack.includes(query))
      && (!values.date || (values.date === 'undated' ? !year : Math.floor(year / 10) * 10 === Number(values.date)))
      && (!values.subject || record.subjects?.includes(values.subject))
      && (!values.location || record.locations?.includes(values.location))
      && (!values.resolution || effectiveClassification(record) === values.resolution)
      && (!values.research || record.research_status === values.research)
      && (!values.selection || (values.selection === 'selected' ? isSelected(record) : values.selection === 'unselected' ? !isSelected(record) : record.curated));
  });
  const active = Object.values(values).filter(Boolean).length + Number(Boolean(query));
  $('#filterCount').textContent = active; render(); updateCounts();
}

function updateCounts() {
  if (!state.catalog) return;
  $('#visibleCount').textContent = state.filtered.length.toLocaleString();
  $('#catalogCount').textContent = state.records.length.toLocaleString();
  $('#selectedCount').textContent = state.records.filter(isSelected).length.toLocaleString();
}

function card(record) {
  const selected = isSelected(record); const year = effectiveDate(record); const classification = effectiveClassification(record);
  return `<article class="photo-card" data-id="${record.id}">
    <div class="photo-media"><img src="${encodeURI(record.thumbnail)}" loading="lazy" alt="${escapeHtml(edited(record,'title',record.title))}">
    ${record.curated ? '<span class="flag">Mural set</span>' : ''}<button class="select-box ${selected?'selected':''}" type="button" data-select aria-label="${selected?'Remove from':'Add to'} mural selection">${selected?'✓':'＋'}</button></div>
    <div class="photo-body"><p class="photo-date">${year || 'Date unknown'}</p><h3 class="photo-title">${escapeHtml(edited(record,'title',record.title))}</h3>
    <p class="photo-caption">${escapeHtml(edited(record,'caption',record.caption))}</p>
    <p class="photo-credit">Credit: ${escapeHtml(edited(record,'attribution',record.attribution||'Unknown'))}</p>
    <div class="photo-meta"><span class="quality-pill ${classification==='Reference Only'?'reference':''}">${escapeHtml(classification)}</span><span>${record.original_pixels.width.toLocaleString()} × ${record.original_pixels.height.toLocaleString()} px</span></div></div>
    <div class="card-actions"><button type="button" data-detail>View details</button>${record.version_file_ids.length>1?`<button type="button" data-compare>${record.version_file_ids.length} versions</button>`:''}</div>
  </article>`;
}

function render() {
  const root = $('#catalog'); if (!root) return;
  root.className = `catalog ${state.view}-view`; const visible = state.filtered.slice(0, state.limit);
  if (!visible.length) { root.innerHTML = '<div class="notice"><strong>No photographs match these filters.</strong><br>Try clearing one or more filters.</div>'; $('#loadMore').hidden = true; return; }
  if (state.view === 'grid') root.innerHTML = visible.map(card).join('');
  else {
    const groups = new Map(); visible.forEach(record => { const year = effectiveDate(record); const label = year ? `${Math.floor(year/10)*10}s` : 'Undated'; if (!groups.has(label)) groups.set(label, []); groups.get(label).push(record); });
    root.innerHTML = [...groups].map(([label, records]) => `<section class="timeline-group"><h2 class="timeline-year">${label}</h2><div class="timeline-items">${records.map(card).join('')}</div></section>`).join('');
  }
  $('#loadMore').hidden = state.filtered.length <= state.limit;
}

function catalogClick(event) {
  const article = event.target.closest('.photo-card'); if (!article) return; const record = recordById(article.dataset.id);
  if (event.target.closest('[data-select]')) { updateSaved(record, { selected: !isSelected(record) }); applyFilters(); }
  else if (event.target.closest('[data-compare]')) showCompare(record);
  else showDetail(record);
}

function metricRows(record) { return Object.entries(record.print_viability.ppi).map(([ppi, value]) => `<tr><td>${ppi} PPI</td><td>${value.width_inches} × ${value.height_inches} in</td><td>${value.native_crop_width_inches} × ${value.native_crop_height_inches} in</td></tr>`).join(''); }
function showDetail(record) {
  const saved = savedFor(record); const master = fileById(record.master_file_id);
  const livePrint = calculatedPrint(record);
  $('#detailContent').innerHTML = `<div class="detail-layout"><div class="detail-image"><img src="${encodeURI(record.preview)}" alt="${escapeHtml(edited(record,'title',record.title))}"></div>
  <div class="detail-copy"><p class="eyebrow">${record.curated?'Curated mural candidate':'Collection photograph'}</p><h2>${escapeHtml(edited(record,'title',record.title))}</h2>
  <button class="${isSelected(record)?'secondary-button':'primary-button'}" id="detailSelect" type="button">${isSelected(record)?'✓ Selected for mural':'Select for mural'}</button>
  <label>Working title<input id="editTitle" value="${escapeHtml(edited(record,'title',record.title))}"></label>
  <label>Estimated year<input id="editDate" type="number" min="1800" max="2100" value="${escapeHtml(edited(record,'date',record.date.start)||'')}" placeholder="Unknown"></label>
  <label>Working caption<textarea id="editCaption" placeholder="Add a verified or provisional caption…">${escapeHtml(edited(record,'caption',record.caption))}</textarea></label>
  <label>Attribution / credit<input id="editAttribution" value="${escapeHtml(edited(record,'attribution',record.attribution||'Unknown'))}" placeholder="Holding institution, collection, or creator — 'Unknown' if unestablished"><small class="attribution-note">Source: ${escapeHtml(record.caption_source||'—')} · confidence: ${escapeHtml(record.attribution_confidence||'unknown')}</small></label>
  <label>Research status<select id="editResearch"><option>${escapeHtml(record.research_status)}</option><option>In progress</option><option>Researched</option></select></label>
  <label>Scan quality factor<select id="editQuality"><option value="1" ${effectiveQuality(record)===1?'selected':''}>Sharp · 100%</option><option value="0.75" ${effectiveQuality(record)===0.75?'selected':''}>Moderate · 75%</option><option value="0.5" ${effectiveQuality(record)===0.5?'selected':''}>Soft or damaged · 50%</option></select></label>
  <label>Client comment<textarea id="detailComment" placeholder="Why this image works, preferred crop, questions…">${escapeHtml(saved.comment)}</textarea></label>
  <div class="metric-box"><span id="liveClass">${escapeHtml(effectiveClassification(record))}</span><strong id="livePrint">Recommended native maximum: ${livePrint.width} × ${livePrint.height} in at 100 PPI</strong><small>${master.image.width.toLocaleString()} × ${master.image.height.toLocaleString()} original pixels · ${(record.print_viability.crop_allowance_percent)}% crop allowance · <span id="liveQuality">${Math.round(effectiveQuality(record)*100)}</span>% quality factor</small></div>
  <table class="metric-table"><thead><tr><th>Output</th><th>Quality-adjusted</th><th>Native after crop</th></tr></thead><tbody>${metricRows(record)}</tbody></table>
  <p class="disclaimer">Quality factors prevent soft or damaged scans from being overrated. AI-upscaled dimensions are not shown as native detail. Dates and machine suggestions require human verification.</p>
  ${record.version_file_ids.length>1?`<button class="secondary-button" id="detailCompare" type="button">Compare ${record.version_file_ids.length} available versions</button>`:''}
  </div></div>`;
  const dialog = $('#detailDialog'); dialog.showModal();
  $('#detailSelect').addEventListener('click', () => { updateSaved(record, { selected: !isSelected(record) }); dialog.close(); applyFilters(); });
  ['Title','Date','Caption','Attribution'].forEach(name => $(`#edit${name}`).addEventListener('change', event => { const current = savedFor(record); updateSaved(record, { edits: { ...(current.edits||{}), [name.toLowerCase()]: event.target.value } }); }));
  $('#editQuality').addEventListener('change', event => { const current = savedFor(record); updateSaved(record, { edits: { ...(current.edits||{}), quality: Number(event.target.value) } }); const value = calculatedPrint(record); $('#livePrint').textContent = `Recommended native maximum: ${value.width} × ${value.height} in at 100 PPI`; $('#liveQuality').textContent = Math.round(effectiveQuality(record)*100); $('#liveClass').textContent = effectiveClassification(record); });
  $('#detailComment').addEventListener('input', event => updateSaved(record, { comment: event.target.value }));
  $('#detailCompare')?.addEventListener('click', () => { dialog.close(); showCompare(record); });
}

function showCompare(record) {
  const files = record.version_file_ids.map(fileById).filter(Boolean);
  $('#compareContent').innerHTML = `<div class="compare-wrap"><p class="eyebrow">Alternate-version review</p><h2>${escapeHtml(edited(record,'title',record.title))}</h2><p>${escapeHtml(record.master_reason)}</p><div class="compare-grid">${files.map(file => `<article class="compare-item"><img src="${encodeURI(file.preview)}" alt="Version ${escapeHtml(file.filename)}"><div><strong>${file.file_id===record.master_file_id?'Recommended master · ':''}${escapeHtml(file.filename)}</strong><br>${file.image.width.toLocaleString()} × ${file.image.height.toLocaleString()} px · ${escapeHtml(file.image.format)}<br>Sharpness measure: ${file.image.sharpness_score}<br><small>${escapeHtml(file.path)}</small></div></article>`).join('')}</div></div>`;
  $('#compareDialog').showModal();
}

function showSelectionPage() {
  $('#catalog').hidden = true; $('.controls').hidden = true; $('#filterPanel').hidden = true; $('#loadMore').hidden = true; $('#muralPage').hidden = true; $('#selectionPage').hidden = false;
  const records = state.records.filter(isSelected); $('#selectionSummary').textContent = `${records.length} photograph${records.length===1?'':'s'} in this browser’s saved shortlist.`;
  $('#selectedGrid').innerHTML = records.length ? records.map(record => { const size=calculatedPrint(record); return `<article class="selected-row"><img src="${encodeURI(record.thumbnail)}" alt=""><div><strong>${escapeHtml(edited(record,'title',record.title))}</strong><p>${effectiveDate(record)||'Undated'} · ${escapeHtml(effectiveClassification(record))} · ${size.width} × ${size.height} in at 100 PPI</p><textarea data-id="${record.id}" placeholder="Client comment">${escapeHtml(savedFor(record).comment)}</textarea></div><button class="text-button danger" data-remove="${record.id}" type="button">Remove</button></article>`; }).join('') : '<div class="notice">No photographs are selected yet.</div>';
  scrollTo({top:0, behavior:'smooth'});
}
function showCatalogPage() { $('#selectionPage').hidden = true; $('#muralPage').hidden = true; $('#catalog').hidden = false; $('.controls').hidden = false; applyFilters(); scrollTo({top:0, behavior:'smooth'}); }

function showMuralPage() {
  $('#catalog').hidden = true; $('.controls').hidden = true; $('#filterPanel').hidden = true; $('#loadMore').hidden = true; $('#selectionPage').hidden = true; $('#muralPage').hidden = false;
  renderMural(); scrollTo({top:0, behavior:'smooth'});
}

function muralFrame(record, index) {
  const year = effectiveDate(record); const size = calculatedPrint(record); const classification = effectiveClassification(record);
  return `<article class="mural-frame" draggable="true" data-id="${record.id}">
    <button class="frame-remove" type="button" data-remove-seq="${record.id}" aria-label="Remove from mural">×</button>
    <div class="frame-media"><img src="${encodeURI(record.preview)}" loading="lazy" alt="${escapeHtml(edited(record,'title',record.title))}"><span class="frame-index">${index+1}</span></div>
    <div class="frame-body">
      <p class="frame-year">${year || 'Undated'}</p>
      <h3 class="frame-title">${escapeHtml(edited(record,'title',record.title))}</h3>
      <p class="frame-caption">${escapeHtml(edited(record,'caption',record.caption))}</p>
      <p class="frame-credit">${escapeHtml(edited(record,'attribution',record.attribution||'Unknown'))}</p>
      <p class="frame-print"><span class="quality-pill ${classification==='Reference Only'?'reference':''}">${escapeHtml(classification)}</span> ${size.width} × ${size.height} in · 100 PPI</p>
    </div>
  </article>`;
}

function renderMural() {
  const records = orderedSelection(); const ribbon = $('#muralRibbon');
  const years = records.map(effectiveDate).filter(v => v != null);
  const span = years.length ? ` · ${Math.min(...years)}–${Math.max(...years)}` : '';
  $('#muralSummary').textContent = records.length ? `${records.length} photograph${records.length===1?'':'s'} in sequence${span}. Drag to reorder.` : 'No photographs selected yet.';
  $('#downloadMural').disabled = !records.length;
  ribbon.innerHTML = records.length ? records.map(muralFrame).join('') : '<div class="notice">Nothing selected yet. Choose photographs in the catalog, then return here to arrange them.</div>';
}

function bindMuralInteractions() {
  const ribbon = $('#muralRibbon');
  ribbon.addEventListener('dragstart', event => { const frame = event.target.closest('.mural-frame'); if (!frame) return; frame.classList.add('dragging'); event.dataTransfer.effectAllowed = 'move'; });
  ribbon.addEventListener('dragend', event => { event.target.closest('.mural-frame')?.classList.remove('dragging'); saveSequence($$('.mural-frame', ribbon).map(frame => frame.dataset.id)); renderMural(); });
  ribbon.addEventListener('dragover', event => {
    event.preventDefault(); const dragging = $('.dragging', ribbon); if (!dragging) return;
    const after = frameAfterPoint(ribbon, event.clientX, event.clientY);
    if (after == null) ribbon.appendChild(dragging); else if (after !== dragging) ribbon.insertBefore(dragging, after);
  });
  ribbon.addEventListener('click', event => {
    const remove = event.target.closest('[data-remove-seq]');
    if (remove) { updateSaved(recordById(remove.dataset.removeSeq), { selected: false }); renderMural(); return; }
    if ($('.dragging', ribbon)) return;
    const frame = event.target.closest('.mural-frame'); if (frame) showDetail(recordById(frame.dataset.id));
  });
}

function frameAfterPoint(container, x, y) {
  const frames = $$('.mural-frame:not(.dragging)', container);
  let closest = { distance: Infinity, element: null };
  frames.forEach(frame => { const box = frame.getBoundingClientRect(); const cx = box.left + box.width / 2; const cy = box.top + box.height / 2; if (x < cx) { const distance = Math.hypot(x - cx, y - cy); if (distance < closest.distance) closest = { distance, element: frame }; } });
  return closest.element;
}

function muralData() {
  const records = orderedSelection();
  return { generated_at: new Date().toISOString(), project: state.catalog.project_title, sequence_length: records.length, sequence: records.map((record, index) => { const size = calculatedPrint(record); return { position: index+1, id: record.id, title: edited(record,'title',record.title), estimated_year: effectiveDate(record), caption: edited(record,'caption',record.caption), attribution: edited(record,'attribution',record.attribution||'Unknown'), classification: effectiveClassification(record), recommended_native_maximum: `${size.width} × ${size.height} in at 100 PPI`, comment: savedFor(record).comment, master_file_id: record.master_file_id, source_paths: record.version_file_ids.map(id => fileById(id)?.path).filter(Boolean) }; }) };
}
function downloadMural() { const blob = new Blob([JSON.stringify(muralData(), null, 2)], {type:'application/json'}); const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = `beaumont-mural-sequence-${new Date().toISOString().slice(0,10)}.json`; link.click(); URL.revokeObjectURL(url); }

function reportData() { return { generated_at: new Date().toISOString(), project: state.catalog.project_title, note: 'Selections and comments are browser-local until this report is shared.', selections: state.records.filter(isSelected).map(record => { const size=calculatedPrint(record); return { id: record.id, title: edited(record,'title',record.title), caption: edited(record,'caption',record.caption), attribution: edited(record,'attribution',record.attribution||'Unknown'), attribution_confidence: record.attribution_confidence||'unknown', caption_source: record.caption_source||'', estimated_year: effectiveDate(record), comment: savedFor(record).comment, classification: effectiveClassification(record), recommended_native_maximum: `${size.width} × ${size.height} in at 100 PPI`, quality_factor: effectiveQuality(record), master_file_id: record.master_file_id, source_paths: record.version_file_ids.map(id => fileById(id)?.path).filter(Boolean) }; }) }; }
function reportText() { const data = reportData(); return `${data.project}\nSelection report · ${new Date(data.generated_at).toLocaleString()}\n\n${data.selections.map((item,i) => `${i+1}. ${item.title} (${item.estimated_year||'undated'})\n   ID: ${item.id}\n   Caption: ${item.caption||'—'}\n   Credit: ${item.attribution||'Unknown'} (${item.attribution_confidence})\n   Print: ${item.classification}; ${item.recommended_native_maximum}\n   Comment: ${item.comment||'—'}\n   Master: ${item.source_paths[0]||item.master_file_id}`).join('\n\n')}`; }
function downloadReport() { const blob = new Blob([JSON.stringify(reportData(), null, 2)], {type:'application/json'}); const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href=url; link.download=`beaumont-mural-selection-${new Date().toISOString().slice(0,10)}.json`; link.click(); URL.revokeObjectURL(url); }
async function copyReport() { await navigator.clipboard.writeText(reportText()); const button=$('#copyReport'); const old=button.textContent; button.textContent='Copied'; setTimeout(()=>button.textContent=old,1600); }

init();
