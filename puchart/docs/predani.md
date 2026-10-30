# Předání – Puchart (stav 30. 10. 2026 ráno)

## 30. 10. odpoledne: uzavřené předhradí, branka do dolního hradu, interiéry věží (Míša: snímky z tabletu)
- Zeď na valu napojená na JZ nároží horního hradu, z druhé strany vstupní branky nová zeď po hřebeni V valu k V zdi
  jádra → předhradí (předbraní, most, příkop) uzavřené. Data `hrad_puchart.json` A.hradba_val, A.hradba_vychod.
- Cesta do dolního hradu z horního hradu: **branka v jižní zdi u věžičky** (A.branka, NAVRH – terén tam klesá k hřbetu
  nejmírněji; palác zkrácen o 5 m kvůli průchodu), předprostor a serpentina na hřbet (`cesty_puchart.json` hrebenova).
- Padací mosty: sklon byl obráceně (visely ve vzduchu) → leží a navazují na pevnou mostovku až na práh.
- Křídla vrat: materiál se tvořil až po uložení (bílá) → `lib.MAT` vyrábí materiál při prvním použití, UV v metrech.
- Zábradlí ochozů: sloupky po 1,5 m (dřív bez sloupků, viselo), v rozích průsečík se zábradlím sousední zdi (dřív díry).
- **Věž zadního hradu** (B.vez): vyvýšený vstup z ochozu v patře 15,5 (historicky správně), sklad dole jen po schodech
  shora, strážní patra 18,7 / 21,9 / 25,1 a podkroví 28,3; trámové stropy, schody podél stěn kolem dokola (45°, rohové
  podesty), otvory v podlahách se zábradlím. **Věžička** předního hradu (5,5 m): komora v úrovni ochozu + strážní patro.
- Test průchodu: 9 tras OK (A_vstup, A_ochoz, A_vezicka – až do strážního patra, A_branka, B_vstup, B_ochoz_vez,
  B_vez_nahoru – až do podkroví, B_vez_sklep, cesta_mezi_hrady – z nádvoří brankou až k mostu přes průrvu).
- Procházka: místa ve věžích a u branky, seznam míst posuvný (nevešel se na tablet).

## NEJNOVĚJŠÍ 30. 10.: dvojhradí podle dochovaných zdrojů a kreseb, průchozí, APK test + procházka
- Zdroje dohledány a sepsány v `docs/hrady_zdroje.md`: kresebné rekonstrukce a plán z GC80T08, atlas (Tomášek 2015),
  turistika.cz (palác 10×12), sborník SOkA Přerov 2004, DMR 5G (lokální reliéf `docs/screens/hrady_relief.png`), bod OSM.
- **Chyba #13:** staré polohy z georeferencovaného plánu atlasu byly posunuté (přední hrad o 12 m na svah, zadní o 50 m
  na úbočí). Teď hrady stojí na skutečných valech a skalním suku. Pravidlo: před stavbou poloha nad reliéfem DMR + OSM.
- Data `pravidla/svet/hrad_puchart.json` (každý díl má jistota DOLOZENO/KRESBA/NAVRH), stavba `blender/puchart_hrad.py`
  (stavebnice Havrana přes `hrady.py`), terén `nastroje/teren_upravy.py` (plošiny, rampa za branou, průrva – valy jsou v DMR).
  Palisáda zrušena; místo ní kamenná zeď po hřebeni valu s brankou (kresba). Krytí ochozů zrušeno (kresby: otevřené cimbuří).
- Kolize jako v Havranu: uzel KOLIZE z kvádrů (zdivo samo, mostovka = šikmá deska zapuštěná do terénu, schody = rampa,
  pavlač + zábradlí, nájezdy přes prahy), ve hře skrytý. Křídla vrat otevřená.
- **Test průchodu** `PUCHART_TEST=pruchod godot --headless` (v `hra/`): postava sama projde trasy z `hra/data/pruchody.json`
  (generuje stavitel ze stejné geometrie): A_vstup (cesta → branka → předbraní → most → brána → nádvoří), A_ochoz (schody,
  podesta, pavlač, nad branou, kolem SZ rohu), A_vezicka, B_vstup (hřbet → most přes průrvu → brána → kamenné schody
  na horní nádvoří), B_ochoz_vez (schody na ochoz, kolem celé čelní hradby, lávka do věže), cesta_mezi_hrady. **Vše OK.**
  Test našel a opravil: schod na prahu branky, kolizi budovy až do střechy (blokovala ochoz), nástup mostu B pod cestou,
  zeď na valu přes průjezd branky, cestu souběžnou s mostem.
- Hráč: **létání** (tlačítko Létání + ▲/▼ vpravo dole, F, E/Q, LB/RB; bez kolize, dopředu = kam se díváš), místa procházky
  vč. ochozů (`mista.json` volitelné y).
- APK (`nastroje/export_apk.sh`, textury hradu omezené `import_hrady.py` podle `rozpocty.json`): `apk/puchart_test.apk`
  (měření → procházka) a `apk/puchart_prochazka.apk` (rovnou procházka), 95,4 MB.
- Pořadí přestavby: teren_upravy → cesty → teren_dlazdice → r16z → puchart_hrad.py → godot --import → import_hrady.py →
  godot --import → test průchodu → export_apk.sh.
- Dál: měření na tabletu (hrad nyní 0,37 M troj. v detailu, dálková verze 16 k), interiéry (palác, věž – zatím plné),
  textury, les p95 < 40 ms.


## Hotovo (krok A podklady + základ D)
- Poloha: přední hrad N 49.611560 E 17.682476 (OSM ruins, atlas). Výsek 2×2 km (`svet.json`), obzor 10×9 km.
- DMR 5G: 31 mapových listů (`zdroje_dat.json`), hustota 0,076–0,09 bodu/m² (TIN klíčové body → efektivně ~3,6 m).
  Snímky: `docs/screens/00_*.png` (přehled, toky, ostroh, obzor).
