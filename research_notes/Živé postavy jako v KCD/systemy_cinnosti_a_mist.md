# Systémy činností a míst (smart objects, rozvrhy, animace u předmětů)

Rešerše 11. 11. 2026. Jak otevřené hry (KCD/KCD2, RDR2, Zaklínač 3, Skyrim, FF XV, The Sims Medieval, UE5) dělají
uvěřitelný denní život postav: činnost je vázaná na **místo/předmět**, ne na postavu. Na konci doporučený datový model
pro naši Godot hru.

Poznámka ke zdrojům: ck.uesp.net a en.uesp.net vracely 403, Furniture/IdleMarker stránky Creation Kitu jsou proto
citovány přes výsledky vyhledávání a fóra. Přednášky Warhorse (GDC 2025) jsou dostupné jen jako anotace a novinové
shrnutí, ne jako slajdy.

---

## 1. Jak fungují smart objects a rozvrhy v KCD/KCD2 (Warhorse, CryEngine)

### Takeaway
Veřejně doložené je jen to, že KCD/KCD2 má rozvrhy NPC (domov – práce – hostinec), dálkový přesun mezi místy,
AI LOD pro tisíce NPC a NPC logiku v XML behavior trees (MBT) se „smart objects“; podrobnou dokumentaci smart objektů
KCD jsem nenašel. Přenositelný vzor ale dokládají ostatní hry: rozvrh vybírá *typ místa*, místo samo nese animace a pozici.

