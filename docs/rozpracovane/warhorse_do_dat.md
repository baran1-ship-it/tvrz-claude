# Dokumentace Warhorse pro modery KCD2 → naše data

Zdroj: veřejná znalostní báze Warhorse `warhorse.youtrack.cloud`, články `KM-A-*` (staženo 28. 10. 2026 přes API,
78 článků). Citace jsou přeložené nebo zkrácené, u každého údaje je ID článku. Hodnoty RPG konstant jsou z KM-A-20
(„Values exported 14/1/2025“).
**NEOVĚŘENO** = číslo není z článku (náš odhad, výklad nebo přepočet na tablet). Než se použije, musí se změřit
nebo schválit.
Nic v repu se tímto souborem nemění, jsou to jen návrhy. Vnímání NPC, pověst, špínu, charisma a zločin jako vstup
reakcí už pokrývá `reserse_reakce_kcd2.md`, tady se to neopakuje (jen odkazy).

Prázdné nebo jen nadpisové články (nic k převzetí): KM-A-22 (Clothing – technical overview), KM-A-29 (Quest
System), KM-A-40 (Environment Art), KM-A-44 (Asset creation pipeline – rozcestník), KM-A-67 (Event system – jedna
věta), KM-A-71, KM-A-72. Obsah „Asset creation pipeline“ je ve skutečnosti v KM-A-45 (Asset creation).

---

## 1. Hned použitelné

### 1.1 Texel ratio → `pravidla_modelu.json` `textura_px`

| Pravidlo Warhorse | ID | Náš soubor / klíč | Teď u nás | Návrh | Důvod |
|---|---|---|---|---|---|
| Texel ratio = `sqrt(plocha trojúhelníku v UV / plocha trojúhelníku v m²) × strana textury v px`, jednotka px/m, počítá se pro každý trojúhelník | KM-A-54 | nový sloupec `texel_m` (px/m) u každé třídy + nový test `texel` | nic, jen strop `textura_px` | `texel_m` u třídy; test spočítá texel na trojúhelník z UV a sítě LOD0 | Strop rozlišení neříká, jak ostrá textura je. Hráč porovnává sousední textury, takže jednotnost je důležitější než velikost (KM-A-54) |
| Cíl Warhorse pro diffuse na PC: **512 px/m**, platí jen pro LOD0 | KM-A-45 | `texel_m` | – | PC 512; **tablet 256 (NEOVĚŘENO**, polovina PC; ověřit snímkem 1 m od zdi) | Pro textury, které nejsou vidět zblízka, má být hustota menší (KM-A-45) |
| Hrdinské předměty víc, spodky stolů a nevidné plochy méně | KM-A-45 | `texel_m` u `predmet` / v ruce | – | věci v ruce (louč, zbraň) 2× `texel_m` třídy (**NEOVĚŘENO**, násobek) | KM-A-45: „hero asset might need more“ |
| Ostatní mapy: Normal+Gloss 512 (256, když to jde), Specular 128, Heightmap 128, DetailAtlas 64, Detail 2048 (dlaždicováním) | KM-A-45 | nový klíč `textura_podil` {normala, orm} | normála i roughness v plném rozlišení | `normala` 1,0 (případně 0,5), `orm` (roughness/metallic/AO) **0,25** | Spec a height mají u Warhorse ¼ hustoty diffuse (128/512). U nás tomu odpovídá ORM. Ušetří VRAM (`rozpocet.gpu_textury_mb` 400) |
| Rozlišení podle mapování: krychle 1×1×1 m se všemi stěnami přes sebe v UV 0–1 → 512×512 | KM-A-45 | `textura_px` = strop | strom/skala/stavba/postava/zvire 1024, jinak 512 | `textura_px` = mocnina 2 ≥ `texel_m × sqrt(světová plocha na jedinečném UV)`, nejvýš strop třídy. Příklad: bedna 0,5 m se sdílenými stěnami při 256/m → 128 px | Velikost textury určují mapování a velikost objektu, ne třída |
| Kontrolní rozsah pohledu `r_TexelsPerMeter`: červená = aspoň 2× cíl, střed = v cíli, polovina cíle leží v půlce levé strany | KM-A-54, KM-A-45 | mez testu `texel` | – | chyba mimo **0,5× až 2×** `texel_m` (na LOD0, vážený plochou) | Meze barevné stupnice Warhorse |
| Detailní mapy 512×512 dlaždicované na 2048 px/m: diffuse 512 → dlaždice 2,2; 1024 → 4,4; 512×1024 → 2,4. Detail mizí na `Detail fadeout distance` (příklad 10 m) | KM-A-45, KM-A-53 | `pravidla_modelu.json` nový klíč `detail` u stavba/skala/drevo | nic | `{"px":512,"dlazdice_na_px":1/256,"zhasne_m":10}`, **na tabletu jen LOD0 a jen do 10 m (NEOVĚŘENO** cena vzorku navíc) | Zblízka je 512/m rozmazané (KM-A-45). Ostrost dodá levná dlaždice, ne větší textura |
| Detail atlas: jeden materiál, víc detailních map podle šedé masky `_dt` (např. RGB 200 = kartáčovaný kov) | KM-A-53, KM-A-59 | později `detail.atlas` | – | až po zavedení `detail`; maska ve vrcholové barvě, ne další textura (**NEOVĚŘENO**) | Jeden draw call pro dřevo i kování |
| Využít UV co nejvíc, zrcadlit, sdílet výseče (půlky sudu), dlaždicovat; textury sdílet mezi modely (v paměti jen jednou) | KM-A-45 | `tools/import_model.py` (zpráva) | – | import hlásí využití UV < 0,6 (**NEOVĚŘENO**, mez) | Volné UV je ztracené rozlišení |

### 1.2 LOD → `troj_lod`, `lod_m`, `lod_px`

