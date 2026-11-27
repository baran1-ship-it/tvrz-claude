# Rešerše: animace a postavy – jak to řeší jiné hry (27. 11.)

Zadání Míši 27. 11. (verze 0.9999999, `misa_27_11_chyby.md` body 5–9): „animace a postavy jsou další level, udělej si
širokou a hlubokou rešerši, jak to řeší jiné hry, a s tím se řiď“. Konkrétně: kuchařka u ohniště (moc animací, leží/klečí
v ohni a sahá do něj, kotlík je cíl), vlasy mladíka (černé střepy), kůň Hero Horse se pase s krkem do C, jízda horší než
s původním koněm.

Pravidla čtení:
- Každé tvrzení „jak to dělají jiní“ má u sebe zdroj (URL). Co zdroj nemá, je označeno **odhad** (= NEOVĚŘENO,
  podle CLAUDE.md se před použitím musí změřit na tabletu nebo v modelu).
- „Co z toho pro nás“ = pravidla k zápisu do JSON (`pravidla/svet/*.json`), ne čísla v kódu. Názvy klíčů jsou návrh;
  konkrétní hodnoty jsou výchozí odhad k doladění na tabletu, pokud u nich není zdroj.
- Mnoho GDC přednášek je za přihlášením do GDC Vault; uvádím jen to, co je z veřejných shrnutí/slajdů ověřitelné.

---

## 1. Kuchařka a aktivity u předmětů („smart objects“)

### 1.1 Co dělají jiné hry a enginy

**Objekt nese data, postava nese chování (Unreal Smart Objects).**
- Smart Object je objekt v úrovni, který nese informace potřebné k interakci, ale žádnou logiku – chování implementuje
  ten, kdo ho používá. Objekty jsou v prostorové databázi a dotazují se podle oblasti a tagů.
  https://dev.epicgames.com/documentation/unreal-engine/smart-objects-in-unreal-engine---overview?lang=en-US
- Definice má jeden či více **slotů**; slot má polohu a rotaci **relativně k rodičovskému objektu** a vlastní tagy
  a chování. Slot má stavy Free → Claimed → Occupied; agent si slot **zarezervuje** (claim), dojde na transform slotu
  (GetSlotTransform) libovolnou navigací a teprve na místě zavolá Use. Při změně stavu objektu se sloty uvolní
  a agent dostane notifikaci. (tamtéž)
- Slot má navíc **vstupní body (entrance annotation)** s lokálním offsetem a rotací; volitelně se ověřují proti
  navigaci, **dotrasováním na zem** (`bTraceGroundLocation`) a **kontrolou kolize na trajektorii z navigačního bodu do
  slotu** (`bCheckTransitionTrajectory`) – vstup, který neprojde, se zahodí.
  https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/SmartObjectsModule/FSmartObjectSlotEntranceAnnotati-?lang=en-US
  https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/SmartObjectSlotValidationParams
  Pozn.: dokumentace upozorňuje, že kontrola „na navigovatelném povrchu“ neznamená dosažitelnost.

**Práce = sekvence vstup → smyčka ×N → výstup (The Witcher 3, REDkit).**
- ActionPoint (komponenta na šabloně entity) odkazuje na **Job tree** = sekvenci animací. Příklad CDPR: vstup
  „playing_with_coin_bag“, smyčka „money_counting“ několikrát opakovaná, závěr „counting_money_end“. Hotové action
  pointy jsou rozdělené do složek `work` a `marketplace` a v názvu mají, kdo je smí použít (m = muž, w = žena,
  d = trpaslík). Spawn tree určuje denní dobu.
  https://cdprojektred.atlassian.net/wiki/spaces/W3REDkit/pages/47186233/HOW-TO+Create+an+encounter+with+NPC+merchant

**Nábytek se vstupními směry, idle markery (Skyrim/Fallout Creation Kit).**
- Furniture marker = „sedadlo“ pro jednoho herce; povolené **směry vstupu** (Marker Entry Points; ve Fallout 4 Front,
  Rear, Left, Right). Bethesda pro různé směry dělala raději **samostatné varianty objektu** (CommonWritingChair01L/R/LR)
  než složitou logiku. Mnoho idle animací je řešeno jako nábytek, ne jako volné idle markery; marker s „Ignored by
  Sandbox“ používá jen k němu přímo napojená postava.
  https://ck.uesp.net/wiki/Furniture  https://ck.uesp.net/wiki/IdleMarker  https://falloutck.uesp.net/wiki/Furniture
