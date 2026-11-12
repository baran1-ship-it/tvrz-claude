# Technický průzkum otevřených historických světů

## Grafika, vykreslování, optimalizace, streamování a simulace

**Stav průzkumu: 12. listopadu 2026**

Tento dokument shrnuje veřejně dostupné informace o projektech, které
byly vybrány v předchozím průzkumu. Rozlišuje mezi doloženými
implementacemi, tvrzeními autorů, plánovanými funkcemi a projekty, které
jsou pouze technickými experimenty. Čísla FPS a rozsahů nejsou
přenositelná mezi různým hardwarem.

------------------------------------------------------------------------

# 1. Rychlý přehled

  ---------------------------------------------------------------------------
  Projekt           Technologie / typ     Co je technicky   Stav důkazů
                                          nejzajímavější    
  ----------------- --------------------- ----------------- -----------------
  The Last Eagle    Godot 4, Terrain3D,   tráva, animace    veřejné
                    Blender; 3D RPG       davu, FSR 2, AA,  vývojářské deníky
                                          kamera, stíny,    a Reddit autora;
                                          world map → 3D    bez veřejného
                                          lokace            buildu

  Hearth & Fortune  Unity a Unreal 5; 3D  vegetace,         podrobné deníky;
                    sandbox               grafické úrovně,  uzavřená alpha
                                          velký heightmap,  
                                          oddělené          
                                          testovací větve   

  Latticefolk       Three.js r180,        coarse/fine chunk veřejný GitHub a
                    TypeScript, Node.js;  streaming,        technická
                    3D web sandbox        persistence,      dokumentace
                                          fyzika,           
                                          deterministická   
                                          simulace          

  The End of        Unreal Engine 5;      velká společnost  vydaná Early
  History           sandbox RPG/strategie NPC, UE5, reálné  Access hra; málo
                                          HW požadavky      veřejných detailů
                                                            render pipeline

  Iberia Medieval   procedurální          hydrologie,       Reddit autora;
                    geologicko-terénní    povodí, geologie  zatím bez
                    prototyp              a hexová mapa     hratelné hry

  Brunnfeld         TypeScript/Node.js;   až 1 000 agentů   veřejný GitHub;
                    ekonomická simulace   jako deklarovaný  2D/pixelový
                                          cíl, dávkování a  prohlížeč, nikoli
                                          souběh LLM        3D open world

  AI Civilization   PixiJS; 2D simulace   16×16 chunk       veřejný GitHub a
  Simulation                              baking, spatial   popsané
                                          hash, culling,    optimalizace
                                          throttling        

  Etherworld        Unity; medieval       procedurální      stručný README;
                    city-builder prototyp mapa, suroviny,   render
                                          NPC, crafting     optimalizace
                                                            nedoložena

  Bellwright        Unreal Engine;        opravy CPU        oficiální patch
                    komerční open-world   micro-stutter,    notes a komunitní
                    survival              upscaling,        hlášení
                                          foliage, počasí,  
                                          minimapa          

  Liangshan Deep    popis čínského        DEM, satelitní    zdroj je označen
                    open-world projektu   data, QGIS, LOD a jako
                                          occlusion         AI-generated;
                                                            nízká
                                                            důvěryhodnost
  ---------------------------------------------------------------------------

# 2. The Last Eagle: nejbližší hobby projekt k našemu směru

**Odkazy** - Hra: https://dometgames.itch.io/the-last-eagle - Devlog:
https://dometgames.itch.io/the-last-eagle/devlog - Reddit, autorův
technický popis:
https://www.reddit.com/r/aigamedev/comments/1xb2oep/6_months_of_solo_parttime_dev_on_my_first_game_a/

## Technologie a hardware

Autor uvádí Godot 4 + Terrain3D pro světovou mapu. Postavy používají
AnimationTree, retargetované animace a spring bones pro pláště a
oblečení. Většina postav, budov a rekvizit pochází z koupených asset
packů, které autor upravuje; část rekvizit a UI vznikla pomocí AI
nástrojů a následných úprav.

Autor uvedl vlastní vývojový počítač Ryzen 5 3600, Radeon RX 580 a 16 GB
RAM. Optimalizace pro starší hardware je podle něj důležitá. Záběry
traileru pořídil v Godotu Movie Maker při uzamčených 30 FPS. To není
důkaz, že běžná hra běží na 30 FPS na všech scénách.

