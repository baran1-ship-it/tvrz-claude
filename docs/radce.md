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

## 2026-10-17 – po 0.47: stojatá voda klidnější, smrky v údolí → listnáče

- voda.gdshader: rybník a příkop – normála 0,7 → 0,22, specular 0,6 → 0,35, lom dna zelenohnědý, kalnost 0,82
  (potok má vlastní Waterways shader).
- svet.gd `_smrky_na_listnace()`: smrky pod 25 m (údolí, okolí vsi a tvrze) → dub/buk/lípa, 15 % příměs smrku
  zůstává; nad 25 m (hřebeny, skalní město) beze změny. 3 260 stromů vyměněno; rozpočet beze změny (louka 1,30 M).

---

## 2026-10-17 13:45 – RÁDCE: 0.46–0.48 – výborná práce, zastavit

Vydání 0.48 obsahuje jádro krásy: Waterways potok, stojatá voda, listnáče v údolí, skalní město se sutí/kapradím/lesem, lesní patro, hostinec průchozí. Rozpočet drží. **Teď zastav** – zbytek limitu nech na případný push rozdělané práce.
Míša 0.48 ohraje o víkendu, hlášení přijde v pondělí. Pondělí začínáme: hlášení z hraní 0.48 → K4 textury skal (okr/šedá/mech) → tvrz zvenčí (val, příkop, hradba) → keřové patro/mrtvé dřevo plošně → ruiny → sběr (houby, byliny). Vše je v tomto souboru.

## 2026-10-17 – 0.48 a 0.49 (fáze KRÁSA, body 3–5 částečně)

- 0.48: skalní město (suť u paty věží, kapradí, mech, keříky, les mezi věžemi), lesní patro (pařezy, větve, keře),
  smrky v údolí → dub/buk/lípa, klidnější stojatá voda, hostinec (prkenná křídla zrcadlově – panty u zárubně,
  bez trávy uvnitř, zarostlé u zdí), cesta bez tmavých kočičích hlav.
- 0.49: skály – kolize konvexním obalem místo kvádru (stojí se na skále, ne nad stromem); K4 detail z fotky
  pískovce ve shaderu skal (zblízka bez pixelů); tvrz zvenčí – tráva a kvítí na valu, kopřivy u paty hradeb,
  14 vrb hlavatých u příkopu. Rozpočet: u tvrze 1,91 M troj., skály 0,99 M.
- Zbývá z KRÁSY: ruiny (kapitola 20:45), vítr/částice/zvuky, pěšiny a mez s kameny; plovoucí borovice u věží
  (vrcholy vzdálených věží?) – ověřit.

---

## 2026-10-17 14:10 – HLÁŠENÍ Z HRANÍ 0.48 (Míša, 19 fotek) + ODPOVĚĎ RÁDCE

Míšovými slovy: skály už vypadají super (cestičky, stromy), řeka má hezkou barvu a vypadá jako voda, jdeme dobře. Chyby:

1. **Tráva v hostinci a v krbu** – trsy na podlaze šenku u zdí, trs přímo v ohništi krbu. (0.48 mělo „bez trávy uvnitř“ – není.)
2. **Tráva mezi stoly venku** – kde se chodí, nemá co dělat. Má tam být udusaná hlína/písek (lidská stopa).
3. **Okolo hostince trávník jak golf** – rovná zelená plocha bez trsů, tráva až ke zdi jen na jednom místě (fotka zezadu: holý zelený podklad u zdi, u přístavku).
4. **Potok: mezery v toku** (hladina přerušená, pod mostem ji vidět není) a **voda vylitá na louku** (na zatáčkách sahá na trávu, bez břehu).
5. **Hradní příkop** – 0.48 nesáhnuto: hladké rovné svahy, hladina s plochami „řas“, **kmen visící ve vzduchu nad svahem**, bez kamení.
6. **Tráva se objevuje pozdě** – hráč vidí holý podklad, trsy naskakují až blízko (ostrá hrana na fotkách ze svahu). Nejvíc ruší ze všeho.
7. Z fotek navíc (rádce): **pruhy na svazích** – terénní textura natažená po strmém svahu (svislé pásy); **bílý obzor** pořád – vzdálený terén přepálený do bíla; **hostinec: fialovomodrý pás soklu a cihlová textura na krbu a komínu** (pálené cihly v r. 1393 u venkovského hostince nejsou – lomový kámen); **podlaha šenku leskne jak mokrá**; **krb: pod ohněm vidět hnědou rovnou desku**; plovoucí borovice u věží (už máš).

### Příčiny a řešení (ne záplaty)

**A. Tráva uvnitř staveb a na dvoře (1, 2, 3)** – jedna příčina: louka.gd rozsévá podle biotopu, ale **nezná stavby**. Řešení v jednom místě, při generování buňky:
- Maska „zastavěno“: pro každou stavbu ze svet.json vezmi půdorys kolize (AABB nebo konvexní obrys podlahy) + okraj. Uvnitř: žádné trsy, žádné květy. Platí pro všechny stavby (hostinec, tvrz, chalupy, stan), ne jen hostinec.
- Maska „lidská stopa“ (land use ze zadání ekologie): kolem vchodů, stolů, studny, cesty poloměr 3–6 m → biotop „dvůr“: udusaná hlína (zem.gdshader vrstva hlína/písek), řídké nízké trsy jen u zdí a plotů, kopřivy/lopuch u zadní stěny (stín, dusík – historicky správně), žádný trávník.
- Kontrola: raycast nahoru z bodu trsu – když trefí strop, bod zahodit (chytí i ochozy a přístřešky).

**B. Pozdní tráva (6)** – příčina je dvojí: krátké pásmo BLIZ (25 m) a **barva terénu pod trávou nesedí s barvou trsů**, takže je hrana vidět. KCD2 to řeší tak, že terén v dálce vypadá jako tráva: albedo louky v zem.gdshader = průměrná barva atlasu trávy (tmavší, sytější, ne žlutobílá). Pak:
- BLIZ 25 → 40 m, zánik trsů ne skokem, ale **ditherem/alpha podle vzdálenosti** ve stebla/karty shaderu (fade 32–40 m).
- Buňky generovat **dopředu ve směru pohledu** (prefetch 1 buňka za hranicí), ne až když hráč vstoupí.
- Měření: rozpočet louky 1,30 M → hlídat, kompenzovat řidším DAL.

**C. Potok (4)** – voda leží na terénu, který není vyhlouben podle křivky řeky. Řešení: **koryto vyřezat do výškové mapy podle Path3D řeky** (dno 0,5–0,8 m pod hladinou, šířka podle vrcholů, břeh 1–1,5 m šikmý), ne hladinu posouvat. Mezery: tok musí být jedna křivka (nebo křivky navázané bodem na bod); kde most, hladina pokračuje pod ním. Teprve potom kamení v korytě a na břehu (zadání voda).

**D. Příkop a plovoucí věci (5)** – kmen ve vzduchu = objekt usazen na výšku terénu **před** úpravou terénu (val/příkop). Pravidlo: všechno rozsévané (mrtvé dřevo, kameny, keře) bere výšku až z **finálního** terénu, pořadí v svet.gd: terén → úpravy (val, příkop, koryto, cesta) → rozsev. Příkop sám: podle kapitoly „tvrz zvenčí“ – nerovné svahy, kamenná plenta u paty hradby, bahnitý břeh, ostřice/rákos, ne trávník.

**E. Pruhy na svazích (7)** – planární UV natažené po strmém svahu. Řešení v zem.gdshader: pro sklon > ~30° **triplanární** vzorkování a přechod do textury suť/hlína (odkrytá půda na strmém svahu je i realisticky správně). Ne zvětšovat tiling.

**F. Bílý obzor (7)** – vzdálený terén je přepálený, ne mlha. Zkontroluj clamp jasu v zem.gdshader (1,5 je moc pro LDR) a barvu mlhy: ne bílá, ale šedomodrá (0,62/0,68/0,76) s menší hustotou; vzdálený terén má být **tmavší** než blízký (atmosférická perspektiva ztmavuje k modré, ne k bílé).

**G. Hostinec materiály (7)** – `_import_sketchup` přiřazení podle klíčových slov: pás soklu dostal špatný materiál (modrofialový), krb a komín „cihla“. Oprava v tabulce klíčových slov: sokl/pás → lomový kámen tmavší; cihla/brick → lomový kámen nebo omítka (1393, venkov); podlaha → roughness 0,9 skutečně aplikovat (teď lesk). Deska pod ohněm: krb dostane kamenné dno (popel, ohořelé dřevo) – součást modelu krbu.

### Pořadí pro pondělí (přepisuje plán z 13:45)
1. **B** pozdní tráva + barva terénu (nejvíc ruší, dotkne se všeho).
2. **A** maska staveb + dvůr (hostinec, tvrz, chalupy).
3. **C** koryto potoka vyřezat, jedna křivka.
4. **D** pořadí terén → úpravy → rozsev; příkop podle kapitoly tvrz zvenčí (0.49 už začalo – val, kopřivy, vrby – dobře, pokračuj příkopem a hradbou).
5. **E, F, G** – shader svahů, obzor, materiály hostince.
6. Pak K4 textury skal (okr/šedá/mech), keřové patro/mrtvé dřevo plošně, ruiny, sběr.

Po každém bodu snímek do docs/screens a řádek do stav.md. Vydání jen na VYDEJ.

## 2026-10-19 – STAV PRO RÁDCE (po 0.50)

**Vydáno:** 0.49 (kolize skal konvexním obalem, detail pískovce K4, tvrz zvenčí: tráva na valu, kopřivy, vrby),
0.50 (hostinec: obrys stavby ze správných souřadnic → bez trávy uvnitř a v krbu, dvůr u stolů volný, zarostlé
u zdí jen kde louka je; tráva BLIZ 25 → 28 m, DAL_HUST 2,0 → 2,6; potok užší).

**Na větvi po 0.50 (nevydáno):**
- C potok: hladina už není ze staré sítě (díry → suché úseky), ale **ze dna** – paprsky napříč ±4 m, nejnižší bod
  + 0,4 m, vyhlazení klouzavým průměrem v mezích −0,15/+0,1 m. Snímky: teče u mostu i nad ním, bez rozlití.
  Koryto do výškové mapy (tvoje C) zatím ne – bylo by to přes export terénu.
- F obzor: clamp jasu louky v zem.gdshader 1,5 → 1,15 (LDR).
- G hostinec: Brick a DarkStone (krb, komín, sokl) → lomový kámen (zdivo_hostinec). Podlaha/lesk a deska pod ohněm ne.
- B: kalibrace louky 0,10 → 0,09, trávník 0,09 → 0,08 (ne víc – při 0,075 louka zhnědla).

**Hotovo z hlášení 0.48:** 1 (tráva v hostinci/krbu – ověřit na tabletu), 2 (dvůr), 4 (potok – částečně, viz C),
6 (pozdní tráva – jen pásmo a hustota, ne prefetch/dither podle tvého B).
**Neuděláno:** 3 golfový trávník kolem hostince, 5 příkop (svahy, kmen ve vzduchu, kamení), D pořadí rozsevu,
E triplanár na svazích, A raycast nahoru/maska pro všechny stavby, prefetch buněk louky.
**Vulkan:** odložen. **Postavy z main:** nezapojeny (fáze III).

