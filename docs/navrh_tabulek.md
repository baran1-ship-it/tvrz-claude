# Návrh: svět Odkazu Havrana z jednoho zdroje (rádce 27. 10. 10:45)

Podklad: `docs/soupis_pravidel.md` + `docs/soupis/*.md` (stavitel 10:30), reference KCD1 01–20, Astřino zadání kap. 2–10.
Stav: **návrh ke schválení** (Míša, Astra). Hodnoty označené *změřit* se doplní z referencí a měření, ne z hlavy.

## 0. Co soupis ukázal a co z toho plyne
Svět se dnes nestaví z tabulek: `pravidla/*.json` kód skoro nečte, stejná čísla jsou v 6 souborech různě, Blender a Godot
si drží každý vlastní pravdu (cesty, ves, pole, hony), pořadí stavby porušuje „pozdější krok nehýbe dřívějším“ a logika
krajiny (potok, rybník, sklony cest, pole) je špatně už v generátoru. Z toho tři zásady, které návrh plní:

1. **Jeden zdroj = `pravidla/svet/`.** Co je *kde* (lokace, cesty, voda) a *jak* se to staví a kreslí (4 tabulky) je v JSON.
   Blender (`kraj.py`) i Godot (`svet.gd`) **čtou tytéž soubory**. Godot nic neodvozuje zpětně z barvy terénu, Blender nic nezná navíc.
2. **Kód bez vlastních čísel.** Každá konstanta ze soupisu buď přejde do tabulky, nebo se smaže (mrtvý kód). Test `pravidla_cteni`
   hlásí klíč v JSON, který kód nečte, a číslo v kódu, které není v JSON (seznam povolených výjimek je prázdný).
3. **Pevné pořadí a testy.** Stavba světa = pipeline níže; každý krok má test v `rychle` sadě; bez průchodu se nevydává.

## 1. Soubory v `pravidla/svet/`
| soubor | co drží | nahrazuje dnes |
|---|---|---|
| `lokace.json` | každá lokalita: id, typ, **jeden obrys** (polygon), střed, výškový režim (plošina / kotlina / ostroh), budovy[] (půdorys, podlaha_y, dvůr_r, orientace štítu, vchod), příznaky (vyhled, vlastni_stena) | 8 obdélníků tvrze, 6 poloměrů „ve vsi“, `VES_STARE`, `lokace_ves.json` (do něj se slije), ruční obdélníky v shaderech |
| `cesty.json` | každá cesta: id, typ (vozova / ulice / pesina), osa[] (x, z), šířka, napojení (lokace / cesta), prvky na ose: most, brod, lávka, brána | HLAVNI/ODBOCKA/PESINY v kraj.py a svet.gd, barva pásu `Teren_cesta`, zpětné odvozování os |
| `voda.json` | potok: osa[] s **hladinou klesající od pramene k ústí**, min. spád, šířka; rybník: obrys, hladina, hráz (segment), přítok, odtok; příkop: hladina, přítok | `osa.json`, `koryto.gd` směr podle nižšího konce, rybník bez hráze |
| `plochy.json` | pravidla rozdělení krajiny mimo lokace: pole (max sklon, od vsi do m, ne v lomu/dvoře), les (sklon od, sever, okraj), louka kosená (do m od vsi/tvrze), remízek (na mezi, u kamení), skála (sklon od) | `field_strip`, `forest`, hony 2× (kraj.py + zem.gdshader) |
| `pasma.json` | **tabulka 1 ZASAZENÍ** (dnes `pravidla_sveta.json: pasma`, přesune se) | 10 různých odstupů v rozsevech, `_cesty_kere` vzorec |
| `povrchy.json` | **tabulka 2 POVRCHY** | masky rozeseté v shaderech, `hlina_m` nečtený, `p / 2.0` |
| `tridy.json` | **tabulka 3 TŘÍDY** (dnes `pravidla_modelu.json: tridy`, nečte se) | dosahy v main, svet, louka, daylight, predmety, shadery |
| `materialy.json` | **tabulka 4 MATERIÁLY** | `limity_textur.py`, měřítka v shaderech, Blender bump/rough/moss, které se nepřenáší |
| `druhy.json` | druhy rostlin (36) + stanoviště + výplňový mix (dnes v `pravidla_sveta.json`, nečte se) – **kód je začne číst**; mrtvé druhy (`grass_medium_02`, `dandelion_01`) dostanou model nebo se vyřadí z mixu, ne tiše | kosený mix 0,48/0,22 v kódu vs 0,6/0,1 v JSON |

`pravidla_sveta.json` a `pravidla_modelu.json` se **rozpustí** do těchto souborů (žádná třetí sada).