## Doložené grafické a výkonnostní postupy

### Vegetace

-   Tráva sahá daleko do horizontu, aby hráč neviděl pohybující se
    hranici louky.
-   Autor odstranil blikání trávy při pohybu.
-   V pozdějším deníku uvádí, že tráva nyní stojí města přibližně
    polovinu původních nákladů.
-   Kamera má řešit situace, kdy se hráč dívá skrz trávu nebo koruny
    stromů: tráva se kolem objektivu odklání a listí řídne při
    přiblížení.
-   To je zajímavé nejen jako optimalizace, ale také jako ochrana obrazu
    před obřím polygonem trávy těsně před kamerou.

### Anti-aliasing a upscaling

Veřejně popsané možnosti: - Anti-aliasing Off, FXAA, SMAA, TAA. - FSR 2
upscaling. - Texture filtering až 16×. - V-Sync včetně Adaptive
režimu. - FOV 60--90°. - FPS limit včetně 48 a 72 FPS. - Motion blur
Off/Low/High; autor uvádí náklad pod 0,5 ms a možnost jej vypnout.

### Animace davu

-   Dříve se vzdálené postavy aktualizovaly jen několikrát za sekundu.
-   To způsobovalo trhanou chůzi.
-   Nově viditelné postavy působí plynuleji a postavy, které lze
    rozeznat při chůzi, mají animaci na plné frekvenci.
-   Režim Crowd nabízí Performance, Balanced a Cinematic.
-   To je přímý příklad škálování kvality animací podle výkonu a významu
    postavy.

### Stíny a materiály

-   Při detailním záběru na obličej autor zpřesnil sluneční stíny
    přibližně čtyřikrát.
-   Hrany kamene a dřeva dostaly zaoblení odpovídající velikosti
    objektu, například 3 cm u nábytku a 14 cm u zdi.
-   Kulaté objekty jako kola, klády a úly dostaly hladší stínování.
-   Autor řešil i prosvítání mezi hlavou a tělem, průnik oblečení do
    končetin, zbroje a štítu.
-   Nejde o obecný důkaz konkrétního shaderového řešení; deník popisuje
    výsledek, nikoli celý zdrojový kód.

### Kamera a obraz

-   Camera smoothing sjednocuje pocit z myši napříč FPS.
-   Camera damping tlumí pohyb kamery při schodech a změnách výšky.
-   Kamera se při přiblížení ke zdi rychle stáhne a plynule se vrací.
-   Na světové mapě byl upraven anti-aliasing a lehké doostření, aby se
    terén při cestování nerozmazával a počty vojáků zůstaly ostré.

### Kolize a život ve světě

-   Vesničané, voli a povozy se přestali propadat do nerovného terénu.
-   NPC a zvířata se vyhýbají projíždějícímu vozu.
-   Sedící postavy se správně usazují na lavici.
-   Dveře a okenice mají vlastní správné umístění.
-   Zahradníci používají nástroje a zasazené rostliny zůstávají v
    záhonu.
-   To ukazuje, že vizuální kvalita vyžaduje také přesné vazby mezi
    animací, kolizí, terénem a objekty.

## Co není veřejně doloženo

-   Přesné FPS v konkrétních scénách mimo uzamčené záběry.
-   RAM/VRAM při běžném hraní.
-   Konkrétní počet draw calls, polygonů, shader instrukcí.
-   Přesná implementace LOD stromů a trávy.
-   Přesná velikost a streamingová strategie 3D lokací.
-   Veřejně stažitelný herní build zatím není.

**Použitelné poučení:** oddělit kvalitu trávy, animací davu, stínů a
kamery do samostatných nastavení. Nezpracovávat každou postavu a každou
rostlinu stejně draze.

# 3. Hearth & Fortune: vegetace a měřitelná práce s krajinou

**Odkazy** - Oficiální stránka:
https://www.iconicxp.games/games/hearth-and-fortune/ - Vývojový deník:
https://www.iconicxp.games/journal/ - Itch.io:
https://iconicxpgames.itch.io/hearth-and-fortune

