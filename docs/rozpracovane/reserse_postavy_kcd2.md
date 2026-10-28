# Rešerše: jak žijí postavy v KCD1/KCD2 a jiných hrách → data pro Odkaz Havrana

Rešerše z 28. 10. 2026 pro krok 2 postav (`pravidla/svet/postavy.json`, `scripts/lide.gd`). Ke každému tvrzení je
odkaz. Co se dohledat nedalo, je označeno *odhad*. Kde v textu stojí „[Z12]“, jde o zdroj č. 12 v seznamu na konci.

**Stav v repu, se kterým rešerše počítá (přečteno, nic neměněno):**
- `pravidla/svet/postavy.json` už obsahuje krok 2 v první podobě. Jsou v něm `role` → `rozvrh` (bloky `od` hodiny →
  `cinnost` + `kde`), `mista` jako záznamy, `cinnosti` (klipy a `obmena_s`), `obyvatele` (domov a práce), `graf`
  (síť chůze z os cest), `hlava` (LookAt: limit 70°, krk 35°, prodleva 0,45 s) a LOD animací 25/45/70 m s 10 fps.
  Návrh v kap. 8 proto tento formát **rozšiřuje** a nevymýšlí nový.
- Herní čas: `scripts/daylight.gd` `RATE = 24/5400`, takže **1 herní den = 90 skutečných minut** a
  **1 herní minuta = 3,75 s**. Všechny délky v herních minutách níže jsou přepočtené tímto poměrem.
- Klipy: `modely/postavy/anim/UAL1.glb` a `UAL2.glb` (Quaternius UAL 1 a 2, verze Standard, CC0). Seznam klipů
  v kap. 3 je vyčtený přímo z těchto souborů (43 + 43 klipů včetně `A_TPose`) i s délkami.
- Kostra postav má 65 kostí (`root`, `pelvis`, `spine_01–03`, `neck_01`, `Head`, ruce s prsty, `thigh/calf/foot/ball`).
  **Oční kosti nemá**, pohyb očí tedy jde jen přes shader hlavy (`shaders/postava_hlava.gdshader`), *odhad*.

---

## 1. Kingdom Come: jak NPC žijí

### 1.1 Co je doložené
- **Každá postava má domov, práci a denní cyklus.** Přednáška Petra Smrčka (Warhorse, AI programátor) na MFF UK
  uvádí jako témata „denní cykly, práce a domovy NPC“, chytré objekty (dveře, kamna, židle, instrukce interakce)
  a „smart areas“ (např. krčma). Zmiňuje také **asi 600 současně aktivních NPC** v KCD1 [Z1].
  Plné znění slajdů se stáhnout nepodařilo (server vrací HTML ochranu proti robotům), čísla jsou z výpisu
  vyhledávače.
- **KCD2 má skoro 2 400 trvalých NPC s denním rozvrhem, který běží pořád.** Rozvrhy jsou kvůli historické věrnosti
  složité, výkonově náročné a vyžadují hodně ručního umísťování. Rozvrhy se kříží s questy (Martin Labuť,
  GDS Praha 2024, „NPC Daycycles in KCD2“) [Z2].
- **Asi polovina NPC KCD2 je v jednom městě (Kutná Hora). NPC žijí a chodí svými cestami, ať s nimi hráč jedná,
  nebo ne** (GDC, „Supporting Thousands of NPCs in KCD & KCD2“) [Z3][Z4].
- **Architektura v KCD1:** chování řídí behavior trees rozšířené o proměnné a typy a bohatý systém zpráv mezi NPC.
  Nad tím stojí **Smart Areas**: oblast (např. krčma) obsahuje vše, co NPC v daném místě potřebuje, a koordinuje je.
  Přiděluje volná místa k sezení, vybírá, kdo se porve, a nabízí „behavior tag“ (malý behavior tree) podle
  vlastností NPC, například „pozvi všechny na pivo“ jen pro bohaté. Má události OnAdopt, OnDrop, OnEnter a OnExit.
  Hlavní účel je „simulace rutinních denních činností (práce, spánek, jídlo, odpočinek)“. Nové místo (nová krčma)
  jde přidat bez změny kódu NPC. Questy a boj mají přednost a smart area je nesmí narušit
  (Černý, Plch, Marko, Ondráček, Brom 2014; autoři z Warhorse) [Z5].
- **Behavior objects:** rozšíření smart objects ve stylu OOP, implementované a vyhodnocené přímo v KCD [Z6].
- **KCD2: GOAP + modulární behavior trees.** Stav každého NPC je popsaný daty. MBT určí žádaný stav a plánovač
  (GOAP) najde, jak se do něj dostat (Matej Marko, GDC Game AI Summit) [Z7].
- **Den NPC v KCD2:** snídají s ostatními, jdou do práce, nakoupí, večer krčma nebo procházka. Rozvrh přeruší rvačka
  na ulici, pozdrav s přítelem nebo veřejný trest na pranýři. Po násilí nebo krádeži v okolí rozvrh změní: zůstanou
  doma, nosí zbraň, žádají víc hlídek (Martin Ziegler, lead scripter) [Z8].
- **Noc:** NPC jdou domů, svléknou denní šaty a spí v posteli. Když musí ven, nesou pochodeň nebo lucernu. Na alarm
  reagují útěkem a zamykáním dveří (recenze RPG Codex) [Z9].
- **Krčma a opilost:** NPC, které pije v krčmě, se po pár pivech snáz okrade. Rozvrh tedy ovlivňuje hratelnost [Z10].
- **Reakce na hráče:** NPC hlásí zločiny stráži [Z11]. Vykázání hráče z místnosti stojí podle Viktora Bocana na
  „mnoha propojených systémech“ (přednáška „Invisible Design“) [Z2].
- **Déšť:** KCD na déšť zřejmě nereaguje úkrytem. Hráči hlásí, že NPC v lijáku dál zametají [Z12], a srovnávají to
  s Zaklínačem 3, kde se NPC schovávají pod střechy [Z13]. Obojí jsou jen hráčské postřehy.
- **Kostel:** v klášteře se modlí ve 4 a v 16 h vždy 2 hodiny a účast na mši je povinná (návod k questu
  „V klášteře“) [Z14]. Kodex hry uvádí, že mše byla latinsky a kázání bylo oddělené od mše [Z15].
- **Skald** je interní nástroj Warhorse na **dialogy, cutscény a questy**. Zapisuje i to, jaké animace a nálady
  postavy v dialogu používají. **Není to AI rozvrhů** [Z16][Z17].
- **LOD AI:** podle hráče, který zprostředkovává livestream Warhorse, se pro KCD1 zaváděl „nějaký LOD AI“
  (informace z druhé ruky) [Z18]. Smart Areas popisují, že co hráč nevidí, se jen simuluje [Z19].

### 1.2 Jak NPC vybírá činnost (shrnutí pro nás)
1. **Rozvrh** (denní cyklus podle role) určí blok, např. „práce 6–12“.
2. Blok odkazuje na **místo / smart area** (pracoviště, krčma, domov).
3. Smart area přidělí **konkrétní slot**: židli, kovadlinu nebo špalek. Je to záznam s animacemi
   (vstup → smyčka → výstup). Kdo už slot drží, ten ho nepustí, a tak se dva nepotkají na jedné židli [Z5].
4. **Přerušení** (událost, hráč, déšť) mají přednost a po skončení se NPC vrací do bloku [Z8].

### 1.3 Typický den vesničana (KCD + historie → náš návrh)
| Blok | Herní čas | Doklad |
|---|---|---|
| Vstávání, ranní práce u domu (dobytek, voda) | 4:30–6:00 | práce od úsvitu, krmení dobytka a zalévání [Z20][Z21]; čas *odhad* |
| Snídaně (doma, skrytá) | 6:00–6:30 | „snídají s ostatními“ [Z8]; čas *odhad* |
| Práce (pole, zahrada, řemeslo, lom) | 6:30–11:30 | [Z8][Z9] |
| Oběd a polední odpočinek | 11:30–13:00 | polední odpočinek doložen jen anekdoticky [Z20], *odhad* |
| Práce | 13:00–17:30 | *odhad* |
| Večeře, pak hovor na návsi nebo krčma (muži) | 17:30–20:00 | krčma a hazard večer [Z9][Z8] |
| Cesta domů s lucernou za tmy, spánek | 20:00–4:30 | [Z9]; v zimě dřív, protože den je kratší [Z20] |
| Neděle: mše dopoledne, odpoledne volno | ne 8–10 | *odhad* (účast povinná doložena v klášteře [Z14]) |

---

## 2. Činnosti podle profese (vesnice a tvrz, Čechy kolem 1393)

Délky jsou **herní minuty** a v závorce **skutečné sekundy** (×3,75 s). Délku jednoho bloku nezná žádný zdroj,
**všechny délky jsou *odhad*** odvozený z toho, že činnost musí jít vidět aspoň minutu skutečného času a nesmí
přeskakovat po pár vteřinách. Fórum KCD si stěžovalo, že rozvrhy působí „uspěchaně“ a mění se moc často [Z22].
Sloupec „UAL“ ukazuje, čím to jde zahrát z klipů, které máme. **✗** znamená, že klip chybí (viz kap. 3).