## 2. Tabulka 1 – ZASAZENÍ (`pasma.json`)
Měřeno vždy **od kraje hlíny cesty / od zdi / od hladiny** (jedno měřítko, dnes míchané s osou).
| pásmo | vozová | ulice vsi | pěšina | poznámka |
|---|---|---|---|---|
| jízdní pás | hlína + kameny, nic jiného | – | – | koleje jen vozová |
| sešlapaný drn | 0–2 m | 0–2 m | 0–1 m | KCD1 05, 19 |
| trsy od | 2 m | 2 m | 1 m | |
| keř od | 3 m | 3 m | 1,5 m | |
| kmen od | 6 m | **3 m** (Míša) | 3 m | |
| příčný sklon, rovné, přechod | 1,0 / 0,6 / 5 m | 0,25 / 0,6 / 5 m | 1,0 / 0,3 / 2 m | ze stavitelova měření |
| **podélný sklon max** | **12,5 %** (1:8) | 10 % | 25 % | logika; generátor cestu přeloží, nevyrovnává ±3 m |
| zářez / násyp max | 3 m, úvoz = zářez do svahu | 1 m | 0,5 m | |

Budova: dvůr `dvur_r` rovný (hlína), tráva až za dvorem, kmen ≥ 2,5 m od zdi, keř/kopřivy u zdi ano, podlaha vodorovná,
rozdíl terénu pod půdorysem ≤ 0,3 m (jinak plošina/podezdívka – dnes chýše u lomu 0,88 m).
Voda: břeh 0–1,5 m vlhká zem bez trsů, rákos jen ve skupinách, kameny břehu na skutečné výšce hladiny.
Skála: tráva ne nad sklon *změřit* (návrh 45°), mech jen ve spárách, úlomky u paty do 3 m.
Zapuštění paty rostliny: **podle třídy** (strom −0,15, keř −0,10, trs −0,05, balvan −0,30 … *změřit*), ne per druh; práh „visí“ 0,25 m.

**Pořadí stavby (pipeline, jeden skript `stavba.gd`, každý krok ví jen o předchozích):**
1. terén (Blender z `lokace`/`cesty`/`voda`/`plochy`) → 2. cesty (profil do terénu, sklon v mezích) → 3. budovy (plošiny, dvůr, terén přitažen) →
4. voda (koryto, hladiny, hráz) → 5. masky stanoviště (**až teď, po všech úpravách terénu**) → 6. vegetace (celá, včetně keřů u cest a kompozice lokací) →
7. `_na_povrch` + `_kmeny` + kolize (na **všechno** z kroku 6) → 8. předměty → 9. test `zasazeni`.
Mazání druhů (vrba 3× zasadit, 1× smazat; šípek) se **ruší**: druh se nesází tam, kde nemá být (stanoviště), ne maže dodatečně.

## 3. Tabulka 2 – POVRCHY (`povrchy.json`)
Pravidlo A/B/C (26. 10. 15:20) platí; tabulka k němu dává **druhy povrchu** a **jednu definici masek**.
| druh povrchu | třída | maska (kanál) | textury (atlas) | drsnost | hlína/tráva | kde vzniká |
|---|---|---|---|---|---|---|
| cesta vozová | A | CUSTOM0.r | hlína, štěrk, koleje | 0,85 | 1,0 | z `cesty.json` |
| ulice vsi | A | CUSTOM0.r | hlína udusaná, kaluže v prohlubních | 0,8 / mokro 0,4 | 1,0 | `cesty.json` |
| pěšina | A | CUSTOM0.g | sešlapaná tráva + hlína | 0,9 | 0,6 | `cesty.json` |
| dvůr | A | COLOR.a | hlína, prkna, sláma | 0,85 | 1,0 | `lokace.json` dvur_r |
| pole (lán, strniště – léto) | A | COLOR.r | strniště, hlína | 0,9 | – | `plochy.json` |
| louka kosená / divoká | A | COLOR.g (+ divokost) | tráva nízká / vysoká | 0,9 | – | `plochy.json` |
| břeh | A | COLOR.b | vlhká hlína, štěrk | 0,5 | – | `voda.json` |
| plocha lomu | A | CUSTOM1.r | drť, prach | 0,9 | 1,0 | `lokace.json` |
| stěna lomu, skála, rybník, domy | B | – (díl) | vlastní | vlastní | – | díl, terén přitažen |
| voda | C | – | shader voda, **bez screen texture** | – | – | `voda.json` |
Kanály jsou *návrh*; stavitel potvrdí podle shadery.md (zem je u 13 vzorkovačů – nová textura nahrazuje jinou). Hony a lány **jen jednou** (z `plochy.json`), shader je čte z masky, nepočítá znovu.