## Stav projektu

Projekt je uzavřená alpha. Existují samostatné vývojové větve Unity a
Unreal Engine 5. Nejde o volně dostupnou veřejnou demoverzi. Vývojář
výslovně odděluje editorové záběry, zabalené QA buildy a běžné hraní.

## Krajina

-   Vývojář uvádí heightmap footprint přibližně 39,2 čtverečních mílí,
    tedy zhruba 102 km².
-   Tato plocha zahrnuje i nepřístupné části; není to potvrzená hratelná
    plocha.
-   Terén obsahuje plánované lesy, sníh, louky, prérie, skály, mokřady a
    pobřeží.
-   Vývojář uvádí, že část prostředí byla v některých kontrolních bodech
    pouze barevně namalovaným terénem, nikoli hotovými lesy, cestami,
    vesnicemi a rostlinami.

## Tráva a vegetace

Veřejný devlog k tester buildu L uvádí: - hustou trávu a rostliny
přibližně do 80 m; - vzdálené svahy barevně sladěné s vegetací; - měření
holé půdy na 81 místech; - u kontrolovaných travnatých, lesních,
mokřadních a prérijních míst byla holá půda pod 2 %; - pět úrovní
Vegetation: Auto, Low, Medium, High, Ultra.

Pozdější vývojový zápis popisuje detailní kontrolu mezer v trávě. Autor
použil kontrastní barvu podkladu a následně hloubkovou kontrolu. Vybrané
detailní vzorky měly méně než 1 % odkryté půdy, ale autor výslovně
upozorňuje, že šlo o kontrolované detailní záběry, nikoli o měření celé
mapy nebo porovnání identických kamer.

## Výkon

Veřejný tester devlog uvádí přibližně 60 FPS při 720p na Ultra na
výkonné grafické kartě. Výkon klesá při vyšším rozlišení. Jde o údaj z
vývojářského testování, nikoli nezávislý benchmark a nikoli výsledek na
mobilním zařízení.

## Streamování a navigace

Vývojový deník uvádí, že větší svět nebyl uznán za funkční pouze podle
velikosti heightmapy. Autoři požadují důkazy průchodu světem,
streamování, navigace, ukládání a výkonu. Objevila se také chyba, kdy
NPC plánovala cestu za hranici právě načtené oblasti, ale cesta v běžné
hře nebyla dostupná.

## Použitelné poučení

-   Měřit pokrytí vegetací na pravidelných vzorcích, ne pouze podle
    jednoho hezkého screenshotu.
-   Oddělit kvalitu vegetace od celkového grafického nastavení.
-   Vzdálené svahy barevně sladit s vegetací, aby při cullingu
    nevznikaly holé šedé plochy.
-   Testovat navigaci NPC společně se streamováním, ne pouze v editoru.
-   Velikost heightmapy není totéž jako velikost funkčního světa.

# 4. Latticefolk: nejzajímavější otevřená technická architektura

**Odkazy** - GitHub: https://github.com/ranzevor/Latticefolk - README:
https://github.com/ranzevor/Latticefolk/blob/main/README.md - Fyzika:
https://github.com/ranzevor/Latticefolk/blob/main/docs/physics.md -
Prezentace prostředí:
https://github.com/ranzevor/Latticefolk/blob/main/docs/environment-presentation.md -
Persistence:
https://github.com/ranzevor/Latticefolk/blob/main/docs/persistence.md

## Technologie

-   Three.js r180.
-   TypeScript 5.9.
-   Node.js 20+.
-   SQLite pro persistentní svět.
-   Quaternius CC0 assety, zejména low-poly styl.
-   První osoba a oddělený God View.

Nejde o fotorealistický KCD klon. Je to především technický experiment s
živým světem a streamováním.

## Chunk streaming: coarse ↔ fine

Nejdůležitější architektonický princip: - V blízkém aktivním prostoru se
materializují konkrétní NPC, budovy, zvířata a objekty. - Vzdálené
chunky drží agregovaný stav populace, zdrojů, ekologie a prosperity. -
Při přiblížení se z agregovaného stavu vytvoří konkrétní reprezentativní
entity. - Při odchodu se důsledky detailní simulace složí zpět do
hrubého stavu. - Aktivní vykreslovaná oblast je omezená na konečné okno
chunků. - Historie prozkoumaných oblastí zůstává uložená. - Chunk →
Region → World strategické vrstvy pracují v různých, pomalejších
intervalech.