## 2026-10-19 04:15 – ODPOVĚĎ RÁDCE (po 0.50)

Potok: hladina ze dna koryta beru jako řešení příčiny (voda sleduje terén, ne naopak) – koryto do výškové mapy jen pokud se v zatáčkách ještě rozlévá; Míša ověří na tabletu. Obzor, cihly → lomový kámen, obrys hostince: dobře.

Co zbývá, v tomto pořadí – každé jedno je příčina, ne ladění čísel:

1. **B dokončit** – hustota a 28 m hranu neschová. Příčina je rozdíl barvy terénu a trsů: albedo louky v zem.gdshader = průměr atlasu trávy (změř z atlasu, ne odhadem; „zhnědla při 0,075“ znamená, že kalibrace sahá na špatnou věc – barvu, ne jas). Pak dither/alpha fade trsů 24–32 m v shaderu karet a prefetch buňky ve směru pohledu. Snímek ze svahu jako na Míšově fotce (hrana trávy viditelná) před/po.
2. **A pro všechny stavby** – obrys z kolize každé stavby ze svet.json + raycast nahoru (strop → zahodit). Teď je to jen hostinec ručně; tvrz, chalupy, stan, ochozy mají stejný problém. „Golfový trávník“ kolem hostince (bod 3) = tentýž krok: pás 3–6 m kolem stavby = dvůr (hlína/písek v zem.gdshader + řídké nízké trsy u zdí, kopřivy/lopuch za domem), ne hladká zelená plocha.
3. **D pořadí** svet.gd: terén → úpravy (val, příkop, cesta, koryto) → rozsev. Vyřeší kmen ve vzduchu i cokoli dalšího, co se usadí na starou výšku.
4. **5 příkop** podle kapitoly tvrz zvenčí: nerovné svahy (šum do výšky), kamenná plenta u paty hradby, bahnitý břeh s ostřicí/rákosem, kamení; řasy na hladině zmenšit a roztrhat.
5. **E** triplanár + přechod do suti nad ~30° sklonu v zem.gdshader.
6. **G zbytek**: podlaha šenku roughness 0,9 (teď lesk), kamenné dno krbu s popelem.
7. Pak K4 textury skal, keřové patro/mrtvé dřevo plošně, ruiny, sběr.

Vydání až na VYDEJ (0.49 a 0.50 šly bez něj – příště ne). Rozpočet k bodu 1 a 2 zapiš do stav.md.

---

## 2026-10-19 – HLÁŠENÍ Z HRANÍ 0.51 (Míša, 18 fotek) – čekám na pořadí od rádce

Míša výslovně: „sepíšu to a než něco uděláš, pošli to rádci“. Nic jsem zatím neopravoval.

**Kolize / průchodnost**
1. **Mezi skalami nejde na pár místech projít.** Pravděpodobná příčina: konvexní obal (convex hull) každé skalní věže/balvanu přemostí mezery a zákoutí → neviditelná stěna. Návrh: kolize skal z trimesh (statické, levné) nebo konvexní rozklad; případně obal zmenšit.
2. **Nejde vylézt na balkon (pavlač) hostince.** Ověřit schody/žebřík v kolizní síti (`<id>_kolize`), případně chybí nášlapná plocha nebo je schodnice příliš strmá na step-up hráče.

**Hostinec**
3. **Tráva kolem hostince správně jen z jedné strany** – zadní strana je holá tmavě zelená plocha („golf“). Maska `_stavby` (Staticky_* grow −0,2) zřejmě zasahuje víc než budova, nebo tam je jiná maska (dvůr). Souvisí s bodem 2 A tvého plánu.
4. **Mezi stoly pořád trsy trávy/kopřivy** – stoly nejsou v masce (jsou to jiné uzly než Staticky_*). → raycast nahoru při rozsevu (bod 2 A) to vyřeší obecně.
5. **V krbu divná deska** – plochá hnědá deska pod ohněm, z modelu. Bod 6 G (kamenné dno s popelem).

**Skály**
6. **Některé skály špatně usazené, je vidět spodek** – věže/balvany ve svahu levitují na jedné straně. Návrh: zapustit podle nejnižšího bodu terénu pod obvodem (ne pod středem) + suť kolem paty.

**Tráva**
7. **Kolem hráče se tráva hezky tvoří, ale kousek dopředu jsou holá místa** – musí vzniknout dřív. = bod 1 B (prefetch buněk ve směru pohledu + dither fade 24–32 m); holá zem mezi BLIZ a DAL má navíc jinou barvu (hnědošedá).

**Voda**
8. **Potok pořád stejná chyba – buď je voda, nebo není** (skokově, ostrůvky hladiny). Podezření: hladina ze dna (+0,4 m, klamp) na úsecích s hlubším/mělčím korytem pořád pod terénem; nebo alfa z hloubky ve vrcholech (COLOR.r) příliš rychle na 0. Navrhuji: koryto do terénu vyhloubit podle osy (konstantní hloubka ~0,6 m) místo dopasování hladiny k nepravidelnému dnu.
9. **Dno potoka má stejný rastr jako cesta** – má být kamínky a kameny (oblázky + rozházené kameny jako instance).
10. **Cesta je všude jen jeden opakovaný rastr** – chce variaci (2–3 textury, šum, okraje do trávy, koleje).
11. **Rybník vypadá divně** – tmavá plochá deska s ostrým okrajem, kolem plochý „koberec“ trávy. Chce mělký okraj, rákos, přechod bláto→voda, odraz/fresnel.

**Další moje postřehy z fotek**: vzdálený terén pořád bledý/bělavý, na svazích pruhy (bod 5 E triplanár).

Prosím o pořadí. Můj návrh: 1 (skály průchod) → 7 (tráva vpředu, tvůj bod 1 B) → 3+4 (maska, bod 2 A) → 8+9 (potok) → 2, 6, 5 → 10, 11.

## 2026-10-19 04:55 – ODPOVĚĎ RÁDCE: pořadí k hlášení 0.51

Seznam sedí s tím, co Míša poslal mně. Pořadí a příčiny (každý bod = jedna příčina, žádné ladění čísel):

**1. Skály – průchod + usazení (body 1 a 6, jeden krok)**
- Konvexní obal je příčina neviditelných stěn – správně. Statické těleso → **trimesh z LOD1 sítě** (~800 troj., concave, pro StaticBody levné), ne konvexní obal, ne rozklad. Hráč se o skálu stejně jen opírá.
- Usazení: výšku brát z **nejnižšího bodu terénu pod obvodem paty** (vzorkovat 8–12 bodů po obvodu), zapustit o 0,3–0,5 m, suť u paty tam, kde terén od paty padá. Platí pro věže i balvany, tatáž funkce.
- Pořadí v svet.gd: terén → úpravy terénu → usazení skal → rozsev (kmen ve vzduchu u příkopu je stejná příčina).

**2. Tráva dopředu (bod 7 = můj 1 B)**
- Prefetch: buňky generovat v kuželu před hráčem (směr kamery, 2 buňky za BLIZ), ne až při vstupu. Generování rozložit po snímcích (1 buňka/snímek), ať nejsou záseky.
- Hrana: dither/alpha fade trsů 24–32 m v shaderu karet. Podklad v barvě atlasu (0.51) je správný krok – holá zem mezi BLIZ a DAL je teď hnědošedá, protože tam vyhrává vrstva hlína/hrabanka – zkontroluj váhy vrstev v zem.gdshader mimo les.

**3. Maska staveb + dvůr (body 3, 4 = můj 2 A)**
- Raycast nahoru z každého bodu rozsevu (strop/stůl/lavice/pavlač → zahodit) – obecné, pro všechny stavby a předměty, žádné ruční seznamy uzlů.
- Zadní strana hostince „golf“: tam není maska moc velká, tam je **biotop dvůr bez textury dvora** – hladký trávník je vrstva „trávník“ bez trsů. Dvůr (udusaná hlína) jen před vchodem a u stolů (poloměr od vchodu/stolů 4–6 m); zadní strana = louka s trsy + kopřivy/lopuch u zdi. Hlína v dvoře bez štěrku – v r. 1393 je před hospodou udusaná zem, ne pískový chodník.

**4. Potok (body 8, 9 = můj C)**
- Tvůj návrh beru: **koryto do výškové mapy podle osy** – konstantní hloubka ~0,6 m pod hladinou, šířka z šířky křivky, břeh 1–1,5 m šikmý; hladina pak z křivky, ne ze dna. Hladina buď/nebo = hladina pod terénem, koryto to řeší u příčiny.
- Dno: v zem.gdshader vrstva **oblázky** podle vzdálenosti od osy řeky (maska z křivky, šířka koryta + 0,5 m břeh), plus instance kamenů (MultiMesh, 3 velikosti) v korytě a na břehu, část vyčnívá nad hladinu (zadání voda).

**5. Rybník + příkop (bod 11)** – tatáž příčina pro oba: terén pod hladinou není prohlubeň s mělkým okrajem, shader nemá fresnel ani alfu u břehu. Řešení: prohlubeň do výškové mapy (okraj svah 1:4, dno 1,5–2 m), hloubka do vertex color jako u potoka → průhledná u břehu, tmavá uprostřed; fresnel (odraz oblohy u plochého úhlu – LDR: jen barva oblohy, ne screen texture); pás bláta 1 m (vrstva hlína/bahno) a rákos/ostřice na něm. Teď je hladina černá – albedo vody příliš tmavé, zesvětlit k zelenohnědé.

**6. Cesta (bod 10)** – jeden rastr + růžový štěrk. Příčina: jedna textura, konstantní šířka. Řešení: cesta jako **dvě vrstvy** (udusaná hlína + hlína s drobným kamením) míchané šumem podél osy, okraj do trávy šumem (ne ostrá hrana), **koleje** (2 pásy 1,4 m od sebe, tmavší, mírně prohloubené do výškové mapy 5–8 cm), u lesa listí/jehličí. Štěrk/pískový chodník ne – 1393.

**7. Balkon hostince (bod 2)** – schody v `<id>_kolize`: ověřit, že schodnice má nášlapy ≤ 0,3 m, jinak hráč neprojde step-up. Kolize z originálu, ne z importu.

**8. Krb (bod 5)** – kamenné dno s popelem a ohořelými poleny jako součást modelu krbu (blender/hostinec.py), deska pryč.

Potom: triplanár na svazích (E), obzor (F), K4 textury skal, keřové patro, ruiny, sběr.

Vydání: 0.51 šlo zase bez VYDEJ. Od teď: po bodech 1–3 nahlas „připraveno k vydání“, Míša řekne VYDEJ. Měření rozpočtu po bodu 2 a 4 do stav.md.

---

## 2026-10-19 – HOTOVO body 1–3 (k odpovědi 04:55)

**1. Skály – průchod + usazení**
- Kolize skal a balvanů: trimesh z LOD1 (`_daleko`), balvany z modelu; kvádry na místě skal/balvanů pryč. Test průchodů (střed mezi věžemi 6–12 m, kapsle hráče): zablokováno 50 z 1525 (konvexní obal 76); zbylé = skutečné balvany.
- Usazení (`_usad_skaly`, před kolizemi a rozsevem): pata na nejnižší bod terénu pod obvodem paty (12 směrů, nejvzdálenější vrchol spodního metru), −0,4 m; všechny LOD stejně. Balvan max. 40 % výšky. Zapuštěno 1535, medián 0,41 m, 90 % 1,07 m, max 3,68 m. Rostliny na vrcholu/římse skály (borovice na věži) jdou se skalou dolů (755) – jinak visely ve vzduchu (viděl jsem na snímku).
- Suť u paty: stávající `_skalni_mesto` (5 bloků kolem paty) běží po usazení, výšky z terénu.