## 4. Tabulka 3 – TŘÍDY (`tridy.json`)
Sloupce (26. 10. 16:00/20:05): `dosah_m, lod1_m, impostor_m, stin, stin_m, kolize, kolize_m, nacitani, uvolnit_m, dlazdice_m, zapusteni_m, textura` (odkaz do tabulky 4).
| třída | dosah | LOD1 | impostor | stín (m) | kolize (m) | načítání | poznámka |
|---|---|---|---|---|---|---|---|
| strom | 120 | 60 | 120–900 | ano 60 | kmen válec 40 | dlaždice 64 | `STROM_DOHLED` = konec tvaru, ne stromu |
| keř | 60 | 30 | – | ne | ne | dlaždice | projde se |
| trs / vysoká bylina | 80 (tablet 80) | – | pás 80–130 | ne | ne | louka | dnes 80/110/130 na 3 místech → jedno |
| drn | 25 / 60 (25 %) | – | – | ne | ne | louka | |
| balvan | 120 | 40 | – | ano 40 | konvexní 40 | dlaždice | |
| skála | 500 | 40 / 120 | – | LOD0 | konvexní díly | stálé | výhled – výjimka příznakem |
| dům | 500 | 75 | 1024 (ves) | z LOD1 40 | hrubá (boxy) 40 | portál | |
| tvrz | stálé | LOD čtverce | – | 40 | hrubá | portál | |
| předmět velký / střední / drobný | 80 / 40 / 20 | – | – | ano 40 / ano / ne | hrubá / box / ne | plánovač 1,5 ms | |
| voda | 500 | – | – | ne | ne | stálé | |
| terén | stálé | – | barva krajiny od 100 m | kaskády | HeightMap dlaždice 64 | stálé | |
Globální (dnes rozeseté): stíny **jedna definice** (kaskády, dosahy – daylight vs main se přepisují), hranice světa **jedna** (main vs player/mapa), LOD prah px, rozpočty plánovače. Hodnoty = dnešní měřené (0.93/0.94); změna jen s měřením (K1).

## 5. Tabulka 4 – MATERIÁLY (`materialy.json`)
| třída materiálu | rozlišení | vzor v metrech (*změřit z fotek, meta_2k.json chybí*) | normály | drsnost suché / mokré | zákaz |
|---|---|---|---|---|---|
| terén (zem atlas) | 1024 | hlína 2 m, štěrk 1 m, tráva 1,5 m | OpenGL Y+ | 0,9 / 0,5 | screen texture |
| kámen zdiva | 1024 | kámen 0,25–0,4 m, spára 2 cm | Y+ | 0,85 / 0,6 | lak |
| dřevo (prkno, kulatina, šindel) | 1024 | prkno 0,25 × 3 m, kulatina ⌀ 0,2–0,3, šindel 0,15 × 0,4 | Y+, vlákna po délce | 0,8 / 0,5 | |
| došek | 1024 | vrstva 0,3 m, snop 0,1 | Y+ + geometrie okraje | 0,95 | hladká deska |
| vegetace | 512 | – | – | 0,7 | MSAA, alpha_to_coverage |
| skála | 1024 | vrstva 0,5–1 m | Y+ | 0,85 / 0,5 | |
| voda | – | – | – | – | screen texture |
Přenos z Blenderu: bump/rough_add/dirt/moss **buď se zapečou do textur, nebo se škrtnou** – ne „v Blenderu je, ve hře není“.
Povinný `tex_cache/meta_2k.json` (skutečné rozměry fotek) v repu, jinak test `materialy` neprojde.

## 6. Testy (rychlá sada, ≤ 3 min)
`pravidla_cteni` (každý klíč čten, žádné číslo mimo JSON) · `lokace` (jeden obrys, budovy na plošině) · `cesty` (sklony, napojení, nic přes dům) ·
`voda` (hladina monotónní, spád, hráz níž než přítok) · `plochy` (pole ≤ sklon, les na strmém) · `zasazeni` · `povrchy` · `tridy` · `materialy` · `pravidla_stala` (MSAA vypnuto, žádné primitivum, žádná screen texture).