Tím se řeší zásadní problém: celý svět může existovat a měnit se, aniž
by všechny objekty musely být současně vykreslené a simulované v plném
detailu.

## Fyzika a kolize

Veřejná dokumentace popisuje samostatnou FinePhysicsAuthority: -
statické kolizní AABB; - dveře s deterministickým otevřeným/zavřeným
stavem; - kruhové kinematické kolize hráče, NPC a zvířat; - sub-stepping
proti tunnelingu při velkém kroku; - oddělené řešení os, aby postava
mohla klouzat podél zdi; - dynamické kolize postava--postava; -
neblokující interakční triggery; - segmentové a swept-circle dotazy; -
registrace a čištění kolizí po chunkech; - terénní kontakt, omezení
sklonu a výškového schodu.

Dokumentace zároveň přiznává, co zatím hotové není: obecné rigid body,
skládání objektů, některé projektilové a kontaktní systémy a kompletní
fyzikální interakce dveří.

## Vizuální prezentace

Dokumentace řeší konkrétní chyby: - stromy byly příliš malé; nová
kalibrace používá zdrojové výšky přibližně 7,0 / 7,4 / 8,4 m pro tři
typy; - kotva stromu se umisťuje na bázi kmene, ne doprostřed celé
koruny; - kolize stromu odpovídá základně kmene; - animované postavy
mají korekci podle skutečných chodidel, nikoli podle hrubého
kontejnerového Y; - sluneční stínová kamera sleduje fokus
hráče/pozorovatele; - používá stínovou mapu 2048², rozsah pro první
osobu s polovičním rozměrem 24 m a pro God View 32--96 m; - texel
snapping stabilizuje pohyb stínů; - materiály plodin byly opraveny z
chybné metalness hodnoty 1 na 0, bez změny geometrie.

Pozor: tyto parametry jsou popsané pro konkrétní Three.js projekt a
nelze je bez měření přenést do Godotu.

## AI a výkon

-   Deterministická simulace je autoritou pro pohyb, inventář,
    ekonomiku, vztahy, potřeby a fyziku.
-   AI poskytuje záměr, nikoli pravdu o fyzickém výsledku.
-   Vzdálené chunkové rozhodování se dávkuje.
-   K dispozici je cache, confidence gating a rozpočty volání a tokenů.
-   Pro vzdálené NPC se zkracují vstupní informace a používá se
    pomalejší agregovaná simulace.
-   Projekt má deterministické testy a browser E2E testy, které skutečně
    vstupují do Three.js světa, pohybují hráčem a pořizují
    screenshoty/traces.

## Co je pro nás nejcennější

Především oddělení: 1. světového stavu; 2. detailní lokální simulace; 3.
vzdálené agregované simulace; 4. vykreslování; 5. fyzikální autority; 6.
rozhodovací AI.

Toto je velmi dobrý vzor pro architekturu Havrana/Puchartu. Grafická
kvalita současného Latticefolk je ale low-poly a není důkazem
fotorealismu.

# 5. The End of History: UE5 a simulace společnosti

**Odkazy** - Steam:
https://store.steampowered.com/app/2953520/The_End_of_History/ - Web:
https://end-of-history.worldmap-game.com/en/ - Press kit:
https://end-of-history.worldmap-game.com/en/presskit/

## Stav a technologie

-   Autor Tatamibeya, sólový nezávislý vývojář.
-   Unreal Engine 5.
-   Early Access vydán 10. prosince 2025.
-   Středověký sandbox se společností NPC, politikou, válkami a osobními
    příběhy.

## HW požadavky

Steam uvádí: - minimum: Core i5-9400, 8 GB RAM, GTX 1050 Ti, DirectX
12; - doporučeno: 16 GB RAM a RTX 3070.

Steam Deck vyžaduje ruční nastavení grafiky, aby hra dosahovala
přijatelného výkonu. To je důležité upozornění: UE5 samo o sobě
nezaručuje mobilní výkon.

## Co není veřejně dostatečně popsáno