| Pravidlo Warhorse | ID | Náš klíč | Teď | Návrh | Důvod |
|---|---|---|---|---|---|
| Pořadí cílů LOD: 1. méně draw callů, 2. stejný vzhled (žádný samostín při přepnutí), 3. jednodušší shader (bez parallaxu, detailu a alfy), 4. až pak trojúhelníky | KM-A-46 | nový sloupec `lod_materialu` [LOD0, LOD1, LOD2] | nic. Godot auto-LOD drží všechny materiály, takže draw calls se nesníží | stavba [n, 2, 1], predmet_velky [n, 1, –], strom [n, 2, 1] (kůra + listí → karta) | Příklady KM-A-46: interiérový předmět 7 DC → LOD 1–2 DC; velký venkovní 8 DC → LOD1 + LOD2 s menším počtem ID; univerzální 3 DC → jeden LOD s jedním ID |
| LOD1 aspoň o 50 % méně než LOD0, LOD2 aspoň o 50 % méně než LOD1 | KM-A-46 | `troj_lod` + test `modely` | všechny třídy splňují (strom 12000/3000, stavba 40000/12000/3000, predmet 2000/400, skala 3000/800/150) | zapsat jako mez testu `lod_pomer_max: 0.5` | Teď to platí náhodou, pravidlo hlídá nové modely |
| Počet LOD podle velikosti: malé předměty s málo materiály **žádný** LOD („je lepší je nemít“: při přepnutí se kreslí obě verze), střední 1 LOD, LOD1 i LOD2 jen velké stavby. Pravidlo **1 m³**: od této velikosti musí mít LOD; nádobí a jídlo bez LOD | KM-A-46 | `troj_lod` u `predmet` | `predmet` [2000, 400, 0] pro všechno (modely.json ho dělí na predmet_drobny 95 ks, predmet_stredni 127, predmet_velky 106) | rozdělit třídu: `predmet_drobny` [≤1000, 0, 0], `predmet_stredni` [≤2000, 400, 0], `predmet_velky` (≥1 m³) [≤5000, ≤2500, 0] | KM-A-46. Navíc tyto tři třídy už v `modely.json` jsou, ale `pravidla_modelu.json` je nezná |
| Výchozí rozpočet trojúhelníků podle objemu: 0,1 m³ = 1000, 1 m³ = 5000, 10 m³ = 20000, 100 m³ = několik modelů po 64000 | KM-A-45 | `troj_lod[0]` | viz výše | na tablet **½ těchto čísel (NEOVĚŘENO)**: 0,1 m³ 500, 1 m³ 2500, 10 m³ 10000; stavba 40000 nechat (měřeno vlastním rozpočtem) | Nejsou to meze, ale výchozí bod. Kulaté věci mají trojúhelníky jen na obrysu (poleno: konce husté, střed řídký) |
| LodRatio: 255 velké městské domy, 200 velké objekty (velké stany, menší městské a vesnické domy, stodoly), 150 ostatní (nábytek, kůlny) | KM-A-46 | `lod_m` / `lod_bias` | `lod_m` stavba [40, 120, 600] | poměr vzdáleností 255:200:150 ≈ 1,7 : 1,33 : 1 jako `lod_nasobek` záznamu (tvrz 1,7, chalupy a stodoly 1,33, kůlny 1,0). **Převod LodRatio na metry je výklad (NEOVĚŘENO)** | CryEngine LodRatio násobí vzdálenost přepnutí. Godot: `lod_bias` / `visibility_range` instance |
| Přepnutí LOD podle plochy na obrazovce (u nás `lod_px` = e_LodFaceAreaTargetSize) | – | `lod_px` 4 | 4 | beze změny; tyto články číslo neuvádějí | zdroj hodnoty 4 je jinde (rešerše 20:50), ne v KM-A-* |
| Interiér v LOD domů: v LOD1 smazat celý vnitřek (zdi, schody, trámy) a místo něj **černá výplň** (vrcholová barva 0,0,0), plochy **aspoň 30 cm od vnější zdi**, zakryjí okna a dveře, normály dovnitř. Stejná výplň i v LOD2 | KM-A-46 | `stavba` nové klíče `lod_vnitrek: "cerna_vypln"`, `vypln_od_zdi_m: 0.3` | stavba LOD1 12000 i s vnitřkem? (neověřeno) | zavést, test: LOD1 stavby nemá trojúhelníky vnitřku | Okny se nedá prohlédnout skrz dům a vnitřek nestojí trojúhelníky |
| LOD1 musí mít všechny tvary LOD0; LOD nesmí být větší než předchozí (samostín při přepnutí); pozor na díry ve střeše zespodu a na domy ve svahu viděné zdola | KM-A-46 | test `modely` | – | kontrola: obálka LODn ⊂ obálka LOD0 + 2 cm (**NEOVĚŘENO**, tolerance) | KM-A-46 (věž se samostínem) |
| Doškovou střechu, prkna a velké nálepky (decals) v LOD1 nechat; drobné nálepky (hřebíky) smazat | KM-A-46 | import | – | do `import_model.py` jako seznam materiálů „drzet_v_lod1“ | KM-A-46 |
| Optimalizace LOD0: mazat neviditelné (trámy ve zdi, pod zemí); u nepřístupných domů smazat vnitřek; štít nepřístupného domu dlaždicí, ne prkny; okraj střechy 11 m nad zemí stačí 1–2 vrstvy; u doškové střechy smazat aspoň každou druhou vrstvu (ne horní); jednoduché konce trámů vysoko; zbytečně dělené rovné zdi bez vrcholových barev ne | KM-A-51 | kontrolní seznam importu stavby | – | do `docs/pipeline.md` jako kontrolní seznam modelu stavby | KM-A-51 |
| Složitý interiér (sklep) jako zvláštní model s malou dohledností (ViewDistRatio) | KM-A-51 | `nacitani` / `dosah_m` dílu | stavba `nacitani: "dil"`, `portaly: true` | vnitřek = vlastní záznam s `dosah_m` 30 (**NEOVĚŘENO**) | ladí s našimi portály |
| Zbraně nemají LOD; mnoho trojúhelníků v LOD0 je v pořádku (drží se v ruce); textura 2048 nebo 1024×2048, čepel může mít až o 30 % menší UV | KM-A-88 | budoucí třída `zbran` | – | `zbran`: troj_lod [≤8000, 0, 0] (**NEOVĚŘENO**), textura_px 1024 (tablet strop) | KM-A-88 |

### 1.3 Stín (shadow proxy) → `stin`, `stin_m`

| Pravidlo Warhorse | ID | Náš klíč | Teď | Návrh | Důvod |
|---|---|---|---|---|---|
| Stínová zástupná síť: zjednodušená geometrie **bez alfa dílů** (decals), **jeden materiál**. Do stínové mapy jde jen geometrie, takže z mnoha draw callů je jeden | KM-A-49 | `stin` | `"lod0" \| "ne"` | nová hodnota `"proxy"`: stínová síť = LOD1 (u stavby LOD0 decimovaná) bez alfa materiálů, sloučená do jedné plochy. Viditelná síť má `cast_shadow` vypnuté. V Godotu `ArrayMesh.shadow_mesh` nebo `MeshInstance3D` jen se stínem (`SHADOWS_ONLY`). **Že renderer Mobile v Godotu 4.4 `shadow_mesh` použije, je NEOVĚŘENO**, ověřit jedním modelem | Na tabletu je stínový průchod drahý. Stavba s několika materiály = několik draw callů ve stínu |
| Proxy jen pro **LOD0 a LOD1** | KM-A-49 | `stin_m` | stavba/skala/drevo/balvan 40, strom 60, předmět 20 | `stin_m` ≤ konec LOD1 (`lod_m[1]`), dál bez stínu. To u nás už platí: stavba 40 < 120 | potvrzení stavu |
| Proxy LOD0: dost rozlišení (hráč chodí mezi nimi, artefakty jsou vidět na střeše a zdech); u střechy „zůstat aspoň kolem 60–65 % redukce“, případně ruční oprava (Push) | KM-A-49 | `troj_stin` (nový) | – | stavba: `troj_stin` = 0,35–0,4 × LOD0 (**výklad věty „60–65 % reduction“, NEOVĚŘENO** – může znamenat i 60–65 % zachovat) | KM-A-49 |
| Výjimky, kde alfa materiál stín vrhá: došková střecha, seno, sláma, kamenné rohy, okraje střechy s alfa výřezem. U vysokých budov to není potřeba (stín daleko od země nic nepřidá) | KM-A-49 | `stin_alfa` (nový seznam materiálů) | `alfa: scissor` u stromů: listí stín vrhá (strom `stin: lod0`) | `stin_alfa: ["doskova", "seno", "slama", "listi"]` (listí je u nás nutné, KCD má listí jako alfa test) | KM-A-49 |
| Proxy má v materiálu bílou texturu 256×256 a diffuse barvu = celková barva modelu | KM-A-49 | – | – | **jen CryEngine** (u nás stínová síť materiál nepotřebuje) | – |

### 1.4 Okluzor (occlusion proxy) → `pasma.test.okluzor_*`, nový sloupec

| Pravidlo Warhorse | ID | Náš klíč | Teď | Návrh | Důvod |
|---|---|---|---|---|---|
| Okluzor se počítá na CPU před vším ostatním → co nejlehčí: „počet trojúhelníků co nejblíž jednocifernému číslu“. Stavět z rovin, nespojovat. Malé tvary (sloupek mezi okny) vynechat | KM-A-47 | nový sloupec `okluzor` v `pravidla_modelu.json` | jen les (`okluzor_les_*`) a „pozdeji domu“ | stavba: `okluzor: "steny"`, `troj_okluzor_max: 12` (**NEOVĚŘENO**, Warhorse: „blízko jednomu místu“), ostatní `false` | Godot `OccluderInstance3D` je taky CPU rastr. Každý trojúhelník stojí na každém snímku |
| Vnitřní zdi, podlahy a stropy bez okluzoru; vnější zdi z **obou stran** (zakrývá jen strana ke kameře) | KM-A-47 | test `okluzor` | – | kontrola: okluzor stavby má obě strany. U Godotu jde o `two_sided` u `PolygonOccluder3D` / `BoxOccluder3D` (box je oboustranný sám) | KM-A-47 |
| Okluzor jen tam, kde se geometrie za hry nemění. **Ne do vrstev, které se načítají a uvolňují** | KM-A-47 | stavba `nacitani: "dil"` | stavba se načítá po dílech | okluzor stavby patří do záznamu dílu a s dílem se načte i uvolní (Godot okluzory za běhu přidávat smí, CryEngine ne). Pro díly s `nacitani: "dil"` mez `okluzor_vypnout_m` platí dál | rozdíl enginu, viz 1.8 |
| Okluzor terénu: zjednodušený terén posunutý **o několik metrů dolů** (zjednodušení nesmí vyčnívat); zachovat díry (vstupy do dolů) | KM-A-47 | nový `pasma.test.okluzor_teren_pod_m` | – | `okluzor_teren_pod_m: 3.0` (**NEOVĚŘENO**, „several meters“), zvážit jen pro kopce mezi vsí a lesem | velké kopce zakryjí celé údolí |
| Pivot okluzoru = pivot viditelného modelu, přípona `_occ` | KM-A-47 | jména v `modely.json` | – | `<model_id>_occ` | jednotné jméno |

