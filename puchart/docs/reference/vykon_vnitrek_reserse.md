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
   Godotu mu dává za pravdu (kap. 2).
5. Návrh (kap. 3): v Blenderu dát vnitřek každé budovy a věže do vlastního uzlu `*_Vnitrek_<budova>`, který se kreslí
   do vzdálenosti „poloměr budovy + 25 m“. Z daleké verze vnitřek úplně vyndat a okna i dveře zevnitř zakrýt tmavou
   zátkou (Warhorse). Stín hradu brát z daleké verze. Occlusion culling vyzkoušet jako A/B. Každý krok hlídat
   hlídačem scén (změna obrazu na hranici dosahu) a snímky do otvorů ze `build/portaly.json`.

Pozn.: v datech je `hrad_vzhled.json lod.daleko_od_m = 60` (výchozí hodnota v kódu `hlavni.gd` je 120). Hrad se tedy
přepíná na dálkovou verzi už u 60 m.

## 1. Havranovy techniky a stav v Puchartu

Zdroj: větev `origin/claude/new-session-0dtk58` (čteno přes `git show`). Puchart: `hra/scripts/*.gd`,
`pravidla/svet/rozpocty.json`, `hra/project.godot`, `blender/`.

| # | Technika | Havran soubor | Puchart má? | Doporučení |
|---|---|---|---|---|
| 1 | **Místnosti s portály** (okna/dveře jako obdélníky). Předměty místnosti se kreslí, jen když je hráč v ní, v sousední místnosti s otevřenými dveřmi, nebo venku do 12 m a otvor je v zorném poli. Vyhodnocení 5× za sekundu | `scripts/predmety.gd` `_interier`, `scripts/portaly.gd`; `docs/radce.md` 19. 10. 15:30 | **NE.** Kód je zkopírovaný beze změny, ale `portaly.gd` má natvrdo rozměry Havranovy tvrze a `hv_most.gd` říká „portály v Puchartu vypnuto“ (`world = null`). Hrad portály nemá | Převzít, až budou v hradu předměty. Portály plnit z `build/portaly.json` (Blender je už zapisuje: místo, směr ven, rozměr), ne natvrdo |
| 2 | **Skrývání krajiny, když je hráč uvnitř.** Režim 1 (vidí okno nebo dveře do 10 m): skryje vše dál než 80 m. Režim 2 (zavřená místnost): vše dál než 25 m, i impostory a cizí terén. Průchod stromem 1 ms za snímek, zúžení až po 2 s ustáleného stavu, rozšíření hned | `predmety.gd` `_vnitrek`, `_vnitrek_krok`; `rozpocty.json predmety_vnitrek` (měřeno 15–26 → 1–1,75 ms) | **NE** (kód je, ale vypnutý: `world = null`) | Až budou místnosti hradu jako data. Uvnitř věží a paláce se teď kreslí les i louka za zdmi. Přínos jen uvnitř, NEOVERENO |
| 3 | **Louka uvnitř budovy jen do 20 m** (`louka.vnitrek`) | `scripts/louka.gd` (soupis skripty.md ř. 58) | NE | Spolu s bodem 2 (byliny.gd, les.gd) |
| 4 | **Interiér zvenku jen do 12 m** (dřív 25 m). Hostinec: nábytek 0,4 M troj. okny z dálky, „z dálky je okny vidět jen tma“ | `predmety.gd` (0.62), `radce.md` 0.62 | NE | Vzdálenost pro vnitřek hradu (kap. 3.3) |
| 5 | **Předměty uvnitř domů vsi jen do 12 m** (`svet.v_dome`, `ves_vnitrek.do_m`). Commit c4020a2 | `scripts/svet.gd` `v_dome`, `predmety.gd` spawn | **Částečně.** Dosah předmětů podle velikosti (20/40/80 m) ano, test „uvnitř domu“ ne | Převzít `v_dome` pro domy míst a pro budovy hradu (`stavby_pudorysy.json`) |
| 6 | **Drobné a vnitřní díly tvrze do 200 m** podle předpony jména (Sklep, KuchyneOhniste, Sin, Pohyb_*, SchodyHradba, Studna…) | `svet.gd` build, `rozpocty.json tvrz_drobne`; c4020a2 | **NE pro hrad**, protože hrad je jedna síť a není co pojmenovat. Pohyblivé díly ano (`rozpocty.json pohyblive_dily`, `dvere.gd`) | Hlavní úkol: rozdělit síť hradu (kap. 3) |
| 7 | **Dosah předmětu podle velikosti** (20/40/80 m, lomová stěna 160) | `predmety.gd` spawn | ANO (převzato) | – |
| 8 | **LOD domů ve třech stupních**: podrobný, střední (1 materiál, barva vrcholu), `_Daleko` (konvexní obal, 2 materiály). `lod_bias`, aby automatický LOD nerozpustil šindele | `svet.gd` `_ves_domy`, `blender/ves_domy.py`, `ves_domy_lod.py` | ANO (`hlavni.gd _mista`, `ves.gd`) | – |
| 9 | **Vnitřek domu (`*Interier`) jen do 35 m, bez stínu. Drobnosti (`*Drobne`) do 70 m** | `svet.gd` `_ves_domy` | ANO u domů míst (`vnitrek_do_m`). **NE u hradu** | Totéž pro hrad (kap. 3) |
| 10 | **Stín jen z hrubé verze**: kopie `_Daleko` jako `SHADOWS_ONLY`, podrobná verze stín nevrhá (u rybníka ubylo 186 kreslení stínu) | `svet.gd` `_ves_domy` (0.92) | ANO u domů. **NE u hradu**: plná síť vrhá stín se všemi 25+18 povrchy, `rozpocty.json hrad_shadow_meshes: false` | Stín hradu z `puchart_daleko.glb` (kap. 3.5) |
| 11 | **Occlusion culling**: terén jako `ArrayOccluder3D` (mřížka 12 m, 0,8 m pod terénem), krabice domů (`BoxOccluder3D`, zmenšené, u hráče se vypínají: `okluzory_u_hrace`), remízky, nitro lesa; `use_occlusion_culling = true` | `svet.gd` `_okluzory` (ř. ~8383), `main.gd` 2127, `project.godot` ř. 58; soupis `svet_b.md` 307–312 | **NE.** `hra/project.godot` nastavení nemá. Puchart (a Havran 13. 11.) píše „Compatibility nemá occlusion culling“, to je omyl | A/B test (kap. 3.6). Havran ušetřil terénem 0–46 kreslení (PC), přínos zdí hradu NEOVERENO |
| 12 | **Velké sloučené sítě rozdělit na čtverce** (> 60 m a > 8000 troj., čtverce 128–640 m), aby je šlo ořezat pohledem. Terén se kvůli dírám nedělí | `svet.gd` `_rozdel_site` (0.60–0.62) | Terén ano (dlaždice z Blenderu). **Hrad NE** (dvě sítě ~70 m) | Hrad dělit podle budov a věží, ne na čtverce (kap. 3.2) |
| 13 | **Poučení: `ImporterMesh.generate_lods` za běhu vrací 0 úrovní.** LOD jen offline z Blenderu | `radce.md` 0.62 (oprava zápisu 0.60) | ANO (daleká verze se peče v Blenderu) | – |
| 14 | **Impostory stromů** (hemi-oktaedr 8×8, atlas 1024, od 30–50 m do 900 m, buňka 1024 m) | `blender/impostory.py`, `svet.gd` `_impostory`, `shaders/impostor.gdshader` | ANO (`blender/impostory.py`, `les.gd`) | – |
| 15 | **Mizení trávy po trsech ditherem a „kupy“ jako impostor trávy** (CryEngine merged meshes) | `louka.gd`, `radce.md` 19. 10. 07:30 | Částečně (`byliny.gd`: buňky, předstih, zánik) | Mimo téma hradu |
| 16 | **Částice jen do dosahu, dál neviditelné a bez výpočtu** (`PROCESS_MODE_DISABLED`; plamen 60 m, kouř 250 m) | `life.gd` `_castice_lod`, `rozpocty.json castice`; c4020a2 | Částečně: plamen louče `visibility_range_end = 40`, výpočet CPU částic dál běží (NEOVERENO) | Převzít `_castice_lod` (levné, louče jsou ve věžích a ve sklepě) |
| 17 | **Pohyblivé díly do dosahu** | (Havran podle Míši „maluje celý hrad i s vnitřkem“) | ANO od 13. 11. (`pohyblive_dily`, `dvere.gd`) | – |
| 18 | **Warhorse KM-A-46: v LOD1 smazat celý vnitřek a místo něj černá výplň** (vrcholová barva 0), aspoň 30 cm za vnější zdí, zakryje okna a dveře, normály dovnitř. Stejně v LOD2 | `docs/rozpracovane/warhorse_do_dat.md` 1.2 | Částečně: materiál `tma` jako „tmavý světlík“ v oknech plných věží (`hrady.py` 406–432, 68–70). Daleká verze vnitřek má | **Převzít** pro dálkovou verzi a pro blízkou verzi bez vnitřku (kap. 3.4) |
| 19 | **Warhorse KM-A-51: složitý interiér (sklep) jako zvláštní model s malou dohledností.** U nepřístupných domů vnitřek smazat, smazat neviditelné trámy ve zdi | `warhorse_do_dat.md` 1.2 | Neviditelné plochy ano (`hrady.odstran_vnitrni_cela`). Sklep jako zvláštní díl ne | Sklep = vlastní uzel s nejkratším dosahem |
| 20 | **Warhorse KM-A-47: okluzor co nejlehčí** („blízko jednocifernému počtu trojúhelníků“), z rovin, vnější zdi z obou stran, vnitřní zdi, podlahy a stropy bez okluzoru | `warhorse_do_dat.md` 1.4 | NE | Okluzory zdí hradu z kolizních kvádrů (kap. 3.6) |
| 21 | **Warhorse KM-A-49: stínová proxy** – jeden materiál, bez alfa dílů, jen pro LOD0 a LOD1 | `warhorse_do_dat.md` 1.3 | NE (hrad) | Kap. 3.5 |
| 22 | **Warhorse KM-A-46: pořadí cílů LOD** – 1. méně kreslení (materiálů), 2. stejný vzhled bez samostínu, 3. jednodušší shader, 4. až pak trojúhelníky | `warhorse_do_dat.md` 1.2 | Daleká verze: A 18 povrchů, B 10 (z 25/18), tedy jen částečně | Daleká verze bez vnitřku ztratí další materiály (dub, kvadr_schod, kvadr_sedy…) |
| 23 | **Atlasy a sloučení materiálů staveb** (cíl < 400 kreslení) | `docs/ZAVER_tablet_grafika.md` §3.7; rešerše 10. 11. bod 4 („nezavedeno“) | NE | Až když měření ukáže kreslení jako hrdlo (dnes ne) |
| 24 | **Bez průhledného prolínání** (`fade` jen Disabled, okraj proti blikání) | PREHLED §6, `svet.gd` | ANO (hrad FADE_DISABLED, `Pravidla.fade_dosahu`) | – |
| 25 | **Zapečené AO / tmavší vnitřek** | radce K4, ZAVER §3 | ANO (`hrady.zapec_ao`) | – |
| 26 | **Rozpad, co se kreslí** (`TVRZ_ROZPAD`, `tools/rozbor_tvrze.gd`: síť po síti troj. a kreslení) | `radce.md` 0.59–0.60 | Částečně (hlídač scén: kreslení a troj. na snímek, bez rozpadu po uzlech) | Po rozdělení hradu přidat rozpad po uzlech `Vnejsek` / `Vnitrek_*` |
| 27 | **Tabulka tříd** (dosah, LOD1, impostor, stín, kolize, načítání, portál: „tvrz – LOD čtverce – portál“) | `docs/navrh_tabulek.md` tab. 3 | Částečně (dosahy v `rozpocty.json`, `mista_stavby.json lod`) | Vnitřek hradu zapsat jako třídu/řádek v datech, ne číslem v kódu |
| 28 | **Krabicové okluzory domů vypnuté** (`OKL_DOMY = false`), protože kamera uvnitř krabice zakryje vše. Řešení: zmenšit a u hráče vypnout | `svet.gd` 7170, 8431–8433 | NE | Okluzor zdi hradu ležet uvnitř tloušťky zdi, aby kamera nikdy nebyla uvnitř |

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

