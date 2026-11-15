# Scény podle KCD: remízky, křoví a vzdálený les jako hmota (15. 11. 17:45, rozbor a plán)

Zadání Míši 15. 11.: vrátit plán scén. Výhled má přirozeně zavírat remízek nebo křoví. Vzdálený les se má kreslit
jako jedna levná hmota korun, jako v KCD (Míša poslala i fotku z jiné testovací hry).
Tento dokument je jen rozbor a plán. Kód, pravidla ani nástroje se tu neměnily.

**Proč (NAMĚŘENO):** `docs/mereni_verze.md`, blok „0.999998 – Měřicí trasa 15. 11. 17:28“. Úsek **ves-vjezd** je
nejhorší ve všech variantách (p50 36/43/28/39 ms). Kreslí se v něm 810 volání a 2,28 mil. trojúhelníků, asi dvakrát víc
než u mlýna (320 / 1,07). Varianta `bez_vnitrku` nepomáhá (43 ms) a skripty berou jen 8–9 ms. Cenu tedy dělá množství
kresleného v záběru. Které skupiny to jsou, zatím **NEZMĚŘENO**.

Navazuje na `docs/rozpracovane/zadani_sceny_2_11.md` (zadání 2. 11.) a `docs/rozpracovane/kompozice_mapy.md`
(Astra 29. 10.). Nejde o druhý systém: všechno níže rozšiřuje `lokace.json kompozice`, `svet._okluzory`,
`svet._impostory` a měřicí trasu.

---

## 1. Co ukazují předlohy KCD (prohlédnuto všech 74 snímků, Read)

Prohlédnuté snímky: `docs/screens/kcd1/` (50), `docs/screens/ref_kcd2_*` (11), `docs/reference/kcd_13_11/` (8),
`docs/reference/sceny_3_11/` (4), `docs/screens/misa_9_11/18_kcd_les.png`. Míšiny složky `misa_6_11`, `misa_9_11`,
`misa_10_11` a `misa_15_11` jsou všechny z **naší** hry (prohlédnuto, viz konec tabulky).
Fotka z cizí testovací hry v repu **není**. Na Disku je od dnešního rána `Forest100-Vulkan-2.5.apk`
(id `1jmw5DCtjN1bzTkKh9l4YgEOkvQpS60Vb`). Je to nejspíš ta hra (NEOVĚŘENO, neotevřeno). Pozor: běží na Vulkanu, který
na našem tabletu v Godotu 4.4.1 padá (`reserse_10_11_optimalizace_tablet.md`).

Sloupce: **zavírá výhled** = co ukončí dlouhý pohled · **dálka** = jak vypadá vzdálený les · **vjezd/ves** = jak je
orámovaný příchod.