| Činnost | Kdo | Místo (záznam) | Délka (herní min) | UAL klip | Poznámka |
|---|---|---|---|---|---|
| Štípání dřeva | čeledín, sedlák | `u_spalku` (model `spalek_stipani`) | 20–40 (75–150 s) | `TreeChopping_Loop` (0,96 s) | sekera v pravé ruce; vstup ✗ (stačí `PickUp_Table`) |
| Nošení vody | děvečka, selka | `u_studny` → `dvere` / `chlev` | 2–5 na cestu, 3–6 cest | `Interact` + `Walk_Carry_Loop` | `Walk_Carry` drží břemeno před sebou; vědra po stranách ✗ |
| Navíjení vědra u studny | děvečka | `u_studny` | 2–3 | `Idle_Rail_Loop` / `Interact` | navíjení rumpálem ✗ |
| Pletí a okopávání záhonu | selka, děvečka | `zahrada` | 30–90 | `Farm_Harvest`, `Farm_PlantSeed`, `Farm_Watering` | motyka ✗ (blízko je `Fixing_Kneeling`) |
| Krmení drůbeže a dobytka | selka, čeledín | `dvorek` / `chlev` | 10–20 | `Farm_PlantSeed` (rozhazování), `Interact` | |
| Kidání hnoje, vidle | čeledín | `chlev` | 20–40 | ✗ (náhrada `TreeChopping_Loop` je hrubá) | |
| Mletí (vodní mlýn) | mlynář | `mlyn_slozeni` (u kamene), `mlyn_dvur` | 30–60 v kole | `Interact`, `Idle_FoldArms_Loop`, `Walk_Carry_Loop` (pytle) | pytel na rameni ✗ |
| Mletí (větrný mlýn) | mlynář | `vetrak_schody`, `vetrak_plac` | 30–60 | totéž + `Push_Loop` (otáčení mlýna ojí) | sloupový mlýn se točí za vítr, `Push_Loop` sedí |
| Práce v lomu (klín, palice) | lamač | `lom_stena_N` | 30–60 | `TreeChopping_Loop`, `Fixing_Kneeling` | úder palicí shora ✗ |
| Opracování kamene | kameník | `lom_spalek` | 30–60 | `Fixing_Kneeling` | |
| Kovář u výhně | kovář | `kovarna_kovadlina`, `kovarna_vyhen` | 10–20 u kovadliny, 2–5 u výhně | `TreeChopping_Loop` (úder), `Interact` | kladivo na kovadlinu a měch ✗ |
| Stráž na obchůzce | strážný | `obchuzka` (body po hradbě nebo nádvoří) | 3–8 na úsek, stání 2–5 | `Walk_Formal_Loop`, `Idle_Shield_Loop`, `Idle_Rail_Loop` | v noci `Idle_Torch_Loop` / `Idle_Lantern_Loop` |
| Stráž u brány | strážný | `brana` | 60–120 | `Sword_Idle`, `Idle_Shield_Loop`, `Idle_FoldArms_Loop` | |
| Posezení na lavici | všichni | `lavice_N` (slot 1–3) | 15–40 | `Sitting_Enter` → `Sitting_Idle_Loop` / `Sitting_Talking_Loop` → `Sitting_Exit` | celý řetězec je k dispozici |
| Hovor ve dvojici | všichni | `naves_N`, `u_studny` | 5–15 | `Idle_Talking_Loop`, `Yes`, `Idle_No_Loop`, `Idle_FoldArms_Loop` | navzájem natočení |
| Hostinský | hostinský | `hostinec_pult`, `hostinec_sklep`, `hostinec_stoly` | pult 20–40, roznášení 2–4 na stůl | `Idle_Loop`, `PickUp_Table`, `Walk_Carry_Loop`, `Consume` | čepování ✗ |
| Jídlo a pití | všichni | `stul_N` | 15–30 | `Sitting_Idle_Loop` + `Consume` | |
| Modlitba, mše | všichni | `kostel_lavice` / `kostel_kleceni` | 60–120 | `Fixing_Kneeling` (kleknutí), `Sitting_Idle_Loop` | sepnuté ruce ✗ |
| Spánek | všichni | `domov` (skrytý) | 7–9 h | `LayToIdle` (vstávání z lehu) | uvnitř se nekreslí (dnešní `skryty: true`) |

---

## 3. Animace: co je potřeba a co dává Quaternius UAL

### 3.1 Co máme (vyčteno ze souborů v repu, verze Standard, CC0 [Z23])
**UAL1:** `Idle_Loop` 2,50 s, `Idle_Talking_Loop` 2,92, `Idle_Torch_Loop` 1,25, `Walk_Loop` 1,33,
`Walk_Formal_Loop` 1,33, `Jog_Fwd_Loop` 0,92, `Sprint_Loop` 0,67, `Crouch_Fwd_Loop` 2,00, `Crouch_Idle_Loop` 2,92,
`Sitting_Enter` 1,29, `Sitting_Idle_Loop` 1,67, `Sitting_Talking_Loop` 2,92, `Sitting_Exit` 1,00,
`Fixing_Kneeling` 5,17, `Interact` 2,00, `PickUp_Table` 0,83, `Push_Loop` 2,67, `Driving_Loop` 1,67,
`Dance_Loop` 1,00, `Jump_Start/Loop/Land`, `Roll`, `Hit_Chest`, `Hit_Head`, `Death01`, `Punch_Jab/Cross`,
`Sword_Idle`, `Sword_Attack`, `Swim_Idle/Fwd_Loop`, `Spell_Simple_*` (4×), `Pistol_*` (6×), `A_TPose`.

**UAL2:** `Walk_Carry_Loop` 2,00 s, `TreeChopping_Loop` 0,96, `Farm_Harvest` 2,50, `Farm_PlantSeed` 2,75,
`Farm_Watering` 3,79, `Consume` 1,33, `Chest_Open` 1,33, `Idle_FoldArms_Loop` 2,50, `Idle_Lantern_Loop` 2,50,
`Idle_No_Loop` 2,50, `Yes` 2,50, `Idle_Rail_Loop` 2,50, `Idle_Rail_Call` 2,50, `Idle_TalkingPhone_Loop` 2,92,
`LayToIdle` 1,50, `ClimbUp_1m` 0,67, `OverhandThrow` 1,33, `Hit_Knockback`, `Idle_Shield_Loop`,
`Idle_Shield_Break`, `Shield_Dash/OneShot`, `Sword_Block`, `Sword_Dash`, `Sword_Regular_A/B/C(+_Rec)`,
`Sword_Regular_Combo`, `Sword_Heavy_Combo`, `Melee_Hook(+_Rec)`, `NinjaJump_*`, `Slide_*`, `Zombie_*`.

**Placené verze Pro a Source** (UAL1 „120+“, UAL2 „130+“) přidávají podle prodejní stránky lokomoci v 8 směrech,
tlačení, plazení, plavání, sezení, emoce (UAL1) [Z24][Z25] a farmaření, rybaření a idles/emotes (UAL2) [Z26].
Jednotlivá jména klipů placených verzí stránka neuvádí. Popisek obrázku UAL2 Standard uvádí 42 klipů včetně
`WAVE`, ale v našem souboru `UAL2.glb` mávání není. **Pro, zda je v něm otočení na místě a start/stop, je *odhad*,
ověřit v prohlížeči** quaternius.com/animviewer.html. Aktuální verze UAL1 má klipy s root motion i bez [Z24].

### 3.2 Potřeba pro uvěřitelnost × pokrytí
| Potřeba | UAL Standard | Stav |
|---|---|---|
| Chůze pomalá / běžná / svižná | `Walk_Loop`, `Walk_Formal_Loop`, `Jog_Fwd_Loop` + měnit `speed_scale` ±20 % | ✓ (blend space 1D) |
| Chůze s břemenem | `Walk_Carry_Loop` (před tělem) | ◐ pytel na rameni a vědra ✗ |
| Chůze s pochodní / lucernou | jen stoj (`Idle_Torch_Loop`, `Idle_Lantern_Loop`) | ◐ horní polovina přes filtr kostí (kap. 5.4) |
| Rozběh a zastavení | ✗ | prolínání 0,2–0,3 s a zpomalení v kódu (kap. 5.3) |
| Otočení na místě | ✗ | procedurálně: natočení `root` + krok s `Walk_Loop` při rychlosti 0,3 (kap. 5.3) |
| Sednutí / vstání | `Sitting_Enter` / `Sitting_Exit` | ✓ |
| Kleknutí, práce u země | `Fixing_Kneeling` | ✓ |
| Lehnutí / vstání z lehu | `LayToIdle` | ◐ jen vstávání |
| Práce rukama | `Interact`, `PickUp_Table`, `Chest_Open`, `Farm_*`, `TreeChopping_Loop`, `Push_Loop` | ◐ kladivo, motyka, vidle, čepování ✗ |
| Jídlo a pití | `Consume` | ✓ |
| Rozhovor ve dvojici | `Idle_Talking_Loop`, `Sitting_Talking_Loop`, `Yes`, `Idle_No_Loop` | ✓ (natočení k sobě v kódu) |
| Gesta (mávnutí, ukázání, pokrčení ramen) | `Idle_Rail_Call` (volání) | ◐ mávnutí ✗ |
| Pozdrav, úklona | ✗ | look-at + `Yes` jako kývnutí (kap. 5.1) |
| Klidové varianty (fidgets) | `Idle_Loop`, `Idle_FoldArms_Loop`, `Crouch_Idle_Loop` | ◐ přenesení váhy a protažení ✗ |
| Stráž | `Sword_Idle`, `Idle_Shield_Loop`, `Idle_Rail_Loop`, `Walk_Formal_Loop` | ✓ |
| Úlek, útěk | `Hit_Knockback`, `Sprint_Loop` | ✓ |
| Nohy na svahu | (IK, ne klip) | kap. 5.5 |

**Chybějící klipy podle priority:**
1. otočení na místě ±90°/180°;
2. kladivo na kovadlinu;
3. motyka a vidle;
4. pytel na rameni;
5. vědra po stranách;
6. mávnutí a úklona;
7. modlitba vkleče;
8. čepování;
9. zametání.

Zdroje: Pro/Source UAL (*odhad*, že v něm část je), nebo vlastní úprava v Blenderu z existujících klipů.
Například kladivo jde udělat z `TreeChopping_Loop` s menším rozmachem a modlitba z `Fixing_Kneeling` se sepnutýma
rukama přes `CopyTransform`, *odhad*.

---

## 4. Jak to dělají jiné hry (co převzít a proč)