- Komunita uvádí, že u každého ohniště je aspoň jeden marker „ohřívání rukou“, i když tam je kotlík (neoficiální,
  https://forums.nexusmods.com/topic/12948471-where-are-animation-entry-points-definedcreated). Tj. u ohně se
  stojí/dřepí **vedle**, ruce jdou k ohni jen ve vzdálenosti dané klipem.

**Kde přesně postava stojí, je dáno klipem a slotem, ne odhadem za běhu (The Sims 4).**
- Offset postavy od kořene objektu je **uvnitř animačního klipu**; přesun v tuningu rozbil navázané efekty (VFX
  nalévání). Objekt má **footprint** (zakázanou plochu pro routing) a při interakci se na zem pokládá neviditelný
  **jig** (např. 2×2 m u kytary), který blokuje cesty ostatním.
  https://sims4studio.com/thread/31804/changing-slot-size  https://db.modthesims.info/d/683612
  https://sims4studio.com/thread/14883/edit-shape-objects-footprint

**Málo klipů, a přesto věrně (Horizon Forbidden West, GDC 2023).**
- Dlouhá smyčka s přirozeným otočením (malíř jde podél zdi a zpět), dvoustavová smyčka „přenes bednu ze stolu na zem
  → odejdi → po dlouhé pauze ji někdo vrátí“; dělníci působí, že pracují, aniž by cokoli dokončili. Rekvizita bez
  postavy, která s ní pracuje, působí jako kulisa (pila v HZD). Každý kmen měl vlastní sadu, ne jednu generickou.
  https://www.gamedeveloper.com/marketing/adding-texture-to-the-people-and-places-of-horizon-forbidden-west
- FF XV má samostatnou „Ambient AI“ pro civilisty ve městech; vývojáři přiznávají, že ručně umístěné postavy (rozestup,
  natočení k sobě) působí přirozeněji než automaticky rozmístěné.
  https://gamedeveloper.com/programming/the-ai-systems-that-govern-i-final-fantasy-xv-i-s-believable-npcs
  https://cgworld.jp/feature/201905-ff15ai-02.html

**Přechody a čitelnost (Game Developer – „Growing game animation“).**
- Přechodová animace nese okamžik změny stavu; když neodpovídá, věrohodnost padá. Pohled hlavou (look-at) na objekt
  zájmu ukazuje vědomí bez přerušení pohybu. Pár animací + spouštěč blízkosti stačí (prodavač ve Skyward Sword).
  https://www.gamedeveloper.com/art/growing-game-animation-state-changes-and-pathing
- Naughty Dog (Uncharted): stavový systém akcí s „next state“, blend time a guardy, aby šly přechody přidávat bez kódu;
  40+ variant vstupu do krytu – tj. variabilita je ve **vstupech**, smyčka je jedna.
  https://www2.slideshare.net/naughty_dog/creating-a-character-in-uncharted-drakes-fortune

**KCD / KCD2 (Warhorse).**
- Doloženo: modulární behavior trees jako jádro AI; KCD2 ~2400 NPC (polovina v Kutné Hoře), každá postava má denní
  rutinu, kterou události mění. GDC „Supporting Thousands of NPCs…“ (Petr Smrček):
  https://schedule.gdconf.com/session/supporting-thousands-of-npcs-in-kingdom-come-deliverance-kingdom-come-deliverance-ii/915120
  https://gdcvault.com/play/1035718/Supporting-Thousands-of-NPCs-in
  https://wccftech.com/kingdom-come-deliverance-2-dev-talks-about-dynamic-npc-routines-and-emergent-storytelling-for-side-quests/
- Článek Warhorse-spjatých autorů (Smart Areas, 2014) popisuje smart object jako „grafickou entitu doprovázenou
  animací postavy“ a modulární „smart areas“ pro simulaci denního života.
  https://scitepress.org/PublishedPapers/2014/49211/pdf/index.html
- **Jak přesně KCD2 animuje vaření u kotle, veřejně doložené nenašel jsem** (ani v modding wiki
  https://modding.wiki/en/kingdomcomedeliverance, ani v rozhovorech). Pozorování ze hry (**odhad**, ověřit na videu):
  kuchařky stojí u kotle/ohniště, míchají vařečkou ve stoje, občas přiloží; neleží ani neklečí v plameni.

### 1.2 Diagnóza naší kuchařky (odhad z popisu a snímků 12–13)
- Příliš mnoho klipů v rotaci → působí neklidně (Horizon i Witcher drží jednu hlavní smyčku).
- Leží/klečí v ohni → kotva aktivity = střed ohniště, ne pracovní bod u kotlíku; klip s posunem kořene (kleknutí,
  ležení) se přehrává bez kontroly zakázané zóny.
- Sahá do ohně → ruka míří na střed ohně (IK/uchop na špatný cíl) místo na ucho kotlíku / vařečku.

### 1.3 Co z toho pro nás (pravidla do JSON, např. `pravidla/svet/postavy.json` → `aktivity`, `nabytek.json` → sloty)
1. **Cíl aktivity je předmět, ne místo.** Aktivita „vaření“ má `cil: "kotlik"`; slot(y) se počítají relativně ke
   kotlíku (`slot.offset`, `slot.rotace`, jako UE slot relativně k rodiči). Ohniště je jen překážka.
2. **Zakázaná zóna (`keep_out`) kolem ohně**: kruh `polomer_m` pro kořen postavy i pro kosti rukou/hlavy; ověřuje se
   (a) poloha slotu, (b) trajektorie vstupu (jako `bCheckTransitionTrajectory`), (c) za běhu každý snímek u kořene.
   Porušení = slot se zahodí/ postava couvne, ne „projde“. Výchozí odhad: poloměr = poloměr ohniště + 0,35 m.
3. **Vstupní bod (`pristup`)**: samostatný bod mimo keep-out, odkud jde postava do slotu krátkým přechodem; zarovnat na
   zem (ground trace) a natočit čelem ke kotlíku.
4. **Rezervace slotu**: Free/Claimed/Occupied; jeden slot = jedna postava; uvolnit při přerušení.
5. **Sada klipů na aktivitu = vstup / smyčka / výstup + max. 1–2 „zpestření“** (Witcher job tree). Pro vaření:
   `vstup: dojit+zastavit`, `smycka: michani_ve_stoje`, `zpestreni: [prilozit_poleno, ochutnat/nahlédnout]`,
   `vystup: odlozit_varecku`. Zakázat v aktivitě klipy s výraznou změnou výšky pánve (`zakazane_pozy: [lehni, klek,
   sed_na_zemi]`), pokud slot výslovně neříká jinak.
6. **Kategorie klipu = pevná vlastnost klipu v datech** (`stoj`, `dřep`, `klek`, `leh`, `chuze`), aktivita dovolí jen
   některé – pak nemůže nastat „leží v ohni“ omylem z náhodného výběru.
7. **Cíl ruky = značka na předmětu** (`uchop_pozy.json`: kotlík → `ucho`, `nad_hrncem` pro vařečku), nikdy střed ohně;
   IK ruky zapnout jen ve fázi klipu, kde se ruka blíží (okno `ik_okno: [t0, t1]`), jinak čistý klip.
8. **Málo klipů, dlouhé smyčky**: hlavní smyčka ≥ 8–12 s nebo skládaná z 2–3 podsmyček (odhad), zpestření
   s náhodným intervalem v rozsahu (`zpestreni_interval_s: [min, max]`) a **zákaz opakování stejného zpestření dvakrát
   po sobě** (Animschool: neopakovat stejný fidget, makro-variace přes 3–6 smyček
   https://blog.animschool.edu/2024/06/14/breathing-life-into-idle-animations).
9. **Rekvizita vždy s postavou**: vařečka připnutá k ruce po dobu smyčky; kotlík nad ohněm, pára/oheň jako efekt objektu,
   ne postavy (Sims: offset a VFX vázané na klip – neměnit polohu postavy mimo klip).
10. **Kontrolní test** (`kontroly.json`): pro každou aktivitu u ohně spočítat vzdálenost kořene a kostí rukou od středu
    ohně přes celý klip (vzorkovat) – musí být ≥ `keep_out.polomer_m`.

---

## 2. Vlasy – „černé střepy“

### 2.1 Co dělají jiné hry a enginy
- **Struktura vlasů z karet**: nejdřív **neprůhledná základní vrstva**, která zakryje skalp a určuje tvar; pak řidší
  „breakup“ vrstvy; typický chomáč = 3 karty (1 hustší + 2 řidší). Neprůhledný základ šetří vrstvy průhlednosti.
  https://80.lv/articles/tips-tricks-on-hair-for-games/  https://cgmasteracademy.com/blog/jeff-hindsbol-hansen
  https://80.lv/articles/004adk-005cg-cgma-student-project-voluminous-hair
- Epic (Hair Card Generator): karta = obdélník s texturou pramenů, shluk obvykle **3 karty**; atlas sdílený, LODy
  zmenšují trojúhelníky karet a znovu používají stejný atlas; kvalita = rovnováha počtu shluků a trojúhelníků.
  https://dev.epicgames.com/documentation/unreal-engine/creating-hair-cards-and-lods-using-hair-card-generator
- **AO zapečené do vrcholů karet po vrstvách** (vnitřní vrstvy tmavší) – hloubka bez drahého stínování.
  https://80.lv/articles/techniques-for-game-character-hair-creation
- **Alpha test (scissor) a mipmapy**: s mipmapami se průměruje alfa, na vzdálenost propadne práh a vlasy/listí řídnou
  až mizí. Řešení The Witness: při stavbě každé mip úrovně přeškálovat alfu, aby zůstalo **stejné pokrytí**.
  https://www.ludicon.com/castano/blog/articles/computing-alpha-mipmaps/
  Unity má na to volbu `mipMapsPreserveCoverage`:
  https://docs.unity3d.com/ScriptReference/TextureImporter-mipMapsPreserveCoverage.html
- **Alpha hash** (stochastický práh) je pro vlasy často lepší než pevný práh – NVIDIA „Hashed Alpha Testing“
  https://research.nvidia.com/sites/default/files/pubs/2017-02_Hashed-Alpha-Testing/Wyman2017Hashed.pdf ;
  diskuse k vlasovým kartám https://discourse.threejs.org/t/alpha-test-vs-alpha-hash/44493
- **Alpha to coverage** vyžaduje MSAA; na mobilech není spolehlivě dostupné, potřeba fallback.
  https://forum.unity.com/threads/alpha-to-coverage-doesnt-work-reliably-on-mobile-devices.686842/
  https://en.wikipedia.org/wiki/Alpha_to_coverage

**Godot 4.4 konkrétně**
- Alpha Scissor: rychlejší než blend, **bez problémů s řazením**, vrhá stíny. Alpha Hash: poloprůhlednost ditherem,
  také vrhá stíny. Alpha blend: problémy s řazením při překryvu, pomalejší, bez stínů. Depth Pre-Pass zlepší řazení,
  ale poloprůhledné části se dál mohou řadit špatně.
  https://docs.godotengine.org/en/4.4/tutorials/3d/standard_material_3d.html
- Alpha antialiasing (= alpha to coverage) potřebuje MSAA ≥ 2× pro dobrý výsledek; hrana antialiasingu musí být
  **striktně pod prahem scissoru** (výchozí 0,3 při prahu 0,5). Bez MSAA jen pevný dither. (tamtéž, 4.5:
  https://docs.godotengine.org/en/4.5/tutorials/3d/standard_material_3d.html)
- Compatibility renderer: z AA má jen MSAA a SSAA; MSAA 2× „může být přijatelné na některém mobilním HW“, vyšší
  nepravděpodobně; FXAA není v Compatibility. MSAA nevyhlazuje 1bit průhlednost – na to je alpha antialiasing.
  https://docs.godotengine.org/en/4.4/tutorials/3d/3d_antialiasing.html
- Godot nemá order-independent transparency; překrývající se blend karty se nutně řadí špatně.
  https://docs.godotengine.org/en/stable/tutorials/3d/3d_rendering_limitations.html
- Cull Disabled = kreslí se i rub (výkon); u karet nutné, ale normály rubu jsou obrácené (**odhad**: bez
  „backlight“/oboustranného světla rub vychází černý – typická příčina „černých střepů“).

### 2.2 Diagnóza „černých střepů“ (odhad, ověřit na modelu)
1. Materiál vlasů v režimu Scissor s vysokým prahem + mipmapy → zbydou jen ostré trojúhelníkové špičky.
2. Rub karet osvětlený obrácenou normálou → černá.
3. Chybí neprůhledná základní vrstva/skalp ve stejné barvě → prosvítá tmavá hlava.
4. Textura vlasů bez dilatace barvy do průhledných pixelů → okraje tmavé (černá RGB pod alfou se při filtrování vmíchá).

### 2.3 Co z toho pro nás (`pravidla/svet/postavy_vzhled.json` → `vlasy`)
1. `rezim_pruhlednosti`: výchozí **scissor** (tablet, bez řazení); `alpha_hash` jako alternativa k testu na tabletu;
   **blend zakázat** pro vlasy (řazení, žádné stíny).
2. `prah_scissor` v datech (výchozí odhad 0,35–0,5) + kontrola: vlasy se ve vzdálenosti `lod_vzdalenosti` nesmí
   „vyprázdnit“ → **mipmapy s zachováním pokrytí** generovat nástrojem při importu (Castaño) nebo vypnout mipmapy
   u malé textury vlasů (odhad, porovnat).
3. `alpha_aa`: **na tabletu vypnuto** – CLAUDE.md zakazuje MSAA na tabletu a alpha to coverage bez MSAA dává jen
   pevný dither. Hladkost hran tedy řešit tvarem karet, alpha hash a mipmapami se zachováním pokrytí. (Kdyby se
   někdy povolilo, hlídat testem `alpha_aa_hrana < prah_scissor`.)
4. `oboustranne`: true + korekce normály rubu (shader: `if (!FRONT_FACING) NORMAL = -NORMAL;`) – pravidlo
   „rub nesmí být černý“.
5. **Povinný neprůhledný skalp/základ** ve stejné barvě jako vlasy (`zakladni_vrstva: true`), karty jen jako lem.
6. `dilatace_barvy` textury vlasů při importu (barva pramenů pod alfou místo černé) – nástroj v `tools/`.
7. AO po vrstvách do barvy vrcholů (vnitřní tmavší, max. ztmavení v datech).
8. Rozpočet: počet karet a trojúhelníků vlasů na postavu v `rozpocty.json` (číslo **odhad**: řádově stovky trojúhelníků
   pro NPC na tabletu); u vzdálených LOD vlasy = neprůhledná slupka.

---

## 3. Kůň – pastva (krk do C)

### 3.1 Co dělají jiné hry a reálná anatomie
- **Reálná poloha při pastvě**: hlava dolů k zemi, krk natažený **dopředu-dolů**, šíjový vaz (nuchal ligament) napnutý;
  krk je jedna dlouhá oblouková páka, ne „háček“. Při pastvě ze země si kůň často **rozkročí/předsune jednu přední
  nohu**; při krmení z výšky hrudi stojí rovněji.
  https://www.yourhorse.co.uk/horse-care/feeding-from-the-floor/
  Morfometrická studie poloh krku a zad při krmení ze země vs. ze sítě (6 koní, malý vzorek):
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7998216/
- **Pastevní krok**: duty factor blízký 1 – nohy skoro pořád na zemi, kůň se posouvá velmi pomalu po kroku.
  (Biology Letters 2018, odkaz v rešerši výše: https://pmc.ncbi.nlm.nih.gov/articles/PMC6012707)
- **Kritika herních koní (The Mane Quest)**: nosné přední nohy nesmí být pokrčené; neblendovat mezi chody; koně mají
  mimo jízdu **pást se, odpočívat, socializovat**; nezahlcovat řehtáním – raději dech, frkání, přešlapování.
  https://www.themanequest.com/blog/2024/7/16/adding-horses-to-your-game-tips-resources-dos-and-donts
- **RDR2** (Tobias Kleanthous, GDC 2021): vrstvené části (hlava, ocas, jezdec) jako samostatné „motions“ (~6 300
  celkem); na svazích **dedikované animace stoupání/klesání** vybírané podle sklonu, protože samotné IK vypadalo špatně.
  https://www.gamedeveloper.com/design/rockstar-s-quest-for-the-ultimate-video-game-horse
  https://gdcvault.com/play/1027230/AI-Summit-Making-the-Believable
- **Omezení pohledu**: Godot 4.4 `LookAtModifier3D` má `use_angle_limitation`, limity pro primární/sekundární osu,
  `damp_threshold` (nelineární útlum u kraje), `duration` (časová interpolace při změně cíle), `forward_axis`,
  `origin_safe_margin`. Dokumentace: modifikátor rodičovské kosti musí být v seznamu **nad** modifikátorem dceřiné.
  https://docs.godotengine.org/en/4.4/classes/class_lookatmodifier3d.html
  Unity Animation Rigging Multi-Aim má min/max limity a lze vypnout osu (např. roll):
  https://docs.unity3d.com/Packages/com.unity.animation.rigging@1.0/manual/constraints/MultiAimConstraint.html
- **IK v Godotu**: 4.4 přidal SkeletonModifier3D, LookAtModifier3D, RetargetModifier3D; 4.5 BoneConstraint3D/
  AimModifier3D; plné IK (TwoBoneIK3D, CCDIK3D, FABRIK3D) až **4.6** – v 4.4 tedy nemáme hotové nožní IK.
  https://godotengine.org/article/inverse-kinematics-returns-to-godot-4-6/
- **Osy kostí**: Godot 4 má Bone Pose včetně Bone Rest; resty se liší podle exportéru, stejně pojmenované kosti mají
  jiné transformace; referenční konvence = +Y od rodiče k dítěti, +X jako osa ohybu. Procedurální rotace v lokálních
  osách proto na cizím rigu ohne kost jinam.
  https://docs.godotengine.org/en/4.4/tutorials/assets_pipeline/retargeting_3d_skeletons.html
- **3ds Max Biped**: doporučuje se exportovat „herní“ kostru, ne biped helpery; přebytečné kosti jsou v enginu null
  kosti, které stojí paměť/CPU. https://forums.unrealengine.com/t/3dsmax-biped-rig-for-herotpp-default-blue-man/19213?page=3
  https://www.cryengine.com/docs/static/engines/cryengine-3/categories/1114113/pages/1310793
  (**odhad**: Biped má délku kosti podél lokální osy X, ne Y jako Godot konvence – rotace „kolem X“ v kódu pak kroutí,
  místo aby skláněla.)

### 3.2 Diagnóza (odhad)
Hero Horse má vlastní klip `eating` (snímky 546–646, `kun_hero.md`). Krk do C dozadu/dolů typicky vzniká, když se
přes autorský klip **přičte procedurální vrstva** (look-at, „živé kosti“, ohyb krku k zemi) počítaná v ose, která
na Biped kostech `horse Neck…Neck3` neznamená „předklon“, nebo když se ohyb rozdělí na všechny tři krční kosti stejným
znaménkem, ale hlava se k zemi „dotahuje“ zpětně. Druhá možnost: klip `eating` je přehráván se špatně ořízlým
úsekem/odlišným restem (snímek 0 = T-pose s posunem kořene 0,602 m).

### 3.3 Co z toho pro nás (`pravidla/svet/zvirata.json` / `jizda.json` → `kun.pastva`)
1. **Pastva = autorský klip `eating`, bez procedurálních vrstev krku.** `pastva.vrstvy_vypnout: [look_at, zivy_krk]`.
   Procedurální krk jen v idle stoji, a to s limity.
2. Pokud je nutná procedurální korekce: `osa_predklonu` **per kost v datech** (Biped ≠ Godot konvence), kontrolní test
   „hlava (kost `horse Head`) při pastvě: výška nad zemí ≤ `max_vyska_huby_m` a vodorovně **před** hrudí o ≥
   `min_predsunuti_m`“ – vylučuje C dozadu.
3. **Rozložení ohybu**: kořen krku nese většinu, další kosti postupně méně (`rozlozeni: [0.5, 0.3, 0.2]`, **odhad**),
   všechny stejným směrem (předklon), hlava kompenzuje jen náklon k zemi.
4. Pastva jako aktivita se vstup/smyčka/výstup: `sklon_hlavy (přechod 0,8–1,5 s, odhad)` → `eating` smyčka →
   občas `zvedni_hlavu+rozhlédni` (`looking_around`) → zpět. Mezi tím **pastevní krok** (malý posun, nohy téměř
   na zemi) místo klouzání.
5. Look-at koně (na hráče) **jen v idle**, s `use_angle_limitation`, limity (odhad: vodorovně ±60°, svisle ±25°),
   `duration` > 0, váha přechází na 0 při začátku pastvy.
6. Přední nohy při pastvě: buď klip, nebo předsunutí jedné nohy (v klipu); **nosné nohy rovné** (Mane Quest) –
   kontrolní test na úhel „koleno“ přední nohy ve fázi opory.
7. Import Biped: v `jizda.json kun.kosti` mapovat jen herní kosti; nepoužívané (Biped helpery) vyřadit z animace
   (méně kostí = levnější, viz §5).

---

## 4. Jízda a sladění chodů

### 4.1 Co dělají jiné hry
- **RDR2** (GDC 2021, Kleanthous): 4 chody – krok, klus, cval, trysk; každý má **min/ideální/max rychlost** (vyjadřují
  námahu, ne pevnou rychlost); animace se automaticky analyzují na rozsahy lineární, úhlové a boční rychlosti.
  Blending přes **6 3D blend spaces** (rovina/stoupání/klesání × levá/pravá vedoucí noha) přes rychlost, otáčení, sklon
  a změnu nohy. Změny chodu = **akcelerační/deceleracní cykly** s kontrolou změny rychlosti v pevném okně; vlastní
  zastavovací cyklus, aby šlo na poslední chvíli změnit názor. Otáčení na místě **kolem předních nohou**, ne středu.
  Boční rychlost (drift v zatáčce). Synchronizace jezdce: animace koně mají **sync tagy** (rytmus, došlapy, horní/dolní
  bod těla) a jezdec má odpovídající tagy → houpání jezdce sedí na chod.
  https://www.gamedeveloper.com/design/rockstar-s-quest-for-the-ultimate-video-game-horse
  https://www.pcgamer.com/the-mind-boggling-work-that-went-into-red-dead-2s-incredibly-lifelike-horses
- **Mane Quest**: každý chod vlastní animace, **neblendovat mezi chody** (ani mezi cvalem na různou nohu), přechody
  **ostré**; ukazovat hráči, v jakém je chodu; dovolit přesně krokovat chod nahoru/dolů (RDR, BotW); nenutit hráče
  k „mezirychlostem“ jemným vychýlením páčky (kritika AC a Ghost of Tsushima).
  https://www.themanequest.com/blog/2024/7/16/adding-horses-to-your-game-tips-resources-dos-and-donts
  https://www.themanequest.com/blog/2023/5/1/the-horses-in-ghost-of-tsushima-wonderful-details-and-fundamental-problems
  (GoT: chybí klidný cval mezi klusem a tryskem, přehnané kývání hlavy v trysku, v ostrých zatáčkách „dupání“.)
- **Kamera z první osoby na koni**:
  - KCD1 má cvar `wh_horse_cameracentering` (automatické vracení kamery do směru koně), hráči ho vypínají; existují
    módy vypínající houpání kamery na koni.
    https://nexusmods.com/kingdomcomedeliverance/mods/594  https://www.nexusmods.com/kingdomcomedeliverance/mods/647
    KCD2: mód s volbou vracení kamery na koni https://www.nexusmods.com/kingdomcomedeliverance2/mods/47 ; část hráčů
    první osobu na koni nesnáší https://steamcommunity.com/app/1771300/discussions/0/601895662819280659
  - RDR2: na PC volba „kamera relativně k hráči“ vs. „relativně ke koni“ (míření kamerou bez změny dráhy).
    https://shacknews.com/article/114938/how-to-fix-horse-controls-in-read-dead-redemption-2-on-pc
  - Xbox Accessibility Guideline 117: opakovaný pohyb obrazu (head bob) omezit, a pokud zůstane, **dát volbu ho
    vypnout**; ESO má posuvník intenzity, Cyberpunk škálu sekundárního pohybu kamery.
    https://learn.microsoft.com/en-us/gaming/accessibility/xbox-accessibility-guidelines/117
- **Animace na svahu**: RDR2 dedikované klipy stoupání/klesání místo čistého IK (výše). Mane Quest: při IK na
  nerovném terénu držet nosné přední nohy rovné.

### 4.2 Co z toho pro nás (`pravidla/svet/jizda.json`)
1. **Chody jako tabulka dat** pro každého koně (`kun_hero`, `henry`): `krok/klus/cval(trysk)` s `rychlost_min/ideal/max`,
   klip, `prehrat_rychlost = v / v_klipu` omezené na rozsah (`skala_min/max`, odhad 0,85–1,15), aby nohy neklouzaly.
   **Stejná tabulka pro oba koně** → sladění = stejné rychlosti chodů, jiné klipy. Rychlost klipu měřit nástrojem
   (posun kořene RM_* klipů / délka kroku), ne odhadovat.
2. **Diskrétní chody, žádný blend krok↔klus** podle páčky; páčka/tlačítko volí chod (stupně), plynulé je jen zrychlení
   uvnitř chodu. Přechod mezi chody krátký prolnutí (`prechod_s`, odhad 0,2–0,35 s) **synchronizovaný na fázi**
   (sync tag došlapu).
3. **Sync tagy** v datech pro každý klip chodu: časy došlapů a horního/dolního bodu hřbetu → z nich počítat houpání
   jezdce/kamery (místo samostatně laděné sinusovky). Tím se kamera „sladí“ s koněm automaticky.
4. **Kamera 1. osoby**: houpání = `houpani_nasobek × pohyb kosti sedla`, s **volbou intenzity 0–100 %** v nastavení
   (Xbox AG 117); dolní propust (`vyhlazeni_s`) na svislý pohyb; **horizont stabilizovat** (roll kamery ≈ 0);
   vracení kamery do směru koně volitelné a s prodlevou (`recentr_po_s`, `recentr_rychlost`), jako KCD cvar.
5. **Otáčení**: ve stoji pivot kolem předních nohou (posun středu otáčení dopředu v datech `pivot_offset_m`); v pohybu
   omezit úhlovou rychlost podle chodu (`max_uhlova_rychlost_deg_s` per chod) – na tryskem nelze otočit na místě.
6. **Zastavení**: vlastní klip/přechod zastavení z každého chodu, zrušitelný (RDR2), délka brzdné dráhy per chod v datech.
7. **Nasedání/sesedání**: kamera prolne z výšky očí chodce do výšky sedla po křivce, ne skokem; během něj vstup
   blokovaný (`nasedani_s`).
8. **Kontrolní měření** (`mereni_trasa.json`): projet stejnou trasu oběma koňmi, porovnat dobu, výkyv kamery
   (směrodatná odchylka výšky), počet přechodů chodu – nový kůň nesmí být horší v žádné metrice než původní.

---

## 5. Obecné zásady a rozpočty animací na mobilu

### 5.1 Co dělají jiné hry a enginy
- **Počet kostí**: Unity doporučuje pro mobil postavu **pod ~30 kostí**; 15 kostí navíc k 30 = o 50 % víc operací
  (Generic); max. 4 vlivy na vrchol; IK uzly zapečené do FK a odstranit z modelu.
  https://docs.unity3d.com/2018.3/Documentation/Manual/ModelingOptimizedCharacters.html
- **Neanimovat, co není vidět**: Unity Animator Culling Mode „Based on Renderers“ + vypnout Update When Offscreen.
  https://docs.unity3d.com/550/Documentation/Manual/MecanimPeformanceandOptimization.html
  Godot: `VisibleOnScreenEnabler3D` zapíná cílový uzel (enable_node_path, režim podle ProcessMode) jen když je
  na obrazovce; kontrola je přibližná. https://docs.godotengine.org/en/4.3/classes/class_visibleonscreenenabler3d.html
- **Snížená frekvence aktualizace**: Unreal Animation Budget Allocator – rozpočet v ms, max. tick rate, interpolace
  jen při překročení rozpočtu, výběr podle významnosti; URO (Update Rate Optimization) přeskakuje vyhodnocení.
  https://dev.epicgames.com/documentation/unreal-engine/animation-budget-allocator-in-unreal-engine
  https://dev.epicgames.com/documentation/unreal-engine/animation-optimization-in-unreal-engine?lang=en-US
  Pozor: hlášené „trhání“ při neinterpolovaném snižování frekvence
  https://forums.unrealengine.com/t/animationbudgetallocator-doesnt-utilize-interpolation-on-registered-components-and-it-feels-like-framerate-drop-what-is-a-proper-way-to-address-it/2663219
  Godot: `AnimationMixer.callback_mode_process = MANUAL` + vlastní `advance(delta)` → lze ručně tikat vzdálené
  postavy méně často. https://docs.godotengine.org/en/4.3/classes/class_animationmixer.html
- **Animační LOD v davu**: AC Unity – na 30 FPS s mnoha NPC nutný LOD i v animaci: méně kostí, bez IK, jednodušší
  look-at a procedurální rig; AI přepínaná podle vzdálenosti.
  https://www.slideshare.net/slideshow/assassins-creed-i/253244281
  https://www.gdcvault.com/play/1022141/Massive-Crowd-on-Assassin-s
  Hitman 2: ~1700 postav na úroveň, max. 700 na obrazovce, animace aktualizovaná asynchronně v jobech.
  https://www.intel.com/content/dam/develop/external/us/en/documents/06-create-a-scalable-and-destructible-world-in-hitman2-807276.pdf
  Akademické davové LOD: na nejnižším LOD aktualizace animace ~4 Hz (obecný výzkum, ne konkrétní hra – viz přehled
  https://typeset.io/pdf/a-survey-of-real-time-crowd-rendering-3gvcfk2bo0.pdf).
- **Motion Matching** (UE): cena roste s počtem kanálů a vzorků, doporučeno minimum kanálů – pro tablet a malý tým
  nevhodné (**odhad**: databáze + dotazy každý snímek). https://dev.epicgames.com/documentation/unreal-engine/motion-matching-in-unreal-engine
- **Skinning v Compatibility rendereru**: dokumentace jen uvádí, že skinning přidává vrcholovou zátěž a na dlaždicových
  mobilních GPU je drahá; čísla pro Compatibility nenalezena – nutné měřit.
  https://docs.godotengine.org/en/4.3/tutorials/performance/gpu_optimization.html
- **Idle variace**: základní idle smyčka + **2–4 sekundární idle** v náhodných intervalech, varianta doběhne celá
  (exit time) a vrací se do základu https://mocaponline.com/blogs/mocap-news/idle-animation-loop ; náhodný interval
  z rozsahu místo pevného https://dev.to/arkfuldodger/programming-natural-idle-character-animations-4l0g ;
  neopakovat stejný fidget za sebou, variace přes 3–6 smyček
  https://blog.animschool.edu/2024/06/14/breathing-life-into-idle-animations
- **Knihovny klipů**: Quaternius UAL (CC0, 120+ klipů, jeden rig; UAL2 přidává civilní činnosti – farmaření, pití,
  rybaření); prohlížeč klipů quaternius.com/animviewer.html.
  https://quaternius.com/packs/universalanimationlibrary.html  https://quaternius.com/packs/universalanimationlibrary2.html

### 5.2 Anti-jitter (proti cukání) – souhrn pravidel z výše uvedeného + odhady
- Minimální doba setrvání ve stavu (`min_setrvani_s`) a hystereze přepínání (jiný práh pro zapnutí a vypnutí) – **odhad**
  (obecná praxe, přímý zdroj nenalezen; Witcher/Uncharted to řeší pevnou sekvencí vstup/smyčka/výstup).
- Zpestření začíná jen na hranici smyčky (exit time) – zdroj mocaponline výše.
- Look-at s časovou interpolací (`duration`) a `origin_safe_margin` proti prudkým otočkám při blízkém cíli (Godot docs).
- Snížená frekvence animace jen s interpolací pózy nebo jen mimo blízký okruh (UE forum výše).
- Kořen postavy neposouvat skokem: přistoupit na vstupní bod, zastavit, pak teprve vstupní klip (UE slot + entrance).

### 5.3 Co z toho pro nás (`pravidla/svet/rozpocty.json` → `animace`, `postavy.json`)
1. **Pásma podle vzdálenosti/viditelnosti** v datech: `blizko` (plná frekvence, look-at, IK uchopu), `stredne`
   (aktualizace každý 2.–3. snímek přes `advance`, bez IK, bez look-at), `daleko` (≤ 5–10 Hz nebo zmrazená póza
   smyčky), `mimo_obrazovku` (nezpracovávat; čas jen připočítat). Hodnoty vzdáleností = **odhad**, ladit na tabletu.
2. **Max. počet plně animovaných postav současně** (`max_plne`) a priorita: hráčův cíl rozhovoru > nejbližší > ve středu
   obrazu.
3. **Rozpočet kostí** na NPC člověka a zvíře (Unity ~30 pro mobil jako horní orientace; náš UAL/Mixamo rig má víc –
   pro vzdálená pásma vyřadit prsty/obličej z vyhodnocení, **odhad**), max. 4 vlivy na vrchol – hlídat importem.
4. **Sady klipů na aktivitu** (viz §1) – limity v datech: `max_klipu_na_aktivitu` (odhad 4: vstup, smyčka, 1–2
   zpestření, výstup), `max_zpestreni`, `zpestreni_interval_s`, `neopakovat_po_sobe: true`.
5. **Idle**: 1 základní + 2–4 varianty, náhodný interval z rozsahu, varianty doběhnou do konce.
6. Žádný motion matching; chody koně a chůze lidí = klipy + měřená rychlost klipu.
7. **Testy**: (a) žádná kost rukou/hlavy v keep-out zóně ohně; (b) hlava koně při pastvě před hrudí a u země;
   (c) vlasy: rub nesmí být černý, vlasový materiál nesmí být blend; (d) jízda: metriky nového koně ≥ původní.

---

## Shrnutí priorit (pořadí práce)
1. Kuchařka: kotlík jako cíl se slotem + vstupním bodem, keep-out kolem ohně, sada vstup/míchání/(přiložit)/výstup,
   zákaz klek/leh v aktivitě, IK ruky jen na ucho kotlíku/vařečku. Test vzdálenosti kostí od ohně.
2. Kůň pastva: vypnout procedurální krk/look-at během pastvy, hrát autorský klip `eating`; osy krčních kostí v datech;
   test polohy hlavy.
3. Jízda: tabulka chodů s měřenými rychlostmi klipů, diskrétní chody, sync tagy → houpání kamery, volba intenzity
   houpání, stabilní horizont, volitelné vracení kamery.
4. Vlasy: scissor (nebo hash) + neprůhledný základ, oprava normály rubu, dilatace barvy textury, mipmapy se zachováním
   pokrytí; blend zakázat.
5. Rozpočty: pásma aktualizace animací + vypnutí mimo obrazovku, limity klipů a idle variant v JSON.