-   konkrétní LOD pipeline;
-   Nanite/Lumen konfigurace;
-   world partition a streaming nastavení;
-   počet NPC a přesná cena simulace;
-   draw calls, GPU/CPU frametimes a paměťové profily.

Projekt je cennější jako příklad toho, jak sólový vývojář může vytvořit
rozsáhlou simulaci společnosti v UE5, nikoli jako zdroj ověřeného
mobilního renderovacího receptu.

# 6. Iberia Medieval: terén, geologie a hydrologie

**Odkaz:**
https://www.reddit.com/r/SoloDevelopment/comments/1xfvidh/im_building_a_medieval_strategy_game_solo_and_i/

Autor zveřejnil výstup procedurálního generátoru: - 7 651 hexových
oblastí; - seed 42094; - výšky terénu; - odtokové sítě; - povodí a
uzavřené pánve; - geologické materiály a zvětrávání; - ukázka uzavřené
pánve s povodím 1 699 hexů a přelivovou výškou 83 m.

Autor výslovně říká, že nejde o finální grafiku a zatím není hotová
hratelná hra. Vegetace, zvířata, lidé, osady, ekonomika a politika jsou
dlouhodobý plán.

**Použitelné poučení:** nejdřív fyzicky správná krajina, voda a
geologie; až potom vegetace, sídla a ekonomika. To je zvlášť vhodné pro
Puchart, kde má být terén založený na skutečné lokalitě.

# 7. Brunnfeld: ekonomická simulace, nikoli 3D svět

**Odkaz:** https://github.com/marcopatzelt/brunnfeld-agentic-world

## Co projekt skutečně dělá

-   TypeScript a Node.js.
-   Vesnická ekonomika s 22 lokacemi.
-   Deklarovaný rozsah až 1 000 LLM agentů v pěti vesnicích.
-   Systém výroby, obchodu, hladu, nástrojů, počasí, dluhů a správy
    vesnice.
-   Viewer je 2D/pixel-art Canvas, nikoli 3D prostředí.

## Výkonnostní údaje

README uvádí orientační délky simulačního ticku: - Classic režim: 20
agentů 8--15 s, 100 agentů 15--30 s, 500 agentů 30--60 s. - Harness
režim: průměrně 5 volání na agenta; 20 agentů 40--90 s, 100 agentů
60--120 s, 500+ agentů 5--15 minut.

To jsou časy simulace a LLM volání, ne FPS vykreslování.

## Optimalizace

-   Paralelní zpracování různých lokací.
-   Sekvenční zpracování agentů na stejné lokaci, aby si předávali
    konverzaci.
-   Batching agentů.
-   Rozdělení promptu na statickou a dynamickou část kvůli cache.
-   Lokální LLM backend přes kompatibilní API.
-   Nižší počet volání v Classic režimu.

**Použitelné poučení:** ekonomiku a logiku NPC lze simulovat nezávisle
na grafice. Pro Havrana by to mohl být samostatný modul, který běží i
tehdy, když hráč danou vesnici nevidí.

# 8. AI Civilization Simulation: konkrétní 2D render optimalizace

**Odkaz:** https://github.com/DMONINK/Live-Simulation

Projekt je 2D simulace v PixiJS, nikoli 3D hra.

## Svět

-   Procedurální mapa 200×200 polí.
-   Perlin noise pro výšku a vlhkost.
-   Biomy, řeky, lesy, vesnice, cesty a surovinové uzly.
-   40+ NPC jako výchozí nastavení; větší počet je konfigurovatelný.

## Popsané optimalizace

  -----------------------------------------------------------------------
  Technika                            Implementace / účel
  ----------------------------------- -----------------------------------
  Chunk baking                        každý chunk 16×16 terénních polí
                                      vykreslen jednou do RenderTexture

  Spatial hash                        prostorové dotazy místo procházení
                                      všech entit

  Update throttling                   zvířata se aktualizují každý druhý
                                      snímek

  Visibility culling                  vykreslují se pouze viditelné
                                      chunky

  AI rate limit                       nejvýše jedno API volání za 6
                                      sekund globálně

  Memory decay                        odstraňování starých a nevýznamných
                                      vzpomínek

  Cleanup                             mrtvé entity se odstraňují z
                                      prostorové struktury
  -----------------------------------------------------------------------