| Hra | Jak to dělá | Co převzít a proč |
|---|---|---|
| **KCD1/2** | rozvrh → smart area → slot s animací; BT, v KCD2 GOAP+MBT; ~600 / ~2 400 NPC [Z1][Z2][Z5][Z7] | **slot jako záznam s rezervací** a oblast, která sloty přiděluje. Je to přesně náš „záznam v datech“ a nové místo nevyžaduje kód |
| **Zaklínač 3** | *Community* = kdo kde je podle *story phase*; *timetable* = tabulka „co a kdy“; *action point* = waypoint s *job tree* (vstup → smyčka → odchod), kategorie, výběr klipů v pořadí nebo náhodně, ruční předměty, příznaky „Is Lookat Enabled“ a „Can React“, volba „Disable Path Agent“ (u stolu NPC nikdo neodstrčí); příznak „Start In AP“ (postava se objeví rovnou na místě) [Z27][Z28][Z29][Z30] | **job tree vstup/smyčka/výstup + předmět v ruce + příznak look-at a reakce na slotu**. „Start In AP“ = náš LOD: mimo dohled se postava rovnou objeví na místě |
| **Skyrim / Oblivion** | Radiant AI: plný 24h rozvrh z *AI packages*; seznam balíčků se čte shora a první platný vyhrává; jména `STARTxDÉLKA`; *Sandbox* = v okruhu použij volný nábytek a idle markery, jen nevlastněné nebo vlastní [Z31][Z32][Z33][Z34] | **pořadí s prioritou (první platný blok vyhrává)** se hodí na výjimky (déšť, neděle, poplach). **Sandbox** oživí volné chvíle a **vlastnictví slotu** zajistí, že hostinský nesedá k cizímu stolu |
| **Gothic 1/2** | rutina `Rtn_Start_<ID>` složená z volání `TA_*` (od–do hodin, waypoint); rutiny musí pokrýt 24 h; *free points* `FP_STAND_*` blízko waypointu určují přesné místo činnosti [Z35] | **povinnost pokrýt 24 h a validace v testu**. Je to nejjednodušší čitelný formát (čas od–do → činnost → bod) a náš `rozvrh` už tak vypadá |
| **Stardew Valley** | rozvrh je řetězec `čas mapa x y směr animace`, klíče se zkoušejí v pořadí `rain` → den v týdnu → sezóna → výchozí; `a1200` = „být tam ve 12“ (start dopočítá); `GOTO` [Z36] | **varianta „déšť“ jako samostatný klíč rozvrhu a záložní výchozí rozvrh**. Čas příchodu („být tam v“) místo času odchodu se dopočítá z délky cesty po grafu |
| **The Sims** | utility AI: objekty „inzerují“, kolik uspokojí potřebu; postava sečte skóre (potřeby × vzdálenost) a vybere nejlepší [Z37][Z38] | jen pro **volné chvíle** uvnitř bloku (lavice / hovor / studna podle únavy a počasí), ne pro celý den. Bez rozvrhu by vesnice působila chaoticky |
| **RDR2** | každé NPC má vlastní denní rozvrh podle času; ~300 000 animací [Z39][Z40]; u koní se přešlo od jednorázových přechodových klipů k plynulému zrychlování a zpomalování [Z41] | **plynulá změna rychlosti** místo přechodových klipů. Funguje s naší malou knihovnou (blend space podle rychlosti) |
| **Assassin's Creed Unity** | *AI recycling*: rozpočet **40 plných AI a 120 modelů ve vysokém rozlišení** pro scénu s 10 000 NPC; pool vymění nízké a vysoké rozlišení bez všimnutí [Z42][Z43] | **tvrdý rozpočet plných AI a poolování uzlů** (předvytvořené postavy se přesouvají místo vytváření a mazání) |
| **TLOU2** | motion matching pro lokomoci, přesuny, boj na blízko i krytí; vlastní tým systémové animace NPC a ambientní chování [Z44][Z45] | motion matching ne: chce velkou databázi mocapu a výkon CPU na hledání každý snímek [Z46]. Převzít **zásadu vrstev a ambientních chování** |
| **For Honor** (motion matching, Clavet) | každý snímek hledá v celém mocapu nejbližší pózu a přechází na ni [Z46][Z47] | pro tablet a 86 klipů ne, viz výše |
| **Mount & Blade Bannerlord** | ve scénách osad body spawnu s animací a předmětem a podmínky den/noc, obléhání a prosperita [Z48] | **podmínky na místě** (jen ve dne, jen za sucha). Oficiální dokumentaci k „animation points“ se dohledat nepodařilo |
| **Medieval Dynasty** | vesničan má jedno pracoviště, % času mezi úkoly, limit pracovníků na pole; hráči si stěžují, že práci „nevidí“ [Z49] | **kapacita místa** (max. pracovníků) a ponaučení: **práce musí být vidět**, jinak vesnice působí mrtvě |
| **Manor Lords** | rodiny přidělené k budovám, nepřidělené staví [Z50] | **výchozí činnost**: kdo nemá práci, jde na nejbližší neobsazenou (stavba, dříví) |
| **Genshin Impact** | behavior trees pro logiku NPC a NavMesh pro chodce ve městě (GDC 2021, miHoYo) [Z51] | potvrzuje, že i mobilní hra s otevřeným světem používá **BT + navigaci**, ne plánování. Detaily o LOD animací na mobilu se nepodařilo dohledat |

---

## 5. Přirozený pohyb člověka (ne robot, ne zombie)

Všechny vrstvy v pořadí, jak se skládají na kostru. Čísla jsou návrh do `postavy.json`, u každé vrstvy je napsáno,
zda jde na tablet. Hodnoty ve 4.4 se nastavují na uzlech `SkeletonModifier3D` pod `Skeleton3D` a ty se vyhodnocují
po animaci [Z52][Z53].

### 5.1 Hlava, krk a oči (look-at)
- **Princip:** rotaci rozdělit do řetězce (hrudník → krk → hlava → oči). Jen hlava působí strojově. Bez časového
  vyhlazení hlava „cvaká“. Oči dorovnají zbytek úhlu, který hlava nepokryla [Z54][Z55].
  Čistě procedurální look-at může působit roboticky [Z56], proto přidat prodlevu a náhodu.
- **Zaklínač 3** zapíná look-at na slotu činnosti (`Is Lookat Enabled`) [Z27]. U práce s rukama (kovadlina) se
  hlava nemá otáčet, na lavici ano.
- **Godot 4.4 `LookAtModifier3D`** [Z52]: `bone_name`, `target_node`, `forward_axis`, `primary_rotation_axis`,
  `use_secondary_rotation`, `duration` + `transition_type` + `ease_type` (prodleva a plynulost při změně cíle),
  `use_angle_limitation`, `symmetry_limitation`, `primary_limit_angle`, `primary_damp_threshold` (tlumení u meze,
  jako u lidského krku), `secondary_*`, `origin_offset` (pro oči), `influence` (síla z `SkeletonModifier3D`).
- **Návrh parametrů** (*odhad*, fyziologie z běžných rozsahů):

| Uzel | Kost | Primární (do stran) | Sekundární (nahoru/dolů) | damp | duration | influence |
|---|---|---|---|---|---|---|
| LookAt hrudník | `spine_03` | 15° | 5° | 0,5 | 0,8 s | 0,3 |
| LookAt krk | `neck_01` | 35° | 15° | 0,6 | 0,6 s | 0,5 |
| LookAt hlava | `Head` | 70° (celkem i s krkem) | 25° | 0,7 | 0,45 s | 1,0 |
| oči | (shader UV) | 25° | 15° | – | 0,08 s (sakáda) | – |

- **Výběr cíle** (*odhad* podle [Z27][Z8]): hráč do `hrac_m` (7 m, už v datech), který je **před** postavou
  (úhel < 100°). Jinak nejbližší postava v hovoru, jinak bod vpřed po trase 6 m. Hráče sledovat nejdéle 3–6 s, pak
  2–4 s pauza (pohled jinam). Kdo pořád zírá, působí strašidelně. Změnu cíle opozdit o 0,2–0,5 s (reakční doba).
  Mrkání shaderem každé 2–6 s, *odhad*.
- **Tablet:** ✓ jedna `LookAtModifier3D` na hlavu, krk a hrudník je levná rotace kosti. Zapínat jen do
  `anim_plna_m` (25 m) a jen pro 4 nejbližší postavy. Oči jen do 8 m.

### 5.2 Stání: dýchání, přenášení váhy, fidgets
- Klidový klip nehrát v nekonečné smyčce. Střídat 2–4 varianty a odlišit začátek fáze. V repu `obmena_s` už je.
  Obecné doporučení pro knihovnu je 5–8 klidových variant na typ postavy (zdroj z oboru, ne Warhorse) [Z57].
- **Náhoda proti „klonům“:** při startu klipu náhodný posun fáze (`seek` 0–délka) a `speed_scale` 0,9–1,1.
  Bez toho stojí dvě postavy vedle sebe a dýchají synchronně, *odhad*.
- **Dýchání** jako aditivní vrstva: `Add2` s filtrem jen na `spine_02`, `spine_03` a `clavicle_*`, amplituda 1–2°,
  perioda 3–5 s (12–20 dechů za min), *odhad*. Lze generovat procedurálně (sinus na rotaci kosti) bez nového klipu.
- **Přenesení váhy:** každých 6–15 s krátký přechod mezi `Idle_Loop` a `Idle_FoldArms_Loop` nebo opačně, prolínání
  0,4 s. Dobře působí i otočení `pelvis` o 2–3°, *odhad*.
- **Tablet:** ✓ střídání klipů a posun fáze zadarmo; ◐ aditivní dýchání jen do 25 m.

### 5.3 Chůze: rychlost, věk, profese, únava, rozjezd, otáčení
- **Blend space 1D podle rychlosti** [Z53]: 0 → `Idle_Loop`, 1,2 m/s → `Walk_Loop`, 2,5 m/s → `Jog_Fwd_Loop`.
  Rychlost přehrávání = rychlost / rychlost klipu. Nohy pak nekloužou (v datech už `chuze_klip_m_s`).
