'use strict';
/*
 * Jednoduchý výpočet vzorců Excelu (běžné funkce). Nepodporované funkce
 * nevyhodí chybu do tabulky – ponechá se poslední uložená hodnota ze souboru.
 */

class FErr { constructor(code) { this.code = code; } toString() { return this.code; } }
class Unsupported extends Error {}

const E = {
  DIV0: new FErr('#DIV/0!'), VALUE: new FErr('#VALUE!'), REF: new FErr('#REF!'),
  NAME: new FErr('#NAME?'), NA: new FErr('#N/A'), NUM: new FErr('#NUM!'),
};

const CZ_FUNCS = {
  'SUMA': 'SUM', 'PRŮMĚR': 'AVERAGE', 'POČET': 'COUNT', 'POČET2': 'COUNTA', 'COUNTBLANK': 'COUNTBLANK', 'KDYŽ': 'IF',
  'ZAOKROUHLIT': 'ROUND', 'ZAOKR.NAHORU': 'ROUNDUP', 'ZAOKR.DOLŮ': 'ROUNDDOWN', 'A': 'AND', 'NEBO': 'OR', 'NE': 'NOT',
  'CELÁ.ČÁST': 'INT', 'SOUČIN': 'PRODUCT', 'ZLEVA': 'LEFT', 'ZPRAVA': 'RIGHT', 'ČÁST': 'MID', 'DÉLKA': 'LEN',
  'VELKÁ': 'UPPER', 'MALÁ': 'LOWER', 'PROČISTIT': 'TRIM', 'SVYHLEDAT': 'VLOOKUP', 'VVYHLEDAT': 'HLOOKUP',
  'POZVYHLEDAT': 'MATCH', 'DNES': 'TODAY', 'NYNÍ': 'NOW', 'ROK': 'YEAR', 'MĚSÍC': 'MONTH', 'DEN': 'DAY',
  'ODMOCNINA': 'SQRT', 'MOCNINA': 'POWER', 'SUMIF': 'SUMIF', 'COUNTIF': 'COUNTIF', 'AVERAGEIF': 'AVERAGEIF',
  'HODNOTA': 'VALUE', 'HODNOTA.NA.TEXT': 'TEXT', 'JE.PRÁZDNÉ': 'ISBLANK', 'JE.ČISLO': 'ISNUMBER', 'JE.ČÍSLO': 'ISNUMBER',
  'JE.TEXT': 'ISTEXT', 'SUMPRODUCT': 'SUMPRODUCT', 'SOUČIN.SKALÁRNÍ': 'SUMPRODUCT', 'MEDIAN': 'MEDIAN', 'ZAOKR.DOLŮ.MAT': 'FLOOR',
  'CONCATENATE': 'CONCATENATE', 'CONCAT': 'CONCAT', 'IFERROR': 'IFERROR', 'MAX': 'MAX', 'MIN': 'MIN', 'ABS': 'ABS', 'MOD': 'MOD',
  'INDEX': 'INDEX', 'PI': 'PI', 'PRAVDA': 'TRUE', 'NEPRAVDA': 'FALSE',
};

