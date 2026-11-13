# Jak se stavějí potoky a říčky – rešerše a návrh pro Puchart (13. 11.)

Zadání (Míša, 13. 11.): „udělej další rešerši, jak se stavějí potoky a řeky, nám to funguje, ale není to ono, KCD je TOP“.
Upřesnění během práce:
- hlavní důraz na **břehy** (přechod vody do hlíny) a na **vegetaci u vody**;
- **závazná předloha vzhledu pro všechny toky včetně Veličky** jsou Míšiny fotky skutečných potoků `misa_real_01–04` (viz `README_misa_real.md`), Míša: „takhle by měly vypadat všechny toky“;
- **KCD bereme jako techniku a styl**, ne jako vzhled.

Brody tu nejsou. Řeší je souběžná rešerše `docs/reference/brody/`; tady jen tvrdá hrana vody u brodu, protože ji způsobuje hladina.

Značení: **[zdroj]** = doloženo odkazem, **odhad z fotky** = odečteno od oka ze snímku (není to měření), **NEOVERENO** = nedoloženo, nebo to musí ověřit snímek či měření na tabletu.

---

## 0. Co je na naší vodě špatně (misa_13_11_voda_deska.jpg + kód)

| příznak na fotce | příčina v kódu (stav 13. 11.) |
|---|---|
| voda je šedavá průsvitná **deska**, všude stejná | `voda.gdshader`: `ALPHA = smoothstep(0, cirost=0.25, h) * kryti_max(0.55)`. Od 0,25 m hloubky má celá hladina konstantní krytí 0,55 bez ohledu na úhel pohledu. Albedo `melka` (0.35, 0.42, 0.23) je světlé a `ROUGHNESS 0.22`. Hladina tak působí jako matná fólie, ne jako voda, která při pohledu shora prosvítá a při šikmém pohledu zrcadlí. |
| dno pod vodou vypadá suché, stejné jako břeh | Pod hladinou je pás `BREH_*` s materiálem terénu (`hlavni.gd`: `material_override = svet.mat_zem`). Maska stanovišť má krok 2 m (`plochy.json maska_krok_m`) a „břeh“ sahá do 8 m. Mokrý tmavý pás široký desítky centimetrů se v ní nedá nakreslit, a kamení pod vodou proto není tmavší ani sytější. |
| **ostrá hrana** na kraji a u brodu | `blender/voda.py`: hladina na mřížce břehu bere jen body `abs(ov) <= pw + 1.3` m. Za nimi se síť utne, i když je tam terén pod hladinou (u brodu je nájezd ±3 m a koryto širší, `voda_hra.json koryto.brod`). Na posledním vrcholu bývá hloubka > 0, takže krytí ~0,3–0,55 skončí hranou polygonu. Čtverce s `max(hq) <= 0` se navíc vynechávají. Kde je terén těsně pod hladinou, vzniká zubatý okraj. |
| voda „rovná“, nic ji neláme | Vlny jsou dvě vrstvy normálové mapy posouvané po UV.x. Chybí pěna kolem kamenů, prahy a peřeje (bílá voda) a změna rychlosti. Valouny pod hladinou průhlednou deskou jen prosvítají, hladinu nelámou. |

---

## 1. Předloha: skutečné potoky (misa_real_01–04, závazné)

| foto | co z něj platí pro stavbu |
|---|---|
| `misa_real_01_potok_trava_kameny.jpg` | Mělký tok s valouny po celém dně. Hladinu lámou hřbety kamenů (světlé „čárky“ a vrásky za každým kamenem). Voda je olivově hnědá a čirá, dno je vidět. Levý břeh: tráva a ostřice přepadají přes hranu až do vody. Pravý: keře (listnáče) visí nad vodou. Na kraji leží kameny napůl ve vodě. **Hranu vody nikde nevidíš.** |
| `misa_real_02_les_skala_perej.jpg` | Lesní potok. Skalní stěna a balvany mají shora mech a kapradí a tmavé holé boky u vody. Bílá voda proudí mezi kameny. Listí leží až k vodě a kmen leží šikmo přes potok. |
| `misa_real_03_perej_listi_breh.jpg` | Peřej přes kamenný práh (bílá voda), nad ní a pod ní klidná tmavá hladina. Břeh tvoří kamení, listí, kořeny a nízký porost. Svah lesa jde až k vodě. |
| `misa_real_04_horsky_balvany.jpg` | Prudší tok s velkými balvany a bílou vodou. Na březích je štěrk a kamení, hustá vegetace sahá až k vodě a převislá tráva je v popředí. |

Shodně s Míšinými staršími fotkami `docs/reference/potok/misa_potok_01–02.jpg`: balvany droby 2–4 m s mechem nahoře, šedé ploché kameny, peřej.

---

## 2. Jak to dělá KCD (screenshoty v této složce)