### 1.5 Kolize (physical proxy) → `kolize`, `kolize_m`

| Pravidlo Warhorse | ID | Náš klíč | Teď | Návrh | Důvod |
|---|---|---|---|---|---|
| Od nejlevnějšího: koule < kapsle < válec < kvádr < trimesh. **Primitiva jsou obvykle lepší**, ale tvar se má blížit skutečnému (kámen s krychlovou kolizí se odráží divně) | KM-A-48 | `kolize` | stavba `"original"`, skala/kamen/balvan/drevo `"trimesh_lod1"` | stavba: `"boxy+trimesh_lod1"` (zdi a podlahy kvádry, zbytek trimesh LOD1); balvan `"kapsle\|kvadr"` podle tvaru; `"original"` zrušit | Plná síť LOD0 jako kolize je v pořadí Warhorse to nejdražší |
| Malé věci (kamínky, větvičky, misky, hrnky) kolizi nepotřebují, **pokud se nedají sebrat** | KM-A-48 | `kamen.kolize` | `"trimesh_lod1"`, ale `kolize_m: 0` (= nikdy). Hodnoty si odporují | `kamen.kolize: false` | sjednotit, aby záznam neříkal dvě věci |
| `drevo` | – | `drevo.kolize` | `"trimesh_lod1"` + `kolize_m: 0` | rozhodnout: hromada dřeva = `kvadr` + `kolize_m 20`, nebo `false` | stejný rozpor |
| Obálka kolize (bounding box) se používá i pro výpočty (např. přímou viditelnost). Má se blížit tvaru, jinak kolizi rozdělit na víc kusů | KM-A-48 | test `modely` | – | kontrola: objem obálky ≤ 2× objem kolize (**NEOVĚŘENO**, mez) | KM-A-48 (příklad dobrý/špatný) |
| Druh povrchu u kolize určuje zvuk, částice, nálepku, průstřelnost, průhlednost pro pohled NPC (keře, sklo), chodivost (navmesh), zda ji kůň ignoruje, jen-kůň, jen-hráč, schody (`slope`, `stairs_wood`, `stairs_stone`), `wood_unwalk` | KM-A-48 | nový sloupec `povrch` + příznaky | – | `povrch`: drevo, kamen, hlina, slama, latka, kov, voda; příznaky `jen_hrac`, `jen_kun`, `kun_ignoruje`, `schody`, `pruhledne_pro_pohled` (keř – napojit na vnímání v `postavy.json`) | Zvuky kroků a zásahů podle povrchu, kůň neprojde tam, kde hráč ano (a naopak), NPC vidí přes keř |

### 1.6 Rozměry → `pravidla_sveta.json` `pasma.budova` + test

Článek KM-A-52 říká, proč rozměry držet pevně: animace s nimi počítají (žebříky, židle), kolize postav má
pevnou velikost a musí projít (dveře, místnosti), a předpřipravené díly (schody, rámy dveří a oken) musí pasovat.

| Rozměr Warhorse | ID | Náš klíč (nový v `pasma.budova`) | Teď u nás | Návrh | Test |
|---|---|---|---|---|---|
| Výška podlaží (podlaha–podlaha): **225, 250, 300, 350, 400 cm** | KM-A-52 | `vyska_patra_m: [2.25, 2.5, 3.0, 3.5, 4.0]` | nic | zavést | `rozmery`: patra stavby z výšek podlah dílů ∈ seznam ±0,05 m (**NEOVĚŘENO**, tolerance) |
| Tloušťka zdi: **10, 25, 60, 100, 150, 200 cm**. 25 = roubené a hrázděné (tloušťka trámu), 60 = kamenný městský dům | KM-A-52 | `tloustka_zdi_m: [0.1, 0.25, 0.6, 1.0, 1.5, 2.0]`, `zed_roubena_m: 0.25`, `zed_kamenna_m: 0.6` | nic | zavést (tvrz: hradba 1,5–2,0) | tloušťka otvoru dveří a oken ∈ seznam |
| Hloubka okna (prvku): **10, 25, 60, 100, 150, 200 cm** | KM-A-52 | `hloubka_okna_m` = `tloustka_zdi_m` | nic | stejný seznam | rám okna = tloušťka zdi |
| Výška schodiště: **225, 250, 300, 350, 400 cm** (= výšky pater) | KM-A-52 | `vyska_patra_m` | nic | sdílet | schodiště spojuje dvě patra ze seznamu |
| **Výška i hloubka schodu 20 cm** | KM-A-52 | `schod_vyska_m: 0.2`, `schod_hloubka_m: 0.2` | `pasma.budova.schody_m: 1.0` (hloubka schodů před dveřmi celkem). `scripts/player.gd` `STEP := 0.45` (nejvyšší vyjitelný schod, číslo v kódu) | zavést. `STEP` přesunout do `hrac.json` `schod_max_m` (0,45 jen pro prahy a kameny, schody stavby ≤ 0,2) | `rozmery`: každý stupeň stavby 0,2 ±0,02 (**NEOVĚŘENO**, tolerance) |
| **Rozestup příček žebříku 20 cm** | KM-A-52 | `zebrik_pricka_m: 0.2` | model `zebrik` 3,0 m (rozestup neměřen) | zavést | změřit `zebrik.glb` (Blender) – **NEOVĚŘENO**, zda odpovídá |
| **Výška sedáku 45 cm** | KM-A-52 | `sedak_m: 0.45` | lavice_selska a lavice_hodovni 0,475 (celková výška = sedák), stolicka 0,437, stolicka_vysoka 0,579 | zavést. Animace sedu (`jizda.json telo.sed_m: 0.5`) navázat na `sedak_m` | sedací předměty: výška sedáku 0,45 ±0,05 (**NEOVĚŘENO**, tolerance); u židlí s opěradlem chybí výška sedáku v datech → doměřit |
| Rozměry dveří (výška, šířka) | **v KM-A-52 nejsou** (článek zmiňuje dveře jen jako důvod) | `dvere_vyska_min_m`, `dvere_sirka_min_m` | kapsle hráče 1,76 × r 0,28 (`player.gd`); dveře na pavlač hostince 2,17 m (komentář v `player.gd`) | výška ≥ 1,76 + 0,10 = **1,86 (NEOVĚŘENO**, odvozeno z kapsle, ne z Warhorse); šířka ≥ 2×0,28 + 0,2 = **0,76 (NEOVĚŘENO)** | `rozmery`: kapsle hráče projde každým otvorem dveří |
| Světlá výška stropu | **není v KM-A-52** | `strop_svetly_min_m` | – | = nejnižší patro 2,25 − strop 0,25 = **2,0 (NEOVĚŘENO**, výpočet) | kapsle + zvednutí na schod (1,76 + 0,2) se vejde |
| Výška zábradlí | **není v KM-A-52** | `zabradli_m` | – | **NEOVĚŘENO**, nutná rešerše (pavlače KCD2, dobové stavby). Číslo nedávat z hlavy | – |

### 1.7 Hráč a kůň (čísla z KM-A-20, k `hrac.json` a `jizda.json`)

KCD2 tu nemá uvedenou maximální výdrž (`mst` je odvozená statistika, KM-A-21). Přepočet předpokládá max 100 jako u
nás: **NEOVĚŘENO**.