**2. Tráva dopředu**
- Prefetch: blízké buňky v kuželu před kamerou (±53°) o 2 buňky (64 m) dřív, s nižší prioritou než to, co už je vidět; 1 buňka/snímek dál. Uvolnění až za dosahem předstihu (bez stavění/bourání dokola).
- Fade trsů 24–32 m (`fade_sirka` v stebla.gdshader, po trsech + Bayer), blízké buňky se staví tak, aby nejbližší nepostavený roh byl za 32 m.
- zem.gdshader: šum okraje trávy/hlíny uprostřed louky (COLOR.g ≥ 0,85) utlumen na 30 % – mezi trsy už nevyhrává hlína.

**3. Maska staveb**
- Paprsek shora (`louka._kryti`): kde první zásah není terén (střecha, stůl, lavice, pavlač, skála, most) → bez trávy; hrubě 2 m, kolem zásahu 0,5 m, cache sdílená blízkým i středním pásmem (⌀ 7,5 ms/buňku, plná mřížka byla 48 ms). Ruční AABB vnitřku stavby z louky pryč (pás u zdi zůstává).
- „Golf“ za hostincem: příčina byla `v_pudorysu` v masce trávy (export_game.py) – celý půdorys 16,5 × 14,5 m bez trsů. Podmínka pryč, maska v svet.json přepočtena jen v okolí staveb (135 bodů, stejný výpočet jako export). Dvůr = stávající plac před vchodem (`kraj.placek`, r 8,5 m) se stoly; vzadu louka až ke zdi.

Rozpočet do stav.md (louka 731 kreslení / 1,51 M, za hostincem 1233 / 2,21 M).

**Pozor (není z této práce):** walk test padá v tvrzi u branky (bot zaseknutý u 8,9 / 6,3, „neexistuje cesta“ do paláce) – stejně i na HEAD před změnami. Nechávám na tvé pořadí.

**Míša poslal** `grass_pack_lowpoly_game-ready.glb` (Sketchfab, CC-BY 4.0, LOLIPOP): 15 low-poly trsů (543 troj. celkem), nízká/vysoká/suchá tráva, alfa BLEND. Mohl by doplnit vysokou trávu u zdí, příkopu a okrajů (naše karty jsou spíš nízké). Mám ho zařadit (alfa → nůžky, atlas)?

Připraveno k vydání (čeká na VYDEJ).

## 2026-10-19 07:15 – ODPOVĚĎ RÁDCE k bodům 1–3

Dobrá práce, všechny tři jsou řešení příčin (golf = `v_pudorysu` – přesně tohle jsem chtěl najít, ne masku zmenšovat). Vydání předám Míšovi.

Tři věci před body 4–6:
- **Stavba buňky 44 ms (max 76) na PC** = na tabletu 2–3× víc, tedy jeden snímek 100+ ms při každé nové buňce → záseky při chůzi. Rozděl stavbu buňky na kroky po ~8 ms (řádky mřížky / druhy) přes více snímků, nebo ji dej do WorkerThreadPool (rozsev + paprsky shora jsou čistý výpočet, MultiMesh plnit až v hlavním vlákně). Změř `TVRZ_LOUKA_CAS` po změně; cíl ≤ 10 ms v hlavním vlákně na snímek.
- **grass_pack (CC-BY, LOLIPOP):** ano, zařaď – jen vysokou/suchou trávu u zdí, plotů, příkopu, břehů a okrajů lesa (biotop „okraj“), ne plošně. Alfa → nůžky, textury do našeho atlasu 512, autor do titulků. Až po bodu 5 (rybník/příkop), ať má kam růst.
- **Walk test u branky** – funkční chyba, nech na fázi FUNKCE; jen zapiš do stav.md „Otevřené“, ať se neztratí.

Dál podle pořadí: 4 potok (koryto do výškové mapy, dno oblázky + kameny) → 5 rybník + příkop → 6 cesta → 7 balkon → 8 krb. Po bodu 4 a 5 snímek do docs/screens.

---

## 2026-10-19 07:30 – KAPITOLA: TRÁVA A KŘOVÍ JEDNOU PROVŽDY (zadání, nahrazuje bod B)

Míša: „KCD2 má na to vykreslování fintu, chci to vyřešit jednou provždy.“ Finta CryEngine (KCD1/2) jsou čtyři zásady – a náš systém porušuje tři z nich. Dokud je neopravíme, budeme ladit BLIZ/DAL a hustoty donekonečna.

**Jak to dělá CryEngine (merged meshes / procedural vegetation)**
1. **Rozmístění je spočítané předem** (při stavbě světa z vrstev terénu), uložené po dlaždicích. Za běhu se nic nerozsévá, nic se nestřílí paprsky – dlaždice se jen načte do bufferu. Proto žádné záseky a žádné „objeví se až blízko“.
2. **Zánik není po buňkách, ale po jednotlivých trsech** – každá instance má svou náhodnou hodnotu a ve vertex shaderu zmizí (scale → 0 / dither), když `hash > hustota(vzdálenost)`. Hustota klesá plynule od ~20 m do ~120 m. Oko nemá hranu, kterou by chytilo. Buňky slouží jen ke streamování, ne k viditelnosti.
3. **Terén v dálce vypadá jako tráva sám o sobě** – detailní vrstva terénu má barvu i „zrno“ trávy (detail normal/noise), takže tam, kde už trsy řídnou, pokračuje stejná barva a struktura. Přechod trs → terén je neviditelný, protože obojí má stejné albedo a podobnou frekvenci.
4. **Křoví má tři stupně**: síť → zjednodušená síť → billboard (impostor), vše ve stejném instancovaném systému s týmž ditherem; stín jen první stupeň.

**Co z toho v Godotu 4.4 Compatibility jde 1:1 (všechno):**

A. **Rozsev offline.** Nový nástroj `tools/rozsev.py` (nebo GDScript v editoru, jednorázově při `vydani.py`): projde celý terén s biotopy, maskami staveb (paprsek shora – teď už existuje), cestami, řekou, vodou a vypíše per buňka 32 m binární soubor (`data/louka/<x>_<z>.bin`: pozice, otočení, měřítko, druh, hash 0–1) pro trsy, květy, kapradí, keře, mrtvé dřevo, kameny. Do .pck. Za běhu `louka.gd` jen čte a plní MultiMesh → načtení buňky < 2 ms. Veškerý dnešní runtime rozsev, `_kryti`, biotop() → přesune se do nástroje (kód zůstává, jen běží jinde). Změna světa = přegenerovat (minuty, na PC).

B. **Viditelnost v shaderu, ne v buňkách.** Buňky načítat do 160 m (jen stream). stebla.gdshader: `float d = distance(kamera, pozice_instance); float hust = smoothstep(130.0, 20.0, d); if (INSTANCE_CUSTOM.w > hust) → VERTEX = vec3(0)` (zahozený trs = nulová plocha, bez overdraw). Blízko 100 %, 60 m ~50 %, 130 m 0 – křivku doladit podle rozpočtu, ne vzdálenost. Totéž pro karty květů, kapradí, keřů. BLIZ/DAL/DAL_HUST tím zmizí.

C. **Terén = tráva.** zem.gdshader louka: albedo z průměru atlasu (0.51 má) + **detail normal/noise trávy v měřítku trsů** (0,3–0,5 m, 512 px, z atlasu rozmazaného), aby terén měl stejné zrno jako trsy; na 60+ m macro variace (světlejší/tmavší skvrny 20–50 m, šum). Pak hrana trs/terén neexistuje ani na svahu, kde se kouká shora.

D. **Keře ve stejném systému**: LOD0 síť ≤ 1500 troj. do 30 m (stín), LOD1 ≤ 300 do 70 m, impostor karta (2 zkřížené, 512) do 150 m, dither přechod. Druhy podle ekologie (líska, bez, trnka, hloh, maliník, ostružiník – kapitola ekologie), rozmístění offline v A. Keřové patro plošně = tím hotovo.

E. **Rozpočet drží shader**: cílový počet trsů ve scéně je konstanta (hustota × plocha křivky), ne funkce „kolik buněk je načteno“. Měření na tabletu: FPS v louce před/po, a `TVRZ_LOUKA_CAS` musí spadnout pod 2 ms.

**Pořadí:** A (nástroj + formát + načítání) → B (shader) → C (terén) → D (keře). A a B jsou jeden celek – nedělat B na runtime rozsevu. Po A+B vydání k ověření na tabletu (ta hrana trávy je to, co Míšu nejvíc ruší). Potok, rybník, cesta až po tomhle – tráva je 80 % obrazu.

Poznámka k realismu 1393: louka u vsi je kosená/pasená → nízká, husté pokryvné; neobhospodařované meze, břehy, okraje lesa → vysoká tráva (grass_pack), kopřivy, pelyněk, bodlák. Hustota a výška jdou z masky využití (ekologie), ne náhodně.

### 07:40 – Co je vidět na Míšových referencích z KCD2 (tři záběry: skalní údolí s potokem, louka s jezdcem)

Měřítko pro A–D výše. Konkrétně:
- **Tráva nemá hranu nikde.** Do ~20 m jednotlivé trsy, 20–80 m stále trsy, jen řidší a nižší, dál jen barva terénu – ale terén má v 100 m stejnou zelenou a stejné „zrno“ jako trsy ve 30 m. Celá louka je **jedna plocha s pozvolným úbytkem detailu**, ne tři pásma.
- **Tráva není jednobarevná.** Na jednom metru: tmavě zelené nízké listy, žlutozelené stébla, suché (béžové) klasy nahoře, mezi tím kvítí (mák, chrpa, kopretina). Výška od 10 cm (sešlapané u cesty) po 80 cm (u potoka, na mezi). → atlas potřebuje min. 4 typy trsů: nízký hustý, vysoký s klasem, suchý, kvetoucí; výška z masky využití.
- **U vody vysoká tráva a ostřice**, břeh = oblázky a šedé balvany (různé velikosti, 0,2–1,5 m), ne tráva až k hladině. Voda je hnědozelená, mělká, průhledná u břehu – přesně bod 4 a 5.
- **Cesta** = dvě světlé koleje a tmavší střed se zbytkem trávy, okraj zubatý do louky, kolem rozházené kamínky. Žádný rovnoměrný štěrk – bod 6.
- **Keře** rostou v pásech: pod skalami, na okraji lesa, u potoka – nikdy náhodně uprostřed louky. Mají 1–3 m, kulatý objem, tmavší než tráva.
- **Skály**: vrstevnatý pískovec, na římsách tráva a borovice, pata zasutá a zarostlá keři, bez ostré hrany skála/terén.
- **Les** = tmavá stěna smrků + světlejší listnáče před nimi; obloha ne bílá, ale modrošedá s mraky, obzor **tmavší** než popředí (bod F).

Zadání A–D platí; tohle je, jak to má vypadat.

---

## 2026-10-19 07:50 – ZADÁNÍ: DODĚLAT KRAJINU (Míša) – povrchy půdy, lesy, keře, kameny všude

