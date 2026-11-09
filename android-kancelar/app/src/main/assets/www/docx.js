'use strict';
/*
 * Převod DOCX <-> HTML.
 *
 * Čtení: vlastní parser word/document.xml (zachová zarovnání, barvy, velikosti,
 * seznamy, tabulky, obrázky, odkazy). Při chybě se použije knihovna mammoth.
 *
 * Zápis: když existuje původní soubor, ponechá se celý balík (záhlaví, zápatí,
 * velikost stránky, písma, styly) a nahradí se jen obsah těla dokumentu.
 */

const W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main';
const R_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships';
const REL_NS = 'http://schemas.openxmlformats.org/package/2006/relationships';

const HL_COLORS = {
  yellow: '#ffff00', green: '#00ff00', cyan: '#00ffff', magenta: '#ff00ff', blue: '#0000ff', red: '#ff0000',
  darkBlue: '#000080', darkCyan: '#008080', darkGreen: '#008000', darkMagenta: '#800080', darkRed: '#800000',
  darkYellow: '#808000', darkGray: '#808080', lightGray: '#c0c0c0', black: '#000000', white: '#ffffff',
};

const Docx = {
  /* ================= ČTENÍ ================= */

  async toHtml(bytes) {
    const zip = await JSZip.loadAsync(bytes);
    const docPath = await Docx._mainDocPath(zip);
    const docXml = await zip.file(docPath).async('string');
    const dir = docPath.replace(/[^/]+$/, '');
    const relsPath = dir + '_rels/' + docPath.slice(dir.length) + '.rels';
    const rels = {};
    if (zip.file(relsPath)) {
      const rx = Docx._parse(await zip.file(relsPath).async('string'));
      for (const r of rx.getElementsByTagNameNS(REL_NS, 'Relationship')) {
        rels[r.getAttribute('Id')] = { target: r.getAttribute('Target'), mode: r.getAttribute('TargetMode'), type: r.getAttribute('Type') };
      }
    }
    // Styly: id -> {heading level, name}
    const styles = { heading: {}, headingIdByLevel: {}, title: null, numPr: {} };
    const stylesPath = dir + 'styles.xml';
    if (zip.file(stylesPath)) {
      const sx = Docx._parse(await zip.file(stylesPath).async('string'));
      const based = {};
      for (const st of sx.getElementsByTagNameNS(W_NS, 'style')) {
        if (st.getAttributeNS(W_NS, 'type') !== 'paragraph') continue;
        const id = st.getAttributeNS(W_NS, 'styleId');
        based[id] = Docx._val(st, 'basedOn');
        const sp = Docx._child(st, 'pPr');
        const snp = sp && Docx._child(sp, 'numPr');
        if (snp) styles.numPr[id] = { numId: Docx._val(snp, 'numId'), ilvl: Docx._val(snp, 'ilvl') };
        const nameEl = Docx._child(st, 'name');
        const name = nameEl ? (nameEl.getAttributeNS(W_NS, 'val') || '').toLowerCase() : '';
        let m = /^heading\s*(\d)$/.exec(name) || /^(?:heading|nadpis)(\d)$/i.exec(id);
        if (m) {
          const lvl = Math.min(6, +m[1]);
          styles.heading[id] = lvl;
          if (!styles.headingIdByLevel[lvl]) styles.headingIdByLevel[lvl] = id;
        } else if (name === 'title') {
          styles.heading[id] = 1;
          styles.title = id;
        }
      }
      // číslování zděděné z nadřazeného stylu
      for (const id of Object.keys(based)) {
        let cur = id, guard = 0;
        while (cur && !styles.numPr[cur] && guard++ < 10) cur = based[cur];
        if (cur && styles.numPr[cur] && !styles.numPr[id]) styles.numPr[id] = styles.numPr[cur];
      }
    }
    // Číslování: numId -> abstract -> lvl -> formát
    const numbering = {};
    const numPath = dir + 'numbering.xml';
    if (zip.file(numPath)) {
      const nx = Docx._parse(await zip.file(numPath).async('string'));
      const abs = {};
      for (const a of nx.getElementsByTagNameNS(W_NS, 'abstractNum')) {
        const levels = {};
        for (const l of Docx._children(a, 'lvl')) {
          const f = Docx._child(l, 'numFmt');
          levels[l.getAttributeNS(W_NS, 'ilvl')] = f ? f.getAttributeNS(W_NS, 'val') : 'decimal';
        }
        abs[a.getAttributeNS(W_NS, 'abstractNumId')] = levels;
      }
      for (const n of Docx._children(nx.documentElement, 'num')) {
        const a = Docx._child(n, 'abstractNumId');
        numbering[n.getAttributeNS(W_NS, 'numId')] = abs[a ? a.getAttributeNS(W_NS, 'val') : ''] || {};
      }
    }
    // Obrázky jako data URI
    const media = {};
    for (const [id, r] of Object.entries(rels)) {
      if (!/\/image$/.test(r.type || '') || r.mode === 'External') continue;
      const p = Docx._resolve(dir, r.target);
      const f = zip.file(p);
      if (!f) continue;
      const ext = Util.ext(p);
      const mime = { png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg', gif: 'image/gif', bmp: 'image/bmp', webp: 'image/webp', svg: 'image/svg+xml' }[ext];
      if (!mime) continue; // emf/wmf prohlížeč neumí
      media[id] = 'data:' + mime + ';base64,' + (await f.async('base64'));
    }

    const ctx = { rels, styles, numbering, media };
    const doc = Docx._parse(docXml);
    const body = doc.getElementsByTagNameNS(W_NS, 'body')[0];
    const html = Docx._blocks(body, ctx);
    return { html: html || '<p><br></p>', meta: { headingIdByLevel: styles.headingIdByLevel } };
  },

  async _mainDocPath(zip) {
    const rootRels = zip.file('_rels/.rels');
    if (rootRels) {
      const rx = Docx._parse(await rootRels.async('string'));
      for (const r of rx.getElementsByTagNameNS(REL_NS, 'Relationship')) {
        if (/\/officeDocument$/.test(r.getAttribute('Type'))) return r.getAttribute('Target').replace(/^\//, '');
      }
    }
    return 'word/document.xml';
  },

  _resolve(dir, target) {
    if (target.startsWith('/')) return target.slice(1);
    const parts = (dir + target).split('/');
    const out = [];
    for (const p of parts) {
      if (p === '..') out.pop(); else if (p && p !== '.') out.push(p);
    }
    return out.join('/');
  },

  _parse(str) { return new DOMParser().parseFromString(str, 'application/xml'); },
  _children(el, name) { return Array.from(el.children).filter(c => c.namespaceURI === W_NS && c.localName === name); },
  _child(el, name) { return Docx._children(el, name)[0] || null; },
  _val(el, name) {
    const c = el && Docx._child(el, name);
    return c ? c.getAttributeNS(W_NS, 'val') : null;
  },
  _on(el, name) {
    const c = el && Docx._child(el, name);
    if (!c) return false;
    const v = c.getAttributeNS(W_NS, 'val');
    return v == null || !/^(0|false|off|none)$/i.test(v);
  },

  /** Převede posloupnost blokových prvků (odstavce, tabulky) na HTML. */
  _blocks(container, ctx) {
    let html = '';
    let list = null; // {stack:[{tag, numId}], html}
    const closeLists = (toDepth = 0) => {
      while (list && list.stack.length > toDepth) {
        html += '</li></' + list.stack.pop().tag + '>';
      }
      if (list && list.stack.length === 0) list = null;
    };
    const flat = [];
    const collect = el => {
      for (const c of el.children) {
        if (c.namespaceURI !== W_NS) continue;
        if (c.localName === 'p' || c.localName === 'tbl') flat.push(c);
        else if (c.localName === 'sdt') { const sc = Docx._child(c, 'sdtContent'); if (sc) collect(sc); }
        else if (c.localName === 'customXml' || c.localName === 'ins' || c.localName === 'smartTag') collect(c);
      }
    };
    collect(container);

    for (const el of flat) {
      if (el.localName === 'tbl') {
        closeLists();
        html += Docx._table(el, ctx);
        continue;
      }
      const pPr = Docx._child(el, 'pPr');
      const numPr = pPr && Docx._child(pPr, 'numPr');
      const pStyle = Docx._val(pPr, 'pStyle');
      const styleNum = pStyle ? ctx.styles.numPr[pStyle] : null;
      let numId = numPr ? Docx._val(numPr, 'numId') : null;
      if (!numId && styleNum) numId = styleNum.numId;
      if (numId && numId !== '0' && ctx.numbering[numId]) {
        const ilvl = +((numPr && Docx._val(numPr, 'ilvl')) || (styleNum && styleNum.ilvl) || 0);
        const fmt = ctx.numbering[numId][ilvl] || 'decimal';
        const tag = fmt === 'bullet' || fmt === 'none' ? 'ul' : 'ol';
        const depth = ilvl + 1;
        if (!list) list = { stack: [] };
        // stejná úroveň, jiný seznam -> zavřít
        if (list.stack.length >= depth && (list.stack[depth - 1].tag !== tag || list.stack[depth - 1].numId !== numId) && depth === 1) closeLists();
        if (list && list.stack.length > depth) {
          while (list.stack.length > depth) html += '</li></' + list.stack.pop().tag + '>';
        }
        if (!list) list = { stack: [] };
        if (list.stack.length === depth) {
          html += '</li><li>';
        } else {
          while (list.stack.length < depth) {
            const t = list.stack.length === depth - 1 ? tag : 'ul';
            let attr = '';
            if (t === 'ol') {
              const st = { lowerLetter: 'a', upperLetter: 'A', lowerRoman: 'i', upperRoman: 'I' }[fmt];
              if (st) attr = ' type="' + st + '"';
            }
            html += '<' + t + attr + '><li>';
            list.stack.push({ tag: t, numId });
          }
        }
        html += Docx._paraInner(el, ctx) || '<br>';
        continue;
      }
      closeLists();
      html += Docx._para(el, ctx);
    }
    closeLists();
    return html;
  },

  _paraAttrs(pPr) {
    if (!pPr) return '';
    const st = [];
    const jc = Docx._val(pPr, 'jc');
    if (jc) {
      const a = { center: 'center', right: 'right', end: 'right', both: 'justify', distribute: 'justify' }[jc];
      if (a) st.push('text-align:' + a);
    }
    const ind = Docx._child(pPr, 'ind');
    if (ind) {
      const left = +(ind.getAttributeNS(W_NS, 'left') || ind.getAttributeNS(W_NS, 'start') || 0);
      if (left > 0) st.push('margin-left:' + Math.round(left / 15) + 'px');
    }
    const shd = Docx._child(pPr, 'shd');
    if (shd) {
      const f = shd.getAttributeNS(W_NS, 'fill');
      if (f && /^[0-9a-f]{6}$/i.test(f)) st.push('background-color:#' + f);
    }
    return st.length ? ' style="' + st.join(';') + '"' : '';
  },

  _para(p, ctx) {
    const pPr = Docx._child(p, 'pPr');
    const styleId = Docx._val(pPr, 'pStyle');
    const lvl = styleId ? ctx.styles.heading[styleId] : null;
    const tag = lvl ? 'h' + lvl : 'p';
    const inner = Docx._paraInner(p, ctx);
    let pre = '';
    if (pPr && Docx._on(pPr, 'pageBreakBefore')) pre = '<hr class="pagebreak">';
    return pre + '<' + tag + Docx._paraAttrs(pPr) + '>' + (inner || '<br>') + '</' + tag + '>';
  },

  _paraInner(p, ctx) {
    let html = '';
    const walk = (el, href) => {
      for (const c of el.children) {
        if (c.namespaceURI !== W_NS) {
          // mc:AlternateContent -> vezmeme Fallback/Choice s obrázkem
          if (c.localName === 'AlternateContent') {
            const choice = c.firstElementChild;
            if (choice) walk(choice, href);
          }
          continue;
        }
        switch (c.localName) {
          case 'r': html += Docx._run(c, ctx, href); break;
          case 'hyperlink': {
            const id = c.getAttributeNS(R_NS, 'id');
            const anchor = c.getAttributeNS(W_NS, 'anchor');
            const h = id && ctx.rels[id] ? ctx.rels[id].target : (anchor ? '#' + anchor : null);
            if (h) html += '<a href="' + Util.html(h) + '">';
            walk(c, h);
            if (h) html += '</a>';
            break;
          }
          case 'ins': case 'smartTag': case 'customXml': case 'fldSimple': case 'sdtContent':
            walk(c, href); break;
          case 'sdt': { const sc = Docx._child(c, 'sdtContent'); if (sc) walk(sc, href); break; }
          case 'del': break; // smazaný text při sledování změn
        }
      }
    };
    walk(p, null);
    return html;
  },

  _run(r, ctx) {
    const rPr = Docx._child(r, 'rPr');
    let content = '';
    for (const c of r.children) {
      if (c.namespaceURI !== W_NS) {
        if (c.localName === 'AlternateContent') {
          const imgs = c.getElementsByTagNameNS('http://schemas.openxmlformats.org/drawingml/2006/main', 'blip');
          if (imgs[0]) content += Docx._img(imgs[0], c, ctx);
        }
        continue;
      }
      switch (c.localName) {
        case 't': content += Util.html(c.textContent); break;
        case 'tab': content += '&emsp;'; break;
        case 'br':
          if (c.getAttributeNS(W_NS, 'type') === 'page') content += '<br>';
          else content += '<br>';
          break;
        case 'cr': content += '<br>'; break;
        case 'noBreakHyphen': content += '‑'; break;
        case 'softHyphen': content += '&shy;'; break;
        case 'sym': {
          const ch = c.getAttributeNS(W_NS, 'char');
          if (ch) { const code = parseInt(ch, 16); content += '&#' + (code >= 0xF000 ? code - 0xF000 : code) + ';'; }
          break;
        }
        case 'drawing': {
          const blip = c.getElementsByTagNameNS('http://schemas.openxmlformats.org/drawingml/2006/main', 'blip')[0];
          if (blip) content += Docx._img(blip, c, ctx);
          break;
        }
        case 'pict': {
          const im = c.getElementsByTagNameNS('urn:schemas-microsoft-com:vml', 'imagedata')[0];
          const id = im && im.getAttributeNS(R_NS, 'id');
          if (id && ctx.media[id]) content += '<img src="' + ctx.media[id] + '">';
          break;
        }
      }
    }
    if (!content || !rPr) return content;
    if (Docx._on(rPr, 'vanish')) return '';
    const st = [];
    const color = Docx._val(rPr, 'color');
    if (color && /^[0-9a-f]{6}$/i.test(color) && color !== '000000') st.push('color:#' + color);
    const sz = Docx._val(rPr, 'sz');
    if (sz) st.push('font-size:' + (+sz / 2) + 'pt');
    const hl = Docx._val(rPr, 'highlight');
    if (hl && HL_COLORS[hl]) st.push('background-color:' + HL_COLORS[hl]);
    else {
      const shd = Docx._child(rPr, 'shd');
      const f = shd && shd.getAttributeNS(W_NS, 'fill');
      if (f && /^[0-9a-f]{6}$/i.test(f) && f.toLowerCase() !== 'ffffff') st.push('background-color:#' + f);
    }
    const fonts = Docx._child(rPr, 'rFonts');
    const font = fonts && (fonts.getAttributeNS(W_NS, 'ascii') || fonts.getAttributeNS(W_NS, 'hAnsi'));
    if (font) st.push("font-family:'" + font.replace(/['"<>]/g, '') + "'");
    if (Docx._on(rPr, 'caps')) st.push('text-transform:uppercase');
    if (Docx._on(rPr, 'smallCaps')) st.push('font-variant:small-caps');
    if (st.length) content = '<span style="' + st.join(';') + '">' + content + '</span>';
    const va = Docx._val(rPr, 'vertAlign');
    if (va === 'superscript') content = '<sup>' + content + '</sup>';
    else if (va === 'subscript') content = '<sub>' + content + '</sub>';
    if (Docx._on(rPr, 'strike') || Docx._on(rPr, 'dstrike')) content = '<s>' + content + '</s>';
    const u = Docx._val(rPr, 'u');
    if (Docx._child(rPr, 'u') && u !== 'none') content = '<u>' + content + '</u>';
    if (Docx._on(rPr, 'i') || Docx._on(rPr, 'iCs')) content = '<i>' + content + '</i>';
    if (Docx._on(rPr, 'b') || Docx._on(rPr, 'bCs')) content = '<b>' + content + '</b>';
    return content;
  },

  _img(blip, container, ctx) {
    const id = blip.getAttributeNS(R_NS, 'embed');
    if (!id || !ctx.media[id]) return '';
    const ext = container.getElementsByTagNameNS('http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing', 'extent')[0];
    let attr = '';
    if (ext) {
      const w = Math.round(+ext.getAttribute('cx') / 9525);
      const h = Math.round(+ext.getAttribute('cy') / 9525);
      if (w > 0 && h > 0) attr = ' width="' + w + '" height="' + h + '"';
    }
    return '<img src="' + ctx.media[id] + '"' + attr + '>';
  },

  _table(tbl, ctx) {
    const rows = Docx._children(tbl, 'tr');
    // Vertikální sloučení: spočítat rowspan
    const grid = rows.map(tr => {
      let col = 0;
      return Docx._children(tr, 'tc').map(tc => {
        const tcPr = Docx._child(tc, 'tcPr');
        const span = +(Docx._val(tcPr, 'gridSpan') || 1);
        const vm = tcPr && Docx._child(tcPr, 'vMerge');
        const vmerge = vm ? (vm.getAttributeNS(W_NS, 'val') === 'restart' ? 'restart' : 'continue') : null;
        const cell = { tc, tcPr, col, span, vmerge, rowspan: 1 };
        col += span;
        return cell;
      });
    });
    for (let r = 0; r < grid.length; r++) {
      for (const cell of grid[r]) {
        if (cell.vmerge !== 'restart') continue;
        for (let rr = r + 1; rr < grid.length; rr++) {
          const below = grid[rr].find(c => c.col === cell.col);
          if (below && below.vmerge === 'continue') { cell.rowspan++; below.skip = true; } else break;
        }
      }
    }
    let html = '<table><tbody>';
    for (const row of grid) {
      html += '<tr>';
      for (const cell of row) {
        if (cell.skip) continue;
        let attr = '';
        if (cell.span > 1) attr += ' colspan="' + cell.span + '"';
        if (cell.rowspan > 1) attr += ' rowspan="' + cell.rowspan + '"';
        const st = [];
        const shd = cell.tcPr && Docx._child(cell.tcPr, 'shd');
        const fill = shd && shd.getAttributeNS(W_NS, 'fill');
        if (fill && /^[0-9a-f]{6}$/i.test(fill)) st.push('background-color:#' + fill);
        const tcW = cell.tcPr && Docx._child(cell.tcPr, 'tcW');
        if (tcW && tcW.getAttributeNS(W_NS, 'type') === 'dxa') {
          const w = Math.round(+tcW.getAttributeNS(W_NS, 'w') / 15);
          if (w > 0) st.push('width:' + w + 'px');
        }
        if (st.length) attr += ' style="' + st.join(';') + '"';
        html += '<td' + attr + '>' + (Docx._blocks(cell.tc, ctx) || '<p><br></p>') + '</td>';
      }
      html += '</tr>';
    }
    return html + '</tbody></table>';
  },

  /* ================= ZÁPIS ================= */

  /**
   * @param root  prvek s obsahem dokumentu (contenteditable)
   * @param original  původní bajty .docx nebo null (nový dokument)
   */
  async fromHtml(root, original) {
    const zip = original ? await JSZip.loadAsync(original) : Docx._skeleton();
    const docPath = await Docx._mainDocPath(zip);
    const dir = docPath.replace(/[^/]+$/, '');
    const relsPath = dir + '_rels/' + docPath.slice(dir.length) + '.rels';

    // --- relace dokumentu
    let relsDoc = zip.file(relsPath)
      ? Docx._parse(await zip.file(relsPath).async('string'))
      : Docx._parse('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="' + REL_NS + '"/>');
    const relRoot = relsDoc.documentElement;
    const usedIds = new Set(Array.from(relRoot.getElementsByTagNameNS(REL_NS, 'Relationship')).map(r => r.getAttribute('Id')));
    let relCounter = 1;
    const addRel = (type, target, external) => {
      let id;
      do { id = 'rIdK' + relCounter++; } while (usedIds.has(id));
      usedIds.add(id);
      const r = relsDoc.createElementNS(REL_NS, 'Relationship');
      r.setAttribute('Id', id);
      r.setAttribute('Type', type);
      r.setAttribute('Target', target);
      if (external) r.setAttribute('TargetMode', 'External');
      relRoot.appendChild(r);
      return id;
    };
    const hasRelType = t => Array.from(relRoot.getElementsByTagNameNS(REL_NS, 'Relationship')).some(r => r.getAttribute('Type').endsWith('/' + t));

    // --- styly: zajistit nadpisy, hypertextový odkaz a mřížku tabulky
    const stylesPath = dir + 'styles.xml';
    let headingIds = {};
    {
      let sx;
      if (zip.file(stylesPath)) sx = Docx._parse(await zip.file(stylesPath).async('string'));
      else {
        sx = Docx._parse(Docx.STYLES_XML);
        if (!hasRelType('styles')) addRel('http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles', 'styles.xml');
        await Docx._ensureOverride(zip, '/' + stylesPath, 'application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml');
      }
      const stylesEl = sx.documentElement;
      const byId = {};
      for (const st of stylesEl.getElementsByTagNameNS(W_NS, 'style')) {
        const id = st.getAttributeNS(W_NS, 'styleId');
        const nameEl = Docx._child(st, 'name');
        byId[id] = { el: st, type: st.getAttributeNS(W_NS, 'type'), name: nameEl ? (nameEl.getAttributeNS(W_NS, 'val') || '').toLowerCase() : '' };
      }
      for (let lvl = 1; lvl <= 6; lvl++) {
        let id = Object.keys(byId).find(k => byId[k].type === 'paragraph' && byId[k].name === 'heading ' + lvl);
        if (!id) {
          id = 'Heading' + lvl;
          if (!byId[id]) {
            const frag = Docx._parse('<w:root xmlns:w="' + W_NS + '">' + Docx._headingStyle(lvl) + '</w:root>');
            stylesEl.appendChild(sx.importNode(frag.documentElement.firstElementChild, true));
          }
        }
        headingIds[lvl] = id;
      }
      zip.file(stylesPath, new XMLSerializer().serializeToString(sx));
    }

    // --- číslování: přidat vlastní abstraktní definice (odrážky / čísla)
    const numPath = dir + 'numbering.xml';
    let nx;
    if (zip.file(numPath)) nx = Docx._parse(await zip.file(numPath).async('string'));
    else {
      nx = Docx._parse('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:numbering xmlns:w="' + W_NS + '"/>');
      if (!hasRelType('numbering')) addRel('http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering', 'numbering.xml');
      await Docx._ensureOverride(zip, '/' + numPath, 'application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml');
    }
    const numRoot = nx.documentElement;
    const maxAttr = (tag, attr) => Math.max(0, ...Array.from(numRoot.getElementsByTagNameNS(W_NS, tag)).map(e => +e.getAttributeNS(W_NS, attr) || 0));
    const absBullet = maxAttr('abstractNum', 'abstractNumId') + 1;
    const absDecimal = absBullet + 1;
    let nextNumId = maxAttr('num', 'numId') + 1;
    const firstNum = Docx._child(numRoot, 'num');
    for (const [aid, kind] of [[absBullet, 'bullet'], [absDecimal, 'decimal']]) {
      const frag = Docx._parse('<w:root xmlns:w="' + W_NS + '">' + Docx._abstractNum(aid, kind) + '</w:root>');
      const node = nx.importNode(frag.documentElement.firstElementChild, true);
      numRoot.insertBefore(node, firstNum);
    }
    const newNum = (absId, restart) => {
      const id = nextNumId++;
      let xml = '<w:num w:numId="' + id + '"><w:abstractNumId w:val="' + absId + '"/>';
      if (restart) xml += '<w:lvlOverride w:ilvl="0"><w:startOverride w:val="1"/></w:lvlOverride>';
      xml += '</w:num>';
      const frag = Docx._parse('<w:root xmlns:w="' + W_NS + '">' + xml + '</w:root>');
      numRoot.insertBefore(nx.importNode(frag.documentElement.firstElementChild, true), Docx._child(numRoot, 'numIdMacAtCleanup'));
      return id;
    };

    // --- obrázky a typy obsahu
    const mediaExts = new Set();
    let imgCounter = 1;
    const addImage = (dataUri) => {
      const m = /^data:image\/(png|jpe?g|gif|bmp|webp);base64,(.*)$/i.exec(dataUri);
      if (!m) return null;
      let ext = m[1].toLowerCase(); if (ext === 'jpeg') ext = 'jpg';
      let name;
      do { name = 'media/kancelar_img' + imgCounter++ + '.' + ext; } while (zip.file(dir + name));
      zip.file(dir + name, m[2], { base64: true });
      mediaExts.add(ext);
      return addRel('http://schemas.openxmlformats.org/officeDocument/2006/relationships/image', name);
    };

    const ctx = {
      headingIds,
      newNum, absBullet, absDecimal,
      addImage,
      addLink: href => addRel('http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink', href, true),
      imgId: 1,
    };
    const bodyXml = Docx._htmlBlocks(root, ctx, { left: 0 });

    // --- dokument: zachovat sectPr (velikost stránky, okraje, záhlaví)
    let sectPr = '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1417" w:right="1417" w:bottom="1417" w:left="1417" w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>';
    let docOpen = Docx.DOC_OPEN;
    if (original && zip.file(docPath)) {
      const orig = await zip.file(docPath).async('string');
      const m = /<w:sectPr\b[\s\S]*<\/w:sectPr>\s*<\/w:body>/.exec(orig);
      if (m) {
        // poslední sectPr (přímo v body)
        const s = m[0].replace(/\s*<\/w:body>$/, '');
        const lastStart = s.lastIndexOf('<w:sectPr');
        sectPr = s.slice(lastStart);
      }
      const open = /^[\s\S]*?<w:body>/.exec(orig);
      if (open) docOpen = open[0];
    }
    const docXml = docOpen + bodyXml + sectPr + '</w:body></w:document>';
    zip.file(docPath, docXml);
    zip.file(numPath, new XMLSerializer().serializeToString(nx));
    zip.file(relsPath, new XMLSerializer().serializeToString(relsDoc));
    for (const ext of mediaExts) {
      await Docx._ensureDefault(zip, ext, { png: 'image/png', jpg: 'image/jpeg', gif: 'image/gif', bmp: 'image/bmp', webp: 'image/webp' }[ext]);
    }
    return zip.generateAsync({ type: 'uint8array', compression: 'DEFLATE', mimeType: MIME.docx });
  },

  async _ensureOverride(zip, partName, type) {
    const ct = Docx._parse(await zip.file('[Content_Types].xml').async('string'));
    const root = ct.documentElement;
    const ns = root.namespaceURI;
    if (!Array.from(root.getElementsByTagNameNS(ns, 'Override')).some(o => o.getAttribute('PartName') === partName)) {
      const o = ct.createElementNS(ns, 'Override');
      o.setAttribute('PartName', partName);
      o.setAttribute('ContentType', type);
      root.appendChild(o);
      zip.file('[Content_Types].xml', new XMLSerializer().serializeToString(ct));
    }
  },

  async _ensureDefault(zip, ext, type) {
    const ct = Docx._parse(await zip.file('[Content_Types].xml').async('string'));
    const root = ct.documentElement;
    const ns = root.namespaceURI;
    if (!Array.from(root.getElementsByTagNameNS(ns, 'Default')).some(o => (o.getAttribute('Extension') || '').toLowerCase() === ext)) {
      const o = ct.createElementNS(ns, 'Default');
      o.setAttribute('Extension', ext);
      o.setAttribute('ContentType', type);
      root.insertBefore(o, root.firstChild);
      zip.file('[Content_Types].xml', new XMLSerializer().serializeToString(ct));
    }
  },

  /* ----- HTML -> WordprocessingML ----- */

  _isBlock(el) {
    return el.nodeType === 1 && /^(P|DIV|H[1-6]|UL|OL|LI|TABLE|BLOCKQUOTE|PRE|HR|SECTION|ARTICLE|HEADER|FOOTER)$/.test(el.tagName);
  },

  _htmlBlocks(container, ctx, inherit) {
    let out = '';
    let inline = []; // posbírané inline uzly mimo blok
    const flushInline = () => {
      if (inline.length && inline.some(n => n.nodeType === 1 || n.textContent.trim())) {
        out += Docx._paragraph(inline, ctx, { tag: 'P', left: inherit.left, align: inherit.align, bold: inherit.bold });
      }
      inline = [];
    };
    for (const node of container.childNodes) {
      if (node.nodeType === 3 || (node.nodeType === 1 && !Docx._isBlock(node))) {
        inline.push(node);
        continue;
      }
      if (node.nodeType !== 1) continue;
      flushInline();
      const tag = node.tagName;
      const align = Docx._align(node) || inherit.align;
      const left = inherit.left + Docx._marginLeft(node);
      const bold = inherit.bold;
      if (tag === 'UL' || tag === 'OL') {
        out += Docx._list(node, ctx, 0, null, { left, align, bold });
      } else if (tag === 'TABLE') {
        out += Docx._tableXml(node, ctx);
      } else if (tag === 'HR') {
        if (node.classList.contains('pagebreak')) out += '<w:p><w:r><w:br w:type="page"/></w:r></w:p>';
        else out += '<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="auto"/></w:pBdr></w:pPr></w:p>';
      } else if (tag === 'BLOCKQUOTE') {
        out += Docx._htmlBlocks(node, ctx, { left: left + 720, align, bold });
      } else if (tag === 'DIV' || tag === 'SECTION' || tag === 'ARTICLE' || tag === 'HEADER' || tag === 'FOOTER') {
        if (Array.from(node.childNodes).some(c => Docx._isBlock(c))) out += Docx._htmlBlocks(node, ctx, { left, align, bold });
        else out += Docx._paragraph(Array.from(node.childNodes), ctx, { tag: 'P', left, align, bold, bg: Docx._bg(node) });
      } else if (tag === 'LI') {
        out += Docx._htmlBlocks(node, ctx, { left, align, bold });
      } else if (Array.from(node.childNodes).some(c => Docx._isBlock(c))) {
        // neplatné vnoření (např. <p><ol>) – zpracovat obsah jako bloky
        out += Docx._htmlBlocks(node, ctx, { left, align, bold });
      } else {
        out += Docx._paragraph(Array.from(node.childNodes), ctx, { tag, left, align, bold, bg: Docx._bg(node) });
      }
    }
    flushInline();
    return out;
  },

  _align(el) {
    const a = (el.style && el.style.textAlign) || el.getAttribute('align') || '';
    return { center: 'center', right: 'right', justify: 'both', left: 'left', start: 'left', end: 'right' }[a.toLowerCase()] || null;
  },
  _marginLeft(el) {
    const s = el.style || {};
    const v = s.marginLeft || s.paddingLeft || '';
    const m = /^([\d.]+)px$/.exec(v);
    if (m) return Math.round(+m[1] * 15);
    const m2 = /^([\d.]+)em$/.exec(v);
    if (m2) return Math.round(+m2[1] * 240);
    return 0;
  },
  _bg(el) {
    const c = Docx._hexColor(el.style && el.style.backgroundColor);
    return c && c !== 'FFFFFF' ? c : null;
  },

  _list(listEl, ctx, level, numId, inherit) {
    const ordered = listEl.tagName === 'OL';
    // Každý seznam nejvyšší úrovně dostane vlastní w:num (číslování od 1).
    if (level === 0 || numId == null) numId = ctx.newNum(ordered ? ctx.absDecimal : ctx.absBullet, ordered);
    // Vnořený seznam jiného typu -> vlastní num
    let out = '';
    for (const li of listEl.children) {
      if (li.tagName !== 'LI') {
        if (li.tagName === 'UL' || li.tagName === 'OL') out += Docx._list(li, ctx, level + 1, null, inherit);
        continue;
      }
      const inlineNodes = [];
      const nested = [];
      for (const c of li.childNodes) {
        if (c.nodeType === 1 && (c.tagName === 'UL' || c.tagName === 'OL')) nested.push(c);
        else if (c.nodeType === 1 && Docx._isBlock(c)) {
          // <li><p>..</p></li>
          inlineNodes.push(...c.childNodes);
        } else inlineNodes.push(c);
      }
      out += Docx._paragraph(inlineNodes, ctx, { tag: 'P', numId, ilvl: level, align: Docx._align(li) || inherit.align, bold: inherit.bold });
      for (const n of nested) {
        const sub = n.tagName === 'OL' ? ctx.newNum(ctx.absDecimal, true) : ctx.newNum(ctx.absBullet, false);
        out += Docx._list(n, ctx, level + 1, sub, inherit);
      }
    }
    return out;
  },

  _paragraph(nodes, ctx, opt) {
    let pPr = '';
    const m = /^H([1-6])$/.exec(opt.tag || '');
    if (m) pPr += '<w:pStyle w:val="' + ctx.headingIds[m[1]] + '"/>';
    if (opt.numId != null) pPr += '<w:numPr><w:ilvl w:val="' + Math.min(8, opt.ilvl || 0) + '"/><w:numId w:val="' + opt.numId + '"/></w:numPr>';
    if (opt.bg) pPr += '<w:shd w:val="clear" w:color="auto" w:fill="' + opt.bg + '"/>';
    if (opt.left) pPr += '<w:ind w:left="' + opt.left + '"/>';
    if (opt.align && opt.align !== 'left') pPr += '<w:jc w:val="' + opt.align + '"/>';
    let runs = '';
    const fmt = { mono: opt.tag === 'PRE', b: !!opt.bold };
    for (const n of nodes) runs += Docx._inline(n, ctx, fmt, opt.tag === 'PRE');
    return '<w:p>' + (pPr ? '<w:pPr>' + pPr + '</w:pPr>' : '') + runs + '</w:p>';
  },

  _inline(node, ctx, fmt, pre) {
    if (node.nodeType === 3) {
      let text = node.textContent;
      if (!pre) text = text.replace(/[\r\n\t]+/g, ' ');
      if (!text) return '';
      // tabulátor z &emsp;
      const parts = text.split(/( |\n)/);
      let out = '';
      for (const part of parts) {
        if (part === ' ') out += Docx._runXml(fmt, '<w:tab/>');
        else if (part === '\n') out += Docx._runXml(fmt, '<w:br/>');
        else if (part) out += Docx._runXml(fmt, '<w:t xml:space="preserve">' + Util.xml(part) + '</w:t>');
      }
      return out;
    }
    if (node.nodeType !== 1) return '';
    const tag = node.tagName;
    if (tag === 'BR') return Docx._runXml(fmt, '<w:br/>');
    if (tag === 'IMG') return Docx._imageRun(node, ctx);
    if (tag === 'SCRIPT' || tag === 'STYLE') return '';
    const f = Object.assign({}, fmt);
    if (tag === 'B' || tag === 'STRONG') f.b = true;
    if (tag === 'I' || tag === 'EM') f.i = true;
    if (tag === 'U' || tag === 'INS') f.u = true;
    if (tag === 'S' || tag === 'STRIKE' || tag === 'DEL') f.s = true;
    if (tag === 'SUP') f.va = 'superscript';
    if (tag === 'SUB') f.va = 'subscript';
    if (tag === 'CODE') f.mono = true;
    if (tag === 'FONT') {
      const c = Docx._hexColor(node.getAttribute('color'));
      if (c) f.color = c;
      const face = node.getAttribute('face');
      if (face) f.font = face.split(',')[0].replace(/['"]/g, '').trim();
      const size = +node.getAttribute('size');
      if (size) f.sz = [0, 16, 20, 24, 28, 36, 48, 72][Math.min(7, size)];
    }
    const st = node.style;
    if (st) {
      if (st.fontWeight === 'bold' || +st.fontWeight >= 600) f.b = true;
      else if (st.fontWeight === 'normal' || (+st.fontWeight && +st.fontWeight < 600)) f.b = false;
      if (st.fontStyle === 'italic') f.i = true;
      const td = st.textDecorationLine || st.textDecoration || '';
      if (/underline/.test(td)) f.u = true;
      if (/line-through/.test(td)) f.s = true;
      const c = Docx._hexColor(st.color);
      if (c) f.color = c;
      const bg = Docx._hexColor(st.backgroundColor);
      if (bg) f.hl = bg;
      if (st.fontSize) {
        const pt = Docx._toPt(st.fontSize);
        if (pt) f.sz = Math.round(pt * 2);
      }
      if (st.fontFamily) f.font = st.fontFamily.split(',')[0].replace(/['"]/g, '').trim();
      if (st.textTransform === 'uppercase') f.caps = true;
      if (st.verticalAlign === 'super') f.va = 'superscript';
      if (st.verticalAlign === 'sub') f.va = 'subscript';
    }
    let inner = '';
    for (const c of node.childNodes) inner += Docx._inline(c, ctx, f, pre);
    if (tag === 'A' && node.getAttribute('href')) {
      const href = node.getAttribute('href');
      if (href.startsWith('#')) return '<w:hyperlink w:anchor="' + Util.xml(href.slice(1)) + '">' + inner + '</w:hyperlink>';
      const id = ctx.addLink(href);
      const lf = Object.assign({}, f, { u: true, color: f.color || '0563C1' });
      inner = '';
      for (const c of node.childNodes) inner += Docx._inline(c, ctx, lf, pre);
      return '<w:hyperlink r:id="' + id + '">' + inner + '</w:hyperlink>';
    }
    return inner;
  },

  _toPt(v) {
    const m = /^([\d.]+)(pt|px|em|rem)?$/.exec(v);
    if (!m) {
      return { 'x-small': 7.5, small: 10, medium: 12, large: 13.5, 'x-large': 18, 'xx-large': 24 }[v] || null;
    }
    const n = +m[1];
    switch (m[2]) {
      case 'px': return n * 0.75;
      case 'em': case 'rem': return n * 11;
      default: return n;
    }
  },

  _hexColor(c) {
    if (!c) return null;
    c = String(c).trim();
    let m = /^#([0-9a-f]{3})$/i.exec(c);
    if (m) return m[1].split('').map(x => x + x).join('').toUpperCase();
    m = /^#([0-9a-f]{6})$/i.exec(c);
    if (m) return m[1].toUpperCase();
    m = /^rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)$/.exec(c);
    if (m) {
      if (m[4] !== undefined && +m[4] === 0) return null;
      return [m[1], m[2], m[3]].map(x => (+x).toString(16).padStart(2, '0')).join('').toUpperCase();
    }
    const named = { black: '000000', white: 'FFFFFF', red: 'FF0000', green: '008000', blue: '0000FF', yellow: 'FFFF00', gray: '808080', grey: '808080', orange: 'FFA500' }[c.toLowerCase()];
    return named || null;
  },

  _runXml(f, content) {
    let rPr = '';
    if (f.font) rPr += '<w:rFonts w:ascii="' + Util.xml(f.font) + '" w:hAnsi="' + Util.xml(f.font) + '" w:cs="' + Util.xml(f.font) + '"/>';
    else if (f.mono) rPr += '<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/>';
    if (f.b) rPr += '<w:b/>';
    if (f.i) rPr += '<w:i/>';
    if (f.caps) rPr += '<w:caps/>';
    if (f.s) rPr += '<w:strike/>';
    if (f.color) rPr += '<w:color w:val="' + f.color + '"/>';
    if (f.sz) rPr += '<w:sz w:val="' + f.sz + '"/><w:szCs w:val="' + f.sz + '"/>';
    const named = f.hl && Object.entries(HL_COLORS).find(([, v]) => v.slice(1).toUpperCase() === f.hl);
    if (named) rPr += '<w:highlight w:val="' + named[0] + '"/>';
    if (f.u) rPr += '<w:u w:val="single"/>';
    if (f.hl && !named) rPr += '<w:shd w:val="clear" w:color="auto" w:fill="' + f.hl + '"/>';
    if (f.va) rPr += '<w:vertAlign w:val="' + f.va + '"/>';
    return '<w:r>' + (rPr ? '<w:rPr>' + rPr + '</w:rPr>' : '') + content + '</w:r>';
  },

  _imageRun(img, ctx) {
    const src = img.getAttribute('src') || '';
    const rid = ctx.addImage(src);
    if (!rid) return '';
    let w = +img.getAttribute('width') || img.naturalWidth || img.width || 300;
    let h = +img.getAttribute('height') || img.naturalHeight || img.height || 200;
    const maxW = 604; // ~16 cm
    if (w > maxW) { h = Math.round(h * maxW / w); w = maxW; }
    const cx = Math.round(w * 9525), cy = Math.round(h * 9525);
    const id = ctx.imgId++;
    return '<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">' +
      '<wp:extent cx="' + cx + '" cy="' + cy + '"/><wp:docPr id="' + (1000 + id) + '" name="Obrázek ' + id + '"/>' +
      '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">' +
      '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="' + (1000 + id) + '" name="Obrázek ' + id + '"/><pic:cNvPicPr/></pic:nvPicPr>' +
      '<pic:blipFill><a:blip r:embed="' + rid + '"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>' +
      '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="' + cx + '" cy="' + cy + '"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>' +
      '</a:graphicData></a:graphic></wp:inline></w:drawing></w:r>';
  },

  _tableXml(table, ctx) {
    const rows = Array.from(table.rows);
    if (!rows.length) return '';
    // mapa obsazenosti kvůli rowspan
    const occupied = [];
    let maxCols = 0;
    const layout = rows.map((tr, r) => {
      const cells = [];
      let c = 0;
      occupied[r] = occupied[r] || [];
      for (const td of tr.cells) {
        while (occupied[r][c]) {
          cells.push({ cont: occupied[r][c] }); c += occupied[r][c].span;
        }
        const span = Math.max(1, td.colSpan || 1);
        const rs = Math.max(1, td.rowSpan || 1);
        const cell = { td, span, rs };
        cells.push(cell);
        for (let k = 1; k < rs; k++) {
          occupied[r + k] = occupied[r + k] || [];
          occupied[r + k][c] = { span };
        }
        c += span;
      }
      while (occupied[r][c]) { cells.push({ cont: occupied[r][c] }); c += occupied[r][c].span; }
      maxCols = Math.max(maxCols, c);
      return cells;
    });
    const colW = Math.floor(9000 / Math.max(1, maxCols));
    let xml = '<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblBorders>' +
      ['top', 'left', 'bottom', 'right', 'insideH', 'insideV'].map(s => '<w:' + s + ' w:val="single" w:sz="4" w:space="0" w:color="auto"/>').join('') +
      '</w:tblBorders><w:tblLook w:val="04A0"/></w:tblPr><w:tblGrid>';
    for (let i = 0; i < maxCols; i++) xml += '<w:gridCol w:w="' + colW + '"/>';
    xml += '</w:tblGrid>';
    for (const cells of layout) {
      xml += '<w:tr>';
      let used = 0;
      for (const cell of cells) {
        if (cell.cont) {
          xml += '<w:tc><w:tcPr>' + (cell.cont.span > 1 ? '<w:gridSpan w:val="' + cell.cont.span + '"/>' : '') + '<w:vMerge/></w:tcPr><w:p/></w:tc>';
          used += cell.cont.span;
          continue;
        }
        let tcPr = '<w:tcW w:w="' + colW * cell.span + '" w:type="dxa"/>';
        if (cell.span > 1) tcPr += '<w:gridSpan w:val="' + cell.span + '"/>';
        if (cell.rs > 1) tcPr += '<w:vMerge w:val="restart"/>';
        const bg = Docx._bg(cell.td);
        if (bg) tcPr += '<w:shd w:val="clear" w:color="auto" w:fill="' + bg + '"/>';
        let inner = Docx._htmlBlocks(cell.td, ctx, { left: 0, align: Docx._align(cell.td), bold: cell.td.tagName === 'TH' });
        if (!/<w:p[ >]/.test(inner) && !inner.includes('<w:p/>')) inner += '<w:p/>';
        if (/<\/w:tbl>$/.test(inner)) inner += '<w:p/>';
        xml += '<w:tc><w:tcPr>' + tcPr + '</w:tcPr>' + inner + '</w:tc>';
        used += cell.span;
      }
      for (; used < maxCols; used++) xml += '<w:tc><w:tcPr><w:tcW w:w="' + colW + '" w:type="dxa"/></w:tcPr><w:p/></w:tc>';
      xml += '</w:tr>';
    }
    return xml + '</w:tbl>';
  },

  _headingStyle(lvl) {
    const sizes = { 1: 32, 2: 26, 3: 24, 4: 22, 5: 22, 6: 22 };
    const colors = { 1: '1F4E79', 2: '2E74B5', 3: '1F4E79', 4: '2E74B5', 5: '2E74B5', 6: '1F4E79' };
    return '<w:style w:type="paragraph" w:styleId="Heading' + lvl + '"><w:name w:val="heading ' + lvl + '"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:uiPriority w:val="9"/><w:qFormat/>' +
      '<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="' + (lvl === 1 ? 240 : 120) + '" w:after="60"/><w:outlineLvl w:val="' + (lvl - 1) + '"/></w:pPr>' +
      '<w:rPr><w:rFonts w:asciiTheme="majorHAnsi" w:hAnsiTheme="majorHAnsi"/><w:b/>' + (lvl === 4 ? '<w:i/>' : '') + '<w:color w:val="' + colors[lvl] + '"/><w:sz w:val="' + sizes[lvl] + '"/></w:rPr></w:style>';
  },

  _abstractNum(id, kind) {
    let xml = '<w:abstractNum w:abstractNumId="' + id + '"><w:multiLevelType w:val="hybridMultilevel"/>';
    const bullets = ['•', 'o', '▪'];
    const fmts = ['decimal', 'lowerLetter', 'lowerRoman'];
    for (let l = 0; l < 9; l++) {
      const ind = 720 * (l + 1);
      if (kind === 'bullet') {
        const b = bullets[l % 3];
        const font = b === 'o' ? 'Courier New' : (b === '•' ? 'Symbol' : 'Wingdings');
        const ch = b === '•' ? '' : (b === '▪' ? '' : 'o');
        xml += '<w:lvl w:ilvl="' + l + '"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="' + ch + '"/><w:lvlJc w:val="left"/>' +
          '<w:pPr><w:ind w:left="' + ind + '" w:hanging="360"/></w:pPr><w:rPr><w:rFonts w:ascii="' + font + '" w:hAnsi="' + font + '" w:hint="default"/></w:rPr></w:lvl>';
      } else {
        xml += '<w:lvl w:ilvl="' + l + '"><w:start w:val="1"/><w:numFmt w:val="' + fmts[l % 3] + '"/><w:lvlText w:val="%' + (l + 1) + '."/><w:lvlJc w:val="left"/>' +
          '<w:pPr><w:ind w:left="' + ind + '" w:hanging="360"/></w:pPr></w:lvl>';
      }
    }
    return xml + '</w:abstractNum>';
  },

  /** Minimální prázdný balík .docx */
  _skeleton() {
    const zip = new JSZip();
    zip.file('[Content_Types].xml',
      '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
      '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' +
      '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>' +
      '<Default Extension="xml" ContentType="application/xml"/>' +
      '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>' +
      '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>' +
      '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>' +
      '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>' +
      '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>' +
      '</Types>');
    zip.file('_rels/.rels',
      '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
      '<Relationships xmlns="' + REL_NS + '">' +
      '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>' +
      '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>' +
      '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>' +
      '</Relationships>');
    const now = new Date().toISOString().replace(/\.\d+Z$/, 'Z');
    zip.file('docProps/core.xml',
      '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
      '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' +
      '<dc:creator>Kancelář</dc:creator><dcterms:created xsi:type="dcterms:W3CDTF">' + now + '</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">' + now + '</dcterms:modified></cp:coreProperties>');
    zip.file('docProps/app.xml',
      '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
      '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Kancelář pro Android</Application></Properties>');
    zip.file('word/_rels/document.xml.rels',
      '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
      '<Relationships xmlns="' + REL_NS + '">' +
      '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>' +
      '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>' +
      '</Relationships>');
    zip.file('word/styles.xml', Docx.STYLES_XML);
    zip.file('word/numbering.xml', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:numbering xmlns:w="' + W_NS + '"/>');
    zip.file('word/document.xml', Docx.DOC_OPEN + '<w:p/></w:body></w:document>');
    return zip;
  },
};

Docx.DOC_OPEN = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
  '<w:document xmlns:w="' + W_NS + '" xmlns:r="' + R_NS + '" ' +
  'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" ' +
  'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" ' +
  'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><w:body>';

Docx.STYLES_XML = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
  '<w:styles xmlns:w="' + W_NS + '">' +
  '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:eastAsia="Calibri" w:hAnsi="Calibri" w:cs="Times New Roman"/>' +
  '<w:sz w:val="22"/><w:szCs w:val="22"/><w:lang w:val="cs-CZ" w:eastAsia="en-US" w:bidi="ar-SA"/></w:rPr></w:rPrDefault>' +
  '<w:pPrDefault><w:pPr><w:spacing w:after="160" w:line="259" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>' +
  '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>' +
  '<w:style w:type="character" w:default="1" w:styleId="DefaultParagraphFont"><w:name w:val="Default Paragraph Font"/><w:uiPriority w:val="1"/><w:semiHidden/></w:style>' +
  '<w:style w:type="table" w:default="1" w:styleId="TableNormal"><w:name w:val="Normal Table"/><w:semiHidden/><w:tblPr><w:tblInd w:w="0" w:type="dxa"/>' +
  '<w:tblCellMar><w:top w:w="0" w:type="dxa"/><w:left w:w="108" w:type="dxa"/><w:bottom w:w="0" w:type="dxa"/><w:right w:w="108" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style>' +
  '</w:styles>';