KCD 1 i 2 běží na CryEngine (KCD 2 na jeho upravené verzi). Řeka v CryEngine je entita River (spline) s materiálem vody. Doklady jsou v oddílu 3.

### 2.1 Uložené snímky

| soubor | zdroj (každý stažen curl zvlášť 13. 11.) | co ukazuje |
|---|---|---|
| `kcd1_oficial_potok_valouny_pruhlednost.jpg` | Steam, oficiální snímek KCD1 (app 379430), https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/379430/ss_3c205f4c6b09f7838aa003cac2bdf3842629e50a.1920x1080.jpg | Valouny po celém dně. V mělké vodě u kamery je dno plně vidět, kameny jsou pod vodou tmavší a sytější než suché na břehu. Do dálky hladina přechází v odraz oblohy a lesa (Fresnel). Kolem nohou koní je bílá tříšť. |
| `kcd1_oficial_breh_bahno_koreny.jpg` | Steam, oficiální snímek KCD1, https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/379430/ss_01dea4f433b9dcf121a3120c6c36712dc136c63a.1920x1080.jpg | Strmý hlinitý břeh s obnaženými kořeny a drnem nahoře. Na hraně břehu mech. Ve vodě leží větve a naplavené dřevo, voda je tmavá. |
| `kcd1_potok_podemlety_breh_koreny.jpg` | Steam Community, KCD1, https://steamcommunity.com/sharedfiles/filedetails/?id=2099937734 | **Hlavní vzor břehu.** Vpravo podemletý břeh 0,4–0,6 m (odhad z fotky) s visícími kořeny, pod ním mokrá písčito-štěrková lavice 1–2 m s balvany 0,3–0,8 m a bylinkami. Vlevo tráva a ostřice až do vody. Voda hnědoolivová, u kraje průhledná, uprostřed tmavší. Vrásky a světlé pruhy jsou za kameny. |
| `kcd1_potok_trava_az_k_vode_vrba.jpg` | Steam Community, KCD1, https://steamcommunity.com/sharedfiles/filedetails/?id=2099936077 | Úzký potok ~1 m (odhad z fotky). Tráva 0,5–0,9 m roste až k vodě a přes ni, takže hranu vody úplně zakrývá. V pozadí vrba smuteční. **Tu nebrat**: v Evropě je až od 17.–18. stol. ([Trees and Shrubs Online](https://treesandshrubsonline.org/articles/salix/salix-babylonica/)) a `pravidla/svet/druhy.json` ji už má jako `historicky: false`. |
| `kcd1_potok_louka_mekky_okraj.jpg` | Steam Community, KCD1, https://steamcommunity.com/sharedfiles/filedetails/?id=1302514860 | Potůček 0,5–0,8 m zaříznutý ~0,3 m do louky (odhad z fotky). Drn přechází přes hranu, voda je tmavá. Hromady sběrového kamene leží 3–5 m od vody. |
| `kcd1_lesni_potok_kameny_mech.jpg` | Steam Community, KCD1, https://steamcommunity.com/sharedfiles/filedetails/?id=1317895324 | Lesní tok ~3 m. Balvany v korytě mají mech nahoře a listí. Hladina je tmavá a zrcadlí korunami. Na březích nízké byliny, kapradí a semenáčky až k vodě, břízy 2–5 m od vody. |
| `kcd1_melcina_mlyn_mokre_bahno.jpg` | Steam Community, KCD1, https://steamcommunity.com/sharedfiles/filedetails/?id=1438802550 | Široká mělčina u mlýna. Suchá cesta přechází do tmavého mokrého bahna 2–4 m (odhad z fotky) a pak do vody, **bez hrany**. Jednotlivé kameny trčí z vody. U mlýna rákos a orobinec, na břehu keřové vrby. |
| `kcd2_potok_previsla_trava_kameny.jpg` | Steam Community, KCD2 (app 1771300), https://steamcommunity.com/sharedfiles/filedetails/?id=3602731022 | Strouha ~0,8–1 m. Kraj vody lemují ploché kameny a přes ně visí tráva 0,6–1 m. Na břehu hlavatá vrba (ořezávaná). Voda zrcadlí a u kamery je vidět dno. |
| `kcd2_potok_skaly_mech_listi.jpg` | Steam Community, KCD2, https://steamcommunity.com/sharedfiles/filedetails/?id=3632109342 | Lesní potok mezi skalami: balvany s mechovými polštáři, malý stupeň s bílou vodou, kmen přes potok, listí až k vodě a lávka z prken. |
| `kcd2_potok_kameny_most.jpg` | Steam Community, KCD2, https://steamcommunity.com/sharedfiles/filedetails/?id=3421360612 | Mechem porostlé kameny v toku, drobné kaskády se světlou vodou. Tráva a mech přecházejí přes hranu do vody, nahoře velký balvan s mechem. |

Autorská práva ke snímkům má Warhorse Studios / Deep Silver. Snímky z komunity patří jejich autorům. Slouží jen jako interní reference, nic z nich se do hry nekopíruje.