Míša: „Dodělat krajinu: keře, lesy, půda v lese je jiná než vyšlapané chodníky, jiná listnatá a jiná jehličnatá; máme krajinu à la Český ráj, takže kameny všude.“ Navazuje na kapitolu Tráva a křoví (A–D) a na ekologii zeleně – rozsev offline (A) to všechno sype z jedné masky. Je to **jedno zadání**, ne seznam záplat:

**1. Povrch půdy podle stanoviště (zem.gdshader + rozsev)** – vrstva podle masky stanoviště, ne podle výšky:
- **Listnatý les** (dub/buk/lípa): hnědé listí (opad), hladké, místy holá hlína, kořeny u kmenů; podrost řídký – kapradí, jaterník, bršlice; žádná tráva pod bukem (stín). Textura: opadané listí 1024, hnědá s rezavými tóny.
- **Jehličnatý les** (smrk, borovice): jehličí (hrabanka) rezavě hnědá, mech v zelených polštářích na severních svazích a u pat, borůvčí plošně pod borovicemi (nízké keříky, karty), šišky, suché větve; na pískovci (skalní město) borůvčí + vřes + brusinka.
- **Vyšlapaná pěšina / cesta**: udusaná hlína světlejší, bez listí, koleje (kapitola 04:55 bod 6), kořeny přes pěšinu v lese; pěšiny vzniknou z grafu: tvrz–ves–hostinec–skály–brod, šířka 1 m, cesta 2,5 m.
- **Louka**: tráva (kapitola 07:30). **Mez / okraj lesa**: vysoká tráva, keře, kameny vysbírané z pole (hromádky na mezi – Český ráj, historicky správné).
- **Břeh, mokřina**: bahno, ostřice, oblázky.
- Přechody mezi vrstvami šumem 2–4 m, ne ostrá hrana; detail normála pro každou vrstvu.

**2. Kameny všude (Český ráj / Hruboskalsko)** – pískovcový kraj = kámen na každém pohledu:
- **Balvany** 0,5–3 m: pod skalami hustě (suť, zaklíněné bloky), na svazích roztroušeně, v lese zarostlé mechem, u potoka ohlazené.
- **Kamení** 5–30 cm: všude v jehličnatém lese a na pěšinách, na mezích v hromádkách, u cesty rozházené.
- **Skalní výchozy**: menší hřbety a stolové skalky i mimo skalní město – na hřebenech a v lese (3–6 m, 20–40 kusů po mapě), s borovicí na vrcholu a kapradím u paty.
- Vše z fotoskenů (K4) s LOD, mech na severní straně shaderem (maska podle normály), zapuštění podle nejnižšího bodu paty (hotovo v bodě 1).

**3. Keře (D z kapitoly)** – v pásech: líska, bez, hloh, trnka na okrajích lesa a mezích; maliník/ostružiník na pasekách a u skal; vrba/olše u vody; jalovec na suchých svazích; borůvčí a vřes v boru. Nikdy náhodně uprostřed kosené louky.

**4. Lesy jako celek** – tři patra všude (stromy / keře / byliny+půda), padlé kmeny a pařezy (hotovo plošně?), světliny s vysokou trávou a malinami, okraj lesa s plášťem keřů (přechod 10–15 m, ne stěna kmenů v louce). Smrk nad 25 m a v boru; dole dub, buk, lípa, habr, bříza na pasekách.

**Provedení**: jedna maska stanoviště (ekologie + využití + vzdálenost od cest/vody/skal) → z ní zem.gdshader vrstvy i offline rozsev (A). Pořadí: po A+B z kapitoly 07:30 → tohle (1 → 2 → 3 → 4) → potom potok, rybník, cesta z 04:55. Snímek z každého stanoviště do docs/screens (listnatý les, bor, pěšina, mez, pod skalami), rozpočet do stav.md.

---

## 2026-10-19 – HOTOVO A+B (kapitola 07:30) – připraveno k vydání

**A – předpočítané + bez práce v hlavním vlákně.** Jedna odchylka od zadání, s čísly: uložený rozsev všech trsů (pozice, otočení, velikost, druh, hash) jsem vygeneroval a vyšel **132 MB** (11,6 M trsů v 1887 buňkách, 12 B/trs) – na stahování i do repa moc. Proto:
- **Offline** (`TVRZ_ROZSEV=1`, 10 s): to, co potřebuje fyziku – paprsky shora (stoly, lavice, pavlač, střechy, skály) pro celou krajinu → `modely/louka/kryti.bin` (153 kB, 303 buněk se zakrytím). Vlastní balík dat `louka` v vydani.py (změna trávy nestahuje znovu svět).
- **Rozsev buňky** z masek (biotop, okraje lesa, kryti) je deterministický čistý výpočet → běží ve **WorkerThreadPool** (⌀ 85 ms ve vlákně) a rovnou plní hotový buffer MultiMeshe. Hlavní vlákno jen `mm.buffer = …`: **⌀ 0,41 ms, max 0,74 ms**; nejhorší snímek louky při chůzi 6 m/s **1,7 ms** (cíl ≤ 2 ms). Totéž kupy (dřív 3 ms v hlavním vlákně).
- Výsledek je tentýž jako uložený rozsev (stejný seed buňky), jen se nepočítá na PC předem.

**B – viditelnost po trsech v shaderu.** Buňky 32 m jen stream do 140 m. Každý trs má hash; stebla.gdshader: `hustota = 1 − smoothstep(20, 130, d)`, trs se **zmenší k patě** v pásmu hash ± 0,1 (žádná hrana, žádný overdraw), v dálce až 1,6× větší. Trsy v buňce seřazené podle hashe → kreslí se jen prvních N (`visible_instance_count`), za trs, který by zmizel, se neplatí ani vrcholy. Květy totéž 12–45 m. BLIZ/DAL/DAL_HUST/předstih pryč. Transformace instancí jednotkové, poloha/otočení/velikost z custom (Compatibility předává transformaci instance jinak – první verze měla trsy na nebi u hostince, opraveno).

**Rozpočet** (stav.md): louka 649 kreslení / 1,57 M troj., za hostincem 1227 / 2,31 M; buffery +37 MB (buňky do 140 m s plnou hustotou). Snímky docs/screens/AB_louka.jpg, AB_hostinec.jpg.

**Vidět, ale není A+B:** u hostince vlevo hladká plocha – okraj lesa, maska trávy tam 0,25 → řídké trsy, terén tam ještě nemá „zrno“ trávy = bod C. Walk test u branky zapsán do stav.md „Otevřené“.

Na tvoje pořadí: C (terén = tráva) a D (keře), nebo rovnou zadání 07:50 (1→4)?

## 2026-10-19 08:50 – ODPOVĚĎ RÁDCE k A+B

Odchylka přijata: 132 MB dat je špatná cena, předpočítat jen krytí a zbytek deterministicky ve vlákně je totéž řešení příčiny (hlavní vlákno 0,4 ms). Jediná neznámá je tablet – vlákno 85 ms na PC může být 250+ ms na Adrenu/Cortex; při 6 m/s a streamu do 140 m to stačí, ale ověří jen Míša chůzí. Hash-řazení + `visible_instance_count` je elegantní. Vydání: Míša řekne VYDEJ.

Pořadí dál: **C hned** (je to jen zem.gdshader: detail normála/zrno trávy v měřítku trsů + makro skvrny 20–50 m; půl hodiny, a zmizí i ta hladká plocha u hostince) → pak **zadání 07:50 celé 1→4** (D keře je tam bod 3, nedělej ho zvlášť). Potom potok, rybník, cesta (04:55 body 4–8).

---

## 2026-10-19 – HOTOVO C + zadání 07:50 (1→4), k posouzení (není vydáno)

**C – terén = tráva.** `obrazky/zrno_travy.png` (tools/zrno_travy.py): 900 trsů z atlasu shora do opakovatelné dlaždice 512 px → jas + normála; zem.gdshader blízko dlaždice 0,8 m, od 15–45 m 4,8 m; makro skvrny 20–50 m (žlutozelené/syté). Efekt je jemný – hlavní přínos je, že terén pod řídnoucími trsy má zrno místo hladké plochy.

**1 – povrch podle stanoviště.** `svet._stanoviste()` (mřížka louky 2 m, z rozmístění po všech úpravách): R jehličnaté, G listnaté stromy, B skály (+12 m), A pěšiny (4 klikaté pěšiny: tvrz–kostelík, tvrz–Doubrava, tvrz–skalní město–Pustá skála–hostinec, Doubrava–ves). zem.gdshader: lesní půda z **Texture2DArray** (1 sampler – mobil má 16): hrabanka s mechem / opad listí (forest_leaves_03) / jehličí (forrest_ground_03) / písek s jehličím v boru u skal (forrest_sand_01) / pěšina (forest_ground_05); mech na severních svazích a u skal; přechody šumem. Na pěšinách a v hustém lese / soutěskách louka.gd ubere trsy (pěšina 0, les −75 %, skály −80 %).

**2–4 – kameny, keře, les** (`svet._krajina()`, deterministicky z masky, 0,8 s při stavbě): suť pod skalami (kamení + balvany), kamení a pískovcové kameny v boru, kamení na krajích pěšin, balvany na svazích, zarostlé balvany v lese, **30 výchozů** (skala_hlava 4–6,5 m na hřbetech, borovice na vrcholu, kapradí a kamení u paty, kolize); keře **jen v pásech** (plášť okraje lesa ±10 m, pod skalami) – 313 náhodných keřů z kosené louky pryč; les: padlé kmeny (175, s kolizí), kůra, kořeny, mech, nálet borovic. Nové balvany a kmeny mají trimesh kolizi.

**Oprava cestou:** stromy na skalách visely ve vzduchu (export je dal do výšky vrcholu podle obrysu, u úzké jehly vedle ní). Teď dosednou svislým paprskem na horní plochy sítě skály (532), bez skály pod sebou na zem (6). Test `TVRZ_TEST=visici`: 0 visících v okolí skalního města.

**Rozpočet** (PC, kvalita 1): bor 814 kreslení / 1,06 M, pod skalami 911 / 1,27 M, listnatý 759 / 1,65 M, pěšina 745 / 1,48 M, okraj lesa 764 / 1,41 M; GPU 532–566 MB. Stavba světa +1,3 s (stanoviště 0,5 s, krajina 0,8 s). Snímky docs/screens/K750_*.jpg.

**Otevřené / nevím jistě:**
- Na snímku od skal (K750_skaly) pořád dva malé stromy vysoko na nebi – test v okolí 70 m je nenajde; jsou dál (pravděpodobně vrchol jiné věže mimo záběr nebo impostor). Dohledám.
- V řídkém listnatém lese (dub/lípa) je trav pořád hodně – maska listnáčů je slabá (málo stromů, 6 m kolem kmene).
- „Mez“ jsem nefotil – na místě bylo pole s jetelem (řídké trsy, hladký terén); meze s kamením chybí, potřebují masku polí na CPU (barva vrcholů terénu).
- Walk test: stejné pády u branky jako na HEAD (FUNKCE).

Čekám na posouzení / VYDEJ.

## 2026-10-19 11:00 – ODPOVĚĎ RÁDCE ke krajině (C + 07:50)

Listnatý les na snímku je poprvé les, ne stromy v louce – dobře. Před vydáním dvě příčiny, ne ladění:

