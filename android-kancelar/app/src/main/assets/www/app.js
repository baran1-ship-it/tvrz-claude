'use strict';
/* Řízení aplikace: obrazovky, otevírání, ukládání, nedávné soubory. */

const RECENT_KEY = 'kancelar.recent';

const App = {
  file: null,    // { name, uri, persistent, kind: 'word'|'excel', ext }
  dirty: false,
  screen: 'home',

  init() {
    WordEditor.init();
    SheetEditor.init();
    $('#btnOpen').onclick = () => Platform.pickFile();
    $('#btnNewDoc').onclick = () => App.newFile('word');
    $('#btnNewSheet').onclick = () => App.newFile('excel');
    $('#btnBack').onclick = () => App.goHome();
    $('#btnSave').onclick = () => App.save(false);
    $('#btnMode').onclick = () => { WordEditor.setEditing(!WordEditor.editing); };
    $('#btnMenu').onclick = e => { e.stopPropagation(); App.toggleMenu(); };
    document.addEventListener('click', e => {
      if (!$('#menu').hidden && !e.target.closest('#menu')) $('#menu').hidden = true;
    });
    $('#modal').addEventListener('click', e => { if (e.target.id === 'modal') UI.closeModal(); });
    App.renderRecent();
    // Rychlé uložení Ctrl+S (klávesnice u tabletu)
    document.addEventListener('keydown', e => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's' && App.screen !== 'home') { e.preventDefault(); App.save(false); }
    });
    // V Androidu mohl soubor přijít dřív, než se stránka načetla
    if (Platform.isAndroid) App.onFileReady();
  },

  /* ---------- Callbacky z Androidu ---------- */
  onFileReady() {
    const json = window.Android.takeFile();
    if (!json) return;
    const f = JSON.parse(json);
    App.openFile({ name: f.name, uri: f.uri, persistent: f.persistent, bytes: Util.base64ToBytes(f.data) });
  },

  onOpenFailed(uri) {
    // Soubor ze seznamu nedávných již neexistuje / chybí oprávnění
    App.removeRecent(uri);
  },

  onSavedAs(ok, uri, name) {
    const res = Platform._saveAsResolve;
    Platform._saveAsResolve = null;
    if (res) res({ ok, uri, name });
  },

  /** Systémové tlačítko Zpět. Vrací true, pokud bylo obslouženo. */
  onBack() {
    if (UI.closeModal()) return true;
    if (!$('#menu').hidden) { $('#menu').hidden = true; return true; }
    if (App.screen === 'word' && WordEditor.editing) { WordEditor.setEditing(false); return true; }
    if (App.screen !== 'home') { App.goHome(); return true; }
    return false;
  },

  /* ---------- Otevírání ---------- */
  async openFile({ name, uri, persistent, bytes }) {
    if (App.screen !== 'home' && App.dirty) {
      if (!(await App.confirmDiscard())) return;
    }
    const ext = Util.ext(name);
    const kind = ext === 'docx' || ext === 'docm' || ext === 'dotx' ? 'word'
      : ['xlsx', 'xlsm', 'xls', 'ods', 'csv', 'xltx'].includes(ext) ? 'excel'
      : App.sniff(bytes);
    if (!kind) {
      UI.dialog({ text: 'Tento typ souboru není podporován.\n\nPodporované formáty: .docx, .xlsx, .xlsm, .xls, .ods, .csv.\n(Starý formát Word .doc lze nejdřív převést na .docx.)' });
      return;
    }
    UI.busy(true);
    await new Promise(r => setTimeout(r, 30));
    try {
      if (kind === 'word') await WordEditor.open(bytes);
      else SheetEditor.open(bytes, ext || 'xlsx');
    } catch (err) {
      console.error(err);
      UI.busy(false);
      UI.dialog({ text: 'Soubor se nepodařilo otevřít.\n\n' + (err && err.message ? err.message : err) });
      return;
    }
    UI.busy(false);
    const realExt = ext || (kind === 'word' ? 'docx' : 'xlsx');
    App.file = { name: name || ('soubor.' + realExt), uri, persistent, kind, ext: realExt };
    App.showScreen(kind);
    App.setDirty(false);
    if (uri && persistent) App.addRecent(App.file);
  },

  /** Rozpoznání typu podle obsahu (soubory bez přípony z e-mailu apod.). */
  sniff(bytes) {
    if (bytes[0] === 0x50 && bytes[1] === 0x4B) {
      const s = new TextDecoder('latin1').decode(bytes.subarray(0, Math.min(bytes.length, 4000)));
      if (s.includes('word/')) return 'word';
      if (s.includes('xl/') || s.includes('content.xml')) return 'excel';
    }
    if (bytes[0] === 0xD0 && bytes[1] === 0xCF) return 'excel'; // starý .xls (může být i .doc)
    return null;
  },

  newFile(kind) {
    App.file = { name: kind === 'word' ? 'Dokument.docx' : 'Tabulka.xlsx', uri: null, persistent: false, kind, ext: kind === 'word' ? 'docx' : 'xlsx', isNew: true };
    App.showScreen(kind); // nejdřív zobrazit – skrytý editor nemůže dostat fokus
    if (kind === 'word') WordEditor.newDocument();
    else SheetEditor.newWorkbook();
    App.setDirty(false);
    if (kind === 'excel') setTimeout(() => SheetEditor.focusInput(), 100);
  },

  showScreen(name) {
    App.screen = name;
    $('#home').hidden = name !== 'home';
    $('#word').hidden = name !== 'word';
    $('#sheet').hidden = name !== 'excel';
    document.body.classList.toggle('excel', name === 'excel');
    const inEditor = name !== 'home';
    $('#btnBack').hidden = !inEditor;
    $('#btnSave').hidden = !inEditor;
    $('#btnMenu').hidden = !inEditor;
    $('#btnMode').hidden = name !== 'word';
    $('#menu').hidden = true;
    App.updateTitle();
    if (name === 'home') App.renderRecent();
  },

  async goHome() {
    if (App.dirty && !(await App.confirmDiscard())) return;
    if (App.screen === 'word') WordEditor.setEditing(false);
    App.file = null;
    App.dirty = false;
    App.showScreen('home');
  },

  async confirmDiscard() {
    const r = await UI.dialog({
      text: 'Dokument obsahuje neuložené změny.',
      buttons: [{ label: 'Zahodit', value: 'discard', danger: true }, { label: 'Zrušit', value: null }, { label: 'Uložit', value: 'save', primary: true }],
    });
    if (r.value === 'discard') return true;
    if (r.value === 'save') return App.save(false);
    return false;
  },

  setDirty(d) {
    App.dirty = d;
    App.updateTitle();
  },

  updateTitle() {
    const t = $('#title');
    if (App.screen === 'home' || !App.file) { t.textContent = 'Kancelář'; return; }
    t.textContent = (App.dirty ? '• ' : '') + App.file.name;
  },

  /* ---------- Ukládání ---------- */
  async save(asNew) {
    if (!App.file) return false;
    const f = App.file;
    let bytes;
    UI.busy(true);
    await new Promise(r => setTimeout(r, 30));
    try {
      bytes = f.kind === 'word' ? await WordEditor.getBytes() : SheetEditor.getBytes(f.ext);
    } catch (err) {
      console.error(err);
      UI.busy(false);
      UI.dialog({ text: 'Uložení se nezdařilo:\n' + (err && err.message ? err.message : err) });
      return false;
    }
    UI.busy(false);
    if (f.ext === 'csv' && SheetEditor.wb.SheetNames.length > 1 && !asNew) {
      UI.toast('CSV uloží jen aktuální list');
    }
    if (!asNew && f.uri && Platform.saveInPlace(f.uri, bytes)) {
      App.setDirty(false);
      UI.toast('Uloženo');
      if (f.kind === 'word') WordEditor.original = bytes;
      return true;
    }
    // Uložit jako… (nový soubor nebo zdroj bez práva zápisu)
    const mime = MIME[f.ext] || MIME.xlsx;
    const res = await Platform.saveAs(f.name, mime, bytes);
    if (!res.ok) {
      if (res.uri !== null || res.name !== null) UI.dialog({ text: 'Soubor se nepodařilo zapsat.' });
      return false;
    }
    if (res.uri) {
      const newExt = Util.ext(res.name) || f.ext;
      App.file = Object.assign({}, f, { uri: res.uri, name: res.name || f.name, persistent: true, isNew: false, ext: newExt });
      App.addRecent(App.file);
    }
    if (f.kind === 'word') WordEditor.original = bytes;
    App.setDirty(false);
    UI.toast('Uloženo');
    return true;
  },

  async saveAsFormat(ext) {
    const f = App.file;
    const old = f.ext;
    f.ext = ext;
    const oldName = f.name;
    f.name = Util.baseName(f.name) + '.' + ext;
    const oldUri = f.uri;
    f.uri = null;
    const ok = await App.save(true);
    if (!ok) { f.ext = old; f.name = oldName; f.uri = oldUri; }
  },

  /* ---------- Menu ---------- */
  toggleMenu() {
    const m = $('#menu');
    if (!m.hidden) { m.hidden = true; return; }
    const items = [];
    items.push(['Uložit', () => App.save(false)]);
    items.push(['Uložit jako…', () => App.save(true)]);
    if (App.file.kind === 'word') {
      items.push(['Hledat…', () => WordEditor.find()]);
      if (WordEditor.lastFind) items.push(['Najít další', () => WordEditor.findNext(WordEditor.lastFind)]);
      items.push(['Zvětšit písmo', () => WordEditor.zoom(0.15)]);
      items.push(['Zmenšit písmo', () => WordEditor.zoom(-0.15)]);
      items.push(['Statistika', () => WordEditor.stats()]);
      if (Platform.isAndroid && window.Android.print) items.push(['Tisk / PDF…', () => window.Android.print(App.file.name)]);
    } else {
      items.push(['Hledat…', () => SheetEditor.find()]);
      items.push(['Uložit jako Excel (.xlsx)', () => App.saveAsFormat('xlsx')]);
      items.push(['Uložit jako CSV (aktuální list)', () => App.saveAsFormat('csv')]);
      items.push(['Uložit jako OpenDocument (.ods)', () => App.saveAsFormat('ods')]);
      items.push(['Nápověda ke vzorcům', () => App.formulaHelp()]);
    }
    items.push(['Zavřít soubor', () => App.goHome()]);
    m.innerHTML = '';
    for (const [label, fn] of items) {
      const b = document.createElement('button');
      b.textContent = label;
      b.onclick = () => { m.hidden = true; fn(); };
      m.appendChild(b);
    }
    m.hidden = false;
  },

  formulaHelp() {
    UI.dialog({
      text: 'Vzorec začíná znakem „=“, např. =A1+B1 nebo =SUMA(A1:A10).\n\n' +
        'Lze psát české i anglické názvy a oddělovat argumenty „;“ nebo „,“.\n\n' +
        'Podporované funkce: SUMA/SUM, PRŮMĚR/AVERAGE, MIN, MAX, POČET/COUNT, POČET2/COUNTA, KDYŽ/IF, IFERROR, ' +
        'A/AND, NEBO/OR, NE/NOT, ZAOKROUHLIT/ROUND, ZAOKR.NAHORU, ZAOKR.DOLŮ, CELÁ.ČÁST/INT, ABS, MOD, MOCNINA, ODMOCNINA, ' +
        'SOUČIN, MEDIAN, SUMIF, COUNTIF, AVERAGEIF, SOUČIN.SKALÁRNÍ, SVYHLEDAT/VLOOKUP, VVYHLEDAT, POZVYHLEDAT/MATCH, INDEX, ' +
        'CONCATENATE, ZLEVA, ZPRAVA, ČÁST, DÉLKA, VELKÁ, MALÁ, PROČISTIT, HODNOTA, HODNOTA.NA.TEXT, DNES, NYNÍ, ROK, MĚSÍC, DEN.\n\n' +
        'Ostatní vzorce ze souboru zůstanou zachovány s poslední hodnotou z Excelu.',
    });
  },

  /* ---------- Nedávné soubory ---------- */
  getRecent() {
    try { return JSON.parse(localStorage.getItem(RECENT_KEY)) || []; } catch (e) { return []; }
  },
  setRecent(list) {
    try { localStorage.setItem(RECENT_KEY, JSON.stringify(list.slice(0, 20))); } catch (e) { /* ignore */ }
  },
  addRecent(f) {
    const list = App.getRecent().filter(x => x.uri !== f.uri);
    list.unshift({ name: f.name, uri: f.uri, kind: f.kind, t: Date.now() });
    App.setRecent(list);
  },
  removeRecent(uri) {
    App.setRecent(App.getRecent().filter(x => x.uri !== uri));
    App.renderRecent();
  },
  renderRecent() {
    const list = App.getRecent();
    const ul = $('#recent');
    ul.innerHTML = '';
    $('#recentTitle').hidden = !list.length;
    ul.hidden = !list.length;
    for (const it of list) {
      const li = document.createElement('li');
      li.innerHTML = '<span class="badge ' + (it.kind === 'word' ? 'word">W' : 'excel">X') + '</span>' +
        '<span class="name"><div>' + Util.html(it.name) + '</div><small>' + Util.fmtDate(it.t) + '</small></span>' +
        '<button class="del" title="Odebrat ze seznamu">×</button>';
      li.onclick = e => {
        if (e.target.closest('.del')) { App.removeRecent(it.uri); return; }
        Platform.openUri(it.uri);
      };
      ul.appendChild(li);
    }
  },
};

window.App = App;
document.addEventListener('DOMContentLoaded', App.init);