- **Rozdíly mezi lidmi** (*odhad*; průměrná rychlost chůze dospělého je zhruba 1,2–1,4 m/s):

| Typ | Rychlost m/s | Klip | Úprava |
|---|---|---|---|
| mladá děvečka, čeledín | 1,25–1,40 | `Walk_Loop` | – |
| sedlák, selka | 1,05–1,25 | `Walk_Loop` | – |
| starý člověk | 0,80–0,95 | `Walk_Loop` ×0,7 | předklon `spine_01` +8° (aditivně) |
| stráž, rychtář | 1,10–1,20 | `Walk_Formal_Loop` | vzpřímený |
| s břemenem | 0,85–1,00 | `Walk_Carry_Loop` | po 3+ cestách −10 % (únava) |
| za tmy s lucernou | 0,90–1,05 | `Walk_Loop` + horní polovina `Idle_Lantern_Loop` | filtr kostí paží |

- **Nesouměrnost:** každé postavě při vytvoření náhodně 0,95–1,05 délky kroku a 2–4° natočení špiček
  (`foot_l/r` yaw), *odhad*.
- **Rozjezd a zastavení:** rychlost měnit plynule (zrychlení 1,5 m/s², brzdění 2,5 m/s²) a blend space se posune
  sám. Je to postup, ke kterému došel RDR2 místo jednorázových přechodových klipů [Z41].
- **Otáčení:** úhlová rychlost max. 180°/s při chůzi a 120°/s ve stoje. Při změně směru o víc než 60° ve stoje
  udělat 2–3 kroky na místě (`Walk_Loop` při 0,3 m/s). Při chůzi náklon `spine_01` do zatáčky 3–5°, *odhad*.
- **Tablet:** ✓ vše jsou parametry, žádné další klipy.

### 5.4 Vrstvy těla (AnimationTree, filtry kostí)
- **Godot 4.4 AnimationTree:** `BlendSpace1D/2D`, `Blend2/Blend3`, `Add2`, `OneShot`, `TimeScale`, `Transition`,
  `StateMachine` s `xfade_time`. Blend uzly mají **filtry**, kterými se určí, které stopy (kosti) blendem projdou.
  Tak se dělá „spodní polovina chodí, horní nese lucernu“ [Z53].
- **Navržený strom na postavu:**
  `StateMachine(pohyb | činnost | sed)` → `Blend2(horní polovina, filtr: spine_02+, clavicle, ruce)` →
  `Add2(dýchání, filtr: spine_02/03)` → `OneShot(gesto: Yes, Idle_No_Loop, Idle_Rail_Call, Interact; fade 0,2/0,3 s)`.
- **Tablet:** ◐ AnimationTree je dražší než `AnimationPlayer` a každý animovaný parametr se interpoluje každý snímek
  [Z58]. Strom používat jen do 25 m, mezi 25 a 45 m jen `AnimationPlayer` s jedním klipem (dnešní stav).

### 5.5 Přechody k místu činnosti (approach, zarovnání, warping)
- **Zaklínač 3:** slot má vstupní a výstupní animaci. Postava, která zůstává na stejném slotu, nevstává a nesedá
  znovu. „Disable Path Agent“ brání odstrčení [Z27].
- **Unreal Motion Warping:** root motion klipu se v okně klipu „ohne“ tak, aby skončil přesně na cílovém bodu
  a natočení (Skew Warp) [Z59].
- **Pro nás (bez root motion, levně):** místo má `pristup` (bod 0,6–1,0 m před slotem) a `yaw_st`.
  1. Postava dojde na `pristup` a zpomalí podle 5.3.
  2. Za 0,3–0,5 s se natočí na `yaw_st` a zároveň se posune na přesný bod. Posun je max. 0,3 m a skryje se
     prolínáním do vstupního klipu (to je ruční „warp“).
  3. Spustí se `vstup` (např. `Sitting_Enter`), pak smyčka a nakonec `vystup`.
  - UAL1 má verze s root motion i bez [Z24]. **Pro NPC použít verze bez root motion** (in-place), protože
    polohu řídí kód podle grafu cest. Root motion jen tam, kde klip mění polohu (`Sitting_Enter`, `ClimbUp_1m`),
    *odhad*.
- **Tablet:** ✓.

### 5.6 Nohy na svahu, ruce k předmětu, sekundární pohyb
- **Godot 4.4:** `SkeletonIK3D` existuje, ale je označený jako zastaralý (FABRIK, `root_bone` → `tip_bone`,
  `magnet`, `max_iterations` 10, `influence`) [Z60]. Nové IK uzly (`TwoBoneIK3D`, `FABRIK3D`, `CCDIK3D`) jsou
  **až v 4.6** a `SpringBoneSimulator3D` (vlasy, oděv) **až v 4.5** [Z61].
- **Nohy na svahu (návrh):** 2 paprsky dolů z `foot_l/r` (od výšky boků) → posun `pelvis` dolů o rozdíl nižší nohy
  (max. 0,15 m) → `SkeletonIK3D` thigh→foot na každou nohu s `max_iterations` 4. Zarovnání chodidla podle normály
  terénu max. 20°, *odhad*.
  - **Tablet:** jen pro hráče a postavy ve stoji do 10 m (max. 3 postavy).
  - Ostatním stačí posun celé postavy na výšku terénu (dnešní stav) a na svahu do 10 % (`pasma.cesta`) chyba
    pod chodidlem obvykle nebude vidět, *odhad*.
- **Ruce k předmětu:** pro uchopení (vědro, kliky rumpálu) `SkeletonIK3D` upperarm→hand jen ve chvíli `vstup`,
  *odhad*. Na tablet raději ne. Místo toho předmět připnout na `hand_r` přes `BoneAttachment3D` (Zaklínač 3 to dělá
  „Left/Right Item“ v job tree [Z27]).
- **Sekundární pohyb (oděv, vlasy):** ve 4.4 bez `SpringBoneSimulator3D` (je až v 4.5) [Z61]. Na tablet ✗.
  Náhrada je vertex shader lehkého vlnění sukně podle rychlosti, *odhad*.

### 5.7 Jak to dělají velké hry (shrnutí)
- **RDR2:** plynulé zrychlování místo přechodových klipů [Z41]; obrovská knihovna (~300 000 animací) [Z40].
  Pro nás nepřenosné, přenosné jsou jen zásady.
- **TLOU2:** motion matching na lokomoci a přesuny a samostatná vrstva ambientního chování NPC [Z44][Z45].
- **KCD2:** mocap z vlastního studia [Z62]; Skald ukládá k replikám animace a nálady [Z17]. Čísla o počtu
  klidových variant se dohledat nepodařilo.
- **Assassin's Creed:** davy jsou levné (nízké rozlišení, jednoduchý „mozek“) a plnou péči dostane jen 40 AI
  [Z42][Z43].

---

## 6. Hustota a výkon

### 6.1 Co je známo
- KCD1: ~600 aktivních NPC [Z1]. KCD2: ~2 400 NPC, z toho ~1 200 v Kutné Hoře [Z2][Z3]. Rozvrhy běží pořád,
  i daleko od hráče [Z3]. Mimo dohled se jen simulují [Z19], LOD AI zmíněn z druhé ruky [Z18]. Pokles FPS
  v Kutné Hoře připisují návody zátěži CPU od NPC [Z63].
- AC Unity: 40 plných AI + 120 modelů ve vysokém rozlišení a zbytek davu nízko [Z42].
- **Godot:**
  - `AnimationTree`/`AnimationMixer` mají `callback_mode_process = MANUAL` a `advance(delta)`. Manažer seřadí
    postavy podle vzdálenosti a vzdálené posouvá méně často (`advance(delta × přeskočené snímky)`) [Z58].
  - `VisibleOnScreenEnabler3D` vypne zpracování uzlu mimo obraz [Z58].
  - 100 postav: 75 fps v renderu Compatibility a 500+ v Mobile/Forward+ (jedno měření uživatele) [Z58].
- **Dav přes MultiMesh + VAT** (vertex animation texture): desítky tisíc postav jedním draw callem, blend
  v instance custom data. **MultiMesh ale nemá frustum culling ani LOD** a velikost textury roste s počtem vrcholů
  [Z64][Z65]. Godot má návod „animating thousands of fish“ [Z66].

### 6.2 Návrh limitů pro tablet (*odhad*, ověřit měřením na tabletu)
| Pásmo | Vzdálenost | Co běží | Frekvence AI | Animace |
|---|---|---|---|---|
| 0 – plná | do 25 m (`anim_plna_m`) | AnimationTree, look-at, vrstvy, IK nohou do 10 m | 10 Hz (0,1 s) | každý snímek; **max. 8 postav** |
| 1 – střední | 25–45 m (`anim_do_m`) | AnimationPlayer, 1 klip, bez look-at | 2 Hz | 10 fps (`anim_daleko_fps`); **max. 16 postav** |
| 2 – daleká | 45–70 m (`dosah_m`) | stojí v póze, nebo VAT dav | 0,5 Hz | 0–5 fps |
| 3 – mimo | nad 70 m nebo mimo obraz | jen rozvrh (čas → místo), bez uzlu nebo uzel z poolu skrytý | při změně bloku | žádná |

- **Celkem kreslených postav max. 24.** Pool 24 předvytvořených postav, které se přesouvají místo
  vytváření a mazání (jako AI recycling v AC [Z42]).
- Zmizení a objevení jen **mimo obraz** nebo za 70 m s prolnutím průhlednosti 0,5 s. Při změně bloku mimo
  dohled se postava objeví rovnou na místě (jako „Start In AP“ v Zaklínači 3 [Z30]). V repu už je.
- MultiMesh VAT se hodí jen na daleký dav (trh, mše), ne na Lhotu s 14 obyvateli.

