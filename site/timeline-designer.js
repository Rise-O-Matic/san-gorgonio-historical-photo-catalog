(() => {
  "use strict";

  const STORAGE_KEY = "bld.timelineDesigner.draft.v1";
  const ERA_NAMES = ["Origins and homeland", "Railroad and town building", "Civic life and orchards", "Growth and renewal"];
  const ERA_RANGES = [[0, 4], [5, 9], [10, 15], [16, 19]];
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

  const state = {
    approvedTokens: null,
    tokens: null,
    events: [],
    approvedEvents: [],
    baseMilestones: null,
    fixtures: [],
    history: [],
    future: [],
    selectedIndex: 0,
    fixtureId: "current",
    selectedRegion: "module",
    issues: [],
    dirty: false,
    canvasZoom: 14,
    timelineZoom: 3.8,
    saveTimer: null,
    preflightTimer: null,
    toastTimer: null,
    fieldStart: null
  };

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function escapeHtml(value = "") {
    return String(value).replace(/[&<>'"]/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[char]);
  }

  function getPath(object, path) {
    return path.split(".").reduce((value, key) => value?.[key], object);
  }

  function setPath(object, path, value) {
    const keys = path.split(".");
    const last = keys.pop();
    const target = keys.reduce((node, key) => node[key], object);
    target[last] = value;
  }

  function stableStringify(value) {
    if (Array.isArray(value)) return `[${value.map(stableStringify).join(",")}]`;
    if (value && typeof value === "object") {
      return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(",")}}`;
    }
    return JSON.stringify(value);
  }

  function snapshot(label = "Edit") {
    return { label, tokens: clone(state.tokens), events: clone(state.events), selectedIndex: state.selectedIndex };
  }

  function pushUndo(label, previous = null) {
    state.history.push(previous || snapshot(label));
    if (state.history.length > 80) state.history.shift();
    state.future = [];
    updateUndoButtons();
  }

  function pushUndoIfChanged(label, previous) {
    if (!previous) return;
    const before = stableStringify({ tokens: previous.tokens, events: previous.events });
    const after = stableStringify({ tokens: state.tokens, events: state.events });
    if (before !== after) pushUndo(label, previous);
  }

  function applySnapshot(next) {
    state.tokens = clone(next.tokens);
    state.events = clone(next.events);
    state.selectedIndex = Math.min(next.selectedIndex ?? 0, Math.max(0, state.events.length - 1));
    state.dirty = true;
    renderAll();
    scheduleSave();
  }

  function undo() {
    const previous = state.history.pop();
    if (!previous) return;
    state.future.push(snapshot(previous.label));
    applySnapshot(previous);
    toast(`Undid: ${previous.label}`);
  }

  function redo() {
    const next = state.future.pop();
    if (!next) return;
    state.history.push(snapshot(next.label));
    applySnapshot(next);
    toast(`Redid: ${next.label}`);
  }

  function updateUndoButtons() {
    $("#undoButton").disabled = !state.history.length;
    $("#redoButton").disabled = !state.future.length;
    $("#undoButton").title = state.history.length ? `Undo ${state.history.at(-1).label}` : "Nothing to undo";
    $("#redoButton").title = state.future.length ? `Redo ${state.future.at(-1).label}` : "Nothing to redo";
  }

  function toast(message) {
    const element = $("#toast");
    element.textContent = message;
    element.classList.add("show");
    clearTimeout(state.toastTimer);
    state.toastTimer = setTimeout(() => element.classList.remove("show"), 2600);
  }

  function markDirty() {
    state.dirty = true;
    $("#saveLight").className = "status-light dirty";
    $("#saveStatus").textContent = "Saving local draft…";
    scheduleSave();
  }

  function scheduleSave() {
    clearTimeout(state.saveTimer);
    state.saveTimer = setTimeout(saveDraft, 350);
  }

  function saveDraft() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ schemaVersion: 1, savedAt: new Date().toISOString(), tokens: state.tokens, events: state.events }));
      $("#saveLight").className = "status-light saved";
      $("#saveStatus").textContent = `Local draft saved ${new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`;
    } catch (error) {
      $("#saveStatus").textContent = "Draft could not be saved locally";
      console.error(error);
    }
  }

  function loadDraft() {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
      if (saved?.schemaVersion === 1 && saved.tokens && Array.isArray(saved.events)) {
        state.tokens = saved.tokens;
        state.events = saved.events;
        state.dirty = true;
        return saved.savedAt;
      }
    } catch (error) {
      console.warn("Ignored invalid local draft", error);
    }
    return null;
  }

  function assignEra(index) {
    return ERA_RANGES.findIndex(([start, end]) => index >= start && index <= end);
  }

  function buildEvents(milestones, catalog) {
    const records = new Map(catalog.records.map(record => [record.id, record]));
    return milestones.milestones.map((milestone, index) => {
      const record = records.get(milestone.record_id) || {};
      return {
        id: milestone.record_id,
        position: index + 1,
        reference_number: milestone.reference_number || record.reference_number || "",
        date: milestone.date || record.date?.display || "",
        headline: milestone.headline || "",
        caption: record.caption || record.title || "",
        photo: record.thumbnail || "",
        era: assignEra(index),
        title: record.title || "",
        context: milestone.context || "",
        sources: clone(milestone.sources || []),
        rights_status: record.rights_status || "",
        credit: record.rights_note || record.attribution || "",
        original_pixels: record.original_pixels || null,
        print_viability: record.print_viability || null
      };
    });
  }

  function selectedEvent() {
    return state.events[state.selectedIndex] || state.events[0];
  }

  function moduleVars(tokens, event, scale, unit = "px") {
    const m = tokens.module;
    const type = tokens.type;
    const c = tokens.colors;
    return {
      "--s": `${scale}${unit}`,
      "--module-width": m.width,
      "--headline-height": m.headlineHeight,
      "--headline-gap": m.headlineGap,
      "--lower-height": m.lowerHeight,
      "--lower-gap": m.lowerGap,
      "--inset": m.contentInset,
      "--photo-height": m.photoHeight,
      "--radius": m.cornerRadius,
      "--accent-height": m.accentHeight,
      "--shadow-offset": m.shadowOffset,
      "--stem-gap": m.stemGap,
      "--rule-width": m.ruleWidth,
      "--rule-height": m.ruleHeight,
      "--date-size": type.dateSize,
      "--date-leading": type.dateLeading,
      "--headline-size": type.headlineSize,
      "--headline-leading": type.headlineLeading,
      "--caption-size": type.captionSize,
      "--caption-leading": type.captionLeading,
      "--module-bg": c.module,
      "--photo-matte": c.photoMatte,
      "--module-ink": c.ink,
      "--caption-ink": c.caption,
      "--timeline-ink": c.timeline,
      "--era-color": c.eras[Number(event.era) || 0],
      "--font-family": `"${type.family}", ${type.fallback}`
    };
  }

  function createModule(event, options = {}) {
    const { scale = 10, unit = "px", selected = false, handles = false, left = null, top = null, index = -1 } = options;
    const element = document.createElement("article");
    element.className = "timeline-module";
    element.dataset.eventIndex = index;
    element.dataset.recordId = event.id || "fixture";
    if (selected) element.dataset.selected = "true";
    for (const [name, value] of Object.entries(moduleVars(state.tokens, event, scale, unit))) element.style.setProperty(name, value);
    if (left !== null) element.style.left = `${left}${unit}`;
    if (top !== null) element.style.top = `${top}${unit}`;
    if (left !== null || top !== null) element.style.transform = "translate(-50%,-50%)";

    const photo = event.photo
      ? `<img src="${escapeHtml(event.photo)}" alt="" draggable="false">`
      : `<span class="tm-photo-placeholder">Photo area</span>`;
    element.innerHTML = `
      <span class="tm-line" aria-hidden="true"></span>
      <span class="tm-stem tm-stem-upper" aria-hidden="true"></span>
      <span class="tm-stem tm-stem-lower" aria-hidden="true"></span>
      <span class="tm-dot" aria-hidden="true"></span>
      <section class="tm-headline-tile" data-region="headline" aria-label="Headline tile">
        <div class="tm-date" data-overflow="date">${escapeHtml(event.date)}</div>
        <div class="tm-rule" aria-hidden="true"></div>
        <div class="tm-headline" data-overflow="headline">${escapeHtml(event.headline)}</div>
      </section>
      <section class="tm-lower" data-region="lower" aria-label="Photo and caption tile">
        <div class="tm-photo" data-region="photo">${photo}</div>
        <div class="tm-accent" data-region="accent" aria-hidden="true"></div>
        <div class="tm-caption" data-overflow="caption" data-region="caption">${escapeHtml(event.caption)}</div>
        <span class="tm-ref">${escapeHtml(event.reference_number || "")}</span>
      </section>
      <span class="tm-warning" title="Preflight issue">!</span>
      ${handles ? `
        <button class="design-handle handle-width" data-handle="width" aria-label="Module width" type="button"></button>
        <button class="design-handle handle-headline" data-handle="headlineHeight" aria-label="Headline height" type="button"></button>
        <button class="design-handle handle-lower" data-handle="lowerHeight" aria-label="Lower tile height" type="button"></button>
        <button class="design-handle handle-photo" data-handle="photoHeight" aria-label="Photo height" type="button"></button>
        <button class="design-handle handle-inset" data-handle="contentInset" aria-label="Content inset" type="button"></button>` : ""}
    `;
    return element;
  }

  function fixtureOptions() {
    const events = state.events;
    const byLength = key => events.reduce((best, item) => String(item[key] || "").length > String(best[key] || "").length ? item : best, events[0]);
    return [
      { id: "current", label: "Current event", get: selectedEvent },
      { id: "longest-date", label: "Longest date", get: () => byLength("date") },
      { id: "longest-headline", label: "Longest headline", get: () => byLength("headline") },
      { id: "longest-caption", label: "Longest caption", get: () => byLength("caption") },
      ...state.fixtures.map(fixture => ({ id: fixture.id, label: fixture.label, get: () => fixture }))
    ];
  }

  function activeFixture() {
    return fixtureOptions().find(option => option.id === state.fixtureId)?.get() || selectedEvent();
  }

  function renderFixtureSelect() {
    const select = $("#fixtureSelect");
    const options = fixtureOptions();
    select.innerHTML = options.map(option => `<option value="${escapeHtml(option.id)}">${escapeHtml(option.label)}</option>`).join("");
    select.value = options.some(option => option.id === state.fixtureId) ? state.fixtureId : "current";
  }

  function renderModuleCanvas() {
    const canvas = $("#moduleCanvas");
    canvas.innerHTML = "";
    const module = createModule(activeFixture(), { scale: state.canvasZoom, handles: true, selected: true });
    module.style.top = "39%";
    module.addEventListener("click", handleRegionSelection);
    canvas.append(module);
    bindHandles(module);
    applyRegionSelection(module);
    $("#canvasZoom").value = state.canvasZoom;
    $("#canvasZoomOutput").textContent = `${Math.round(state.canvasZoom / 14 * 100)}%`;
    $(".module-stage").style.setProperty("--grid-size", `${state.canvasZoom}px`);
  }

  function applyRegionSelection(module) {
    $$(`[data-region]`, module).forEach(element => element.classList.toggle("is-selected", element.dataset.region === state.selectedRegion));
    const descriptions = {
      module: ["Module", "Shared width, upper and lower geometry"],
      headline: ["Headline tile", "Date, rule, headline, height and gap"],
      lower: ["Lower tile", "Photo, accent, caption and total height"],
      photo: ["Photo area", "Shared crop window and photo height"],
      accent: ["Accent bar", "Shared height, radius and era color"],
      caption: ["Caption area", "Natural area text using shared type tokens"]
    };
    const [title, detail] = descriptions[state.selectedRegion] || descriptions.module;
    $("#selectionReadout").innerHTML = `<strong>${title}</strong><span>${detail}</span>`;
    const group = ["headline", "caption"].includes(state.selectedRegion) ? "type" : state.selectedRegion === "module" ? "module" : "module";
    $$(`.inspector details`).forEach(element => element.classList.toggle("active-group", element.dataset.group === group));
  }

  function handleRegionSelection(event) {
    const region = event.target.closest("[data-region]")?.dataset.region || "module";
    state.selectedRegion = region;
    applyRegionSelection(event.currentTarget);
  }

  function bindHandles(module) {
    $$(`[data-handle]`, module).forEach(handle => {
      handle.addEventListener("keydown", event => {
        const key = handle.dataset.handle;
        const increase = event.key === "ArrowRight" || event.key === "ArrowUp";
        const decrease = event.key === "ArrowLeft" || event.key === "ArrowDown";
        if (!increase && !decrease) return;
        event.preventDefault();
        const limits = {
          width: [8, 24], headlineHeight: [2.5, 10], lowerHeight: [10, 28], photoHeight: [4, 16], contentInset: [.35, 2.5]
        }[key];
        const previous = snapshot(`Resize ${key}`);
        const step = state.tokens.behavior.snapIncrement || .05;
        const value = Math.max(limits[0], Math.min(limits[1], state.tokens.module[key] + (increase ? step : -step)));
        state.tokens.module[key] = Number(value.toFixed(2));
        pushUndo(`Resize ${key}`, previous);
        markDirty();
        renderAll();
      });
      handle.addEventListener("pointerdown", event => {
        event.preventDefault();
        event.stopPropagation();
        const key = handle.dataset.handle;
        const previous = snapshot(`Resize ${key}`);
        const startX = event.clientX;
        const startY = event.clientY;
        const startValue = state.tokens.module[key];
        const scale = state.canvasZoom;
        const snap = state.tokens.behavior.snapIncrement || .05;
        const limits = {
          width: [8, 24], headlineHeight: [2.5, 10], lowerHeight: [10, 28], photoHeight: [4, 16], contentInset: [.35, 2.5]
        }[key];
        handle.setPointerCapture(event.pointerId);
        handle.addEventListener("pointermove", move);
        handle.addEventListener("pointerup", finish, { once: true });

        function move(moveEvent) {
          const delta = key === "width" ? ((moveEvent.clientX - startX) * 2 / scale)
            : key === "contentInset" ? ((moveEvent.clientX - startX) / scale)
              : key === "headlineHeight" ? ((startY - moveEvent.clientY) / scale)
                : ((moveEvent.clientY - startY) / scale);
          let value = Math.round((startValue + delta) / snap) * snap;
          value = Math.max(limits[0], Math.min(limits[1], value));
          state.tokens.module[key] = Number(value.toFixed(2));
          applyLiveModuleToken(key, state.tokens.module[key]);
          markDirty();
        }

        function finish() {
          handle.removeEventListener("pointermove", move);
          if (state.tokens.module[key] !== startValue) pushUndo(`Resize ${key}`, previous);
          renderAll();
        }
      });
    });
  }

  function applyLiveModuleToken(key, value) {
    const cssNames = {
      width: "--module-width",
      headlineHeight: "--headline-height",
      lowerHeight: "--lower-height",
      photoHeight: "--photo-height",
      contentInset: "--inset"
    };
    const cssName = cssNames[key];
    if (!cssName) return;
    $$(".timeline-module").forEach(item => item.style.setProperty(cssName, value));
    const input = $(`[data-token="module.${key}"]`);
    if (input) input.value = value;
    schedulePreflight();
  }

  function layoutPositions() {
    const count = state.events.length;
    const ramp = state.tokens.ramp;
    const pitch = count > 1 ? (ramp.endX - ramp.startX) / (count - 1) : 0;
    const tangent = Math.tan(ramp.angleDegrees * Math.PI / 180);
    return state.events.map((event, index) => {
      const x = ramp.layoutMode === "fixed" ? ramp.startX + index * state.tokens.module.width * 1.18 : ramp.startX + index * pitch;
      const y = ramp.startY + (x - ramp.startX) * tangent;
      return { event, index, x, y };
    });
  }

  function addRampSegments(container, scale, unit) {
    const positions = layoutPositions();
    if (!positions.length) return;
    for (let era = 0; era < 4; era++) {
      const members = positions.filter(item => Number(item.event.era) === era);
      if (!members.length) continue;
      const first = members[0];
      const last = members.at(-1);
      const pad = positions.length > 1 ? Math.abs(positions[1].x - positions[0].x) / 2 : state.tokens.module.width / 2;
      const startX = Math.max(0, first.x - pad);
      const endX = Math.min(state.tokens.document.width, last.x + pad);
      const startY = state.tokens.ramp.startY + (startX - state.tokens.ramp.startX) * Math.tan(state.tokens.ramp.angleDegrees * Math.PI / 180);
      const dx = endX - startX;
      const dy = dx * Math.tan(state.tokens.ramp.angleDegrees * Math.PI / 180);
      const length = Math.hypot(dx, dy);
      const line = document.createElement("div");
      line.className = "ramp-segment";
      line.style.cssText = `left:${startX * scale}${unit};top:${startY * scale}${unit};width:${length * scale}${unit};background:${state.tokens.colors.eras[era]};transform:rotate(${state.tokens.ramp.angleDegrees}deg)`;
      container.append(line);

      const label = document.createElement("div");
      label.className = "era-label-card";
      const centerX = (first.x + last.x) / 2;
      const centerY = state.tokens.ramp.startY + (centerX - state.tokens.ramp.startX) * Math.tan(state.tokens.ramp.angleDegrees * Math.PI / 180) - state.tokens.module.headlineGap - state.tokens.module.headlineHeight - 1.1;
      label.style.cssText = `left:${centerX * scale}${unit};top:${centerY * scale}${unit};background:${state.tokens.colors.eras[era]}`;
      label.innerHTML = `${escapeHtml(ERA_NAMES[era])}<small>Era ${era + 1} · ${members.length} events</small>`;
      container.append(label);
    }
  }

  function renderTimeline() {
    const artboard = $("#timelineArtboard");
    const scale = state.timelineZoom;
    artboard.innerHTML = "";
    artboard.style.setProperty("--artboard-width", `${state.tokens.document.width * scale}px`);
    artboard.style.setProperty("--artboard-height", `${state.tokens.document.height * scale}px`);
    addRampSegments(artboard, scale, "px");
    layoutPositions().forEach(({ event, index, x, y }) => {
      const module = createModule(event, { scale, left: x * scale, top: y * scale, index, selected: index === state.selectedIndex });
      module.draggable = true;
      module.addEventListener("click", () => selectEvent(index, true));
      module.addEventListener("dragstart", dragEvent => {
        dragEvent.dataTransfer.effectAllowed = "move";
        dragEvent.dataTransfer.setData("text/plain", String(index));
      });
      module.addEventListener("dragover", dragEvent => {
        dragEvent.preventDefault();
        dragEvent.dataTransfer.dropEffect = "move";
      });
      module.addEventListener("drop", dragEvent => {
        dragEvent.preventDefault();
        const from = Number(dragEvent.dataTransfer.getData("text/plain"));
        if (!Number.isInteger(from) || from === index) return;
        pushUndo("Reorder timeline events");
        const [moved] = state.events.splice(from, 1);
        const destination = from < index ? index - 1 : index;
        state.events.splice(destination, 0, moved);
        state.selectedIndex = destination;
        normalizePositions();
        markDirty();
        renderAll();
      });
      artboard.append(module);
    });
    $("#timelineZoom").value = state.timelineZoom;
    $("#timelineStats").textContent = `${state.events.length} events · 4 eras · ${state.tokens.ramp.angleDegrees}°`;
    $("#timelineArtboard").dataset.eventCount = state.events.length;
    $("#eraLegend").innerHTML = ERA_NAMES.map((name, i) => `<span><i style="background:${state.tokens.colors.eras[i]}"></i>Era ${i + 1} · ${escapeHtml(name)}</span>`).join("");
    schedulePreflight();
  }

  function renderPrintSurface() {
    const surface = $("#printSurface");
    const outputScale = state.tokens.document.outputScale;
    surface.innerHTML = "";
    surface.style.background = state.tokens.colors.paper;
    addRampSegments(surface, outputScale, "in");
    layoutPositions().forEach(({ event, index, x, y }) => {
      surface.append(createModule(event, { scale: outputScale, unit: "in", left: x * outputScale, top: y * outputScale, index }));
    });
  }

  function renderInspector() {
    $$(`[data-token]`).forEach(input => {
      const value = getPath(state.tokens, input.dataset.token);
      if (document.activeElement !== input) input.value = value;
    });
    $("#tokenRevision").textContent = state.tokens.revision || "draft";
  }

  function renderEventSelect() {
    const select = $("#eventSelect");
    select.innerHTML = state.events.map((event, index) => `<option value="${index}">${index + 1}. ${escapeHtml(event.date)} — ${escapeHtml(event.headline)}</option>`).join("");
    select.value = state.selectedIndex;
    $("#eventPosition").textContent = state.selectedIndex + 1;
    $("#eventTotal").textContent = state.events.length;
    $("#moveEarlierButton").disabled = state.selectedIndex === 0;
    $("#moveLaterButton").disabled = state.selectedIndex === state.events.length - 1;
  }

  function renderContentForm() {
    const event = selectedEvent();
    if (!event) return;
    const form = $("#contentForm");
    for (const field of form.elements) {
      if (!field.name || document.activeElement === field) continue;
      field.value = event[field.name] ?? "";
    }
  }

  function renderAll() {
    renderFixtureSelect();
    renderModuleCanvas();
    renderInspector();
    renderEventSelect();
    renderContentForm();
    renderTimeline();
    renderPrintSurface();
    updateUndoButtons();
  }

  function renderWithoutForms() {
    renderModuleCanvas();
    renderInspector();
    renderTimeline();
    renderPrintSurface();
  }

  function selectEvent(index, scroll = false) {
    state.selectedIndex = Math.max(0, Math.min(Number(index), state.events.length - 1));
    if (state.fixtureId === "current") renderModuleCanvas();
    renderEventSelect();
    renderContentForm();
    $$("#timelineArtboard .timeline-module").forEach((module, moduleIndex) => module.dataset.selected = moduleIndex === state.selectedIndex ? "true" : "false");
    if (scroll) $("#contentHeading").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function moveEvent(direction) {
    const target = state.selectedIndex + direction;
    if (target < 0 || target >= state.events.length) return;
    pushUndo(direction < 0 ? "Move event earlier" : "Move event later");
    [state.events[state.selectedIndex], state.events[target]] = [state.events[target], state.events[state.selectedIndex]];
    state.selectedIndex = target;
    normalizePositions();
    markDirty();
    renderAll();
  }

  function normalizePositions() {
    state.events.forEach((event, index) => event.position = index + 1);
  }

  function duplicateEvent() {
    pushUndo("Duplicate event");
    const duplicate = clone(selectedEvent());
    duplicate.id = `event_${Date.now().toString(36)}`;
    duplicate.reference_number = "";
    duplicate.headline = `${duplicate.headline} (copy)`;
    state.events.splice(state.selectedIndex + 1, 0, duplicate);
    state.selectedIndex += 1;
    normalizePositions();
    markDirty();
    renderAll();
  }

  function addEvent() {
    pushUndo("Add event");
    const era = Number(selectedEvent()?.era) || 0;
    const event = { id: `event_${Date.now().toString(36)}`, position: state.events.length + 1, reference_number: "", date: "Year", headline: "New historical milestone", caption: "Add a standalone photograph caption.", photo: "", era, title: "", context: "", sources: [], rights_status: "Unresolved", credit: "", original_pixels: null, print_viability: null };
    state.events.splice(state.selectedIndex + 1, 0, event);
    state.selectedIndex += 1;
    normalizePositions();
    markDirty();
    renderAll();
    $("#contentForm [name=date]").focus();
    $("#contentForm [name=date]").select();
  }

  function deleteEvent() {
    const event = selectedEvent();
    if (!event || state.events.length === 1) return;
    if (!confirm(`Remove “${event.headline}” from this timeline draft? The catalog photograph will not be deleted.`)) return;
    pushUndo("Delete placed event");
    state.events.splice(state.selectedIndex, 1);
    state.selectedIndex = Math.min(state.selectedIndex, state.events.length - 1);
    normalizePositions();
    markDirty();
    renderAll();
  }

  function restoreApproved() {
    if (state.dirty && !confirm("Discard the local designer draft and restore the approved tokens and event content?")) return;
    pushUndo("Restore approved design");
    state.tokens = clone(state.approvedTokens);
    state.events = clone(state.approvedEvents);
    state.selectedIndex = 0;
    state.fixtureId = "current";
    state.dirty = false;
    localStorage.removeItem(STORAGE_KEY);
    renderAll();
    $("#saveLight").className = "status-light saved";
    $("#saveStatus").textContent = "Approved design restored";
    toast("Approved design restored. Undo is available.");
  }

  function schedulePreflight() {
    clearTimeout(state.preflightTimer);
    state.preflightTimer = setTimeout(runPreflight, 120);
  }

  function overflowed(element) {
    return element && (element.scrollHeight > element.clientHeight + 1 || element.scrollWidth > element.clientWidth + 1);
  }

  function runPreflight() {
    const issues = [];
    const positions = layoutPositions();
    const modules = $$("#timelineArtboard .timeline-module");
    const fontReady = document.fonts ? document.fonts.check(`16px "${state.tokens.type.family}"`) : true;
    if (!fontReady) issues.push({ severity: "error", message: `Font “${state.tokens.type.family}” is unavailable in this browser.`, scope: "Design" });

    state.events.forEach((event, index) => {
      const ref = event.reference_number || `Event ${index + 1}`;
      if (!String(event.date).trim()) issues.push({ severity: "error", message: `${ref} has no date.`, scope: ref, index });
      if (!String(event.headline).trim()) issues.push({ severity: "error", message: `${ref} has no headline.`, scope: ref, index });
      if (!String(event.caption).trim()) issues.push({ severity: "error", message: `${ref} has no caption.`, scope: ref, index });
      if (![0, 1, 2, 3].includes(Number(event.era))) issues.push({ severity: "error", message: `${ref} is not assigned to one of the four eras.`, scope: ref, index });
      if (!event.photo) issues.push({ severity: "warning", message: `${ref} has no selected photo.`, scope: ref, index });
      if (!event.rights_status || /unclear|unresolved/i.test(event.rights_status)) issues.push({ severity: "warning", message: `${ref} has unresolved rights status.`, scope: ref, index });
      if (event.print_viability?.classification === "Reference Only") issues.push({ severity: "warning", message: `${ref} is classified Reference Only for print.`, scope: ref, index });

      const module = modules[index];
      ["date", "headline", "caption"].forEach(area => {
        if (overflowed($(`[data-overflow="${area}"]`, module))) issues.push({ severity: "error", message: `${ref} ${area} is overset at the current size.`, scope: ref, index });
      });
      const position = positions[index];
      if (position) {
        const halfWidth = state.tokens.module.width / 2;
        const upper = position.y - state.tokens.module.headlineGap - state.tokens.module.headlineHeight;
        const lower = position.y + state.tokens.module.lowerGap + state.tokens.module.lowerHeight;
        if (position.x - halfWidth < 0 || position.x + halfWidth > state.tokens.document.width || upper < 0 || lower > state.tokens.document.height) {
          issues.push({ severity: "error", message: `${ref} extends outside the 356 × 120 in artboard.`, scope: ref, index });
        }
      }
    });

    for (let era = 0; era < 4; era++) {
      if (!state.events.some(event => Number(event.era) === era)) issues.push({ severity: "error", message: `Era ${era + 1} has no events.`, scope: "Eras" });
    }
    let previousEra = -1;
    state.events.forEach((event, index) => {
      const era = Number(event.era);
      if (era < previousEra) issues.push({ severity: "error", message: `Era sequence is not contiguous near event ${index + 1}.`, scope: "Eras", index });
      previousEra = Math.max(previousEra, era);
    });

    state.issues = issues;
    const errorIndexes = new Set(issues.filter(issue => issue.severity === "error" && Number.isInteger(issue.index)).map(issue => issue.index));
    modules.forEach((module, index) => module.classList.toggle("has-error", errorIndexes.has(index)));
    const errors = issues.filter(issue => issue.severity === "error").length;
    const warnings = issues.filter(issue => issue.severity === "warning").length;
    $("#preflightCount").textContent = errors ? `${errors} error${errors === 1 ? "" : "s"}` : warnings ? `${warnings} warnings` : "Ready";
    $("#preflightButton").classList.toggle("has-errors", Boolean(errors));
    renderPreflightDialog();
    return { errors, warnings };
  }

  function renderPreflightDialog() {
    const errors = state.issues.filter(issue => issue.severity === "error").length;
    const warnings = state.issues.filter(issue => issue.severity === "warning").length;
    const passes = 6 - Number(errors > 0);
    $("#preflightSummary").innerHTML = `<div><strong>${errors}</strong><span>Blocking errors</span></div><div><strong>${warnings}</strong><span>Warnings</span></div><div><strong>${passes}/6</strong><span>Core checks</span></div>`;
    const list = $("#preflightList");
    if (!state.issues.length) {
      list.innerHTML = `<li class="pass"><b>Ready</b><span>No preflight problems found. The current state is ready for print and SVG export.</span></li>`;
    } else {
      list.innerHTML = state.issues.map(issue => `<li class="${issue.severity}"><b>${issue.severity}</b><span>${escapeHtml(issue.message)}</span></li>`).join("");
    }
  }

  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function downloadJson(value, filename) {
    downloadBlob(new Blob([JSON.stringify(value, null, 2)], { type: "application/json" }), filename);
    toast(`Downloaded ${filename}`);
  }

  function exportedContent() {
    return {
      schemaVersion: 1,
      updated: new Date().toISOString(),
      policy: "Designer draft export; catalog records remain separate.",
      milestones: state.events.map((event, index) => ({
        position: index + 1,
        record_id: event.id,
        reference_number: event.reference_number,
        date: event.date,
        headline: event.headline,
        caption: event.caption,
        era: Number(event.era),
        photo: event.photo,
        rights_status: event.rights_status,
        credit: event.credit,
        context: event.context,
        sources: event.sources || []
      }))
    };
  }

  function exportedIllustratorData() {
    const eraLabelWidths = [50, 58, 54, 48];
    const eras = ERA_NAMES.map((label, index) => {
      const members = state.events.filter(event => Number(event.era) === index);
      const firstDate = members[0]?.date || "";
      const lastDate = members.at(-1)?.date || "";
      return {
        id: `era-${index + 1}`,
        label,
        range: firstDate && lastDate && firstDate !== lastDate ? `${firstDate}–${lastDate}` : firstDate,
        color: state.tokens.colors.eras[index],
        labelWidthInches: eraLabelWidths[index]
      };
    });
    return {
      schemaVersion: 1,
      generator: "beaumont-timeline-illustrator",
      exportedAt: new Date().toISOString(),
      document: {
        widthInches: state.tokens.document.width,
        heightInches: state.tokens.document.height,
        outputScale: state.tokens.document.outputScale
      },
      assets: {
        basePath: "",
        missingPhotoPolicy: "keep-placeholder"
      },
      layout: {
        angleDegrees: state.tokens.ramp.angleDegrees,
        startXInches: state.tokens.ramp.startX,
        endXInches: state.tokens.ramp.endX,
        startYInches: state.tokens.ramp.startY,
        moduleOffsetXInches: 0,
        moduleOffsetYInches: 0,
        dotDiameterInches: 0.72,
        dotStrokeWidthInches: 0.08,
        lineWidthInches: 1.05,
        underlayWidthInches: 1.45,
        stemWidthInches: 0.18,
        upperStemLengthInches: state.tokens.module.stemGap,
        lowerStemLengthInches: state.tokens.module.stemGap,
        underlayColor: state.tokens.colors.timeline,
        dotStrokeColor: state.tokens.colors.module,
        labelsEnabled: true,
        labelOffsetYInches: -17,
        labelHeightInches: 4.2,
        labelFontSizeInches: state.tokens.type.headlineSize,
        labelPaddingInches: state.tokens.module.contentInset,
        labelCornerRadiusInches: state.tokens.module.cornerRadius,
        labelTextColor: "#ffffff",
        labelFont: state.tokens.type.family,
        generatedLayerName: "TIMELINE — GENERATED"
      },
      eras,
      events: state.events.map((event, index) => ({
        id: event.id,
        order: index + 1,
        era: `era-${Number(event.era) + 1}`,
        date: event.date,
        headline: event.headline,
        caption: event.caption,
        photo: event.photo,
        reference_number: event.reference_number,
        credit: event.credit,
        rights_status: event.rights_status,
        context: event.context
      }))
    };
  }

  async function contentHash() {
    const payload = new TextEncoder().encode(stableStringify({ tokens: state.tokens, events: state.events }));
    const digest = await crypto.subtle.digest("SHA-256", payload);
    return [...new Uint8Array(digest)].map(byte => byte.toString(16).padStart(2, "0")).join("");
  }

  async function buildManifest() {
    runPreflight();
    return {
      schemaVersion: 1,
      generatedAt: new Date().toISOString(),
      dataRevision: state.baseMilestones?.version || "designer-draft",
      tokenRevision: state.tokens.revision || "designer-draft",
      contentHash: await contentHash(),
      document: {
        fullSizeInches: [state.tokens.document.width, state.tokens.document.height],
        outputScale: state.tokens.document.outputScale,
        outputInches: [state.tokens.document.width * state.tokens.document.outputScale, state.tokens.document.height * state.tokens.document.outputScale]
      },
      ramp: clone(state.tokens.ramp),
      fonts: [`${state.tokens.type.family}, ${state.tokens.type.fallback}`],
      events: state.events.length,
      images: state.events.map(event => ({ recordId: event.id, referenceNumber: event.reference_number, path: event.photo, rightsStatus: event.rights_status })),
      preflight: { blockingErrors: state.issues.filter(issue => issue.severity === "error"), warnings: state.issues.filter(issue => issue.severity === "warning") }
    };
  }

  async function exportManifest() {
    downloadJson(await buildManifest(), "beaumont-timeline-manifest.json");
  }

  async function exportSvg() {
    const { errors } = runPreflight();
    if (errors && !confirm(`Preflight found ${errors} blocking error${errors === 1 ? "" : "s"}. Export the review SVG anyway?`)) return;
    renderPrintSurface();
    const css = await fetch("timeline-designer.css").then(response => response.text());
    const width = state.tokens.document.width * state.tokens.document.outputScale;
    const height = state.tokens.document.height * state.tokens.document.outputScale;
    const compiled = $("#printSurface").cloneNode(true);
    $$(`img`, compiled).forEach(image => image.setAttribute("src", new URL(image.getAttribute("src"), location.href).href));
    const html = compiled.innerHTML;
    const manifest = await buildManifest();
    const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${width}in" height="${height}in" viewBox="0 0 ${width * 96} ${height * 96}">
  <title>Beaumont and San Gorgonio Pass historical timeline</title>
  <metadata>${escapeHtml(JSON.stringify(manifest))}</metadata>
  <foreignObject width="100%" height="100%">
    <div xmlns="http://www.w3.org/1999/xhtml" class="compiled-surface" style="position:relative;width:${width}in;height:${height}in;overflow:hidden;background:${state.tokens.colors.paper};">
      <style>${css.replace(/<\/style/gi, "<\\/style")}</style>
      ${html}
    </div>
  </foreignObject>
</svg>`;
    downloadBlob(new Blob([svg], { type: "image/svg+xml" }), "beaumont-timeline-compiled.svg");
    toast("Compiled SVG downloaded");
  }

  function printTimeline() {
    const { errors } = runPreflight();
    if (errors && !confirm(`Preflight found ${errors} blocking error${errors === 1 ? "" : "s"}. Open the 1:10 print dialog anyway?`)) return;
    renderPrintSurface();
    setTimeout(() => window.print(), 60);
  }

  async function importJson(input, kind) {
    const file = input.files?.[0];
    if (!file) return;
    try {
      const data = JSON.parse(await file.text());
      pushUndo(`Import ${kind}`);
      if (kind === "tokens") {
        if (data.schemaVersion !== 1 || !data.module || !data.type || !data.colors) throw new Error("This is not a compatible token file.");
        state.tokens = data;
      } else {
        const records = data.milestones || data.events;
        if (!Array.isArray(records)) throw new Error("This content file has no milestones array.");
        state.events = records.map((record, index) => ({ ...record, id: record.id || record.record_id || `event_${Date.now().toString(36)}_${index}`, era: Number(record.era ?? assignEra(index)), position: index + 1, photo: record.photo || "", caption: record.caption || "", sources: record.sources || [] }));
        state.selectedIndex = 0;
      }
      markDirty();
      renderAll();
      toast(`${kind === "tokens" ? "Design tokens" : "Timeline content"} imported`);
    } catch (error) {
      alert(`Import failed: ${error.message}`);
    } finally {
      input.value = "";
    }
  }

  function bindUi() {
    $("#undoButton").addEventListener("click", undo);
    $("#redoButton").addEventListener("click", redo);
    $("#restoreButton").addEventListener("click", restoreApproved);
    $("#preflightButton").addEventListener("click", () => { runPreflight(); $("#preflightDialog").showModal(); });
    $("#fixtureSelect").addEventListener("change", event => { state.fixtureId = event.target.value; renderModuleCanvas(); });
    $("#canvasZoom").addEventListener("input", event => { state.canvasZoom = Number(event.target.value); renderModuleCanvas(); });
    $("#timelineZoom").addEventListener("input", event => { state.timelineZoom = Number(event.target.value); renderTimeline(); });
    $("#fitTimelineButton").addEventListener("click", () => {
      const width = $("#timelineScroll").clientWidth - 52;
      state.timelineZoom = Math.max(2.4, Math.min(6.5, Number((width / state.tokens.document.width).toFixed(1))));
      renderTimeline();
      $("#timelineScroll").scrollTo({ left: 0, top: 0, behavior: "smooth" });
    });
    $("#eventSelect").addEventListener("change", event => selectEvent(event.target.value));
    $("#moveEarlierButton").addEventListener("click", () => moveEvent(-1));
    $("#moveLaterButton").addEventListener("click", () => moveEvent(1));
    $("#duplicateEventButton").addEventListener("click", duplicateEvent);
    $("#addEventButton").addEventListener("click", addEvent);
    $("#deleteEventButton").addEventListener("click", deleteEvent);

    $$(`[data-token]`).forEach(input => {
      let inputStart = null;
      input.addEventListener("focus", () => inputStart = snapshot(`Change ${input.dataset.token}`));
      const applyTokenInput = () => {
        const value = input.type === "number" ? Number(input.value) : input.value;
        setPath(state.tokens, input.dataset.token, value);
        state.tokens.revision = `draft-${new Date().toISOString().slice(0, 10)}`;
        markDirty();
        renderWithoutForms();
      };
      input.addEventListener("input", applyTokenInput);
      input.addEventListener("change", () => {
        applyTokenInput();
        pushUndoIfChanged(`Change ${input.dataset.token}`, inputStart);
        inputStart = null;
      });
      input.addEventListener("blur", () => {
        pushUndoIfChanged(`Change ${input.dataset.token}`, inputStart);
        inputStart = null;
      });
    });

    const form = $("#contentForm");
    $$(`[name]`, form).forEach(field => {
      let contentStart = null;
      if (field.name === "id") return;
      field.addEventListener("focus", () => contentStart = snapshot(`Edit ${field.name}`));
      field.addEventListener("blur", () => {
        pushUndoIfChanged(`Edit ${field.name}`, contentStart);
        contentStart = null;
      });
      field.addEventListener("change", () => {
        pushUndoIfChanged(`Edit ${field.name}`, contentStart);
        contentStart = null;
      });
    });
    form.addEventListener("input", event => {
      const field = event.target;
      if (!field.name || field.name === "id") return;
      selectedEvent()[field.name] = field.name === "era" ? Number(field.value) : field.value;
      markDirty();
      renderModuleCanvas();
      renderTimeline();
      renderEventSelect();
    });

    $("#exportTokensButton").addEventListener("click", () => downloadJson(state.tokens, "beaumont-timeline-design-tokens.json"));
    $("#exportIllustratorButton").addEventListener("click", () => downloadJson(exportedIllustratorData(), "beaumont-timeline-illustrator.json"));
    $("#exportContentButton").addEventListener("click", () => downloadJson(exportedContent(), "beaumont-timeline-content.json"));
    $("#importTokensInput").addEventListener("change", event => importJson(event.target, "tokens"));
    $("#importContentInput").addEventListener("change", event => importJson(event.target, "content"));
    $("#exportManifestButton").addEventListener("click", exportManifest);
    $("#exportSvgButton").addEventListener("click", exportSvg);
    $("#printButton").addEventListener("click", printTimeline);

    document.addEventListener("keydown", event => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "z") {
        event.preventDefault();
        event.shiftKey ? redo() : undo();
      }
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "y") {
        event.preventDefault(); redo();
      }
    });
  }

  async function init() {
    try {
      const [tokens, milestones, catalog, fixtureData] = await Promise.all([
        fetch("data/timeline-design-tokens.json").then(response => response.json()),
        fetch("data/timeline-milestones.json").then(response => response.json()),
        fetch("data/catalog.json").then(response => response.json()),
        fetch("data/timeline-preview-fixtures.json").then(response => response.json())
      ]);
      state.approvedTokens = clone(tokens);
      state.tokens = clone(tokens);
      state.baseMilestones = milestones;
      state.approvedEvents = buildEvents(milestones, catalog);
      state.events = clone(state.approvedEvents);
      state.fixtures = fixtureData.fixtures || [];
      state.canvasZoom = tokens.behavior?.canvasZoom || 14;
      state.timelineZoom = tokens.behavior?.timelineZoom || 3.8;
      const draftTime = loadDraft();
      bindUi();
      renderAll();
      if (draftTime) {
        $("#saveLight").className = "status-light saved";
        $("#saveStatus").textContent = `Local draft restored from ${new Date(draftTime).toLocaleString()}`;
        toast("Your local designer draft was restored");
      } else {
        $("#saveLight").className = "status-light saved";
        $("#saveStatus").textContent = "Approved design loaded";
      }
    } catch (error) {
      console.error(error);
      $("#saveLight").className = "status-light dirty";
      $("#saveStatus").textContent = "The designer could not load its source data";
      document.body.insertAdjacentHTML("beforeend", `<div class="toast show">Designer failed to load: ${escapeHtml(error.message)}</div>`);
    }
  }

  init();
})();