Seřazeno podle poměru přínos/riziko. Každý krok je samostatný: jedna změna, jedno měření (pravidlo rádce 21. 10.),
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
- `stavba("_daleko")`: vnitřní funkce z 3.1 vůbec nevolat (sklep, podlahy, schody, nábytek, vnitřní příčky). Rozbor
  glb: −~10 tis. troj. z 71 tis. a ubude několik materiálů (dub, kvadr_schod, kvadr_sedy…). Kreslení: NEOVERENO.
- Zátka (Warhorse KM-A-46): obdélník `tma` 0,3 m za vnějším lícem v každém okně a dveřích s normálou ven. V daleké
  verzi napevno, v blízké jako vlastní uzel `hrad_*_Zatky` s `visibility_range_begin` (3.3). Funkce `tma` v
  `hrady.py` 68–70 a 406 už existuje (světlíky plných věží), stačí ji zavolat ve všech `kit.stone_window` a
  `kit.doorway` daleké verze. Platí pravidlo Míši: chyba v prvku, který mají všechny stavby, se opravuje ve společné
  funkci.

### 3.5 Stín hradu z daleké verze
- Jako Havran u domů (`_ves_domy`, „stín vrhá jen hrubý dům“): blízká verze `cast_shadow = OFF`, kopie daleké verze
  `SHADOWS_ONLY` do `stiny.dosah_m` (40 m). Stínový průchod u hradu klesne z 469 tis. troj. a 43 povrchů na 71 tis.
  a 28 povrchů. Po kroku 3.4 bude ještě méně.