---

## 7. Graf cest a vyhýbání
- **Graf:** uzly z os `cesty.json` (vozové, pěšiny, odvozené pěšiny, přechody/brody) po `krok_m` 2 m, spoje do
  `spoj_m` 2,5 m (v repu `graf`). K tomu **cestičky ke dveřím a ke slotům** (`pristup`), aby postava nešla
  napříč záhonem. Cesta přes vodu jen přes `prechody` (pravidlo testu smyslu).
- **Pravidla vyhýbání** (*odhad*, podle [Z5] a zásady „Disable Path Agent“ [Z27]):
  1. Na grafu se postavy míjejí vpravo: boční posun 0,5 m od osy, když protijdoucí je do 4 m.
  2. Hráč do `uhyb_hrac_m` (1,6 m) v cestě: zpomalit, ustoupit o 1 m stranou, look-at na hráče a případně
     kývnutí `Yes` jako pozdrav. Když hráč stojí déle než 3 s, obejít ho po grafu.
  3. Postava na slotu se neodstrkuje (kovadlina, lavice).
  4. Slot má kapacitu a rezervaci a kdo nedostal slot, vezme další ve skupině nebo počká 5–15 s s fidgetem.
  5. Dvě postavy na úzké pěšině (< 1,2 m) se nemíjí, jedna počká na rozšíření.

---

## 8. Návrh datového formátu (`pravidla/svet/postavy.json`, rozšíření kroku 2)

Zachovat stávající klíče (`role.rozvrh[].od/cinnost/kde`, `mista`, `cinnosti`, `obyvatele`, `graf`, `hlava`).
Návrh přidává:
- **`varianty` rozvrhu** (`dest`, `nedele`, `zima`) s pořadím jako ve Stardew [Z36] a Skyrimu [Z32];
- **sloty na místech** (`sloty[]` s `p`, `yaw_st`, `pristup_m`, `kapacita`, `vlastnik`) jako smart objects [Z5][Z27];
- **`vstup / smycka / vystup`** a **`predmet`** u činnosti (job tree [Z27]), `lookat` a `reaguje` na činnosti [Z27];
- **`podminky`** u místa (den/noc, sucho) [Z48];
- **`chuze`** v roli (rychlost, klip, náklon) pro odlišení věku a profese.

Odkaz na polohu je vždy přes existující záznam: `lokace` (`lokace.json`), `dum` (index z `svet._domy`), `pohyb`
(dveře dílu), `ulice` (podíl osy vsi), nebo `p` jen tam, kde žádný záznam není. Čísla jen v datech, kód nemá vlastní.

### 8.1 Místa činností (sloty)
```json
"mista": {
  "lhota_studna": {"lokace": "ves/studna", "r_m": 1.2, "sloty": [
      {"id": "rumpal", "uhel_st": 0,   "yaw_st": 180, "pristup_m": 0.8, "kapacita": 1},
      {"id": "cekani", "uhel_st": 120, "yaw_st": 300, "pristup_m": 0.0, "kapacita": 2}]},
  "lhota_lavice_hostinec": {"lokace": "hostinec", "r_m": 4.0, "uhel_st": 200, "sloty": [
      {"id": "s1", "dx_m": -0.5, "yaw_st": 20, "kapacita": 1},
      {"id": "s2", "dx_m": 0.5,  "yaw_st": 20, "kapacita": 1}], "podminky": {"sucho": true}},
  "hostinec_pult":   {"pohyb": "Hostinec_Dvere_", "dovnitr_m": 3.0, "sloty": [{"id": "pult", "kapacita": 1, "vlastnik": "hostinsky"}]},
  "hostinec_stoly":  {"lokace": "hostinec", "skryty": true, "sloty": [{"id": "t1", "kapacita": 4}, {"id": "t2", "kapacita": 4}]},
  "lhota_kovarna":   {"dum": 3, "strana": "stit", "od_zdi_m": 2.5, "sloty": [
      {"id": "kovadlina", "yaw_st": 90, "pristup_m": 0.7, "kapacita": 1, "vlastnik": "kovar"},
      {"id": "vyhen",     "yaw_st": 0,  "pristup_m": 0.6, "kapacita": 1, "vlastnik": "kovar"}]},
  "dum_spalek":      {"dum": "domov", "strana": "dvur", "od_zdi_m": 3.0, "model": "spalek_stipani", "sloty": [{"id": "s", "pristup_m": 0.7, "kapacita": 1}]},
  "dum_chlev":       {"dum": "domov", "strana": "zadni", "od_zdi_m": 1.0, "sloty": [{"id": "s", "kapacita": 2}]},
  "mlyn_slozeni":    {"pohyb": "Mlyn_Dvere_Vstup", "dovnitr_m": 2.0, "skryty": true, "sloty": [{"id": "kamen", "kapacita": 1, "vlastnik": "mlynar"}]},
  "mlyn_dvur":       {"pohyb": "Mlyn_Dvur", "sloty": [{"id": "pytle", "yaw_st": 0, "kapacita": 2}]},
  "vetrak_schody":   {"lokace": "vetrak", "r_m": 3.0, "uhel_st": 90, "sloty": [{"id": "pata", "yaw_st": 270, "pristup_m": 0.5, "kapacita": 1}]},
  "vetrak_oj":       {"lokace": "vetrak", "r_m": 4.5, "uhel_st": 270, "sloty": [{"id": "oj", "yaw_st": 90, "kapacita": 1, "vlastnik": "mlynar_vetrak"}]},
  "vetrak_plac":     {"lokace": "vetrak", "r_m": 5.0, "uhel_st": 90}
}
```
- `lokace: "ves/studna"`, `lhota_kovarna` a `Hostinec_Dvere_` jsou **návrhy jmen**. V datech dnes kovárna je jen na
  nádvoří (`nadvori_kovarna`) a studna jen v `jizda.json`. Než se použijí, musí vzniknout záznamy v `lokace.json`
  (pořadí stavby: budovy → předměty).
- **Test smyslu** má hlídat, že slot neleží ve vodě, na cestě ani na svahu nad pásmo a že `pristup` je na grafu.

### 8.2 Činnosti (job tree jako záznam)
```json
"cinnosti": {
  "stipani":  {"vstup": "PickUp_Table", "klipy": ["TreeChopping_Loop"], "obmena_s": [8, 14], "fidget": ["Idle_Loop"], "predmet": {"hand_r": "sekera"}, "lookat": false, "reaguje": true, "delka_min": [20, 40]},
  "voda":     {"obchuzka": ["lhota_studna/rumpal", "dvere"], "na_miste": {"lhota_studna/rumpal": {"klipy": ["Idle_Rail_Loop", "Interact"], "s": [6, 10]}}, "chuze": "Walk_Carry_Loop", "predmet": {"hand_r": "vedro"}, "opakovani": [3, 6]},
  "zahon":    {"klipy": ["Farm_Harvest", "Farm_PlantSeed", "Farm_Watering"], "obmena_s": [8, 18], "lookat": true, "delka_min": [30, 90]},
  "krmeni":   {"klipy": ["Farm_PlantSeed", "Interact"], "obmena_s": [5, 10], "delka_min": [10, 20]},
  "kovani":   {"klipy": ["TreeChopping_Loop"], "rychlost": 1.3, "stridani": {"vyhen": ["Interact"], "s": [20, 40]}, "predmet": {"hand_r": "kladivo"}, "lookat": false, "delka_min": [10, 20]},
  "mleti":    {"klipy": ["Interact", "Idle_Loop", "Idle_FoldArms_Loop"], "obmena_s": [6, 15], "delka_min": [30, 60]},
  "pytle":    {"obchuzka": ["mlyn_slozeni/kamen", "mlyn_dvur/pytle"], "chuze": "Walk_Carry_Loop", "opakovani": [2, 4]},
  "otaceni":  {"klipy": ["Push_Loop"], "delka_min": [2, 4], "pohyb_po_kruhu_m": 4.5, "podminky": {"vitr_zmena": true}},
  "cepovani": {"klipy": ["Idle_Loop", "PickUp_Table", "Interact"], "obmena_s": [4, 9], "lookat": true},
  "roznaseni":{"obchuzka": ["hostinec_pult/pult", "hostinec_stoly"], "chuze": "Walk_Carry_Loop"},
  "lavice":   {"vstup": "Sitting_Enter", "klipy": ["Sitting_Idle_Loop", "Sitting_Talking_Loop"], "vystup": "Sitting_Exit", "obmena_s": [10, 25], "sed": true, "lookat": true},
  "mse":      {"skryty": true, "misto": "kostel", "delka_min": [60, 90]},
  "s_luci":   {"chuze_horni": "Idle_Lantern_Loop", "filtr": "horni"}
}
```
- `delka_min` = herní minuty (×3,75 s). `obmena_s` = skutečné sekundy (v repu už tak).
- `filtr: "horni"` = Blend2 s maskou kostí `spine_02` a výš (kap. 5.4).

