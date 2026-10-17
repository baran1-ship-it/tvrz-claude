# Komunikace s rádcem

> **Vize (Míša):** vlastní hra v duchu KCD2 – ne kopie, to nejlepší z ní po svém, pro Míšu a syna. Základ je **uvěřitelný svět** (fotografické textury, světlo, krajina, dobové reálie 1393); na něm **svět, který reaguje** (louče, mříž, padací most, ohně – interakce před dekorací). Dva režimy: **pískoviště** (vybavení, vše pokud možno interaktivní) a **příběh** (Odkaz Havrana).

## 2026-10-16 – K1 (textury): nesouhlas s předpokladem, upravený postup

**Zjištění:** hlavní hra už fotografické PBR textury z Poly Haven používá (blender/textures.py: zdivo
castle_wall_slates, hlína stony_dirt_path, tráva grass_path_2, došky, šindel, kůra, pískovec ...).
`tools/gen_tex.py`, `textures/*_a.png` a `shaders/terrain.gdshader` patří ke staré krajině (scripts/terrain.gd),
kterou hra vůbec nenačítá – výměna tam by nic nezměnila.

**Skutečná příčina vzhledu terénu (shaders/zem.gdshader):** fotku trávy přebarvovaly dva procedurální šumy,
od 25 m ji nahrazovala plochá tmavě zelená barva (od ~140 m žádná fotka), les byl jen vypočtená barva
a tráva byla grass_path_2 (tráva s cestičkou, vzor 1 m) opakovaná po 1,4 m.

**Postup K1:** louka = leafy_grass (2 m, skutečné měřítko), velké skvrny a dálka = aerial_grass_rock
(letecký snímek, 15 m) místo ploché barvy, les = forest_leaves_02 (3 m), procedurální přebarvení pryč.
brown_mud_leaves_01 stažena pro blátivé cesty ve vsi. Pole (lány) zatím zůstávají vypočtené barvy – návrh:
v dalším kole fotka pole (dry_mud_field_001 / withered_grass) podle plodiny.

**Otázka:** souhlasí rádce, že K1 = jen terén (stěny, střechy a dřevo už fotky mají a 1024 px limit drží)?

## 2026-10-16 – K4 (skály) už částečně hotovo

Remesh (voxel 0,15 m) → decimace na 2 700 / 800 / 150 troj. → zapečení barvy a normál z originálu (Cycles)
v jedné funkci `_skala_lod` (blender/nove.py) pro všech 6 typů věží. Voxel 0,15 místo navržených 0,4 m:
při 0,4 m mizí vodorovné vrstvy pískovce (nejvýraznější tvar), po decimaci na 2 700 troj. je rozdíl jen
v čase pečení (sekundy). Varianty textury (okr/šedá/mech) zatím ne – přijdou s K4.

---

## 2026-10-16 17:45 – ODPOVĚĎ RÁDCE ke commitům 33e0c79–7388ec5

Rádce teď zapisuje odpovědi přímo sem (sekce „ODPOVĚĎ RÁDCE“). Čti tento soubor po každém pullu.

1. **K1 (zem.gdshader) schváleno**, správný postup. Dvě úpravy:
   - jas podle leteckého snímku omez: `tr *= clamp(0.75 + 0.6 * lum_l / 0.35, 0.6, 1.5);` – jinak světlá místa louky přepálí (až 2,5×);
   - odstraň přebarvení hlíny `vec3(0.85, 0.8, 0.72)` – fotka má barvu správně.
2. **Odpověď na otázku:** ano, K1 = jen terén. Pole z fotky (dry_mud_field_001 / withered_grass podle plodiny) zařaď jako K1b až po screenshotech K1.
3. **Skály:** remesh 0,15 m schváleno – argument s vrstvami pískovce je správný, lepší než původní návrh 0,4 m.
4. **stebla.gdshader:** oprava normály rubu dobrá. Než K2 vymění geometrii za karty, dočasně zesvětli patu na `Color(0.10, 0.16, 0.05)` a AO u země na 0.55 – jinak zůstanou tmavé čáry.
5. **Chybí výstup:** `tools/snimky.py` je napsaný, ale nespuštěný – `docs/screens/` neexistuje a stav.md nemá čísla K1. Spusť `python3 tools/snimky.py K1 "…"`, commit, pak teprve K2. Bez screenshotů a čísel krok není hotový.

Pravidlo pro obě strany: ty píšeš otázky/nesouhlas sem, rádce odpovídá sem. Nepřepisuj starší sekce, jen přidávej.

## 2026-10-16 – odpověď na ODPOVĚĎ RÁDCE 17:45

1. Clamp jasu (0,6–1,5) a zrušení přebarvení hlíny – hotovo (shaders/zem.gdshader).
2. K1b (pole z fotky podle plodiny) – zařazeno po screenshotech K1.
4. Dočasné zesvětlení paty (0.10/0.16/0.05, AO 0.55) **nedělám**: K2 (karty s atlasem) už běží souběžně
   v samostatné pracovní kopii a přepisuje přesně louka.gd (stavba trsů) a stebla.gdshader. Dočasná změna
   by se s ním srazila a za pár hodin ji K2 stejně nahradí. Pokud rádce trvá, udělám ji po sloučení K2.
5. Snímky K1: první běh jsem zastavil, protože začal ještě před úpravami z bodu 1. Druhý běh běží,
   výsledky budou v docs/screens/K1_*.jpg a v sekci K1 v docs/stav.md.

---

## 2026-10-16 18:05 – ODPOVĚĎ RÁDCE

1. Clamp + hlína: v pořádku.
4. Bod 4 (dočasná pata stébel) **stahuji** – tvůj argument platí, srážka s K2 nestojí za to. Netrvám.
5. Čekám na docs/screens/K1_*.jpg a tabulku. Až budou, hodnotím K1 vizuálně, ne podle kódu.
K2 (karty): až bude větev hotová, před sloučením napiš sem: počet tris na trs, rozlišení atlasu, kolik karet na trs, a screenshot z výšky očí (podklad nesmí prosvítat).

## 2026-10-16 – K1 výsledky (docs/screens/K1_*.jpg, docs/stav.md sekce K1)

- Rozpočet drží kromě hostince: 2,86 M troj. (před K1 2,63 M). K1 geometrii neměnil (jen shader terénu);
  rozdíl je z exportu – nové LOD skal (remesh LOD0 ~2 800 + tráva ze skály) a 21 881 rostlin posazených
  níž na terén (méně jich pod terénem vypadne z ořezu). Rozpad (TVRZ_ROZPAD) udělám v K2, kde se mění
  louka (u hostince 0,73 M) – to je tam největší položka po předmětech (~1 M, occlusion culling = další fáze).
- Louka: fotka leafy_grass je na velké ploše do žluta/slámova (viz K1_louka.jpg). Příčina: leafy_grass má
  hodně suchých stébel a letecký snímek (aerial_grass_rock) je světlá pastvina s kamením. Návrh: místo
  leafy_grass „grass_ground“ nebo „sparse_grass“ (zelenější), rozhodnu podle snímků – zapíšu sem.
- Referenční místo „skalní město“ stálo u zdi zříceniny (špatná souřadnice), opraveno na -80,300 → -110,285.

---

## 2026-10-16 18:20 – ODPOVĚĎ RÁDCE ke K1 výsledkům

Prohlédl jsem K1_*.jpg. Fotografické textury fungují (zeď hostince, skály po remeshi – výrazně lepší, bez děr a šupin). Ale snímky ukazují jednu příčinu nad všemi ostatními:

**Scéna je přepálená.** K1_cesta.jpg: terén skoro bílý, kopce v dálce bílé, bez textury. Není to texturou (leafy_grass je středně světlá fotka), je to **světlem**: `sun_e` 3,3–3,5 + ambient 0,5 z oblohy + ACES s white 8. V rendereru Compatibility (Godot 4.4) **není HDR framebuffer** – hodnoty nad 1,0 se oříznou dřív, než na ně dojde tonemapping, takže ACES tam přepal nezachrání. Proto fotka trávy vyjde jako slámově bílá a dálka ztrácí texturu. Tohle je ta „bílá dálka“, kterou jsme ráno hledali v texturách.

**Oprava (systémová, ne záplata):** nastavit světlo pro LDR renderer.
- `sun_e`: poledne 1,3, ráno/odpoledne 1,1, soumrak 0,7 (násobky ~0,38×).
- ambient_light_energy úměrně: 0,5 → 0,35 ve dne.
- tonemap: ponechat ACES, `tonemap_white` 8 → 1,6, exposure 1,0.
- Kontrola: na K1_cesta nesmí být žádný pixel terénu čistě bílý; stěna hostince si má zachovat kresbu kamene i na slunci.
- Pokud Vulkan varianta (Mobile renderer, má HDR) pak vyjde tmavě, dej energie jako samostatný profil podle `RenderingServer.get_current_rendering_method()` – ne jeden kompromis pro oba.

Před změnou textury trávy (leafy_grass → grass_ground) **nejdřív oprav světlo** a znovu vyfoť louku a cestu. Teprve pak se rozhoduj o textuře – teď nevidíš její skutečnou barvu.

Dále:
- Hostinec 2,86 M: souhlas s tvým postupem, rozpad v K2.
- Střecha hostince (K1_hostinec) je do modra a leskne se jako plech – šindel má mít roughness ≥ 0,85 a šedohnědou; zkontroluj, jestli se k ní nepřiřadil špatný materiál.
- Tráva (černé čáry) čeká na K2, beru.

---

## 2026-10-16 18:41 – ODPOVĚĎ RÁDCE: viditelnost rozpracované práce

Vidím jen to, co je pushnuté. Práci agentů (K2 tráva, případně další) nevidím, dokud ji nesloučíš – a pak už je pozdě na korekci směru.

Proto: každý agent pracuje na vlastní větvi (`k2-trava`, `k4-skaly-textury`, …) a **pushuje rozpracované stavy průběžně** – po každém smysluplném kroku, ne až hotovo. Do commitu krátce, co je hotové a co ne. Já ty větve sleduji stejně jako hlavní a případné poznámky píšu sem s označením větve. Sloučení do hlavní větve až po mém pohledu na screenshot a čísla.

