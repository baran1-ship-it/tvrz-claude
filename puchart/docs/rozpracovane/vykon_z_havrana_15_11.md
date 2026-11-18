# Výkon: co si vzít z Havranova rozboru GPU (15. 11.)

Zdroj: Havran `docs/rozpracovane/rozbor_gpu_15_11.md` (větev claude/new-session-0dtk58), Míša 15. 11.: „Havran jede na grafiku,
možná se ti bude něco hodit“. Porovnání s Puchartem (kód 15. 11.):

| Havran zjištění | Puchart | Akce |
|---|---|---|
| Terén jedna obří síť na pásmo, bez LOD (547 tis. troj. stále) | **už dlaždice + LOD** (`scripts/svet.gd` _lod, visibility_range) | nic – ověřit jen počet troj. terénu v panelu |
| Uvnitř krčmy se kreslí celý venkovní svět (1,2–1,6 M prim.) | **totéž** – vnitřky mají jen `vnitrek_do_m`, venkovní svět (les, louka, terén, hrad) se uvnitř kreslí dál | **P1:** režim „uvnitř“ (hráč pod střechou celku/domu: zkrátit dohled louky/lesa/dálky, nebo okluzory zdí krčmy/hájovny/domů) – data `rozpocty.json uvnitr`, měřit snímkem v krčmě |
| Nové MultiMeshe při každé přestavbě buňky (alokace GPU bufferu dokola, špička 1,2 s) | `bunky_kolem.gd`, `byliny.gd`, `les.gd`, `louka.gd` dělají `MultiMesh.new()` za hry | **P2:** pevná zásoba MultiMeshů (kruh slotů), přestavba = přepis bufferu; ověřit na trase řádkem záseků |
| Diag čte buffer MultiMeshe z GPU (`get_instance_transform` na `mm.buffer`) = synchronizace CPU–GPU | Puchart diag to nedělá | nic |
| Plný panel stojí 7–11 ms | panel Puchartu také prochází strom? | **P3:** změřit cenu panelu (zapnutý/vypnutý), drahé části jen na požádání |
| „shadery +0“ v Compatibility nic nedokazuje (`get_pipeline_compilations` vždy 0) | platí i pro Puchart | do docs/kcd_grafika_tablet.md poznámka |
| Impostory obzoru v buňkách 1024 m bez visibility_range | Puchart les dálky – zkontrolovat buňky a `visibility_range_end` | **P4:** kontrola les.gd dálky |
| Stínová tělesa (`SHADOWS_ONLY`) panel počítá jako viditelná | Puchart má `_Daleko_Stin` u domů | panel: oddělit viditelné/stín (`get_render_info TYPE_VISIBLE/TYPE_SHADOW`) |

Pořadí: po dokončení funkcí a hlídačů, před vydáním APK měřit P1 a P3 (rychlé), P2 a P4 podle výsledku.

## Video Míši 16. 11. (LOD stromů a trávy) – co z toho pro Puchart
| Technika z videa | Puchart dnes | Akce po APK |
|---|---|---|
| Časované prolnutí LOD (timed fade 0,25 s místo pásma podle vzdálenosti – strom kreslen dvakrát jen chvíli) | stromy: doplňkový dithering v pásmu `prolinani_m` (10 m) – v pásmu běží oba stupně (discard), les.gd _fade | P2: časované prolnutí v shaderu (čas spuštění v INSTANCE_CUSTOM), změřit dvojí kreslení v pásmu, Havran to plánuje také |
| LOD0–LOD3 + impostor (2 troj.) | plný strom → jednoduchý tvar → impostor (atlas 8×8, Havran) | jen ověřit počty troj. stupňů |
| Tráva: dither maska do dálky | byliny i louka – rozpouštění ditheringem / zmenšení trsu podle hustoty(vzdálenost) | nic |
| Tráva z dálky: impostorové buňky (2 troj./buňka místo karet) | louka jen v okruhu buněk, dál barva terénu | P3: zvážit „travní impostor“ pásmo, pokud dálka louky vypadá holá |
| Záseky Havrana (bohatší příroda) | Puchart P2 výše: zásoba MultiMeshů, plánovač | měřit trasou na tabletu |