## 7. Pořadí migrace (každý krok = test + snímek + vydání)
A. **Infrastruktura** (bez změny vzhledu): `pravidla/svet/` + načítání `pravidla.gd`, test `pravidla_cteni`, Blender i Godot čtou `lokace`/`cesty`/`voda`; MSAA od startu pryč, mrtvý kód pryč. Vydání 0.95.
B. **Logika krajiny** (zemětřesení, mantinely Míša 21:15): potok správným směrem a se spádem, rybník s hrází/přítokem/odtokem, cesty ≤ 12,5 % (přeložit, ne jen vyrovnat), pole ≤ 12 %, les na strmém; lokace a výhledová místa zůstávají. Vydání 0.96.
C. **Zasazení** (tabulka 1 + pipeline + stanoviště místo mazání + mrtvé druhy). Vydání 0.97.
D. **Povrchy** (tabulka 2, masky jednou, náves pryč). 0.98.
E. **Třídy** (tabulka 3, všechny dosahy z ní, K1 měření). 0.99.
F. **Materiály** (tabulka 4, meta fotek, Blender přenos). 1.0 = BLOK „svět z jednoho zdroje“ hotov; pak KRÁSA po lokalitách podle Astřina seznamu.

## 8. Otevřené otázky pro Míšu / Astru
1. Mlýn: vodní mlýn potřebuje spád – kam ho potok po opravě přivede (B)? Návrh: pod rybník na odtok (hráz = spád), lom zůstává.
2. Hostinec stojí 43 m nad údolím s cestou 64 % – přesunout hostinec k cestě v údolí, nebo přeložit cestu serpentinou? (B)
3. Kanály masek (3) a hodnoty vzorů (5) – stavitel změří, Astra zkontroluje.

---
## 9. Změny po kontrole Astry (27. 10. 10:55) – platí nad kap. 1–7
1. **Globální soubory** v `pravidla/svet/`: `svet.json` (hranice světa – jedna, jednotky, souřadnice, seed), `generovani.json` (terénní šumy, velikosti dlaždic), `prostredi.json` (vítr – jeden směr pro trávu, listí i vodu; slunce, kaskády stínů, atmosféra), `rozpocty.json` (načítání, paměť, callů/troj. – chráněné už od kroku A).
2. **Katalog modelů `modely.json`**: model_id, scéna, třída, materiály po částech, rozměry, pata (zapuštění: výchozí z třídy, korekce per model), kolizní model, varianty. **Rozmístění** = buď poloha+orientace (lokace), nebo pravidlo rozsevu (hustota, rozestup, rozsah měřítka) v `druhy.json`.
3. **Sloupce**: cesty – `pricny_podil`, `rovne_sirka_m`, `prechod_sirka_m` zvlášť; plochy – `priorita` při překryvu + `prechod_m`; třídy – `lod[]` (pole vzdáleností), `impostor_od_m` / `impostor_do_m` zvlášť, `nacist_m` / `uvolnit_m`. Oprava: u domů je 1024 m **dlaždice impostorů**, ne vzdálenost; dům: lod [75, 500], impostor od 500 (ves z dálky) – bez mezery.
4. **Pipeline v2** (nahrazuje kap. 2): 1 terén hrubý → 2 voda (koryto, hladiny, hráz, přítok/odtok) → 3 cesty (profil, brody, mosty, sklony) → 4 plošiny budov a dvorů → **ZÁMEK TERÉNU** (od teď nic terén nemění) → 5 masky základní (stanoviště z terénu, vody, cest, ploch) → 6 stromy → 7 kryt korun (maska stínu) → 8 podrost a keře (podle 5+7) → 9 předměty → 10 usazení + kmeny + kolize **všeho** z 6–9 → 11 povrchy vizuální (shader z masek) → testy.
5. **Masky**: kanály z kap. 3 **neplatí**. Nejdřív `masky.md` = slovník: význam, rozsah, výchozí hodnota, kdo zapisuje, kdo čte, verze formátu; dnešní obsazení (CUSTOM0/1 cesta+koleje+bahno, COLOR.b les, COLOR.a břeh/dno) se zachová a rozšíří. Význam masky oddělen od fyzického kanálu (shader čte přes jména). Zachovat lesní půdu; rozlišit vozová/ulice a kosená/divoká.
6. **Vzory v metrech**: `repeat_size_m [š, v]`, způsob mapování, směr vláken, výřez atlasu, **zvlášť** rozměr prvku (kámen, prkno) a rozměr opakování; u každé hodnoty zdroj měření a stav `overeno | odhad`. Všechny hodnoty v kap. 5 = odhad.
7. **Migrace**: do **A** navíc slovník masek, katalog modelů, kontrakt pipeline (rozhraní kroků), rozpočty; jejich zapojení je součást **B**. Datové masky (z D) musí být **před** rozsevem (C) – D se dělí na D-data (do B/C) a D-vzhled (později). Pravidlo zní: **„žádný laditelný parametr světa v kódu“** (matematické konstanty a indexy ano). Na konci migrace kontrola, že klíč svět skutečně ovlivňuje (A/B snímek při změně hodnoty), ne jen že se čte.
8. **Test vody (oprava)**: odtok níž než přítok (ne koruna hráze); hladina rybníka vodorovná; min. spád jen na tekoucích úsecích.