### 8.3 Role s variantami rozvrhu
Pravidlo: první platná varianta vyhrává (`poplach` → `dest` → `nedele` → `zima` → `vychozi`), podle [Z32][Z36].
Rozvrh musí pokrýt 24 h a test to ověří, jako v Gothicu [Z35].
```json
"role": {
  "sedlak": {"nazev": "sedlák", "chuze": {"m_s": [1.05, 1.25], "klip": "Walk_Loop"},
    "rozvrh": {
      "vychozi": [{"od": 4.5, "cinnost": "krmeni", "kde": "dum_chlev"}, {"od": 5.5, "cinnost": "stipani", "kde": "dum_spalek"},
                  {"od": 6.5, "cinnost": "zahon", "kde": "zahrada"}, {"od": 11.5, "cinnost": "jidlo", "kde": "domov"},
                  {"od": 13.0, "cinnost": "zahon", "kde": "zahrada"}, {"od": 17.5, "cinnost": "hovor", "kde": "naves"},
                  {"od": 19.0, "cinnost": "lavice", "kde": "lhota_lavice_hostinec"}, {"od": 20.5, "cinnost": "spi", "kde": "domov"}],
      "dest":    [{"od": 4.5, "cinnost": "krmeni", "kde": "dum_chlev"}, {"od": 6.0, "cinnost": "doma", "kde": "domov"},
                  {"od": 17.5, "cinnost": "jidlo", "kde": "hostinec_stoly"}, {"od": 20.5, "cinnost": "spi", "kde": "domov"}],
      "nedele":  [{"od": 6.0, "cinnost": "krmeni", "kde": "dum_chlev"}, {"od": 7.5, "cinnost": "mse", "kde": "kostel"},
                  {"od": 9.5, "cinnost": "hovor", "kde": "naves"}, {"od": 12.0, "cinnost": "jidlo", "kde": "domov"},
                  {"od": 15.0, "cinnost": "jidlo", "kde": "hostinec_stoly"}, {"od": 20.0, "cinnost": "spi", "kde": "domov"}]}},
  "selka": {"nazev": "selka", "chuze": {"m_s": [1.05, 1.2]},
    "rozvrh": {"vychozi": [{"od": 4.5, "cinnost": "voda", "kde": "lhota_studna"}, {"od": 5.5, "cinnost": "krmeni", "kde": "dum_chlev"},
                  {"od": 6.5, "cinnost": "jidlo", "kde": "domov"}, {"od": 7.0, "cinnost": "zahon", "kde": "zahrada"},
                  {"od": 10.5, "cinnost": "jidlo", "kde": "domov"}, {"od": 13.0, "cinnost": "zahon", "kde": "zahrada"},
                  {"od": 16.0, "cinnost": "hovor", "kde": "lhota_studna/cekani"}, {"od": 17.0, "cinnost": "jidlo", "kde": "domov"},
                  {"od": 20.0, "cinnost": "spi", "kde": "domov"}],
               "dest": [{"od": 4.5, "cinnost": "krmeni", "kde": "dum_chlev"}, {"od": 5.5, "cinnost": "doma", "kde": "domov"}, {"od": 20.0, "cinnost": "spi", "kde": "domov"}]}},
  "devecka": {"nazev": "děvečka", "chuze": {"m_s": [1.25, 1.4]},
    "rozvrh": {"vychozi": [{"od": 4.5, "cinnost": "voda", "kde": "lhota_studna"}, {"od": 6.5, "cinnost": "krmeni", "kde": "dum_chlev"},
                  {"od": 8.0, "cinnost": "zahon", "kde": "zahrada"}, {"od": 11.5, "cinnost": "jidlo", "kde": "domov"},
                  {"od": 12.5, "cinnost": "voda", "kde": "lhota_studna"}, {"od": 14.0, "cinnost": "zahon", "kde": "zahrada"},
                  {"od": 17.0, "cinnost": "hovor", "kde": "lhota_studna/cekani"}, {"od": 18.5, "cinnost": "jidlo", "kde": "domov"},
                  {"od": 19.5, "cinnost": "spi", "kde": "domov"}]}},
  "celedin": {"nazev": "čeledín", "chuze": {"m_s": [1.25, 1.4]},
    "rozvrh": {"vychozi": [{"od": 4.0, "cinnost": "krmeni", "kde": "dum_chlev"}, {"od": 5.5, "cinnost": "stipani", "kde": "dum_spalek"},
                  {"od": 8.0, "cinnost": "voda", "kde": "lhota_studna"}, {"od": 9.0, "cinnost": "stipani", "kde": "dum_spalek"},
                  {"od": 12.0, "cinnost": "odpocinek", "kde": "dum_spalek"}, {"od": 13.0, "cinnost": "krmeni", "kde": "dum_chlev"},
                  {"od": 14.0, "cinnost": "zahon", "kde": "zahrada"}, {"od": 18.0, "cinnost": "lavice", "kde": "lhota_lavice_hostinec"},
                  {"od": 20.0, "cinnost": "spi", "kde": "dum_chlev"}]}},
  "kovar": {"nazev": "kovář", "chuze": {"m_s": [1.1, 1.2]},
    "rozvrh": {"vychozi": [{"od": 5.0, "cinnost": "rano", "kde": "dvere"}, {"od": 5.5, "cinnost": "kovani", "kde": "lhota_kovarna/kovadlina"},
                  {"od": 12.0, "cinnost": "jidlo", "kde": "domov"}, {"od": 13.0, "cinnost": "kovani", "kde": "lhota_kovarna/kovadlina"},
                  {"od": 18.0, "cinnost": "jidlo", "kde": "hostinec_stoly"}, {"od": 20.5, "cinnost": "spi", "kde": "domov"}],
               "nedele": [{"od": 7.5, "cinnost": "mse", "kde": "kostel"}, {"od": 9.5, "cinnost": "hovor", "kde": "naves"},
                  {"od": 12.0, "cinnost": "jidlo", "kde": "domov"}, {"od": 15.0, "cinnost": "jidlo", "kde": "hostinec_stoly"}, {"od": 20.5, "cinnost": "spi", "kde": "domov"}]}},
  "hostinsky": {"nazev": "hostinský", "chuze": {"m_s": [1.0, 1.15]},
    "rozvrh": {"vychozi": [{"od": 6.0, "cinnost": "rano", "kde": "dvere"}, {"od": 7.0, "cinnost": "voda", "kde": "lhota_studna"},
                  {"od": 8.0, "cinnost": "cepovani", "kde": "hostinec_pult/pult"}, {"od": 12.0, "cinnost": "jidlo", "kde": "domov"},
                  {"od": 13.0, "cinnost": "cepovani", "kde": "hostinec_pult/pult"}, {"od": 17.0, "cinnost": "roznaseni", "kde": "hostinec_stoly"},
                  {"od": 23.0, "cinnost": "spi", "kde": "domov"}]}},
  "mlynar": {"nazev": "mlynář (vodní mlýn)", "chuze": {"m_s": [1.0, 1.15], "klip": "Walk_Loop"},
    "rozvrh": {"vychozi": [{"od": 4.0, "cinnost": "rano", "kde": "dvere"}, {"od": 4.5, "cinnost": "mleti", "kde": "mlyn_slozeni/kamen"},
                  {"od": 8.0, "cinnost": "pytle", "kde": "mlyn_dvur"}, {"od": 9.0, "cinnost": "mleti", "kde": "mlyn_slozeni/kamen"},
                  {"od": 12.0, "cinnost": "odpocinek", "kde": "mlyn_dvur"}, {"od": 13.0, "cinnost": "mleti", "kde": "mlyn_slozeni/kamen"},
                  {"od": 16.0, "cinnost": "pytle", "kde": "mlyn_dvur"}, {"od": 17.5, "cinnost": "dohled", "kde": "mlyn_dvur"},
                  {"od": 19.5, "cinnost": "spi", "kde": "domov"}]}},
  "mlynar_vetrak": {"nazev": "mlynář (větrný mlýn)", "chuze": {"m_s": [0.95, 1.1]},
    "rozvrh": {"vychozi": [{"od": 4.5, "cinnost": "rano", "kde": "dvere"}, {"od": 5.0, "cinnost": "otaceni", "kde": "vetrak_oj/oj"},
                  {"od": 5.3, "cinnost": "mleti", "kde": "vetrak_schody/pata"}, {"od": 9.0, "cinnost": "pytle", "kde": "vetrak_plac"},
                  {"od": 10.0, "cinnost": "mleti", "kde": "vetrak_schody/pata"}, {"od": 12.0, "cinnost": "odpocinek", "kde": "vetrak_plac"},
                  {"od": 13.0, "cinnost": "zahon", "kde": "zahrada"}, {"od": 15.0, "cinnost": "mleti", "kde": "vetrak_schody/pata"},
                  {"od": 19.0, "cinnost": "spi", "kde": "domov"}],
               "bezvetri": [{"od": 4.5, "cinnost": "zahon", "kde": "zahrada"}, {"od": 9.0, "cinnost": "stipani", "kde": "dum_spalek"},
                  {"od": 12.0, "cinnost": "jidlo", "kde": "domov"}, {"od": 13.0, "cinnost": "dohled", "kde": "vetrak_plac"}, {"od": 19.0, "cinnost": "spi", "kde": "domov"}]}}
}
```
- Varianta `bezvetri` odpovídá sloupovému mlýnu bez vody: bez větru nemele (`NAVOD_VETRAK.md`, lokace `vetrak`).
  Otáčení celého mlýna ojí (`otaceni`, `Push_Loop`) při změně větru je *odhad* podle běžné konstrukce sloupových
  mlýnů.
- `domov` mlynáře u vodního mlýna je `{"misto": "mlyn"}` a u větrného `{"dum": 30}` (chalupa u větráku), stejně
  jako v dnešních `obyvatele`.

### 8.4 Obyvatelé Lhoty (příklad)
```json
"obyvatele": [
  {"id": "sedlak_2",  "jmeno": "Havel",    "role": "sedlak",    "muz": true,  "vek": 40, "domov": {"dum": 2}},
  {"id": "selka_2",   "jmeno": "Markéta",  "role": "selka",     "muz": false, "vek": 36, "domov": {"dum": 2}},
  {"id": "devecka_2", "jmeno": "Ludmila",  "role": "devecka",   "muz": false, "vek": 16, "domov": {"dum": 2}},
  {"id": "celedin_2", "jmeno": "Vít",      "role": "celedin",   "muz": true,  "vek": 19, "domov": {"dum": 2}},
  {"id": "kovar",     "jmeno": "Bušek",    "role": "kovar",     "muz": true,  "vek": 45, "domov": {"dum": 3}, "prace": "lhota_kovarna"},
  {"id": "hostinsky", "jmeno": "Mareš",    "role": "hostinsky", "muz": true,  "vek": 50, "domov": {"misto": "hostinec_pult"}, "prace": "hostinec_pult"},
  {"id": "mlynar",    "jmeno": "Bartoš",   "role": "mlynar",    "muz": true,  "vek": 48, "domov": {"misto": "mlyn"}, "prace": "mlyn_slozeni"},
  {"id": "mlynar_vetrak", "jmeno": "Linhart", "role": "mlynar_vetrak", "muz": true, "vek": 58, "domov": {"dum": 30}, "prace": "vetrak_plac"}
]
```
- `vek` přepočte chůzi: nad 55 let rychlost ×0,85 a předklon 8° (kap. 5.3), *odhad*.
- Nová jména (Ludmila, Vít, Bušek, Mareš) jsou běžná česká jména 14. století, *odhad*, ověřit v rešerši jmen.