## Stav 17. 11. (bod 1b plánu po APK)
- **P2 hotovo:** `hra/scripts/zasoba_mm.gd` (rozpocty.json `zasoba_mm`) – louka, byliny, keře, les zblízka, kameny koryt,
  rostliny skal a drobnosti vsi berou MultiMesh ze zásoby; přestavba = přepis bufferu stejné velikosti (`glBufferData` bez
  `glGenBuffers`), slot znovu až po 3 snímcích. Zdroj Godot 4.7.2 gles3 `mesh_storage.cpp`: změna sítě u MultiMeshe
  s nahraným bufferem čte buffer z GPU → klíč zásoby obsahuje síť. Havran K5 zatím jen v plánu – tady první.
- **Časované prolnutí stromů hotovo** (bez kopie obrazovky, bez vzorkovače navíc): shader porovná vzdálenost stromu teď
  a před `cas_s` (uniform `kamera_pred`) → bez stavu na strom; `stromy_modely.json lod_casove`, A/B `PUCHART_LOD_PASMO=1`.
- **Měření PC** (llvmpipe, 1200×750 = 75 %, stejná trasa, A = vše vypnuto, B1 = P2 + časovaný LOD, B = + houštiny):

| úsek | A p50/p95 | B1 p50/p95 | B p50/p95 | A/B1/B >2×p50 | troj M A/B |
|---|---|---|---|---|---|
| hrad | 248/312 | 210/242 | 218/255 | 0/0/0 | 1,82/1,83 |
| les | 485/1145 | 335/548 | 381/565 | 30/0/0 | 1,36/1,47 |
| voda | 265/323 | 187/226 | 194/262 | 0/0/0 | 1,06/1,10 |
| vyhlídka | 239/341 | 151/209 | 170/225 | 0/0/0 | 0,89/0,93 |
| les znovu | 353/719 | 334/554 | 381/579 | 15/0/0 | 1,33/1,45 |

  Alokací MultiMeshů za trasu: A 20 257 → B 9 257 nových + 12 247 znovu (volných na konci 442, VRAM +8 MB).
  Pozor: llvmpipe kreslí na CPU (každý snímek > 40 ms), rozptyl mezi běhy velký (výchozí běh téže verze les p50 341,
  p95 736) – směr ano, čísla pro tablet NEOVERENO. Záseky tabletu změří Míša (řádek „zásoba MM“ a sloupec >2×p50 v měření).

## Tráva podle Havrana (17. 11., Míša: „Havran má velkou hustotu trávy, ale pod stromy v lese ne, a už mu i FPS vychází“)
Havran (FETCH claude/new-session-0dtk58 d53fa65): `pravidla/svet/les_podrost.json`, `scripts/svet.gd` _koruny_stin/zapoj_v/_puda_zapoj,
`scripts/louka.gd` _svetlo_lesa, `modely.json trava_unshaded`, `docs/mereni_verze.md`.

| | Havran | Puchart před | Puchart teď |
|---|---|---|---|
| koruny pro trávu | všechny stromy po všech krocích sázení, poloměr z glb modelu | stromy.bin, poloměr 0,2 × výška (modely mají 0,23–0,6, buk 0,32–0,35) → koruny 1,6× užší | jako Havran: glb × měřítko les.gd (`nastroje/kryt_korun.py`) |
| zápoj | krytí × zápoj okolí (samotný strom v louce bez zápoje), přechod 6 m | jen třídy les_*/luh, kryt 0,6–1,0 | krytí × okolí 0,35–0,6 (les Puchartu má krytí 0,59), přechod 3 m, všechny třídy |
| tráva pod zápojem | × 0,015 (nic) | × 0,1 (louka 0,05 trsu/bod), byliny tráva bez omezení | × 0,015; byliny tráva/vysoká také (`byliny.json zapoj`) |
| tráva na světle v lese | jako louka | 0,5 | 0,9 (jako paseka/okraj) |
| půda pod zápojem | zem.gdshader hrabanka/listí z masky + zápoj | opad jen podle masky svahu | zem.gdshader: zápoj → opad, světlina v lese → drn (`louka.json les.puda`) |
| podrost | řídké kapradí/byliny z atlasu podle zápoje | byliny.gd kapradí, mech, ostružiník podle třídy | beze změny (už je) |
| tráva bez stínového průchodu | `trava_unshaded` (v datech tablet **false** – barva lesa; měřeno: unshaded p50 ≈ bez trávy) | stínovaná všude (stebla vertex_lighting) | **tablet unshaded** (`louka.json unshaded`), světlo okolí + slunce × (1 − 0,6 × zápoj), kalibrace barvy na PC ±2 % |

