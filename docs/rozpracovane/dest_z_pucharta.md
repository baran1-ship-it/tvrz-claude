# Déšť z Pucharta (Míša 13. 11.: „u Pucharta je připravena změna počasí, vem si ji i pro Havrana“)

Zdroj: větev origin/ccr-f2d32673-9fi7m5, commit 6d4c1b0e (12. 11.) – `puchart/hra/scripts/pocasi.gd`,
`shaders/dest.gdshader`, `pravidla/svet/pocasi.json`, úprava `den.gd` (zatažení), uniform `mokro` v shaderech povrchů,
zvuky `hra/zvuky/pocasi/` (Ylmir „Rain loopable“, OpenGameArt, CC0 → do titulků), rešerše `docs/reference/reserse_dest_kcd.md`.
Snímek prohlédnut (dest_ves.png): závoj čar kolem kamery, zatažená šedá obloha, tmavší mokrá zem – vypadá dobře.

Co to dělá: rozvrh deterministicky podle čísla dne (2–6 dní mezi dešti, 1–4 h, síla 0,55–1), zatahování → mrholení →
vrchol → doznívání → osychání; 2 průhledné válce kolem kamery (bez čtení obrazovky – pravidlo tabletu OK), 1 CPUParticles3D
odstřiky, mokré povrchy (tmavší, lesklejší), zvuk slabý/silný, pod střechou (paprsek nahoru) tlumený a bez kapek.

Převzetí do Havrana (na další verzi, PO vydání 0.99999 – změna scripts/ by zneplatnila běh celé sady k otisku):
1. `pravidla/svet/pocasi.json` (čísla jen v datech), `scripts/pocasi.gd`, `shaders/dest.gdshader`, zvuky + titulky.
2. Napojit na náš den/oblohu (u nás jiný skript než Puchartův den.gd – hledat ekvivalent `zatazeni` / přepočtu oblohy).
3. `mokro` do našich shaderů terénu, zdiva a dřeva (jen ty, které už jsou ShaderMaterial; StandardMaterial3D řešit zvlášť).
4. Měřicí trasa: varianta s vynuceným deštěm (Puchart přidal „les dest“, „hrad dest“) → `docs/mereni_verze.md`.
5. Test: déšť se v rozvrhu objeví, pod střechou nejsou kapky, snímek s deštěm prohlédnout sám.

## Stav 13. 11. večer (po vydání 0.999994)
- Hotovo v kódu: `pravidla/svet/pocasi.json` (poznámky jako `_klíč`, čísla odstřiků a přechodů z kódu do dat), `scripts/pocasi.gd`
  (čte `Pravidla`, den z `daylight.gd`), `shaders/dest.gdshader` (beze změny; předehřátí ho vezme z `res://shaders`),
  `daylight.gd` `zatazeni` + `_zatazit` + `prekresli` (obloha šedne, `cloud_cover` z `obloha.mraky_kryti`).
- Zvuky: Havranovy `zvuky/prostredi/dest.ogg` a `dest_strecha.ogg` (CC0, už v seznamu) – venku / pod střechou (paprsek vzhůru
  jako Puchart; `daylight.interior` = kolik oblohy je vidět, ne střecha → nepoužito).
- Měřicí trasa: varianta `dest` (vynucený plný déšť); do seznamu variant až při vydání.
- Test `pocasi`: rozvrh 60 dní (počet dešťů, délka, zatažení předem), závoj venku ano, v hostinci ne.
- Zbývá: `mokro` do našich shaderů (žádný zatím nemá – krok 3), snímek deště prohlédnout, měření na tabletu (NEOVĚŘENO).