### 8.5 LOD a vyhýbání v datech
```json
"lod": {"plna_m": 25, "plna_max": 8, "stredni_m": 45, "stredni_max": 16, "stredni_fps": 10, "daleko_m": 70, "kresleno_max": 24,
        "ai_hz": [10, 2, 0.5], "ik_nohy_m": 10, "ik_nohy_max": 3, "lookat_max": 4, "oci_m": 8, "zmizeni_s": 0.5},
"vyhybani": {"bok_m": 0.5, "protijdouci_m": 4.0, "hrac_ustup_m": 1.0, "hrac_obejit_s": 3.0, "uzka_pesina_m": 1.2, "cekani_slot_s": [5, 15]},
"prirozenost": {"faze_nahodne": true, "speed_scale": [0.9, 1.1], "krok_delka": [0.95, 1.05], "spicky_st": [2, 4],
        "zrychleni_m_s2": 1.5, "brzdeni_m_s2": 2.5, "otoc_chuze_st_s": 180, "otoc_stoj_st_s": 120, "naklon_st": [3, 5],
        "dech_st": [1, 2], "dech_s": [3, 5], "vaha_s": [6, 15], "pohled_hrac_s": [3, 6], "pohled_pauza_s": [2, 4], "mrkani_s": [2, 6]}
```

---

## 9. Doporučená architektura pro Odkaz Havrana
1. **Rozvrh v datech** (`role.rozvrh.<varianta>`): bloky od hodiny → činnost → místo. Varianty jsou vybírané
   pořadím (`poplach`, `dest`, `nedele`, `zima`, `bezvetri`, `vychozi`). Test ověří pokrytí 24 h a existenci všech
   míst [Z35][Z36][Z32].
2. **Smart objects jako záznamy** (`mista.<id>.sloty[]`): poloha přes odkaz na lokaci, dům nebo dveře; natočení,
   přístupový bod, kapacita, vlastník a podmínky. Činnost nese vstup, smyčku, výstup, předmět, look-at a reakci
   [Z5][Z27].
3. **Plánovač činností** = jednoduchý stavový automat, ne GOAP:
   blok → rezervace slotu → cesta po grafu (A* nad `graf`) → přístup → zarovnání → vstup → smyčka s fidgety →
   výstup. Volné chvíle (čekání, slot obsazený) vyplní malá utility volba (lavice / hovor / stání) [Z37].
   Přerušení (hráč, déšť, poplach) mají prioritu a po nich se vrací do bloku [Z8][Z31].
4. **LOD AI:** mimo 70 m a mimo obraz jen výpočet „kde má teď být“ z rozvrhu. Uzel z poolu se přidělí při
   přiblížení a postava se objeví rovnou na slotu [Z30][Z42].
5. **LOD animací:** do 25 m AnimationTree s vrstvami a look-at (max. 8 postav), 25–45 m AnimationPlayer 10 fps
   s ručním `advance` (max. 16), 45–70 m póza, dál nic. Celkem max. 24 kreslených postav [Z58].
6. **Přirozenost:** look-at s mezemi a prodlevou, náhodná fáze a rychlost klipů, střídání klidových variant,
   plynulé zrychlení, náklon a otočení, ruční warp na slot. IK nohou jen zblízka a jen pro pár postav.
   Sekundární pohyb oděvu ve 4.4 ne [Z52][Z60][Z61].
7. **Hlídači** (`docs/pipeline.md`): do `tools/test_smyslu.py` přidat kontroly: slot není ve vodě, na cestě ani na
   svahu nad pásmo; přístup je na grafu; rozvrh pokrývá 24 h; každé `kde` existuje; každý klip je v UAL
   (`anim_ual.gd` hlásí chybějící).

---

## 10. Shrnutí v 10 bodech
1. KCD řídí NPC **rozvrhem → smart area → slotem s animací**. Smart area přiděluje sloty a nové místo nevyžaduje
   kód [Z5]. V KCD2 je navíc GOAP+MBT [Z7].
2. Rozsah: KCD1 ~600 aktivních NPC [Z1], KCD2 ~2 400 trvalých NPC s rozvrhem, který běží pořád [Z2][Z3].
3. Den: snídaně, práce, nákup, večer krčma nebo procházka. Přerušení (rvačka, přítel, trest) a změna rozvrhu po
   zločinu [Z8]. V noci domů, svléknout se, venku s pochodní [Z9]. Na déšť KCD zřejmě nereaguje [Z12][Z13].
4. Zaklínač 3 přidává **job tree** (vstup/smyčka/výstup, předmět, příznak look-at a reakce) a „Start In AP“
   [Z27][Z30]. Skyrim **pořadí balíčků** a sandbox [Z31][Z34], Gothic **pokrytí 24 h** [Z35], Stardew **variantu
   „déšť“** [Z36].
5. Náš `postavy.json` už má jádro (rozvrh, místa, činnosti, obyvatele, graf, hlava). Doplnit varianty, sloty
   s kapacitou a přístupem, vstup/výstup/předmět a parametry přirozenosti.
6. Z UAL Standard (86 klipů) pokryjeme chůzi, sezení, kleknutí, nošení, farmaření, sekání, rozhovor, jídlo, stráž
   a lucernu. **Chybí** otočení na místě, kladivo, motyka/vidle, pytel na rameni, vědra, mávnutí/úklona, modlitba
   a čepování.
7. Člověk, ne robot: look-at v řetězci hrudník–krk–hlava s mezemi 15/35/70°, prodlevou 0,45–0,8 s a pauzami
   v pohledu; náhodná fáze a rychlost klipů; plynulé zrychlení (podle RDR2 [Z41]); ruční warp na slot.
8. Godot 4.4 má `LookAtModifier3D` [Z52] a zastaralý `SkeletonIK3D` [Z60]. Nové IK uzly jsou až v 4.6 a pružiny
   vlasů a oděvu až v 4.5 [Z61]. Foot IK proto jen pro pár postav zblízka.
9. Tablet (*odhad*): max. 8 plně animovaných postav do 25 m, 16 zjednodušených do 45 m (10 fps), zmizení za 70 m,
   AI 10/2/0,5 Hz, max. 24 kreslených postav z poolu (podle AC Unity 40/120 [Z42]).
10. Motion matching (TLOU2, For Honor) a dav přes MultiMesh+VAT pro Lhotu ne: chtějí velká data nebo nemají
    culling [Z46][Z64]. VAT nechat na velké davy (trh, mše).

---