### Cited Findings
- GDC 2025 „Supporting Thousands of NPCs in Kingdom Come: Deliverance & KCD II“ (Petr Smrček) popisuje vývoj **AI LOD**
  a optimalizací z KCD do KCD2 z technického hlediska — [GDC schedule](https://schedule.gdconf.com/session/supporting-thousands-of-npcs-in-kingdom-come-deliverance-kingdom-come-deliverance-ii/915120); [GDC Vault](https://gdcvault.com/play/1035718/Supporting-Thousands-of-NPCs-in); shrnutí, že jde o Smrčka a AI LOD — [GamesRadar přes vyhledávání](https://gamesradar.com/games/rpg/kingdom-come-deliverance-had-to-add-complex-pathfinding-for-just-2-npcs-that-owned-horses-if-you-want-to-do-this-feature-you-have-to-support-it)
- Shrnutí téže přednášky: NPC v KCD2 „mají své cesty a životy, které sledují, ať s nimi hráč interaguje, nebo ne“;
  rozvrhy, questy, zločin a navigace musí zůstat v synchronizaci — [gamedev.net](https://gamedev.net/news/5526-supporting-thousands-of-npcs-in-kingdom-come-deliverance-kingdom-come/)
- Kuttenberg (Kutná Hora) byl navrhován kolem limitů streamingu, AI, navigace a **plánování (scheduling)**; hustota
  obyvatel je hlavní omezení návrhu města — [gamedev.net](https://gamedev.net/news/4891-designing-kuttenberg-city-around-design-constraints-kcd-2/)
- Matej Marko (AI programátor Warhorse, GDC 2025): systém **Long-Distance Movement** simuluje cesty NPC mezi prací,
  domovem a hostincem; kdo vlastní koně, jede na něm; použily ho nakonec jen 2 NPC; poučení „když funkci uděláš,
  musíš ji plně podporovat“ — [TheGeek.games](https://thegeek.games/?p=109791); [GamesRadar](https://gamesradar.com/games/rpg/kingdom-come-deliverance-had-to-add-complex-pathfinding-for-just-2-npcs-that-owned-horses-if-you-want-to-do-this-feature-you-have-to-support-it)
- KCD2: dynamické rutiny NPC se mění podle událostí (část vyvolá hráč) — [Wccftech, rozhovor s M. Zieglerem](https://wccftech.com/kingdom-come-deliverance-2-dev-talks-about-dynamic-npc-routines-and-emergent-storytelling-for-side-quests/)
- Už 2014 Warhorse uváděl, že s **objekty prostředí zachází jako s NPC** a plánování NPC je hlavní téma — [NicheGamer](https://nichegamer.com/2014/02/kingdom-come-deliverance-living-world-update/)
- Komunitní dokumentace KCD2 uvádí vrstvy NPC logiky: XGEN AI pro behavior trees (MBT) a smart objects — [muyuanjin/kcd2-mod-docs](https://github.com/muyuanjin/kcd2-mod-docs/blob/main/MODDING_STACK.md); oficiální wiki modování KCD2 — [Warhorse YouTrack](https://warhorse.youtrack.cloud/articles/KM-A-1/Modding-Kingdom-Come-Deliverance-2)
- CryEngine MBT = rozhodovací stromy v XML (proměnné, signály, timestampy, sekvence, selektory, priority, akce) — [CRYENGINE docs: Modular Behavior Tree](https://www.cryengine.com/docs/static/engines/cryengine-5/categories/23756813/pages/23306488)
- Tutoriál modování KCD: chování drží **SmartArea**, uloženo v Data/Libs/AI, chování najde tag point a dojde k němu
  (mirror starší stránky) — [Scripting Tutorial mirror](https://gamecytus.netlify.app/host-https-wiki.nexusmods.com/index.php/Scripting_Tutorial); [modding.wiki](https://modding.wiki/en/kingdomcomedeliverance/developers/scripting-tutorial)

### Inferences
- KCD model je ve shodě s ostatními: rozvrh (čas → kam/co) + místo s připravenou činností + AI LOD (vzdálené NPC jen
  „posouvají“ stav rozvrhu bez animací). Pro nás: rozvrh postavy musí jít simulovat i bez animací (skok do správného
  místa při přiblížení hráče), jinak NPC při načtení „startují od rána“.
- Poučení Marka platí i pro malou hru: každý typ místa (studna, kovadlina) = plná podpora (animace, rekvizita, test),
  jinak nedělat.

### Gaps
- Konkrétní formát smart objektů KCD (XML, sloty, sada animací enter/loop/exit) jsem v otevřených zdrojích nenašel;
  slajdy GDC 2025 i přednáška MFF 2018 nejsou veřejně v textu. Doporučeno: video na GDC Vault, případně rozbalit
  `Data/Libs/AI` a tabulky v `.pak` hry (jen ke studiu, ne kopírovat).
- Přednášku MFF 2018 jsem nedohledal.

---

## 2. Jak Skyrim (furniture / idle markery, AI packages), Zaklínač 3 (action points, community) a další vážou animaci na místo a orientaci

### Takeaway
Všechny studované systémy mají stejné jádro: **místo nese transformaci (pozice + natočení), typ/kategorii činnosti a
sadu animací** (vstup – smyčka/varianty – výstup, případně rekvizitu do ruky), postava místo jen vybírá podle rozvrhu a
**rezervuje**. Rozvrh nikdy neříká „přehraj animaci X“, ale „jdi dělat kategorii Y na vrstvě/v budově Z“.

### Cited Findings
**Skyrim / Creation Kit**
- IdleMarker = objekt, který určuje, jak se postava na daném místě chová; s volbou „Ignored by Sandbox“ ho sandbox
  package nenajde a použijí ho jen postavy na něj explicitně napojené — [CK wiki IdleMarker](https://ck.uesp.net/wiki/IdleMarker) (citováno přes výsledky hledání; stránka vrací 403)
- Mnoho idle animací je ve Skyrimu řešeno jako **Furniture** (oranžové markery), ne Idle Marker (modré „I“) — [CK wiki IdleMarker](https://ck.uesp.net/wiki/IdleMarker); [Fallout CK wiki](https://falloutck.uesp.net/wiki/IdleMarker)
- Napojení NPC: AI package se šablonou **UseIdleMarker** + Linked Reference na marker; u nábytku šablona **Sit** — [Nexus fórum](https://forums.nexusmods.com/topic/8345573-force-npc-use-idle); [CK: Sit procedure](https://ck.uesp.net/wiki/Procedure_Sit)
- Sandbox package nechá NPC volně používat okolní nábytek/markery v okruhu — [Fallout CK: Sandbox](https://falloutck.uesp.net/wiki/Sandbox_Package)
- Furniture markery mají **povolené směry vstupu** (front, behind, left, right, up); Bethesda kvůli tomu dělá varianty
  téhož nábytku (CommonWritingChair01L / 01R / 01LR); typy markerů Sit (0x01), Sleep (0x02) — [Nifskope Furniture tutorial (Beyond Skyrim)](https://wiki.beyondskyrim.org/w/images/a/ab/Nifskope_Furniture_tutorial.pdf); [UESP: FURN formát](https://en.uesp.net/wiki/Skyrim_Mod:Mod_File_Format/FURN); [Nexus fórum: entry points](https://forums.nexusmods.com/topic/10242203-remaking-the-furniture-entry-points)
- Vstupní bod a poloha sezení jsou svázané s animací — posunout entry point znamená předělat animaci — [Nexus fórum](https://forums.nexusmods.com/topic/10242203-remaking-the-furniture-entry-points)
- (Fallout 4) „interact points“ určují, kde končí vstupní animace; Marker Keyword omezí bod jen na postavy s daným keywordem — [Nexus fórum](https://forums.nexusmods.com/topic/12948471-where-are-animation-entry-points-definedcreated)

**Zaklínač 3 (REDkit)**
- Action point (AP) = waypoint, kde postavy hrají předdefinované animace z **Job Tree**; entita CActionPoint +
  CActionPointComponent s `jobTreeRes` — [REDkit wiki: Action points](https://redkitwiki.cdprojektred.com/actionpoints.htm)
- Job Tree: kořen = vstupní animace, potomek = hlavní animace, nahoře odchodová; Selection Mode Sequence/Random,
  Iterations, **Left/Right Item** (co je v které ruce), Remove at end, **Drop on break** (pustit předmět při přerušení),
  Anim Blend In/Out, Is Lookat Enabled, Can React — [REDkit wiki: Action points](https://redkitwiki.cdprojektred.com/actionpoints.htm)
- **Disable Path Agent**: NPC není kolizemi vytlačeno z AP (např. sezení u stolu) — [REDkit wiki](https://redkitwiki.cdprojektred.com/actionpoints.htm)
- Pre/post animace se dají vypnout při spawnu v AP (NPC se objeví rovnou sedící) a při přepnutí na tentýž AP (pracuje
  dál bez vstávání) — [REDkit wiki](https://redkitwiki.cdprojektred.com/actionpoints.htm)
- Community: Spawnset (šablona, počet, vzhledy, story phase, Start In AP, Is Hidden Spawn – spawn mimo kameru,
  Spawn Strategy – poloměr spawnu/despawnu, Despawn Point Tags) + Timetable (časové intervaly → Layer Name, Category,
  Weight, AP Tags). Výběr: vrstva → kategorie podle váhy → AP s touto kategorií na vrstvě — [REDkit wiki: Community editor](https://redkitwiki.cdprojektred.com/community+editor.htm); [REDkit Atlassian: Job Tree editor](https://cdprojektred.atlassian.net/wiki/spaces/W3REDkit/pages/6328487/TOOL%3A+Job+Tree+editor)
- Kategorie v spawnsetu musí sedět s kategorií na AP, jinak NPC nepracuje — [REDkit wiki přes vyhledávání](https://cdprojektred.atlassian.net/wiki/spaces/W3REDkit/pages/47186233/HOW-TO+Create+an+encounter+with+NPC+merchant)

**RDR2 / GTA V (scenarios)**
- Scénáře RDR2 (káva, sklenice barmana, opírání o zeď) používají vestavěné rekvizity Rockstaru; skript umí postavu
  dovést k markeru nebo spustit scénář na místě; existují „conditional anims“ — [CodeRanch RedM docs](https://coderanch-redm-store.gitbook.io/coderanch-redm-store-docs/coderanch-animation-menu); [Benitobreal Scenarios](https://premium-scripts-by-benitobreal.tebex.io/package/6833552)
- Tisíce scénářů jsou jen pro NPC a hráčova výzva se nezobrazí, když scénář už NPC používá (= rezervace) — [Nexus RDR2 mod](https://www.nexusmods.com/reddeadredemption2/mods/2784)
- GTA V ukládá scenario points do .ymt (body, cesty/řetězy), editovatelné v CodeWalkeru — [CodeWalker](https://www.gta5-mods.com/sl/tools/codewalker-gtav-interactive-3d-map); [FiveM fórum](https://forum.cfx.re/t/streaming-overriding-scenario-ymt/136666/74)
- RDR2 má podle Rockstaru ~10× víc animačních dat než GTA V (sekundární zdroj) — [rdr2.org](https://www.rdr2.org/news/red-dead-redemption-2-ai-animations-physics-open-world-experience/)

**The Sims Medieval (Game AI Pro, D. Graham)**
- Rozvrh = černá skříňka: vstup čas, výstup akce „jdi sem a pusť tuhle animaci“; záznamy rozvrhu po časových
  blocích; akce cílí na **typ objektu** (bed, baker_oven), NPC nejdřív použije svůj vlastněný, jinak nejbližší;
  vlastnictví po budovách (domov/práce) z tabulky; WeightedRandom (např. 75 % stůl, 25 % kopírka); šablony rozvrhů
  s dědičností — [Graham: Breathing Life into Your Background Characters, GAP1 kap. 36](http://www.gameaipro.com/GameAIPro/GameAIPro_Chapter36_Breathing_Life_into_Your_Background_Characters.pdf)
- Ukázka akce: `<Action name="bake_in_oven" target="baker_oven" minDuration="0.1" maxDuration="0.2" animation="bake_bread.anm"/>` — [tamtéž](http://www.gameaipro.com/GameAIPro/GameAIPro_Chapter36_Breathing_Life_into_Your_Background_Characters.pdf)

**UE5 Smart Objects (moderní referenční API)**
- Definice má **sloty** (pozice + rotace vůči kotvě), Activity Tags, Behavior Definition (výchozí, slot může přepsat),
  user-required tags. Cyklus: FindSmartObjects → ClaimSmartObject (Free→Claimed, Claim Handle) → navigace na
  GetSlotTransform → Use (Claimed→Occupied) → Release; při změně stavu objektu se sloty uvolní a agent dostane
  OnSlotInvalidated — [Epic: Smart Objects overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/smart-objects-in-unreal-engine---overview)

**FF XV (Skubch) a Smart Zones**
- Smart Locations: chytrý objekt, který spravuje více rekvizit a skript pro více rolí (lavička: starý muž + turista);
  pravidla typu STRIPS s předpoklady a efekty, rezervace jako fakt v lokální tabuli — [Skubch, GAP3 kap. 35](http://www.gameaipro.com/GameAIPro3/GameAIPro3_Chapter35_Ambient_Interactions_Improving_Believability_by_Leveraging_Rule-Based_AI.pdf)
- Smart Zones: „živá scéna“ (hospoda: hosté jedí/pijí, skupina přátel u stolu, hostinský obsluhuje) je zóna s rolemi,
  chováními a časovou osou se synchronizačními body; při vstupu do zóny NPC dostane roli a připojí se k právě běžící
  fázi — [de Sevin a kol., GAP2 kap. 11](http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter11_Smart_Zones_to_Create_the_Ambience_of_Life.pdf)

### Inferences
- Shodné prvky napříč hrami → minimální záznam místa: transformace, kategorie/tag, směr(y) vstupu, výška (zem/lavice/
  stůl), animace vstup/smyčky/výstup, rekvizita a ruka, chování při přerušení (pustit/odložit), počet slotů, zda
  vypnout tlačení kolizemi, lookat ano/ne, kdo smí (role/vlastník).
- Skyrimový trik s variantami L/R/LR ukazuje, že směr vstupu je vlastnost **místa** (zeď vedle židle blokuje bok), ne
  animace – u nás řešit v záznamu (`vstupy: ["zepredu","zleva"]`), ne v kódu.
- Hospoda je lepší jako zóna (Smart Zone/Smart Location) se sloty než jako volné body: obsluha stolů potřebuje vědět,
  kdo u kterého stolu sedí.

### Gaps
- Oficiální dokumentace RDR2 scenario systému (struktura, enter/exit, conditional anims) není veřejná; máme jen
  pohled modderů. Nativní databázi RDR3 (alloc8or nativedb) jsem neotevřel.
- Mount & Blade jsem nezkoumal (nevyšly relevantní zdroje v rozpočtu dotazů).

---

## 3. Zarovnání postavy k místu bez klouzání nohou a prolínání (snap / warping / motion correction)

### Takeaway
Standard je: dojít navigací na **přibližovací bod** (před místem, ve směru vstupu), pak vstupní animace, během níž se
zbývající rozdíl polohy a natočení **rozprostře po snímcích** (motion warping / motion correction) do cílové
transformace slotu; teprve smyčka běží v přesné poloze. Okamžitý „snap“ jen mimo kameru nebo při spawnu.

### Cited Findings
- Motion correction u jednorázových animací (nastoupení do vozidla, interakce s objektem): spočítat rozdíl mezi koncem
  animace a cílovou polohou a každý snímek přidat úměrnou část delty polohy i natočení; lze upravit i rychlost — [Shroff, GAP2 kap. 36](http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter36_Realizing_NPCs_Animation_and_Behavior_Control_for_Believable_Characters.pdf)
- Aby klouzání nebylo vidět: animace má mít trochu přešlapování v obou nohou, delta se rozloží rovnoměrně přes rotační
  část a kořen se točí konstantní rychlostí; 3 rozjezdové animace + korekce pokryly 360° — [Shroff](http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter36_Realizing_NPCs_Animation_and_Behavior_Control_for_Believable_Characters.pdf)
- Oddělit extrahovaný pohyb kořene od pózy (motion extraction) umožní pohyb upravit, ale úpravy držet malé, jinak
  postava viditelně klouže — [Shroff](http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter36_Realizing_NPCs_Animation_and_Behavior_Control_for_Believable_Characters.pdf)
- UE5 Motion Warping: okno (Anim Notify State) v montáži; Skew Warp upraví root motion, aby na konci okna seděla poloha
  i rotace s cílem; cíl se zadává jménem z transformace (AddOrUpdateWarpTargetFromTransform); volby bWarpToFeetLocation,
  Warp Translation — [Epic: Motion Warping](https://dev.epicgames.com/documentation/en-us/unreal-engine/motion-warping-in-unreal-engine)
- Skubch: akce `sit` se zeptá animačního systému, kde má stát vůči židli při spuštění animace sednutí, dojde tam a
  teprve pak animaci spustí — [Skubch](http://www.gameaipro.com/GameAIPro3/GameAIPro3_Chapter35_Ambient_Interactions_Improving_Believability_by_Leveraging_Rule-Based_AI.pdf)
- Godot: AnimationTree má root motion track; `get_root_motion_position()/rotation()` (delta) a `..._accumulator()`;
  aplikace do CharacterBody3D; StateMachine přechody Immediate/Sync/At End, Xfade Time/Curve, Advance Condition/
  Expression, `travel()`; OneShot s fade in/out — [Godot docs: AnimationTree](https://docs.godotengine.org/en/stable/tutorials/animation/animation_tree.html)
- Zaklínač 3: Disable Path Agent, aby sedícího NPC nevytlačily kolize — [REDkit wiki](https://redkitwiki.cdprojektred.com/actionpoints.htm)

### Inferences
- Pro Godot bez warping pluginu: vstupní klip má root motion; spočítat `chyba = cíl_slotu − (poloha + celkový root
  motion klipu)` a v okně (např. prvních 60 % klipu) přičítat `chyba * Δt/délka_okna`; rotaci stejně (slerp).
  Ověřit metrikou „klouzání chodidel“ (posun kosti chodidla v kontaktu > 2 cm/snímek = chyba).
- Bez root motion (in-place klipy): ze záznamu brát `priblizeni_m` (kam dojít) a krátkou interpolaci 0,2–0,4 s
  během vstupní animace; nikdy nesnapovat ve výhledu kamery.
- Během smyčky vypnout tlačení/vyhýbání (ekvivalent Disable Path Agent) a kolizi postavy s nábytkem daného místa,
  jinak fyzika postavu vytlačí ze židle.

### Gaps
- Konkrétní tolerance (cm, °) používané studii pro „snap vs. warp“ jsem nenašel – musíme změřit sami (NEOVĚŘENO).

---

## 4. Rezervace, variabilita, tlačenice, typické chyby a QA ambientního života

### Takeaway
Rezervovat slot **v okamžiku rozhodnutí** (ne až po příchodu), uvolnit vždy (i při přerušení), proti „dvojčatům“
použít tabuli běžících animací se zpožděním, variabilitu dělat levnými krátkými one-offy/aditivy místo mnoha dlouhých
smyček, a chyby chytat automatickými testy nad daty míst + vizuální kontrolou.

### Cited Findings
- Rezervace: `sit(X)` má předpoklad `seat(X) ∧ ¬reserved(X,Y)` a efekt `reserved(X,.me)` hned při rozhodnutí; po
  dokončení `sitting(.me)` + časovač `randf(2,5)` minut; smart location má výhradní vlastnictví svých rekvizit; role
  málokdy víc než 3–4, herců málokdy víc než 5; přidělení rolí náhodné (Monte Carlo), smí občas selhat; účastníky
  míchat, aby pravidla nezvýhodňovala prvního — [Skubch](http://www.gameaipro.com/GameAIPro3/GameAIPro3_Chapter35_Ambient_Interactions_Improving_Believability_by_Leveraging_Rule-Based_AI.pdf)
- UE5: agent musí slot uvolnit sám (Release) po dokončení i přerušení; při změně objektu systém sloty uvolní a pošle
  OnSlotInvalidated — [Epic Smart Objects](https://dev.epicgames.com/documentation/en-us/unreal-engine/smart-objects-in-unreal-engine---overview)
- Zaklínač 3: „Drop on break“ – co udělat s rekvizitou při přerušení; „Remove at end“ — [REDkit wiki](https://redkitwiki.cdprojektred.com/actionpoints.htm)
- Častá chyba: kovář, který celou hru jen buší, hostinský, který věčně utírá pult, plus náhodné bloudění – vypadá
  to jako NES/SNES; opačná chyba: příliš hluboká AI pro pozadí; pro iluzi města je potřeba 20–30 viditelných NPC,
  4–5 nestačí — [Graham](http://www.gameaipro.com/GameAIPro/GameAIPro_Chapter36_Breathing_Life_into_Your_Background_Characters.pdf)
- „Animation twinning“: dvě postavy hrají stejnou animaci současně – oko to hned pozná; řešení: sdílená tabule
  (id animace, čas startu, poloha, priorita NORMAL/REACTION), zpoždění u ambientních animací, ne u reakcí;
  prostorově vzdálené postavy smí stejnou animaci dřív — [Dawe, GAP2 kap. 6](http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter06_Preventing_Animation_Twinning_Using_a_Simple_Blackboard.pdf)
- Variabilita levně: kontextové one-offy (podrbat se, přenést váhu) jako malé klipy nad smyčkou s fázovým navázáním;
  aditivní šumové animace nad jednosnímkovými idle pózami; mikro-chování; **akční tokeny** omezují, kolik NPC smí
  danou akci dělat naráz — [Shroff](http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter36_Realizing_NPCs_Animation_and_Behavior_Control_for_Believable_Characters.pdf)
- Smart Zones: synchronizační body na časové ose (žonglér skončí → diváci přestanou tleskat a gratulují); překrývající
  se zóny potřebují prioritu — [de Sevin a kol.](http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter11_Smart_Zones_to_Create_the_Ambience_of_Life.pdf)
- Zaklínač 3 proti „pop-inu“: Is Hidden Spawn (spawn mimo kameru), Spawn Strategy (poloměr), spawn rovnou v AP bez
  vstupní animace, Despawn Point Tags (odejít ke dveřím, pak zmizet) — [REDkit Community editor](https://redkitwiki.cdprojektred.com/community+editor.htm)
- Ladění: REDkit má návod na hledání a debug encounterů a náhled job tree bez spuštění hry — [REDkit: Find and debug encounters](https://cdprojektred.atlassian.net/wiki/spaces/W3REDkit/pages/43810840/HOW-TO+Find+and+debug+encounters); [REDkit Action points](https://redkitwiki.cdprojektred.com/actionpoints.htm)
- KCD poučení: každou funkci plně podporovat, i když ji používají 2 NPC — [TheGeek.games](https://thegeek.games/?p=109791)

### Inferences (typické chyby → automatická kontrola)
| Chyba | Příčina | Kontrola (test nad daty / snímek) |
|---|---|---|
| Postava „sedí“ ve vzduchu / jí ze země u stolu | klip pro zem použit u stolu (špatná sémantika) | každý klip má štítek `vyska` (zem/lavice/stůl/pult); test: `misto.vyska == klip.vyska` |
| Ruce v desce stolu, nohy v lavici | offset slotu z oka, ne z modelu | odstup slotu od kolizního tvaru nábytku v pásmu z `pasma`; snímek z boku |
| Vědro drží za dno / rekvizita plave | špatný attach bod / chybí kost ruky | rekvizita má `uchop` (Marker3D) a přiřazenou kost; test vzdálenosti dlaně a úchopu < tolerance |
| Dva lidi na jedné židli | rezervace až po příchodu | rezervace při rozhodnutí; test: žádný slot dvakrát `obsazen` |
| Zaseknutí ve dveřích | přibližovací bod v průchodu / ve zdi; dveře jako místo činnosti | test: přibližovací bod na navmeshi, ne v pásmu dveří; nic neleží blíž než X ke dveřím (`pasma`) |
| Kovář buší 24 h | jedna smyčka bez rozvrhu | rozvrh má ≥ 3 bloky; smyčka max. N minut, pak varianta/přestávka |
| Dvojčata | stejný klip ve stejné fázi | náhodný start fáze + tabule zpoždění |
| Vstup přes zeď | povolen směr vstupu, který blokuje geometrie | raycast od přibližovacího bodu ke slotu bez zásahu |
| Rekvizita zůstane v ruce po přerušení | chybí `pri_preruseni` | každý záznam s rekvizitou musí mít `pri_preruseni` |
- Kolik animací na činnost (z literatury nepřímo): Zaklínač 3 = vstup + hlavní (sekvence/náhodně) + odchod; Shroff
  ukazuje, že variabilitu nese spíš 2–4 krátkých one-offů nad 1–2 smyčkami než mnoho smyček. Pro malou hru rozumné
  minimum: 1 vstup, 1–2 smyčky, 1–3 krátké přestávkové varianty, 1 výstup (odhad, ne citovaný standard).

### Gaps
- Nenašel jsem veřejný popis QA procesu ambientního života velkých studií (automatické „soak“ testy, heatmapy obsazení);
  doporučení v tabulce jsou odvozená.
- Přesné počty animací na scénář v RDR2/KCD nejsou veřejně doložené.

---

## 5. Doporučený datový model pro malou Godot hru (místa činností + jak je NPC používá)

### Takeaway
Místo činnosti = záznam v datech (JSON, souladně s naším pravidlem „každý díl je záznam“), postavené v kroku
„předměty“ jako Marker3D; rozvrh profese vybírá **kategorii**, ne konkrétní místo; NPC místo vyhledá, rezervuje slot,
dojde na přibližovací bod, vstupní klip se dorovná na transformaci slotu, pak smyčky s variantami, výstup, uvolnění.

### Cited Findings
- Vzor rozvrh → kategorie s váhou → místo na vrstvě/v budově: [REDkit Community editor](https://redkitwiki.cdprojektred.com/community+editor.htm); [Graham](http://www.gameaipro.com/GameAIPro/GameAIPro_Chapter36_Breathing_Life_into_Your_Background_Characters.pdf)
- Vzor slot + claim/use/release: [Epic Smart Objects](https://dev.epicgames.com/documentation/en-us/unreal-engine/smart-objects-in-unreal-engine---overview)
- Vzor vstup/hlavní/odchod + rekvizita v ruce + chování při přerušení: [REDkit Action points](https://redkitwiki.cdprojektred.com/actionpoints.htm)
- Godot nástroje: AnimationTree StateMachine (`travel()`, xfade, At End), OneShot pro přestávkové varianty, root motion
  API — [Godot docs](https://docs.godotengine.org/en/stable/tutorials/animation/animation_tree.html)

### Inferences – návrh

**a) Typ činnosti** (`pravidla/svet/cinnosti.json`, sdílené pro všechna místa daného typu):
```json
"cerpat_vodu": {
  "kategorie": "voda",
  "vyska": "zem",                       // zem | lavice | stul | pult | kovadlina
  "klipy": {
    "vstup":  "studna_vstup",           // root motion, konec = poloha slotu
    "smycky": [["studna_tocit", 3], ["studna_tahat", 1]],   // [klip, váha]
    "prestavky": ["opreni_o_roub", "otrit_cel"],            // OneShot, náhodně 20–40 s
    "vystup": "studna_vystup_s_vedrem"
  },
  "rekvizita": {"model": "vedro_drevene", "kost": "ruka_P", "uchop": "ucho",
                "kdy": "vstup@0.7", "pri_preruseni": "polozit", "po_konci": "nest"},
  "trvani_min": [3, 8],
  "lookat": true, "vypnout_vyhybani": true, "max_naraz_v_okoli": 1   // akční token
}
```
**b) Místo** (záznam v datech světa, v pořadí stavby „předměty“; pozice počítá stavba z kotvy objektu, ne ručně):
```json
{"id": "ves_studna_1", "objekt": "studna_A", "cinnost": "cerpat_vodu",
 "sloty": [{"offset": [0, 0, -0.65], "natoceni_deg": 0, "vyska_m": 0.0,
            "vstupy": ["zepredu"], "priblizeni_m": 0.9}],
 "vlastnik": null, "budova": "ves_navsi", "otevreno": [5, 21]}
```
Hospoda: stůl = jedno místo se 4–6 sloty `sedet_jist` (`vyska: lavice`, ruce na úrovni `stul`), pult = slot
`obsluha` s cestou „pult → slot u stolu → pult“ (obsluha čte, které sloty stolu jsou obsazené – zóna jako v FF XV).

**c) Rozvrh profese** (`pravidla/svet/rozvrhy.json`, šablony s dědičností jako Sims Medieval):
```json
"kovar": [{"od": 5, "kat": [["jidlo_doma", 1]]},
          {"od": 6, "kat": [["kovadlina", 6], ["vyhen", 3], ["voda", 1]], "misto": "vlastni"},
          {"od": 12, "kat": [["sedet_jist", 1]], "budova": "hostinec"},
          {"od": 13, "dedi": 1}, {"od": 19, "kat": [["sedet_pit", 1]], "budova": "hostinec"},
          {"od": 22, "kat": [["spat", 1]], "misto": "vlastni"}]
```
**d) Jak NPC místo použije** (stavový automat, jedna instance na NPC):
1. Rozvrh → kategorie (vážený los) → kandidáti: vlastní místo, jinak v budově, jinak nejbližší volné v okruhu.
2. Rezervovat slot hned (`obsazen_kym = npc`); neúspěch → další kandidát; nic → „počkat/procházka“ max. 30 s.
3. Navigace na přibližovací bod (`slot − směr_vstupu * priblizeni_m`), dorazit s xfade do stání.
4. Vstupní klip; v okně 0–60 % dorovnat polohu/rotaci na slot (warp), vypnout vyhýbání; rekvizitu připojit
   v čase `kdy` přes BoneAttachment3D + offset úchopu.
5. Smyčky podle vah, náhodná počáteční fáze; po 20–40 s OneShot přestávka; tabule animací brání dvojčatům v okruhu ~15 m.
6. Konec bloku / přerušení (hráč, poplach): výstupní klip (při přerušení zkrácený), rekvizita podle `pri_preruseni`/
   `po_konci`, **uvolnit slot vždy** (i při despawnu).
7. AI LOD: mimo dosah jen posouvat stav rozvrhu (bez animací); při přiblížení umístit rovnou do slotu ve smyčce
   (bez vstupu, jako Zaklínač „Start In AP“) a spawnovat mimo kameru.

**e) Testy (do `test_smyslu`/`zasazeni`)**: výška klipu = výška slotu; slot a přibližovací bod na navmeshi a mimo
pásmo dveří/cesty (`pasma`); raycast přibližovací bod → slot volný; rekvizita má úchop a `pri_preruseni`; každá
kategorie v rozvrzích má aspoň tolik slotů, kolik NPC ji může chtít naráz; žádný rozvrh nemá jeden blok > 8 h
mimo spánek; snímek každého typu místa s postavou ve smyčce (zepředu + z boku) před vydáním.

### Gaps
- Všechna konkrétní čísla v návrhu (60 % okno, 20–40 s, 15 m, 0,9 m) jsou výchozí odhady – NEOVĚŘENO, nastavit
  v `pasma`/`cinnosti.json` a změřit na tabletu.
- Zda máme pro každou činnost hotové klipy (Mixamo, Quaternius „Universal Animation Library“ apod.) jsem neověřoval –
  patří do samostatné rešerše animací.