| Konstanta KCD2 | ID | Hodnota | Náš klíč | Teď | Návrh |
|---|---|---|---|---|---|
| `SprintCost` | KM-A-20 | 3,5 stam/s | `hrac.json beh_za_s` | 7,0 (běh ~14 s) | 3,5 → ~29 s (**NEOVĚŘENO**, předpoklad max 100) – rozhodne Míša |
| `StamRegenBase` / `StamRegenMoveMod` | KM-A-20 | 22 stam/s / 0,75 při pohybu | `obnova_za_s`, nový `obnova_pohyb_podil` | 14 / – | 22 a `obnova_pohyb_podil: 0.75` |
| `StamRegenRelativeDiff` | KM-A-20 | 0,667: obnova se liší až o ⅔ při nízké a vysoké výdrži | nový `obnova_rozdil` | – | 0,667 (jestli rychleji nahoře nebo dole, článek neříká: **NEOVĚŘENO**) |
| `JumpCostBase` | KM-A-20 | 9 | nový `skok_vydrz` | – | 9 |
| `HarmlessFallHeight` / `InjuringFallHeight` / `FatalFallHeight` (obratnost 0) | KM-A-20 | 1,5 / 2,2 / 8 m | nový `pad: {bez_skody_m, zraneni_od_m, smrt_od_m}` | – | 1,5 / 2,2 / 8,0 (lom, pavlač, žebřík) |
| `FallDamageMultiplierAtMaxAgility` | KM-A-20 | 0,667 | budoucí dovednosti | – | sekce 2.1 |
| `RiderHorseStaminaCoef` | KM-A-20 | 0,75 (poměr spotřeby koně a jezdce) | `jizda.json kun` | `vydrz_s: 12` | jen poznámka; náš kůň má vlastní model trysku |
| `HorseSlowSpeedStaminaRegen` | KM-A-20 | +1 sta/s pod tryskem | `kun.vydrz_obnova` | 0,6 (jednotka v datech nejasná) | sjednotit jednotku na „za s“, pak 1,0 |
| `HorseSlowdownTimeSprint` | KM-A-20 | 1 s bez držení → kůň začne zpomalovat | nový `kun.trysk_dobeh_s` | – | 1,0 |
| `SleepHealthRegenBaseSpeed` | KM-A-20 | plné zdraví za 8 h spánku | později `hrac.json spanek` | – | 8 h |
| `ExhaustionSpeed` | KM-A-20 | 0,000578704 %/s = 100 % za 48 herních hodin | později únava | – | 48 h |

### 1.8 Co platí jen pro CryEngine (u nás nic)

- LodRatio jako číslo 0–255, nastavení „Config spec Medium“, testovat LOD s LodRatio 255 (KM-A-46). U nás jde jen
  o poměr vzdáleností (1.2).
- Jména `$lod1_XXX`, linkování na Merge node, vrstvy a barvy drátů v 3ds Max (KM-A-46, KM-A-48).
- Mez 64 000 indexů na model (KM-A-45). Godot u větších sítí přepne na 32bit indexy sám, mez pro nás dělá jen
  rozpočet tabletu.
- Komprese vrcholů podle vzdálenosti od pivotu (na 100 m až „pár cm“, KM-A-45). Godot ukládá float32, ale pivot
  u geometrie je i tak dobrá zásada.
- `r_TexelsPerMeter`, ViewModes, `e_coverageBufferDebug/Reproj`, `p_draw_helpers`, export `occluder.ocm`, restart
  editoru (KM-A-47, KM-A-48, KM-A-54).
- Okluzor nesmí být ve streamovaných vrstvách (KM-A-47). Godot `OccluderInstance3D` se dá přidat za běhu (s cenou
  přestavby BVH; **NEOVĚŘENO** na tabletu).
- Materiál proxy: „Physicalize: Physical proxy (No Draw)“, ID 1–2 fyzikální, 3–32 běžné; bílá 4×4 / 256×256
  textura v materiálu okluzoru a stínové proxy (KM-A-47, KM-A-48, KM-A-49).
- CryTIF, RC předvolby, přípony `_diff/_ddn/_ddna/_spec/_displ/_dtmask`, neukládat DDS přímo (KM-A-45). U nás
  komprese VRAM při importu.
- Smid, Material Atlas, Feature ID kostka v kanálu Detail (KM-A-24, KM-A-26, KM-A-78). Princip převezmeme
  (sekce 2.2), nástroj ne.
- Zbraňový shader s maskou R rez / G krev / B ostří / A zóny broušení (KM-A-88). Princip dává smysl, na tabletu
  je to další textura a větvení shaderu: později a **NEOVĚŘENO**.
- Tablet: MSAA ani screen texture nic z toho nepotřebuje. Černá výplň interiéru LOD je jen vrcholová barva.

---

## 2. Pro budoucí sekce

### 2.1 Dovednosti (plán 1.0 „Dovednosti hráče“)

**Jak to má KCD2 (vzor):**

- Statistiky duše (KM-A-21): `strength, agility, vitality, speech` (hráčovy vlastnosti), dál `vision, hearing,
  barter, courage, storyProgress, prestige`.
- Dovednosti (KM-A-21, bez `_obsolete`): `stealth, horse_riding, fencing, bard, thievery, alchemy, cooking,
  craftsmanship, fishing, mining, first_aid, drinking, survival, defense, weapon_sword, heavy_weapons,
  marksmanship, weapon_shield, weapon_dagger, weapon_large, weapon_unarmed, scholarship, tailoring, armourer,
  weaponsmithing, shoemaking, gunsmithing, bowyery, gambling, houndmaster`. Část jsou staré nebo interní, hráč
  jich v KCD2 vidí méně.
- Stavy (KM-A-21): `health, stamina, exhaust, hunger, karma, alcoholism`. Odvozené statistiky (charisma,
  viditelnost `vib`, nápadnost `con`, hluk `noi`, nosnost `cap`, špína `drt`, …) se počítají z vlastností,
  výbavy a bufů.
- Strop: `SkillCap` 30, `StatCap` 30 (KM-A-20). „Účinky obecné dovednosti jsou nejvyšší na stropu.“
- XP na další úroveň (KM-A-20): dovednosti `SkillXPLevelBase` 25 (sčítací) a `SkillXPLevelDiff` 35 („násobicí“);
  síla 25/40, obratnost 25/40, vitalita 25/35, výřečnost 25/40, `StoryProgress` 20/30, `Prestige` 20/30.
  **Přesný vzorec v článku není** („see GDD 44/218“). Výklad `xp(n→n+1) = Base + Diff·n` je **NEOVĚŘENO**.
  `StatToMainLevelBase` 0,5 a `SkillToFencingBase` 0,8 jsou „a1 geometrické řady“, kvocient není uveden.
- Perky (KM-A-20): `MaxPerkPoints` 13 bodů za každou statistiku/dovednost, od úrovně `MinLevelForPerkPoints` 6,
  `MinPerkPoints` 5. Rozložení mezi úrovně 6–30 článek neuvádí (**NEOVĚŘENO**: zhruba každé 2 úrovně).
  Perk mění RPG konstanty (`perk_rpg_param_override`), dává buf (`perk_buff`), recept nebo techniku boje
  (tabulky KM-A-12).
- Buf (KM-A-16/84): `buff_params="charisma-4,con+0.4,plr+2"`, `duration` (s), `is_persistent`, `implementation`
  (třída logiky), `exclusivity`, `lifetime`.
- Zkouška dovednosti (KM-A-20): obtížnost soupeře v UI lehká 11 / střední 17 / těžká 24; výsledek v rozsahu 0–1:
  > 0,75 velký úspěch, > 0,5 úspěch, < 0,25 velký neúspěch; `GeneralPropertyDiffToSkillCheckResult` 0,25 (rozdíl
  hodnot, který dá výsledek −1/1); váhy přesvědčit/donutit: výřečnost 0,8; ohromit/ovládnout 0,2; strach: krev
  0,15, špína 0,1; pověst pod 0,5 zkoušku ztěžuje. XP za zkoušku: dovednost +3 úspěch / +1 neúspěch; výřečnost
  nejvýš 40 (přesvědčení), 25 (jiná zkouška), 12,5 (neúspěch).