| snímek | zavírá výhled | dálka | vjezd / ves |
|---|---|---|---|
| kcd1_01 | zatáčka cesty kolem kopce, kamenná mez, keře na svahu | lesnaté svahy jako souvislá tmavá hmota, jednotlivé koruny jen na hraně; údolí modře zamlžené ve 2–3 vrstvách | cesta stoupá k chalupě, chalupa schovaná za korunami |
| kcd1_02 | terénní zlom (svah), keře u cesty | celé údolí = hmota lesa, siluety korun jen na hřebeni; opar zesvětluje a namodrá | – |
| kcd1_03 | rameno kopce, solitérní strom, snos kamení | kopec za loukou = tmavozelená hmota; vzdálené kopce šedomodré | – |
| kcd1_05 | velký keř vlevo (rám), svah | horizont = stěna lesa, koruny splývají | – |
| kcd1_06, _10 | palisáda, ploty a zdi uličky | – | ulička uzavřená, výhled jen na střechy |
| kcd1_09 | zeď a palisáda | kopec za ní = hmota se zamlžením | – |
| kcd1_14 | hustý keř po obou stranách cesty před branou | – | brána orámovaná křovím, za ní nic dalšího |
| kcd1_15 | úvoz: zářez cesty s keři na obou březích, zatáčka nahoru | – | – |
| kcd1_16 | křoví a plot u cesty, hřbet kopce | – | hrad se ukáže až nad hřbetem |
| kcd1_18 | skalní svah s jednotlivými keři, bříza | – | – |
| kcd1_19 | vrata dvora, plot, keře | kopec za vsí: blízké koruny jednotlivě, dál hmota | ves z ulice: dvorce a vrata |
| kcd1_20 | proutěný plot a keř po stranách, domy | – | ulice se táhne, pohled končí u hradu (dominanta) |
| kcd1_21 | husté křoví kolem potoka a lávky | les za loukou: hmota, opar | domy za křovím u potoka, vidět jen střechy |
| kcd1_23 | domy a stodoly kolem návsi | vzdálené kopce: sady a meze jako drobné skvrny v oparu | náves uzavřená budovami |
| kcd1_24, _25 | proutěný plot, ovocný strom, ohyb pěšiny | konec pohledu = okraj lesa | pěšina podél plotu, ves se odkrývá postupně |
| kcd1_26 | proutěný plot, rákos, vysoká tráva | – | – |
| kcd1_28 | – (panorama z výšky) | **les na kopcích = souvislá hmota**, okraje s hrbolky korun, tmavší než louky; opar jen mírný | ves z výšky celá (záměrný výhled C) |
| kcd1_29–38 | les: podrost a mladé stromy zavřou pohled po 30–50 m; potok s křovím (36) | – | – |
| kcd1_04, _07, _08, _11–13, _17, _22, _27, _39–41, drevo_* | blízké detaily, interiéry, dvory | – | (bez vztahu ke scénám) |
| kcd1_42 | proutěný plot, stromy nad chalupami | – | tábor/ves zavřený plotem a stromy |
| ves_1 | laťkový plot, keře, stodola | rovina k horizontu: nízký pruh lesa ve světlém oparu | plot dvora podél cesty |
| ves_2 | stěna smrkového lesa za statkem | les jako souvislá stěna | statek u lesa |
| ves_3 | domy kolem návsi | svah za vsí: hmota lesa s mýtinami | – |
| ves_4 | proutěný plot, solitérní strom | horizont: plochý pruh lesa, namodralý | ves za loukou a plotem, jen střechy |
| ves_5 (malý) | – (pohled shora) | – | ves ze svahu, cesta se stáčí |
| ves_6 | zatáčka cesty, domy, vrby | les na svahu = hmota | **vjezd: cesta mezi kůlnami se stáčí, výhled končí u dvou domů a lesa** |
| ref_kcd2_cesta_k_hradu | zídka, plot, stromy u cesty | – | cesta podél plotu, ves pod ní |
| ref_kcd2_cesta_les | okraj lesa (keře a mladé stromy) | horizont daleko, les = plochý namodralý pruh | – |
| ref_kcd2_chalupa_vecer | ovocný strom a plot | hrad na obzoru | chalupa za sadem |
| ref_kcd2_dvur_zed | kamenná zeď dvora | – | – |
| ref_kcd2_louka_les | **okraj lesa = souvislá zelená stěna z keřů a mladých stromů** | – | – |
| ref_kcd2_ves_plot_cesta | **plot, keře a ovocné stromy u cesty kryjí domy** | – | **vjezd: cesta podél plotu, domy za keři a sadem, ves se otevírá až po ohybu** |
| ref_kcd2_ves_rybnik | rákos a keře u vody, stromy mezi domy | – | – |
| ref_kcd2_ves_shora | stromořadí a meze mezi poli | **obzor = tenký tmavý pruh lesa** s hrbolky korun, mírně namodralý; bližší les jako tmavé skvrny | ves v rovině, kolem pásy stromů a sadů |
| ref_kcd2_ves_ulice | ohyb ulice, stromy mezi domy | – | ulice končí stromy |
| ref_kcd2_vez_skala | – (výhled) | krajina daleko: lesy jako tmavé skvrny s měkkým okrajem v modrém oparu | – |
| ref_kcd2_zahrada_plot | proutěný plot zahrady, stromy | – | – |
| kcd_13_11 mlyn_kcd1 | keře u vody, padlý kmen | smrkový les za mlýnem = stěna | – |
| kcd_13_11 ves_kcd1, ves_mesto | domy po obou stranách | – | ulice uzavřená domy |
| kcd_13_11 boj, dialogy, kovar, kovarna | (bez vztahu ke scénám) | – | – |
| sceny_3_11/1_lesni_cesta (KCD2) | okraj lesa vlevo (keře, mladé stromy) | **les na obzoru = vodorovný pruh korun** v modrošedém oparu | cesta podél lesa ven do krajiny |
| sceny_3_11/2_okraj_lesa (foto) | stromořadí a meze | lesy ve 3 vrstvách oparu, nejvzdálenější jen silueta | ves za loukou mezi stromy, odhalená z návrší |
| sceny_3_11/3_vesnice (KCD2) | ohyb cesty, stromy mezi domy | – | ulice se stáčí, vidět 4–5 domů |
| sceny_3_11/4_vyhlidka (AI) | – | (jen nálada) | – |
| misa_9_11/18_kcd_les | borový les, rozmazané | – | – |
| **naše:** misa_15_11/17, _18; misa_9_11/05, _07 | – | **vzdálený les u nás = jednotlivé světle zelené kužele a koule v řadách**, mezi nimi louka; jasnější než blízko, bez tmavé hmoty | ves z výšky (18): celá ves odkrytá |
| **naše:** misa_15_11/09, _13, _16 (panel) | – | – | ve vsi 794–1 056 volání / 2,56–3,13 mil. prim. (NAMĚŘENO v panelu) |

**Vzory z předloh (shrnutí):**
1. **Výhled zavírá nejčastěji vegetace u cesty**: keř, plot s keři, ovocný strom nebo okraj lesa z keřů a mladých
   stromů. Jen zřídka to je pevná stavba. Pevný tvar (terénní zlom, úvoz, zeď, stodola) bývá druhá vrstva.
2. **Vjezd do vsi** (ves_6, ref_kcd2_ves_plot_cesta, sceny_3_11/3, kcd1_24/25): cesta se stáčí podél plotu, domy jsou
   schované za keři a sadem a odkrývají se po jednom. Celou ves je vidět jen z návrší (kcd1_28, ves_shora). Je to
   záměrný výhled, ne vjezd.
3. **Vzdálený les je hmota**: od zhruba několika set metrů je to souvislá tmavší plocha. Hrbolky korun jsou jen na horní
   hraně a na okraji porostu. Barva je tmavší a modřejší než louka a se vzdáleností přechází do oparu. Jednotlivé
   stromy jsou vidět jen na okraji a jako solitéry. U nás je to opačně: řady jednotlivých světlých impostorů.