- Toky z terénu (D8, `toky.py`): OSM leží 15 m vedle dna → osy z terénu, jména z OSM. `voda.json` v souřadnicích hry.
- Maska stanovišť (`stanoviste.py`, pravidla z Havrana plochy.json): louka 48 %, les 47 %, skála 2 %, břeh 3 %.
- Pečené dlaždice 250 m, LOD 2/4/8/16 m se sukní, obzor 40 m; kolize HeightMapShape3D jen kolem hráče.
- Godot 4.4.1 Compatibility projekt `hra/`: shader terénu (pole textur, 4 vzorkovače), panel měření, prozatímní hráč.
  Snímek `docs/screens/01_louka_k_hradu.png`: PC 33 kreslení, 0,36 M troj. (tablet NEOVERENO).
- Pravidla a tabulky Havrana převzaty (`docs/pravidla_prevzeti.md`), tabulka chyb `docs/chyby.md`.

## Hotovo 29. 10. večer (skutečná podoba místa)
- Biotopy AOPK + PPV + DMP 1G → stanoviště 1393 a 60 362 stromů (`docs/reference_mista.md`, `historie_vegetace.json`).
- Les ve hře: LOD0 do 22 m, vlastní LOD1 (30 % karet), karty dál; PC 1,83 M troj., 301 kreslení, VRAM 315 MB (tablet NEOVERENO).
- Godot/Terrain3D: `docs/godot_verze.md`.

## Hotovo 29. 10. noc (hrady, A/B)
- Plán atlasu zaměřen na DMR (`plan_atlas.py`, `plan_prekryv.py`): zadní hrad 47 m pod předním na V úbočí.
- Terénní úpravy valů a příkopů (`teren_upravy.py`, před pečením). Vyhlídka na protějším svahu (paseka).
- 4 návrhy hradu (`blender/hrady.py`, `hrady_navrhy.json`, `docs/hrady_navrhy.md`, snímky `docs/screens/hrad_*.jpg`).
- Terén ve hře ze souboru výšek ve vláknech (2,7 s na PC), sdílené textury stromů, byliny u hráče.
- A/B srovnání: měřicí trasa (`hra/scripts/mereni.gd`), APK B (4.7.2) a C (Terrain3D) – `docs/ab_srovnani.md`.
  Úspory APK: staré stromy zblízka LOD1, normály stromů 256, pole normál půdy 512, výšky r16z (roviny bajtů + zstd),
  bez auto-LOD a stínových sítí u modelů s vlastním LOD. Limit GitHubu 100 MB/soubor.

## Stav 30. 10. (rozpracováno – navázat odsud)
- A/B hotovo: Terrain3D ne, **přechod na Godot 4.7.2** (kopie projektu v build/ab/g47 už běží na 4.7.2; hlavní `hra/` přepnout).
- Hrad: finální směr **varianta 6** (`hrady_navrhy.json` 6_final, list `docs/screens/hrad_6_final.jpg`): přední hrad z v.1,
  hlavní brána na S, padací mosty, skalní průrva, palisáda po hraně plošiny (`nastroje/palisada_hrana.py`).
- Příjezd: hlavní cesta ze S po hřbetu (doloženo valy a terénem), stezka z údolí; `nastroje/pristup.py`, `nastroje/cesty.py`,
  `pravidla/svet/cesty_puchart.json`. Podloží droby/břidlice (ČGS GeoČR50).
- Rozpracováno: **impostory stromů** (`blender/impostory.py` z Havrana běží, výstup hra/textury/impostory),
  shader `hra/shaders/impostor.gdshader` převzat; zbývá zapojit do `les.gd` místo karet _daleko (vzor Havran svet.gd
  `_impostory`: MultiMesh po buňkách, INSTANCE_CUSTOM = pata + měřítko/otočení) a změřit APK na tabletu (cíl les p95 < 40 ms).
- Pak: hrad dle KCD2 + Havrana (herní verze s LOD, detail), mapa dle KCD2 (Havran `scripts/mapa.gd`, pergamen).

## Stav 30. 10. ráno (po tabletu D)
- Měření D: hrad 11,7 / les 44,8 / voda 21,7 / vyhlídka 35,9 ms p95 – les ještě ~5 ms nad cílem.
- Míša: „mosty, brány, ochozy nejsou domyšlené“ – rozpis vad a správné řešení v `docs/chyby.md` #7–#12.
  PŘÍŠTĚ NEJDŘÍV: přepracovat v `blender/hrady.py` vez(brana)->průjezd, most_padaci (navázání výšek), ochoz_kryty
  (podlaha + sloupky na podlaze + stříška), schody na podlahu ochozu; ověřit snímky z procházky stejných míst.
- Les: zkrátit plné stromy (lod0 22 -> 16 m, blizko 40 -> 32 m) a změřit.

## Další krok
1. Les pod 1,5 M troj. (impostory skupin / menší LOD0 kmenů), modely javor/jasan/habr/jilm, podrost a kameny z droby.
2. Návrhy hradů (`docs/hrady_zadani.md`) – ke schválení Míšou před stavbou.
3. Cesty výseku (plánovač sklonu), Boňkov (dvorce jako ves B Havrana), mlýny na Veličce.
4. Převést hlídače (test smyslu, matice vztahů, tabulka chyb) do `nastroje/`.

## Nový kontejner
`bash nastroje/postav_vse.sh` (Godot 4.4.1: `curl -L https://github.com/godotengine/godot/releases/download/4.4.1-stable/Godot_v4.4.1-stable_linux.x86_64.zip`).
