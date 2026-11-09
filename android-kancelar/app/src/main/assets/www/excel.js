'use strict';
/* Editor sešitů Excel (tabulková mřížka + řádek vzorců). */

const ROW_CHUNK = 200;

const SheetEditor = {
  wb: null,
  sheet: null,       // název aktuálního listu
  sel: { r: 0, c: 0 },
  engine: null,
  live: false,       // po první úpravě se vzorce přepočítávají
  undoStack: [],
  redoStack: [],
  renderedRows: 0,
  lastFind: '',

  init() {
    const grid = $('#grid');
    let lastTap = { addr: null, t: 0 };
    grid.addEventListener('click', e => {
      const td = e.target.closest('td');
      if (td) {
        const r = +td.parentElement.dataset.r, c = +td.dataset.c;
        const addr = r + ':' + c;
        const now = Date.now();
        const second = lastTap.addr === addr && now - lastTap.t < 3000;
        lastTap = { addr, t: now };
        SheetEditor.select(r, c);
        if (second) SheetEditor.focusInput();
        return;
      }
      const th = e.target.closest('th');
      if (th && th.dataset.c != null) SheetEditor.select(SheetEditor.sel.r, +th.dataset.c);
      else if (th && th.parentElement.dataset.r != null) SheetEditor.select(+th.parentElement.dataset.r, SheetEditor.sel.c);
    });
    $('#gridWrap').addEventListener('scroll', () => {
      const w = $('#gridWrap');
      if (w.scrollTop + w.clientHeight > w.scrollHeight - 400) SheetEditor.renderMoreRows();
    });
    const input = $('#cellInput');
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter') { e.preventDefault(); SheetEditor.commit(1, 0); }
      else if (e.key === 'Tab') { e.preventDefault(); SheetEditor.commit(0, 1); }
      else if (e.key === 'Escape') { SheetEditor.showSelection(); input.blur(); }
    });
    $('#cellOk').addEventListener('click', () => SheetEditor.commit(1, 0));
    $('#sheetToolbar').addEventListener('mousedown', e => { if (e.target.closest('button')) e.preventDefault(); });
    $('#sheetToolbar').addEventListener('click', e => {
      const b = e.target.closest('button');
      if (b && SheetEditor.actions[b.dataset.act]) SheetEditor.actions[b.dataset.act]();
    });
    // Klávesnice (připojená ke tabletu)
    document.addEventListener('keydown', e => {
      if ($('#sheet').hidden || document.activeElement === input || !$('#modal').hidden) return;
      const mv = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] }[e.key];
      if (mv) { e.preventDefault(); SheetEditor.move(mv[0], mv[1]); }
      else if (e.key === 'Delete' || e.key === 'Backspace') SheetEditor.actions.clear();
      else if (e.key === 'Enter' || e.key === 'F2') SheetEditor.focusInput();
      else if (e.key.length === 1 && !e.ctrlKey && !e.metaKey) { input.value = ''; SheetEditor.focusInput(); }
    });
  },

  /* ---------- Otevření ---------- */
  open(bytes, ext) {
    let wb;
    if (ext === 'csv') {
      // CSV: rozpoznat české „;“ a desetinné čárky
      let text = new TextDecoder('utf-8').decode(bytes);
      if (text.includes('�')) text = new TextDecoder('windows-1250').decode(bytes);
      const firstLine = text.split(/\r?\n/)[0] || '';
      const FS = (firstLine.match(/;/g) || []).length > (firstLine.match(/,/g) || []).length ? ';' : ',';
      wb = XLSX.read(text.replace(/^﻿/, ''), { type: 'string', FS, raw: true });
      for (const name of wb.SheetNames) SheetEditor._convertCsvNumbers(wb.Sheets[name]);
    } else {
      wb = XLSX.read(bytes, { type: 'array', cellStyles: true, cellNF: true, bookVBA: true });
    }
    SheetEditor.setWorkbook(wb);
  },

  _convertCsvNumbers(ws) {
    for (const addr of Object.keys(ws)) {
      if (addr[0] === '!') continue;
      const cell = ws[addr];
      if (cell.t !== 's') continue;
      const v = SheetEditor.parseInput(cell.v, cell);
      if (v && v.t !== 's') { Object.assign(cell, v); delete cell.w; }
    }
  },

  newWorkbook() {
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet([[]]), 'List1');
    SheetEditor.setWorkbook(wb);
  },

  setWorkbook(wb) {
    SheetEditor.wb = wb;
    SheetEditor.live = false;
    SheetEditor.engine = SheetEditor.makeEngine();
    SheetEditor.undoStack = [];
    SheetEditor.redoStack = [];
    const visible = wb.SheetNames.find((n, i) => !(wb.Workbook && wb.Workbook.Sheets && wb.Workbook.Sheets[i] && wb.Workbook.Sheets[i].Hidden));
    SheetEditor.switchSheet(visible || wb.SheetNames[0]);
  },

  makeEngine() {
    const eng = Formula.engine(SheetEditor.wb);
    const orig = eng.value;
    // Dokud uživatel nic nezměnil, věříme hodnotám uloženým Excelem.
    eng.value = (sn, r, c) => {
      if (!SheetEditor.live) {
        const ws = SheetEditor.wb.Sheets[sn];
        const cell = ws && ws[XLSX.utils.encode_cell({ r, c })];
        if (cell && cell.f && cell.v !== undefined && cell.t !== 'z') return Formula.cellValue(cell);
      }
      return orig(sn, r, c);
    };
    return eng;
  },

  get ws() { return SheetEditor.wb.Sheets[SheetEditor.sheet]; },

  usedRange(ws = SheetEditor.ws) {
    if (!ws || !ws['!ref']) return { s: { r: 0, c: 0 }, e: { r: 0, c: 0 } };
    return XLSX.utils.decode_range(ws['!ref']);
  },

  switchSheet(name) {
    SheetEditor.sheet = name;
    SheetEditor.sel = { r: 0, c: 0 };
    SheetEditor.renderTabs();
    SheetEditor.render();
    $('#gridWrap').scrollTop = 0;
    $('#gridWrap').scrollLeft = 0;
  },

  /* ---------- Vykreslení ---------- */
  render() {
    const ws = SheetEditor.ws;
    const used = SheetEditor.usedRange(ws);
    const nCols = Math.min(16384, Math.max(used.e.c + 6, 12));
    SheetEditor.nCols = nCols;
    SheetEditor.nRows = Math.max(used.e.r + 30, 60);
    const grid = $('#grid');
    let html = '<colgroup><col style="width:44px">';
    for (let c = 0; c < nCols; c++) html += '<col style="width:' + SheetEditor.colWidth(c) + 'px">';
    html += '</colgroup><thead><tr><th class="corner"></th>';
    for (let c = 0; c < nCols; c++) html += '<th data-c="' + c + '">' + XLSX.utils.encode_col(c) + '</th>';
    html += '</tr></thead><tbody></tbody>';
    grid.innerHTML = html;
    grid.style.width = (44 + Array.from({ length: nCols }, (_, c) => SheetEditor.colWidth(c)).reduce((a, b) => a + b, 0)) + 'px';
    SheetEditor.renderedRows = 0;
    SheetEditor.renderMoreRows();
    SheetEditor.showSelection();
    SheetEditor.updateStatus();
  },

  colWidth(c) {
    const cols = SheetEditor.ws['!cols'];
    const ci = cols && cols[c];
    if (ci) {
      if (ci.hidden) return 0;
      if (ci.wpx) return Math.max(30, Math.min(400, ci.wpx));
      if (ci.wch) return Math.max(30, Math.min(400, Math.round(ci.wch * 7 + 5)));
      if (ci.width) return Math.max(30, Math.min(400, Math.round(ci.width * 7)));
    }
    return 88;
  },

  renderMoreRows() {
    const tbody = $('#grid tbody');
    if (!tbody) return;
    const start = SheetEditor.renderedRows;
    const end = Math.min(SheetEditor.nRows, start + ROW_CHUNK);
    if (start >= end) {
      // nekonečné posouvání: přidat další prázdné řádky
      if (SheetEditor.nRows < 1048576) { SheetEditor.nRows += 50; return SheetEditor.renderMoreRows(); }
      return;
    }
    let html = '';
    for (let r = start; r < end; r++) html += SheetEditor.rowHtml(r);
    tbody.insertAdjacentHTML('beforeend', html);
    SheetEditor.renderedRows = end;
  },

  rowHtml(r) {
    const ws = SheetEditor.ws;
    const rows = ws['!rows'];
    const hidden = rows && rows[r] && rows[r].hidden;
    let html = '<tr data-r="' + r + '"' + (hidden ? ' hidden' : '') + '><th>' + (r + 1) + '</th>';
    for (let c = 0; c < SheetEditor.nCols; c++) html += SheetEditor.cellHtml(r, c);
    return html + '</tr>';
  },

  cellHtml(r, c) {
    const { text, cls, style } = SheetEditor.display(r, c);
    return '<td data-c="' + c + '"' + (cls ? ' class="' + cls + '"' : '') + (style ? ' style="' + style + '"' : '') + '>' + Util.html(text) + '</td>';
  },

  display(r, c, sheetName = SheetEditor.sheet) {
    const ws = SheetEditor.wb.Sheets[sheetName];
    const cell = ws[XLSX.utils.encode_cell({ r, c })];
    if (!cell) return { text: '', cls: '' };
    const v = cell.f ? SheetEditor.engine.value(sheetName, r, c) : Formula.cellValue(cell);
    let text = '', cls = '';
    if (v instanceof FErr) { text = v.code; cls = 'err'; }
    else if (v === null || v === undefined) text = '';
    else if (typeof v === 'number') { text = SheetEditor.formatNumber(v, cell.z); cls = 'num'; }
    else if (typeof v === 'boolean') { text = v ? 'PRAVDA' : 'NEPRAVDA'; cls = 'bool'; }
    else text = String(v);
    let style = '';
    const s = cell.s;
    if (s) {
      const fg = s.fgColor && s.fgColor.rgb;
      if (s.patternType === 'solid' && fg && /^[0-9A-F]{6}$/i.test(fg.slice(-6)) && fg.slice(-6).toUpperCase() !== 'FFFFFF') style += 'background:#' + fg.slice(-6) + ';color:#111;';
    }
    return { text, cls, style };
  },

  formatNumber(v, z) {
    if (z && z !== 'General') {
      try {
        let s = XLSX.SSF.format(z, v);
        if (!XLSX.SSF.is_date(z)) s = s.replace(/[,.]/g, ch => (ch === ',' ? ' ' : ','));
        return s;
      } catch (e) { /* spadnout na obecný formát */ }
    }
    if (Math.abs(v) >= 1e15 || (Math.abs(v) < 1e-9 && v !== 0)) return v.toExponential(5).replace('.', ',');
    return v.toLocaleString('cs-CZ', { maximumFractionDigits: 10, useGrouping: false });
  },

  /** Text pro řádek vzorců. */
  editText(r, c) {
    const cell = SheetEditor.ws[XLSX.utils.encode_cell({ r, c })];
    if (!cell) return '';
    if (cell.f) return '=' + cell.f;
    if (cell.t === 'n') {
      if (cell.z && XLSX.SSF.is_date(cell.z)) {
        const d = Formula.serialToDate(cell.v);
        return d.d + '.' + d.m + '.' + d.y;
      }
      if (cell.z && /%/.test(cell.z)) return Formula.fmtNum(cell.v * 100).replace('.', ',') + '%';
      return Formula.fmtNum(cell.v).replace('.', ',');
    }
    if (cell.t === 'b') return cell.v ? 'PRAVDA' : 'NEPRAVDA';
    if (cell.t === 'e') return cell.w || '';
    if (cell.t === 'd') return new Date(cell.v).toLocaleDateString('cs-CZ');
    const s = cell.v == null ? '' : String(cell.v);
    // text, který vypadá jako číslo, chránit apostrofem
    const parsed = SheetEditor.parseInput(s, {});
    return parsed && parsed.t !== 's' ? "'" + s : s;
  },

  /** Rozpozná zadanou hodnotu. Vrací {t, v, f?, z?} nebo null (smazat). */
  parseInput(text, prev) {
    if (text === '' || text == null) return null;
    if (text[0] === "'") return { t: 's', v: text.slice(1) };
    if (text[0] === '=' && text.length > 1) {
      return { t: 'n', v: 0, f: Formula.normalize(text.slice(1)) };
    }
    const t = text.trim();
    let m = /^([-+]?)(\d{1,3}(?:[  ]\d{3})+|\d+)(?:[.,](\d+))?$/.exec(t);
    if (m) {
      const n = parseFloat(m[1] + m[2].replace(/[  ]/g, '') + (m[3] ? '.' + m[3] : ''));
      const z = prev && prev.z && !XLSX.SSF.is_date(prev.z) && !/%/.test(prev.z) ? prev.z : undefined;
      return { t: 'n', v: n, z };
    }
    m = /^([-+]?\d+(?:[.,]\d+)?)\s?%$/.exec(t);
    if (m) return { t: 'n', v: parseFloat(m[1].replace(',', '.')) / 100, z: /[.,]/.test(m[1]) ? '0.00%' : '0%' };
    m = /^(\d{1,2})\.\s?(\d{1,2})\.\s?(\d{4})$/.exec(t);
    if (m) {
      const serial = (Date.UTC(+m[3], +m[2] - 1, +m[1]) - Date.UTC(1899, 11, 30)) / 86400000;
      return { t: 'n', v: serial, z: prev && prev.z && XLSX.SSF.is_date(prev.z) ? prev.z : 'd.m.yyyy' };
    }
    const up = t.toUpperCase();
    if (up === 'PRAVDA' || up === 'TRUE') return { t: 'b', v: true };
    if (up === 'NEPRAVDA' || up === 'FALSE') return { t: 'b', v: false };
    return { t: 's', v: text };
  },

  /* ---------- Výběr ---------- */
  select(r, c, scroll = true) {
    r = Math.max(0, r); c = Math.max(0, Math.min(SheetEditor.nCols - 1, c));
    while (r >= SheetEditor.renderedRows) SheetEditor.renderMoreRows();
    SheetEditor.sel = { r, c };
    SheetEditor.showSelection(scroll);
  },

  move(dr, dc) { SheetEditor.select(SheetEditor.sel.r + dr, SheetEditor.sel.c + dc); },

  tdAt(r, c) {
    const tr = $('#grid tbody').children[r];
    return tr ? tr.children[c + 1] : null;
  },

  showSelection(scroll = true) {
    $$('#grid td.sel').forEach(td => td.classList.remove('sel'));
    $$('#grid th.hl').forEach(th => th.classList.remove('hl'));
    const { r, c } = SheetEditor.sel;
    const td = SheetEditor.tdAt(r, c);
    if (td) {
      td.classList.add('sel');
      td.parentElement.firstElementChild.classList.add('hl');
      const h = $('#grid thead tr').children[c + 1];
      if (h) h.classList.add('hl');
      if (scroll) {
        const w = $('#gridWrap');
        const top = td.offsetTop, left = td.offsetLeft;
        if (top - 28 < w.scrollTop) w.scrollTop = top - 28;
        else if (top + td.offsetHeight > w.scrollTop + w.clientHeight) w.scrollTop = top + td.offsetHeight - w.clientHeight;
        if (left - 44 < w.scrollLeft) w.scrollLeft = left - 44;
        else if (left + td.offsetWidth > w.scrollLeft + w.clientWidth) w.scrollLeft = left + td.offsetWidth - w.clientWidth;
      }
    }
    $('#cellName').textContent = XLSX.utils.encode_cell({ r, c });
    $('#cellInput').value = SheetEditor.editText(r, c);
    SheetEditor.updateStatus();
  },

  focusInput() {
    const inp = $('#cellInput');
    inp.focus();
    const n = inp.value.length;
    inp.setSelectionRange(n, n);
  },

  updateStatus() {
    const ws = SheetEditor.ws;
    const { r, c } = SheetEditor.sel;
    const cell = ws[XLSX.utils.encode_cell({ r, c })];
    let s = '';
    if (cell && cell.f) {
      const v = SheetEditor.engine.value(SheetEditor.sheet, r, c);
      s = 'Výsledek: ' + (v instanceof FErr ? v.code : (typeof v === 'number' ? SheetEditor.formatNumber(v, cell.z) : Formula.str(v)));
    } else {
      // součet čísel ve sloupci
      const used = SheetEditor.usedRange(ws);
      let sum = 0, cnt = 0;
      for (let rr = used.s.r; rr <= used.e.r; rr++) {
        const v = SheetEditor.engine.value(SheetEditor.sheet, rr, c);
        if (typeof v === 'number') { sum += v; cnt++; }
      }
      s = cnt ? 'Sloupec ' + XLSX.utils.encode_col(c) + ': součet ' + SheetEditor.formatNumber(sum) + ' · průměr ' + SheetEditor.formatNumber(sum / cnt) + ' · počet ' + cnt : '';
    }
    $('#status').textContent = s;
  },

  /* ---------- Úpravy ---------- */
  snapshot() {
    SheetEditor.undoStack.push({ sheet: SheetEditor.sheet, ws: structuredClone(SheetEditor.ws), sel: { ...SheetEditor.sel }, all: null });
    if (SheetEditor.undoStack.length > 60) SheetEditor.undoStack.shift();
    SheetEditor.redoStack = [];
  },

  /** Snímek celého sešitu (pro operace měnící vzorce na všech listech). */
  snapshotAll() {
    const all = {};
    for (const n of SheetEditor.wb.SheetNames) all[n] = structuredClone(SheetEditor.wb.Sheets[n]);
    SheetEditor.undoStack.push({ sheet: SheetEditor.sheet, all, names: [...SheetEditor.wb.SheetNames], sel: { ...SheetEditor.sel } });
    if (SheetEditor.undoStack.length > 30) SheetEditor.undoStack.shift();
    SheetEditor.redoStack = [];
  },

  _restore(entry, pushTo) {
    const wb = SheetEditor.wb;
    if (entry.all) {
      const cur = {};
      for (const n of wb.SheetNames) cur[n] = wb.Sheets[n];
      pushTo.push({ sheet: SheetEditor.sheet, all: cur, names: [...wb.SheetNames], sel: { ...SheetEditor.sel } });
      wb.SheetNames.length = 0;
      wb.SheetNames.push(...entry.names);
      wb.Sheets = {};
      for (const n of entry.names) wb.Sheets[n] = entry.all[n];
    } else {
      pushTo.push({ sheet: entry.sheet, ws: wb.Sheets[entry.sheet], sel: { ...SheetEditor.sel } });
      wb.Sheets[entry.sheet] = entry.ws;
    }
    SheetEditor.changed();
    SheetEditor.sheet = wb.SheetNames.includes(entry.sheet) ? entry.sheet : wb.SheetNames[0];
    SheetEditor.renderTabs();
    SheetEditor.render();
    SheetEditor.select(entry.sel.r, entry.sel.c);
  },

  changed() {
    SheetEditor.live = true;
    SheetEditor.engine.reset();
    App.setDirty(true);
  },

  setCell(r, c, parsed) {
    const ws = SheetEditor.ws;
    const addr = XLSX.utils.encode_cell({ r, c });
    const prev = ws[addr];
    if (!parsed) {
      if (prev && prev.s) ws[addr] = { t: 'z', s: prev.s };
      else delete ws[addr];
    } else {
      const cell = { t: parsed.t, v: parsed.v };
      if (parsed.f) cell.f = parsed.f;
      const z = parsed.z !== undefined ? parsed.z : (prev && prev.z);
      if (z) cell.z = z;
      if (prev && prev.s) cell.s = prev.s;
      ws[addr] = cell;
    }
    SheetEditor.extendRef(r, c);
  },

  extendRef(r, c) {
    const ws = SheetEditor.ws;
    const range = ws['!ref'] ? XLSX.utils.decode_range(ws['!ref']) : { s: { r, c }, e: { r, c } };
    range.s.r = Math.min(range.s.r, r); range.s.c = Math.min(range.s.c, c);
    range.e.r = Math.max(range.e.r, r); range.e.c = Math.max(range.e.c, c);
    ws['!ref'] = XLSX.utils.encode_range(range);
  },

  commit(dr, dc) {
    const { r, c } = SheetEditor.sel;
    const text = $('#cellInput').value;
    if (text !== SheetEditor.editText(r, c)) {
      const prev = SheetEditor.ws[XLSX.utils.encode_cell({ r, c })];
      const parsed = SheetEditor.parseInput(text, prev || {});
      if (parsed && parsed.f) {
        try { Formula.parse(parsed.f); } catch (e) {
          if (!(e instanceof Unsupported)) { UI.toast('Chyba ve vzorci'); return; }
        }
      }
      SheetEditor.snapshot();
      SheetEditor.setCell(r, c, parsed);
      SheetEditor.changed();
      const used = SheetEditor.usedRange();
      if (used.e.c >= SheetEditor.nCols - 2) { SheetEditor.render(); }
      else SheetEditor.refreshCells();
    }
    SheetEditor.select(r + dr, c + dc);
    if (dr || dc) SheetEditor.focusInput();
  },

  /** Přepočítá a překreslí viditelné buňky (po změně hodnot). */
  refreshCells() {
    const tbody = $('#grid tbody');
    const ws = SheetEditor.ws;
    for (let r = 0; r < SheetEditor.renderedRows; r++) {
      const tr = tbody.children[r];
      for (let c = 0; c < SheetEditor.nCols; c++) {
        const td = tr.children[c + 1];
        const cell = ws[XLSX.utils.encode_cell({ r, c })];
        if (!cell && !td.textContent) continue;
        const { text, cls, style } = SheetEditor.display(r, c);
        if (td.textContent !== text) td.textContent = text;
        const sel = td.classList.contains('sel');
        td.className = (cls || '') + (sel ? ' sel' : '');
        td.setAttribute('style', style || '');
      }
    }
    SheetEditor.updateStatus();
  },

  /** Posune buňky listu (vložení/odstranění řádku či sloupce). */
  shiftCells(axis, at, delta) {
    const wb = SheetEditor.wb;
    const name = SheetEditor.sheet;
    const ws = SheetEditor.ws;
    const out = {};
    for (const key of Object.keys(ws)) {
      if (key[0] === '!') { out[key] = ws[key]; continue; }
      const a = XLSX.utils.decode_cell(key);
      let { r, c } = a;
      const idx = axis === 'row' ? r : c;
      if (delta < 0 && idx >= at && idx < at - delta) continue; // smazané
      if (idx >= at) { if (axis === 'row') r += delta; else c += delta; }
      out[XLSX.utils.encode_cell({ r, c })] = ws[key];
    }
    // rozsah
    if (ws['!ref']) {
      const rg = XLSX.utils.decode_range(ws['!ref']);
      if (axis === 'row') rg.e.r = Math.max(rg.s.r, rg.e.r + delta); else rg.e.c = Math.max(rg.s.c, rg.e.c + delta);
      out['!ref'] = XLSX.utils.encode_range(rg);
    }
    // sloučené buňky
    if (ws['!merges']) {
      out['!merges'] = ws['!merges'].map(m => {
        const n = { s: { ...m.s }, e: { ...m.e } };
        const k = axis === 'row' ? 'r' : 'c';
        if (n.s[k] >= at) n.s[k] = Math.max(at, n.s[k] + delta);
        if (n.e[k] >= at) n.e[k] = Math.max(n.s[k], n.e[k] + delta);
        return n;
      }).filter(m => m.e.r > m.s.r || m.e.c > m.s.c);
    }
    const dims = axis === 'row' ? '!rows' : '!cols';
    if (ws[dims]) {
      const arr = ws[dims].slice();
      if (delta > 0) arr.splice(at, 0, ...Array(delta).fill(undefined));
      else arr.splice(at, -delta);
      out[dims] = arr;
    }
    wb.Sheets[name] = out;
    // upravit vzorce ve všech listech
    for (const sn of wb.SheetNames) {
      const s = wb.Sheets[sn];
      for (const key of Object.keys(s)) {
        if (key[0] === '!' || !s[key].f) continue;
        s[key].f = Formula.shift(s[key].f, sn, name, axis, at, delta);
      }
    }
  },

  async sort(desc) {
    const ws = SheetEditor.ws;
    const used = SheetEditor.usedRange(ws);
    if (used.e.r - used.s.r < 1) return;
    const r = await UI.dialog({
      text: 'Seřadit řádky podle sloupce ' + XLSX.utils.encode_col(SheetEditor.sel.c) + (desc ? ' sestupně' : ' vzestupně') + '.\nObsahuje první řádek záhlaví?',
      buttons: [{ label: 'Zrušit', value: null }, { label: 'Bez záhlaví', value: 'no' }, { label: 'Se záhlavím', value: 'yes', primary: true }],
    });
    if (!r.value) return;
    SheetEditor.snapshot();
    const startRow = used.s.r + (r.value === 'yes' ? 1 : 0);
    const col = SheetEditor.sel.c;
    const rows = [];
    for (let rr = startRow; rr <= used.e.r; rr++) {
      const cellsOfRow = {};
      for (let c = used.s.c; c <= used.e.c; c++) {
        const a = XLSX.utils.encode_cell({ r: rr, c });
        if (ws[a]) cellsOfRow[c] = ws[a];
      }
      rows.push({ key: SheetEditor.engine.value(SheetEditor.sheet, rr, col), cells: cellsOfRow });
    }
    rows.sort((a, b) => {
      const x = a.key, y = b.key;
      const empty = v => v === null || v === '' || v === undefined;
      if (empty(x) && empty(y)) return 0;
      if (empty(x)) return 1;   // prázdné vždy na konec
      if (empty(y)) return -1;
      let cmp;
      if (typeof x === 'number' && typeof y === 'number') cmp = x - y;
      else if (typeof x === 'number') cmp = -1;
      else if (typeof y === 'number') cmp = 1;
      else cmp = Formula.str(x).localeCompare(Formula.str(y), 'cs', { numeric: true, sensitivity: 'base' });
      return desc ? -cmp : cmp;
    });
    rows.forEach((row, i) => {
      const rr = startRow + i;
      for (let c = used.s.c; c <= used.e.c; c++) {
        const a = XLSX.utils.encode_cell({ r: rr, c });
        if (row.cells[c]) ws[a] = row.cells[c]; else delete ws[a];
      }
    });
    SheetEditor.changed();
    SheetEditor.render();
  },

  async find() {
    const q = await UI.prompt('Hledat v listu', SheetEditor.lastFind, { ok: 'Hledat' });
    if (!q) return;
    SheetEditor.lastFind = q;
    const needle = q.toLocaleLowerCase('cs');
    const used = SheetEditor.usedRange();
    const { r: sr, c: sc } = SheetEditor.sel;
    const total = (used.e.r + 1) * (used.e.c + 1);
    const w = used.e.c + 1;
    let start = sr * w + sc;
    for (let k = 1; k <= total; k++) {
      const idx = (start + k) % total;
      const r = Math.floor(idx / w), c = idx % w;
      const { text } = SheetEditor.display(r, c);
      if (text && text.toLocaleLowerCase('cs').includes(needle)) {
        SheetEditor.select(r, c);
        const td = SheetEditor.tdAt(r, c);
        if (td) { td.classList.add('found'); setTimeout(() => td.classList.remove('found'), 1500); }
        return;
      }
    }
    UI.toast('Nenalezeno');
  },

  actions: {
    undo() {
      const e = SheetEditor.undoStack.pop();
      if (!e) { UI.toast('Není co vrátit'); return; }
      SheetEditor._restore(e, SheetEditor.redoStack);
    },
    redo() {
      const e = SheetEditor.redoStack.pop();
      if (!e) return;
      SheetEditor._restore(e, SheetEditor.undoStack);
    },
    rowAbove() {
      SheetEditor.snapshotAll();
      SheetEditor.shiftCells('row', SheetEditor.sel.r, 1);
      SheetEditor.changed(); SheetEditor.render();
    },
    colLeft() {
      SheetEditor.snapshotAll();
      SheetEditor.shiftCells('col', SheetEditor.sel.c, 1);
      SheetEditor.changed(); SheetEditor.render();
    },
    async rowDel() {
      if (!(await UI.confirm('Smazat řádek ' + (SheetEditor.sel.r + 1) + '?', 'Smazat'))) return;
      SheetEditor.snapshotAll();
      SheetEditor.shiftCells('row', SheetEditor.sel.r, -1);
      SheetEditor.changed(); SheetEditor.render();
    },
    async colDel() {
      if (!(await UI.confirm('Smazat sloupec ' + XLSX.utils.encode_col(SheetEditor.sel.c) + '?', 'Smazat'))) return;
      SheetEditor.snapshotAll();
      SheetEditor.shiftCells('col', SheetEditor.sel.c, -1);
      SheetEditor.changed(); SheetEditor.render();
    },
    clear() {
      const { r, c } = SheetEditor.sel;
      if (!SheetEditor.ws[XLSX.utils.encode_cell({ r, c })]) return;
      SheetEditor.snapshot();
      SheetEditor.setCell(r, c, null);
      SheetEditor.changed();
      SheetEditor.refreshCells();
      SheetEditor.showSelection(false);
    },
    sortAsc() { SheetEditor.sort(false); },
    sortDesc() { SheetEditor.sort(true); },
    sum() {
      const { r, c } = SheetEditor.sel;
      const isNum = (rr, cc) => typeof SheetEditor.engine.value(SheetEditor.sheet, rr, cc) === 'number';
      let f = null;
      let top = r - 1;
      while (top >= 0 && isNum(top, c)) top--;
      if (top < r - 1) f = 'SUM(' + XLSX.utils.encode_cell({ r: top + 1, c }) + ':' + XLSX.utils.encode_cell({ r: r - 1, c }) + ')';
      else {
        let left = c - 1;
        while (left >= 0 && isNum(r, left)) left--;
        if (left < c - 1) f = 'SUM(' + XLSX.utils.encode_cell({ r, c: left + 1 }) + ':' + XLSX.utils.encode_cell({ r, c: c - 1 }) + ')';
      }
      $('#cellInput').value = '=' + (f || 'SUM()');
      if (f) SheetEditor.commit(0, 0);
      else SheetEditor.focusInput();
    },
    find() { SheetEditor.find(); },
  },

  /* ---------- Listy ---------- */
  renderTabs() {
    const tabs = $('#tabs');
    tabs.innerHTML = '';
    const wb = SheetEditor.wb;
    wb.SheetNames.forEach((name, i) => {
      if (wb.Workbook && wb.Workbook.Sheets && wb.Workbook.Sheets[i] && wb.Workbook.Sheets[i].Hidden) return;
      const b = document.createElement('button');
      b.textContent = name;
      if (name === SheetEditor.sheet) b.className = 'active';
      b.onclick = () => { if (name === SheetEditor.sheet) SheetEditor.sheetMenu(name); else SheetEditor.switchSheet(name); };
      b.oncontextmenu = e => { e.preventDefault(); SheetEditor.sheetMenu(name); };
      tabs.appendChild(b);
    });
    const add = document.createElement('button');
    add.className = 'add';
    add.textContent = '+';
    add.title = 'Přidat list';
    add.onclick = () => SheetEditor.addSheet();
    tabs.appendChild(add);
    const active = tabs.querySelector('.active');
    if (active) active.scrollIntoView({ inline: 'nearest', block: 'nearest' });
  },

  async addSheet() {
    const wb = SheetEditor.wb;
    let i = wb.SheetNames.length + 1;
    while (wb.SheetNames.includes('List' + i)) i++;
    SheetEditor.snapshotAll();
    XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet([[]]), 'List' + i);
    SheetEditor.changed();
    SheetEditor.switchSheet('List' + i);
  },

  async sheetMenu(name) {
    const r = await UI.dialog({
      text: 'List „' + name + '“',
      buttons: [{ label: 'Smazat', value: 'del', danger: true }, { label: 'Zavřít', value: null }, { label: 'Přejmenovat', value: 'ren', primary: true }],
    });
    const wb = SheetEditor.wb;
    if (r.value === 'ren') {
      const nn = await UI.prompt('Nový název listu', name);
      if (!nn || nn === name) return;
      if (/[\\/?*[\]:]/.test(nn) || nn.length > 31) { UI.toast('Neplatný název listu'); return; }
      if (wb.SheetNames.includes(nn)) { UI.toast('List s tímto názvem již existuje'); return; }
      SheetEditor.snapshotAll();
      const idx = wb.SheetNames.indexOf(name);
      wb.SheetNames[idx] = nn;
      wb.Sheets[nn] = wb.Sheets[name];
      delete wb.Sheets[name];
      // přejmenovat odkazy ve vzorcích
      const q = s => (/^[A-Za-z_][A-Za-z0-9_.]*$/.test(s) ? s : "'" + s.replace(/'/g, "''") + "'");
      for (const sn of wb.SheetNames) {
        const s = wb.Sheets[sn];
        for (const key of Object.keys(s)) {
          if (key[0] === '!' || !s[key].f) continue;
          s[key].f = Formula.tokenize(s[key].f).map(t => {
            if (t.type !== 'ref' || !t.text.includes('!')) return t.text;
            const ref = t.text.slice(t.text.lastIndexOf('!') + 1);
            const sheetRaw = t.text.slice(0, t.text.lastIndexOf('!'));
            const sheet = sheetRaw.startsWith("'") ? sheetRaw.slice(1, -1).replace(/''/g, "'") : sheetRaw;
            return sheet === name ? q(nn) + '!' + ref : t.text;
          }).join('');
        }
      }
      if (SheetEditor.sheet === name) SheetEditor.sheet = nn;
      SheetEditor.changed();
      SheetEditor.renderTabs();
    } else if (r.value === 'del') {
      if (wb.SheetNames.length <= 1) { UI.toast('Sešit musí mít alespoň jeden list'); return; }
      if (!(await UI.confirm('Opravdu smazat list „' + name + '“?', 'Smazat'))) return;
      SheetEditor.snapshotAll();
      const idx = wb.SheetNames.indexOf(name);
      wb.SheetNames.splice(idx, 1);
      delete wb.Sheets[name];
      if (wb.Workbook && wb.Workbook.Sheets) wb.Workbook.Sheets.splice(idx, 1);
      SheetEditor.changed();
      SheetEditor.switchSheet(wb.SheetNames[Math.max(0, idx - 1)]);
    }
  },

  /* ---------- Uložení ---------- */
  /** Zapíše vypočtené hodnoty vzorců do buněk, aby je ostatní programy zobrazily. */
  bakeFormulaValues() {
    const wb = SheetEditor.wb;
    for (const sn of wb.SheetNames) {
      const ws = wb.Sheets[sn];
      for (const key of Object.keys(ws)) {
        if (key[0] === '!') continue;
        const cell = ws[key];
        if (!cell.f) continue;
        const { r, c } = XLSX.utils.decode_cell(key);
        const v = SheetEditor.engine.value(sn, r, c);
        delete cell.w;
        if (v instanceof FErr) { cell.t = 'e'; cell.v = { '#NULL!': 0, '#DIV/0!': 7, '#VALUE!': 15, '#REF!': 23, '#NAME?': 29, '#NUM!': 36, '#N/A': 42 }[v.code] || 15; cell.w = v.code; }
        else if (typeof v === 'number') { cell.t = 'n'; cell.v = v; }
        else if (typeof v === 'boolean') { cell.t = 'b'; cell.v = v; }
        else if (v === null) { cell.t = 'n'; cell.v = 0; }
        else { cell.t = 's'; cell.v = String(v); }
      }
    }
  },

  getBytes(ext) {
    if (document.activeElement === $('#cellInput')) SheetEditor.commit(0, 0);
    SheetEditor.bakeFormulaValues();
    const bookType = { xlsx: 'xlsx', xlsm: 'xlsm', xls: 'biff8', ods: 'ods', csv: 'csv' }[ext] || 'xlsx';
    if (bookType === 'csv') {
      const csv = XLSX.utils.sheet_to_csv(SheetEditor.ws, { FS: ';' });
      return new TextEncoder().encode('﻿' + csv);
    }
    const out = XLSX.write(SheetEditor.wb, { type: 'array', bookType, compression: true, bookVBA: bookType === 'xlsm' });
    return new Uint8Array(out);
  },
};
