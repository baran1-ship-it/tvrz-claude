# Vnitřek hradu jen zblízka – rešerše a návrh (13. 11. 2026)

Zadání Míši: „s oddělováním vnitřních dílů hradu si načti na internetu, ale jinak si myslím, že i Havran umí podrobnou
databázi, jak co dělat, možná něco ani sám nepoužívá“. Nic se tím nemění, je to podklad k rozhodnutí. Čísla označená
**rozbor glb** jsou spočtená z exportovaných souborů `hra/modely/hrady/puchart*.glb` (těžiště trojúhelníků proti
půdorysům `hra/data/stavby_pudorysy.json`). Nejsou to měření na tabletu. Co z tabletu změřené není, je **NEOVERENO**.

## 0. Krátce

1. **Hrad je ve hře jedna síť na hrad** (`hrad_A` 288 613 troj./25 materiálů, `hrad_B` 180 393/18). Godot proto nemůže
   nic z hradu oříznout. Když je vidět kousek, kreslí se celý hrad se všemi povrchy, ve stínovém průchodu ještě jednou
   v plném detailu. Platí pro něj i limit 8 bodových světel na jednu síť, přitom světel hradu je 37.
2. **Vnitřek je asi 15–25 % blízké verze** (rozbor glb). Uvnitř půdorysů budov zúžených o 0,6 m je u A 72 tis. troj.
   (25 %), u B 23 tis. (13 %), a věže a sklep v tom ještě nejsou. Při zúžení o 1,2 m vychází 41 tis. a 11 tis. Hlavně
   jde o prkna podlah, trámy (dub), kování, ostění oken a sklep. **Daleká verze (71 tis.) vnitřek pořád obsahuje**:
   u A asi 10 tis. troj. (23 %, klenby sklepa, podlahy, schody, nábytek), přitom z 60 m a dál ho nikdo nevidí.
3. Změřený čas hradu na tabletu je p95 17 ms, takže hrad dnes nebrzdí. Oddělený vnitřek dá rezervu, menší stínový
   průchod a správná světla v místnostech. Nejvíc pomůže pohledům ze vsi a z cest, kde se kreslí celý hrad. Les (51 ms)
   a voda (45 ms) jsou větší problém a tímhle se neřeší.
4. **Havran má zapnutý occlusion culling (OccluderInstance3D) i v Compatibility, Puchart ne.** Havranův `svet.gd` k tomu
   26. 10. píše: „nezávisí na rendereru – platí i v Compatibility; předchozí komentáře ‚Compatibility nemá occlusion
   culling‘ byly omyl“. Jeho zápis z 13. 11. (`rozpocty.json` tvrz_drobne) a komentáře v Puchartu (`predmety.gd`
   177/863/948) přesto opakují ten starý omyl. Míša měla pravdu: Havran to umí a sám na to zapomněl. Dokumentace
   Godotu mu dává za pravdu (kap. 2). **Na tabletu ho ale nikdo nezměřil.** Na PC ušetřil terénem jen 0–46 kreslení
   a běží na CPU každý snímek. Proto jen jako A/B.
5. **Havranova data o záseccích (doplnění Míši):** doložené jsou dva zdroje záseků, které se týkají právě skrývání
   vnitřků. (a) Skript, který při vstupu do budovy prochází strom uzlů a přepíná tisíce uzlů najednou
   (`predmety._vnitrek`: zásek 93 ms, `predmety` 15–61 ms na tabletu; po opravě rozpočtem 1 ms skripty 3–8 ms).
   (b) „První vykreslení“: zásek 0,5–4 s, když se poprvé ukáže nový obsah (shader nebo textura). Návrh proto
   nepoužívá žádný skript, který za běhu skrývá uzly. Používá jen `visibility_range` (počítá engine při ořezu,
   bez průchodu stromem) a statické rozdělení z Blenderu. Každý nový uzel se musí předehřát.
6. Návrh (kap. 3): v Blenderu dát vnitřek každé budovy a věže do vlastního uzlu `*_Vnitrek_<budova>`, který se kreslí
   do vzdálenosti „poloměr budovy + 25 m“. Z daleké verze vnitřek úplně vyndat a okna i dveře zevnitř zakrýt tmavou
   zátkou (Warhorse). Stín hradu brát z daleké verze. Occlusion culling vyzkoušet jako A/B. Každý krok hlídat
   hlídačem scén (změna obrazu na hranici dosahu) a snímky do otvorů ze `build/portaly.json`.

Pozn.: v datech je `hrad_vzhled.json lod.daleko_od_m = 60` (výchozí hodnota v kódu `hlavni.gd` je 120). Hrad se tedy
přepíná na dálkovou verzi už u 60 m.

## 1. Havranovy techniky a stav v Puchartu

