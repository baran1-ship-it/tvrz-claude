# Stav projektu – Odkaz Havrana (20. 10. 2026, verze 0.56b, blok 0.57 louka)

Historie měření a starší otevřené body: docs/stav_historie.md.

## Rozpracováno (stavitel, průběžně – pravidlo rádce 18:25)

### 26. 10. – MĚŘENÍ 0.89 NA TABLETU (Míša, okruh během, 29 fotek panelu, t 130–622 s)
| místo | FPS | kreslení (draw) | troj. | fyzika/snímek | skripty | příčina záseku na panelu |
|---|---|---|---|---|---|---|
| most tvrze (-1,25) | 37 | 844 | 2,30 M | 1 | 2 | kreslení |
| 2. nádvoří (4,1) | 15 | 1365 | 2,80 M | 3 | 7 | kreslení (32) |
| palác (8,-9) | 29 | 895 | 1,90 M | 1 | 2 | kreslení |
| louka/cesta u tvrze | 28–36 | 650–780 | 1,8 M | 1–2 | 2–3 | kreslení 64–86 |
| tábor (3,222) | 39 | 241 | 1,35 M | 1 | 2 | kreslení |
| **hostinec venku/uvnitř (-60,878)** | **10–19** | 1247–1273 | **3,7 M** | 2 | 3 | kreslení 71–100 |
| **les u hostince (-2,867)…(73,829)** | **11–25** | 923–1226 | **2,9–3,7 M** (stromy 0,73, byliny 0,53) | 2 | 2–5 | kreslení 33–111 |
| lom (141,916) | 37 | 488 | 0,97 M | 1 | 2 | kreslení |
| ves (413,781)…(471,832) | 30–32 | 835–1040 | 1,8 M | 2–3 | 3–5 | kreslení |
| **rybník ve vsi, molo (525,888), stání** | **9–15** | 1280–1438 | 2,5–2,7 M (stavby 0,98) | **43–63 ms (2 kroky)** | 3 | **fyzika** |

**Závěr:** (1) Mimo rybník jsou „záseky“ trvale pomalé kreslení (GPU): fyzika 1–3 ms, skripty 2–7, plánovač ≤ 2,3 ms → K1
(plánovač/fyzika) záseky nevysvětlí; nejhorší místa mají > 1200 kreslení a > 3 M troj. (hostinec, les u hostince, 2. nádvoří).
(2) **Rybník ve vsi: skutečná fyzika 43–63 ms každý snímek ve stání** (PC test v pohybu 8 ms) → rozbor testem `fyz_misto`
(vypínání objektů po jednom). (3) Počítadlo záseků (1689 za 8 min) bylo k ničemu: při 20–30 FPS je > 40 ms skoro každý
snímek → nově zásek = > 40 ms a 1,6× nad průměrem ~1 s, ostatní „pomalé snímky“ zvlášť. (4) „nejdelší“ na panelu lhalo
(FPS 10 a nejdelší 43 ms): `dt` je vyhlazené (delta_smoothing) → panel bere skutečnou délku z razítek. (5) Paměť: halda
1,26–1,45 GB (po startu +600 MB/min, pak ±), PSS 2,2–2,4 GB – nad cílem 1,25 GB, ale neroste.
**Návrh pro rádce:** K1 = GPU: počet kreslení (cíl < 700) a troj. (< 2 M) v hostinci a lese u hostince (LOD stromů/bylin,
interiér hostince jen uvnitř = portály K4), + oprava fyziky u rybníka. Plánovač dál neladit.

### 26. 10. – K0 (rádce 16:45) → vydání 0.89
**Ověření K0 podle kódu (dotaz 26. 10., commit 8f74336) – našel jsem tři vady, opraveno:**
1. *Záznam při každém snímku > 40 ms*: ano (diag `_process` každý snímek, za `ready_done`), ALE příčina byla o snímek
   posunutá: `dt` ve snímku N = délka snímku N−1, kdežto skripty (`_cas_minule`) a fyzika patřily snímku N. A
   `Performance.TIME_PHYSICS_PROCESS` je v 4.4 **maximum jednoho kroku za poslední sekundu** (main.cpp: `physics_process_max`,
   publikuje se 1× za s, ne součet kroků) → „fyzika“ v záznamu i v testu `fyzika` byla stará až 1 s. **Oprava:** vlastní
   razítka snímku – `physics_frame` a `process_frame` (SceneTree je vysílá před uzly) + konec diag `_process` (běží poslední)
   → pro uzavřený snímek: fyzika (všechny kroky + počet kroků), `_process` (+ měřené skripty, nejdražší), kreslení+čekání,
   celkem; detekce na tomtéž snímku.