README doporučuje při pomalém FPS snížit počet NPC, vypnout jmenné
štítky a upravit prostorovou hash mřížku. Uvádí také, že při velkém
počtu NPC lze zvážit Web Workers.

**Použitelné poučení:** chunk baking a spatial hash jsou přenositelné
principy, ale konkrétní 2D implementace není hotový 3D recept.

# 9. Etherworld: Unity prototyp

**Odkaz:** https://github.com/LeonardotNEO/Etherworld

README popisuje: - procedurálně generovanou mapu; - stromy, rostliny,
města, dungeony a jeskyně; - sběr surovin, crafting a inventáře; - NPC,
najímání pracovníků a ekonomiku; - boj se zvířaty, monstry a lidskými
NPC; - Unity build.

README nepopisuje konkrétní techniky LOD, occlusion culling, GPU
instancing, streamování, paměťové limity ani benchmarky. Proto ho nelze
považovat za zdroj ověřených optimalizačních postupů.

# 10. Bellwright: co se dá naučit z větší hry

**Odkazy** - Oficiální stránka/patch:
https://patchbot.io/games/bellwright/articles/483-summer-update-and-console-release -
SteamDB patch notes: https://steamdb.info/patchnotes/23628106/ - Starší
vizuální patch: https://steamdb.info/patchnotes/15494308/

Bellwright není hobby projekt, ale jeho optimalizační zkušenosti jsou
velmi relevantní.

## Doložené kroky

-   Přechod na Unreal Engine 5.7.
-   Aktualizace DLSS, FSR a XeSS.
-   Velký optimalizační průchod.
-   Vývojáři výslovně uvádějí odstranění pozdních micro-freezes ve
    velkých osadách.
-   Starší patche řešily FSR, sharpening, nastavení global illumination,
    pořadí grafických voleb podle dopadu na výkon, stromy, malé
    rostliny, textury a stutter při změně nastavení.
-   Pozdější patche uvádějí snížení CPU nákladů minimapy a pohybu
    postav.
-   Počasí a kouřové efekty dostaly samostatné optimalizace.

## Důležitý poznatek

Pokud snížení grafických detailů nepomůže FPS v osadě, problém může být
na CPU straně: NPC, pohyb, simulace, tickování a správa objektů. Reddit
hráči hlásili pokles FPS ve vlastních osadách, i když jinde měli 60+
FPS. To není laboratorní důkaz, ale potvrzuje rozdíl mezi GPU a CPU
bottleneckem.

# 11. Čínský projekt Liangshan Deep: opatrně s důvěryhodností

**Odkaz:** https://tsight.io/articles/8894420

Článek popisuje mapu oblasti Liangshan v Číně: - satelitní snímky; - DEM
výšková data; - QGIS; - export heightmap/mesh; - LOD; - occlusion
culling; - kompresi dat.

**Zásadní výhrada:** stránka sama označuje text jako „AI GENERATED
INTELLIGENCE" a uvádí model Gemini 2.0 Flash. Nejde tedy o ověřený přímý
vývojářský deník. Použité techniky jsou běžné a smysluplné, ale samotnou
existenci popisovaného projektu a skutečnou implementaci nelze z tohoto
zdroje potvrdit. Nezapočítávám jej jako ověřený hobby projekt.