- Odkud XP (KM-A-20, učení prací): zásah zbraní 3 / v kombu 4 / zabití 20 / blok 0,5 / dokonalý blok 2,5 /
  odveta 4 (dovednost); vlastnost: zásah 2 / kombo 6 / zabití 12; obratnost +10 za úhyb v okně; vitalita +10 za
  zabití, +1,5 za skok, +2 za přelez, +6,4 za uběhnutou dávku (`AthleticXPAwardDistance` – vzdálenost není v
  tabulce); síla a vitalita +8 za 50 m (lehce přetížen) až 10 m (2× přetížen); bylina +5; lov: zabití 20, vyvržení
  8 (× koeficient zvířete); plížení: pobyt nepozorován 10 (+ agility 10), tichý útok 30–50, nezdar 10; čtení
  30 XP/h, kniha bez dovednosti 30; oprava sadou 1,5 za bod zdraví; vaření 1 / sušení 0,5 / uzení 3; alchymie
  nezdar 5, druhá jakost ×1,35, třetí ×2; kovářství dokončení na max. jakost 135; praní 10; broušení 125/15.
- Účinky dovedností (příklady z KM-A-20): rychlost útoku +0,1 na úroveň rozdílu obratnosti a +0,05 na úroveň
  rozdílu dovednosti, změna nejvýš ±0,25 (hráč proti NPC); plížení na stropu: kroky tišší (koef. 0,6), čas
  rozpoznání delší (0,6), dohled NPC kratší (0,3); luk: přiblížení od úrovně 10, +1,5° na úroveň; byliny: poloměr
  sběru 0,4 m + 0,04 m/úroveň, počet × 0,25·√úroveň; pád na max. obratnosti × 0,667; nosnost 90 lb + 10 lb za
  bod síly (nejvýš 600); vyčerpání (exhaust 0) násobí sílu, obratnost, výřečnost i charisma 0,75; únik z náhodné
  události (sekce 2.4).

**Návrh `pravidla/svet/dovednosti.json`** (vlastní názvy, rok 1393; čísla, která nejsou přímo z KCD2, jsou
NEOVĚŘENO):

```json
{
 "popis": "Dovednosti hrace (vzor KCD2: KM-A-20, KM-A-21; uceni praci, strop, perky). Cte scripts/dovednosti.gd (budouci).",
 "strop": 20,
 "_strop": "KCD2 30 (SkillCap, StatCap). Nase hra je kratsi -> 20 NEOVERENO",
 "xp_krivka": {"zaklad": 25, "prirustek": 35, "vzorec": "zaklad + prirustek * uroven",
   "_vzorec": "cisla KCD2 SkillXPLevelBase/Diff (KM-A-20), tvar vzorce NEOVERENO"},
 "vlastnosti": {
  "sila":     {"kcd2": "strength", "xp_krivka": {"zaklad": 25, "prirustek": 40}},
  "hbitost":  {"kcd2": "agility",  "xp_krivka": {"zaklad": 25, "prirustek": 40}},
  "vytrvalost": {"kcd2": "vitality", "xp_krivka": {"zaklad": 25, "prirustek": 35}},
  "vyrecnost": {"kcd2": "speech",  "xp_krivka": {"zaklad": 25, "prirustek": 40}}
 },
 "dovednosti": {
  "mec":        {"kcd2": "weapon_sword", "vlastnost": "hbitost"},
  "tezka_zbran":{"kcd2": "heavy_weapons", "vlastnost": "sila"},
  "strelba":    {"kcd2": "marksmanship", "vlastnost": "sila"},
  "pest":       {"kcd2": "weapon_unarmed", "vlastnost": "sila"},
  "jezdectvi":  {"kcd2": "horse_riding", "vlastnost": "vytrvalost"},
  "plizeni":    {"kcd2": "stealth", "vlastnost": "hbitost"},
  "zlodejstvi": {"kcd2": "thievery", "vlastnost": "hbitost"},
  "bylinkarstvi": {"kcd2": "alchemy (+ herbalism)", "vlastnost": "vyrecnost"},
  "ranhojicstvi": {"kcd2": "first_aid", "vlastnost": "hbitost"},
  "pismo":      {"kcd2": "scholarship", "vlastnost": "vyrecnost"},
  "remeslo":    {"kcd2": "craftsmanship", "vlastnost": "sila"},
  "lov":        {"kcd2": "survival + houndmaster", "vlastnost": "vytrvalost"},
  "piti":       {"kcd2": "drinking", "vlastnost": "vytrvalost"}
 },
 "_vlastnost": "vlastnost, ktera dostane cast XP (KCD2 SecondaryStatXPRatio 1). Prirazeni NEOVERENO",
 "xp_za": {
  "zasah": 3, "zasah_kombo": 4, "zabiti": 20, "blok": 0.5, "dokonaly_blok": 2.5, "odveta": 4,
  "vlastnost_zasah": 2, "vlastnost_kombo": 6, "vlastnost_zabiti": 12,
  "uhyb_hbitost": 10, "skok_vytrvalost": 1.5, "prelez_vytrvalost": 2,
  "bylina": 5, "ulovek": 20, "vyvrzeni": 8, "plizeni_nepozorovan": 10,
  "cteni_za_h": 30, "oprava_za_bod": 1.5, "zkouska_uspech": 3, "zkouska_nezdar": 1,
  "_": "vse KM-A-20 (SkillXP*, StatXP*, HerbGatherXP, HunterXP*, StealthSneakBaseXp, ReadingXpPerHour, SkillXPUseRepairKit, SkillXPSkillCheck*)"
 },
 "zkouska": {"lehka": 11, "stredni": 17, "tezka": 24,
             "velky_uspech": 0.75, "uspech": 0.5, "velky_nezdar": 0.25, "rozdil_na_vysledek": 0.25},
 "perky": {"od_urovne": 4, "kazdych": 4, "_": "KCD2: 13 bodu od urovne 6 do 30 (KM-A-20); nase 5 perku na dovednost pri stropu 20 NEOVERENO"},
 "ucinky": {
  "plizeni": {"kroky_tissi_na_stropu": 0.6, "rozpoznani_delsi_na_stropu": 0.6, "dohled_kratsi_na_stropu": 0.3},
  "hbitost": {"rychlost_utoku_za_uroven": 0.1, "pad_na_stropu": 0.667},
  "sila":    {"nosnost_zaklad_kg": 41, "nosnost_za_bod_kg": 4.5, "_": "KCD2 90 lb + 10 lb/str (KM-A-20), prepocet na kg"},
  "bylinkarstvi": {"polomer_m": 0.4, "polomer_za_uroven_m": 0.04}
 },
 "ucinek_format": "buf jako KCD2 buff_params: [{\"stat\": \"charisma\", \"zmena\": -4}], trvani_s, trvaly"
}
```

Napojení: `plizeni` násobí hodnoty v `postavy.json vnimani` (rozpoznání, dohled) a `rozpoznani_s` z
`reserse_reakce_kcd2.md` 6.1 se prodlouží nejvýš o 0,6 na stropu.

### 2.2 Oblečení (sekce „Postavy – vzhled“)

**KCD2 (KM-A-23, KM-A-25, KM-A-64, KM-A-26, KM-A-78, KM-A-24):**

- Postava = komponenty: tělo, hlava, vlasy, vousy (u zvířat ocas), oblečení (KM-A-25).
- Komponenta má: konfiguraci (rasa, pohlaví, typ zbroje, archetyp), **skrývací skupiny**, **tvarové morfy**
  (proti prolínání vrstev, i „nafouknutí“ kabátce přes plát), štítky (pro rozdělení ve světě), prvky (model:
  skin, VCloth, kyvadlové klouby), **features** (oblasti podle ID barvy, do nich materiál z atlasu).
- Skrývací skupiny: bitové pole v alfa kanálu vrcholové barvy, **nejvýš 8 skupin (0–7)** na díl; 255 = vždy vidět,
  254 = skryt se skupinou 0, 0 = skryt s jakoukoli. Oblečení zapne svoje skupiny na celé postavě (i na jiných
  dílech). Zvláštní skupina FirstPersonView pro hráče v první osobě (KM-A-64).