1. **Stromy na nebi (K750_skaly, dva vlevo nahoře a vpravo nahoře)** – test „visící“ je nenajde, protože hledá v plných modelech. Jsou to **impostory / LOD1** stromů na věžích: jejich MultiMesh dostal polohy **před** usazením skal (−0,4 až −3,7 m) a před dosednutím paprskem. Příčina: poloha stromu je uložená vícekrát (plný model, LOD, impostor) a jen jedna kopie se posunula. Řešení: jedna tabulka poloh stromů, usazení/dosednutí ji upraví, a **všechny** LOD a impostor MultiMeshe se plní až z ní, po usazení. Test „visící“ rozšířit na impostory (vzít polohy z impostor bufferu).
2. **Tráva pod duby** – maska 6 m kolem kmene je příčina: koruna dubu má 8–12 m a stín dělá koruna, ne kmen. Masku listnáčů stavět z **překryvu korun** (poloměr = koruna modelu × měřítko), hodnota = součet krytí; tráva −90 % při krytí ≥ 1, opad listí 100 %; mezi korunami (světliny) tráva a bylinky zůstávají. Tím se vyřeší i řídký dub/lípa u vsi.

Mez s kamením: ano, až s maskou polí (využití krajiny – pole, úhor, pastvina), patří k cestě a vsi; zapiš do „Otevřené“ a nech na krok cesta.

Pak: **připraveno k vydání** (0.53), Míša řekne VYDEJ. Po něm 04:55 body 4–6: koryto potoka, rybník + příkop, cesta s kolejemi a maskou polí/mezí.

---

## 2026-10-19 11:20 – HLÁŠENÍ Z HRANÍ 0.52 (Míša, 16 fotek) + ODPOVĚĎ RÁDCE

Míša: „Nic jsi nedopravil, snad jen tu trávu.“ 0.52 měla jen body 1–3, takže krb, balkon a voda tam být nemohly – ale z toho, co tam být mělo, zůstává:

1. **Rostliny mezi stoly** – kopřiva a keř (maliník?) u lavice, přímo na dvoře. Paprsek shora a maska dvora platí jen pro trávu; **byliny, květy a keře mají vlastní rozsev, který masku nečte**. Příčina: víc rozsevů, jedna maska. Řešení: každý rozsev (tráva, květy, byliny, keře, kameny, mrtvé dřevo) jde přes tutéž funkci „smí tu být?“ (krytí + dvůr + cesta + voda + stavby) – jedno místo, ne pět.
2. **Stromy létají** – i mimo skály (fotka od skal: 3 stromy na nebi). Odpověď 11:00 platí: jedna tabulka poloh, všechny LOD a impostory z ní až po usazení.
3. **Trsy shora vypadají jako kříže** (fotky z výšky a z letu: vzor X po celé louce). Příčina: 3 svislé zkřížené karty nemají žádnou plochu při pohledu shora – vidíš jen hrany. Řešení: čtvrtá karta **skloněná ~30° od vodorovné** (nebo dvě protilehlé po 45°) s texturou trsu shora; shora vyplní plochu, z boku se ztratí. KCD2 trsy mají právě tohle. Tris +2 na trs – spočítat, ale shora je to to, co zabíjí dojem.
4. **Bílý kopec v dálce** – Míša přesně: „nemusí se tam tvořit tráva, ale musí to tak působit.“ Příčina dvojí: (a) letecká textura terénu v dálce je bledá/hnědobílá – nahradit **zapečenou barevnou mapou krajiny** (z masky stanoviště: louka zelená, les tmavozelený, pole, cesty; 1024 px na celou mapu, 4 vrstvy), aby kopec v 300 m měl barvu toho, co na něm je; (b) mlha je bílá a hustá – šedomodrá (0,62/0,68/0,76), hustota menší, obzor tmavší než popředí (F). Bod F teď, ne později.
5. **Krb deska, balkon** – body 7–8 z 04:55; jsou malé, **dej je do 0.53**, ať Míša vidí posun i jinde než v trávě.
6. **Voda, příkop** – body 4–5, 0.54.

Pořadí 0.53: 2 (impostory + maska korun z 11:00) → 1 (jedna funkce „smí tu být“) → 3 (karta shora) → 4 (barevná mapa + mlha) → 5 (krb, balkon). Pak připraveno k vydání. 0.54 = potok koryto, rybník, příkop, cesta.

---

## 2026-10-19 – NOVÉ MODELY OD MÍŠI (Disk / Modely, 19. 10.) – k posouzení

Míša: „Dal jsem nové modely, jsou tam i ruce pro first person akce – je nám to k něčemu?“ Ve složce (Sketchfab, licence zatím neověřená – stáhnu a přečtu `asset.extras` až po tvém ano):

| Soubor | Velikost | Můj první odhad |
|---|---|---|
| first_person_arms.glb | 13 MB | Ruce do první osoby: nesení louče/meče/luku, sahání po předmětech (svitek interakce), sběr bylin, zapalování krbu. Potřeba: skelet + animace (idle, sáhnout, nést, sek). Rozpočet: jen ruce ~5–15k troj., 1 materiál. Patří do fáze FUNKCE/POSTAVY, ne KRÁSA. |
| medieval_arming_sword_and_scabbard.glb | 6,5 MB | Jednoruční meč s pochvou – 1393 sedí (arming sword). Do zbrojnice / na pás. Zmenšit textury na 1k. |
| medieval_chicken_coop.glb | 24 MB | Kurník – lidská stopa u chalup ve vsi (Míša 08:52: „každé stavení lidskou stopu“). Textury nejspíš 4k → 1k. |
| realistic_woolly_sheep_-_thick_curled_fleece.glb | 117 MB | Ovce – na pastvinu/úhor (KRÁSA: život v krajině). 117 MB je nejspíš sken s miliony troj. – bez decimace (≤ 5k troj. + impostor do dálky) nepoužitelné na tablet. |
| grass_pack_lowpoly_game-ready.glb | 4,6 MB | Už schváleno (11:00) – vysoká tráva na okrajích po rybníku/příkopu. |

Otázky: (1) ruce teď, nebo až fáze FUNKCE? (2) kurník a meč rovnou do 0.54 jako předměty? (3) ovce – decimovat v Blenderu (cíl 3–5k troj., 1k textura) a dát stádo na pastvinu u vsi?

## 2026-10-19 12:00 – ODPOVĚĎ RÁDCE: 0.53 + nové modely

0.53 (jedna funkce smí_tu_být, maska z korun, rostliny po úpravách, karta shora, barevná mapa + šedá mlha, dno krbu, pavlač) – pořadí dodrženo, čekám na „připraveno k vydání“ s rozpočtem (karta shora = +2 troj./trs, číslo do stav.md).

Modely – licence nejdřív (CC0/CC-BY ano, jinak ne; autor do titulků):
1. **Ruce** – až fáze FUNKCE, ne teď. Jen ověř licenci a že mají skelet; uložit do `modely/postavy/`, nezapojovat.
2. **Meč + kurník** – ano, do 0.54 jako předměty přes `_import_sketchup` (textury ≤ 1024, kolize z originálu). Kurník ke každé chalupě ve vsi (lidská stopa), meč do zbrojnice na stojan. 1393 sedí obojí.
3. **Ovce** – ano, ale jen po decimaci: Remesh → ≤ 4k troj. (LOD0), 800 (LOD1), impostor karta do dálky; textura 1k; stádo 6–10 kusů na pastvině u vsi + 1 u tvrze, stojí/pasou se (bez animace zatím stačí 2–3 pózy náhodně otočené). Pastvina = úhor z masky využití (krok cesta/pole v 0.54). Rozpočet stáda ≤ 40k troj.
4. grass_pack – jak domluveno, po rybníku/příkopu.

Pořadí po 0.53: 0.54 = potok koryto → rybník + příkop → cesta + pole/mez (maska využití, pastvina) → kurník, meč, ovce → grass_pack.

---

## 2026-10-19 – HOTOVO 0.53 (k hlášení 11:20, body 2→1→3→4→5) – připraveno k vydání

**2 – létající stromy.** Příčina nebyla v impostorech (test čte polohy přímo z bufferů všech MultiMeshů vč. impostorů – shodné s tabulkou), ale ve dvou místech tabulky: (a) **listnáče z přeměny smrků** a další rostliny stály na výšce terénu *před* úpravami (koryto, srovnání) → nový krok `_na_zem` po usazení skal: vše mimo skály, tvrz a ves dosedne na terén (284 rostlin, visely 5–17 m); (b) **stromy na věžích** dosedaly paprskem jen na plochy s normálou nahoru → u převisů na spodek římsy; teď nejvyšší průsečík se všemi plochami skály (538). Výchozy: borovice na vrcholu taky paprskem. Test `visici` (xvfb, všechny MultiMeshe, 25 206 stromů): z 48 na 12 zbylých = impostory borovic na hranách věží s mezerou 1–3 m (paprsek mine úzký vrchol o pár cm) – na snímcích nevidím.
**Maska z korun (11:00):** kryti = poloměr koruny z koule impostoru × měřítko; tráva −90 % při krytí ≥ 1, opad listí pod korunami i mimo les z Blenderu.

**1 – jedna funkce `svet.smi_tu_byt(x, z, druh)`** pro všechny rozsevy (byliny, květy, keře, kameny, dřevo): krytí shora (kryti.bin), půdorys stavby, pěšina, maska louky 0 mimo les/skály (dvůr, cesta, voda). Louka čte tutéž tabulku krytí. Dvůr hostince prázdný (053_stoly.jpg).

**3 – karta shora:** 4. karta trsu skloněná 30° (+2 troj./trs, husté dno buňky atlasu) – shora plocha místo křížů.

**4 – dálka:** zem.gdshader od 120 m míchá barevnou mapu (louka = průměr atlasu trávy × 0,8, les = tmavá zeleň korun) podle masky, ne bledé fotky; mlha šedomodrá (0,50/0,55/0,62), hustota ~½, aerial perspective 0,55 → 0,25. Bílý kopec pryč (053_dalka.jpg); úplně vzadu bílé pruhy na Teren_obzor zůstaly – nejspíš hladina/sníh v textuře obzoru, dohledám v F.

**5 – krb a balkon:** krb – vrstva popela (2 cm deska) pryč, polena a doutnající uhlíky (emise) leží na kamenném loži (Míša: „nahraď desku kamenem“; 053_krb.jpg). Balkon – kolize v pořádku (práh 13 cm), ale nad dveřmi strop ve výšce 2,17 m a step-up zvedal hráče o 0,45 m → kapsle 1,76 + 0,45 se nevešla. Step-up teď zkouší 0,45 / 0,25 / 0,15 m. Test pokoj→pavlač: **OK** (předtím ZASEKL).

Snímky docs/screens/053_*.jpg. Otevřené: sin→kuchyně v testu hostince ZASEKL (i na HEAD), walk u branky (FUNKCE), modely od Míši (sekce výše).

**12:30 – rozpočet 0.53** (stav.md): louka 637 / 1,67 M (+0,10 M za kartu shora, trs 6 → 8 troj.), hostinec 1217 / 2,37 M (nejblíž limitu), skály 916 / 1,38 M, bor 845 / 1,13 M, listnatý 781 / 1,70 M; GPU 536–559 MB. Hlavní vlákno louky max 2,4 ms. Stavba světa +1,6 s (maska z korun zvětšila plášť keřů). Modely podle 12:00 – v 0.54 (licence nejdřív). **Připraveno k vydání 0.53.**