- Riziko: samostín a „plovoucí“ stín, protože daleká verze je bez reliéfu (±5 cm) a bez prken. Warhorse KM-A-46 varuje:
  LOD nesmí být větší než LOD0. Ověřit snímkem zdi a nádvoří proti dnešku. Pokud nevyhoví, použít stínovou kopii
  blízkého vnějšku bez vnitřku a bez `zelezo`/`tma`.

### 3.6 Occlusion culling jako A/B (Havran ho má, Puchart ne)
- `hra/project.godot`: `rendering/occlusion_culling/use_occlusion_culling=true`.
- Okluzory podle Warhorse KM-A-47 a Havrana `_okluzory`:
  1. terén: `ArrayOccluder3D` z mřížky dlaždic, 0,8 m pod nejnižším bodem buňky (hřbet mezi hrady, svahy nad vsí);
  2. hradby a zdi budov: `BoxOccluder3D` z kolizních kvádrů zdiva (`hra/data/stavby_clony.json` už je, výška > 2 m,
     tloušťka > 0,3 m), **zúžené dovnitř tloušťky zdi**, aby v nich kamera nikdy nebyla (Havranův `OKL_DOMY` problém).
     Vnitřní příčky, podlahy a stropy okluzor nedostanou.
- Co to může ořezat: z nádvoří ves, les a byliny za hradbou, ze vsi vnitřky budov (po 3.2) a nádvoří.
- Havran ušetřil terénem 0–46 kreslení (PC). Zdi hradu a cena CPU na tabletu: NEOVERENO. Měřit variantou trasy
  (`hra/data/mereni.json`), stejně jako vrstvy lesa.