Zdroj: větev `origin/claude/new-session-0dtk58` (čteno přes `git show`). Puchart: `hra/scripts/*.gd`,
`pravidla/svet/rozpocty.json`, `hra/project.godot`, `blender/`. **Doplnění Míši: Havran má na tabletu záseky, takže
nic nepřebírat naslepo.** Ke každé technice je proto sloupec, který říká, co z ní je doložené měřením (Havran
`docs/mereni_verze.md`, `docs/stav_historie.md`, `docs/rozpracovane/misa_28_chyby.md`, `radce.md`, commity) a jestli
může sama zásek způsobit. Zkratky: **TAB** = změřeno na tabletu, **PC** = změřeno jen na PC (režim mobil),
**NEOV** = neměřeno.

| # | Technika | Havran soubor | Ověřeno měřením? / riziko záseku | Puchart má? | Doporučení |
|---|---|---|---|---|---|
| 1 | **Místnosti s portály.** Předměty místnosti se kreslí, jen když je hráč v ní, v sousední místnosti, nebo venku do 12 m s otvorem v zorném poli; vyhodnocení 5× za sekundu | `predmety.gd` `_interier`, `portaly.gd`; `radce.md` 19. 10. 15:30 | **PC:** hostinec −0,33 M troj. (stav_historie ř. 193). Tvrz „v kódu, neměřeny“ (ř. 214). Riziko: přepíná `visible` jen u předmětů (desítky uzlů), malé. Na tabletu nikdy samostatně neměřeno | **NE** (kód zkopírovaný, `portaly.gd` má natvrdo Havranovu tvrz, `world = null`) | Teď nepřebírat. Hrad nemá předměty v místnostech. Až budou, měřit samostatně |
| 2 | **Skrývání krajiny, když je hráč uvnitř** (režim okno = dál než 80 m pryč, zavřená místnost = dál než 25 m pryč), průchod stromem uzlů po částech, přepočet po 8 m pohybu | `predmety.gd` `_vnitrek`, `_vnitrek_krok`; `rozpocty.json predmety_vnitrek` | **PC:** hostinec síň 839 → 578 kreslení, 1,84 → 1,12 M troj. (radce 0.60). **ZPŮSOBOVALO ZÁSEKY (TAB):** 0.93/0.94 hostinec zásek 93 ms a `predmety` 55–57 ms; 0.99994 `predmety` 15–26 ms každý snímek v síni (misa_28_chyby ř. 75: režim přeskakoval 48× za 48 hodnocení a pokaždé začal procházet 20 000 uzlů). Oprava 07ad712: rozpočet 1 ms, zúžení až po 2 s. **TAB 0.99995: skripty 3–8 ms**, záseky skriptů pryč. Zbylé podezření: po vstupu 2 s kreslí celý svět (misa_28 ř. 130). Každé zobrazení skrytých uzlů může vyvolat první vykreslení (viz č. 29) | **NE** (kód je, vypnutý) | **Nepřebírat** bez vlastního měření. Model „projít strom a přepínat tisíce uzlů“ je u Havrana doložený zdroj záseků. Lepší je dosah ve vlastnostech uzlů (`visibility_range`), který počítá engine sám bez skriptu. Pokud ano, tak až po kap. 3 a s testem `predmety_cas` |
| 3 | **Louka uvnitř budovy jen do 20 m** | `louka.gd` (soupis skripty ř. 58) | Součást č. 2 (PC). Samostatně NEOV | NE | S č. 2, nepřebírat teď |
| 4 | **Interiér zvenku jen do 12 m** (dřív 25 m) | `predmety.gd` (0.62) | **PC:** hostinec venku 1,83 → 1,52 M troj., 537 kreslení (radce 0.62). Riziko záseku malé (předměty) | NE | Číslo jako vodítko pro dosah vnitřku hradu (kap. 3.3) |
| 5 | **Předměty uvnitř domů vsi jen do 12 m** (`svet.v_dome`) | `svet.gd`, `predmety.gd`; c4020a2 | **NEOV.** Commit sám píše „ověřuje se“. Je to `visibility_range` (engine), bez skriptu za běhu. Riziko: první vykreslení při přiblížení (č. 29) | Částečně (dosah podle velikosti ano, `v_dome` ne) | Lze bezpečně měřit (snímek a kreslení u domu). Až po Havranově měření nebo po našem |
| 6 | **Drobné a vnitřní díly tvrze do 200 m** podle předpony jména | `svet.gd`, `rozpocty.json tvrz_drobne`; c4020a2 | **NEOV** („ověřuje se“). Motivace: rozbor kreslení 13. 11. (tvrz z 900 m 119 kreslení). Mechanismus `visibility_range`, bez skriptu | **NE pro hrad** (jedna síť). Pohyblivé díly ano (13. 11.) | Princip převzít v kap. 3 a změřit u nás |
| 7 | **Dosah předmětu podle velikosti** 20/40/80 m | `predmety.gd` spawn | Havran 29. 10.: dosah 60 m natvrdo dával u lomu +232 kreslení (predani 382). PC. Riziko malé | ANO | – |
| 8 | **LOD domů ve třech stupních**, `lod_bias` proti automatickému LOD | `svet.gd` `_ves_domy`, `blender/ves_domy.py` | **TAB:** „ves 47 FPS“ (0.83), domy do 75 m (0.92). PREHLED ř. 188: „úbytek kreslení – zavedeno“. Riziko: přechod LOD = první vykreslení stupně | ANO | – |
| 9 | **Vnitřek domu (`*Interier`) do 35 m bez stínu, `*Drobne` do 70 m** | `svet.gd` `_ves_domy` | Součást č. 8 (TAB nepřímo) | ANO u domů, **NE u hradu** | Kap. 3 |
| 10 | **Stín jen z hrubé verze** (`SHADOWS_ONLY` kopie `_Daleko`) | `svet.gd` `_ves_domy` (0.92) | **PC:** stín domů u rybníka 186 kreslení (radce 0.92). Riziko záseku: žádné nové materiály, jen jiná síť | ANO u domů, **NE u hradu** | Převzít pro hrad (kap. 3.5), změřit |
| 11 | **Occlusion culling** (terén `ArrayOccluder3D`, krabice domů vypínané u hráče, remízky, nitro lesa) | `svet.gd` `_okluzory`, `main.gd` 2127 | **PC:** terén ušetřil jen 0–46 kreslení (stav.md, PREHLED ř. 190: „přínos malý“). Na tabletu nikdy samostatně neměřeno. Riziko: rastr Embree běží na CPU **každý snímek** (stálá cena, NEOV na Adrenu). Okluzor za hry nehýbat. Přepínání `visible` u hráče je levné. Odkrytí uzlu za kopcem = jeho první vykreslení (č. 29) | **NE** (`project.godot` ho nemá; komentáře „Compatibility ho nemá“ jsou omyl) | Jen jako **A/B na měřicí trase** (jedno nastavení), bez dalších okluzorů. Pokud nepřinese ≥ 5 % na úseku hradu/vsi, nezavádět |
| 12 | **Velké sítě rozdělit na čtverce** kvůli ořezu pohledem | `svet.gd` `_rozdel_site` (0.60–0.62) | **PC:** příkop 2,78 → 2,54 M troj., ale kreslení 1527 → 1762, větší čtverce pak 1621. Dělení terénu dělalo díry a skvrny, zrušeno (0.62). Dělalo se za běhu při startu (2 s) | Terén ano (offline). Hrad NE | Dělit offline v Blenderu podle budov (kap. 3.2), ne za běhu |
| 13 | **`ImporterMesh.generate_lods` za běhu vrací 0 úrovní**, LOD jen offline | `radce.md` 0.62 | Ověřeno skriptem (PC). Generování „jen zdržovalo start“ | ANO (offline) | – |
| 14 | **Impostory stromů** | `blender/impostory.py`, `svet.gd` | TAB nepřímo (les jinak 13–16 FPS, radce). Les dál 51–57 ms | ANO | – |
| 15 | **Mizení trávy po trsech, buňky ve vláknech** | `louka.gd` | **TAB:** špičky při načítání nových buněk (rákosí 86, louka 69 ms – radce 2471). Načítání za běhu je u Havrana doložený zdroj špiček | Částečně (`byliny.gd` ve vláknech, předstih) | Mimo téma hradu |
| 16 | **Částice jen do dosahu, dál bez výpočtu** | `life.gd` `_castice_lod`; c4020a2 | **NEOV** (motivace: trasa 13. 11. ves-vjezd CPU 95 %, 16 kreslení částic). Riziko: přepnutí `process_mode` znovu spustí částice. Kontrola 2× za sekundu, malé | Částečně (plamen `visibility_range_end = 40`, výpočet dál) | Lze bezpečně změřit (CPU na úseku se loučemi). Až po měření |
| 17 | **Pohyblivé díly do dosahu** | – | Puchart 13. 11., NEOV na tabletu | ANO | – |
| 18 | **Warhorse KM-A-46: v LOD1 a LOD2 není vnitřek, okna a dveře kryje černá výplň 30 cm za zdí** | `warhorse_do_dat.md` 1.2 | Pravidlo studia (KCD2), u Havrana nezavedeno. Riziko záseku žádné: méně geometrie, žádný skript | Částečně (`tma` ve světlících plných věží) | **Převzít** (kap. 3.4), bezpečné |
| 19 | **Warhorse KM-A-51: sklep jako zvláštní model s malou dohledností** | `warhorse_do_dat.md` 1.2 | Pravidlo studia, Havran nezavedl | NE | Kap. 3.3 |
| 20 | **Warhorse KM-A-47: okluzor s jednotkami trojúhelníků, vnější zdi oboustranně** | `warhorse_do_dat.md` 1.4 | Pravidlo studia. Cena CPU každý snímek | NE | Jen pokud A/B č. 11 vyjde |
| 21 | **Warhorse KM-A-49: stínová proxy, jeden materiál** | `warhorse_do_dat.md` 1.3 | Pravidlo studia. NEW STATE Mobile: zjednodušené stínové modely −2 % GPU (rešerše 10. 11.) | NE (hrad) | Kap. 3.5 |
| 22 | **Warhorse KM-A-46: LOD nejdřív ubírá materiály (kreslení)** | `warhorse_do_dat.md` 1.2 | Pravidlo studia | Částečně (daleká verze 18/10 povrchů) | Daleká verze bez vnitřku ubere další |
| 23 | **Atlasy a sloučení materiálů** | ZAVER §3.7 | Nezavedeno. Kreslení u Havrana 266–528 „přestalo být hrdlem“ (rešerše 10. 11.) | NE | Ne teď |
| 24 | **Bez průhledného prolínání dosahů** | PREHLED §6 | Zásada (Adreno), riziko žádné | ANO | – |
| 25 | **Zapečené AO** | radce K4 | Za běhu zdarma | ANO | – |
| 26 | **Rozpad, co se kreslí** (`TVRZ_ROZPAD`) | `radce.md` 0.59 | Diagnostika | Částečně (hlídač scén) | Přidat rozpad po uzlech hradu |
| 27 | **Tabulka tříd** | `navrh_tabulek.md` | – | Částečně | Dosahy vnitřku zapsat do dat |
| 28 | **Krabicové okluzory domů vypnuté** (kamera uvnitř zakryje vše) | `svet.gd` 7170 | Poučení z chyby | NE | Okluzor zdi jen uvnitř tloušťky zdi |
| 29 | **Poučení o záseku „první vykreslení“**: 0,5–4 s při prvním objevení něčeho nového (kovárna 538 ms, ves 1897 ms, most 4104 ms). Compatibility sestaví shader až při prvním kreslení. Předehřátí shaderů při načtení | `predani.md`, `mereni_verze.md` 0.99995, misa_28 ř. 90; rešerše 10. 11. | **TAB:** opakovaně naměřeno, příčina jen zčásti potvrzena (shader nebo nahrávání textur). Platí pro **každý uzel, který se poprvé objeví** dosahem, skrytím nebo LOD | ANO (`predehrati.gd`). **Pozor:** předehřívá jen uzly `is_visible_in_tree()`, takže skrytý stupeň hradu (`_lod_tick` ho skryje) a budoucí skryté vnitřky se nepředehřejí | Každý nový uzel z kap. 3 (vnitřky, zátky, stínová kopie) předehřát s `mimo_strom = true`. Ověřit: zásek > 40 ms při prvním vstupu na nádvoří a do budovy jen v 1. průchodu = chybí předehřátí |