2. *„jen FPS“*: ano, detekce běží vždy (i s vypnutým panelem).
3. *Neblokující zápis*: soubor se psal ve vlákně, ale hlavní vlákno při každém záseku dělalo celý `_zapis` – čtení RAM
   (JNI, `/proc/meminfo`, 1× za 30 s **PSS = drahé**), formát řádku a `join` 400 řádků (~140 kB). Při 13–20 FPS na tabletu
   je > 40 ms skoro každý snímek → měřič sám přidával práci každý snímek. **Oprava:** zásek = jen formát řádku do kruhu
   300; soubor `user://zaseky.log` ve vlákně max 2× za s (když předchozí zápis běží, nečeká se); do `diag.log` se zásek
   přidá při běžném zápisu po 2 s (max 10 řádků). Zásek ve snímku s měřením PSS se označí „měřič PSS“.
   Test `fyzika` měří z razítek (dřív četl 1s maximum, po teleportu v něm zůstalo načítání).

**Teren_okoli_kolize (278 692 troj.) – co říká zdroj 4.4 (GodotPhysics3D, projekt jiný engine nemá):**
- BVH trimesh se staví v `ConcavePolygonShape3D._setup` = při `set_faces`/`create_trimesh_shape` (u nás při stavbě světa),
  **ne při prvním dotyku**. Dotaz = průchod BVH (hloubka ~18) + test trojúhelníků v AABB kapsle → desítky troj./dotaz,
  na počtu 278 k skoro nezávisí. Hodnoty 71–489 ms z testu tedy první dotyk nevysvětlí; byly to 1s maxima včetně
  teleportu (bod 1), tvar „do 6 m“ byl jen to, na čem hráč stál. Nové měření běží (test `fyzika` s razítky).
- Docs 4.4: ConcavePolygon „nejpomalejší tvar“, dutý (průnik při velké rychlosti); HeightMapShape3D „rychlejší než
  ConcavePolygon“, bez převisů; dotaz po buňkách mřížky v AABB, bez stromu.
- **Doporučení:** dlaždice ConcavePolygon 32 m z téže sítě terénu (přesně jako obraz: lom, příkop, břehy, cesty A),
  `set_faces` ve WorkerThreadPool, aktivní jen okolí (2 kruhy), BVH dlaždice ~5–10 k troj. = stavba ~ms ve vlákně, paměť
  a uvolňování po kusech. HeightMap převzorkovaný 1 m až tam, kde měření ukáže, že dotaz je drahý: na volné louce
  ano, ale lomové stěny a příkop by z 1m mřížky byly schody/šikminy a nohy by nesouhlasily s obrazem (rozdíl sítě
  a mřížky už dnes až 0,5 m). Rozhodnout po tabletovém měření z opraveného metru.
- **Nové měření (test `fyzika` z razítek, PC):** tvrz 3,2 / 3,3 ms, **lom 3,5 ms** (dřív „245“), ves 8,8, **rybník 8,2**
  (dřív „489“), **hostinec 17,3 ms** (dřív „71“). Staré hodnoty = 1s maxima s načítáním po teleportu. Velký
  `Teren_okoli_kolize` sám drahý není (lom 3,5 ms na něm). Nejdražší je hostinec (-61,875): kolem hráče desítky
  `StaticBody3D` BoxShape3D (nábytek/předměty) + terén → kandidát K2: předměty < 0,5 m bez kolize, sloučit krabice do
  jednoho těla. Dlaždice terénu tedy nejsou kvůli rychlosti dotazu, ale kvůli stavbě/paměti (K2/K3).

- Detektor záseků (diag.gd): každý snímek > 40 ms se zapíše (příčina fyzika / kreslení / skripty + nejdražší skript +
  stav plánovače), i v režimu „jen FPS“ (tam počet záseků a poslední zásek na řádku). Práh jeden: 40 ms.
