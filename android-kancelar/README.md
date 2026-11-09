# Kancelář – Word a Excel pro Android

Jednoduchá aplikace pro **čtení a úpravu dokumentů Word (.docx) a tabulek Excel (.xlsx, .xls, .ods, .csv)**.
Funguje celá offline, nic se neodesílá na internet.

## Instalace do telefonu

1. Stáhněte soubor [`Kancelar.apk`](Kancelar.apk) do telefonu (na GitHubu: otevřít soubor → „Download raw file“).
2. Otevřete ho ve Správci souborů a potvrďte instalaci
   (Android se jednou zeptá na povolení „Instalovat neznámé aplikace“).
3. Hotovo – v seznamu aplikací se objeví **Kancelář**.

Požadavky: Android 7.0 nebo novější.

## Co aplikace umí

**Word (.docx)**
- zobrazení dokumentu včetně nadpisů, tučného/kurzívy/podtržení, barev, zarovnání, seznamů, tabulek, obrázků a odkazů
- režim čtení / úprav (tužka vpravo nahoře)
- úpravy: styly nadpisů, B / I / U / S, barva písma a zvýraznění, odrážky a číslování, odsazení, zarovnání, vložení tabulky a odkazu, zpět/znovu
- hledání v textu, zvětšení písma, statistika (počet slov a znaků), tisk a uložení do PDF
- při uložení se zachová záhlaví, zápatí, velikost stránky a styly původního dokumentu

**Excel (.xlsx, .xlsm, .xls, .ods, .csv)**
- mřížka s listy, řádek vzorců, výběr buňky klepnutím (druhým klepnutím začnete psát)
- vzorce s výpočtem: SUMA, PRŮMĚR, KDYŽ, SVYHLEDAT, SUMIF, COUNTIF… (české i anglické názvy, oddělovač `;` i `,`)
- vkládání a mazání řádků a sloupců (odkazy ve vzorcích se posunou), řazení A→Z / Z→A, automatický součet Σ, hledání
- přidání, přejmenování a smazání listu (klepnutím na aktivní záložku listu)
- uložení jako .xlsx, .ods nebo .csv
- ve stavovém řádku součet, průměr a počet čísel ve sloupci

**Obecně**
- otevírání přes systémový výběr souborů (telefon, SD karta, Disk Google, OneDrive…)
- „Otevřít v aplikaci → Kancelář“ ze Správce souborů, e‑mailu apod.
- seznam naposledy otevřených souborů, upozornění na neuložené změny, tmavý režim

### Omezení
- Starý formát Word **.doc** není podporován (je potřeba převést na .docx).
- U Excelu se při uložení nezachovává formátování buněk (barvy, písma, ohraničení) – data, vzorce, listy,
  sloučené buňky a šířky sloupců zůstanou.
- Složité prvky Wordu (textová pole, poznámky pod čarou, komentáře, sledování změn) se při úpravě
  zjednoduší nebo vynechají. Pokud dokument jen čtete a neuložíte, soubor zůstane beze změny.

## Sestavení ze zdrojového kódu

Potřebujete Android Studio nebo JDK 17+ a Android SDK (platforma 34).

```bash
cd android-kancelar
./gradlew assembleRelease
# výsledek: app/build/outputs/apk/release/app-release.apk
```

Release je pro jednoduchost podepsán ladicím klíčem. Pro zveřejnění na Google Play
si vytvořte vlastní podpisový klíč.

## Jak je to uděláno

- `app/src/main/java/.../MainActivity.java` – nativní část: WebView, otevírání a ukládání souborů
  přes Storage Access Framework, tisk.
- `app/src/main/assets/www/` – uživatelské rozhraní (HTML/CSS/JS):
  - `docx.js` – vlastní převod DOCX ↔ HTML (JSZip)
  - `word.js` – editor dokumentů
  - `excel.js`, `formula.js` – tabulkový editor a výpočet vzorců (SheetJS)
  - `lib/` – knihovny [SheetJS](https://sheetjs.com) (Apache 2.0), [JSZip](https://stuk.github.io/jszip/) (MIT)
    a [mammoth](https://github.com/mwilliamson/mammoth.js) (BSD, záložní čtení .docx)