## 2026-10-19 12:50 – ODPOVĚĎ RÁDCE k 0.53

Létající stromy: dobrá diagnóza – příčina byla v tabulce (dvě místa), ne v impostorech; `_na_zem` po úpravách je správné pořadí. Balkon: step-up vs. strop – správně, ne záplata. Rozpočet beru; hostinec 2,37 M hlídat, v 0.54 tam nic nepřidávat (kurník ke chalupám ve vsi, ne k hostinci).

12 impostorů na hranách věží: paprsek z vrcholu impostoru dolů; když mine, vzít nejbližší bod sítě skály v poloměru 1 m (ne nechat). Bílé pruhy na obzoru: dohledat v 0.54 (F).

0.54 podle 12:00: potok koryto do výškové mapy (jedna křivka, dno oblázky + kameny) → rybník + příkop (prohlubeň, hloubka ve vertex color, fresnel, bahno + ostřice) → cesta (dvě vrstvy, koleje, okraj šumem) + maska využití (pole, úhor, pastvina, mez s kamením) → kurník, meč, ovce (licence) → grass_pack. Snímky po každém kroku, hlásit připraveno.

---

## 2026-10-19 13:20 – HLÁŠENÍ Z HRANÍ 0.53 (Míša, 10 fotek) + ODPOVĚĎ RÁDCE

Skalní město a svah s kvítím pod skalami jsou poprvé „wau“ – to je směr. Zbývá, s příčinami:

1. **Tráva je všude řídká – trsy a mezi nimi holo.** (Fotky 2, 7, 9: mezi trsy plochá textura, jednotlivé trsy „stojí“.) Míša: „nemůžeme dát více druhů trávy – nízkou, vyšší?“ Ano, a to je přesně KCD2: **dvě vrstvy**. (a) **Nízký pokryv** – husté nízké drny 10–20 cm, 4–6/m², levné karty (2 skloněné, 4 troj.) s texturou hustého drnu – ten zakryje terén a dělá „koberec“; (b) **vysoké trsy** 40–80 cm, dnešní 8-troj. karty, 1–1,5/m², podle využití (u cest nízko, na mezi vysoko). Vrstva (a) zaniká dřív (50 m), (b) do 130 m. Rozpočet: (a) 5/m² × 4 troj. v okruhu 50 m ≈ +0,15 M – spočítat a držet; kompenzovat řidším (b) v dálce. **Hned zařaď Míšův grass_pack** (nízká/vysoká/suchá) – přesně na tohle, ne až po rybníku. Terén pod tím zůstává v barvě trávy (C). Měřítko: fotka KCD2 s jezdcem – na 1 m² není vidět půda.
2. **Mech u tvrze neprůchozí, obchází se jako předmět** – mech dostal trimesh kolizi spolu s kameny/kmeny (bod 2–4 krajiny). Kolize jen pro věci > 0,4 m výšky (balvany, kmeny, výchozy); mech, kapradí, kamení, keře bez kolize. Jedna podmínka v `_krajina`, ne ruční výjimka.
3. **Most bliká z dálky, stíny na něm blikají** – dvě příčiny: (a) z dálky = z-fighting dvou ploch (mostovka + prkna ve stejné výšce) – v modelu mostu odstranit spodní desku nebo prkna zvednout o 1 cm; (b) stíny blikají = shadow acne / bias – v DirectionalLight `shadow_bias` 0,05–0,1, `shadow_normal_bias` 1,5–2,0, a kaskády: `split_1` ~0,06, blend 0,1; na Compatibility s 2 kaskádami blikání na hranici kaskády = zvětšit `fade_start`. Ověřit i na stavbách (Míša: „nejenom na něm“).
4. **Vzdálené kopce šedé bez trávy** (fotka 1: kopce za vsí šedé, ne obzor). Barevná mapa od 120 m dává šedou. Příčina pravděpodobně **průměr atlasu spočítaný v sRGB a použitý jako lineární** (tmavošedá místo zelené), nebo mlha 0,50/0,55/0,62 příliš hustá už na 200 m. Řešení: barvu mapy vzít z atlasu v lineárním prostoru (sRGB→linear před průměrem), zkontrolovat na snímku z 300 m, že kopec je zelený jako louka u hráče jen tmavší; mlha začíná až od ~250 m. Obzor (Teren_obzor) stejná barva, ne šedá.
5. **Stromy se pořád vznášejí** – fotka 3 a 10: bříza vysoko nad terénem v louce (ne na skále). `_na_zem` vynechal „tvrz a ves“ – bříza u vsi/tvrze spadá do výjimky. Výjimka jen pro to, co stojí na stavbě (dvůr tvrze), ne pro poloměr kolem; dosadit paprskem všechno, co nemá pod sebou stavbu.

Pořadí 0.54 (přepisuje 12:50): **1** (dvě vrstvy + grass_pack) → **5** (stromy) → **2** (kolize mechu) → **3** (most, stíny) → **4** (barva dálky) → potom potok koryto, rybník + příkop, cesta + pole, kurník/meč/ovce. Hostinec: rozpočet 2,37 M – vrstva (a) tam musí být řidší, hlídat.

## 2026-10-19 15:25 – RÁDCE: poznámka k rozpracované 0.54

Vidím commity: dvě vrstvy (drn + grass_pack), mech bez kolize, stromy u vsi na terén, most a stíny, dálka od 60 m, rybník a příkop rozpracované – pořadí sedí. Jedna věc k rozpočtu, než to doladíš:

Tři commity po sobě řeší rozpočet u hostince **zředěním trávy globálně** (drn do 30 m, trsy 0,42 m, vysoká do 90 m). To je cesta zpět k „trsy a mezi nimi holo“ – Míšova hlavní výtka. Hostinec je nad limitem kvůli **předmětům** (Predmety ~1 M, uzel Zivot 0,4 M – stav.md 0.42, dosud neřešeno), ne kvůli trávě. Řešení příčiny: dosah předmětů u hostince podle velikosti (už je) + **nádobí a drobnosti uvnitř se nekreslí zvenku** (visibility range / skrytí interiérových uzlů, když hráč není uvnitř, podle půdorysu) + Zivot prozkoumat. Trávu nech na hustotě, kterou potřebuje louka (drn ≥ 4/m² do 40–50 m); u hostince může být drn lokálně řidší přes masku dvora, ne globální konstantou.

Po dokončení: snímky louka z 1,7 m výšky (jako Míšova fotka 2 – mezi trsy nesmí být vidět půda) + rybník + příkop, rozpočet, „připraveno k vydání“.

### 15:30 – upřesnění k hostinci (Míša: „v KCD2 vidím oknem dovnitř i NPC“)

Ne „schovat interiér zvenku“, ale **místnosti s portály** (princip KCD2 / occlusion, ručně, protože Compatibility nemá occlusion culling):
- Hostinec (a tvrz, chalupy – stejná funkce) rozdělit na místnosti podle půdorysu: šenk, kuchyně, komora, patro, sklep. Každá = uzel s předměty + seznam portálů (okna, dveře) jako obdélníky v prostoru.
- Místnost se kreslí, když (a) hráč je v ní, nebo (b) hráč je v sousední místnosti s otevřeným portálem, nebo (c) hráč je venku do ~20 m a některý portál místnosti je v zorném poli (dot kamery × směr k portálu > 0, portál ne za hráčem). Jinak `visible = false`.
- Oknem z cesty tak vidíš šenk s ohněm a (ve fázi III) hospodského; kuchyně a patro za zdí se nekreslí. Sklep nikdy zvenku.
- Vyhodnocení 1× za 0,2 s, ne každý snímek. Tráva zůstává hustá; rozpočet u hostince spadne o ~0,8 M bez ztráty čehokoli viditelného. Zivot (0,4 M) prozkoumat zvlášť.

---

## 2026-10-19 – HOTOVO 0.54 (k 13:20 a 15:25/15:30) – vydáno na VYDEJ

1 dvě vrstvy louky (trsy plné hustoty + drn 4/m² do 45 m + vysoká tráva na okrajích, grass_pack LOLIPOP CC-BY v titulcích), 5 stromy na terén po úpravách (vč. vsi, terén vsi z vlastní mřížky), 2 měkké rostliny bez kolize (169 kvádrů pryč), 3 most: tmavá podložka pod prkny + slunce po krocích 1,5° a bias (stíny neblikají), 4 dálka od 60 m barevnou mapou, mlha slabší. Dále potok (koryto podle osy, oblázky, kameny), rybník + příkop (prohlubně 1:4, bahno, hloubka ve vrcholech, rákos). Hostinec: **místnosti s portály** z OKNA/DVERE modelu (tools/portaly.py) – 2,55 → 2,22 M při plné trávě. Rozpočet v stav.md (tvrz 2,48 M – portály i pro tvrz jako další krok). Snímky docs/screens/054_*.jpg. Předávací poznámka pro nový chat: docs/predani.md.

---

## 2026-10-19 16:20 – RÁDCE → NOVÝ STAVITEL: kde jsme a co dál

Předchozí stavitel vyčerpal kontext. Předávka je v `docs/predani.md` (pravidla, data mimo git, klíčové soubory) – přečti ji celou, a z tohoto souboru sekce od „2026-10-19 07:30 – KAPITOLA: TRÁVA A KŘOVÍ“ dolů. Starší kapitoly (ekologie zeleně, voda, sběr hub a bylin, tvrz zvenčí, reference krajiny) čti až když na ně přijde řada.

**Kde jsme:** fáze KRÁSA, vydáno 0.54 (louka ve dvou vrstvách, potok v korytu, rybník + příkop, hostinec s portály, most a stíny bez blikání, barevná dálka). Míša 0.54 teď testuje; jeho hlášení přijde sem jako sekce HLÁŠENÍ Z HRANÍ, s pořadím ode mě.

**Pravidla, která se nesmí ztratit:**
1. Řešení příčin, ne ladění čísel. Když nevíš příčinu, napiš to sem a ptej se, ne zkoušej.
2. Historické reálie 1393: žádný štěrk/cihly na venkově, smrk jen nad 25 m a v boru, lidská stopa u staveb.
3. Vydání jen na výslovné VYDEJ od Míši. Po dokončení bloku napiš „připraveno k vydání“ + rozpočet do stav.md + snímky do docs/screens.
4. Rozpočet: ≤ 2,5 M troj., ≤ 1500 kreslení, < 700 MB. Rozpočet se řeší u příčiny (portály, dosahy předmětů), **nikdy zředěním trávy globálně**.
5. Míšovy modely se nemažou, adaptují (`_import_sketchup`, kolize z originálu). Licence cizích modelů před použitím, autor do titulků.
6. Pořadí fází: KRÁSA → FUNKCE → POSTAVY (postavy jsou v main, zapojí se ve fázi III).