### 2.2 Z čeho se KCD potok skládá (pozorování ze snímků)

1. **Koryto a břehy.** Profil není symetrický. Na jedné straně bývá strmý až podemletý břeh s kořeny (`kcd1_potok_podemlety…`, `kcd1_oficial_breh…`), na druhé mírná štěrková či písčitá lavice nebo drn až k vodě. Šířka se mění. V lese břehy tvoří balvany a skály.
2. **Přechod vody do břehu (hlavní rozdíl proti nám).** Hrana vody se nikde nečte jako čára. Zakrývá ji několik vrstev zároveň:
   - (a) terén pod vodou a těsně nad ní je **tmavší a lesklejší** (mokrý), na snímcích ~0,2–0,5 m nad čárou vody (odhad z fotky; bahno u mlýna až 2–4 m);
   - (b) na čáře vody leží **kameny napůl ve vodě**;
   - (c) **tráva, ostřice a mech přepadají přes hranu**;
   - (d) samotná hladina je v mělké vodě skoro neviditelná, protože ji prozradí jen odlesk a vrásky.
3. **Barva podle hloubky.** Mělko je čiré a dno (valouny) je vidět. Hlubší místo nebo tůň je tmavě olivové až hnědé (lesní potok téměř černé). V CryEngine to dělá „fog“ vodního objemu podle hloubky ([CryEngine River Tool: Fog Density, Fog Color](https://www.cryengine.com/docs/static/engines/cryengine-5/categories/23756816/pages/36867737)).
4. **Odlesk.** Při pohledu shora je hladina průhledná, při šikmém pohledu zrcadlí oblohu a koruny. Je to Fresnel: krytí roste s úhlem, není konstantní.
5. **Pěna a bílá voda** se drží na kamenech, prazích a kaskádách a koncentruje se za překážkou. V CryEngine je pěna u styku s terénem a předměty („Foam soft intersection“, oddíl 3).
6. **Tok.** Vrásky se posouvají po proudu a za kameny se stáčejí (flow).
7. **Kameny a dřevo.** Valouny pokrývají celé dno a balvany trčí z vody, nahoře s mechem, holé boky mají u vody. Leží tu kmen přes potok a naplavené větve u kamenů a na břehu.
8. **Vegetace.** Tráva a ostřice až do vody, keřové vrby, hlavaté vrby a olše na břehu, v lese kapradí, devětsil a mech. Orobinec a rákos jen v klidné vodě (mlýn, tůň).

### 2.3 Pásma od vody podle snímků (odhad z fotky, ne měření)

| pásmo (vzdálenost od čáry vody) | KCD snímky | skutečné potoky (misa_real) | doloženo v katalogu biotopů ČR |
|---|---|---|---|
| **pod vodou** (dno) | valouny 5–30 cm souvisle, balvany 0,3–1 m jednotlivě (`kcd1_oficial_potok_valouny`) | valouny po celém dně (real_01), balvany a skalní prahy (real_02–04) | – |
| **čára vody ±0,3 m** | kameny napůl ve vodě, ploché kameny lemem (`kcd2_potok_previsla`), trsy trávy převislé do vody (`kcd1_potok_trava…`) | kameny napůl ve vodě, tráva a ostřice převislé do vody (real_01, real_04) | – |
| **0–1 m** | louka: hustá tráva a ostřice 0,5–1 m, souvislý drn; les: kapradí, mech, listí, holá hlína a kořeny na strmém břehu; na vnitřní straně zákrutu holá štěrková lavice 1–2 m | listí a kořeny, nízký porost (real_02, real_03), štěrk (real_04) | štěrkové náplavy na **jesepních (vnitřních) březích** jsou mladé **bez vegetace**, mechové patro chybí (M4.1, [Chytrý et al. 2010, Katalog biotopů ČR, 2. vyd.](https://www.sci.muni.cz/botany/chytry/Chytry_etal2010_Katalog-biotopu-CR-2.pdf), s. 67–68) |
| **0,5–3 m** | keřové vrby a hlavaté vrby ve skupinách, olše jednotlivě; mezi nimi vysoká tráva | keře a listnáče visící nad vodu (real_01) | vrbové křoviny na březích a náplavech **2–5(–10) m** vysoké, nesnášejí zastínění, převážně **200–550 m n. m.**: vrba trojmužná, košíkářská, křehká (K2.1), na štěrku vrba nachová (K2.2) (tamtéž, K2) |
| **1–8 m (niva)** | v lese olše, břízy a smrky až k vodě, pod nimi kapradí | les až k vodě (real_02, real_03) | potoční luhy: **olše lepkavá** nebo jasan, keřové patro husté, v bylinném patře čarovník, kostřava obrovská, čistec lesní, ptačinec hajní, mech slabě (L2.2, tamtéž s. 270); podél horských a podhorských potoků lemy **devětsilu lékařského 1,0–1,5 m**, zcela zapojené, převážně **450–800 m n. m.** (M5, tamtéž s. 74) |
| **3–5 m** | hromady sběrového kamene na loukách (`kcd1_potok_louka…`) | – | NEOVERENO (pro rok 1393) |

Hustoty v trsech na m² nejsou ve snímcích ani v katalogu. Každá hustota v návrhu je proto **NEOVERENO** a nastaví se podle snímku ze hry vedle předlohy.

---

## 3. Techniky (se zdroji)

### 3.1 CryEngine (KCD): River entity a vodní shader
[CryEngine 5, River Tool](https://www.cryengine.com/docs/static/engines/cryengine-5/categories/23756816/pages/36867737):
- **Width** se „obvykle nastavuje mnohem širší než skutečná řeka, protože viditelnou šířku určuje okolní terén“. Hladina tedy leží i pod břehem a schová ji terén. To děláme také (`presah_m`), ale u nás pak na hraně sítě skončí tvrdě.
- **Border Width** slouží jen pro „Align Height Map“ a dělá hladký kraj terénu. **Step Size** (výchozí 4) říká, že menší krok znamená víc polygonů a hladší oblouky. **Erase Veg Width** maže vegetaci kolem řeky.
- Spline má **Depth** a **Fog Density / Fog Color**, tedy barvu podle hloubky ve vodním objemu. Vizuální rychlost určuje **Flow Speed** v materiálu.
- „River Tool je v podstatě 2D … pro toky z kopce použijte řadu řek s občasnými vodopády; důležité je pečlivé použití částic.“ To znamená **kaskády jako samostatné díly**.

[CryEngine 5, Water Volume / WaterVolume shader](https://cryengine.com/docs/static/engines/cryengine-5/categories/23756816/pages/36869912) a [CryEngine 3, Water Shader](https://www.cryengine.com/docs/static/engines/cryengine-3/categories/1114113/pages/1048756) uvádějí:
- *Soft intersection factor* (měkký průnik s geometrií);
- *Foam soft intersection* („pěna se tvoří kolem protínajících předmětů a terénu“);
- *Flow map scale / Flow offset / Flow speed*;
- *Detail normals*;
- *Realtime reflection*.

Měkký průnik i pěna u styku jsou v CryEngine z hloubky scény. **To my nesmíme** (pravidlo: žádné čtení obrazovky ani hloubky), takže tutéž informaci musíme **upéct předem** (3.3).

### 3.2 Unreal Water a pečené řeky (Horizon, Houdini)
- [UE Water Body Actors](https://dev.epicgames.com/documentation/en-us/unreal-engine/water-body-actors-in-unreal-engine):
  - řeka má na bodech splinu **Depth, River Width, Velocity**;
  - zářez terénu má **Channel Edge Offset, Falloff Width** a **Edge Offset** („plochý pás před svahem – plochý břeh“);
  - přechody River→Lake mají vlastní materiál.
- [Simon Schreibt, River (Houdini → Unreal, podle workflow Horizon Zero Dawn)](https://simonschreibt.de/gat/river):
  - z každého polygonu terénu se střílí paprsek nahoru, kde zasáhne řeku, dostane barvu vrcholu, a ta **maska mokrého koryta řídí tmavší albedo a roughness**;
  - **flow ve vertex color** ze směru splinu, obtékání překážek;
  - **pěna = vzdálenost k překážce uložená ve vertex color** + šum − posouvaný mrak;
  - řeka „teče ve **stupních**“ místo stálého spádu, na kaskády zvlášť pěna;
  - jen vnější hrany sítě vody se přirovnají k terénu.
- Havran tuto rešerši už má: větev `claude/new-session-0dtk58`, `research_notes/Otevřený svět Godot Android/voda_toky.md`, oddíly 1 a 3. Recept pro mobil: hloubka do vrcholu, alfa, barva a pěna z ní, síť přes čáru vody s alfa 0, mokrý pás terénu 0,2–0,4 m nad hladinou (to je tam NAVRH, ne měření).

### 3.3 Měkký okraj bez hloubky obrazovky: co jde levně v Godot Compatibility
Všechno níže čte jen atributy vrcholu (`UV`, `COLOR`) a nepotřebuje žádný vzorkovač navíc:
1. **Hloubka ve vrcholu.** Máme ji (`UV.y` = hladina − terén). Síť ale musí pokrýt **celou plochu, kde je hloubka > 0, a ještě jednu řadu vrcholů za čárou vody**. Na krajní řadě se vynutí alfa 0 (např. `COLOR.a = 0`), takže hranu sítě nikdy neuvidíš. Pak nevadí zuby ani brod.
2. **Krytí podle fyziky, ne konstanta.** Absorpce roste s hloubkou podle Beer–Lambertova zákona (`1 − exp(−h/d)`). Odraz roste s úhlem pohledu podle Fresnela. Schlickova aproximace má F0 = ((n−1)/(n+1))², pro vodu (n ≈ 1,33) **F0 ≈ 0,02** ([Schlick's approximation](https://en.wikipedia.org/wiki/Schlick%27s_approximation)). Shora je mělká voda skoro neviditelná a do dálky zrcadlí, přesně jak to ukazuje `kcd1_oficial_potok_valouny`. V Godotu stačí `dot(NORMAL, VIEW)`, tedy počet a ne textura.
3. **Mokré dno a mokrý pás řeší terén, ne voda.** Mokrý povrch je tmavší a sytější, protože voda v pórech potlačí rozptyl (Lekner & Dorf, *Why some things are darker when wet*, Applied Optics 27, 1988; NEOVERENO, článek jsem nečetl, jen citaci znám). Projekt už to má jako `mokro` v `zem.gdshader` (déšť: albedo × 0,66, roughness 0,55). Stačí to zapnout místně podle barvy vrcholu pásu `BREH`, který už leží přesně podél toku na mřížce 1 m × (0,25 × polovina šíře).
4. **Pěna** se upeče do vrcholu: vzdálenost ke kameni nebo prahu a úsek peřeje (Schreibt). Jediná textura je šum, který už máme (`pena_tex`).
5. **Flow mapa** = směr toku ve vrcholu + dvě fáze posunu normály posunuté o půl periody, s trojúhelníkovými vahami a šumovým posunem času proti pulzování ([Catlike Coding, Texture Distortion](https://catlikecoding.com/unity/tutorials/flow/texture-distortion/); původ: [Vlachos, Water Flow, SIGGRAPH 2010](https://www.advances.realtimerendering.com/s2010/Vlachos-Waterflow(SIGGRAPH%202010%20Advanced%20RealTime%20Rendering%20Course).pdf)). Cena je dvojnásobek vzorků normálové mapy (dnes 2 vzorky normál + 2 pěny = 4 vzorky ze 2 textur, s flow 4 + 2). Počet vzorkovačů se nemění, pořád 2.
6. Godot Waterways (Arnklit), který Havran používá jako základ `reka.gdshader`, umí „Edge Fade“ a upečené flow a pěnu z raycastů, ale nedělá zářez ani soutoky (Havran `voda_toky.md` §1, §5). Jeho pečení v Godotu převzít nemusíme, totéž umí `blender/voda.py`, protože zná osu, hloubku i kameny.
7. Hloubková textura (`hint_depth_texture`) v Compatibility existuje (Havran `voda_toky.md` §3), ale je to čtení obrazovky. **Zakázáno** (pády Havrana 0.58–0.59).

### 3.4 Kaskády, peřeje, LOD
- Peřej je krátký úsek s větším spádem hladiny, napříč ho přetíná kamenný práh a na něm je pěna. Nad ním je klidná tmavá tůň (real_03). U Schreibta to je „flow in steps“ a pěna maskovaná na úsek spádu. CryEngine řeší strmý tok řadou řek a vodopádů s částicemi.
- Malý stupeň 0,2–0,5 m (`kcd2_potok_skaly…`, real_02 a 04) se dá udělat jako samostatný díl: pás „přepadu“ s vlastní UV po proudu a rychlou pěnou, plus kotouče tříště. Velikost a počet částic na tabletu jsou NEOVERENO, nejdřív bez částic.
- LOD: máme jemnou hladinu do `dosah_kresleni_m` 220 m a dál `VODA_DALEKO` po 4 m (`voda.py`). Daleko se flow a pěna nevyplatí, stačí barva, Fresnel a alfa okraje ve vrcholech. Za stejnou cenu (NEOVERENO) to může být jen druhá varianta shaderu se `#define`.

---

## 4. Návrh pro Puchart (seřazeno podle přínos / cena)

Vzhled podle `misa_real_01–04`, technika podle KCD, CryEngine, Horizon a Havrana. Pořadí stavby zůstává terén → koryta → cesty → … → voda → vegetace → předměty. Každý krok končí snímkem vedle předlohy (Míša). Čísla bez zdroje jsou **NAVRH / NEOVERENO** a patří do `pravidla/svet/voda_hra.json` s polem `zdroj`.

### Krok 1 – Hladina bez tvrdé hrany (`blender/voda.py`) · přínos velký, cena malá
- Jemná hladina na mřížce `BREH` přestane brát jen `abs(ov) <= pw + 1.3`. V každém řezu napříč vezme **všechny body pásu, kde je hloubka > 0, plus jednu řadu za čárou vody**. U brodu tak hladina sama dosáhne až na nájezd a neskončí uprostřed vody.
- Do vrcholů hladiny přidat barvu: `COLOR.a` = 0 na krajní řadě a na vrcholech s hloubkou ≤ 0, jinak 1. Shader tím násobí alfu, takže hrana sítě nikdy není vidět.
- `hrady.uloz` dnes exportuje barvy vrcholů jen s `vzhled`. Pro `voda.glb` je nutné zapnout `export_vertex_color` a barvu vrcholu zapisovat i bez AO, třeba parametrem `barvy=True` (malá změna společné funkce, ostatní stavby se nemění).
- Odhad nárůstu trojúhelníků jemné hladiny: NEOVERENO (hlídač scén).

### Krok 2 – Shader vody: krytí podle hloubky a úhlu (`hra/shaders/voda.gdshader`) · velký přínos, malá cena
- Zrušit konstantu `kryti_max 0.55`. Krytí `A = max(1 − exp(−h / d_cir), F) · COLOR.a`, kde Fresnel `F = 0.02 + 0.98·(1 − dot(N, V))^5` (Schlick, F0 vody 0,02). Hodnotu `d_cir` (čirost; dnes `cirost` 0,25 m) nastavit podle real_01, kde je dno vidět i uprostřed (NEOVERENO).
- Albedo tmavší a hnědoolivové podle real_01 a 03 (měřit pipetou z fotky do `voda_hra.json` se zdrojem), mělko skoro bez vlastní barvy. Hloubka pak tmaví k černozelené (`hluboka`). Do tůní nad prahy dát víc.
- `ROUGHNESS` nízký (~0,05–0,1, NEOVERENO) jen na klidné vodě, aby šikmý pohled zrcadlil les. Na peřeji a pěně vyšší. `SPECULAR` odpovídající F0 0,02: v Godotu je F0 = 0,16·specular², tedy ~0,35. Vzorec je podle konvence Filamentu, pro Godot NEOVERENO, ověřit snímkem.
- Žádný nový vzorkovač.

### Krok 3 – Mokrý pás a mokré dno (terén, `blender/voda.py` BREH + `hra/shaders/zem.gdshader`) · velký přínos, malá cena
- Pás `BREH_*` dostane barvu vrcholu `COLOR.r` = **sucho**:
  - 0 pod hladinou;
  - lineárně k 1 do výšky `mokry_pas_m` nad hladinou;
  - KCD snímky ukazují ~0,2–0,5 m (odhad z fotky), Havran `voda_toky.md` navrhuje 0,2–0,4 m (NAVRH), u mělkých plochých břehů a brodu širší, podle vodorovné vzdálenosti (KCD mlýn 2–4 m).
- `zem.gdshader` použije stávající větev `mokro` místně: `mokro_mista = max(mokro, 1 − COLOR.r)`. Terén bez barvy vrcholu má v Godotu výchozí bílou, takže se nic nemění. Pod vodou navíc ztmavit a mírně zezelenit podle hloubky (`COLOR.g` = hloubka/0,5 m), což nahradí chybějící lom a absorpci (na fotkách je kamení pod vodou tmavší a sytější).
- Nula nových vzorkovačů, platí jen pro pás `BREH` (do 220 m). Maska stanovišť (2 m) zůstane na hrubé „breh“.

### Krok 4 – Kameny, které lámou hladinu, a pěna u nich (`nastroje/koryto_kameny.py`, `voda.py`, shader) · velký přínos (real_01), střední cena
- Dnes vyčnívají jen balvany (`balvany_na_m 0.3`, `balvan_nad_hladinou 0.05–0.35`). Podle real_01 hladinu lámou i **hřbety valounů**: část valounů v proudnici má vrch 0–5 cm nad nebo pod hladinou (podíl NEOVERENO, ladit snímkem).
- **Pěna do vrcholu hladiny** (`COLOR.b`) jako vzdálenost ke kameni, který trčí z vody, protažená po proudu ~1–3× průměr kamene (Schreibt: vzdálenost k překážce + šum). K tomu `COLOR.rg` = vychýlení proudu kolem kamene pro krok 6.
- Pořadí: voda.py musí znát kameny. Rozmístění kamenů (`koryto_kameny.py`) potřebuje jen `toky_hladina.json` a brody, které počítá už `koryta.py` (`toky_hladina.json … "brody"`). Rozmístění tedy patří **před** voda.py jako data koryta (krok „koryta“), samotná instance zůstává v předmětech. Dnes `koryto_kameny.py` čte `hra/data/brody.json` z voda.py, takže nutno přepojit na brody z `koryta.py` (ověřit, že jde o tytéž brody, NEOVERENO).
- Hustota sítě hladiny napříč je ~0,4–0,6 m (`body_napric` × polovina šíře). Pěnová stopa tak bude měkká skvrna, ne ostrý límec. Pro valouny to stačí. Ostrý límec u velkých balvanů lze doplnit plochým „límcem“ (kroužek s alfou) jen u balvanů nad 0,6 m, za cenu kreslení NEOVERENO.

### Krok 5 – Tůně a peřeje přes kamenné prahy (`nastroje/koryta.py` hladina, `koryto_kameny.py` práh, `voda.py` pěna) · velký přínos (real_02–04), střední cena
- Hladinu skládat ze **stupňů**: dlouhá klidná tůň (sklon hladiny ~0) a krátká peřej, kde spadne o 0,1–0,4 m na 1–3 m (NEOVERENO). Vzdálenost peřejí 2–5 šířek koryta (`voda_hra.json kolisani_sirky` zdroj detaily_hradu_1393 §9, sám NEOVERENO rozměrově). Dnešní `rampa_hladiny_m` skoky naopak rozmazává, takže tam, kde je peřej v datech, ji nevyhlazovat.
- Na každém prahu řada kamenů napříč, nový typ `prah` v `koryto_kameny`: vrch u hladiny, v tůni pod prahem hlouběji (dno `hloubka_vody_m` × 1,5, NEOVERENO).
- Ve `voda.py` dostane úsek peřeje plnou pěnu (`COLOR.b`), shader na něm rychlejší posun a vyšší roughness. Stávající `pena_sklon` (pěna podle sklonu) tím zpřesní data.
- Stupně nad ~0,3 m jako samostatný díl „přepad“ (CryEngine: řada řek + vodopády). NEOVERENO, až po snímku.

### Krok 6 – Tok (flow) podle směru a kolem kamenů (shader) · střední přínos, střední cena
- Dvoufázový posun normál podle `COLOR.rg` (směr a rychlost z osy, obtékání kamenů z kroku 4) a šum času (Catlike, Valve). Rychlost z `voda_hra.json` (dnes `rychlost 0.45` m/s, zdroj chybí, NEOVERENO), v peřeji vyšší a v tůni nižší.
- +2 vzorky normálové mapy (celkem 6 vzorků, pořád 2 vzorkovače). Na tabletu změřit (trasa „voda 75 %“ v `mereni.json`), mezicíl p95 40 ms.

### Krok 7 – Tvar břehu (`nastroje/koryta.py`) · střední přínos, střední cena
- **Nesouměrný profil podle zakřivení osy.** Na vnější straně oblouku (nárazový břeh) práh vyšší a strmější, na vnitřní (jesep) nízká štěrková lavice 0,5–2 m těsně nad hladinou bez vegetace (M4.1 výše; `kcd1_potok_podemlety…`). Dnes `prah_nad_hladinou_m 0.55` a `sklon_svahu 0.9` platí na obě strany stejně. Dvě hodnoty podle znaménka křivosti, velikosti NEOVERENO.
- **Podemletý břeh** se ve výškovém poli udělat nedá, protože nemá převis. Je to předmět: kus hlinité stěny 0,3–0,6 m s visícími kořeny podle `kcd1_potok_podemlety…` a `kcd1_oficial_breh…`, postavený na nárazový břeh do zářezu (model NEOVERENO, hledat nejdřív Havran, Poly Haven a Sketchfab CC0).
- Stanoviště `koryta.py DRUH` rozdělit z 2 tříd (1 dno, 2 břeh) na: 1 dno, 3 **čára vody** (±0,3 m), 4 **jesep štěrk**, 2 břeh, a nést to do vegetace (krok 8).

### Krok 8 – Vegetace u vody (`pravidla/svet/byliny.json`, `kere.json`, `druhy.json`, `hra/scripts/byliny.gd`) · velký přínos, střední cena
- **Pás u vody jako `pata_pas`.** Mechanismus už existuje: `stavby_vegetace.py` → `data/pata_pas.json` a `byliny.gd` mají pás podél hrany, hustší u hrany. Totéž podél čáry vody (`voda_pas`):
  - trsy trávy a ostřice **na čáře vody a 0,1–0,4 m přes ni, nakloněné k vodě** o 30–50° (převis; KCD `kcd1_potok_trava…`, `kcd2_potok_previsla…`, real_01, real_04; úhly odhad z fotky);
  - hustota u hrany nejvyšší, čísla NEOVERENO.
- **Pásma** podle tabulky 2.3 (zdroj: snímky + Katalog biotopů ČR):

  | pásmo | louka / ves | les (údolí Veličky) |
  |---|---|---|
  | čára vody | převislá tráva, ostřice, kameny napůl ve vodě | mech a kapradí na kamenech, listí, kořeny |
  | 0–1 m | hustá tráva a ostřice 0,5–1 m; jesep holý štěrk | kapradí, devětsil, holá hlína a kořeny na nárazovém břehu |
  | 0,5–3 m | **keřové vrby** (křehká, trojmužná, košíkářská; na štěrku nachová – K2) ve skupinách, **hlavatá vrba** (bílá) u vsi | olše lepkavá, mladé olše (L2.2), líska, bez |
  | 1–8 m | olše jednotlivě | olše, jasan, smrk; devětsil v zapojených lemech 1–1,5 m (M5) |

- `kere.json` „breh“ má dnes bez, lísku a zmlazený buk, **chybí keřové vrby**. `druhy.json` má olši, ale `vrba_hlavata` je `pouzit: false` (chybí model). Doplnit model keřové vrby a hlavaté vrby. Vrbu smuteční nebrat (`historicky: false`).
- Devětsil: katalog M5 ho uvádí v 450–800 m n. m. Potštátsko kolem Puchartu je kolem 400 m (`svet.json` počátek H 400), takže u Veličky spíš okrajově (NEOVERENO podle skutečné nadmořské výšky toku).
- Orobinec a rákos jen u klidné vody (rybník, náhon, tůň), ne v peřejích.
- **Mech na kamenech:** jen na vrchu a nad hladinou (`misa_potok_01–02`, real_02, KCD les). Kameny koryta mají velké balvany s mechem (`tvar 6–11`). Pro menší kameny nad hladinou mech podle normály nahoru a výšky nad hladinou ve shaderu kamene. Vodní mech pod hladinou NEOVERENO, nedělat.

### Krok 9 – Dřevo ve vodě (`byliny.json` kmen nebo nový záznam ve `voda_hra.json`) · střední přínos, malá cena
- **Kmen přes potok** (real_02, `kcd2_potok_skaly…`, `misa_potok_01`): záznam v datech, ne náhoda. Konce na březích, šikmo, nad hladinou nebo napůl ve vodě. Dnes je `kmen 0.05` v `breh` a leží podél, ne přes. Hustota NEOVERENO, první návrh pár míst v lesní části Veličky se zdrojem.
- **Naplavené větve** zachycené u balvanů a na jesepu (`kcd1_oficial_breh…`), malé modely, jen do ~45 m (`kameny_koryta.dosah_m`).

### Krok 10 – Dálka (LOD) · malý přínos, malá cena
- `VODA_DALEKO`: stejné krytí podle Fresnelu a hloubky, alfa 0 na krajích pásu (dnes vrcholy jen ±hw). Bez flow a pěny.

### Co nedělat
- Žádná hloubka nebo kopie obrazovky (měkký průnik jako v CryEngine), žádné MSAA, žádné odrazy v reálném čase. Fresnel odráží jen oblohu a prostředí, které Godot má.
- Žádné zprůhlednění celé hladiny na 0,55 „aby bylo vidět dno“. Dno má být vidět díky Fresnelu a hloubce, ne díky fólii.
- Nekopírovat z KCD vrbu smuteční ani modely. Brát princip a doloženou flóru.

### Kontrola po krocích
- Snímek ze hry ze stejného místa jako `misa_13_11_voda_deska.jpg` (brod u hájovny, kraj louky) vedle `misa_real_01` a `kcd1_potok_podemlety…`.
- Hlídači: `voda_v_korytu`, geometrie (převislé trsy nesmí viset ve vzduchu, pata trsu na terénu), hlídač scén (trojúhelníky hladiny a trsů), měření „voda 75 %“.

## Zdroje
- CryEngine 5 River Tool: https://www.cryengine.com/docs/static/engines/cryengine-5/categories/23756816/pages/36867737
- CryEngine 5 Water Volume (shader params): https://cryengine.com/docs/static/engines/cryengine-5/categories/23756816/pages/36869912
- CryEngine 3 Water Shader: https://www.cryengine.com/docs/static/engines/cryengine-3/categories/1114113/pages/1048756
- Unreal Water Body Actors: https://dev.epicgames.com/documentation/en-us/unreal-engine/water-body-actors-in-unreal-engine
- S. Schreibt, River (Horizon workflow): https://simonschreibt.de/gat/river
- Catlike Coding, Texture Distortion (flow): https://catlikecoding.com/unity/tutorials/flow/texture-distortion/
- A. Vlachos, Water Flow, SIGGRAPH 2010: https://www.advances.realtimerendering.com/s2010/Vlachos-Waterflow(SIGGRAPH%202010%20Advanced%20RealTime%20Rendering%20Course).pdf
- Schlick's approximation: https://en.wikipedia.org/wiki/Schlick%27s_approximation
- Chytrý et al. (2010) Katalog biotopů ČR, 2. vyd. (K2, K2.1, L2.2, M4.1, M5): https://www.sci.muni.cz/botany/chytry/Chytry_etal2010_Katalog-biotopu-CR-2.pdf
- Vrba smuteční v Evropě: https://treesandshrubsonline.org/articles/salix/salix-babylonica/
- Havran (větev claude/new-session-0dtk58): `research_notes/Otevřený svět Godot Android/voda_toky.md`, `shaders/reka.gdshader`, `tools/reka_bake.gd`
- Godot shadery vody s okrajem používají `DEPTH_TEXTURE` (godotshaders.com: Stylized Water, Foam Edge, Simple River), proto pro nás nevhodné.
- RDR2 a Witcher 3: veřejný technický rozbor řek jsem nenašel. Bývalý vodní umělec RDR2 (D. O'Reilly) rozebírá jinou hru, KCD se netýká. Bez závěru, NEOVERENO.
