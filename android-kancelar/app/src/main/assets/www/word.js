'use strict';
/* Editor dokumentů Word. */

const WordEditor = {
  original: null,   // bajty původního .docx (kvůli zachování záhlaví, stylů...)
  editing: false,
  savedRange: null,
  fontScale: 1,

  init() {
    const doc = $('#doc');
    try { document.execCommand('defaultParagraphSeparator', false, 'p'); } catch (e) { /* starší WebView */ }
    const tb = $('#wordToolbar');

    // Tlačítka nesmí vzít fokus editoru (jinak se ztratí výběr).
    tb.addEventListener('mousedown', e => {
      if (e.target.closest('button')) e.preventDefault();
    });
    tb.addEventListener('click', e => {
      const b = e.target.closest('button');
      if (!b) return;
      WordEditor.restoreSelection();
      if (b.dataset.cmd === 'insertOrderedList' || b.dataset.cmd === 'insertUnorderedList') {
        WordEditor.toggleList(b.dataset.cmd === 'insertOrderedList' ? 'OL' : 'UL');
        WordEditor.changed();
      } else if (b.dataset.cmd) {
        document.execCommand('styleWithCSS', false, false);
        document.execCommand(b.dataset.cmd, false, null);
        WordEditor.changed();
      } else if (b.dataset.act === 'table') {
        WordEditor.insertTable();
      } else if (b.dataset.act === 'link') {
        WordEditor.insertLink();
      }
      WordEditor.updateToolbar();
    });
    $('#blockStyle').addEventListener('change', e => {
      WordEditor.restoreSelection();
      document.execCommand('formatBlock', false, e.target.value);
      WordEditor.changed();
      doc.focus();
    });
    const color = (inp, cmd) => {
      inp.addEventListener('input', () => {
        WordEditor.restoreSelection();
        document.execCommand('styleWithCSS', false, true);
        document.execCommand(cmd, false, inp.value);
        document.execCommand('styleWithCSS', false, false);
        inp.parentElement.style.color = cmd === 'foreColor' ? inp.value : '';
        WordEditor.changed();
      });
      // na mobilu se výběr ztratí při otevření dialogu barvy
      inp.addEventListener('pointerdown', () => WordEditor.saveSelection());
    };
    color($('#foreColor'), 'foreColor');
    color($('#hiliteColor'), 'hiliteColor');

    doc.addEventListener('input', () => { WordEditor.saveSelection(); WordEditor.changed(); });
    // Výběr ukládat i při opuštění editoru (select, výběr barvy, dialog)
    for (const ev of ['blur', 'keyup', 'mouseup', 'touchend']) doc.addEventListener(ev, () => WordEditor.saveSelection());
    $('#blockStyle').addEventListener('pointerdown', () => WordEditor.saveSelection());
    document.addEventListener('selectionchange', () => {
      if (!WordEditor.editing) return;
      const sel = window.getSelection();
      if (sel.rangeCount && doc.contains(sel.anchorNode)) {
        WordEditor.savedRange = sel.getRangeAt(0).cloneRange();
        WordEditor.updateToolbar();
      }
    });
    // Klepnutí na odkaz v režimu čtení otevře odkaz
    doc.addEventListener('click', e => {
      const a = e.target.closest('a');
      if (a && !WordEditor.editing && a.getAttribute('href')) {
        e.preventDefault();
        const href = a.getAttribute('href');
        if (href.startsWith('#')) return;
        window.location.href = href; // Android předá prohlížeči
      }
    });
    // Vložení: jen čistý text nebo jednoduché HTML bez cizích stylů stránek
    doc.addEventListener('paste', e => {
      const html = e.clipboardData && e.clipboardData.getData('text/html');
      if (html) {
        e.preventDefault();
        document.execCommand('insertHTML', false, WordEditor.sanitize(html));
      }
    });
  },

  sanitize(html) {
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    tmp.querySelectorAll('script,style,meta,link,title,iframe,object').forEach(n => n.remove());
    tmp.querySelectorAll('*').forEach(el => {
      for (const a of Array.from(el.attributes)) {
        if (!/^(href|src|colspan|rowspan|style|width|height)$/.test(a.name) || /^on/i.test(a.name)) el.removeAttribute(a.name);
      }
      if (el.hasAttribute('href') && /^\s*javascript:/i.test(el.getAttribute('href'))) el.removeAttribute('href');
      if (el.style) {
        const keep = {};
        for (const p of ['color', 'background-color', 'font-weight', 'font-style', 'text-decoration', 'text-align']) {
          const v = el.style.getPropertyValue(p);
          if (v) keep[p] = v;
        }
        el.removeAttribute('style');
        for (const [k, v] of Object.entries(keep)) el.style.setProperty(k, v);
      }
    });
    return tmp.innerHTML;
  },

  async open(bytes) {
    WordEditor.original = bytes;
    let html;
    try {
      html = (await Docx.toHtml(bytes)).html;
    } catch (err) {
      console.warn('Vlastní převod selhal, používám mammoth', err);
      const r = await mammoth.convertToHtml({ arrayBuffer: bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) });
      html = r.value;
    }
    WordEditor.show(html);
    WordEditor.setEditing(false);
  },

  newDocument() {
    WordEditor.original = null;
    WordEditor.show('<p><br></p>');
    WordEditor.setEditing(true);
  },

  show(html) {
    const doc = $('#doc');
    WordEditor.savedRange = null;
    doc.innerHTML = html;
    // Obrázky nesmí přetékat; zachovat poměr
    doc.querySelectorAll('img').forEach(img => { img.style.maxWidth = '100%'; img.style.height = 'auto'; });
    $('#wordScroll').scrollTop = 0;
    WordEditor.applyScale();
  },

  setEditing(on) {
    WordEditor.editing = on;
    const doc = $('#doc');
    doc.contentEditable = on ? 'true' : 'false';
    $('#wordToolbar').hidden = !on;
    const btn = $('#btnMode');
    btn.classList.toggle('on', on);
    btn.title = on ? 'Režim čtení' : 'Upravit';
    if (on) doc.focus(); else doc.blur();
  },

  changed() { App.setDirty(true); },

  saveSelection() {
    const sel = window.getSelection();
    if (sel.rangeCount && $('#doc').contains(sel.anchorNode)) WordEditor.savedRange = sel.getRangeAt(0).cloneRange();
  },

  restoreSelection() {
    const doc = $('#doc');
    const sel = window.getSelection();
    // Editor má fokus i platný výběr -> ten je aktuální
    if (document.activeElement === doc && sel.rangeCount && doc.contains(sel.anchorNode)) return;
    doc.focus();
    if (WordEditor.savedRange && doc.contains(WordEditor.savedRange.startContainer)) {
      sel.removeAllRanges();
      sel.addRange(WordEditor.savedRange);
    }
  },

  updateToolbar() {
    for (const b of $$('#wordToolbar button[data-cmd]')) {
      const c = b.dataset.cmd;
      if (/^(bold|italic|underline|strikeThrough|insertUnorderedList|insertOrderedList|justifyLeft|justifyCenter|justifyRight|justifyFull)$/.test(c)) {
        let on = false;
        try { on = document.queryCommandState(c); } catch (e) { /* ignore */ }
        b.classList.toggle('on', on);
      }
    }
    const sel = window.getSelection();
    let node = sel.anchorNode;
    if (node && node.nodeType === 3) node = node.parentNode;
    const block = node && node.closest ? node.closest('h1,h2,h3,h4,h5,h6,p,li,td') : null;
    const v = block && /^H[1-4]$/.test(block.tagName) ? block.tagName.toLowerCase() : 'p';
    $('#blockStyle').value = v;
  },

  /** Vlastní přepínání seznamů (execCommand v Chrome tvoří neplatné <p><ol> a ztrácí kurzor). */
  toggleList(tag) {
    const doc = $('#doc');
    const sel = window.getSelection();
    if (!sel.rangeCount || !doc.contains(sel.anchorNode)) return;
    const range = sel.getRangeAt(0);
    const saved = [range.startContainer, range.startOffset, range.endContainer, range.endOffset];
    const blockOf = n => {
      let el = n.nodeType === 3 ? n.parentNode : n;
      if (el === doc) el = doc.childNodes[Math.min(n === doc ? range.startOffset : 0, doc.childNodes.length - 1)] || doc;
      const b = el.closest && el.closest('li,p,h1,h2,h3,h4,h5,h6,div,blockquote,pre');
      return b && doc.contains(b) && b !== doc ? b : null;
    };
    let first = blockOf(range.startContainer);
    let last = blockOf(range.endContainer) || first;
    if (!first) {
      // holý text přímo v editoru -> zabalit do odstavce
      const p = document.createElement('p');
      doc.insertBefore(p, doc.firstChild);
      while (p.nextSibling && !(p.nextSibling.nodeType === 1 && /^(P|H\d|UL|OL|TABLE|DIV)$/.test(p.nextSibling.tagName))) p.appendChild(p.nextSibling);
      first = last = p;
    }
    if (first.tagName === 'LI') {
      const list = first.parentElement;
      if (list.tagName === tag) {
        // zrušit seznam: položky -> odstavce
        const frag = document.createDocumentFragment();
        for (const li of Array.from(list.children)) {
          const p = document.createElement('p');
          while (li.firstChild) p.appendChild(li.firstChild);
          if (!p.firstChild) p.appendChild(document.createElement('br'));
          frag.appendChild(p);
        }
        list.replaceWith(frag);
      } else {
        const nl = document.createElement(tag);
        while (list.firstChild) nl.appendChild(list.firstChild);
        list.replaceWith(nl);
      }
    } else {
      // posloupnost bloků od first po last (sourozenci)
      if (last.parentNode !== first.parentNode) last = first;
      const blocks = [];
      for (let n = first; n; n = n.nextSibling) {
        if (n.nodeType === 1) blocks.push(n);
        if (n === last) break;
      }
      const list = document.createElement(tag);
      first.parentNode.insertBefore(list, first);
      for (const b of blocks) {
        const li = document.createElement('li');
        while (b.firstChild) li.appendChild(b.firstChild);
        if (!li.firstChild) li.appendChild(document.createElement('br'));
        list.appendChild(li);
        b.remove();
      }
    }
    try {
      const r = document.createRange();
      r.setStart(saved[0], saved[1]);
      r.setEnd(saved[2], saved[3]);
      sel.removeAllRanges();
      sel.addRange(r);
    } catch (e) { /* kurzor nelze obnovit */ }
  },

  async insertTable() {
    WordEditor.saveSelection();
    const r = await UI.dialog({
      text: 'Vložit tabulku',
      fields: [{ label: 'Počet řádků', type: 'number', value: 3, min: 1, max: 100 }, { label: 'Počet sloupců', type: 'number', value: 3, min: 1, max: 20 }],
      buttons: [{ label: 'Zrušit', value: false }, { label: 'Vložit', value: true, primary: true }],
    });
    if (r.value !== true) return;
    const rows = Math.max(1, Math.min(100, +r.fields[0] || 1));
    const cols = Math.max(1, Math.min(20, +r.fields[1] || 1));
    let html = '<table><tbody>';
    for (let i = 0; i < rows; i++) {
      html += '<tr>';
      for (let j = 0; j < cols; j++) html += '<td><br></td>';
      html += '</tr>';
    }
    html += '</tbody></table><p><br></p>';
    WordEditor.restoreSelection();
    document.execCommand('insertHTML', false, html);
    WordEditor.changed();
  },

  async insertLink() {
    WordEditor.saveSelection();
    const url = await UI.prompt('Adresa odkazu', 'https://', { type: 'url' });
    if (!url) return;
    WordEditor.restoreSelection();
    const sel = window.getSelection();
    if (sel.isCollapsed) {
      document.execCommand('insertHTML', false, '<a href="' + Util.html(url) + '">' + Util.html(url) + '</a>');
    } else {
      document.execCommand('createLink', false, url);
    }
    WordEditor.changed();
  },

  /** Najde text a označí ho. */
  async find() {
    const q = await UI.prompt('Hledat v dokumentu', WordEditor.lastFind || '', { ok: 'Hledat' });
    if (!q) return;
    WordEditor.lastFind = q;
    WordEditor.findNext(q);
  },

  findNext(q) {
    const doc = $('#doc');
    const sel = window.getSelection();
    // začít za aktuálním výběrem
    let start = null;
    if (sel.rangeCount && doc.contains(sel.anchorNode)) start = sel.getRangeAt(0);
    const walker = document.createTreeWalker(doc, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    const needle = q.toLocaleLowerCase('cs');
    if (!nodes.length) { UI.toast('Text nenalezen'); return; }
    let si = 0, so = 0;
    if (start) {
      const i = nodes.indexOf(start.endContainer);
      if (i >= 0) { si = i; so = start.endOffset; }
    }
    let hit = null;
    for (let k = 0; k <= nodes.length && !hit; k++) {
      const n = nodes[(si + k) % nodes.length];
      const idx = n.textContent.toLocaleLowerCase('cs').indexOf(needle, k === 0 ? so : 0);
      if (idx >= 0) hit = [n, idx];
    }
    if (!hit) { UI.toast('Text nenalezen'); return; }
    const range = document.createRange();
    range.setStart(hit[0], hit[1]);
    range.setEnd(hit[0], hit[1] + q.length);
    sel.removeAllRanges();
    sel.addRange(range);
    const rect = range.getBoundingClientRect();
    const sc = $('#wordScroll');
    sc.scrollTop += rect.top - sc.getBoundingClientRect().top - sc.clientHeight / 3;
  },

  zoom(delta) {
    WordEditor.fontScale = Math.max(0.6, Math.min(2.2, WordEditor.fontScale + delta));
    WordEditor.applyScale();
  },
  applyScale() {
    $('#doc').style.fontSize = (15 * WordEditor.fontScale) + 'px';
  },

  stats() {
    const text = $('#doc').innerText || '';
    const words = (text.match(/[\p{L}\p{N}]+(?:[-'’][\p{L}\p{N}]+)*/gu) || []).length;
    const chars = text.replace(/\n/g, '').length;
    const noSpace = text.replace(/\s/g, '').length;
    const paras = $$('#doc p, #doc h1, #doc h2, #doc h3, #doc h4, #doc li').filter(p => p.textContent.trim()).length;
    UI.dialog({ text: 'Slova: ' + words + '\nZnaky: ' + chars + '\nZnaky bez mezer: ' + noSpace + '\nOdstavce: ' + paras });
  },

  async getBytes() {
    return Docx.fromHtml($('#doc'), WordEditor.original);
  },
};