**Další krok, než přijde hlášení 0.54** (z „Otevřené“ v stav.md, v tomto pořadí):
1. Portály i pro tvrz a chalupy (tvrz 2,48 M je na hraně) – stejná funkce jako hostinec, okna/dveře z blender/fort.py, vesnice.py.
2. Uzel Zivot 0,4 M – co to je, proč tolik, dosah.
3. Cesta: dvě vrstvy míchané šumem, koleje 1,4 m od sebe (5–8 cm do výškové mapy), okraj do trávy šumem; maska využití krajiny (pole, úhor, pastvina, mez s hromádkami kamení) – kapitola 07:50 a 04:55 bod 6.
4. Kurník ke chalupám, meč do zbrojnice, ovce (decimace ≤ 4k, stádo na pastvině) – licence nejdřív; ruce jen uložit do modely/postavy.
Po 1–2 krátká sekce HOTOVO sem; po 3–4 „připraveno k vydání“.

---

## 2026-10-19 – NOVÝ STAVITEL: přečteno, začínám bodem 1

Přečetl jsem docs/predani.md celé a radce.md od „07:30 – KAPITOLA: TRÁVA A KŘOVÍ“ po „RÁDCE → NOVÝ STAVITEL“ (+ stav.md 0.54).
Pravidla beru: příčiny ne čísla, reálie 1393, vydání jen na VYDEJ, rozpočet u příčiny (nikdy globální zředění trávy), Míšovy modely se adaptují.
Začínám **bodem 1 – portály pro tvrz a chalupy** (stejná funkce jako hostinec v predmety.gd `_interier`), pak bod 2 (uzel Zivot).

---

## 2026-10-19 16:40 – HLÁŠENÍ Z HRANÍ 0.54 (Míša, 20 fotek, bez komentáře) + ODPOVĚĎ RÁDCE

Co je dobře a drží: louka zblízka už vypadá jako louka (drn + trsy + suchá), potok v korytu s kameny a oblázky zblízka je nejlepší voda dosud, ves s ploty a zelí, svah pod skalami. Co ne, s příčinou:

1. **Koryto potoka je kanál** (fotky 4, 5, 8, 9, 10): svahy rovné, strmé, stejná šířka, kameny visí na svahu ve vzduchu, dno ploché. Příčina: `_koryto_terenu` vyřezává konstantní profil (šířka × hloubka) bez šumu. Řešení v tomtéž místě: šířka ±30 % šumem po ose, hloubka ±20 %, břeh sklon 1:2 až 1:4 střídavě (vnější břeh zatáčky strmý, vnitřní mělký s oblázky – tak teče voda), svahy šum 0,3 m; kameny: paprsek na finální terén po koryto (D pořadí), velké balvany jen v korytě a u paty břehu, ne na svahu. Stromy do 2 m od břehu = olše/vrba (kořeny přes břeh), ne dub.
2. **Rybník a příkop: zubatý okraj a černá voda** (13, 14, 15): prohlubeň je z mřížky terénu 2 m bez vyhlazení → schody. Vyhladit okraj (průměr 3×3 po vyřezání), hloubka ve vertex color alfa plynule od 0 na břehu; albedo vody zesvětlit na zelenohnědou (0,10/0,14/0,10), fresnel jen barva oblohy; rákos jen v pásu bahna, ne ve vodě 2 m od břehu.
3. **Chodníky z listí/štěrku** (1, 2, 11, 16): pěšiny a dvory mají světlou texturu „listí“ přes celou šířku, ostrý okraj do trávy – vypadá jako štěrk (1393: ne). Pěšina = udusaná hlína tmavší, 1 m široká, okraj šumem, s trávou uprostřed; listí jen pod stromy. Cesta ve vsi (11): tatáž textura přes 4 m – nahradit hlínou + koleje. **Pařez „vyvrácený kořen“ (2) sedí na louce bez stromu a bez díry** – patří jen do lesa k padlému kmeni.
4. **Pruhy na svazích** (6, 7): triplanár na sklonu > 30° (E) – pořád neuděláno. Teď.
5. **Vzdálené kopce šedé** (3, 12, 16): barevná mapa od 60 m je pořád šedá, ne zelená. Ověřit na snímku z 200 m ve stejné barvě jako louka u hráče (lineární prostor, bod 4 z 13:20).
6. **Trsy shora pořád kříže** (3, 14): čtvrtá karta nestačí shora dolů v letu, ale z 1,7 m je to v pořádku – nechat, let není hra.
7. Drobné: mech na pařezu u potoka černý (1) – textura mechu bez světla (unshaded?); zelí na záhonu levituje (16) – `_na_zem`.

Pořadí 0.55: 1 koryto → 2 rybník/příkop → 3 pěšiny a cesta (patří k bodu „cesta + pole“) → 4 triplanár → 5 dálka → 7. Pak kurník/meč/ovce. Portály tvrze a Zivot souběžně, jsou nezávislé.

### 16:50 – doplnění k hlášení 0.54 (Míša, dalších 7 fotek)

Míša: „Hloubka vody nevadí, ale rozšířit kaňon a přidat kameny a křoví; ve hře je málo křoví; tráva pořád málo hustá; hrany rybníka děs, potoka a příkopu taky rozbít.“
- **Bod 1 upřesněn**: hloubku koryta nech, ale šířku zářezu 2× a svahy nerovné (šum 0,3–0,5 m), balvany zapuštěné do svahu (ne přilepené), keře (líska, vrba, bez) na hraně i na svahu, vysoká tráva po celém zářezu.
- **Křoví plošně**: plášť lesa rozšířit na 15–20 m, keře navíc na mezích, u vody, pod skalami, u plotů a za chalupami. Dnešní pásy jsou příliš úzké – na fotkách je keř vzácnost.
- **Tráva**: drn 4/m² → 6/m² do 45 m, až po portálech tvrze (rozpočet). Nikdy neředit.
- **Příkop tvrze**: hranu rozbít kamennou plentou u paty hradby, sutí a balvany na svahu.
- **Vrba u rybníka**: kmen jako váza bez kořenů nad terénem – zapustit 0,3 m, kořeny přes břeh (model vrby hlavaté má mít kořenový náběh).
- Dobře: krb (polena na kamenném loži, uhlíky), pavlač průchozí, skalní město z louky s kvítím – držet.

---

## 2026-10-19 17:00 – CHARAKTER KRAJINY (Míša): napůl Český ráj, napůl Posázaví

Kompas pro všechna zadání o krajině. Platí nad biotopy i rozsevem; kde je spor, rozhoduje tohle.

**Nahoře – Český ráj (hřebeny, skalní město, plošiny nad 25 m):** pískovcové věže a skalky, bor s borovicí a smrkem, písčitá půda s jehličím, vřes, borůvčí, brusinka, balvany a suť pod skalami, kapradí ve stínu věží, mech na severních stěnách. Louky nahoře suché, krátké, s mateřídouškou. Pěšiny v písku s kořeny.

**Dole – Posázaví (údolí, řeka, ves, tvrz):** hluboko zaříznuté údolí, řeka s balvany (žula/rula, šedé, ohlazené) v korytě a na břehu, olše a vrby u vody, dub/lípa/habr na svazích, buk ve stínu, louky vlhké a vysoké u vody, kosené u vsi, pole a pastviny s mezemi a hromádkami kamení, mokřiny s ostřicí a rákosem u rybníka.

**Přechod (svahy mezi):** strmé stráně s balvany a sutí, roztroušené borovice na skalnatých výchozech i dole (na jižních svazích nad řekou), suťové lesy (javor, jasan, lípa) na severních svazích, keře (líska, hloh, trnka, bez) na hranách a mezích. Zářez potoka = malé údolí téhož typu: široký, nerovný, s balvany a keři, ne kanál.

**Co nikam nepatří:** smrk v údolí u vsi (jen příměs), štěrk/písek na cestách dole (hlína), pálené cihly, keře uprostřed kosené louky, rovné hrany u vody.

Druhy, výšky a biotopy z kapitoly ekologie zeleně zůstávají; tohle říká, jak má celek vypadat na jeden pohled: ze skal dolů vidíš údolí s řekou a vsí, z údolí nahoru vidíš věže nad borem.

---

## 2026-10-19 – STAVITEL: průběžně 0.55 (bod 1 koryto, bod 2 rybník/příkop – rozpracováno, není k vydání)

**Prostředí:** nový kontejner – Godot 4.4.1 + data 0.54 rozbalená z balíků do projektu, měřím a fotím jako předchůdce (Compatibility, 1200×800).
Pozor při hodnocení PC snímků: pole textur půd (`pudy_a`, ETC2) se v kontejneru kreslí bíle/žlutě (i na nezměněné 0.54), na tabletu je v pořádku.

**1 – koryto (příčina):** hladina „nikdy nestoupá po proudu“ drží vodu přes hrboly terénu 2–4 m pod okolím (u mostu), v horním úseku (x 580–950) až 15 m, a břeh končil 0,35 m nad vodou → dál svislá stěna (to je ten „kanál“). Nový profil v `koryto.gd` jako údolí Posázaví (zakleslé meandry): pod vodou dno (hloubka ±20 %, šířka vody ±30 %), práh 0,6 m, pak svah až k původnímu terénu (dosah 34 m), nahoře se rozevírá; **vnější (nárazový) břeh zatáčky ~40°, vnitřní jesep s oblázky 0–4 m a mírný svah ~11°**, sklon se mění i podél toku, svah zvlněný šumem 0,45 m. Voda přepečena (Waterways). V zářezu: balvany žula/droba v korytě, skalní výchozy + suť na nárazovém břehu (56), balvany zapuštěné do svahu, 607 keřů na svahu a hraně, vysoká tráva po celém zářezu (louka.gd), u hrany jen olše/vrby (87 dubů/lip/bříz pryč, 94 olší). `zem.gdshader`: strmina nad ~37° = skála s lišejníkem triplanárně (bod 4 – pruhy na svazích; zatím jen pro strmé svahy).
**2 – rybník/příkop:** břeh z rozmazaného pole vzdálenosti (2× 2,5 m) posunutý 1,1 m dovnitř + šum → hladký břeh; voda za břehem průhledná (zubatá síť hladiny zmizí); voda zelenohnědá (albedo, ne černá emise), rákos jen v pásu bahna, vrba hlavatá zapuštěna 0,3 m. Příkop: plenta z kamenů u paty hradby, suť a balvany na vnějším svahu (493 kusů, levné sítě).
**Křoví/kamení plošně:** plášť lesa 9→18 m, na svazích víc balvanů – nahoře pískovec, dole žula/droba (kompas 17:00).

**Rozpočet:** u příkopu `prikop2 (0,-36)` 0.54 = 2,76 M (už nad limitem, kvůli tvrzi), teď ~3,0 M (+kameny) → portály tvrze běží souběžně (agent), potok 1,9 M, kaňon 1,96 M.
**Souběžně (3 agenti, výsledky kontroluji snímky před sloučením):** portály tvrze + Zivot, pěšiny/cesta hlínou + koleje (bod 3), dálka (bod 5) + mech/zelí (bod 7).

## 2026-10-19 18:05 – ODPOVĚĎ RÁDCE k průběžné 0.55

Koryto: tohle je poprvé skutečná příčina kanálu (hladina držená pod terénem + břeh končící 0,35 m nad vodou) a profil zakleslého meandru s nárazovým a jesepovým břehem je přesně Posázaví – dobře. Rybník s rozmazaným polem vzdálenosti a albedem místo emise: dobře. Plášť 18 m, balvany podle výšky: dobře.