const Formula = {
  /* ---------- Lexer ---------- */
  tokenize(src) {
    const toks = [];
    let i = 0;
    const re = {
      ws: /^\s+/,
      str: /^"(?:[^"]|"")*"/,
      err: /^#(?:DIV\/0!|VALUE!|REF!|NAME\?|N\/A|NUM!|NULL!)/,
      // 'List 1'!A1:B2, List1!A1, $A$1, A:A, 1:1
      ref: /^(?:(?:'(?:[^']|'')+'|[A-Za-z0-9_À-ɏ.]+)!)?(?:\$?[A-Za-z]{1,3}\$?\d+(?::\$?[A-Za-z]{1,3}\$?\d+)?|\$?[A-Za-z]{1,3}:\$?[A-Za-z]{1,3}|\$?\d+:\$?\d+)(?![\w(.])/,
      num: /^(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?/,
      func: /^[A-Za-z_À-ɏ][A-Za-z0-9_.À-ɏ]*(?=\s*\()/,
      name: /^[A-Za-z_À-ɏ][A-Za-z0-9_.À-ɏ]*/,
      op: /^(?:<>|<=|>=|[-+*/^&=<>%(),;:])/,
    };
    while (i < src.length) {
      const rest = src.slice(i);
      let m, type = null;
      for (const t of ['ws', 'str', 'err', 'ref', 'num', 'func', 'name', 'op']) {
        m = re[t].exec(rest);
        if (m) { type = t; break; }
      }
      if (!type) { toks.push({ type: 'bad', text: rest[0] }); i++; continue; }
      toks.push({ type, text: m[0] });
      i += m[0].length;
    }
    return toks;
  },

  /** Převede zápis s českými názvy funkcí a středníky na anglický tvar uložený v souboru. */
  normalize(src) {
    let toks = Formula.tokenize(src);
    const hasSemicolon = toks.some(t => t.type === 'op' && t.text === ';');
    const out = [];
    for (let k = 0; k < toks.length; k++) {
      const t = toks[k];
      if (t.type === 'func') {
        const up = t.text.toUpperCase();
        out.push(CZ_FUNCS[up] || up);
      } else if (t.type === 'name') {
        const up = t.text.toUpperCase();
        if (up === 'PRAVDA' || up === 'TRUE') out.push('TRUE');
        else if (up === 'NEPRAVDA' || up === 'FALSE') out.push('FALSE');
        else out.push(t.text);
      } else if (hasSemicolon && t.type === 'num' && toks[k + 1] && toks[k + 1].text === ',' && toks[k + 2] && toks[k + 2].type === 'num') {
        // desetinná čárka: 3,5
        out.push(t.text + '.' + toks[k + 2].text);
        k += 2;
      } else if (t.type === 'op' && t.text === ';') {
        out.push(',');
      } else if (t.type === 'ref') {
        const bang = t.text.lastIndexOf('!');
        out.push(t.text.slice(0, bang + 1) + t.text.slice(bang + 1).toUpperCase());
      } else out.push(t.text);
    }
    return out.join('');
  },

  /* ---------- Parser ---------- */
  parse(src) {
    const toks = Formula.tokenize(src).filter(t => t.type !== 'ws');
    let p = 0;
    const peek = () => toks[p];
    const next = () => toks[p++];
    const isOp = (t, ...ops) => t && t.type === 'op' && ops.includes(t.text);
    const expect = txt => { const t = next(); if (!t || t.text !== txt) throw E.NAME; };

    const compare = () => {
      let l = concat();
      while (isOp(peek(), '=', '<>', '<', '>', '<=', '>=')) { const op = next().text; l = { k: 'bin', op, l, r: concat() }; }
      return l;
    };
    const concat = () => {
      let l = add();
      while (isOp(peek(), '&')) { next(); l = { k: 'bin', op: '&', l, r: add() }; }
      return l;
    };
    const add = () => {
      let l = mul();
      while (isOp(peek(), '+', '-')) { const op = next().text; l = { k: 'bin', op, l, r: mul() }; }
      return l;
    };
    const mul = () => {
      let l = pow();
      while (isOp(peek(), '*', '/')) { const op = next().text; l = { k: 'bin', op, l, r: pow() }; }
      return l;
    };
    const pow = () => {
      let l = unary();
      while (isOp(peek(), '^')) { next(); l = { k: 'bin', op: '^', l, r: unary() }; }
      return l;
    };
    const unary = () => {
      if (isOp(peek(), '-')) { next(); return { k: 'neg', e: unary() }; }
      if (isOp(peek(), '+')) { next(); return unary(); }
      return postfix();
    };
    const postfix = () => {
      let e = primary();
      while (isOp(peek(), '%')) { next(); e = { k: 'pct', e }; }
      return e;
    };
    const primary = () => {
      const t = next();
      if (!t) throw E.VALUE;
      switch (t.type) {
        case 'num': return { k: 'lit', v: parseFloat(t.text) };
        case 'str': return { k: 'lit', v: t.text.slice(1, -1).replace(/""/g, '"') };
        case 'err': return { k: 'lit', v: new FErr(t.text) };
        case 'ref': return { k: 'ref', ref: Formula.parseRef(t.text) };
        case 'name': {
          const up = t.text.toUpperCase();
          if (up === 'TRUE') return { k: 'lit', v: true };
          if (up === 'FALSE') return { k: 'lit', v: false };
          throw new Unsupported(up); // pojmenované oblasti
        }
        case 'func': {
          const name = t.text.toUpperCase();
          expect('(');
          const args = [];
          if (!isOp(peek(), ')')) {
            for (;;) {
              if (isOp(peek(), ',') ) { args.push({ k: 'lit', v: null }); }
              else args.push(compare());
              if (isOp(peek(), ',')) { next(); if (isOp(peek(), ')')) { args.push({ k: 'lit', v: null }); break; } continue; }
              break;
            }
          }
          expect(')');
          return { k: 'fn', name: name.replace(/^_XLFN\./, ''), args };
        }
        case 'op':
          if (t.text === '(') { const e = compare(); expect(')'); return e; }
      }
      throw E.VALUE;
    };
    const ast = compare();
    if (p < toks.length) throw E.VALUE;
    return ast;
  },

  parseRef(text) {
    let sheet = null;
    const bang = text.lastIndexOf('!');
    if (bang >= 0) {
      sheet = text.slice(0, bang);
      if (sheet.startsWith("'")) sheet = sheet.slice(1, -1).replace(/''/g, "'");
      text = text.slice(bang + 1);
    }
    const parts = text.replace(/\$/g, '').toUpperCase().split(':');
    const cell = s => {
      const m = /^([A-Z]*)(\d*)$/.exec(s);
      return { c: m[1] ? XLSX.utils.decode_col(m[1]) : null, r: m[2] ? +m[2] - 1 : null };
    };
    const a = cell(parts[0]);
    const b = parts[1] ? cell(parts[1]) : a;
    return { sheet, s: { r: a.r, c: a.c }, e: { r: b.r, c: b.c }, single: !parts[1] };
  },

  /* ---------- Vyhodnocení ---------- */

  /**
   * Engine pro jeden sešit; drží mezipaměť vypočtených hodnot.
   */
  engine(wb) {
    const cache = new Map();
    const visiting = new Set();
    const self = {
      wb,
      value(sheetName, r, c) {
        const ws = wb.Sheets[sheetName];
        if (!ws) return E.REF;
        const addr = XLSX.utils.encode_cell({ r, c });
        const cell = ws[addr];
        if (!cell) return null;
        if (cell.f) {
          const key = sheetName + '!' + addr;
          if (cache.has(key)) return cache.get(key);
          if (visiting.has(key)) return 0; // kruhový odkaz
          visiting.add(key);
          let v;
          try {
            v = self.evalFormula(cell.f, sheetName);
          } catch (e) {
            if (e instanceof Unsupported) v = Formula.cellValue(cell);
            else if (e instanceof FErr) v = e;
            else v = E.VALUE;
          }
          visiting.delete(key);
          cache.set(key, v);
          return v;
        }
        return Formula.cellValue(cell);
      },
      evalFormula(f, sheetName) {
        const ast = Formula.parse(f);
        let v = self.ev(ast, sheetName);
        if (v && v.range) v = v.range[0] ? v.range[0][0] : null;
        if (v === null || v === undefined) v = 0;
        return v;
      },
      range(ref, sheetName) {
        const sn = ref.sheet || sheetName;
        const ws = wb.Sheets[sn];
        if (!ws) throw E.REF;
        const used = ws['!ref'] ? XLSX.utils.decode_range(ws['!ref']) : { s: { r: 0, c: 0 }, e: { r: 0, c: 0 } };
        const r1 = ref.s.r == null ? 0 : ref.s.r, r2 = ref.e.r == null ? used.e.r : ref.e.r;
        const c1 = ref.s.c == null ? 0 : ref.s.c, c2 = ref.e.c == null ? used.e.c : ref.e.c;
        const rows = [];
        for (let r = Math.min(r1, r2); r <= Math.max(r1, r2); r++) {
          const row = [];
          for (let c = Math.min(c1, c2); c <= Math.max(c1, c2); c++) row.push(self.value(sn, r, c));
          rows.push(row);
        }
        return { range: rows };
      },
      ev(n, sn) {
        switch (n.k) {
          case 'lit': return n.v;
          case 'ref':
            if (n.ref.single) return self.value(n.ref.sheet || sn, n.ref.s.r, n.ref.s.c);
            return self.range(n.ref, sn);
          case 'neg': { const v = Formula.num(scalar(self.ev(n.e, sn))); return v instanceof FErr ? v : -v; }
          case 'pct': { const v = Formula.num(scalar(self.ev(n.e, sn))); return v instanceof FErr ? v : v / 100; }
          case 'bin': return Formula.binop(n.op, scalar(self.ev(n.l, sn)), scalar(self.ev(n.r, sn)));
          case 'fn': {
            const fn = FUNCS[n.name];
            if (!fn) throw new Unsupported(n.name);
            if (fn.lazy) return fn(n.args, a => self.ev(a, sn), self, sn);
            const args = n.args.map(a => self.ev(a, sn));
            return fn(args, self, sn);
          }
        }
        throw E.VALUE;
      },
      reset() { cache.clear(); },
    };
    return self;
  },

  cellValue(cell) {
    if (!cell) return null;
    if (cell.t === 'e') return new FErr(cell.w || '#VALUE!');
    if (cell.t === 'z') return null;
    if (cell.t === 'd') return Formula.dateToSerial(cell.v);
    return cell.v === undefined ? null : cell.v;
  },

  dateToSerial(d) {
    const dt = d instanceof Date ? d : new Date(d);
    return (Date.UTC(dt.getFullYear(), dt.getMonth(), dt.getDate(), dt.getHours(), dt.getMinutes(), dt.getSeconds()) - Date.UTC(1899, 11, 30)) / 86400000;
  },
  serialToDate(n) {
    const ms = Math.round(n * 86400000) + Date.UTC(1899, 11, 30);
    const d = new Date(ms);
    return { y: d.getUTCFullYear(), m: d.getUTCMonth() + 1, d: d.getUTCDate() };
  },

  num(v) {
    if (v instanceof FErr) return v;
    if (v === null || v === undefined || v === '') return 0;
    if (typeof v === 'number') return v;
    if (typeof v === 'boolean') return v ? 1 : 0;
    const s = String(v).trim().replace(/\s/g, '').replace(',', '.');
    const n = Number(s);
    return s !== '' && isFinite(n) ? n : E.VALUE;
  },
  str(v) {
    if (v === null || v === undefined) return '';
    if (typeof v === 'boolean') return v ? 'TRUE' : 'FALSE';
    if (typeof v === 'number') return Formula.fmtNum(v);
    return String(v);
  },
  fmtNum(v) {
    if (Number.isInteger(v)) return String(v);
    return String(parseFloat(v.toPrecision(15)));
  },
  bool(v) {
    if (v instanceof FErr) return v;
    if (typeof v === 'boolean') return v;
    if (typeof v === 'number') return v !== 0;
    if (v === null || v === '') return false;
    const s = String(v).toUpperCase();
    if (s === 'TRUE') return true;
    if (s === 'FALSE') return false;
    return E.VALUE;
  },

  binop(op, a, b) {
    if (a instanceof FErr) return a;
    if (b instanceof FErr) return b;
    if (op === '&') return Formula.str(a) + Formula.str(b);
    if (['=', '<>', '<', '>', '<=', '>='].includes(op)) {
      let c;
      if (a === null) a = typeof b === 'string' ? '' : (typeof b === 'boolean' ? false : 0);
      if (b === null) b = typeof a === 'string' ? '' : (typeof a === 'boolean' ? false : 0);
      const rank = v => typeof v === 'number' ? 0 : typeof v === 'string' ? 1 : 2;
      if (rank(a) !== rank(b)) c = rank(a) - rank(b);
      else if (typeof a === 'string') c = a.toLowerCase().localeCompare(b.toLowerCase(), 'cs');
      else c = (a > b) - (a < b);
      return { '=': c === 0, '<>': c !== 0, '<': c < 0, '>': c > 0, '<=': c <= 0, '>=': c >= 0 }[op];
    }
    const x = Formula.num(a), y = Formula.num(b);
    if (x instanceof FErr) return x;
    if (y instanceof FErr) return y;
    switch (op) {
      case '+': return x + y;
      case '-': return x - y;
      case '*': return x * y;
      case '/': return y === 0 ? E.DIV0 : x / y;
      case '^': { const r = Math.pow(x, y); return isFinite(r) ? r : E.NUM; }
    }
    return E.VALUE;
  },

  /** Kritérium pro SUMIF/COUNTIF: "&gt;5", "&lt;&gt;x", "ab*" ... */
  criteria(crit) {
    if (typeof crit === 'number' || typeof crit === 'boolean') return v => v === crit;
    const s = Formula.str(crit);
    const m = /^(<>|<=|>=|=|<|>)?(.*)$/.exec(s);
    const op = m[1] || '=';
    const rhs = m[2];
    const n = Number(rhs.replace(',', '.'));
    const isNum = rhs !== '' && isFinite(n);
    if (isNum) {
      return v => {
        if (typeof v !== 'number') return op === '<>';
        return { '=': v === n, '<>': v !== n, '<': v < n, '>': v > n, '<=': v <= n, '>=': v >= n }[op];
      };
    }
    if ((op === '=' || op === '<>') && /[*?]/.test(rhs)) {
      const rx = new RegExp('^' + rhs.replace(/[.+^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '.*').replace(/\?/g, '.') + '$', 'i');
      return v => (op === '=') === rx.test(Formula.str(v));
    }
    const low = rhs.toLowerCase();
    return v => {
      const sv = Formula.str(v).toLowerCase();
      if (op === '=') return rhs === '' ? (v === null || v === '') : sv === low;
      if (op === '<>') return sv !== low;
      const c = sv.localeCompare(low, 'cs');
      return { '<': c < 0, '>': c > 0, '<=': c <= 0, '>=': c >= 0 }[op];
    };
  },

  /* ---------- Posun odkazů při vkládání/mazání řádků a sloupců ---------- */
  shift(f, formulaSheet, targetSheet, axis, at, delta) {
    const toks = Formula.tokenize(f);
    return toks.map(t => {
      if (t.type !== 'ref') return t.text;
      let txt = t.text, prefix = '';
      const bang = txt.lastIndexOf('!');
      let sheet = formulaSheet;
      if (bang >= 0) {
        prefix = txt.slice(0, bang + 1);
        sheet = prefix.slice(0, -1);
        if (sheet.startsWith("'")) sheet = sheet.slice(1, -1).replace(/''/g, "'");
        txt = txt.slice(bang + 1);
      }
      if (sheet !== targetSheet) return t.text;
      let broken = false;
      const parts = txt.split(':').map(p => {
        const m = /^(\$?)([A-Za-z]*)(\$?)(\d*)$/.exec(p);
        if (!m) return p;
        let [, dc, col, dr, row] = m;
        if (axis === 'row' && row) {
          let r = +row - 1;
          if (r >= at) { r += delta; if (delta < 0 && r < at) broken = true; }
          row = String(Math.max(0, r) + 1);
        }
        if (axis === 'col' && col) {
          let c = XLSX.utils.decode_col(col.toUpperCase());
          if (c >= at) { c += delta; if (delta < 0 && c < at) broken = true; }
          col = XLSX.utils.encode_col(Math.max(0, c));
        }
        return dc + col + dr + row;
      });
      if (broken && parts.length === 1) return '#REF!';
      return prefix + parts.join(':');
    }).join('');
  },
};

function scalar(v) {
  if (v && v.range) return v.range.length === 1 && v.range[0].length === 1 ? v.range[0][0] : E.VALUE;
  return v;
}

/** Zploští argumenty na seznam hodnot; z oblastí bere jen čísla (jako Excel). */
function flat(args, { fromRangeOnlyNumbers = true } = {}) {
  const out = [];
  for (const a of args) {
    if (a && a.range) {
      for (const row of a.range) for (const v of row) {
        if (v instanceof FErr) throw v;
        if (!fromRangeOnlyNumbers || typeof v === 'number') out.push(v);
      }
    } else {
      if (a instanceof FErr) throw a;
      out.push(a);
    }
  }
  return out;
}
function nums(args) {
  return flat(args).filter(v => v !== null).map(v => {
    const n = Formula.num(v);
    if (n instanceof FErr) throw n;
    return n;
  });
}
function cells(a) {
  if (a && a.range) return a.range.flat();
  return [a];
}
function roundTo(x, d, mode) {
  const f = Math.pow(10, d);
  const v = Math.abs(x) * f;
  let r;
  const eps = 1e-9;
  if (mode === 'up') r = Math.ceil(v - eps);
  else if (mode === 'down') r = Math.floor(v + eps);
  else r = Math.round(v + eps);
  return Math.sign(x) * r / f;
}
const argNum = v => { const n = Formula.num(scalar(v)); if (n instanceof FErr) throw n; return n; };
const argStr = v => { v = scalar(v); if (v instanceof FErr) throw v; return Formula.str(v); };

const FUNCS = {
  SUM: a => nums(a).reduce((s, x) => s + x, 0),
  AVERAGE: a => { const n = nums(a); return n.length ? n.reduce((s, x) => s + x, 0) / n.length : E.DIV0; },
  MIN: a => { const n = nums(a); return n.length ? Math.min(...n) : 0; },
  MAX: a => { const n = nums(a); return n.length ? Math.max(...n) : 0; },
  MEDIAN: a => {
    const n = nums(a).sort((x, y) => x - y);
    if (!n.length) return E.NUM;
    const h = Math.floor(n.length / 2);
    return n.length % 2 ? n[h] : (n[h - 1] + n[h]) / 2;
  },
  PRODUCT: a => nums(a).reduce((s, x) => s * x, 1),
  COUNT: a => {
    let c = 0;
    for (const x of a) {
      if (x && x.range) c += x.range.flat().filter(v => typeof v === 'number').length;
      else if (typeof Formula.num(x) === 'number' && x !== null) c++;
    }
    return c;
  },
  COUNTA: a => a.reduce((c, x) => c + cells(x).filter(v => v !== null && v !== '').length, 0),
  COUNTBLANK: a => a.reduce((c, x) => c + cells(x).filter(v => v === null || v === '').length, 0),
  ABS: a => Math.abs(argNum(a[0])),
  INT: a => Math.floor(argNum(a[0])),
  SQRT: a => { const n = argNum(a[0]); return n < 0 ? E.NUM : Math.sqrt(n); },
  POWER: a => Formula.binop('^', argNum(a[0]), argNum(a[1])),
  MOD: a => { const n = argNum(a[0]), d = argNum(a[1]); return d === 0 ? E.DIV0 : n - d * Math.floor(n / d); },
  PI: () => Math.PI,
  ROUND: a => roundTo(argNum(a[0]), a[1] == null ? 0 : argNum(a[1])),
  ROUNDUP: a => roundTo(argNum(a[0]), a[1] == null ? 0 : argNum(a[1]), 'up'),
  ROUNDDOWN: a => roundTo(argNum(a[0]), a[1] == null ? 0 : argNum(a[1]), 'down'),
  FLOOR: a => { const n = argNum(a[0]), s = a[1] == null ? 1 : argNum(a[1]); return s === 0 ? 0 : Math.floor(n / s) * s; },
  AND: a => { const v = flat(a, { fromRangeOnlyNumbers: false }).filter(x => x !== null).map(Formula.bool); const e = v.find(x => x instanceof FErr); return e || v.every(Boolean); },
  OR: a => { const v = flat(a, { fromRangeOnlyNumbers: false }).filter(x => x !== null).map(Formula.bool); const e = v.find(x => x instanceof FErr); return e || v.some(Boolean); },
  NOT: a => { const b = Formula.bool(scalar(a[0])); return b instanceof FErr ? b : !b; },
  CONCATENATE: a => a.map(argStr).join(''),
  CONCAT: a => flat(a, { fromRangeOnlyNumbers: false }).map(Formula.str).join(''),
  LEN: a => argStr(a[0]).length,
  UPPER: a => argStr(a[0]).toUpperCase(),
  LOWER: a => argStr(a[0]).toLowerCase(),
  TRIM: a => argStr(a[0]).trim().replace(/ +/g, ' '),
  LEFT: a => argStr(a[0]).slice(0, a[1] == null ? 1 : argNum(a[1])),
  RIGHT: a => { const s = argStr(a[0]); const n = a[1] == null ? 1 : argNum(a[1]); return n <= 0 ? '' : s.slice(-n); },
  MID: a => { const s = argStr(a[0]); const st = argNum(a[1]); return s.substr(st - 1, argNum(a[2])); },
  VALUE: a => { const v = Formula.num(scalar(a[0])); return v; },
  TEXT: a => {
    const v = scalar(a[0]); const f = argStr(a[1]);
    try { return XLSX.SSF.format(f, typeof v === 'number' ? v : Formula.num(v)); } catch (e) { return E.VALUE; }
  },
  ISBLANK: a => { const v = scalar(a[0]); return v === null; },
  ISNUMBER: a => typeof scalar(a[0]) === 'number',
  ISTEXT: a => typeof scalar(a[0]) === 'string',
  TODAY: () => { const d = new Date(); return Math.floor(Formula.dateToSerial(new Date(d.getFullYear(), d.getMonth(), d.getDate()))); },
  NOW: () => Formula.dateToSerial(new Date()),
  YEAR: a => Formula.serialToDate(argNum(a[0])).y,
  MONTH: a => Formula.serialToDate(argNum(a[0])).m,
  DAY: a => Formula.serialToDate(argNum(a[0])).d,
  SUMIF: a => {
    const test = Formula.criteria(scalar(a[1]));
    const crit = cells(a[0]);
    const sum = a[2] ? cells(a[2]) : crit;
    let s = 0;
    crit.forEach((v, i) => { if (test(v) && typeof sum[i] === 'number') s += sum[i]; });
    return s;
  },
  COUNTIF: a => { const test = Formula.criteria(scalar(a[1])); return cells(a[0]).filter(v => test(v)).length; },
  AVERAGEIF: a => {
    const test = Formula.criteria(scalar(a[1]));
    const crit = cells(a[0]);
    const vals = a[2] ? cells(a[2]) : crit;
    let s = 0, n = 0;
    crit.forEach((v, i) => { if (test(v) && typeof vals[i] === 'number') { s += vals[i]; n++; } });
    return n ? s / n : E.DIV0;
  },
  SUMPRODUCT: a => {
    const arrs = a.map(cells);
    const len = arrs[0].length;
    if (arrs.some(x => x.length !== len)) return E.VALUE;
    let s = 0;
    for (let i = 0; i < len; i++) s += arrs.reduce((p, arr) => p * (typeof arr[i] === 'number' ? arr[i] : 0), 1);
    return s;
  },
  VLOOKUP: a => {
    const key = scalar(a[0]);
    const tbl = a[1] && a[1].range;
    if (!tbl) return E.VALUE;
    const col = argNum(a[2]);
    const approx = a[3] == null ? true : Formula.bool(scalar(a[3]));
    if (col < 1 || col > (tbl[0] || []).length) return E.REF;
    const idx = lookupIndex(key, tbl.map(r => r[0]), approx);
    return idx < 0 ? E.NA : tbl[idx][col - 1];
  },
  HLOOKUP: a => {
    const key = scalar(a[0]);
    const tbl = a[1] && a[1].range;
    if (!tbl) return E.VALUE;
    const row = argNum(a[2]);
    const approx = a[3] == null ? true : Formula.bool(scalar(a[3]));
    if (row < 1 || row > tbl.length) return E.REF;
    const idx = lookupIndex(key, tbl[0], approx);
    return idx < 0 ? E.NA : tbl[row - 1][idx];
  },
  MATCH: a => {
    const key = scalar(a[0]);
    const arr = cells(a[1]);
    const type = a[2] == null ? 1 : argNum(a[2]);
    const idx = lookupIndex(key, arr, type !== 0);
    return idx < 0 ? E.NA : idx + 1;
  },
  INDEX: a => {
    const tbl = a[0] && a[0].range;
    if (!tbl) return scalar(a[0]);
    let r = a[1] == null ? 1 : argNum(a[1]);
    let c = a[2] == null ? 1 : argNum(a[2]);
    if (tbl.length === 1 && a[2] == null) { c = r; r = 1; }
    const row = tbl[r - 1];
    if (!row || row[c - 1] === undefined) return E.REF;
    return row[c - 1];
  },
};

function lookupIndex(key, arr, approx) {
  const eq = (v) => Formula.binop('=', v, key) === true;
  if (!approx) {
    if (typeof key === 'string' && /[*?]/.test(key)) {
      const test = Formula.criteria(key);
      return arr.findIndex(v => test(v));
    }
    return arr.findIndex(eq);
  }
  let best = -1;
  for (let i = 0; i < arr.length; i++) {
    if (arr[i] === null) continue;
    if (Formula.binop('<=', arr[i], key) === true && typeof arr[i] === typeof key) best = i;
    else if (typeof arr[i] === typeof key) break;
  }
  return best;
}

// Funkce s líným vyhodnocením argumentů
FUNCS.IF = Object.assign((args, ev) => {
  const c = Formula.bool(scalar(ev(args[0])));
  if (c instanceof FErr) return c;
  if (c) return args[1] ? ev(args[1]) : true;
  return args[2] ? ev(args[2]) : false;
}, { lazy: true });
FUNCS.IFERROR = Object.assign((args, ev) => {
  let v;
  try { v = scalar(ev(args[0])); } catch (e) { if (e instanceof Unsupported) throw e; v = e instanceof FErr ? e : E.VALUE; }
  return v instanceof FErr ? ev(args[1]) : v;
}, { lazy: true });

// Výjimky FErr vyhozené uvnitř funkcí převést na hodnotu
for (const [k, fn] of Object.entries(FUNCS)) {
  if (fn.lazy) continue;
  FUNCS[k] = (...p) => { try { return fn(...p); } catch (e) { if (e instanceof FErr) return e; throw e; } };
}
