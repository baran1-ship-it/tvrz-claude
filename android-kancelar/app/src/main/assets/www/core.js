'use strict';
/* Společné pomůcky: DOM, dialogy, převody dat a most k Androidu. */

// Starší WebView (Android 7/8 bez aktualizace) nemá structuredClone
if (typeof window.structuredClone !== 'function') {
  window.structuredClone = v => JSON.parse(JSON.stringify(v));
}

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

const Util = {
  bytesToBase64(bytes) {
    const u8 = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
    let out = '';
    const CH = 0x8000;
    for (let i = 0; i < u8.length; i += CH) {
      out += String.fromCharCode.apply(null, u8.subarray(i, i + CH));
    }
    return btoa(out);
  },
  base64ToBytes(b64) {
    const bin = atob(b64);
    const u8 = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
    return u8;
  },
  xml(s) {
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      // znaky, které XML 1.0 nedovoluje
      .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F￾￿]/g, '');
  },
  html(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  },
  ext(name) {
    const m = /\.([^.]+)$/.exec(name || '');
    return m ? m[1].toLowerCase() : '';
  },
  baseName(name) {
    return (name || '').replace(/\.[^.]+$/, '');
  },
  fmtDate(t) {
    const d = new Date(t);
    return d.toLocaleDateString('cs-CZ') + ' ' + d.toLocaleTimeString('cs-CZ', { hour: '2-digit', minute: '2-digit' });
  },
};

/* ---------- Dialogy ---------- */
const UI = {
  _modalResolve: null,

  dialog({ text = '', fields = [], buttons = [{ label: 'OK', value: true, primary: true }] }) {
    return new Promise(resolve => {
      const modal = $('#modal');
      $('#modalText').textContent = text;
      const fbox = $('#modalFields');
      fbox.innerHTML = '';
      const inputs = fields.map(f => {
        if (f.label) {
          const l = document.createElement('label');
          l.textContent = f.label;
          fbox.appendChild(l);
        }
        const inp = document.createElement('input');
        inp.type = f.type || 'text';
        inp.value = f.value != null ? f.value : '';
        if (f.placeholder) inp.placeholder = f.placeholder;
        if (f.min != null) inp.min = f.min;
        if (f.max != null) inp.max = f.max;
        fbox.appendChild(inp);
        return inp;
      });
      const bbox = $('#modalButtons');
      bbox.innerHTML = '';
      const finish = value => {
        modal.hidden = true;
        UI._modalResolve = null;
        resolve({ value, fields: inputs.map(i => i.value) });
      };
      buttons.forEach(b => {
        const btn = document.createElement('button');
        btn.textContent = b.label;
        if (b.primary) btn.className = 'primary';
        if (b.danger) btn.className = 'danger';
        btn.onclick = () => finish(b.value);
        bbox.appendChild(btn);
      });
      inputs.forEach(inp => inp.addEventListener('keydown', e => {
        if (e.key === 'Enter') { const p = buttons.find(b => b.primary); finish(p ? p.value : true); }
      }));
      UI._modalResolve = () => finish(null);
      modal.hidden = false;
      if (inputs[0]) setTimeout(() => { inputs[0].focus(); inputs[0].select(); }, 50);
    });
  },

  async confirm(text, okLabel = 'OK', cancelLabel = 'Zrušit') {
    const r = await UI.dialog({ text, buttons: [{ label: cancelLabel, value: false }, { label: okLabel, value: true, primary: true }] });
    return r.value === true;
  },

  async prompt(text, value = '', opts = {}) {
    const r = await UI.dialog({
      text,
      fields: [{ value, type: opts.type, placeholder: opts.placeholder }],
      buttons: [{ label: 'Zrušit', value: false }, { label: opts.ok || 'OK', value: true, primary: true }],
    });
    return r.value === true ? r.fields[0] : null;
  },

  closeModal() {
    if (UI._modalResolve) { UI._modalResolve(); return true; }
    return false;
  },

  toast(msg, ms = 2400) {
    const t = $('#toast');
    t.textContent = msg;
    t.hidden = false;
    clearTimeout(UI._toastT);
    UI._toastT = setTimeout(() => { t.hidden = true; }, ms);
  },

  busy(on) { $('#busy').hidden = !on; },
};

/* ---------- Most k systému (Android / prohlížeč) ---------- */
const Platform = {
  isAndroid: typeof window.Android !== 'undefined',
  _saveAsResolve: null,

  pickFile() {
    if (Platform.isAndroid) {
      window.Android.pickFile();
    } else {
      const inp = $('#fileInput');
      inp.value = '';
      inp.onchange = async () => {
        const f = inp.files[0];
        if (!f) return;
        const buf = await f.arrayBuffer();
        App.openFile({ name: f.name, uri: null, persistent: false, bytes: new Uint8Array(buf) });
      };
      inp.click();
    }
  },

  openUri(uri) {
    if (Platform.isAndroid) window.Android.openUri(uri);
  },

  /** Zapíše přímo do původního souboru. */
  saveInPlace(uri, bytes) {
    if (!Platform.isAndroid || !uri) return false;
    return window.Android.save(uri, Util.bytesToBase64(bytes)) === true;
  },

  /** Nechá vybrat umístění. Vrací {ok, uri, name}. */
  saveAs(name, mime, bytes) {
    if (Platform.isAndroid) {
      return new Promise(resolve => {
        Platform._saveAsResolve = resolve;
        window.Android.saveAs(name, mime, Util.bytesToBase64(bytes));
      });
    }
    // Prohlížeč: stáhnout soubor
    const blob = new Blob([bytes], { type: mime });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = name;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
    return Promise.resolve({ ok: true, uri: null, name });
  },

  exit() {
    if (Platform.isAndroid) window.Android.exitApp();
  },
};

const MIME = {
  docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  xlsm: 'application/vnd.ms-excel.sheet.macroEnabled.12',
  xls: 'application/vnd.ms-excel',
  ods: 'application/vnd.oasis.opendocument.spreadsheet',
  csv: 'text/csv',
};