- Sloty a vrstvy (KM-A-23):
  - Trup: **body garment** (tunika, jupon, pourpoint nebo prošívanice/gambeson, každá s malým a velkým měšcem a
    druhým opaskem jako skrývatelnou geometrií) → **chainmail** (kroužková košile nemá vlastní model, je to
    malovaná feature na prošívanici; 2 délky sukně, 2 délky rukávů) → **body plate** (kyrys, brigantina; obsahuje
    geometrii nejběžnější délky prošívanice) → **coat** (waffenrock, plášť; rukávy žádné/krátké/dlouhé, morf
    „nafouknout“ přes plát).
  - Paže: **arm armour** (obsahuje krátký rukáv kabátce, vyhrnutý dlouhý rukáv a feature prošívanice i kroužků;
    ramenní plát skrývatelný; konec v jednotné délce do rukavice) → **gloves** (kožené, plátové; široký otvor).
  - Nohy: **hose** (nohavice; jednotný šev u kotníku a v bocích, objem pro sukně a vysoké boty) → **leg plate** →
    **boots** (3 výšky: nízké, po kotník, po koleno, každá s vlastní feature; ostruhy skrývatelné) → **spurs**.
  - Hlava: **coif** (látková, prošívaná malá a velká, kroužková; velká má morf pod kapuci) → **collar** (jednotný
    šev krku, pod dlouhou čepicí) → **hood** (s kapucí na hlavě a bez, 2 modely) → **helmet** (klobouky, čepice,
    přilby; přilba bez kroužkového závěsu nese geometrii čepic uvnitř; hledí má standardní kost pro animaci).
- Přebarvení: materiál z atlasu (kovy, látky, prošívanice, kroužky, kůže, kožešina, dřevo) přiřazený feature;
  odstín, sytost a jas, u některých lesk; dlaždicování UV stejné jako u kořenového materiálu; „Grime“ (špína) a
  druhý materiál „Scratches“ (opotřebení, když věc ztrácí zdraví). Změna materiálu atlasu změní všechny šaty, které
  ho sdílejí. Skrytí části: materiál NoDraw na feature (KM-A-26, KM-A-78).
- Špinění a krev (KM-A-20): oblečení zašpiní na 100 % za 35 km chůze plnou rychlostí (`FullClothDirtyingOnFullSpeed`
  35000 m), při poloviční rychlosti za 500 m (`…ZeroSpeed`, popis v tabulce si s názvem odporuje); krvácení
  naplno = zakrvavené za 240 s; útočník dostane 5–10 % krve z rány, oběť 30–50 %; kopání hrobu = špína 0,45;
  nošení pytle +0,04; čisté do 0,25; praní dovednosti odstraní 0,3 (min.) až 0,8 (max.).
- Opotřebení vrstev (KM-A-20): rána sníží zdraví vrstvy, která ji zastavila, o 0,3 × poškození, vrstev nad ní o
  0,375 ×, pod ní o 0,0075 ×; obuv −0,0001 za metr (přepočet po 50 m) → nová obuv vydrží ~10 km.

**Návrh `pravidla/svet/obleceni.json`:**

```json
{
 "popis": "Odev a zbroj postav (vzor KCD2 KM-A-23 vrstvy, KM-A-64 skryvaci skupiny, KM-A-26 atlas). Postava = telo + hlava + vlasy + vousy + kusy odevu.",
 "sloty": [
  {"id": "kosile",    "cast": "trup", "vrstva": 0, "_": "KCD2 v KM-A-23 neuvedena (infografika chybi) - NEOVERENO"},
  {"id": "suknice",   "cast": "trup", "vrstva": 1, "kcd2": "body garment (tunika/prosivanice)"},
  {"id": "krouzky",   "cast": "trup", "vrstva": 2, "kcd2": "body chainmail", "jen_feature": true},
  {"id": "plat",      "cast": "trup", "vrstva": 3, "kcd2": "body plate"},
  {"id": "kabatec",   "cast": "trup", "vrstva": 4, "kcd2": "coat", "morf": "nafouknout_pres_plat"},
  {"id": "pazni",     "cast": "ruce", "vrstva": 3, "kcd2": "arm armour"},
  {"id": "rukavice",  "cast": "ruce", "vrstva": 4},
  {"id": "nohavice",  "cast": "nohy", "vrstva": 1, "kcd2": "hose"},
  {"id": "nohy_zbroj","cast": "nohy", "vrstva": 3, "kcd2": "leg plate"},
  {"id": "obuv",      "cast": "nohy", "vrstva": 4, "vysky": ["nizka", "kotnik", "koleno"]},
  {"id": "ostruhy",   "cast": "nohy", "vrstva": 5},
  {"id": "cepec",     "cast": "hlava","vrstva": 1, "kcd2": "coif"},
  {"id": "obojek",    "cast": "hlava","vrstva": 2, "kcd2": "collar"},
  {"id": "kapuce",    "cast": "hlava","vrstva": 3, "kcd2": "hood", "varianty": ["na_hlave", "spustena"]},
  {"id": "pokryvka",  "cast": "hlava","vrstva": 4, "kcd2": "helmet (klobouk, cepice, prilba)"}
 ],
 "skryvaci_skupiny": {"max": 8, "_": "KM-A-64: bity 0-7 v alfe vrcholove barvy",
   "seznam": ["mesce", "druhy_opasek", "rukav_dlouhy", "noha_nad_kotnikem", "ostruhy", "cepec_pod_prilbou", "vlasy_pod_kapuci", "prvni_osoba"]},
 "vychozi_ztrata": {"nova_obuv_km": 10, "spina_plna_km": 35, "krev_plna_s": 240,
   "_": "KM-A-20 ShoeHealthDecrease, FullClothDirtyingOnFullSpeed, ClothesBloodSoakOnMaxBleeding"},
 "poskozeni_vrstvy": {"zastavila": 0.3, "nad": 0.375, "pod": 0.0075},
 "prebarveni": {"atlas": "pravidla/svet/materialy_odevu.json (budouci)", "meni": ["odstin", "sytost", "jas", "lesk"], "dlazdice_jako_koren": true},
 "vykon_tablet": {"kusu_na_postavu_max": 6, "slouceni_do_site": true,
   "_": "NEOVERENO: kazda vrstva = draw call navic; NPC slit do 1-2 siti pri nacteni (pravidla_modelu postava atlasy 2)"}
}
```

Dojem z oblečení (třída, nápadnost, charisma) je už v `reserse_reakce_kcd2.md` 6.4 (`hrac_dojem.vzhled`). Oblečení
na něj jen napojit: KCD2 charisma kusu × `sqrt(zdravi)·0,6 + 0,4` (KM-A-89) a × špína (`ArmorDirtToCharismaCoef`
0,8, KM-A-20).

### 2.3 Předměty: jakost a opotřebení

**KCD2 (KM-A-89, KM-A-90, KM-A-17, KM-A-88, KM-A-20):**

- Zdraví věci 0–1 (hráč ho přímo nevidí). Jakost 1–4 je interval zdraví, intervaly se překrývají:
  1: 0–0,1; 2: 0,075–0,3; 3: 0,225–0,6; 4: 0,45–1 (4. jakost jen výrobou hráče) (KM-A-89).
  Překryv `ItemHealthOverlapCoef` 0,25; pod polovinou překryvu roste šance na pokles jakosti, nejvýš 0,8
  (`ItemQualityDecreaseProbability*`, KM-A-20).
- Vzorce (KM-A-89):
  - útok = `Attack·(√zdravi·0,6 + 0,4)` (`WeaponStatusToAttackCoef` 0,6)
  - obrana zbroje a charisma: stejně s 0,6
  - cena = `Price·(zdravi·0,99 + 0,01)` (`ItemHealthPriceStatusWeight` 0,99)
  - ceny v databázi v decigroších (1 groš = 10 decigrošů)
- Upozornění na poškození (KM-A-20): poškozené pod 0,4, skoro rozbité pod 0,2. Zbroj pod 0,3 a zbraň pod 0,7
  dostávají poškození rychleji.