## Zdroje
- [Z1] Smrček P. (Warhorse): přednáška MFF UK o AI v KCD, https://www.karlin.mff.cuni.cz/mffseminar/prezentace_smrcek.pdf (obsah z výpisu vyhledávače, soubor nešel stáhnout); plakát https://karlin.mff.cuni.cz/mffseminar/posters/petrsmrcek.pdf
- [Z2] GDS Praha 2024, přednášky Warhorse (Labuť: NPC Daycycles in KCD2; Bocan: Invisible Design; Ziegler), https://2024.gdsession.com/index.php?action=kcd
- [Z3] GDC: Supporting Thousands of NPCs in KCD & KCD2, https://schedule.gdconf.com/session/supporting-thousands-of-npcs-in-kingdom-come-deliverance-kingdom-come-deliverance-ii/915120 ; https://gamedev.net/news/5526-supporting-thousands-of-npcs-in-kingdom-come-deliverance-kingdom-come/
- [Z4] GDC (příspěvek): https://digg.com/gaming/ketmfwph
- [Z5] Černý, Plch, Marko, Ondráček, Brom: Smart Areas – A Modular Approach to Simulation of Daily Life in an Open World Video Game (2014), https://www.scitepress.org/Papers/2014/49211/49211.pdf
- [Z6] Using Behavior Objects to Manage Complexity in Virtual Worlds, https://arxiv.org/pdf/1508.00377v1.pdf ; https://dspace.cuni.cz/handle/20.500.11956/82390
- [Z7] Marko M.: Combining GOAP and MBTs to Create NPCs' Behaviors for KCD II (GDC Game AI Summit), https://gdcvault.com/play/1035576/Game-AI-Summit-Combining-GOAP
- [Z8] Wccftech: KCD2 dev talks about dynamic NPC routines (Ziegler), https://wccftech.com/kingdom-come-deliverance-2-dev-talks-about-dynamic-npc-routines-and-emergent-storytelling-for-side-quests/amp/
- [Z9] RPG Codex Review: KCD, https://rpgcodex.net/article.php?id=11114
- [Z10] Press Start: rozhovor s týmem KCD2, https://press-start.com.au/features/2024/12/05/we-spoke-to-the-kingdom-come-deliverance-2-team-about-the-brutal-combat-and-living-world/
- [Z11] Wikipedie: Kingdom Come: Deliverance, https://en.wikipedia.org/wiki/Kingdom_Come:_Deliverance
- [Z12] Fórum KCD: A few small suggestions (zametání v dešti), https://forum.kingdomcomerpg.com/t/a-few-small-suggestions/44517
- [Z13] Steam KCD2 (Zaklínač: schovávání pod střechy), https://steamcommunity.com/app/1771300/discussions/0/601895917151378452/
- [Z14] Guides4gamers: In the Cloister, https://guides4gamers.com/kingdom-come-deliverance/quests/in-the-cloister/
- [Z15] KCD wiki: Church / Liturgy, https://kingdomcomedeliverance.wiki.gg/wiki/Church ; https://kingdomcomedeliverance.wiki.gg/wiki/Liturgy
- [Z16] TechRaptor: KCD modding tools (Skald), https://techraptor.net/gaming/news/kingdom-come-deliverance-modding-tools-released
- [Z17] GameStar: KCD Mod-Support (Skald: dialogy, cutscény, animace a nálady), https://www.gamestar.de/artikel/kingdom-come-deliverance-mod-support,3350817.html
- [Z18] Fórum KCD: Performance on loading every npc, https://forum.kingdomcomerpg.com/t/performance-on-loading-every-npc-suggestion/27257
- [Z19] E15: Ze školy do hry. Jak Warhorse a Matfyz tvoří umělou inteligenci, https://www.e15.cz/magazin/ze-skoly-do-hry-jak-warhorse-a-matfyz-tvori-umelou-inteligenci-1178418
- [Z20] Daily Life in the Middle Ages, https://historycrunch.com/daily-life-in-the-middle-ages/ ; https://feddit.it/comment/3597089
- [Z21] World History Encyclopedia: Peasant Life in a Medieval Manor, https://www.worldhistory.org/article/2826/peasant-life-in-a-medieval-manor/
- [Z22] Fórum KCD: NPC behaviour and routine, https://forum.kingdomcomerpg.com/t/npc-behaviour-and-routine/20268
- [Z23] Repo: `modely/postavy/anim/UAL1.glb`, `UAL2.glb`, `UAL_License.txt` (CC0, Quaternius); původ v `docs/predani.md`
- [Z24] Quaternius: Universal Animation Library (itch.io), https://quaternius.itch.io/universal-animation-library
- [Z25] Quaternius: Universal Animation Library, https://quaternius.com/packs/universalanimationlibrary.html ; OpenGameArt https://opengameart.org/content/universal-animation-library
- [Z26] Quaternius: Universal Animation Library 2, https://quaternius.itch.io/universal-animation-library-2 ; https://opengameart.org/content/universal-animation-library-2
- [Z27] REDkit wiki: Action points (job tree, vstup/výstup, Is Lookat Enabled, Can React, Disable Path Agent, předměty), https://redkitwiki.cdprojektred.com/actionpoints.htm
- [Z28] REDkit: TOOL Job Tree editor, https://cdprojektred.atlassian.net/wiki/spaces/W3REDkit/pages/6328487/TOOL%3A+Job+Tree+editor
- [Z29] REDkit wiki: Spawn NPCs (community, spawnset, story phase, timetable), https://redkitwiki.cdprojektred.com/spawn+npcs.htm
- [Z30] REDkit wiki: Community editor (Start In AP), https://redkitwiki.cdprojektred.com/community+editor.htm
- [Z31] UESP: Oblivion Radiant, https://en.uesp.net/wiki/Oblivion:Radiant ; Wikipedie Radiant AI https://en.wikipedia.org/wiki/Radiant_AI
- [Z32] UESP CS wiki: AI Package (kaskádový seznam), https://cs.uesp.net/wiki/Package
- [Z33] Creation Kit wiki: Bethesda Tutorial Packages, https://ck.uesp.net/wiki/Bethesda_Tutorial_Packages
- [Z34] Fallout CK wiki: Sandbox (Procedure), https://falloutck.uesp.net/wiki/Sandbox_Package ; Idle Markers https://ck.uesp.net/wiki/IdleMarker
- [Z35] World of Gothic: tutoriál denní rutiny (TA, Rtn_Start, FP_STAND), https://worldofgothic.de/download.php?id=1162
- [Z36] Stardew Valley wiki: Modding:Schedule data, https://stardewvalleywiki.com/Modding:Schedule_data
- [Z37] GMTK: The Genius AI Behind The Sims (přepis), https://amara.org/subtitles/cVoJS4OdmVql/en/1/download/The%20Genius%20AI%20Behind%20The%20Sims.en.txt
- [Z38] Wikipedie: Utility system, https://en.wikipedia.org/wiki/Utility_system
- [Z39] PPE: RDR2 z konkretami, https://www.ppe.pl/news/58028/red-dead-redemption-2-z-konkretami-wrazenia-po-45-minutach-gry.html ; Mein-MMO: co dělají NPC v RDR2, https://mein-mmo.de/en/3-npcs-red-dead-redemption-2-einen-tag,286499
- [Z40] TechRadar: GTA 6 600 000 animací, dvojnásobek RDR2, https://techradar.com/gaming/rockstar-reveals-it-built-a-gta-6-team-that-focused-solely-on-creating-more-realistic-npcs-with-over-600-000-animations-twice-as-many-as-red-dead-redemption-2-had
- [Z41] PC Gamer: koně v RDR2 (plynulé zrychlování místo přechodů), https://www.pcgamer.com/uk/the-mind-boggling-work-that-went-into-red-dead-2s-incredibly-lifelike-horses/ ; GDC lokomoce RDR2 https://gdconf.com/news/learn-secrets-red-dead-redemption-2s-player-locomotion-gdc
- [Z42] GDC Vault: Massive Crowd on Assassin's Creed Unity: AI Recycling (40 AI / 120 modelů / 10 000 NPC), https://gdcvault.com/play/1022141/Massive-Crowd-on-Assassin-s
- [Z43] GDC: Postmortem Developing Systemic Crowd Events on AC Unity, https://gdcvault.com/play/1022211/Postmortem-Developing-Systemic-Crowd-Events ; GameStar 10 000 NPC https://www.gamestar.de/artikel/assassins-creed-unity-szene-mit-10000-npcs-gleichzeitig,3080201.html
- [Z44] Naughty Dog at GDC 2021 (Motion Matching in TLOU2), https://www.naughtydog.com/blog/naughty_dog_at_gdc_2021
- [Z45] Mach M.: TLOU2 NPC Animation reel, https://vimeo.com/433024043 ; GDC Bringing Allies to Life https://gdcvault.com/play/1027207/Bringing-Allies-to-Life-in
- [Z46] Game Watch: Motion Matching (GDC 2016), https://game.watch.impress.co.jp/docs/news/749136.html
- [Z47] GDC Vault: Clavet, Motion Matching and The Road to Next-Gen Animation, https://gdcvault.com/play/1023280/Motion-Matching-and-The-Road
- [Z48] TaleWorlds fórum: Agent Spawning OSP (Bannerlord), https://forums.taleworlds.com/index.php/topic,317313.0.html
- [Z49] Medieval Dynasty: Steam diskuse a návod k práci, https://steamcommunity.com/app/1129580/discussions/0/2952663522503846415 ; https://www.gfinityesports.com/medieval-dynasty/medieval-dynasty-jobs-guide-how-to-assign-roles-to-villagers-and-make-workers/
- [Z50] Manor Lords: recenze Digitec, https://www.digitec.ch/en/page/manor-lords-played-now-unbelievably-good-32837 ; Unreal rozhovor https://www.unrealengine.com/developer-interviews/solo-dev-makes-sophisticated-sim-manor-lords-using-unreal-engine
- [Z51] Famitsu: GDC 2021 Genshin Impact – Building a Scalable AI System, https://www.famitsu.com/news/202107/22228078.html
- [Z52] Godot 4.4 docs: LookAtModifier3D, https://docs.godotengine.org/en/4.4/classes/class_lookatmodifier3d.html
- [Z53] Godot 4.4 docs: Using AnimationTree, https://docs.godotengine.org/en/4.4/tutorials/animation/animation_tree.html
- [Z54] Vulkan tutorial: Look-At Controllers, https://docs.vulkan.org/tutorial/latest/Advanced_glTF/Procedural_Animation_IK/05_look_at.html
- [Z55] Unreal Community Wiki: Head and Eye Look At, https://unrealcommunity.wiki/head-and-eye-look-at-tutorial-fq2ru1sq
- [Z56] MIG 2023 (procedurální look-at působí roboticky), https://unpaywall.org/10.1145%2F3623264.3624438
- [Z57] MoCap Online: NPC animation guide (5–8 klidových variant), https://mocaponline.com/blogs/mocap-news/crowd-npc-animation-guide
- [Z58] Godot docs AnimationTree (callback_mode_process, advance), https://docs.godotengine.org/en/latest/classes/class_animationtree.html ; r/godot „Animation tree killing FPS“ https://lr.sudovanilla.org/r/godot/comments/1fivfwd/animation_tree_killing_fps
- [Z59] Unreal Engine: Motion Warping, https://dev.epicgames.com/documentation/en-us/unreal-engine/motion-warping-in-unreal-engine
- [Z60] Godot 4.4 docs: SkeletonIK3D (deprecated), https://docs.godotengine.org/en/4.4/classes/class_skeletonik3d.html
- [Z61] Godot blog: Inverse kinematics returns to Godot 4.6 (přehled 4.4/4.5/4.6), https://godotengine.org/article/inverse-kinematics-returns-to-godot-4-6/
- [Z62] Multiplayer.it: motion capture KCD2, https://multiplayer.it/notizie/un-video-ci-mostra-il-motion-capture-di-kingdom-come-deliverance-2.html
- [Z63] CheckFPS: KCD2 optimalizace (Kutná Hora a CPU), https://checkfps.io/en/optimize-fps/kingdom-come-deliverance-2
- [Z64] Godot Shaders: Vertex animation with instancing (VAT), https://godotshaders.com/shader/vertex-animation-with-instancing/
- [Z65] Godot fórum: OpenVAT for Godot, https://forum.godotengine.org/t/openvat-for-godot-animated-multimeshinstance3d-using-vertex-animation-textures/139440
- [Z66] Godot docs: Animating thousands of fish with MultiMeshInstance3D, https://docs.godotengine.org/de/4.4/tutorials/performance/vertex_animation/animating_thousands_of_fish.html