Co Havranovi dalo FPS (jeho měření 0.9999991, tablet): dlaždice terénu (louka −12, tvrz-cesta −14 ms p50), méně trávy pod
korunami (les 21/33 ms) a jádro korun; unshaded tráva naměřena 0.99992 (p50 ≈ bez trávy), ale vydaná jen jako varianta.
Puchart tablet 17. 11.: les 35,2 ms, bez trávy 22,9 → tráva v lese 12 ms; Havranova zkušenost: ~60 % ceny trávy = stínový průchod.

Měření PC 17. 11. (llvmpipe, souběžně cizí Godoty, `PUCHART_MERENI_JEN=les PUCHART_MERENI_RYCHLE=1` – 16 snímků na úsek,
před = moje soubory z b362d2a, oba stavy 2 běhy těsně po sobě; **pro tablet NEOVERENO**, llvmpipe kreslí na CPU – stínový
průchod trávy tu cenu nemá jako na Adrenu), p50 / p95 ms, běh 1 · běh 2:

| úsek | před | po |
|---|---|---|
| les | 491/765 · 467/755 | 455/694 · 431/819 |
| les bez trávy | 437/689 · 442/683 | 494/709 · 449/726 |
| les tráva stínovaná | 459/761 · 454/814 | 453/702 · 453/769 |
| les tráva unshaded | (před: metoda chybí = les) | 462/698 · 463/828 |
| troj M les | 1,55 · 1,55 | 1,50 · 1,51 |

PC: les p50 −6 až −8 % (v šumu), trojúhelníky −0,05 M; unshaded na llvmpipe bez rozdílu (očekávané – rozhodne tablet).
Deterministicky (trsy louky do 66 m / trávy bylin do 32 m z dat): zapojený les (372, −195) 9 039 → 995 (−89 %) / 390 → 6;
měřicí úsek les (−160, −160, hlavně paseka a suť) 34 499 → 31 702 / 4 213 → 3 635; okraj (−60, −140) −14 %; louka beze změny;
vyhlídka (bučina s mezerami) +29 % (světliny 0,9). Tablet: změří Míša – varianty `les trava stinovana` / `les trava unshaded`.
Snímky: `docs/screens/trava_havran_17_11_{pred,po,un}_{les,okraj,louka}.png`. Test: `smysl:trava_zapoj`.
Zbývá: tablet změřit (les, varianty stínovaná/unshaded) a porovnat barvu unshaded trávy na tabletu a v jiných denních dobách
(kalibrace jen PC odpoledne); unshaded tráva nemá stín samotných stromů na louce (zápoj okolí = 0 – snímek _un_okraj: chybí stín
koruny vlevo) – když bude vadit, stin_korun z čistého krytí místo zápoje; louka krok 0,5 m (Havran 0,36 + drn) – hustší jen po
měření tabletu (rozpočet scén 2,1 M troj.).

## Měření tabletu 18. 11. (a9930dd, Compatibility 75 %, snímek docs/screens/misa_18_11_mereni_compat.jpg)
| úsek | 17. 11. (24f5ac0) p50/p95, záseky | 18. 11. (a9930dd) p50/p95, záseky |
|---|---|---|
| hrad | 13,4 / 20,0, 0 | 13,9 / 20,2, 0 |
| les | 35,2 / 51,6, 187 | 34,7 / 44,8, 161 (les znovu 30,3 / 39,5, 36) |
| voda | 27,7 / 49,1, 84 | 27,7 / 40,0, 55 |
| výhled | 26,7 / 30,3, 0 | 23,9 / 29,4, 0 |
| les bez trávy | 22,9 / 33,7 | 25,9 / 36,8 |
| les tráva stínovaná / unshaded | – | 31,1 / 43,3, 73 · 30,2 / 39,1, 36 |
VRAM 859 → 707 MB (Godot textury 444 MB). Zásoba MM: znovu použito 37 926, nových 19 574. Les na prvním úseku
horší než „les znovu“ (náběh/načítání) – reálně ~30 ms p50, p95 ~40 ms. Unshaded tráva p95 −4 ms, poloviční záseky.