- Opotřebení (KM-A-20): zbraň při zásahu do zbroje −0,002 × obrana soupeře, při bloku −0,001 ×; střelná −0,1 za
  výstřel (jednotka „status“); vrstvy oblečení viz 2.2.
- Oprava (KM-A-20): u řemeslníka cena × 0,45 (+0,005 za bod dovednosti řemeslníka), opravit jakost 2/3/4 může
  řemeslník s dovedností 3/5/15, opravnou sadou 5/12/16; kapacita sady 600 grošů opravy; obchod si vlastní zboží
  opraví o 5 % denně (`RestockRepairPerDay`).
- Zbraně podle vzhledu: levná (matná, otlučené ostří), běžná, drahá (lesklá, dokonalý tvar); sekery 3 zóny
  broušení, meče 5 (KM-A-88).
- Řádek předmětu (KM-A-17): `Attack, AttackModStab/Slash/Smash, Class, SubClass, Defense, MaxStatus, StrReq,
  AgiReq, IsBreakable, BrokenItemClassId, Visibility, Conspicuousness, Charisma, SocialClassId, WealthLevel,
  MaxQuality, Weight, Price, FadeCoef, Model, IconId, UIName`.
- Sady vybavení (KM-A-90): zdroje = jiná sada / sada oblečení / sada zbraní / předmět; výběr `All` (vše),
  `OneChild` (jeden zdroj, váženě; u NPC nejbližší `CombatLevel`), `AmountCount` (N ± odchylka kusů),
  `AmountFraction` (N ± odchylka %). Vlastnosti `Weight`, `Quality` 1–4, `Health`+`HealthVariation`,
  `Condition`+`ConditionVariation`, `Amount`. Stejný systém plní NPC, truhly i zboží obchodu.

**Návrh `pravidla/svet/vybava.json`** (jméno `predmety` už nese `modely.json`):

```json
{
 "popis": "Jakost a opotrebeni veci (vzor KCD2 KM-A-89, KM-A-20, KM-A-90). Zdravi 0-1, jakost = interval zdravi.",
 "jakost": [
  {"stupen": 1, "nazev": "chatrna",  "zdravi": [0.0, 0.1]},
  {"stupen": 2, "nazev": "obycejna", "zdravi": [0.075, 0.3]},
  {"stupen": 3, "nazev": "dobra",    "zdravi": [0.225, 0.6]},
  {"stupen": 4, "nazev": "mistrovska","zdravi": [0.45, 1.0], "jen_vyroba": true}
 ],
 "pokles_jakosti": {"prekryv": 0.25, "od_podilu_prekryvu": 0.5, "sance_max": 0.8},
 "vzorce": {
  "utok":   "zaklad * (sqrt(zdravi) * 0.6 + 0.4)",
  "obrana": "zaklad * (sqrt(zdravi) * 0.6 + 0.4)",
  "dojem":  "zaklad * (sqrt(zdravi) * 0.6 + 0.4)",
  "cena":   "zaklad * (zdravi * 0.99 + 0.01)"
 },
 "prahy": {"poskozene": 0.4, "skoro_rozbite": 0.2, "zbroj_rychleji_pod": 0.3, "zbran_rychleji_pod": 0.7},
 "opotrebeni": {"zbran_do_zbroje_za_obranu": 0.002, "zbran_blok_za_obranu": 0.001, "obuv_za_m": 0.0001},
 "oprava": {"remeslnik_cena": 0.45, "remeslnik_za_bod": 0.005,
   "remeslnik_min_dovednost": {"2": 3, "3": 5, "4": 15},
   "sada_min_dovednost": {"2": 5, "3": 12, "4": 16},
   "obchod_za_den": 0.05,
   "_": "KCD2 strop 30; pri nasem stropu 20 (dovednosti.json) prepocet x 2/3 NEOVERENO"},
 "mena": {"jednotka": "gros", "dil": "parvus", "dilu_v_jednotce": 10,
   "_": "KCD2 decigros (KM-A-89); prazsky gros 1393 a jeho deleni NEOVERENO - resers"},
 "sady": {"vyber": ["vse", "jeden", "pocet", "podil"], "pole": ["vaha", "jakost", "zdravi", "zdravi_rozptyl", "pocet"],
   "_": "KM-A-90 All/OneChild/AmountCount/AmountFraction"}
}
```

### 2.4 Náhodné události a místa událostí

**KCD2 (KM-A-68, KM-A-69, KM-A-70, KM-A-73, KM-A-74, KM-A-75, KM-A-20):**

- **Událost** (definice): `Cooldown`, `Tags`, vstupy OnSpawn/OnDespawn, výstupy ActivateCooldown, IsEnabled.
  Definice je v knihovně, **instance** v místě události (každá instance má vlastní stav, dá se vypnout zvlášť).
- **Varianta**: `Profile` (co se načte), `Weight` (pravděpodobnost výběru, **roste lineárně s dobou od posledního
  výběru této varianty**), `Tags`, skupiny NPC: zásobník duší (seznam jmen) nebo jedno jméno, `Count` a `Count SD`
  (normální rozdělení; 0 = přesný počet), body vzniku, zástupce rozvrhu (scheduler proxy). Varianty se dědí:
  varianta s podvariantami je **abstraktní** (sama nevznikne, pokud se nevypne Abstract); OnSpawn běží u všech
  předků, IsSpawned jen u té skutečné (příklad: Přepadení na cestě → Raubritter → Kůň).
- **Místo události**: oblast obvykle **do 8 × 8 m**; střed (`fastTravel_close`), kam hráče postaví přerušené
  rychlé cestování; body `fastTravel_far1–4` **asi 30 m** od středu na každé cestě, natočené k události. Události
  dál než **~25 m** od sebe = samostatná místa. **Dvě události stejného typu na jednom místě nejdou.** Spouštěcí
  oblast taková, aby hráč při vstupu **neviděl střed** (na otevřené ploše víc malých oblastí na cestách). Ve vsi a
  ve městě události rychlé cestování nepřerušují. Jméno `<kód kraje>_<místo>` (např. `tvid_road2`); obecná jména
  `road`, `roadJunction`. Než vznikne nové místo, ověřit, že na stejném místě (8×8 m) už nějaké není.
- **Obecné události rychlého cestování** (GenericRandomEvent): typ a cooldown; tři úrovně cooldownu (globální
  obecný, události, varianty); výsledek „cestování pokračuje“ (unikl nebo nic nevzniklo) nebo „únik se nezdařil“
  (indikátor zločinu).
- **Vzorce odhalení** (KM-A-20): dohled události EVR = 0,5·dohled varianty + 0,5·dohled místa; jak snadno událost
  odhalí hráče = 0,5·EVR + 0,5·viditelnost hráče; dohled hráče při cestování = 0,5·dohled + 0,5·přežití;
  šance na únik = `(V·(1−viditelnost) + S·přežití + E·výsledek_odhalení) / (V+S+E)`, V = S = E = 1; přepadení
  (hráč přepadne je) stejně s plížením místo přežití; útěk = `(V·vitalita + E·(1−|odhalení|)) / (V+E)` (váhy v
  exportu tabulky chybí).

**Návrh `pravidla/svet/udalosti.json`:**