### 3.7 Další Havranovy techniky k převzetí (pozdější pořadí)
1. `_castice_lod` (částice za dosahem bez výpočtu): malé, levné, louče ve věžích.
2. Skrývání krajiny uvnitř (`predmety._vnitrek`, kód v Puchartu už je): zapojit, až budou místnosti hradu jako data.
   `main.world` = kořen světa, místnosti z VNITRKY (3.1), portály z `build/portaly.json` místo natvrdo psaného
   `portaly._tvrz`.
3. Portály předmětů místností (`_interier`): až bude hrad vybavený předměty.
4. `v_dome` pro domy míst: předměty uvnitř jen do 12 m (Havran c4020a2).
5. Atlas a sloučení materiálů: až měření ukáže kreslení jako hrdlo.

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
- **Tablet:** úsek hradu měřicí trasy (dnes p95 17 ms) a pohled ze vsi na hrad (kreslení, troj.). Jedna změna = jedno
  měření (3.4, 3.2–3.3, 3.5, 3.6 zvlášť).

## Zdroje
- Havran: `docs/rozpracovane/reserse_10_11_optimalizace_tablet.md`, `docs/ZAVER_tablet_grafika.md`, `docs/radce.md`
  (19. 10. 15:30–18:30, 0.59–0.62), `docs/PREHLED.md`, `docs/predani.md`, `docs/navrh_tabulek.md`,
  `docs/soupis/{blender,skripty,svet_a,svet_b,svet_c,shadery}.md`, `docs/rozpracovane/warhorse_do_dat.md`,
  `pravidla/svet/rozpocty.json`, `scripts/predmety.gd`, `scripts/portaly.gd`, `scripts/svet.gd` (`_okluzory`,
  `_ves_domy`, `v_dome`, `_rozdel_site`), `scripts/life.gd` (`_castice_lod`), `blender/ves_domy.py`, commit c4020a2.
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