- Zápis záseku do logu ve vlákně (ne synchronně v hlavním vlákně).
- Plánovač jen jako detail `main: planovac`, nesčítá se do skriptů dvakrát.
- Cesty v terénu A (K5) jsou v 0.89 uvnitř; stavba zrychlena (hledání osy jen v jedné buňce 4 m, dělení 1 m místo 0,7).
- Přepínač kroku fyziky v nastavení (60/3, 60/2 výchozí, 30/2).
- Míša: 3× okruh tvrz–ves–hostinec–lom + 10 min stání → z logu záseků rozhodne rádce o K1.
- Plánovač měřen po částech (`main: plan kolize`, `main: plan rostliny` v detailu panelu a v záznamu záseku).
- **Test `fyzika` (PC, headless) – nejdražší krok fyziky a tvar u hráče:** tvrz (-35,29) 13 ms – `Teren_kolize` 32 517 troj.;
  hostinec (-55,870) 71 ms (také `Teren_okoli_kolize`); rybník (520,880) 489 ms; **lom (150,931) 245 ms – `Teren_okoli_kolize` ConcavePolygonShape3D 278 692 troj.** (jeden tvar
  pro celé okolí). Hypotéza: první dotyk velkého trimesh (BVH) / úzká fáze proti obrovskému tvaru, ne spirála kroků.
  → kandidát pro K2/K5: rozdělit kolizi terénu okolí na dlaždice (nebo HeightMapShape3D 64 m). Čeká na tabletové měření.

### 26. 10. – cesty po 0.87 (Míša: lemy, keře, brod, zelené pásky)
- Okraj cest: travnatá část sítě cesty se nekreslí (zem.gdshader discard při gm > 0,55) → za hranou hlíny skutečný terén
  (pole, suchá louka, náves); terén snížen jen pod hlínou. Louka v pásu kryti za okrajem sází trsy podle průměru okolí 5 m.
- Keře u cest ve shlucích 1–6, mezery 6–45 m (556 ks); rostliny z pásu cest pryč (3983), u cest na profil (3747).
- Brod: profil cesty u vody neplatí (břehy dělá _brody). Hřbet cesty s trávou jen místy.
- Snímky vedle reference: `docs/screens/rozprac_cesta_tvrz.jpg` (3,95), `docs/screens/rozprac_cesta_pole.jpg` (271,736).
- Jdu dál: vydání 0.88 po potvrzení Míši; pak záseky (panel 0.86 – čekám na fotku záseku z tabletu).

### 26. 10. – připomínky stavitele k SYSTÉMU NAČÍTÁNÍ (rádce 16:00)
Souhlas s celkem (tabulka → plánovač → kolize offline → paměť → portály → terén A). Co je v kódu jinak / nejde:
1. **trimesh v hlavním vlákně**: 7 z 8 míst (svet.gd 514, 1459, 1700, 4552, 8208, 8517, 8990) běží **při stavbě světa za
   načítací obrazovkou**, ne za hry – záseky za chůze nedělají. Za hry vzniká kolize jen ve `kolize_okoli` (StaticBody
   po dávkách se **sdílenými** předem postavenými tvary – BVH tvaru se nestaví znovu) a `predmety.spawn` (predmety.gd:151,
   lešení/nábytek při vložení). Měřená „fyzika 25–34 ms“ u hostince a rybníka je **čas kroku fyziky × až 3 kroky na snímek**
   (60 Hz, `max_physics_steps_per_frame = 3` na tabletu): při 13–20 FPS běží 3 kroky → spirála. Ověřuji testem `fyzika`
   (trasy hostinec, rybník doplněny) – který tvar v okolí je drahý. K2 (.kol, dlaždice) má smysl hlavně pro velké díly
   (rybník Rybnik_Teren, hostinec Staticky_*), a navíc **sjednotit krok fyziky**: 30 Hz + interpolace (už zapnutá),
   nebo max 2 kroky/snímek – návrh pro K1 jako měřený přepínač na panelu.
2. **FADE_SELF**: dokumentace 4.4 – prolínání visibility_range v Compatibility není; ověřím snímkem v pásmu prolínání
   na PC; pokud bez účinku → DISABLED (méně práce) a dither jen pro stromy/impostory (pravidlo 4).
3. **HeightMapShape3D**: terén z Blenderu není pravidelná mřížka (Teren_ves, Teren_okoli, rybník); mřížky výšek
   `trava_kraj/trava_ves` se od sítě liší až o 0,5 m (komentář v svet.gd) → chůze by nesouhlasila s obrazem. Návrh: výšky
   HeightMap převzorkovat ze sítě terénu (po 1 m) ve vlákně, dlaždice 64 m – K5.