# 12. Srovnání technik

  --------------------------------------------------------------------------
  Technika          Kde je doložena   Přínos            Co ověřit při
                                                        převzetí
  ----------------- ----------------- ----------------- --------------------
  Terrain LOD       Liangshan článek, méně vrcholů a    přechody LOD,
                    obecný princip    menší render      praskliny, normály
                                      náklady           

  Vegetation        Last Eagle,       menší cena trávy, pop-in, holé svahy,
  distance /        Hearth & Fortune  méně objektů      barva vzdálené
  culling                                               krajiny

  Grafické profily  Hearth & Fortune  škálování pro     skutečná RAM/VRAM a
  vegetace                            různé počítače    FPS

  Crowd animation   Last Eagle        vzdálené NPC      přepínání režimu a
  LOD                                 levněji animovat  viditelné trhání

  FSR 2             Last Eagle        nižší interní     ostrost, ghosting,
                                      rozlišení a       podpora cílového GPU
                                      následné          
                                      upscaling         

  FXAA/SMAA/TAA     Last Eagle        volba kompromisu  výkon a rozmazání
                                      mezi ostrostí a   pohybu
                                      stabilitou hran   

  Chunk baking      AI Civilization   opakované         paměť RenderTexture,
                                      vykreslení        aktualizace
                                      statického terénu změněných chunků
                                      levněji           

  Spatial hash      AI Civilization   rychlejší         velikost buněk a
                                      prostorové dotazy pohyb entit

  Coarse/fine       Latticefolk       detail jen v      zachování identity,
  streaming                           okolí hráče,      zdrojů a následků
                                      zbytek světa      
                                      agregovaně        

  Chunk-scoped      Latticefolk       kolize jen v      správné
  physics                             aktivních         načtení/odstranění
                                      oblastech         kolizí

  CPU optimalizace  Bellwright,       méně              CPU profiling, počet
  NPC               Brunnfeld         micro-stutter a   aktivních NPC
                                      kratší tick       

  DEM + hydrologie  Iberia Medieval   přírodně logická  přesnost dat a herní
                                      krajina a voda    škálování
  --------------------------------------------------------------------------

# 13. Doporučení pro Havrana a Puchart

Nejlepší není kopírovat jeden projekt. Je vhodné sestavit technologický
základ z ověřených dílčích postupů.

## A. Krajina a vzdálené vykreslování

1.  Detailní terrain mesh pouze poblíž hráče.
2.  Nižší LOD pro vzdálené kopce.
3.  Vegetace s více vzdálenostními úrovněmi.
4.  Distant foliage barevně sladit s terénem.
5.  Culling stromů nesmí vytvořit prázdný šedý horizont.
6.  Testovat z několika výšek kamery a při pohybu, nikoli jen statickým
    screenshotem.

## B. Tráva, keře a stromy

1.  Oddělit trávu, keře a stromy do různých rozpočtů.
2.  Trávu nechat hustou v okolí hráče a postupně zjednodušovat.
3.  Vzdálenou trávu reprezentovat levnější geometrií nebo vhodnou
    texturou.
4.  Omezit dynamické stíny na drobných rostlinách.
5.  Měřit CPU i GPU cenu vegetace samostatně.
6.  Otestovat pohyb kamery nízko nad trávou, aby listy a stébla
    nezakrývaly obraz.

## C. NPC a život ve světě

1.  Blízké NPC: plná navigace, kolize a animace.
2.  Střední vzdálenost: zjednodušené animace a méně časté rozhodování.
3.  Daleko: agregovaná simulace práce, potřeb a zásob.
4.  Při přiblížení materializovat NPC se zachováním identity a
    inventáře.
5.  Při odchodu složit výsledky zpět do regionálního stavu.
6.  AI nesmí rozhodovat o fyzikálních výsledcích, jako je průchod zdí
    nebo zásah nástrojem.

## D. Fyzika a interakce

-   Jedna autorita pro kolize.
-   Kolizní geometrie oddělená od render modelu.
-   Chunk-scoped registrace a odstraňování kolizí.
-   Sub-stepping při pohybu.
-   Sklon terénu a výškové schody jako pravidla pohybu.
-   Interakce ověřovat nejen raycastem, ale také dosahem/triggerem a
    překážkami.

## E. Profilování na Xiaomi Pad 8

Vzhledem k omezené volné RAM nesmí být žádný projekt přijat jen podle
toho, že v editoru běží plynule.

Pro každou scénu zaznamenávat: - průměrné FPS; - 1% low a frame time v
ms; - CPU frame time; - GPU frame time; - využití RAM a VRAM, pokud je
dostupné; - počet vykreslovaných objektů; - počet draw calls; - počet
aktivních NPC; - počet aktivních kolizních objektů; - vzdálenost
vegetace; - rozlišení a grafický profil.

Testovat samostatně: 1. prázdnou krajinu; 2. les s hustou trávou; 3.
vesnici s budovami; 4. vesnici s NPC; 5. interiér; 6. rychlý pohyb a
načítání nových chunků; 7. desetiminutové stání a opakovanou trasu.