4. Opar dělá hloubku ve vrstvách, ale nezakrývá chyby (souhlas se zadáním 2. 11. bod 7).

---

## 2. Rešerše: jak to dělá KCD / CryEngine a co umí Godot 4 Compatibility

### KCD / CryEngine
- **Veřejná přednáška Warhorse o vegetaci nebo LOD lesa nenalezena** (hledáno: GDC, Digital Dragons, Game Access,
  modding wiki). Vše o KCD níže je z dokumentace CryEngine nebo z komunity, tedy **NEOVĚŘENO pro KCD samotné**.
- CryEngine má pro husté porosty **Merged Meshes**: sloučené instance vegetace s vlastním dosahem
  ([CRYENGINE docs – Vegetation 02 Grass (Merged Meshes)](https://www.cryengine.com/docs/static/engines/cryengine-5/categories/23756816/pages/24285889)).
  Vzdálené stromy mají v CryEngine 3 **sprity s nastavitelnou vzdáleností** (sprite distance ratio). Doskakování se
  ladí poměry vzdáleností
  ([CRYENGINE 3 – Optimizing Vegetation Assets](https://www.cryengine.com/docs/static/engines/cryengine-3/categories/1114113/pages/1310885)).
- KCD/KCD2 má proměnné `e_ViewDistRatioVegetation` a `e_MergedMeshesViewDistRatio` (dosah vegetace). Pochází to
  z hráčských a modových stránek
  ([Nexus KCD2 mod 1211](https://www.nexusmods.com/kingdomcomedeliverance2/mods/1211),
  [Steam KCD](https://steamcommunity.com/app/379430/discussions/0/2860219962081819052/)) – NEOVĚŘENO.
- Hráči KCD2 píšou o přechodu „render trees → **HLod trees**“. Při běžném pohledu stromy HLOD „splývají v homogenní
  hmotu“ ([Nexus KCD2 mod 897, příspěvky](https://www.nexusmods.com/kingdomcomedeliverance2/mods/897?tab=posts) – podle
  úryvku z vyhledávání, stránka sama vrací 403). Shoduje se to s tím, co je vidět na snímcích (vzor 3). Že KCD2 kreslí
  vzdálený les jako sloučenou HLOD hmotu, je ale **NEOVĚŘENO** z primárního zdroje.
- Předchozí rešerše projektu (`reserse_10_11_optimalizace_tablet.md`): KCD drží vzhled hlavně světlem a velkoplošným
  zastíněním. Switch port ubral rozlišení, textury a stíny drobností, **vzdálené siluety ponechal**. Recenzenty
  na Steam Decku ruší hlavně doskakování.

### Jiné hry (ověřitelný primární zdroj)
- **Serious Sam 4** (Croteam, GDC 2019, [slajdy GPUOpen](https://gpuopen.com/gdc-presentations/2019/gdc-2019-agtd2-4-million-acres-serious-sam-4.pdf);
  PDF staženo a přečteno):
  - Vegetace má vrstvy: holý terén → **forest imposters** → blízké stromy → rostliny → tráva.
  - Impostory jsou v **blocích 1 km** (asi 16 000 stromů, mřížka ~8 m, každý strom 2 trojúhelníky, předgenerované
    čtverce). Textury mají 8 směrů a prolínají se 2 nejbližší.
  - **„Far forest: splatted into terrain at distance beyond forest imposters“**: za dosahem impostorů je les jen
    barvou terénu.
  - Hranice přechodu: „fade-out vegetation map“.

  → Náš systém už je skoro stejný: impostory v buňkách 1024 m (`svet.IMP_BUNKA`), obzor 2 500 m a les ze šumu
  v `zem.gdshader`. Chybí mezivrstva „hmota“ mezi impostory a barvou terénu a dnes nemáme tmavou barvu porostu.
- Procedurální „faraway forest“ (Procworld 2012, [blog](https://procworld.blogspot.com/2012/04/faraway-forest.html)):
  - V dálce zůstanou jen „puffs“ korun, les splyne s terénem.
  - Autor varuje, že **přechod mezi blízkým LOD a hmotou je problém**, pokud hmota netvoří tvar ze skutečných korun.

  → Hmota se musí stavět ze skutečných poloh a velikostí stromů, ne ze šumu.

### Godot 4 (4.4.1, Compatibility/GLES3)
- **OccluderInstance3D:**
  - Okluze běží na CPU (Embree, rastr v nízkém rozlišení). Dokumentace zmiňuje jen Forward+ a Mobile
    ([Occlusion culling](https://docs.godotengine.org/en/stable/tutorials/3d/occlusion_culling.html)).
  - V našem projektu okluze v Compatibility funguje: okluzor terénu ušetřil na PC 0–46 volání
    (`reserse_10_11_optimalizace_tablet.md`), tedy **málo**.
  - Dokumentace: velké okluzory (zdi) účinkují víc než malé. Pečou se jen neprůhledné sítě. MultiMesh se nepeče, tvar
    okluzoru se musí udělat ručně. Pohyb okluzoru je drahý, **přepnutí viditelnosti levné** (náš `okluzory_u_hrace`
    přepíná viditelnost, to je správně).
- **Visibility range:**
  - Hystereze je v okrajích (margins), když je prolínání vypnuté. Prolínání se dělá jen průhledností nebo ditherem
    ve vlastním materiálu ([Visibility ranges](https://docs.godotengine.org/en/stable/tutorials/3d/visibility_ranges.html)).
  - Projekt už změřil, že prolínání v Compatibility 4.4.1 se nekreslí. Režimy Self/Dependencies se tam chovají jako
    vypnuté, **bez hystereze** (`reserse_10_11_optimalizace_tablet.md`).

  → **Přechod dělat ditherem v shaderu** (bez průhlednosti, bez screen texture). Přesně tak už to dělá
  `shaders/impostor.gdshader`: náhodný práh na strom (`prah`) a discard podle `viditelnost`.
- **MultiMesh:** viditelnost se řídí jen za celou instanci uzlu (buňku), ne za kus. Prostorové dělení (buňky) a vlastní
  AABB už máme (`_impostory`: `custom_aabb`, poloha v `INSTANCE_CUSTOM`).
- **Sloučená vzdálená síť (HLOD):**
  - Godot doporučuje nahradit skupinu objektů jednou větší sítí ve vzdálenosti (příklad se skupinou domů, stejná stránka
    o visibility ranges).
  - Pro les v Compatibility neexistuje hotový doplněk. Oktaedrické impostory z Asset Library uvádějí jen Forward+ a Mobile
    (`reserse_10_11`).
  - Hmotu tedy postaví Blender jako síť (model, ne primitivum).
- **Listí jako okluzor:**
  - Godot to výslovně neřeší. Peče jen neprůhledné sítě, listí s alpha scissor nezakrývá ani GPU (Adreno LRZ se
    discardem nepočítá, `reserse_10_11`).
  - Okluzor uvnitř houštiny je proto vždy ručně udělaný tvar a platí jen tam, kde je listí opravdu neprůhledné
    (podmínky v kroku 3).

---

## 3. Co už máme a v jakém stavu (nestavět znovu)

| věc | kde | stav (ověřeno čtením kódu a dat 15. 11.) |
|---|---|---|
| remízky | `lokace.json kompozice.remizky` (16 záznamů, r 9 nebo 14 m, s důvodem), staví `blender/kraj.py kompozice_remizky` → `veg.py` | **zapojeno**. Skladba (5 stromů a 14 keřů na r 9, výšky 9–15 m a 1,2–3 m, seznam druhů) je **natvrdo v kódu** `kraj.py:1098-1121`, ne v pravidlech |
| návrh remízků | `tools/kompozice_navrh.py` z `build/vyhledy.json` | funguje, ale vzdálenosti (MAXD 300, 28 m od staveb, 6 m od vody a cest) jsou **v kódu**. Navrhuje jen na louce a u cest, ne u vjezdu do vsi (vylučuje okolí usedlostí 28 m a `kraj.ves_r`) |
| výhledy | `kompozice.vyhledy` (5 kruhů) | **`prijezd_ves` (330, 735; r 45) leží přesně na začátku úseku ves-vjezd** (od 330, 725). Záměrný výhled a nejdražší úsek jsou totéž místo. Výhled nemá výšku ani směr (Astra 29. 10.: ZBÝVÁ) |
| mez dohledu | `kompozice.dohled_oblasti ves` (130 m), `drahe_celky` | slouží jen `mapa_vyhledu.py` (hlídač), hra je nečte |
| mapa výhledů | `tools/mapa_vyhledu.py` (pevné × listí, `listi_zavre_m` 12) | funguje, `--krok`, výstup `build/vyhledy.json` |
| scény A/B/C ve hře | `pravidla/svet/sceny.json` (mřížka dohledu, část `hra`: far kamery podle dohledu) z `tools/sceny.py` | **mrtvý záznam**: `scripts/sceny.gd` neexistuje a v historii gitu nikdy nebyl. `player.gd:107` má `cam.far = 2200` napevno. Buď zapojit, nebo záznam smazat (pravidlo „žádný mrtvý záznam“) |
| okluzory | `svet._okluzory` (`svet.gd:8756`) | terén (25 270 troj.) **zapnut**. Domy vsi (krabice z rámců, `pasma.budova.okluzor_*`) **zapnuty, 13 krabic** (log). Remízky a nitro lesa **vypnuty** (`pasma.test.okluzor_listi` false, Astra 29. 10.). U hráče se vypínají (`okluzor_vypnout_m` 6) |
| blízké stromy | plný strom do `STROM_PREP` (tablet 40 m, PC 60 m, **konstanta v kódu** `svet.gd:4127`), jádro koruny bez alfy + stínové těleso (10. 11.) | NAMĚŘENO: les p95 85 → 40 |
| vzdálené stromy | `svet._impostory`: 1 čtverec na strom, MultiMesh po druhu × buňce 1024 m, do `IMP_DOHLED` 900 m (konstanty v kódu), přechod ditherem `fade_od`/`fade_do` v `impostor.gdshader` | 20 578–20 600 stromů (logy `build/beh`) |
| obzor | `svet._obzor_les`: impostory za okrajem mapy po 7,5 m, 3 druhy, do 2 500 m | 76 550 stromů |
| jabloně v sadu | full model 24–28 tis. troj. (`lokace.json ves.dvorec.sad._modely`), dál `_daleko` 3 karty | v okolí vjezdu je sad za každým dvorcem. Podíl na 2,28 M **NEZMĚŘEN** |
| LOD staveb | `modely.json ves_domy_lod` (podrobný 30 m, střední do 75 m tablet, dál obal), `dily_lod` (krčma 172 tis., kovárna 65 tis.: podrobný 35 m, hrubý od 75 m tablet) | funguje, test `lod_mezera` |
| měřicí trasa | `mereni_trasa.json` úsek `ves-vjezd` (330,725 → 380,752, cíl 440,790, výška jezdce 2,5 m), varianty `les_bez_korun`, `dohled_kratsi`, skupiny `main._ab_skupiny` (louka, rostliny, stavby, predmety, stíny…) | `les_bez_korun` se na ves-vjezd **nikdy neměřil** (10. 11. jen les/louka/skály: koruny les p50 −13 ms, louka −5) |
| hlídač scén | `mereni_trasa.json hlidac_sceny`, test `trasa_sceny` (doskoky, typ scény) | běží na PC |
| keře z Disku | `bush.glb` (7thFlare, CC-BY 4.0) → `ker_kulaty` (radce 08:05), Poly Haven `shrub_02` | v remízcích jsou `shrub_02`, `bez_cerny_1`. `sipek` vyřazen (`druhy.json pouzit` false) |

Další hotové zdroje (hledáno 15. 11.):
- Poly Haven API, CC0: `shrub_01` (282 tis. troj.), `shrub_03` (17 tis.), `shrub_04` (48 tis.). Druh a vzhled (líska,
  hloh?) NEOVĚŘENO, prohlédnout před použitím.
- Disk Modely: `bush.glb` (použito), `tall_bush.glb` (tráva, nepoužito), `green_bush.glb`, `bush_cover__freefire.glb`,
  `low_poly_forest_tree_pack.glb` (licence NEOVĚŘENA, stylizované).
- Mladé jabloně: `Mlady_jablonovy_sad.zip` (Míša 14. 11.). Pro sad u cesty stačí stávající `jablon_*`.
- Quaternius a Kenney mají jen stylizovaná low-poly křoví. K fotoskenům se nehodí, jen nouzově pro hmotu
  (NEOVĚŘENO vzhledem).
- Model „hmoty lesa“ hotový nenajdeme, protože jde o odvozeninu našich stromů. Musí ji postavit Blender z polohy
  a velikosti skutečných korun.

---

## 4. Co víme o ves-vjezd: měřeno a hypotézy

- **NAMĚŘENO:** 810 volání, 2,28 M troj., p50 28–43 ms. Vnitřky domů nejsou příčinou (`bez_vnitrku` 43). Postavy
  ve vsi už ověřené bez vlivu (0.999995). Vyplňování pixelů nebylo brzdou 2. 11.: varianta 3D +60 % pixelů dala stejné
  FPS. To ale platí pro tvrz-cestu, pro ves-vjezd **NEOVĚŘENO**.
- **Hypotézy (NEOVĚŘENO, k izolaci v kroku 0):**
  - H1: celá ves v záběru. Střední stupně domů a dílů do 75 m (krčma, kovárna) a hrubé za nimi, plus stíny.
  - H2: sady jabloní (plné modely 24–28 tis. troj. do 40 m) a koruny listnáčů u vsi.
  - H3: impostory lesa za vsí (overdraw discardem, ne trojúhelníky). 20 tis. stromů je nejvýš asi 40 tis. troj.,
    takže 2,28 M nevysvětlí.
  - H4: tráva louky na otevřené ploše před vsí.
- Z toho plyne: **clona sama trojúhelníky neubere.** Listí okluzi nedělá a keře se kreslí navíc. Ubere jen tehdy, když
  (a) má pevné jádro s okluzorem (krok 3), nebo (b) díky ní smí ve vsi dřív přepnout hrubší stupeň. Ani jedno se nesmí
  slíbit bez měření.

---

## 5. Plán po krocích

Každý krok: **záznam** (data, žádná čísla v kódu) · **očekávaná úspora** (vždy NEOVĚŘENO, dokud ji nezměří Míša) ·
**měření** (varianta Měřicí trasy proti `vse` ve stejném běhu) · **návrat**.
Pořadí stavby zůstává terén → cesty → budovy → voda → vegetace → předměty. Clony, remízky i hmota lesa jsou krok
**vegetace**. Nehýbou cestou ani stavbou, jen se jim vyhýbají podle `pasma`. Před exportem musí projít
`/opt/bl/bin/python tools/test_smyslu.py` a test `zasazeni`. Platí: bez MSAA, bez screen texture, model (ne primitivum)
a po každé změně snímek `--write-movie`, na který se stavitel sám podívá.

### Krok 0: izolace ceny ves-vjezd (jen měření, bez nové verze kódu, kromě dat trasy)
- **Záznam:** `mereni_trasa.json varianty` = `["", "les_bez_korun", "rostliny", "stavby", "louka", ""]`. Skupiny
  `rostliny`/`stavby`/`louka` jsou v `main._ab_skupiny`, `les_bez_korun` v `mereni_trasa.gd`. Zúžení jen na úseky
  ves-vjezd, ves, mlýn a louka, pokud trasa umí výběr úseků (jinak celá).
- **Souběžně na PC:** `MERENI_AB` (`TVRZ_MERENI_AB=rostliny,stavby,louka,stiny`) z bodu (355, 738) výška 2,5 m s pohledem
  na (440, 790). Dá volání a trojúhelníky po skupinách hned, bez tabletu.
- **Co rozhodne:**
  - `les_bez_korun` je horní mez přínosu hmoty lesa (kroky 4–5). Ubere-li na ves-vjezd < 3 ms p50, hmota lesa je jen
    kvůli vzhledu, ne kvůli výkonu.
  - `stavby` × `rostliny` řekne, jestli clonu doplnit o přepnutí stupně staveb (krok 2b).
- **Návrat:** varianty zpět na stávající seznam.

### Krok 1: záznam „clona“ v kompozici a skladba remízku do pravidel (příprava, bez změny vzhledu)
- **Záznam:**
  - `lokace.json kompozice.remizek_skladba`: stromy na m poloměru, keře na m obvodu, výšky stromů a keřů, podíl jádra,
    seznam druhů podle stanoviště. Přesun z `kraj.py:1098-1121`, stejná čísla = stejný výsledek. Je to oprava „čísla
    v kódu“, ne nová věc.
  - `kompozice.clony` (nový seznam) se záznamy `{id, typ: "sad" | "kroviny_mez" | "remizek" | "zivy_plot", osa
    | stred+polomer_m, sirka_m, duvod, zavira: {odkud: [x,z], smer_st, vyska_oci_m}}`. Clona je pás, ne kruh: KCD
    křoví podél cesty.
  - Vzdálenosti od cesty a domu jen z `pasma` (cesta, budova `kmen_od_zdi_m`, `koruna_od_zdi_podil`), žádné nové
    číslo v kódu.
  - `kompozice_navrh.py` přečte prahy (`MAXD`, odstup 28 m, 6 m) z `kompozice` místo z kódu.
- **Test smyslu:** clona ne na cestě, ve vodě, na svahu nad `sklon_max`, ne v průchodu, ne přes záměrný výhled. Druhy
  podle stanoviště (`druhy.json`: mez, okraj, sad, ves). Při exportu se kontroluje každý kus.
- **Úspora:** žádná (stejný vzhled). **Měření:** export beze změny `svet.json` rostlin (porovnání počtu kusů remízků).
- **Návrat:** `git revert` (jen přesun čísel).

### Krok 2: (a) přirozená clona před vjezdem do vsi
- **Nejdřív rozhodnout s Míšou konflikt:** `vyhledy.prijezd_ves` (330, 735; r 45) je dnes záměrný výhled na celou ves
  přesně tam, kde je úsek nejdražší. Podle předloh (kcd1_28, ref_kcd2_ves_shora × ves_6, ref_kcd2_ves_plot_cesta) se
  celá ves ukazuje **z návrší**, vjezd po cestě je zavřený. Návrh:
  - `prijezd_ves` dostane `smer_st` a `vyska_m` (Astra ZBÝVÁ) a krátký úsek odhalení na hraně svahu odbočky. Cesta
    `odbocka_ves` od (310, 705) klesá a stáčí se k (343, 748); bod odhalení je potřeba najít `mapa_vyhledu.py`.
  - Za ohybem (343–380, 745–760) cesta vede podél **pásu sadu a křovin na severní straně**. Typ `sad` +
    `kroviny_mez`: jabloně a keře, jako před chalupami v ref_kcd2_ves_plot_cesta. Pás kryje pohled na (400–440,
    760–800).
  - Ves se pak odkrývá po dvorcích (vrata, plot) jako v kcd1_19/20.
- **Záznam:**
  - `kompozice.clony += {id: "vjezd_ves_sad", typ: "sad", osa: [...], duvod: "vjezd jako v KCD: ves za sadem a křovím,
    odkrývá se po ohybu; měření 0.999998 ves-vjezd 810 volání", zavira: {odkud: [355, 745], smer_st: …}}`.
  - Úprava `vyhledy.prijezd_ves`.
  - Polohy přesně až z `mapa_vyhledu.py` (cíl: z bodů úseku ves-vjezd za ohybem dohled ≤ `dohled_oblasti.ves.max_m` 130 m
    kromě směru výhledu).
- **Modely:** stávající `jablon_*` (sad), `shrub_02` / `ker_kulaty` / `bez_cerny`. Na mez případně Poly Haven
  `shrub_03` (CC0) po prohlédnutí. Nic nového se nemodeluje.
- **Úspora:** sama o sobě **0 nebo záporná** (keře a jabloně se kreslí navíc; listí neokluduje). Přínos je zážitek:
  postupné odkrývání. Výkon přinese až krok 2b nebo 3.
- **Krok 2b, jen pokud krok 0 ukáže, že vede `stavby`:**
  - Za clonou smí domy a díly přepnout na hrubší stupeň dřív. Pravidlo v `modely.json ves_domy_lod` / `dily_lod`:
    `stredni_do_m_za_clonou`.
  - Platí jen pro stavby, jejichž střed je ze všech bodů úseku za clonou podle mapy výhledů.
  - Riziko: vidět je to v mezerách listí. Musí ho chytit hlídač doskoků (`trasa_sceny`) a snímek.
- **Měření:** úsek ves-vjezd `vse` před a po (stejná verze trasy). Mapa výhledů po exportu, `build/mapa_stavby.png`.
  Snímky z (355, 745), (380, 752) a z výhledu.
- **Návrat:** záznam `clony[vjezd_ves_sad]` smazat (nebo `"zapnuto": false`) a vrátit `prijezd_ves`. Export.

### Krok 3: (b) hustá houština s okluzorovým jádrem – kdy je to bezpečné
Astra 29. 10. zakázala okluzor přes listí, protože „listím je vidět a dá se jím projít“. To platí pro dnešní řídké
remízky (5 stromů a 14 keřů na r 9). Bezpečné je to jen při **všech** podmínkách:
1. **Jádro je opravdu neprůhledné z oka hráče.** Test na PC: z 16 směrů ve výšce očí (1,7 a 2,5 m) a ze vzdálenosti
   `okluzor_vypnout_m` až dohled se paprsky na krabici okluzoru musí trefit listí nebo kmen skutečných instancí
   (`svet.json rostliny`, koruny z `trava_unshaded.koruny`) v podílu ≥ `okluzor_houstina_kryti_min`.
   - Číslo je potřeba změřit. Návrh 0,95 je jen výchozí hodnota pro test.
   - Krabice okluzoru je menší než jádro o `okluzor_houstina_okraj_m`.
2. **Hustota z dat:** jádro má spodní patro (keře, mladé stromy, `ker_husty`) i korunové patro. Remízek bez spodního
   patra okluzor nedostane (pod korunami je vidět, `mapa_dohledu.nasazeni_koruny` 0,3).
3. **Hráč je venku:** u hráče se okluzor vypíná (`okluzory_u_hrace`, `okluzor_vypnout_m`). To máme.
4. **Kontrola doskoku obrazem:** z bodů trasy kolem houštiny dva snímky, okluzor zapnut a vypnut. Pixely mimo masku
   houštiny se nesmí lišit (jinak okluzor schoval něco, co je vidět mezerou). Patří do testu `trasa_sceny` nebo nového
   `okluzor_pruhled`.
5. Pevný tvar má přednost (terén, zdi, stodola). Houština je doplněk.

- **Záznam:**
  - `pravidla_sveta.json pasma.test`: `okluzor_listi` (dnes jeden přepínač) nahradit pravidlem
    `okluzor_houstina: {kryti_min, okraj_m, spodni_patro_min, vyska_m}`.
  - Remízek nebo clona dostane okluzor, jen když projde testem 1–4. Výsledek testu se zapíše k záznamu
    (`okluzor: true/false, kryti: 0.97`). V kódu žádná výjimka.
  - Hustá houština = `kompozice.remizek_skladba` s vyšší hustotou jádra (druh `ker_husty`) jen u záznamů typu
    `remizek_husty`.
- **Úspora:**
  - Jen objekty, jejichž AABB je **celý** za krabicí. Okluze terénem dala na PC 0–46 volání, houština bude spíš
    desítky volání (NEOVĚŘENO).
  - Největší smysl má u clony vjezdu, kde za ní leží celé dvorce.
- **Měření:** nová varianta trasy `okluzor_houstiny` (zapne okluzory jen u záznamů, které testem prošly) proti `vse`
  na ves-vjezd a louce. Na PC `MERENI_AB` volání a trojúhelníky.
- **Návrat:** `okluzor_houstina.kryti_min` > 1 vypne všechny bez nové verze kódu.

### Krok 4: (c) vzdálený les jako hmota po porostech
- **Princip** (SS4 + KCD vzhled):
  - Blízko plný strom do `STROM_PREP`, pak impostor.
  - Od `hmota_od_m` impostory **uvnitř porostu** ditherem zmizí a nahradí je **jedna neprůhledná síť korun na porost
    a dlaždici**.
  - Okraj porostu (plášť do `okraj_m`), solitéry, sady, remízky a stromořadí zůstávají impostory. Tak vznikne silueta
    s hrbolky korun na hraně a hmota uvnitř (vzor 3, kcd1_28, ref_kcd2_ves_shora).
  - Za mapou (`_obzor_les`, 76 550 impostorů) totéž: hmota po dlaždicích 1 024 m. Úplně nejdál zůstává barva terénu
    (`zem.gdshader`, jako SS4 „splatted into terrain“).
- **Záznam** (`pravidla/svet/modely.json les_hmota`, nový, s `_pozn`):
  - `od_m`: začátek hmoty. Odhad 250–400 m, **zjistit snímky**, ne odhadem. Musí být za dosahem, kde je mezi korunami
    vidět louka.
  - `pasmo_m`: šířka ditherového přechodu (hystereze v prostoru: každý strom má náhodný práh, takže nevznikne čára).
  - `okraj_m`: plášť porostu zůstává impostory. Nejspíš stejné jako `pasma.test.okluzor_les_okraj_m`; sdílet, ne
    duplikovat.
  - `dlazdice_m`, `troj_max_dlazdice`, `les_min` (porost = `_les` ≥ hodnota, sdílet `okluzor_les_min`).
  - `barva`: průměr z atlasu impostoru druhu × `ztmaveni` (KCD: tmavší než louka), vnitřek a spodek tmavší ve vrcholech.
  - `stin`: false (hmota je daleko za dosahem stínu).
  - Ve stejném kroku přesunout do dat `STROM_PREP`, `IMP_DOHLED`, `IMP_BUNKA`, `OBZ_*` a `TINT_LISTI` (dnes konstanty
    v `svet.gd`).
- **Stavba (krok vegetace, Blender):**
  - Nový `blender/les_hmota.py` po rozmístění stromů vezme skutečné polohy a koruny stromů porostu (`svet.json
    rostliny`, rozměry `tools/koruny_rozmery.py`).
  - Postaví obálku jako sjednocení elipsoidů korun (metaball nebo voxel remesh), decimuje na `troj_max_dlazdice` a uloží
    barvu ve vrcholech: `modely/les/hmota_<x>_<z>.glb`.
  - Hmota je tedy tvarem shodná s impostory (Procworld: jinak přechod nesedí). Je to model z dat, ne primitivum.
- **Hra:**
  - `_impostory` rozdělí stromy na „jádro porostu“ (pod hmotou) a „ostatní“ zvláštními MultiMeshi.
  - Jádro dostane v `impostor.gdshader` druhý konec `fade_do = hmota_od + pasmo` se stejným `prah`.
  - Hmota má vlastní shader s **komplementárním** prahem z polohy ve světě, tedy ditherem bez průhlednosti
    a bez screen texture. Mlha je stávající (opar podle zadání, žádná nová vrstva).
  - Uzel hmoty má `visibility_range_begin` = `od_m` − rezerva a margin z dat, fade vypnutý (hystereze).
- **Pevná hmota = poctivý okluzor:**
  - Ve vzdálenosti, kde se kreslí neprůhledná hmota, je les opravdu neprůhledný.
  - Okluzory „nitro lesa“ (`okluzor_les_*`, dnes vypnuté) smí platit jen tehdy, když je hráč od buňky dál než `od_m`.
    Pravidlo `okluzor_les_jen_za_hmotou: true`, přepínání stejné jako `okluzory_u_hrace`, jen obráceně.
  - Řeší to Astřinu námitku: blízko listím vidět je, daleko už se kreslí neprůhledná hmota.
- **Úspora (NEOVĚŘENO):**
  - Horní mez dá krok 0 (`les_bez_korun` na ves-vjezd).
  - Čekaný přínos je hlavně v překryvu fragmentů s discardem (Adreno LRZ, `reserse_10_11`) a v počtu instancí, ne
    v trojúhelnících. Impostorů je ~97 tis., tj. ~0,2 M troj.
  - Pokud krok 0 ukáže < 3 ms, dělá se krok 4 jen kvůli vzhledu (KCD les), ne kvůli výkonu.
- **Měření:**
  - Varianta trasy `les_hmota` (vypne hmotu a vrátí impostory) proti `vse` na úsecích ves-vjezd, louka, kun-les,
    vez-vyhled. Na PC test `trasa_sceny` (doskoky v pásmu `od_m`).
  - Snímky z věže, z (355, 745) a z louky. Porovnat s kcd1_28 a ref_kcd2_ves_shora vedle sebe.
- **Bez doskakování:**
  1. Přechod je po stromech náhodným prahem přes `pasmo_m`, ne hranou.
  2. Hmota je tvarem ze stejných korun.
  3. Hystereze uzlu je z marginu.
  4. Hlídač doskoků (`trasa_sceny`, `doskok_m`) musí dát 0 nových doskoků proti schválené trase.
  5. Žádná průhlednost (prolínání v Compatibility nefunguje).
- **Návrat:** `les_hmota.od_m` ≥ `IMP_DOHLED` (po přesunu do dat) vypne hmotu bez nové verze kódu. Soubory hmoty
  zůstanou nepoužité.

### Krok 5: barva a opar vzdáleného lesa (vzhled, souběžně s krokem 4)
- Na našich snímcích (misa_15_11/17, 18; misa_9_11/05) je vzdálený les světlejší než blízký a rozpadá se na jednotlivé
  kužele. KCD má dálku tmavší a souvislou.
- **Záznam:** `les_hmota.barva`, `ztmaveni` a `TINT_LISTI` v datech (krok 4). Kalibrace podle snímku z věže proti
  ref_kcd2_ves_shora: průměrná barva pásu lesa a louky, poměr jasů.
- **Úspora:** 0 (jen vzhled). **Měření:** snímek, test smyslu, případně nová kontrola „les tmavší než louka“ ve snímku
  z pevného bodu. **Návrat:** činitele na 1.

### Krok 6: rozhodnout o `sceny.json hra`
- Záznam slibuje řízení `Camera3D.far` podle typu scény, ale skript neexistuje (`player.gd` má 2 200 m).
- Varianta `dohled_kratsi` (15. 11.) to částečně měří.
- Buď zapojit (pak měřit `dohled_kratsi` proti `vse` na ves-vjezd), nebo `hra` ze záznamu smazat a zapsat do
  `predani.md`.
- Nejdřív výsledek kroku 0.

---

## 6. Pořadí a první krok
1. **Krok 0 (první):** jedna Měřicí trasa s variantami `les_bez_korun`, `rostliny`, `stavby`, `louka` a na PC
   `MERENI_AB` z bodu vjezdu. Bez nové verze kódu (jen data trasy) a bez exportu. Rozhodne, jestli táhne les, sady nebo
   stavby.
2. Krok 1 (přesun čísel do pravidel) jde souběžně, je bez rizika.
3. Krok 2 (clona vjezdu) až po rozhodnutí Míši o výhledu `prijezd_ves`.
4. Krok 3 (okluzor houštiny) až když je clona hotová a test průhledu napsaný.
5. Krok 4 (hmota lesa): rozsah podle výsledku kroku 0. Vzhled KCD se dělá v každém případě, výkon jen pokud ho krok 0
   ukáže.

Rozlišení jistoty: v celém dokumentu je **NAMĚŘENO** jen to, co je v `mereni_verze.md` nebo v logu `build/beh`.
Ostatní je podezření nebo návrh. Po dvou neúspěšných pokusech o tutéž věc nový rozbor, ne třetí oprava.