4. **K5 cesty do terénu A je už napsané** (dnes, commit „Povrchy A“: dělení trojúhelníků u cest ~0,7 m, profil do výšky
   terénu, údaje cesty v CUSTOM0/1, hrubý pás bez kolize). Zatím bez snímku; přidá terénu trojúhelníky (počet změřím v K1).
5. **Louka** (louka.gd) má vlastní rozpočet a vlákna – do plánovače ji zapojím jako jednu frontu (jen hlášení ms + délka
   fronty), stavbu ve vláknech nechám.
6. Tabulka tříd: `pravidla/pravidla_modelu.json` už má `tridy` (strom, ker, trava…) s `lod_m` a `kolize` – doplním
   `dosah_m`, `kolize_m`, `stin_m`, `nacitani`, `uvolnit_m`, žádná nová tabulka.
- Šípek (červené bobule) ze světa pryč (Míša). Žebřík: odchod pákou do strany. Záseky na panelu od 100 ms.
- Jdu na K1.

## Rozpočet (Android, Xiaomi Pad 8 / Adreno 825)
- Volání kreslení: max 1500 / snímek
- Trojúhelníky: cíl 2 M / snímek, tolerance do 2,75 M, pokud FPS drží 30+
- Paměť GPU: pod 700 MB (monitor ukazuje zvlášť textury a buffery)
- Hlídání: diag.gd loguje každé 2 s do user://diag.log, varování při 1,5× rozpočtu (s pozicí hráče) do user://diag_varovani.log, panel „Měření výkonu“ v nastavení
- Skály: LOD0 ≤ 3000 troj. (0–40 m, se stínem), LOD1 ~800 (40–120 m), LOD2 ~150 (120–500 m)
- Stromy: plný model do 60 m (stín), zjednodušený tvar 55–120 m bez stínu, za 120 m nic
- Stíny: 2 kaskády, atlas 2048, vegetace (mimo stromy a skály LOD0) bez stínů
- Louka: max 3–4 volání na buňku (32 m); střední pásmo do 100 m, 1,2 trsu/m²
- Drobná vegetace: nízká 22/32/45 m, střední 50/70/95 m (podle kvality)
- Předměty: dosah podle velikosti 20 / 40 / 80 m, drobné (<0,5 m) bez stínu
- Textury: terén a modely 1024, vegetace 512, stromy a skály 1024; vše VRAM komprese + mipmapy (tools/limity_textur.py, spouští vydani.py)
- Prah LOD sítí: rendering/mesh_lod/lod_change/threshold_pixels = 4

## Známá omezení (Compatibility renderer)
- U MultiMesh je transformace instance už ve VERTEX, MODEL_MATRIX je jen uzel (střed 32m buňky louky) –
  vzdálenost pro prolínání se musí brát z polohy vrcholu, ne z MODEL_MATRIX (stebla i kvety.gdshader).
- Není HDR buffer: světlo nad 1 se ořízne před tonemapem → samostatný světelný profil (daylight.gd, `ldr`).

> **ARCHIV (rádce 16:45):** tabulky a čísla 0.57–0.59 níže jsou staré měření (jiný měřič, před K0). Neplatí pro rozhodování o K1.

## 0.57 – blok LOUKA (archiv) (20. 10. 2026, PC, Compatibility, kvalita 1, 1200×800)
| Místo | Kreslení | Troj. | GPU* |
|---|---|---|---|
| louka (60, 60) | 975 | 2.49 M | 892 MB |
| hostinec (-62, 881) | 956 | 2.37 M | 876 MB |
| příkop (0, -36) | 1581 | 3.14 M | 899 MB |
| skály (-80, 300) | 585 | 1.69 M | 891 MB |
| potok u mostu (222, 604) | 848 | 2.56 M | 891 MB |

*GPU na PC v kontejneru. Příkop nad rozpočtem kvůli tvrzi (LOD tvrze odložen, 0.55 už 2,99 M). Snímky docs/screens/057_*.jpg.

**Hlavní příčina děr v trávě na tabletu (od pátku):** kvalita 1 (hustota 0,7) ředila po hashi i výplň – 30 % drnu chybělo všude; na PC se testovalo stejně, ale díry se schovaly v malých snímcích. Výplň se teď kvalitou neřídí. Druhá příčina: drn_atlas je z 93 % průhledný (jednotlivé chomáče) – karta nic nekryla → vlastní atlas vějíře (tools/vejir_atlas.py).