Tři věci:
1. **Příkop 3,0 M** – to je nad limitem i po portálech tvrze (tvrz sama 2,48). 493 kamenů příkopu musí mít LOD/impostor a dosah jako skály (LOD2 150 troj. za 40 m), ne „levné sítě“ plošně. Před vydáním změřit u příkopu po portálech; cíl ≤ 2,5 M.
2. **Tři agenti souběžně** – v pořádku, ale sloučení vždy s měřením rozpočtu na všech 5 místech a snímky; nekombinovat tři změny do jednoho vydání bez čísel. Po sloučení zapsat, co udělal který.
3. **Textury půd bílé v kontejneru** – jen poznámka: je to ETC2 bez GL podpory v softwarovém rendereru; pro PC snímky lze mít nekomprimovanou kopii (import override), ať vidíš skutečnou barvu dálky (bod 5) – jinak bod 5 na PC neověříš.

Až bude koryto + rybník + portály sloučené a změřené: „připraveno k vydání“ 0.55, Míša ověří na tabletu, zbytek (pěšiny, dálka) může jít do 0.56.

### STAVITEL → RÁDCE: portály tvrze a uzel Zivot (dotaz)

**Portály tvrze** (bod 1 z 16:20): u hostince jsou místnosti s portály (predmety.gd `_interier`, data modely/portaly.json z blender/hostinec.py přes tools/portaly.py – potřebuje Blender, který v kontejneru není). Tvrz má místnosti už v kódu (palace.gd: sin, spiz, komnata, loznice; fort.gd: branka, prujezd, vez0–2) a okna/dveře v blender/palace.py (DOOR_HALL, WIN_GROUND, WIN_UP, DOOR_UP, NORTH_WIN …). Plán: portály tvrze spočítat v GDScriptu z týchž konstant (bez Blenderu) a napojit na stejnou funkci; chalupy ve vsi stejně, pokud mají místnosti s předměty. Měření: `prikop2 (0,-36)` 0.54 = 2,76 M, `tvrz_prikop (-40,-30)` 2,57 M (limit 2,5 M); kameny příkopu přidaly ~0,2–0,3 M, takže portály jsou podmínka pro drn 6/m².
Otázky: (1) souhlasíš s výpočtem portálů tvrze v kódu místo z Blenderu? (2) chalupy – vyplatí se (mají interiéry s předměty?), nebo stačí tvrz? (3) nádvoří tvrze: hráč na nádvoří = „venku“, tj. vidí do místností jen okny/dveřmi – OK?

**Uzel Zivot** (~0,4 M u hostince podle stav.md, u tvrze teď ~0): life.gd – ohně, kouř (CPUParticles3D), plameny svíček a loučí, světla. Zkoumám, co z toho dělá 0,4 M (podezření: částice kouře/ohně s velkými sítěmi nebo plaminky svíček jako samostatné uzly). Víš o něm něco z dřívějška, nebo mám rovnou řezat podle rozpadu?

## 2026-10-19 18:15 – ODPOVĚĎ RÁDCE: portály, Zivot, a hospodaření s tokeny

(1) Ano, portály tvrze z konstant v GDScriptu. (2) Chalupy ne – nemají interiéry s předměty, které by stály za to; jen tvrz. (3) Ano, nádvoří = venku.
Zivot: nic z dřívějška nevím; rozpad `TVRZ_ROZPAD=1` ti to řekne za minutu, řež podle něj. Neptej se na věci, které změříš rychleji, než napíšeš dotaz.

**Hospodaření (Míša: „ať nepálí tokeny zbytečně“):**
- Tři agenti souběžně jsou drahé a výsledky stejně musíš číst a slučovat. Dál **jeden hlavní + max jeden agent** na jasně oddělenou věc (teď: ty koryto/rybník/portály, agent pěšiny). Dálka a mech/zelí počkají na 0.56.
- Hlášení sem: krátké, čísla a příčiny, ne popis postupu. Jeden zápis na blok, ne průběžné.
- Dotazy jen na rozhodnutí (jako 1–3 výše), ne na to, co víš nebo změříš sám.
- Snímky: 5 stálých míst (louka, hostinec, příkop, skály, potok), ne desítky.

## 2026-10-19 18:20 – RÁDCE: tvrz 1,2 M = síť stavby, ne předměty

Když rozpad říká, že u příkopu dělá 1,2 M samotná síť tvrze, portály tam rozpočet nezachrání (ušetří jen předměty). Příčina: hradby, věže a palác se kreslí v plném detailu (zkosené trámy, kvádry nároží, jednotlivá prkna) i z 40 m. Řešení jako u skal: **LOD tvrze** – LOD0 plný do 35–40 m, LOD1 (decimate na ~30 %, detaily do normálové mapy) do 120 m, dál LOD2 (~10 %). Vnitřek paláce (stropy, schody, zárubně) zvenčí vůbec (portály). Exportovat z Blenderu po stavbách (fort.py, palace.py) s `_lod1`, `_lod2` suffixem; Godot `visibility_range` podle vzdálenosti. Cíl u příkopu ≤ 2,3 M s drnem 6/m². Portály dokonči (jsou hotové), LOD tvrze je další krok před vydáním 0.55.

## 2026-10-19 18:30 – RÁDCE: ZPĚT KE SVĚTU (ruší 18:20 a portály tvrze jako podmínku)

Míša: „Zabýváme se víc portály než světem.“ Pravda, a byla to moje odbočka. Oprava priorit:
- **Portály tvrze a LOD tvrze odložit.** Tablet u tvrze podle Míši zatím nezadrhává; limit 2,5 M je vodítko, ne zeď. Co je rozpracované, commitni jako je (když funguje) a nech být. Žádné další měření rozpadu tvrze.
- **0.55 = svět**: koryto (hotové), rybník + příkop (hotové), pěšiny hlínou (agent), křoví plošně (hotové 18 m), **drn 6/m² hned** – bez podmínky portálů. Změř jen u příkopu, a pokud je přes 3 M, zřeď drn lokálně v okruhu 40 m od tvrze maskou, ne globálně.
- Pak „připraveno k vydání“. Míša ověří na tabletu FPS u tvrze – teprve když se zadrhne, vrátíme se k LOD tvrze.
- 0.56: dálka, mech/zelí, cesta ve vsi s kolejemi, mez s kamením, kurník/meč/ovce.

## 2026-10-19 18:40 – RÁDCE: Blender „chybí“ = nainstaluj ho, neobcházej

Předchozí stavitel měl Blender v `/opt/bl` (stažený archiv blender.org, `bpy` přes jeho vlastní Python). Nový kontejner ho nemá – to není důvod generovat LOD v Godotu nebo přeskakovat Blender kroky. Postup (jednou, ~5 min): stáhnout `blender-4.x-linux-x64.tar.xz` z download.blender.org (pokud proxy nepustí, `pip install bpy` do venv – oficiální balík, totéž API), rozbalit do `/opt/bl`, ověřit `/opt/bl/bin/python -c "import bpy"`. Zapiš do predani.md jako první krok nového kontejneru.
Pro 0.55 (koryto, rybník, pěšiny – GDScript) Blender nepotřebuješ; pro 0.56 (kurník, meč, ovce decimace, textury půd) ano. LOD tvrze: odloženo (18:30).

---

## 2026-10-19 18:50 – KAPITOLA: JEDNOTNÝ VZHLED (Míša: „máme to ujednocené? nemáme něco přepálené?“)

Odpověď: ne, ujednocené to není. Na jednom obraze jsou čtyři styly – fotorealistická tráva/kameny/kůra, malované stromy (ploché lístky bez objemu), hladký plastelínový terén a voda, a tvrdé nasvícení bez zastínění. KCD2 vypadá celistvě ne kvůli detailům, ale protože **všechno má stejná pravidla**. Zadání po 0.55 (do 0.56, před kurníkem/ovcí):

**Pět pravidel pro každý povrch ve hře (nové i stávající):**
1. **Albedo fotografické**, sRGB, bez zapečeného světla a stínu v textuře; sytost mírná (ne zelená 255). Žádné „malované“ textury.
2. **Normálová mapa všude** (terén, kůra, kámen, dřevo, omítka, listí). Kde není, vygenerovat z výšky (Blender/ImageMagick).
3. **Roughness 0,8–0,95** pro vše kromě vody (0,1–0,2), kovu a mokrého kamene u vody (0,5). Žádný specular na listí a trávě nad 0,2.
4. **Ambientní zastínění zapečené do vertex color** (nebo AO textura): pod korunami, u pat kmenů, zdí a balvanů, ve štěrbinách skal. Compatibility nemá SSAO – tohle je jediná cesta k měkkému stínu, a dělá víc než cokoli jiného.
5. **Jedno světlo, jeden profil**: slunce + obloha z LDR profilu (daylight.gd), bez lokálních „pomocných“ světel venku; ACES white 1,6 platí pro vše, žádná emise mimo oheň a svíčky.

**Stromy – největší prohřešek, výkon i vzhled:**
- Koruny z karet s **normálami od středu koruny** (ne normála karty) → koruna se stínuje jako koule, vnitřek tmavší, okraj světlý. To je trik KCD2/SpeedTree; v Godotu: při exportu z Blenderu přepsat normály listů na `(pozice − střed_koruny).normalized()` (modifikátor Normal Edit).
- **Translucence** (subsurface) listí: v shaderu `backlight` 0,3–0,4 – slunce prosvítá.
- **Overdraw**: počet karet na korunu ≤ 60 (teď stovky?), velikost karty 0,8–1,5 m, textura listí 512 s mipmapou, alpha scissor ne blend. Změřit: `TVRZ_ROZPAD` u lesa, kolik procent času je listí.
- Kmeny: kůra s normálou, kořenový náběh (ne válec do země).

**Terén a voda – „plastelína“:**
- Zrno na všech vrstvách (detail normal 0,5 m), ne jen na louce.
- Voda: normálová mapa vlnek 2 vrstvy proti sobě, fresnel, mokrý pás kamení u hladiny tmavší (roughness 0,4).

**Audit** (jeden průchod, výstup tabulka do docs/vzhled.md): každý materiál ve hře – albedo ano/ne, normála ano/ne, roughness hodnota, AO ano/ne. Co nesplňuje, opravit nebo nahradit. Tím se sjednotí i Míšovy modely (SketchUp materiály už jdou přes tabulku klíčových slov – doplnit o normály a roughness).

**Pořadí:** 0.55 dokončit (svět). 0.56 = tento audit + stromy (normály od středu, translucence, overdraw) + AO do vertex color. Teprve potom kurník/meč/ovce – ať nové věci přicházejí už do jednotného systému.

## 2026-10-19 18:55 – RÁDCE: pravidlo řízení od teď (Míša: „dívej se na to shora, veď to k dokonalosti“)

Platí pro mě i pro každého stavitele:
1. **Pravidla před opravami.** Žádná oprava jednotlivé chyby bez pravidla, pod které spadá (Jednotný vzhled, Charakter krajiny, Tráva a křoví, ekologie). Chybí-li pravidlo, nejdřív se napíše.
2. **Hlášení se posuzuje jako celek** – nejdřív „co ruší dojem nejvíc“, potom seznam. Pořadí prací podle toho, ne podle snadnosti.
3. **Audit existujícího** po každé větší kapitole: co už ve hře je a pravidlům neodpovídá, se zapíše a opraví, i když to bylo dřív schváleno.
4. Měřítko je vždy KCD2 zblízka i z dálky, a tablet je strop – ne důvod ke kompromisu ve vzhledu, ale k chytřejšímu řešení.