```json
{
 "popis": "Nahodne udalosti (vzor KCD2: KM-A-68, -69, -74, -75, KM-A-20). Udalost = definice; mista = zaznamy ve svete; instance = udalost na miste.",
 "mista": [
  {"id": "lhota_cesta1", "stred": [0, 0], "oblast_m": 8, "spoustec": [{"stred": [0, 0], "r_m": 12}],
   "daleko": [{"p": [0, 0], "yaw_st": 0}], "ves": false,
   "_": "souradnice doplnit; spoustec tak, aby hrac stred pri vstupu nevidel (test smyslu: primka spoustec-stred zakryta terenem nebo lesem)"}
 ],
 "pravidla_mist": {"oblast_max_m": 8, "samostatne_od_m": 25, "daleko_m": 30, "jeden_typ_na_miste": true,
   "_": "KM-A-69"},
 "udalosti": [
  {"id": "prepadeni_na_ceste", "odstup_h": 48, "stitky": ["cesta", "nasili"],
   "varianty": [
    {"id": "loupeznici", "abstraktni": true, "vaha": 1.0,
     "skupiny": [{"zasobnik": "loupeznici_les", "pocet": 3, "pocet_sd": 1, "body": "vznik_kraj"}],
     "podvarianty": [{"id": "rytir_loupeznik", "vaha": 0.3}]},
    {"id": "zraneny_poutnik", "vaha": 0.5, "skupiny": [{"jmeno": "poutnik", "pocet": 1, "pocet_sd": 0}]}
   ]}
 ],
 "vyber": {"vaha_roste_s_h": "linearne od posledniho vyberu varianty (KM-A-75)", "odstup_vychozi_h": 24,
   "odstup_globalni_h": 6, "_odstup": "tri urovne jako KCD2 (KM-A-70); hodiny NEOVERENO"},
 "odhaleni": {"dohled_varianta_podil": 0.5, "skryti_dohled_podil": 0.5,
   "unik_vahy": {"neviditelnost": 1, "lov": 1, "odhaleni": 1},
   "prepadeni_vahy": {"neviditelnost": 1, "plizeni": 1, "odhaleni": 1},
   "_": "KM-A-20 Event*Weight*; dovednosti z dovednosti.json (preziti -> lov)"},
 "zasobniky": {"loupeznici_les": ["loupeznik_1", "loupeznik_2", "loupeznik_3"]}
}
```

U nás není rychlé cestování. Spouštěčem je chůze nebo jízda spouštěcí oblastí, střed se hráči ukáže až za ohybem
cesty. Test smyslu by měl hlídat, že místo leží mimo vodu, stavby a pásma (`pasma.cesta`) a že má aspoň jeden bod
`daleko` na ose cesty z `cesty.json`.

### 2.5 Zločin (jen to, co rešerše reakcí nemá)

`crime.xml` (KM-A-27): `expiration` (dny), `fine` (decigroše), `importance`, `isCrime`, `isSpreadable`,
`isViolent`, `jail` (dny), `scalingWithSocialClass`. Příklad napadení: platnost 5, pokuta 1500 (= 150 grošů),
vězení 5, důležitost 130, šíří se, násilné, podle třídy. Parametry skriptů (`script_params.xml`): dlouhodobá
paměť vniknutí 7200 s, práh malé krádeže 50, dosah kontroly skrýší 40 m. Po vězení oslabení na 0,2 × délka trestu,
nejvýš 240 h (`JailRecovery*`, KM-A-20). Výklad platnosti v paměti NPC je v `reserse_reakce_kcd2.md` 6.4.
Návrh až v sekci zločinu: `pravidla/svet/zlociny.json` se stejnými poli (česky: `platnost_dni, pokuta, dulezitost,
siri_se, nasilny, vezeni_dni, podle_tridy`).

---

## 3. Tabulka: co kam a kdy

| Co | Soubor / klíč | Kdy | Zdroj |
|---|---|---|---|
| `texel_m` u tříd (PC 512, tablet 256 NEOVĚŘENO) + test `texel` (0,5×–2×) | `pravidla_modelu.json` sloupec + `tools/test_svet.gd` / import | **teď** | KM-A-45, KM-A-54 |
| `textura_podil` (ORM 0,25, normála 1 nebo 0,5) | `pravidla_modelu.json` | **teď** (přepočet textur při importu) | KM-A-45 |
| `lod_pomer_max: 0.5` jako mez testu `modely` | `pravidla_modelu.json` | **teď** (dnes splněno) | KM-A-46 |
| rozdělit `predmet` na drobny/stredni/velky (bez LOD / 1 LOD / LOD od 1 m³) | `pravidla_modelu.json tridy` | **teď** (`modely.json` je už používá) | KM-A-46, KM-A-45 |
| `lod_materialu` | `pravidla_modelu.json` | **teď** pro stavbu, strom; ostatní při importu | KM-A-46 |
| `lod_vnitrek: cerna_vypln`, `vypln_od_zdi_m: 0.3` | `pravidla_modelu.json stavba` | **teď** (domy krok B) | KM-A-46 |
| `lod_nasobek` 1,7/1,33/1,0 (výklad LodRatio, NEOVĚŘENO) | záznam stavby v `modely.json` / lokace | po ověření snímkem | KM-A-46 |
| `stin: "proxy"`, `troj_stin`, `stin_alfa` | `pravidla_modelu.json` | **teď**: nejdřív jeden dům na tabletu (Mobile + `shadow_mesh` NEOVĚŘENO) | KM-A-49 |
| `okluzor: "steny"`, `troj_okluzor_max` (NEOVĚŘENO), oboustranné vnější zdi | `pravidla_modelu.json` + `pasma.test` | **teď** (navazuje na okluzor lesa) | KM-A-47 |
| `okluzor_teren_pod_m` (NEOVĚŘENO) | `pravidla_sveta.json pasma.test` | později (výkon brána 4) | KM-A-47 |
| `kolize`: stavba `boxy+trimesh_lod1`, `kamen: false`, rozpor u `drevo` | `pravidla_modelu.json` | **teď** | KM-A-48 |
| `povrch` + příznaky (jen_kun, kun_ignoruje, schody, pruhledne_pro_pohled) | `pravidla_modelu.json` / `modely.json` | **teď** sloupec, zapojení se zvuky kroků a vnímáním | KM-A-48 |
| `vyska_patra_m`, `tloustka_zdi_m`, `hloubka_okna_m`, `schod_vyska_m`, `schod_hloubka_m`, `zebrik_pricka_m`, `sedak_m` | `pravidla_sveta.json pasma.budova` + test `rozmery` | **teď** | KM-A-52 |
| `dvere_vyska_min_m`, `dvere_sirka_min_m`, `strop_svetly_min_m` (vše NEOVĚŘENO, z kapsle) | `pasma.budova` + test `rozmery` | **teď** jako mez z kapsle; čísla potvrdit rešerší | odvozeno, ne Warhorse |
| `zabradli_m` | `pasma.budova` | po rešerši (NEOVĚŘENO) | – |
| `STEP 0.45` z `player.gd` → `hrac.json schod_max_m` | `hrac.json` | **teď** (číslo v kódu) | pravidlo projektu |
| `pad` (1,5 / 2,2 / 8 m), `skok_vydrz` 9, `obnova_pohyb_podil` 0,75 | `hrac.json` | **teď** | KM-A-20 |
| `beh_za_s` 3,5 a `obnova_za_s` 22 | `hrac.json` | po rozhodnutí Míši (mění pocit hry; max výdrže KCD2 NEOVĚŘENO) | KM-A-20 |
| `kun.trysk_dobeh_s` 1,0, jednotka `vydrz_obnova` | `jizda.json` | **teď** | KM-A-20 |
| kontrolní seznam optimalizace LOD0 stavby | `docs/pipeline.md` | **teď** | KM-A-51 |
| `detail` (512, dlaždice, zhasne 10 m) | `pravidla_modelu.json` | po změření ceny na tabletu | KM-A-45, KM-A-53 |
| třída `zbran` (bez LOD) | `pravidla_modelu.json` | sekce boje / předmětů | KM-A-88 |
| `dovednosti.json` | nový | sekce **Dovednosti hráče** | KM-A-20, KM-A-21, KM-A-16 |
| `obleceni.json` (+ `materialy_odevu.json`) | nový | sekce **Postavy – vzhled** | KM-A-23, -24, -25, -26, -64, -78, KM-A-20 |
| napojení oblečení na `hrac_dojem` | `postavy.json` | sekce Postavy – vzhled | KM-A-89, KM-A-20 |
| `vybava.json` (jakost, vzorce, oprava, sady) | nový | sekce předmětů / obchodu | KM-A-89, KM-A-90, KM-A-17, KM-A-20 |
| `udalosti.json` + kontrola míst v testu smyslu | nový | sekce **náhodné události** | KM-A-68, -69, -70, -74, -75, KM-A-20 |
| `zlociny.json` | nový | sekce zločinu | KM-A-27, KM-A-20 |