**Louka 0.57:** drn-vějíř (3 karty 50°, 6 troj.) na každém bodě výplně 8/m² + směs podle stanoviště (pravidla_sveta.json vyplnovy_mix), pásma 0–25 m plně / 25–60 m 25 % / do 90 m pryč po čtvrtinách buňky 16 m, trsy 20–110 m, kosená louka jen do 150 m od tvrze a vsi (dál neudržovaná ×1,5 trsů ×1,3 výška), normála trav nahoru ve vertex() (vertex_lighting), paty karet neprůhledné, tmavá pata a AO jen do 40 m.

**Testy (t60/t61):** shadery, sonda, visici (0 z 98 951), kolize, stanoviste, pokryv (100 %), dira (0 skvrn ≥ 400 px na 3 místech; pixelově 8–10 %), prochod 5/5, dalka (3 výhledy) – OK. **pasmo**: 30 a 60 m na všech 3 místech v mezích; 100 m na 2 místech 0,90 a 0,77 (okraj lesa v rámečku u horizontu – barva lesa v dálce, blok 0.58).

**0.58 (výkon tabletu, noční plán 21:15):** kreslení 0,55× (mobil [0,45; 0,55; 0,7]), tráva alpha-to-coverage + MSAA 4× místo discard, frame pacing vypnut, trsy a vysoká tráva na tabletu do 80 m, LOD prah 10 px, stíny 1 kaskáda 40 m, panel ukazuje nejdelší snímek. Pád při teleportu: sdílený FastNoiseLite ve vláknech louky → šum na vlákno, `louka.cekej()` před skokem, příchod na volné místo. Textury: ETC2 .ctex bez horních mip úrovní (tools/textury_tablet.py, 1769 → 458 MB na disku) v opravném balíku `z_textury` (118 MB). PC měření (TVRZ_MOBIL): louka 2,15 M troj. / 934 kreslení, hostinec 2,01 M, příkop 2,80 M; GPU 509–532 MB, z toho textury 284 MB.

**0.59 (pády 0.58):** příčina = MSAA 4× na Adreno 825 (únik nativní paměti ovladače při 3D kreslení, 3–5 MB/s → pád při 1,1–1,8 GB). 0.59h: na tabletu bez MSAA (nastavení „Vyhlazování hran“, výchozí vypnuto), RAM stabilní 1,2 GB. Dále v 0.59: louka (dosah podle vrstev, strop 90 buněk, úrovně hustoty, stavba po částech), RAM na panelu (Android nativní halda) + růst MB/min, zpráva o pádu z logu padlého běhu, voda bez kopie obrazovky, dělení velkých sítí tvrze na čtverce s LOD, automatický test paměti v nastavení.

### Otevřené
- Hostinec na tabletu 26 FPS, 3,7 M troj., 2079 kreslení; příkop kreslení 1770 (dělení sítí – větší čtverce).
- **Troj. ≤ 1,2 M nesplněno** (louka 2,15 M, příkop 2,8 M) – impostory stromů dřív, LOD skal, LOD tvrze.
- **2b unshaded tráva** na PC černá (TVRZ_UNSHADED) – odloženo; **6 plnění bufferu louky po částech** – odloženo.
- Test teleport na PC bez GPU nedoběhne do limitu (~10 skoků ve 2 bězích bez pádu); snímky skály a potok 0.58 chybí.
- **0.55 bez textures/ a audio/** (plamen, kouř, mraky, syntetické zvuky): opraveno v tools/pregeneruj.sh (zaklad), do hry s APK 0.56.
- Tvrz u příkopu ~3 M (síť tvrze 1,2 M) – LOD tvrze odložen (radce 18:30), Míša ověří FPS na tabletu. Portály tvrze v kódu (scripts/portaly.gd), neměřeny.
- Uzel Zivot neprozkoumán. Další: navigační síť z mapy stanovišť a trasy terénem (21:25–21:35), streamování při 12 m/s, import modelů znovu (20:30), mech/zelí, mez s kamením, kurník/meč/ovce. Impostory: otočení v polovičních datech má jen 4 kroky (w = měřítko·256) – opravit kódování.