**Co z Havrana je doložené jako přínos bez záseků:** LOD domů s hrubým stínem (8–10), dosah předmětů podle velikosti
(7), interiér zvenku jen zblízka (4), offline LOD (13), předehřátí (29, s výhradou). **Doložené jako zdroj záseků:**
skript, který za běhu prochází strom a přepíná tisíce uzlů (2), načítání a stavba za běhu (12 za startu, 15 buňky),
první vykreslení nového obsahu (29). **Neověřené:** occlusion culling na tabletu (11), commit c4020a2 (5, 6, 16).

## 2. Internet: jak to řeší jiné hry a co umí Godot 4.7 Compatibility

### 2.1 Occlusion culling v Godotu 4 a renderer Compatibility
- Okluze v Godotu 4 je **na CPU**: geometrie okluzorů se rastruje do malého bufferu knihovnou Embree („rasterizing the
  scene's occluder geometry to a low-resolution buffer on the CPU … using the software raytracing library Embree“).
  Návod jmenuje jen Forward+ a Mobile a o Compatibility mlčí
  ([Occlusion culling, docs stable](https://docs.godotengine.org/en/stable/tutorials/3d/occlusion_culling.html)).
- Srovnání rendererů výslovně říká: „If a feature is not listed here, it is available in all renderers“. Okluze ani
  visibility ranges v tabulce nejsou
  ([Overview of renderers](https://docs.godotengine.org/en/stable/tutorials/rendering/renderers.html)).
- Embree (modul `raycast`) se staví pro x86_64, **arm64** a wasm32
  ([modules/raycast/config.py](https://github.com/godotengine/godot/blob/master/modules/raycast/config.py)). Tablet je
  arm64, takže v šablonách pro Android má být. Havran to ve hře používá (`main.gd` 2127).
  **Že to na Xiaomi Pad 8 skutečně ořezává, je NEOVERENO.** Ověřit A/B s `use_occlusion_culling` na stejném snímku.
- Rady z návodu: okluzory za běhu nehýbat (přestavba BVH), raději přepínat viditelnost. Co nejjednodušší tvary.
  Nejlépe funguje v interiérech s hodně malými místnostmi. Pečení bere jen neprůhledné MeshInstance3D.
- Důsledek pro Puchart: okluze ořezává **celé instance podle jejich AABB**. Hrad jako jedna síť se neořeže nikdy.
  Ořezat jde jen to, co je za hradbou a hřbetem (buňky lesa a bylin, ves, voda) a po rozdělení i vnitřky budov.

### 2.2 Místnosti a portály
- Godot 3.4–3.6 měl Rooms & Portals (Room, RoomGroup, RoomManager, Portal) s portálovým ořezem a notifikacemi
  ([Introduction to Rooms and Portals, 3.4](https://docs.godotengine.org/en/3.4/tutorials/3d/portals/introduction_to_rooms_and_portals.html)).
  **Godot 4 ho nemá.** Náhrada je OccluderInstance3D (kap. 2.1) a ručně psaná logika místností, kterou Havran má
  v `predmety.gd`/`portaly.gd` (KCD2 princip, rádce 19. 10.).
- CryEngine (KCD1/2): **VisArea** je tvar ohraničující interiér pro ořez a světlo, **Portal** je malý otvor napůl uvnitř
  VisArea. Portál dveří se dá při zavřených dveřích vypnout
  ([CryEngine 3: VisArea and Portals](https://www.cryengine.com/docs/static/engines/cryengine-3/categories/1114113/pages/1048727)).
  Podle téhož enginu se portály mají použít jen tam, kde vycházejí lépe než coverage buffer (okluze z hloubky)
  ([Culling Explained](https://www.cryengine.com/docs/static/engines/cryengine-3/categories/1638401/pages/1605709)).
- Warhorse pro modery KCD2 (přes Havranův `warhorse_do_dat.md`, KM-A-46/47/49/51): vnitřek domu v LOD1 a LOD2 vůbec
  není, okna a dveře zakrývá černá výplň 30 cm za vnější zdí. Sklep a složitý interiér jsou zvláštní model s malou
  dohledností. Okluzory mají jen jednotky trojúhelníků. Stínová proxy má jeden materiál.

### 2.3 Dělení modelu a kreslení podle vzdálenosti (HLOD)
- Godot `visibility_range_begin/end` je HLOD: „A single larger mesh can replace several smaller meshes, so that the
  number of draw calls can be reduced at a distance.“ **Vzdálenost se měří ke středu AABB instance.** Okraje
  (margin) brání přeskakování tam a zpět. `Fade Self/Dependencies` vynutí na dobu přechodu průhledné kreslení
  („performance impact“), proto `Disabled`, případně dither. Dálkové stupně mají mít jednodušší materiály
  ([Visibility ranges (HLOD)](https://docs.godotengine.org/en/stable/tutorials/3d/visibility_ranges.html)).
- Unreal HLOD: skupina meshů se v dálce nahradí jedním proxy meshem s jedním materiálem a atlasem. Jedno kreslení na
  proxy místo kreslení za každý mesh, slučování materiálů ubírá kreslení
  ([Unreal: Hierarchical Level of Detail](https://dev.epicgames.com/documentation/unreal-engine/hierarchical-level-of-detail-in-unreal-engine)).
  Daleká verze hradu Puchartu je stejný princip. Chybí jí jen vynechání vnitřku a méně materiálů.

### 2.4 Světla v Compatibility (důvod navíc dělit síť hradu)
- Compatibility kreslí „up to 8 OmniLights + 8 SpotLights … per mesh resource“, limit je v Project Settings > Limits >
  OpenGL ([Lights and shadows](https://docs.godotengine.org/en/stable/tutorials/3d/lights_and_shadows.html)).
  Hrad má 37 světel (`hra/data/svetla.json`, 16 z oken) na dvou sítích. Na jednu síť se tak dostane nejvýš 8 světel
  ze všech místností najednou a každý pixel celého hradu je počítá. Odhad (NEOVERENO): místnosti se rozsvěcují podle
  toho, která světla engine vybere, ne podle toho, kde stojí hráč. Vnitřek po budovách by limit dodržel přirozeně.

### 2.5 Ochrana proti „doskakování“ (pop-in) průhledem
- Okraj a prolínání: Godot margin + `FADE_DISABLED` (kap. 2.3). Havran má hysterezi `zuzeni_s` u režimu vnitřku.
- KCD/Warhorse: zvenku z dálky je oknem vidět jen tma (černá výplň), takže zmizení vnitřku nejde poznat. Havran
  k hostinci 0.62 píše totéž: „z dálky je okny vidět jen tma“.
- Godot 3 i CryEngine dělají portál: vnitřek se ukáže, jakmile je otvor v zorném poli a blízko, bez ohledu na
  vzdálenost ke středu budovy (Havran `_interier`: otvor do 12 m, míří k hráči, je před kamerou).

## 3. Návrh pro Puchart

Seřazeno podle poměru přínos/riziko. **Pravidlo proti záseků (z Havranových měření):** (1) žádný skript, který za
běhu prochází uzly a přepíná `visible`. Jen `visibility_range` a statické uzly z Blenderu. Výjimkou zůstává už
zavedený `_lod_tick` (dva páry uzlů, ne tisíce). (2) Žádné stavění ani načítání za běhu. (3) Každý nový uzel
(vnitřky, zátky, stínová kopie) předehřát při načtení. `predehrati.kopie` dnes bere jen `is_visible_in_tree()`, takže
uzly, které `_lod_tick` při startu skryje, je nutné předat s `mimo_strom = true`. (4) Každá změna se měří
samostatně: zásek > 40 ms jen v 1. průchodu = chybí předehřátí, v každém průchodu = obsah. Každý krok je samostatný: jedna změna, jedno měření (pravidlo rádce 21. 10.),
čísla do dat (`hrad_vzhled.json lod`, `rozpocty.json`), zdroj Warhorse KM-A-46/51 a Havran.

### 3.1 Kritérium „co je vnitřek“ (Blender)
Zdroj kritéria: v `puchart_hrad.py` už existují půdorysy `BUDOVY` (z `budova_k`, 8 budov, `hra/data/stavby_pudorysy.json`).
Chybí v nich věže (`vez2`, `vnitrek_veze`), sklep (`sklep_A`) a brány. Doplnit **seznam VNITRKY**: `{id, polygon
vnějšího líce, tloušťka zdi t, y_podlahy, y_okapu, typ}` pro každou budovu, věž a sklep, zapisovaný stejně jako BUDOVY.

Plocha (trojúhelník Part.f podle těžiště a normály) patří do `*_Vnitrek_<id>`, když:
1. těžiště leží v půdorysu zúženém o `t − 0,05 m`. Tím se dovnitř dostane i vnitřní líc obvodové zdi, ostění oken
   a dveří v tloušťce zdi zůstanou venku;
2. a zároveň leží pod spodním lícem střešní krytiny. Krytina (`sindel*`, `krytina`) a její bednění nad okapem jsou
   vnějšek. Podhled střechy uvnitř půdorysu je vnitřek, protože je vidět jen zevnitř;
3. nebo plochu vytvořila funkce, která je vnitřní z podstaty: `podlaha`, `vnitrek_veze`, `schody2` uvnitř půdorysu,
   `_pricka`, `kolenni_steny`, `podkrovi_vystup`, `klenba` sklepa, nábytek `palac_A` (`_stul`, `_lavice`, `_truhla`,
   `_loze`, obklad světnice), `sklep_A`, `sud`, `kruh_retez`. Doporučená cesta je předat těmto funkcím vlastní
   `Part(f"{P.name}_Vnitrek_{id}")`. Geometrické kritérium 1–2 pak slouží jako **hlídač** (nic z vnitřku ve vnějšku
   a naopak) a jako záchrana pro sdílené funkce (`zed2`/`stena_sit` stavějí obě líce zdi naráz).

**Vždy vnějšek:** střechy, štíty, ochozy a pavlače, cimbuří a koruna, nádvoří a dlažba, venkovní schody a rampy,
**průjezd brány a jeho klenba** (otevřený na obě strany, vidět z cesty), portály a ostění, okenice a mříže v líci,
zátky `tma`, kolize (`KOLIZE` zůstává jedna). Pohyblivé díly (`Pohyb_*`) zůstávají samostatné a mají vlastní dosahy.

Rozbor glb pro představu (blízká verze, jen 8 budov, bez věží a sklepa): A 41–72 tis. troj. z 289 tis., B 11–23 tis.
ze 180 tis. Ve vnitřku převažují materiály `prkno_ven`, `dub`, `zelezo`, `kvadr_okno` (ostění, výklenky), `zdivo`,
`kvadr`, `prkna_ven`, `tma` (popel ohniště).

### 3.2 Kolik uzlů
- `hrad_A`, `hrad_B` → `hrad_A_Vnejsek` + `hrad_A_Vnitrek_<id>` pro každou budovu, věž a sklep. Vnitřní uzel mívá
  5–10 materiálů, takže zblízka přibude několik kreslení. Z dálky ubude celý vnitřek a všechny jeho povrchy.
- Vnějšek **nedělit na čtverce**: hrad měří asi 70 m a dva kusy nic neořežou. Havranovo dělení na čtverce bylo pro
  sítě přes celou mapu.
- Vnitřek po budovách splní tři věci najednou: `visibility_range` se měří ke středu své budovy (kap. 2.3), frustum ořez
  zafunguje, a limit 8 světel platí pro jednu budovu, ne pro celý hrad.

### 3.3 Na jakou vzdálenost kreslit (data `hrad_vzhled.json lod.vnitrek`)
| Uzel | Konec kreslení | Proč |
|---|---|---|
| Vnitřek budovy nebo věže | `r + pruhled_m`, kde r je půl úhlopříčky AABB (budovy 4–13 m) a `pruhled_m` 25 m, okraj 5 m, `FADE_DISABLED`, bez stínu | Havran: interiér zvenku do 12 m od otvoru, domy vsi 35 m od středu. 25 m od líce stačí na průhled dveřmi přes celé nádvoří A (rozměr ověřit snímkem). Dál je vidět jen tma |
| Sklep | `r + 10 m`, bez stínu | Vidět jen ze schodů do sklepa (Warhorse KM-A-51: malá dohlednost) |
| Zátky oken a dveří (3.4) | od `konec vnitřku − okraj` do `daleko_od_m` | Kryjí otvor, když vnitřek nekreslíme |
| Daleká verze | od 60 m (beze změny) | – |

**Průhled branou:** průjezd je vnějšek, takže se kreslí vždy. Nádvoří za branou je vnějšek. Budova za branou se ve
vzdálenosti > r + 25 m ukáže zátkou (tmavé okno nebo dveře), což odpovídá referenci (KCD: dovnitř je vidět jen tma).
Kdyby měl hlídač námitky u konkrétního otvoru (velká vrata do sálu naproti bráně), přidat této budově `pruhled_m`
v datech, ne výjimku v kódu. Havranův portálový test (otvor v zorném poli a do 12 m) je druhá pojistka. Lze ho
zapojit později, až budou portály z `build/portaly.json`.

### 3.4 Daleká verze bez vnitřku a zátky otvorů (nejmenší riziko, převzít jako první)
Riziko záseku: žádné. Ubírá geometrii i materiály a nepřidává žádný uzel ani skript. Měřitelné bezpečně (rozbor glb,
hlídač scén, kreslení ze vsi).
- `stavba("_daleko")`: vnitřní funkce z 3.1 vůbec nevolat (sklep, podlahy, schody, nábytek, vnitřní příčky). Rozbor
  glb: −~10 tis. troj. z 71 tis. a ubude několik materiálů (dub, kvadr_schod, kvadr_sedy…). Kreslení: NEOVERENO.
- Zátka (Warhorse KM-A-46): obdélník `tma` 0,3 m za vnějším lícem v každém okně a dveřích s normálou ven. V daleké
  verzi napevno, v blízké jako vlastní uzel `hrad_*_Zatky` s `visibility_range_begin` (3.3). Funkce `tma` v
  `hrady.py` 68–70 a 406 už existuje (světlíky plných věží), stačí ji zavolat ve všech `kit.stone_window` a
  `kit.doorway` daleké verze. Platí pravidlo Míši: chyba v prvku, který mají všechny stavby, se opravuje ve společné
  funkci.

### 3.5 Stín hradu z daleké verze
Riziko záseku: malé. Stínová kopie používá materiály, které se už kreslí, a musí být předehřátá se stínem. U Havrana
naměřeno jen na PC (domy u rybníka −186 kreslení stínu), u nás změřit na úseku hradu.
- Jako Havran u domů (`_ves_domy`, „stín vrhá jen hrubý dům“): blízká verze `cast_shadow = OFF`, kopie daleké verze
  `SHADOWS_ONLY` do `stiny.dosah_m` (40 m). Stínový průchod u hradu klesne z 469 tis. troj. a 43 povrchů na 71 tis.
  a 28 povrchů. Po kroku 3.4 bude ještě méně.
- Riziko: samostín a „plovoucí“ stín, protože daleká verze je bez reliéfu (±5 cm) a bez prken. Warhorse KM-A-46 varuje:
  LOD nesmí být větší než LOD0. Ověřit snímkem zdi a nádvoří proti dnešku. Pokud nevyhoví, použít stínovou kopii
  blízkého vnějšku bez vnitřku a bez `zelezo`/`tma`.

### 3.6 Occlusion culling jako A/B (Havran ho má, Puchart ne) – jen měřit, nezavádět naslepo
Riziko záseku: stálá cena CPU (Embree rastr každý snímek, na Adrenu NEOV). Odkryté uzly za kopcem = první vykreslení.
Havranův přínos jen 0–46 kreslení (PC). Zavést jen tehdy, když A/B na tabletu ukáže zlepšení úseku vsi nebo hradu
o ≥ 5 % p95 a nepřibudou záseky > 40 ms.
- `hra/project.godot`: `rendering/occlusion_culling/use_occlusion_culling=true`.
- Okluzory podle Warhorse KM-A-47 a Havrana `_okluzory`:
  1. terén: `ArrayOccluder3D` z mřížky dlaždic, 0,8 m pod nejnižším bodem buňky (hřbet mezi hrady, svahy nad vsí);
  2. hradby a zdi budov: `BoxOccluder3D` z kolizních kvádrů zdiva (`hra/data/stavby_clony.json` už je, výška > 2 m,
     tloušťka > 0,3 m), **zúžené dovnitř tloušťky zdi**, aby v nich kamera nikdy nebyla (Havranův `OKL_DOMY` problém).
     Vnitřní příčky, podlahy a stropy okluzor nedostanou.
- Co to může ořezat: z nádvoří ves, les a byliny za hradbou, ze vsi vnitřky budov (po 3.2) a nádvoří.
- Havran ušetřil terénem 0–46 kreslení (PC). Zdi hradu a cena CPU na tabletu: NEOVERENO. Měřit variantou trasy
  (`hra/data/mereni.json`), stejně jako vrstvy lesa.

### 3.7 Další Havranovy techniky (jen po vlastním měření)
1. `_castice_lod` (částice za dosahem bez výpočtu): Havran NEOV (c4020a2 „ověřuje se“). U nás lze změřit bezpečně
   (CPU a skripty na úseku se loučemi, varianta s a bez).
2. `v_dome` pro domy míst (předměty uvnitř jen do 12 m): Havran NEOV. Je to jen `visibility_range`, bez skriptu.
   Změřit kreslení u domu.
3. **Nepřebírat bez samostatného měření:** skrývání krajiny uvnitř (`predmety._vnitrek`, doložený zdroj záseků
   0.93–0.99994, po opravě v rozpočtu 1 ms, zbývá podezření „2 s celý svět po vstupu“) a portály předmětů
   (`_interier`, tablet neměřen). Uvnitř hradu by dnešní les a byliny šly omezit spíš dosahem vrstev podle toho, jestli
   je hráč v budově (jedno přepnutí parametru vrstvy při vstupu, ne průchod stromem). To je NEOV, musí to ukázat
   měření.
4. Atlas a sloučení materiálů: až měření ukáže kreslení jako hrdlo.

### 3.8 Jak to ověřit
- **Rozbor glb (bez Godotu):** troj. a povrchy po uzlech `Vnejsek`/`Vnitrek_*`/`Zatky`, daleká verze s nulovým
  vnitřkem. Připsat do `ULOZENO` výpisu `hrady.uloz`.
- **Test smyslu (nový):** (a) každý trojúhelník `Vnitrek_<id>` leží v půdorysu `<id>` zúženém o t − 0,05 a pod
  okapem; (b) žádný trojúhelník vnějšku neleží v zúženém půdorysu pod podlahou patra (kromě schválených výjimek:
  průjezd); (c) každé okno a dveře daleké verze mají zátku (záznamy `portaly.ZAZNAM` + okna).
- **Hlídač scén:** kreslení a troj. u bodů ze vsi, z cest a z nádvoří před a po. **Změna obrazu při malém posunu**
  (už ji počítá) na hranicích `r + pruhled_m ± okraj`.
- **Snímky do otvorů (nový hlídač „vnitrek_hranice“):** pro každý otvor z `build/portaly.json` (místo, směr ven)
  vyfotit dvojici snímků po ose otvoru těsně před koncem dosahu a těsně za ním (`nastroje/foto_portaly.sh` umí
  fotit portály). Rozdíl pixelů v obdélníku otvoru musí být pod prahem, jinak je to doskakování. Snímky si nejdřív
  prohlédnout sám (pravidlo CLAUDE.md).
- **Test průchodu:** beze změny tras. Kolize zůstávají v `KOLIZE`, ale trasa uvnitř budov ukáže, jestli se vnitřek
  kreslí, když je hráč v budově (dosah ke středu budovy < r).
- **Záseky (z Havrana):** v měřicí trase úsek „vstup na nádvoří a do paláce“ ve dvou průchodech. Zásek > 40 ms jen
  v 1. průchodu = chybí předehřátí nového uzlu. V obou = obsah. Panel „záseky > 40 ms“ už existuje.
- **Tablet:** úsek hradu měřicí trasy (dnes p95 17 ms) a pohled ze vsi na hrad (kreslení, troj.). Jedna změna = jedno
  měření (3.4, 3.2–3.3, 3.5, 3.6 zvlášť).

## Zdroje
- Havran: `docs/rozpracovane/reserse_10_11_optimalizace_tablet.md`, `docs/ZAVER_tablet_grafika.md`, `docs/radce.md`
  (19. 10. 15:30–18:30, 0.59–0.62), `docs/PREHLED.md`, `docs/predani.md`, `docs/navrh_tabulek.md`,
  `docs/soupis/{blender,skripty,svet_a,svet_b,svet_c,shadery}.md`, `docs/rozpracovane/warhorse_do_dat.md`,
  `pravidla/svet/rozpocty.json`, `scripts/predmety.gd`, `scripts/portaly.gd`, `scripts/svet.gd` (`_okluzory`,
  `_ves_domy`, `v_dome`, `_rozdel_site`), `scripts/life.gd` (`_castice_lod`), `blender/ves_domy.py`, commity c4020a2 a 07ad712; měření a záseky:
  `docs/mereni_verze.md`, `docs/stav_historie.md`, `docs/rozpracovane/misa_28_chyby.md` (ř. 75, 90, 130).
- [Godot: Occlusion culling](https://docs.godotengine.org/en/stable/tutorials/3d/occlusion_culling.html)
- [Godot: Overview of renderers](https://docs.godotengine.org/en/stable/tutorials/rendering/renderers.html)
- [Godot: modules/raycast/config.py (Embree, arm64)](https://github.com/godotengine/godot/blob/master/modules/raycast/config.py)
- [Godot: Visibility ranges (HLOD)](https://docs.godotengine.org/en/stable/tutorials/3d/visibility_ranges.html)
- [Godot: Lights and shadows (8 světel na síť v Compatibility)](https://docs.godotengine.org/en/stable/tutorials/3d/lights_and_shadows.html)
- [Godot 3.4: Introduction to Rooms and Portals](https://docs.godotengine.org/en/3.4/tutorials/3d/portals/introduction_to_rooms_and_portals.html)
- [CryEngine 3: VisArea and Portals](https://www.cryengine.com/docs/static/engines/cryengine-3/categories/1114113/pages/1048727)
- [CryEngine 3: Culling Explained](https://www.cryengine.com/docs/static/engines/cryengine-3/categories/1638401/pages/1605709)
- [Unreal Engine: Hierarchical Level of Detail](https://dev.epicgames.com/documentation/unreal-engine/hierarchical-level-of-detail-in-unreal-engine)
- Warhorse knowledge base KCD2 (warhorse.youtrack.cloud, KM-A-46/47/49/51) – citace přes Havranův `warhorse_do_dat.md`.