Cílové 30 FPS znamená frame budget 33,3 ms. Pro stabilitu je vhodné mít
rezervu, ne být trvale na hraně.

------------------------------------------------------------------------

# 14. Co je potřeba ještě ověřit

Veřejné zdroje zatím nedávají přesné odpovědi na: - skutečnou RAM/VRAM
spotřebu The Last Eagle; - konkrétní GPU instancing a LOD implementaci u
The Last Eagle; - přesný render pipeline Hearth & Fortune; - podrobné
Nanite/Lumen/World Partition nastavení The End of History; - nezávislé
benchmarky Latticefolk; - mobilní výkon kteréhokoli z těchto projektů na
Xiaomi Pad 8.

To nejsou mezery, které by bylo správné vyplnit odhadem. Je nutné
stáhnout zdrojové kódy, pokud jsou veřejné, nebo získat přístup k
buildům a změřit je.

# 15. Zdroje

## Primární zdroje

-   The Last Eagle, Reddit autora:
    https://www.reddit.com/r/aigamedev/comments/1xb2oep/6_months_of_solo_parttime_dev_on_my_first_game_a/
-   The Last Eagle, devlog:
    https://dometgames.itch.io/the-last-eagle/devlog
-   Hearth & Fortune, oficiální vývojový deník:
    https://www.iconicxp.games/journal/
-   Hearth & Fortune, hra:
    https://www.iconicxp.games/games/hearth-and-fortune/
-   Latticefolk, GitHub: https://github.com/ranzevor/Latticefolk
-   Latticefolk, fyzika:
    https://github.com/ranzevor/Latticefolk/blob/main/docs/physics.md
-   Latticefolk, prezentace prostředí:
    https://github.com/ranzevor/Latticefolk/blob/main/docs/environment-presentation.md
-   Brunnfeld, GitHub:
    https://github.com/marcopatzelt/brunnfeld-agentic-world
-   AI Civilization Simulation, GitHub:
    https://github.com/DMONINK/Live-Simulation
-   Etherworld, GitHub: https://github.com/LeonardotNEO/Etherworld
-   Iberia Medieval, Reddit:
    https://www.reddit.com/r/SoloDevelopment/comments/1xfvidh/im_building_a_medieval_strategy_game_solo_and_i/
-   The End of History, Steam:
    https://store.steampowered.com/app/2953520/The_End_of_History/
-   Bellwright, letní aktualizace:
    https://patchbot.io/games/bellwright/articles/483-summer-update-and-console-release
-   Bellwright, grafické a výkonové změny:
    https://steamdb.info/patchnotes/15494308/
-   Liangshan Deep, čínský článek: https://tsight.io/articles/8894420

## Závěrečný závěr

Největší technický přínos pro vlastní historický 3D svět mají: 1.
**Latticefolk** pro architekturu chunků, coarse/fine simulaci, fyziku a
persistenci. 2. **The Last Eagle** pro Godot, vegetaci, animace davu,
kameru, stíny a grafické volby. 3. **Hearth & Fortune** pro měření
vegetace, grafické profily a oddělení editorových důkazů od skutečného
hraní. 4. **Bellwright** pro poučení z CPU bottlenecků a optimalizace
velkých osad. 5. **Iberia Medieval** pro přírodně správnou krajinu, vodu
a geologii.

Pro Havrana a Puchart bych nejdříve převzal architektonické principy
Latticefolk a renderovací/vegetation postupy The Last Eagle. Nic z
dostupných zdrojů ale zatím neprokazuje, že některý z těchto projektů
běží s požadovanou kvalitou na Android tabletu s přibližně 2 GB volné
RAM.

---
## Doplnění Míša 12. 11.
- Sandpiper Point – NPC scheduling: https://playsandpiperpoint.com/devdiary-npc-scheduling.html – NPC přecházejí mezi
  scénami; mimo načtenou oblast nemusí existovat model, poloha a činnost se dopočítají podle herního času, po návratu
  hráče se postava znovu vytvoří. **Použito:** `lide.gd _daleko_krok` (postava za dosahem jde po cestě rychlostí chůze,
  bez animace), mimo záběr bez animace a modifikátorů; The Last Eagle → jdoucí postava v záběru plná animace.