Zároveň: Míša ti nechal vlastní úvahu – ber ji jako zadání od zadavatele, ne jako poznámku. Když se s něčím z ní neshodneš, napiš to sem, vyřešíme to společně, ne mlčky.

---

## 2026-10-16 18:50 – ODPOVĚĎ RÁDCE: světelný profil + voda (Míša viděl náhled potoka)

Světelný profil pro Compatibility (ldr, slunce ×0,38, obloha ×0,45) – správně, systémové řešení, schváleno. Společný shader pro fotografické materiály s min. roughness 0,8 – schváleno, drž ho jako jediný materiál pro fotky.

**Voda u mostu je špatně** (Míšův verdikt: „děs“), a souvisí s úpravou odrazů:
1. Vypadá jako hliníková fólie – normálová mapa má moc velkou sílu a moc malé měřítko. Potok v údolí je skoro hladký: síla normály 0,15–0,25, měřítko vlnek 2–4 m, dvě vrstvy proti sobě pomalu (0,02 a 0,015 UV/s). Drobné zčeření jen kolem kamenů a u břehu (maska z hloubky/vzdálenosti od břehu).
2. Barva: ne modrý bazén. Mělká voda je průhledná, barvu dává dno (hnědé kameny); hlubší tmavě zelenohnědá (#2A3A24). Odraz oblohy jen Fresnelem pod plochým úhlem (fresnel 5), přímo shora skoro žádný. Pokud shader nemá depth texture (Compatibility), aproximuj hloubku vzdáleností od břehu (vertex color nebo textura masky z Blenderu).
3. Okraj: měkký přechod voda–břeh (alfa podle hloubkové masky 0–0,4 m), tmavý mokrý pruh břehu 20–30 cm nad hladinou, lehká pěna jen u kamenů.
4. Odraz oblohy globálně vypnutý je OK, pokud voda dostane vlastní odraz (reflection probe nebo vlastní sky sample ve shaderu) – ne naopak.

Toto je krok 7 fáze KRÁSA předtažený sem, protože se v tom teď stejně hrabeš. Screenshot potoka u mostu do docs/screens po úpravě.

5. **Potok u mostu je na snímku rozdělený na tři části** (zčeření – hladký lesklý „bazén“ – zčeření). Jeden tok = jeden materiál a souvislé UV podél toku. Zkontroluj, jestli tam nejsou dva shadery (voda.gdshader vs rybnik.gdshader) nebo víc meshů s různými parametry/UV měřítkem; spoj do jednoho materiálu s UV ve směru proudu, rychlost toku jako parametr podle sklonu. Rybník má mít vlastní (klidnější) materiál, ale potok musí být spojitý.

## 2026-10-16 – K1c (světlo) hotovo, odpověď na ODPOVĚĎ RÁDCE 18:20

Snímky docs/screens/K1c_*.jpg, čísla docs/stav.md sekce K1c (rozpočet beze změny – mění se jen světlo a shader).

1. **Světelný profil podle rendereru** (scripts/daylight.gd): Compatibility = slunce ×0,38, ambient ×0,45,
   ACES white 1,6, exposure 1,0; Vulkan beze změny. Ambient jsem dal ×0,45 místo navrženého poměru
   0,5 → 0,35 (×0,7): při ×0,7 se změnil poměr slunce : obloha a stíny a vodorovné plochy zmodraly.
2. **Druhá příčina bílé dálky – výšková mlha:** `fog_height = -6` ležela nad celým údolím (ves, louky,
   rovina −8 až −21 m), krajina stála celá v husté mlze (test: čistě červený terén vyšel lososově bledý).
   Teď main.gd nastaví hranici od nejnižšího bodu terénu (+4 m) – mlha zůstává jen v nivě.
3. **Louka:** Poly Haven nemá svěží zelenou louku (všechny travnaté povrchy jsou suché/podzimní – srovnání
   jsem dělal), proto ambientCG Grass004 (blízko) a Grass001 (dálka), CC0. Letecký snímek jen pro jas skvrn.
4. **K1b pole:** lány z fotek – obilí withered_grass, oranice dry_mud_field_001, zelené plodiny = trávník.
5. **Kalibrace odrazivosti** (tools/albedo_textur.py → modely/textury/albedo.json): fotky z různých zdrojů mají
   různou expozici (cesta 0,044, obilí 0,31 lineárně). Hra násobí fotku cíl/průměr: hlína 0,08, louka 0,10,
   trávník 0,09, hrabanka 0,08, obilí 0,20, oranice 0,10.
6. **Střecha hostince modrá:** není to materiál krajiny – hostinec je statický model (Staticky_hostinec)
   s vlastním materiálem z glb, sníženou drsností ani ambientem se nezměnil. Míša k tomu napsal: pokud jsou
   jím dodané modely špatně, smím hostinec smazat a postavit vlastní, klidně celý jinak. **Návrh:** zařadit
   po K4 jako samostatný krok (nový obsah = až po přestavbě základu), postavit z našich fotografických
   materiálů (zdivo, šindel, trámy) v blender/hostinec.py, LOD0 ≤ 4 000 troj., zapečené AO. Souhlas?
7. Hostinec 2,86 M troj. (nad 2,5 M) – rozpad v K2.

---

## 2026-10-16 19:03 – ODPOVĚĎ RÁDCE: hostinec (SketchUp model od Míši)

Hostinec je Míšův model ze SketchUpu. **Nemazat a nestavět znovu** – tvar, pavlač, podezdívka i okna jsou dobré. Problémy jsou typické pro SketchUp export a řeší se jednou průchozí funkcí (použitelnou i pro další modely od Míši):
1. **Materiály:** glb nese jen barvy bez roughness/metallic → Godot dá výchozí ~0,5 → lesklá modrá střecha. Řešení: v Blenderu při importu přejmenovat materiály podle našich konvencí (sindel, zdivo, prkna, sklo_tercik…) a nechat `svet.gd._apply_materials` přiřadit stejné fotografické materiály jako ostatním stavbám. Žádný materiál „z glb“ nesmí zůstat.
2. **Normály:** SketchUp často otáčí plochy → Recalculate Outside + odstranit duplicitní vrcholy (Merge by Distance 1 mm).
3. **Geometrie:** sloučit plochy stejného materiálu, decimate planar (úhel 1°), cílově ≤ 4 000 tris LOD0; LOD1 ~1 200.
4. Kolize z výsledného meshe, ne z originálu.
Zapiš to jako `_import_sketchup(glb)` v blender/nove.py, aby se dal použít na každý další model od Míši. Hostinec je první test. Screenshot ze stejného místa jako K1_hostinec.jpg po úpravě.

Doplnění: Míša dodal **~30 modelů** (SketchUp / 3D Warehouse), většinou s texturami 2k–8k. To je zdroj dnešního přetížení paměti. Funkce `_import_sketchup` musí proto navíc:
5. **Textury:** každou zmenšit na max 1024 (předměty 512), převést na ASTC/ETC2 s mipmapami; kde má model víc materiálů s malými texturami, sloučit do jednoho atlasu 1024. Žádná textura > 1024 v buildu. Výsledek zapsat do seznamu `docs/modely_misa.md` (model, tris před/po, textury před/po).
6. Projet všech 30 modelů hromadně, ne po jednom – hostinec jako první pro ověření, pak dávka.

---

## 2026-10-16 19:08 – ODPOVĚĎ RÁDCE ke K1c

**K1 (a+b+c) schváleno a uzavřeno.** Skalní město je po remeshi výborné – věže celistvé, vrstvy pískovce vidět, borovice na vrcholech. Louka u vsi má správnou barvu, dálka má texturu, chalupy sedí v krajině. Dvě příčiny bílé dálky (LDR přepal + výšková mlha od −6 m přes celé údolí) – druhou jsi našel sám a je to pěkná detektivní práce; test „červený terén vyšel lososově“ je přesně ten typ ověření, který chceme.

Kalibrace albeda přes albedo.json: správně, drž ji jako jediné místo pro expozici fotek.

**Hostinec – odpověď na bod 6: NE, nestavět nový.** Viz moje sekce 19:03 výše (psal jsem ji souběžně s tvou otázkou). Míšovo svolení „smaž“ platí jen pro případ, že se model nedá zachránit – a tenhle se dá. Pořadí: (1) `_import_sketchup` na hostinec, screenshot; (2) teprve když i po importu vypadá špatně tvarem, stavět vlastní. Důvod: je to Míšův model a stejnou cestou musí projít dalších ~30 jeho modelů – funkce se zaplatí hned.

Co teď: K2 (tráva) od agenta je jediná věc, která brání vydání. Až bude na větvi, sem čísla + screenshot z výšky očí.

---

## 2026-10-16 19:10 – ZADAVATEL (Míša) – tři mantinely, platí trvale

1. **Cíl: úroveň KCD2** – uvěřitelná krajina a svět, ne „dost dobré“.
2. **Strop: možnosti tabletu** (Xiaomi Pad 8, Compatibility, rozpočet v stav.md) – nikdy nepřekročit.
3. **Neplýtvat tokeny** – každý krok musí mít výsledek, který se dá ukázat. Žádné dlouhé průzkumy bez výstupu, žádné přepisování hotového, žádné rozpady a měření, pokud přímo nevedou k rozhodnutí. Agenti jen na úkoly, které běží paralelně bez střetu. Když si nejsi jistý, zeptej se sem jednou větou místo hodiny zkoušení.

Rádce se řídí stejnými pravidly: odpovědi stručné, bez opakování, jen když je co říct.

## 2026-10-16 – K2 (tráva z karet) sloučeno – údaje podle ODPOVĚDI RÁDCE 18:05

- **Příčina:** trs = 16–36 troj. procedurálních stébel jen s barvou vrcholů (bez textury), tmavá pata + AO 0,35 → černé čáry.
- **Trs:** 3 zkřížené svislé karty (mírně posunuté, různě vysoké, jedna zrcadlená) = **6 troj.** (dřív 16–36).
- **Atlas:** obrazky/trava_atlas.png **1024×512**, 3×2 buňky s alfou: nízká tráva, vysoká, suchá, jitrocel
  (Poly Haven ho nemá → weed_plant_02 + listy celandine), kapradí, kvítí. Generátor blender/atlas_travy.py
  (Cycles, ortografický boční pohled, alfa z Poly Haven *_alpha masek). Buňka atlasu = INSTANCE_CUSTOM.b.
- **Shader:** alpha scissor 0,5, normála z obou stran k view-up, albedo × mix(0,55; 1; výška), AO u země 0,6, vítr zachován.
- **Prolínání:** dřív vzdálenost od středu 32m buňky (v Compatibility MODEL_MATRIX u MultiMesh neobsahuje
  transformaci instance) → mřížka teček přes celé buňky; teď podle vrcholu a náhodného prahu na trs.
- **Snímek z výšky očí:** docs/screens/K2_cesta.jpg (louka u vsi), K2_louka.jpg (u tvrze).
- **Čísla (stav.md K2):** všech 8 míst pod 2,5 M – hostinec 2,86 → 2,32 M, louka u tvrze 1,73 → 1,10 M;
  kreslení beze změny nebo o ~10 méně.
- **Otevřené:** u tvrze (K2_louka) je louka řídká, kde je mapa hustoty nízká, a mezi blízkým (0–25 m) a
  středním pásmem (25–100 m) prosvítá zem. Návrh: DAL_HUST 1,2 → 2,0 (rozpočet to po K2 unese, střední karta
  = 6 troj.). Kvítí (kvety.gdshader) má ještě staré tečkované prolínání – přepíšu stejně jako stébla.

---

## 2026-10-16 19:40 – ODPOVĚĎ RÁDCE ke K2

**K2 schváleno.** K2_cesta.jpg je první snímek, který vypadá jako hra, ne jako technické demo: koberec trávy bez černých čar, suché trsy, kvítí, správná barva. Trs 6 troj. místo 16–36 a všech 8 míst pod 2,5 M – přesně to, co měl krok udělat. Oprava prolínání (MODEL_MATRIX u MultiMesh v Compatibility) je dobrý nález, zapiš ji do stav.md jako známé omezení.

Schvaluji oba otevřené body: DAL_HUST 1,2 → 2,0 a kvítí na stejné prolínání jako stébla. U tvrze (K2_louka) navíc: pod stromy je holá hlína mezi trsy správně (les), ale na okraji lesa by měl být přechod – trsy hustší v pásu 5–10 m od krajních stromů. Stačí hustotu násobit podle masky lesa, žádný nový obsah.

**Pak vydej 0.43** (K1 + K2 + skály). Po vydání: stav.md, a zastavit se do pondělí (limit účtu). Stromy jako nízkopolygonové kužely a koruny-koule řešíme až v K3/impostory, teď ne.

## 2026-10-16 – hostinec přes `_import_sketchup` + vydání 0.43

- **Vydání 0.43** (K1 + K2) je venku pro tablet: apk/OdkazHavrana-0.43.apk a -vulkan.apk.
- **Hostinec:** `_import_sketchup` (blender/nove.py) – modrá střecha pryč (RoofTilesWood → sindel_hra), 9 292 → 4 000
  troj., ostatní glb materiály bez lesku. Snímky docs/screens/hostinec_import_blizko.jpg a _celek.jpg (stejné místo
  jako K1_hostinec). Hostinec teď 2,27 M troj. Tabulka docs/modely_misa.md.
- LOD1 (~1 200) zatím ne: statické stavby nemají LOD systém; hostinec je vidět jen z okolí skal – navrhuji odložit.
- **Otázka (jedna věta):** kterých ~30 Míšových modelů myslíš – v repu/na disku vidím 18 glb v tvrz-modely/drive
  (dřevo, kameny, ploty, dveře, dům house_farm_wood) a 5 ve stazene; ve hře je z nich jen hostinec, dveře a stan –
  mám projet jen ty použité, nebo všechny i do zásoby?

---

## 2026-10-16 19:44 – RÁDCE: šetření tokenů (Míšův pokyn)

Pravidlo vydávání: **vydání jen na výslovné „VYDEJ“, vždy jako poslední krok.** Dvě vydání za sebou (0.43 + 0.44) se nesmí opakovat – chyba byla v mém pokynu, ne u tebe.
Teď: dokonči 0.44 nejkratší cestou (bez dalších měření a screenshotů mimo 2 kontrolní), zapiš stav.md a **stop do pondělí**. Žádní agenti, žádné další kroky.

**Oprava od Míši (19:45):** žádný stop do pondělí. Pracuje se dál, dokud limit vydrží – ale hospodárně: jeden krok po druhém, bez agentů navíc, bez měření a screenshotů mimo ty 2–4 kontrolní na krok, žádné průzkumy. Po 0.44 pokračuj dalším krokem ze zadání (K4 textury skal okr/šedá/mech, pak hromadný import Míšových modelů).

---

## 2026-10-16 19:48 – RÁDCE: K3 stromy (Míšův postřeh – kužely na dohled)

Na snímku louky u tvrze jsou od ~40 m smrky jako zelené kužely a listnáče jako koule. Blízký smrk (větve z fotky) je dobře – problém je LOD1 „zjednodušený tvar“ a hranice 120 m, za kterou nic není.

**K3 – impostory (po 0.44, před K4):**
1. Pro každý druh stromu (smrk, borovice, dub/buk, bříza) octahedral impostor: 8×8 pohledů (albedo + normála) do atlasu 1024, Blender render z LOD0. Jeden quad (2 troj.) na strom, shader vybírá pohled podle úhlu kamery.
2. Vzdálenosti: LOD0 (plný) 0–45 m, LOD1 (polovina větví, textura listí – ne kužel) 45–110 m, impostor 110 m → horizont. Kužely a koule zrušit.
3. Les se tím vrátí až k obzoru; rozpočet: impostory ≈ 2 troj./strom, 5 000 stromů = 10 k troj. Stíny jen LOD0.
4. Mlha a barva impostorů ladit tak, aby přechod LOD1→impostor nebyl vidět (stejný světelný profil, impostor bere albedo × ambient).
Výstup: snímek z louky u tvrze (stejný jako K2_louka) + z vyhlídky u skal.

---

## 2026-10-16 19:53 – RÁDCE: modely od Míši

Hostinec přes `_import_sketchup` – správně (9 292 → 4 000, šindel/dub podle jmen). Zdrojové modely (`stazene/`) nejsou v repu, takže rozsah nevidím. Až přijde řada na hromadný průchod (po K3): projet **všechny** modely od Míši včetně 273 předmětů pískoviště (`p_*` balíčky) a doplnit tabulku v `docs/modely_misa.md` – u každého tris před/po a největší textura před/po. Součet úspory textur zapsat na konec. Zdrojové glb do repa nedávat (velikost), jen tabulku.

---

## 2026-10-16 19:58 – ZADAVATEL (Míša): historické reálie – trvalé pravidlo

Čechy/Morava, rok 1393, venkov a nižší šlechta. Všechno ve hře musí odpovídat době a místu – stromy, rostliny, zvířata, stavby, oděv, nářadí, jídlo, barvy látek, zbraně, jména. Když si stavitel není jistý, zapíše otázku sem místo odhadu. Platí pro krajinu (druhy dřevin: smrk jen ve vyšších polohách, jinak dub, buk, habr, borovice, bříza, lípa; žádné exotické rostliny), pro postavy (oděv, boty, pokrývky hlavy, účesy podle stavu a rodinného stavu), pro budovy (roubenky, došky, šindel, hliněná podlaha; kámen a omítka jen tvrz a kostel) i pro předměty (žádné brambory, kukuřice, rajčata, paprika, tabák; žádné sklo v oknech chalup – terčíky jen hostinec/tvrz).
Rádce kontroluje reálie u každého kroku stejně jako rozpočet.

## 2026-10-16 – K3 impostory stromů hotovo

- **Příčina:** od 60 m stromy nahrazoval vypočtený tvar (kužel / shluk koulí jednou barvou), za 120 m nic.
- **Postup:** blender/impostory.py – 11 druhů (smrk, bříza, borovice, dub ×2, lípa ×2, olše ×2, buk, vrba),
  8×8 pohledů horní polokoule (hemi-oktaedricky), barva s alfou + normála ve světě, atlas 1024 (128 px/pohled).
  Varianty druhu sdílejí impostor (smrk_0..4 → smrk). shaders/impostor.gdshader: čtverec 2 troj. ke kameře,
  pohled podle směru (i s otočením stromu), normála z atlasu, vlastní stín koruny dole. Instance mají jednotkovou
  transformaci a pata/měřítko/otočení jsou v INSTANCE_CUSTOM (Compatibility a Mobile předávají transformaci
  instance shaderu různě). MultiMesh po druzích a buňkách 256 m s ručním obalem.
- **Vzdálenosti:** plný strom 0–60 m (stín), impostor prolíná od 50 m, do 900 m. Kužely a koule pryč
  (zůstávají jen jako záloha, kdyby impostor pro druh chyběl).
- **Odchylka od zadání:** mezistupeň LOD1 (polovina větví 45–110 m) jsem nedělal – oktaedrický impostor drží tvar
  už od 60 m (K3_louka.jpg) a ušetří to krok. Pokud bude přechod 60 m na tabletu vidět, doplním.
- **Čísla:** louka 843 kreslení / 1,11 M troj., vyhlídka 679 / 1,25 M; GPU +30 MB (22 atlasů ETC2) → 487 MB.
- Snímky docs/screens/K3_louka.jpg, K3_vyhled.jpg. Další: K4 (textury skal okr/šedá/mech, zapečené AO).

---

## 2026-10-16 20:22 – RÁDCE: Vulkan odložen

Havran Vulkan 0.44 na tabletu spadl znovu při stahování dat (0 % z 308 MB po 253 s, scéna prázdná, troj 0) – stejně jako 0.42. Compatibility se stejným kódem funguje. Rozhodnutí: **Vulkan variantu dál nestavět ani neladit** (plýtvání), vrátit se k ní až po upgradu Godotu na 4.7+. Vše jde do Compatibility. Z vydání vypustit Vulkan APK.
Oprava (Míša): stažení vždy doběhne na 100 %, pád je **při vstupu do hry** (stavba světa / první snímek), konzistentně od prvních verzí (~100×). Rozhodnutí platí – systémová neslučitelnost Vulkan + Adreno 825 + Godot 4.4 na této scéně, řešit až s upgradem enginu.

---

## 2026-10-16 20:40 – HLÁŠENÍ Z HRANÍ 0.44 (Míša na tabletu, 24 snímků, posouzeno rádcem)

**Celkem: jdeme správně.** Skalní město, louka u tvrze, průhledy mezi věžemi, hospoda s pavlačí, kuchyně – poprvé to vypadá jako hra. Míša: „spousta chyb, ale taky nádhera“.

**Chyby podle závažnosti (řešit systémově, ne po kuse):**

1. **Stromy LOD1 = plovoucí koruny.** Dub/buk na 40–120 m: koruna visí ve vzduchu bez kmene, listnáče jako „mřížka teček“ (síťované koule), smrky jako ploché kužely. Kmeny u LOD1 zcela chybí nebo jsou příliš tenké na to, aby prošly alfa-testem. → K3 impostory to řeší; než budou, LOD1 musí mít kmen (válec ≥ 0,3 m, bez alfy) a korunu z karet s texturou, ne kouli z teček.
2. **Stíny stromů jako černé ploché tvary na zemi** (skalní město, u skal) – stín koruny se kreslí jako plný tmavý polygon s ostrou hranou (alfa v shadow passu neprošla). → materiál listí: `alpha_scissor` i pro stíny (shadow pass musí testovat alfu), nebo stíny z LOD1 vypnout.
3. **Tráva prosvítá skrz skály/terén** (bílý trs před skálou dole vlevo, posledních snímek skal) a tráva roste ze střechy mostu i z lavice na mostě – rozmístění nekontroluje překážky. → maska: žádná tráva na mostě, cestě, pod stavbami, uvnitř skalních kolizí (ray dolů musí trefit terén, ne mesh).
4. **Zem pod stromy v lese = plochá sytě zelená bez textury** (u paty skal, pod dubem). Terén tam má jen vertex color, chybí textura hrabanky/trávy. → zkontrolovat masku lesa v zem.gdshader a `gm` pro tyto oblasti.
5. **Hranice NEAR/FAR terénu vidět** – za ~140 m skoková změna barvy na bledě zelenou, kopce na obzoru bílé. → vzdálený terén musí mít stejnou barvu/texturu jako blízký (sdílený albedo.json), mlha hustší nad 300 m.
6. **Rybník/potok: vodní hladina modrá a lesklá** – již zadáno (sekce voda), potvrzeno na tabletu; zelené „skvrny“ řas na hladině jsou dobrý nápad, ale příliš syté a ostré.
7. **Louka u příkopu tvrze: trávník jako „žlutá plocha s tečkami“** – jiná textura než okolí (trávník vs. louka), přechod ostrý. → sjednotit s loukou, přechod šumem.
8. **Hospoda:** stěna má modrý nádech (kámen příliš chladný – albedo kalibrace), okna s terčíky OK; dřevěná bouda vzadu – dveře do kuchyně: **hráč se zasekl ve dveřích** (kolize rámu vs. průchod). → kolize dveří: rám jen po stranách, průchod ≥ 0,9 m, step-up 0,3 m.
9. **Kuchyně:** zelí = moderní hlávkové zelí OK (dobové), ale hrnce/police jsou bez AO – vše stejně nasvícené. → zapečené AO u interiérů (K4).
10. Drobné: bílé tenké kmeny bříz vypadají jako tyče (chybí textura kůry zdálky); stan obchodníka OK; balvany u louky mají správnou texturu, ale leží na trávě – zapustit 20–30 %.

**Pořadí:** 1+2 (stromy a stíny – nejvíc viditelné) → 3 (maska trávy) → 8 (kolize dveří, blokuje hraní) → 4, 5, 7 → zbytek v K4.
**Doplnění (Míša zdůrazňuje):** trojúhelníkové smrky v pozadí (bod 1) a **bílý obzor** (bod 5) jsou na každém druhém snímku – zvednout prioritu: bílý obzor řešit hned spolu s K3. Příčina obzoru: vzdálený terén + kopce na horizontu jsou přepálené/bez textury a mlha je bílá místo barvy oblohy u horizontu. → barva mlhy = vzorek oblohy těsně nad horizontem (mírně modrošedá, ne bílá), vzdálený terén albedo × 0,8 (dálka je vždy tmavší než popředí), kopce na obzoru musí mít texturu, ne plochou barvu.

---

## 2026-10-16 20:45 – KAPITOLA: RUINY (Míša: „jak z Minecraftu“) – řešit AŽ PO FÁZI KRÁSA

Tři ruiny (lesní zřícenina, zbořená chalupa s pecí, věž ve skalním městě). Podrost kolem (kopřivy, břízy, kapradí, mech) je dobrý – špatné je zdivo samo:
- zdi = kvádry s rovnými řezy, koruna zdi schodovitě po celých blocích, žádná tloušťka ani spáry na hranách
- textura lomového kamene dlaždicovitá, u věže namodralá (chladná kalibrace) s plochým mechem
- žádná suť u paty, žádné vypadlé kameny, žádné stopy po trámech/podlahách, okna jako přesné obdélníky

**Systémové řešení (jedna funkce `_ruina(zed)` v Blenderu, ne ruční modelování):**
1. Koruna zdi: nepravidelný profil – displacement šumem 0,2–0,6 m podél horní hrany, jednotlivé vypadlé kameny (kvádry 20–40 cm) jako samostatné instance podél koruny.
2. Hrany a rohy: zkosit/rozlámat (bevel + šum), zeď má tloušťku 0,8–1,2 m a je vidět vrchní plocha s kamením.
3. Suť: MultiMesh kamenů (fotosken Poly Haven) u paty, kužel 1–2 m, hustší pod proraženými místy; v sutí tráva a kopřivy.
4. Textura: lomové zdivo z fotky (castle_wall_slates nebo rock_wall) s vertex-color maskou: mech jen na severní straně a u paty, tmavé zatečení pod okny, zbytky omítky v chráněných místech (vnitřní stěny, pod překlady).
5. Otvory: okna a dveře s kamennými ostěními (3–4 kvádry), překlad buď dřevěný trám (vypadlý, leží v suti) nebo lomený oblouk s vypadlým klenákem.
6. Stopy života: kapsy po trámech stropu v řadě, zbytek krbu/pece s očazením, propadlá podlaha → terén uvnitř níž, zarostlý.
7. Věž ve skalním městě: kruhová, textura stejné kalibrace jako skály (teplá), ne modrá; koruna ozubená nepravidelně, jedna strana propadlá víc.
Reálie: ruiny roku 1393 = opuštěné tvrze/dvorce ze 13.–14. stol., lomový kámen na vápennou maltu, žádné cihly.
Rozpočet: ruina ≤ 6 000 tris + suť MultiMesh.

## 2026-10-16 – chyby z tabletu (0.44, Míšovy fotky)

1. **Plovoucí tráva nad vodou, příkopem a cestami** (spirály a desky ve vzduchu): moje chyba z K2b. Zvýšení hustoty
   na okraji lesa se přičítalo i tam, kde mřížka louky má hustotu 0 (koryto, příkop, cesta, stavba) – a tam
   `_vzorek` vracel výšku 0 m, zatímco údolí leží −4 až −8 m. Oprava: výška vždy z mřížky, okraj lesa přidává
   jen kde tráva už je. Ověřeno výpisem instancí (dřív 20–200 trsů na buňku o metry nad zemí, teď 0) a snímky.
2. **Zaseknutí ve dveřích hostince** (bouda → kuchyně): `_import_sketchup` stahoval hostinec na 4 000 troj.
   hrubým zjednodušením, které zužuje dveřní otvory, a kolize je ze sítě. U staveb teď jen rovinné slučování
   (9 292 → 8 598). Zadání „≤ 4 000 tris LOD0“ proto u staveb neplatí – tvar a průchodnost mají přednost; souhlas?
3. Ještě otevřené z fotek: balvany tmavě zelené s pruhy (špatný materiál), pixelové textury skal zblízka
   a šestiúhelníkové švy (K4), bílé kmeny bříz, světle zelená „vybledlá“ zem mezi trsy, Vulkan nespustí hru.

---

## 2026-10-16 20:50 – KAPITOLA: TVRZ ZVENČÍ (val, příkop, hradba) – Míša to vyčítá od začátku

Snímek 0.44 od mostu: val je hladký zelený kopec s ostrou hranou, příkop rovný žlab s modrou vodou, pata hradby bez přechodu. Je to první, co hráč vidí – mrtvé.

**Val:**
- Profil: ne hladký, ale nerovný (šum 0,2–0,4 m), místy sesuté, uježděné; hrana k příkopu zaoblená a místy ulomená.
- Povrch: na vrcholu a svahu k hradbě krátká spásaná tráva (udržovaný pás pro obranu – do 10 m od hradby žádné keře, to je dobové), dole u příkopu vysoká tráva, kopřivy, bodláky, lopuch.
- Pěšiny: vyšlapaná cesta po koruně valu a svahem k mostu (hlína, textura cesty).
- Kameny: vypadlé z hradby u paty, roztroušené po svahu; zapuštěné.
- Lidská stopa: hromada hnoje/kompostu u hradby, suché roští, kůl, mrtvý pařez.

**Příkop:**
- Dno nerovné, voda stojatá: tmavá hnědozelená, okřehek a rákos u břehů, bahno s otisky, žádná modř.
- Břehy: strmá strana pod hradbou s kamennou patou (plentou), vnější strana pozvolná, zarostlá rákosem, vrbovými pruty, blatouchem.
- Padlé větve a kus trámu ve vodě, kachny jen pokud máme model.

**Hradba zvenčí:**
- Pata: tmavý vlhký pruh 0,5–1 m (mech, zateklé), opadaná omítka s odhaleným lomovým zdivem víc dole než nahoře.
- Zatečení pod okny a pod stříškami ochozu; prejzy/šindel na ochozu s mechem na severní straně.
- Pod ochozem nahoře tmavší pás (stín, špína).

**Most a brána:** prkna ochozená, u nástupu bláto a koleje; u brány stojan, lavička, odpadky, kůl s řetězem.

Rozpočet: vše přes MultiMesh a textury, max +150 k tris, žádný nový druh stromu. Řešit v rámci fáze KRÁSA hned po K3 (je to „první dojem“).

## 2026-10-16 – PRO RÁDCE: stav po hlášení 0.44, prosím o odpověď

Hotovo (na větvi, do tabletu až s dalším vydáním na „VYDEJ“):
- **Bod 3 (tráva):** plovoucí tráva nad vodou, příkopem a cestami opravena – příčina moje K2b (okraj lesa přidával
  trsy i kde maska = 0, výška tam 0 m). Tráva na mostě a cestě už není.
- **Bod 2 (stíny):** bříza a smrk měly listí s předprůchodem (alfa se ve stínu netestovala) → alfa nůžky.
- **Bod 8 (dveře hostince):** hrubé zjednodušení na 4 000 troj. zužovalo otvory; u staveb jen rovinné slučování.
- **Bod 1 (stromy):** K3 impostory hotové (kužely a koule pryč, les do 900 m).

**Otázky (stačí ano/ne):**
1. Hostinec 8 598 troj. místo ≤ 4 000 (tvar a průchodnost dveří mají přednost) – souhlas?
2. Reálie 1393: smrk dnes tvoří většinu lesa i v nížině (~6 500 stromů). Mám v nížině (pod ~400 m n. m. hry,
   tj. kolem tvrze a vsi) nahradit smrk dubem/bukem/habrem a smrk nechat jen na hřebenech a ve skalním městě?
3. Další krok: **bílý obzor** (barva mlhy = obloha u horizontu, dálka albedo × 0,8, kopce s texturou),
   pak zem v lese (bod 4), pak K4. Souhlas s pořadím?

---

## 2026-10-16 21:02 – ODPOVĚĎ RÁDCE na tři otázky

1. **Hostinec 8 600 tris – ANO.** Průchozí dveře a Míšův tvar mají přednost před číslem; rozpočet celkem to unese. Zapiš výjimku do stav.md.
2. **Smrky v nížině – ANO, ale ne úplně pryč.** Kolem tvrze, vsi a na loukách: dub, buk, habr, lípa, bříza, borovice na písčitých místech. Smrk nechat na hřebenech, ve skalním městě a v hlubokém lese na severních svazích (tam rostl i ve 14. stol.), jako příměs max 20 %. Žádná plošná výměna – podle výšky/sklonu terénu, jedna funkce.
3. **Pořadí – ANO:** bílý obzor → zem v lese → K4 skály (textury okr/šedá/mech). Pak kapitola „tvrz zvenčí“ (val, příkop) – první dojem.
Vydání 0.45 bez Vulkanu: správně.

## 2026-10-16 – ZADAVATEL (Míša): odpovědi na 3 otázky + vydání 0.45

Míša: „jinak vše ano“ → (1) hostinec 8 598 troj. platí, (2) smrk v nížině nahradit dubem/bukem/habrem,
smrk jen hřebeny a skalní město, (3) pořadí: bílý obzor → zem v lese → K4.
**Vydání 0.45** (na Míšův pokyn): K3 impostory, oprava plovoucí trávy, stíny bříz/smrků, dveře hostince,
okno o pádu ukazuje konec zprávy. Jen Compatibility APK (Vulkan vypuštěn).

---

## 2026-10-17 07:25 – HLÁŠENÍ Z HRANÍ 0.45 (Míša, 16 snímků z tabletu)

**Lepší než 0.44:** smrky z karet místo kuželů, listnáče mají kmeny, horizont má barvu, rybník s rákosím a vrbou, hostinec s pavlačí, údolí pod skalami. Správný směr.

**Chyby podle závažnosti:**

1. **ČERNÉ SKVRNY NA SKALÁCH A TERÉNU – regrese, nejvíc viditelné.** Velké černé plochy se zubatým okrajem na stěnách skal, na svahu pod skalami, na balvanu u louky, ve stínu skalního města. Stín koruny stromu promítnutý při nízkém slunci jako plný tvar – přišlo to s impostory/kartami smrku. **Impostory a LOD1 nesmí vrhat stín** (cast_shadow OFF), stín jen z LOD0 s alpha scissor i v shadow passu. Test: vypnout stíny stromů → skvrny pryč = potvrzeno.
2. **Zaseknutí ve dveřích hostince A na schodech** – stále. Kolizní mesh z decimovaného modelu; průchod ≥ 0,9 m; schody jako rampa (ne schodnice); step-up 0,35 m. Ověřit průchodem bota (tools/test.sh).
3. **Voda – břehy:** rybník, potok i příkop končí ostrou hranou, voda „leží“ na trávě. Mělčina: terén pod hladinou klesá pozvolna, u břehu průhlednost, mokrý tmavý pruh 20–30 cm. Řasy OK, ale hnědozelené na tmavé vodě, ne zelené tečky na modré. Potok pořád modrý a hrubý – body 1–5 z dřívější sekce voda.
4. **Tvrz – kámen jiný než jinde, bez struktury:** hradba má béžovou omítku s vypadlými místy, kámen pod ní jiné barvy a měřítka než hostinec/ruiny, chybí normálová mapa (placaté). Sjednotit: lomové zdivo stejné textury všude, omítka jako vrstva s maskou, normála na obou; pata s mokrým pruhem.
5. **Textury ve vzduchu ve skalách:** bílé ploché karty mezi věžemi (tráva/kapradí ve špatné výšce), průhledy u paty věží. Rostliny mimo kolizi skal, výška z terénu; LOD2 skal bez děr.
6. **Interiér hospody tmavě modrý** – bez světla uvnitř. Interiéry: teplý ambient + světlo z oken/ohně (K4 zapečené AO + omni).
7. **Kameny u louky:** 3 balvany jedné modrošedé textury vedle sebe – sjednotit s pískovcem, zapustit, různé velikosti.
8. **Příkop/val u tvrze:** holý trávník, ostrá hrana, břízy v příkopu jako tyče → kapitola „tvrz zvenčí“.

**Od Míši navíc:**
9. **Zkušební louku zrušit** – smazat scénu/kód zkušební louky (zkusebni.gd a vše kolem), louka.gd ji nahradila. Výpis mazaných souborů před smazáním.
10. **Mapa – dvojí kliknutí:** mapa se často otevře až na druhé klepnutí, ale zvuk rozbalení zazní už při prvním. → vstup se zpracuje (zvuk), ale UI se neukáže: závod mezi `visible` a animací/`process_mode`, nebo první klepnutí jen zavře něco jiného (HUD focus). Opravit tak, že zvuk se pouští až po skutečném zobrazení mapy.

Pořadí: 1 (regrese) → 2 + 10 (blokují hraní) → 3, 4 → 9 → zbytek.

---

## 2026-10-17 08:00 – ODPOVĚĎ RÁDCE k fb55418–130d03d

Mech 25–50× jako příčina černých ploch – správně, lepší diagnóza než moje (stíny); beru zpět bod 1 hlášení. Mapa (emulované kliknutí trefilo Zavřít) a zkušební louka – hotovo, dobře.
Pokračuj podle hlášení 0.45: 2 dveře + schody hostince → 3 voda (břehy, mělčina, barva) → 4 kámen tvrze. Po těchto čtyřech screenshoty (hostinec vchod, potok u mostu, hradba zblízka) a pak VYDEJ 0.46.

---

## 2026-10-17 08:08 – RÁDCE: zaseknutí ve dveřích hostince – zkrať hledání

Paprsky netrefily, kapsle stojí → nejčastější příčiny u importovaného SketchUp modelu, zkontroluj v tomto pořadí (každá 2 minuty, ne další testy):
1. **Kolize z původního glb, ne z decimovaného:** `_import_sketchup` vrátil mesh, ale CollisionShape se generuje z `Staticky_hostinec` před decimací → zůstaly vnitřní plochy (práh, zárubeň, neviditelná deska ve dveřích). Řešení: kolize jen z výsledného meshe (`create_trimesh_collision` na decimovaném), nebo ještě lépe ručně: zdi jako BoxShape, průchody vynechat.
2. **Práh / schod > step-up:** SketchUp modely mívají práh 15–25 cm a hráč má step-up nižší. Zvýšit step-up na 0,35 m (`floor_max_angle`/`CharacterBody3D` snap) – pomůže i na schodech.
3. **Dveřní křídlo má kolizi i otevřené:** pokud dveře jsou interaktivní (life.gd), kolize křídla se musí otáčet s ním nebo vypnout při otevření.
4. **Navigační/kolizní vrstva**: kolize hostince na jiné vrstvě než hráč čeká (mask).
Když ani jedno: `get_slide_collision()` v `_physics_process` při zaseknutí vypíše kolidující uzel – jeden řádek, žádné hádání.

**Doplnění 08:15:** stavitel zjistil, že fyzika hlásí jen podlahu – postavu vrací skript, pravděpodobně ořez na hranici světa (bounds/AREA). Souhlas, moje 4 tipy byly špatně. Řešení systémové: hranice světa se musí počítat z obálky všech staveb + 50 m, ne z pevných čísel; a místo tvrdého vracení hráče měkký odpor (zpomalení) + hláška, ať se tohle nikdy neprojeví jako „neviditelná zeď“. Zkontroluj stejně i schody hostince – pokud je to táž hranice, vyřeší se obojí najednou.

---

## 2026-10-17 08:33 – RÁDCE: postavy jsou v main – zapojit do hry

Větev postav sloučena do `main` (8723f11): hrdinové + 9 NPC, modely/postavy/*, animace UAL, postavy_import.gd, postava_sklada.gd, postava_oci.gd. Po dokončení dveří hostince a vody:
1. Přenést z `main` do této větve složku modely/postavy a nastroje/godot/postav* (merge main → tahle větev, konflikty jen v radce.md – zachovat obě strany).
2. Hráč = Jan (volba starší/mladší při startu podle příběhu), NPC rozmístit podle `pribeh/postavy.md`: hostinský a Eliška v hostinci, kovář u kovárny na nádvoří, sedlák + selka ve vsi, stařec na lavici u hostince, dívka u studny, měšťan + měšťka na cestě, stařena u chalupy. Idle varianty náhodně.
3. Snímek na nádvoří tvrze s 3 postavami ve světle hry → docs/screens/K5_postavy_nadvori.jpg. Teprve podle něj se rozhodne o barvách a materiálech postav vůči světu.
Rozpočet: postavy přidají ~60–80 k tris při 9 NPC viditelných – do limitu se vejde, ale změř.

---

## 2026-10-17 08:35 – RÁDCE: hostinec – STOP opravám po kuse (Míša: před importem byl průchozí)

Hostinec byl **před `_import_sketchup` normálně průchozí** – dveře, schody, patro. Všechny dnešní problémy (podlaha nedrží, schod 0,3 m, trám nad podestou) vznikly importem: decimace/přepočet normál/sloučení ploch změnily geometrii, ze které se generuje kolize.

**Příčinové řešení (15 minut, ne další hodina):**
1. Kolizi hostince generovat z **původního** glb (před importem), ne z decimovaného – původní prošel. `_import_sketchup` smí měnit jen vizuální mesh (materiály, textury, decimace), kolize = `create_trimesh_collision` z původní sítě, oboustranná.
2. Patro/podlaha/trám: pokud byly v původním modelu průchozí, neřezat otvory – vrátit původní tvar, jen zkontrolovat, že decimace planar nesloučila podlahu patra přes šachtu schodiště (to je pravděpodobný viník „trámu nad podestou“). Decimace planar jen na plochy stejné roviny A stejného materiálu, ne přes otvory.
3. Ověřit botem: průchod bránou → síň → kuchyně → sklad → schody → patro. Jedna trasa, jeden test.
Totéž pravidlo pro všech ~30 Míšových modelů: **kolize z originálu, vizuál z importu.**

## 2026-10-17 – hostinec: kolize z původního glb (podle RÁDCE 08:35)

- `predmety.py`: u modelů se `sketchup` se před `_import_sketchup` uloží kopie původní sítě jako `<id>_kolize`
  (stejné posunutí a měřítko, nekreslí se); `svet.gd` udělá trimesh kolizi jen z ní (oboustrannou) a kopii skryje.
  Import mění jen vizuál. Otvor ve stropě nad schodištěm jsem vrátil (nebyl potřeba).
- Bot (`TVRZ_TEST=hostinec`, dev_test.gd): sklad↔kuchyně OK, kuchyně→síň OK, vchod→síň OK, sklad→ven OK,
  schody: 1. rameno → podesta 1,35 m → 2. rameno 2,62 m → chodba patra 2,84 m OK. Síň→kuchyně: dveřmi projde,
  zastaví se až v kuchyni o vybavení (trasa testu, ne kolize).
- Příčina u importu: `recalc_face_normals` otočil podlahu (normála dolů) a jednostranná trimesh kolize hráče shora
  propustila na terén 6 cm pod podlahou. Platí pro všechny Míšovy modely: kolize z originálu, vizuál z importu.

---

## 2026-10-17 08:48 – ODPOVĚĎ RÁDCE

Hostinec: hotovo správně, pravidlo „kolize z originálu, vizuál z importu“ beru jako trvalé pro všechny Míšovy modely. Dál podle hlášení 0.45: **voda** (břehy/mělčina/barva, body 1–5 ze sekce voda) → **kámen tvrze** (sjednotit zdivo, normála, pata) → snímky (potok u mostu, hradba zblízka, hostinec vchod) → **VYDEJ 0.46**. Postavy zapojit až po 0.46 (sekce 08:33).

---

## 2026-10-17 08:50 – ZADAVATEL (Míša): pořadí fází – KRÁSA → FUNKCE → POSTAVY

Rádce vede v tomto pořadí; stavitel nepřeskakuje mezi fázemi.

**I. KRÁSA (teď, do odvolání)**
1. Voda (břehy, mělčina, barva, souvislý potok) – rozpracováno
2. Kámen tvrze (sjednotit zdivo, normála, pata) → VYDEJ 0.46, Míša hraje
3. K4 skály: textury okr/šedá/mech, suť u paty, keře v puklinách
4. Tvrz zvenčí: val, příkop, hradba (kapitola 20:50)
5. Keřové patro + mrtvé dřevo (fáze KRÁSA krok 3), cesty s kolejemi a lidská stopa (krok 5)
6. Ruiny (kapitola 20:45)
7. Vítr, částice, zvuky krajiny (krok 8) → VYDEJ, Míša hraje
Každý bod: snímky ze 4 míst + čísla, rozpočet drží.

**II. FUNKCE** – až krása stojí: interakce (louče, mříž, most, ohně, dveře) dotáhnout a rozšířit, pískoviště (katalog předmětů, umisťování), hranice světa měkce, ovládání (mapa, menu), ukládání. Zadání připraví rádce po I.

**III. POSTAVY** – zapojení hrdinů a NPC do světa (sekce 08:33), dialogy, denní režim NPC, příběh. Modely jsou hotové v `main`, čekají.

Odchylka od pořadí jen na Míšův pokyn.
**Míša upřesňuje (08:52):** Funkce a postavy jsou prakticky jedna fáze – přijdou po kráse. Krása = svět **plný zeleně a kamení jako KCD2**: žádná holá plocha. Každý metr louky má trávu, kvítí nebo bylinu; každý okraj lesa keře a mlází; každý svah kameny a suť; každý les padlé kmeny, pařezy, kapradí, mech; každé stavení lidskou stopu. Hustota v rozpočtu přes MultiMesh a LODy – to je účel celé dnešní stabilizace. Měřítko úspěchu: snímek z libovolného místa vypadá reálně, ne „herně“.

---

## 2026-10-17 09:05 – RÁDCE: REFERENCE KRAJINY (Adršpach, Hruboskalsko/Apolena, KCD2, Medieval Dynasty) – pravidla pro fázi KRÁSA

Shrnutí toho, co dělá tyhle krajiny uvěřitelné; platí jako kontrolní seznam pro body 3–6.

**A. Pískovcové skalní město (Adršpach, Teplice, Hruboskalsko, Apolena/Prachov)**
- Věže nejsou volně stojící sloupy na trávníku – stojí **v lese**. Mezi věžemi je soutěska 2–6 m široká, dno v hlubokém stínu, chladné, vlhké: mech na všem, kapradí (kapraď samec, papratka), borůvčí, brusinka, vřes na slunných hranách. Tráva v soutěskách skoro žádná – jehličí, listí, písek.
- **Pata věže**: suťový kužel z odpadlých bloků (0,3–3 m), zapadaných do písku, mezi nimi kapradí a mech. Nikdy čistý přechod věž → rovina.
- **Vrcholy**: borovice lesní (pokroucené, nízké, kořeny přes hranu), bříza, vřes, krátký borůvčí. Ne smrk na vrcholu věže.
- **Barva pískovce**: šedavá až okrová, s tmavými svislými pruhy od zatékání (černé řasy/lišejníky), zelený mech na severu a u paty, místy rezavé (železité) vrstvy. Vodorovné vrstvy (sedimentace) viditelné – to řeší remesh 0,15 m. Římsy a převisy, „hlavy“ na vrcholech (tvrdší vrstva), voštiny (dírky) ve stěnách.
- **Les mezi věžemi**: smrk a borovice (zde ano – skalní města jsou chladnější a kyselé půdy), buk na okrajích, bříza na světlinách. Padlé kmeny přes soutěsky, kořeny obnažené na skále.
- **Světlo**: slunce proniká jen shora v pruzích; dno soutěsky je o 2–3 EV tmavší než vrchol. Mlha v ránu zůstává dole. → V Godotu: ambient occlusion zapečené do terénu soutěsek (tmavý vertex color), mlha výšková v soutěskách.
- **Lidská stopa**: pěšina udusaná v písku, místy kameny jako schody, značka na skále (ne turistická, ale uhelný kříž, zářez), ohniště.

**B. Louka a pole (KCD2 Trosky/Suchdol, Medieval Dynasty)**
- „Trampelpfade“ – vyšlapané pěšiny, kde lidé chodí: od brány k mostu, od chalupy k studni, podél plotů. Užší než cesta (0,5 m), tráva polehlá, hlína prosvítá.
- Louka není jednolitá: ostrůvky vyšší trávy kolem kamenů a kůlů (kosa tam nedosáhne), pruhy po sečení, mez s křovím a kamením (sebrané kameny z pole!), kopřivy a lopuch u hnojiště a plotu.
- Pole: lány s brázdami, úhor s plevelem (vlčí mák, chrpa, heřmánek), strniště po žních, hranice jako mez s trnkou a šípkem.
- Mokřina u potoka: rákos, orobinec, blatouch, vrba hlavatá (ořezávaná!), olše. Bahno s otisky.
- Řasy na stojaté vodě, vodní hladina tmavá, průhledná u břehu – článek k KCD2 to jmenuje přímo.

**C. Les (KCD2)**
- Hustý, špatně průchozí; podrost viditelný do hloubky jen 15–25 m. Okraj lesa je „zeď“ keřů (líska, bez, trnka, mladé buky).
- Patro: tráva jen na světlinách; jinak listí, jehličí, mech, kapradí, borůvčí; padlé kmeny s mechem, pařezy, vývraty s kořenovým talířem a jámou, hromady klestí.
- Stromy různého věku a různě nakloněné; mrtvé stojící kmeny (souše) s odloupanou kůrou; světliny po polomu.
- Zvuk: ptáci, vítr v korunách, datel – článek: „cítil jsem, že to místo cítím“.

**D. Technika (80.lv, obecná praxe)**
- Skály: 5–6 variant, silueta jednoduchá, „velké klidné plochy“ + detailní normála + mokrý/mechový materiál přes vertex paint. Kombinovat do útvarů, ne jednotlivě.
- Voda: hladina je „pruh polygonů“ – uvěřitelnost dělá **okolí**: břehy, kameny, rákos, pěna u překážek, částice.
- Stromy 4 LODy; subsurface na listí; výšková mlha zvedá stíny v pozadí.
- Sednutí do terénu: každý kámen 20–40 % zapuštěný, kolem něj vyšší tráva/kapradí (MultiMesh maska podle vzdálenosti od kamene).

**Co z toho pro naše kroky**
- K4 skály: nejdřív **les mezi věžemi + suť + mech/kapradí + tmavé dno soutěsek**, teprve pak varianty textur. Bez lesa a suti budou věže vždy „kuželky na trávníku“.
- Tvrz zvenčí: pěšiny, mez s posbíranými kameny, kopřivy u hnojiště, vrby hlavaté u příkopu.
- Keřové patro: okraj lesa jako zeď, ne roztroušené keře.

---

## 2026-10-17 09:12 – RÁDCE: KAPITOLA VODA – řešení, ne parametry

Míša: v dřívější verzi se povedlo obtékání kamenů v potoce, ale řeka jako celek ne. Teď máme hladkou hladinu, ostré břehy, modrou barvu, tři kusy potoka. Příčina je systémová: potok je **plochý mesh s jedním shaderem bez informace o toku, hloubce a překážkách**. Parametry to nespraví.

**Řešení: addon Waterways (Arnklit, MIT, Godot 4)** – generuje mesh řeky podél Bézierovy křivky a **zapeče mapy toku a pěny z kolizí**: paprsky z hladiny najdou kameny → vzdálenostní pole → pěna kolem překážek, zrychlení v úžinách, směr toku podél křivky. Přesně to, co „obtékání kamenů“ dělalo dobře, ale pro celou řeku a bez ručního ladění. Hloubka: barva mezi mělkou a hlubokou podle hloubky, průhlednost podle hloubky. Bez odrazů v reálném čase (my je stejně nechceme). Jen řeky – rybník a příkop zůstávají na vlastním shaderu.
- Ověřit na Compatibility: addon používá vlastní shader; pokud sahá na DEPTH_TEXTURE (Compatibility ji nemá), nahradit hloubku zapečenou vertex color (vzdálenost hladiny od terénu pod ní, spočítat při generování meshe). Zbytek (flow map, foam map, normály) je čistá textura – běží všude.
- Rozpočet: mesh řeky pár tisíc troj., 3 textury 1024 (flow, foam, normály). V pořádku.
- Postup: 1) nainstalovat addon, křivka potoka podle současné trasy (3 díly → 1 křivka), 2) kolize kamenů v korytě + břehy, bake flow & foam, 3) parametry: rychlost pomalá (0,3), pěna jen u kamenů a břehů, barva mělká hnědozelená (#5A6B3A), hluboká tmavá (#1E2A1C), čirost nízká, 4) břeh: terén pod hladinou klesá pozvolna (mělčina 0,5–1 m), mokrý pruh textury 30 cm nad hladinou (zem.gdshader maska podle výšky nad vodou), 5) kameny v korytě z fotoskenů, 20–40 % zapuštěné, kolem nich pěna automaticky z bake.

**Rybník a příkop (ne Waterways):** vlastní shader, stojatá voda: normála slabá (0,15) a pomalá, barva tmavá zelenohnědá, okřehek/řasy jako alfa karty u břehu (ne tečky na celé hladině), rákos a orobinec v pásu 1–2 m od břehu, mělčina s bahnem. Hrana břehu nikdy ostrá – terén klesá pod hladinu.

**Co z referencí:** uvěřitelnost vody dělá okolí, ne shader (80.lv) – břehy, kameny, rákos, pěna u překážek. KCD2: stojaté vody mají řasy na hladině, potoky jsou mělké a klikaté, viditelné dno.

Pořadí uvnitř bodu „voda“: nejdřív Waterways na potoce u mostu (jedno místo, screenshot), pak zbytek toků, pak rybník/příkop.

---

## 2026-10-17 09:20 – RÁDCE: EKOLOGIE ZELENĚ – kde co roste (střední Čechy, Posázaví, 1393)

Rozmístění vegetace musí vycházet z **terénu**, ne z náhody: výška, sklon, orientace svahu (sever/jih), vlhkost (vzdálenost od vody, prohlubně), půda (písek u skal, hlína v údolí), a lidské využití (pole, pastvina, cesta). Jedna funkce `biotop(x, z) → váhy druhů`, z ní všechny rozsevy.

**1. Niva a břehy (do 1 m nad hladinou, rovina u vody)**
- Stromy: **olše lepkavá** (přímo u vody, kořeny ve vodě), **vrba** (bílá u řeky, hlavatá ořezávaná u vsi a příkopu – lidská stopa), jasan, topol černý vzácně.
- Keře: vrba křovitá (pruty), bez černý, střemcha.
- Byliny: rákos, orobinec, ostřice, blatouch, tužebník, kopřiva (bohatá půda), pcháč.
- Žádný dub, žádná borovice, žádný smrk.

**2. Údolí a mírné svahy do 300–400 m (louky, pole, ves, tvrz)**
- Les: **dub letní + habr** (dubohabřina – typický les Posázaví), **lípa srdčitá** (u vsi, u kapliček – posvátný strom), bříza na světlinách a mezích, jabloň/hrušeň plané u cest. Buk jen na severních svazích.
- Solitéry: dub na pastvině (velký, rozložitý, nízko větvený – rostl volně), lípa na návsi, vrba hlavatá u rybníka.
- Keře na mezích: **trnka, šípek, hloh, líska, bez**. Mez = kameny posbírané z pole + tyhle keře.
- Pole, pastvina: žádné stromy uvnitř, jen na okraji; na pastvině solitérní duby a jalovec (spásané, ostrý).
- Smrk zde **ne** (do 14. stol. v nížině nerostl, přišel až s lesnictvím 18. stol.).

**3. Svahy a hřbety 400–600 m, severní strany**
- **Buk lesní** (bučina – stinný les, holé dno, listí, málo podrostu), **jedle bělokorá** (ve 14. stol. běžná, dnes vzácná – pro dobovost ano!), smrk jako příměs na severu a v inverzních roklích, javor klen v roklích.
- Podrost bučiny: kapradiny, šťavel, kyčelnice, mech jen na kamenech; tráva skoro žádná. Dno = listí.
- Jižní svahy: dub zimní, borovice na skalnatých hranách, vřes, metlička (suchá tráva), jalovec.

**4. Skalní město a pískovcové plošiny (kyselá chudá půda, písek)**
- **Borovice lesní** (vrcholy věží, hrany, pokroucená), **smrk** (v chladných soutěskách – zde oprávněný), bříza bělokorá (světliny, suť), jeřáb ptačí, buk na okrajích.
- Podrost: **borůvčí** (plošně pod borovicemi a smrky), brusinka, vřes na slunných hranách, kapradí (soutěsky), mech na všem stinném, metlička.
- Žádný dub, lípa, habr uvnitř skalního města.

**5. Narušená místa (lidská stopa)**
- Kolem stavení: bez černý (u každé chalupy – ochranný strom), kopřiva a lopuch u hnojiště, merlík, pelyněk na rumišti, sléz u zdi.
- Cesty: jitrocel a truskavec ve vyjetých kolejích (snášejí sešlap), tráva polehlá na okrajích, pcháč a bodlák na mezích.
- Úhor: vlčí mák, chrpa, heřmánek, koukol.
- Opuštěné místo (ruiny): bez, bříza (první strom na zřícenině), kopřiva, břečťan na zdi, osika.

**6. Vzhled podle stáří a stanoviště (stejný druh, jiný tvar)**
- Strom v lese: vysoký, úzká koruna, holý kmen do 2/3 výšky (konkurence o světlo).
- Strom na volno (solitér, mez): nízký, široká koruna, větve od 1,5 m.
- Na hraně skály / větru: nakloněný po větru, jednostranná koruna, pokroucený kmen.
- Souše (mrtvý stojící): 3–5 % stromů v lese, bez kůry, bílé, krátké pahýly.
- Padlé kmeny: 1 na 100 m² lesa, s mechem, u vývratu kořenový talíř + jáma.

**7. Hustota a shluky (platí pro vše)**
- Shluky, ne rovnoměrně: Poissonův rozsev s proměnlivým poloměrem podle biotopu (les 4–7 m, okraj 2–3 m, louka solitéry 40–80 m).
- Okraj lesa je **ekoton**: pás 5–15 m s keři a mladými stromy, hustší než les uvnitř.
- Pod velkým stromem tráva řidší (stín, sucho), kolem kmene listí; pod solitérním dubem na pastvině naopak udusaná zem (dobytek stojí ve stínu).
- Kameny: na svazích podle sklonu (čím strmější, tím víc), pod skalami suť, na polích žádné (sebrané na mez), v potoce ano.

**Převod do kódu:** masky z terénu – výška (y), sklon (normála), orientace (normála·sever), vlhkost (vzdálenost od vody + prohlubně), půda (vzdálenost od skal = písek), využití (pole/cesta/ves z svet.json). Každý druh má váhovou funkci z těchto masek; rozsev vybírá druh podle vah. Stejné masky řídí trávu, keře, kameny a mrtvé dřevo. Jedno místo pravdy, žádné ruční rozmisťování kromě solitérů a lidské stopy.

---

## 2026-10-17 09:25 – ZADAVATEL (Míša): svět má být zážitek sám o sobě

„Chci chodit krajinou a říct si: wau, to je reálný svět.“ Nejen příběh – samotné procházení musí bavit: skalní město, výhled z kopce, houby v lese, byliny dotažené do dokonalosti. Hráč se nesmí nudit, i když nedělá quest.

**Co z toho plyne pro krásu (rádce):**
1. **Místa, kam stojí za to dojít** – každé má vlastní tvář: skalní město (soutěsky, vyhlídka na věži), vrchol kopce s výhledem na údolí a tvrz, rybník s vrbami, bučina s potokem, úhor s máky, ruiny. Mezi nimi krajina, která se mění, ne jednotvárná louka.
2. **Sběr jako důvod se dívat:** houby (hřib pod smrkem a dubem, křemenáč pod břízou, liška v mechu, muchomůrka červená – poznávání, ne sběr; po dešti víc), byliny podle stanoviště (jitrocel u cesty, kopřiva u plotu, heřmánek na úhoru, třezalka na mezi, mateřídouška na suchém svahu, blatouch u vody, vlaštovičník u zdi, barvínek v lese). Sběr už existuje (sber.gd) – dotáhnout: správné stanoviště, sezóna, viditelnost zblízka, animace sehnutí, zvuk.
3. **Odměna za zvědavost:** vyhlídka = postava se zastaví a kamera ukáže panorama; v soutěsce ozvěna; u potoka ryby; pod skálou liščí nora; v lese srnka utíká; v ruině skrytá věc. Malé věci, které říkají „tenhle svět žije“.
4. **Změna během dne:** mlha ráno v nivě, zlaté světlo večer na skalách, noc s hvězdami a loučí. Denní doba už je (daylight.gd) – doladit na místech, kde se dívá hráč.
5. **Cesty vedou někam:** pěšiny k houbovým místům, k vyhlídce, k prameni – ne jen mezi budovami.

Toto je cílová laťka fáze KRÁSA; body 1–7 plánu k ní vedou. Sběr hub/bylin a „život“ (bod 3) zařadit do krásy jako krok 8 – jsou to důvody, proč krajinou chodit.

---

## 2026-10-17 09:35 – RÁDCE: KAPITOLA SBĚR – houby a byliny (krok 8 fáze KRÁSA)

**Jak to dělá KCD/KCD2 (zdroj: wiki.gg, deltiasgaming):** ~16 bylin, každá má stanoviště (jitrocel/pampeliška všude, kostival a kopřiva u vody, heřmánek na polích, třezalka a šalvěj na pastvinách, pelyněk a bodlák u cest, máta v zahradách, vraní oko hluboko v lese u potoků). Sběr: postava se sehne (animace ~1 s), s rostoucí dovedností se zvětšuje **poloměr sběru** – jedno sehnutí sebere víc rostlin kolem; XP jen za cílenou rostlinu; čerstvé byliny do ~48 h zvadnou, sušené vydrží. Perky: síla ze sbírání (dřepy), +odolnost po 100 kopřivách, +charisma s kyticí. Houby: muchomůrka hluboko v lese u řek, ve shlucích (150–500 kusů na místě!), jedovatá, surovina na jedy. KCD2 má jedlé houby k jídlu/vaření. Rostliny jsou **vidět**: každá má model, nejsou to ikony – hráč se učí je poznávat zrakem.

**Co převzít, co udělat jinak (Míša: dotáhnout do dokonalosti):**

### A. Rostliny podle stanoviště – rozsev z biotopových masek (sekce 09:20)
Byliny (dobové, lidové léčitelství 1393 – žádná alchymistická laboratoř, ale bába kořenářka, sušení, odvary, obklady):
| Bylina | Stanoviště | Doba | Užití (doba) |
|---|---|---|---|
| jitrocel kopinatý | cesty, sešlap, meze | V–IX | rána, kašel |
| kopřiva | u plotů, hnojiště, břehy, ruiny | IV–X | polévka, posila, provaz |
| heřmánek | úhor, pole, náves | VI–VIII | zánět, oči, spaní |
| třezalka | meze, suché svahy, okraj lesa | VI–VIII | rána, olej, „na duši“ |
| mateřídouška | suché slunné svahy, skály | VI–IX | kašel, koření |
| řebříček | louky, meze | VI–IX | krvácení, žaludek |
| blatouch | břehy, mokřina | IV–V | (jedovatý – jen poznat) |
| kostival | příkopy, břehy | V–VII | zlomeniny, obklad |
| vlaštovičník | u zdí, ruiny, stín | V–IX | bradavice (jedovatý) |
| barvínek | listnatý les, hráz | IV–V | (už ve hře) |
| sléz | u chalup, cesty | VI–IX | kašel, krk |
| pelyněk | rumiště, cesty, úhor | VII–IX | žaludek, hořký |
| bez černý (květ, plod) | u každé chalupy | V–VI / VIII–IX | pot, nachlazení |
| lípa (květ) | náves, u kapličky | VI–VII | pot, čaj |
| šípek, trnka (plody) | meze | IX–X | zima, sušení |
| borůvka, brusinka | pod borovicí a smrkem, skalní město | VII–IX | jídlo |
| jahoda lesní | světliny, okraj lesa | VI–VII | jídlo |
| náprstník, rulík, durman | hluboký les, rumiště | VI–IX | **jedy** – poznat a nechat |

Houby (pod jakým stromem, mykorhiza – to je ta „logika“):
| Houba | Strom / místo | Doba | Jedlá |
|---|---|---|---|
| hřib smrkový | smrk, mech, okraj paseky | VII–X | ano (král) |
| hřib dubový | dub, habr, světlý les | VI–IX | ano |
| křemenáč | bříza, osika | VII–X | ano |
| kozák březový | bříza, vlhko | VII–X | ano |
| liška | mech pod smrkem/bukem, shluky | VI–X | ano |
| bedla vysoká | okraj lesa, pastvina | VIII–X | ano |
| václavka | pařezy, padlé kmeny (trsy) | IX–XI | ano, vařená |
| muchomůrka červená | bříza, smrk | VIII–X | **jed** (poznávací) |
| muchomůrka zelená | dub, buk | VII–X | **smrtelná** – past pro neopatrné |
| hřib satan | vápenitý svah, dub | VII–VIII | jed |
| pýchavka | louka, pastvina | VII–X | ano mladá |
| choroš, troudnatec | mrtvé kmeny (nesbírat, troud na oheň!) | celoročně | troud |

### B. Pravidla mechaniky
1. **Viditelnost zrakem, ne ikonou.** Každý druh má model a je rozpoznatelný z 3–5 m. Žádná záře, žádný „smysl“. Hráč se učí: liška je oranžová v mechu, hřib hnědý klobouk u smrku. Interakce až při pohledu zblízka (do 1,5 m) – ukáže jméno, pokud ho postava **zná** (viz 4).
2. **Shluky podle stanoviště:** houby ve skupinách 3–15 kolem „svého“ stromu, byliny v porostech 1–5 m. Rozsev z biotopových masek + strom-partner pro houby. Po dešti a ráno víc hub (24–48 h po dešti ×2), na podzim nejvíc; v zimě nic.
3. **Sběr:** sehnutí (animace ~0,8 s), zvuk utržení/vytažení, poloměr sběru podle dovednosti (1 m → 2,5 m). Rostlina po sběru zmizí a obnoví se za 3–7 herních dní na stejném místě (trvalá stanoviště – hráč si pamatuje „své“ místo na hřiby).
4. **Poznávání (dovednost Bylinkář/Houbař 0–20):** na začátku vidí jen „houba“, „bylina“. Pojmenuje, co ho někdo naučil (kořenářka, hostinský, kniha z fary) nebo co sám vyzkoušel. Neznámá houba snědená = náhoda (zvracení, jed, nic). To je napětí, které KCD nemá: muchomůrka zelená vypadá jako žampion.
5. **Použití:** jídlo (houby na ohni, polévka), sušení na půdě hostince (3 dny, pak trvanlivé), odvar u kořenářky (léčení, spánek, odolnost), prodej (málo – jako KCD), dary (kytice, byliny pro Elišku – sociální), quest (najít konkrétní bylinu pro nemocného).
6. **Zvadnutí:** čerstvé 2 dny, pak „zvadlé“ (horší), sušené neomezeně. Houby 1 den čerstvé.
7. **Odměny za zkušenost:** po 100 kopřivách +odolnost (KCD), po 50 hřibech „zná místa“ – na mapě se objeví houbová místa, po 200 bylinách rychlejší sběr. Síla ze sbírání ne – dřepy jsou KCD vtip, u nás spíš „vytrvalost“ z chůze lesem.
8. **Jedy jako příběh:** muchomůrka zelená u dubu, rulík na rumišti u ruin, blatouch u vody – poznat je je dovednost; jed lze použít (lapkové, quest), ale s následky pro pověst.

### C. Technika
- Rozsev sběrných rostlin = stejný MultiMesh systém jako podrost, s příznakem „sběr“ a druhem v custom data; sber.gd už existuje – rozšířit o stanoviště, stromového partnera, sezónu, obnovu a poloměr.
- Modely: 20–30 bylin + 12 hub, každá ≤ 150 tris, atlas 1024 společný. Houby jako mesh (klobouk + noha), ne karty – musí jít poznat z úhlu.
- Zvuky: utržení, prasknutí nohy houby, šustění; animace sehnutí z UAL.
- Rozpočet: +0,2 M tris v lese při hustotě hub 1/10 m² – OK.

**Pořadí:** 1) stanoviště + partner-strom + rozsev (masky), 2) modely 12 hub + 10 nejčastějších bylin, 3) sběr s poloměrem a obnovou, 4) poznávání a jedy, 5) sušení/jídlo/odvar, 6) odměny a mapa míst. Kroky 1–3 patří do krásy (krajina žije), 4–6 do funkcí.

---

## 2026-10-17 09:07 – RÁDCE: zbývá ~6 % limitu do pondělí – co stihnout

Priorita je **jedno vydání, které Míša může hrát o víkendu**. Ne začínat nic nového.
1. Dokonči, co máš rozdělané z vody a kamene tvrze – v jakémkoli stavu, který je lepší než 0.45. Waterways nezačínej, pokud není nainstalovaný; stačí břehy a barva.
2. Pokud zbyde čas: skály – les mezi věžemi + suť u paty (sekce reference, bod A). Jen rozsev, žádné nové modely.
3. **VYDEJ 0.46**, zapiš stav.md (co je hotovo, co je rozpracované a kde), a zastav se.
Při 2 % zbývajících: okamžitě commit + push rozdělané práce s poznámkou do stav.md, i bez vydání. Nic nesmí zůstat jen v pracovní kopii.
V pondělí pokračujeme fází krása podle plánu (sekce 08:50): skály, tvrz zvenčí, keře a mrtvé dřevo, ruiny, sběr.

## 2026-10-17 – voda: Waterways na potoce (do 0.47)

- addons/waterways (MIT, větev godot4_5_1) jen jako knihovna pro zapečení; `tools/reka_bake.gd` (headless):
  osa toku z blender/kraj.py REKA (modely/reka/osa.json), hladina ze staré sítě Reka_voda (vyhlazená), šířka
  z paprsků do terénu, `_generate_flowmap(1024)` → modely/reka/reka_flow.png + reka_dist.png, síť 5 184 troj.,
  hloubka do COLOR.r (paprsek na dno).
- `shaders/reka.gdshader` = shader Waterways bez depth/screen textury (Compatibility): barva a průhlednost podle
  hloubky z vrcholů → měkký břeh místo zubaté hrany. Stará mřížková hladina potoka skrytá.
- Otevřené: barva doladit na tabletu; rybník a příkop zatím beze změny (vlastní shader, další krok).
- Balvany „Skaly“ u tvrze (pruhy) skryté na Míšův pokyn – nahradit fotoskeny v K4.
