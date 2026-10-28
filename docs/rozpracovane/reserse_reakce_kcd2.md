# Rešerše: jak NPC v KCD1/KCD2 vnímají hráče a reagují na něj → data pro Odkaz Havrana

Rešerše z 28. 10. 2026. Navazuje na `docs/rozpracovane/reserse_postavy_kcd2.md`, kde jsou rozvrhy, místa činností,
look-at hlavy a LOD. Tady to neopakuji. Tato rešerše řeší, **kdo si hráče všimne, jak dlouho to trvá, co na něm
pozná a jak podle své role zareaguje**. Zadání Míši: „ne každý se dívá na hráče, má svoji roli – KCD2 na to má postupy“.

Ke každému tvrzení je odkaz [R…] na seznam na konci. *odhad* = nedohledáno, navrženo z podobnosti.
*výklad* = číslo je doložené, ale význam vzorce si odvozuji z názvu a popisu parametru.
Podle pravidla z CLAUDE.md (28. 10.) platí: **všechny hodnoty návrhu v kap. 6 jsou NEOVĚŘENO**. Na tabletu ani
v naší hře změřené nejsou. Ze hry KCD pocházejí jen čísla s odkazem [R1]–[R4].

**Nejdůležitější zjištění:** KCD2 má vnímání popsané v **oficiálních tabulkách Warhorse pro modery**.
`rpg_param` (export 14. 1. 2025, s popisem a jednotkou každého parametru) a seznam odvozených statistik duše
(`charisma`, `vib` viditelnost, `con` nápadnost, `noi` hluk, `drt` špína, `sml` pach, `bld` zakrvácení, `brn` cejch,
`dru` opilost) [R3][R4]. Pro KCD1 (patch 1.4) je stejná tabulka na Nexus wiki, komentovaná moderem [R1][R2].
Čísla níže jsou tedy skutečné hodnoty ze hry, ne odhady recenzentů.

**Stav v repu (přečteno, nic neměněno):**
- `pravidla/svet/postavy.json` má u role jen `zvedavost` (0–1) a u činnosti `soustredeni` (0–1).
  `scripts/lide.gd` ř. 399–405 počítá šanci, že se postava podívá: `zvedavost × (1 − soustredeni)`. Rozhodne se
  jednou, když hráč vejde do `hlava.hrac_m` = 7 m. Pohled trvá `prirozenost.pohled_hrac_s` = 3–6 s, pak se postava
  dívá jinam 4–9 s.
- Role v datech jsou `sedlak, selka, rychtar, lamac, celedin, dvorka` („děvečka na tvrzi“) a `mlynar`. Stráž zatím
  v datech není.
- Herní čas: 1 herní hodina = 225 s skutečného času (`scripts/daylight.gd`). KCD má `DefaultWorldTimeRatio` = 15,
  tedy 1 herní hodina = 240 s [R1][R3]. **Časy KCD v herních hodinách proto převádíme 1 : 1.** Rozdíl je jen 6 %.

---

## 1. Jak je vnímání v KCD postavené (architektura)

- **Duše (soul):** každé NPC je záznam v tabulce `soul` se statistikami `vision`, `hearing`, `courage`, `charisma`
  a `shadiness`, s osobní pověstí k hráči (`reputation`), frakcí, **společenskou třídou** (`social_class_id`, „hraje roli
  v systému zločinu“), rolí v zločinu (`soul_crime_role`, např. `soldier`) a rozvrhem `activity_0-8` / `time_0-8` [R7].
  To je přesně to, co chceme: **reakce plyne z dat role, ne z kódu.**
- **Mozek `npc_daycycle`** obsluhuje u běžného NPC všechno: sluch, vnímání, zločin, vstup na cizí pozemek,
  žádosti o rozhovor, přítomnost hráče a rozvrh [R7].
- **Metarole = vypínatelné sady replik.** Systémové komentáře jsou metarole s českými interními jmény.
  `KOMENTAR_NA_JINDRU` („Jindřich nás přišel navštívit!“, interně *dudeprox*), komentáře k vniknutí („Vypadni, než
  zavolám stráž“) [R7], `NPC_ZDRAVI_HRACE` (zdraví hráče) a `NPC_VITA_HRACE_V_OBCHODE` (vítá hráče v obchodě) [R13].
  Mod NPC Reactions zvlášť vypíná komentáře k hráči **opilému, zraněnému, nahému a páchnoucímu** [R13]. To jsou
  v KCD2 čtyři „stavy hráče“, na které vesničané mluví.
- **Repliky (barks)** jsou monology typu *InGame* (bez kamer a bez volby). Každá sekvence má **cooldown v sekundách
  herního času**, `-1` znamená „jen jednou“. Ze všech platných replik se přehraje ta s nejvyšší prioritou [R8].
  Pozdrav před rozhovorem je zvláštní typ dialogu *Greeting* [R8].
- **Fáze vnímání na obrazovce (zajíc):** bílý zajíc = hledají (s lupou = hledají tebe), žlutý = všiml si, uši
  stoupají s rozpoznáním a NPC jde blíž, žlutý s rohem = civilista běží hlásit stráži, oranžový se zdviženou rukou
  = „odejdi“ nebo zastavení stráží, oranžový/červený s mečem = boj [R19]. **Pro nás z toho plyne pevné pořadí
  stavů: klid → všiml si → rozpoznal → konfrontace / hlášení → útěk / boj.**
- **Nervozita a hněv** jsou zvlášť od pověsti. Nervozita je u jednotlivce, šíří se na 10 m a rychle opadá. Hněv je
  u frakce (vsi), opadá za dny a nad prahem začnou lidé nosit zbraně [R3]. To souhlasí s výrokem Warhorse, že po
  násilí ve vsi lidé zůstávají doma a nosí zbraň [R29].

---

## 2. Co ovlivňuje, zda si NPC hráče všimne a jak zareaguje

### 2.1 Zorné pole, dohled a světlo (KCD2, oficiální hodnoty [R3], vzorce [R11])
| Parametr | KCD1 [R1] | KCD2 [R3] | Význam |
|---|---|---|---|
| `PerceptionMinFov` / `MaxFov` | 90° / 180° | **90° / 100°** | zorné pole; `FOV = min(MinFov + HearingToFov·sluch, MaxFov)` [R11] |
| `HearingToFov` | 3 °/bod | 1 °/bod | sluch rozšiřuje zorné pole |
| `MinViewRadius` | 2,5 m | **2,5 m** | dohled „slepého“ NPC; **zároveň hranice okamžitého zjištění** |
| `MaxViewRadius` | 100 m | **50 m** | strop dohledu |
| `VisionToViewRadius` | 2 m/bod | **1,35 m/bod** | `dohled = min(2,5 + 1,35·denní_koef·(zrak − 1), 50)` [R11] |
| `MinViewRadiusTimeOfDayCoef` | – | **0,5** | noc zkrátí dohled nejvýš na polovinu |
| `MinViewRadiusFogCoef` | – | 0,5 | mlha stejně |
| `PerceptionInnerConeMin/MaxRelSize` | – | **0,4 / 1,0** | vnitřní kužel je u klidného NPC 40 % a roste s nervozitou až do plných 100 % (`…NervousnessLimit` 1) |
| `DuskTime` / `DawnTime` | 21,5 / 4,5 h | **21,3 / 4,7 h**, přechod 2,6 h | kdy platí „noc“ |
| `VisibilityDecrement…` | `NightCoefToVis` −0,5 | den uvnitř −0,3, noc uvnitř −0,5, **noc venku −0,7**, mlha −0,5, vysoká tráva −0,35 | ubírá viditelnost hráče (rozsah −2 až 3,5) |
| `MinLightProbeVisibility` / `MaxLightProbeValue` | −1 / 65 | – | KCD1 měří světlo u hráče sondou |

- Viditelnost hráče = viditelnost výstroje + postih za pohyb + světlo [R11]. Oblečení je průměr viditelnosti
  viditelných kusů a obyčejný kabátec přes zbroj ji sníží ze 46 na 27 (hráčský postřeh) [R15].
- **Příklad (*výklad*):** NPC se zrakem 10 má ve dne dohled 2,5 + 1,35·9 = **14,6 m**, v noci 2,5 + 1,35·0,5·9 =
  **8,6 m**. Se zrakem 20 je to 28 m ve dne a 15 m v noci. Jaký zrak mají běžní vesničané, tabulky neříkají
  (strop statistiky je 30 [R3]), proto *odhad* 8–15.
- Rada z návodu KCD2: v noci nosit ve vsi pochodeň, jinak budíte podezření [R20b].

### 2.2 Rozpoznání: jak dlouho trvá, než si všimne (KCD2 [R3], KCD1 [R1][R2])
| Parametr | KCD1 | KCD2 | Popis od Warhorse |
|---|---|---|---|
| `RecognitionTimePCoef` | 8 s | **4 s** | doba rozpoznání postavy s nápadností 0 |
| `RecognitionTimeKPositiveCoef` | −3 | **−2 s/bod** | násobek pro kladnou nápadnost |
| `RecognitionTimeKNegativeCoef` | −6 | **−4 s/bod** | násobek pro zápornou nápadnost |
| `MinModConspicuousness` / `Max…` | −1 / 1 | **−1 / 1** | rozsah nápadnosti |
| `RecognitionSpeedNotVisible` | −0,5 | **−0,5 /s** | když hráč zmizí z dohledu, rozpoznání klesá |
| `PerceptionSecondaryDecayTime` | – | **4 s** | za tak dlouho NPC na hráče „zapomene“, když ho přestane vnímat |
| `PerceptionSecondaryCrowdMembers` | – | **4** | **v hloučku 4 a více lidí je hráč pro vedlejší vnímání neviditelný** |
| `StealthSkillToRecogTime` | – | +60 % při max. dovednosti | (dovednosti hráče až později) |
| `StealthCooldown` | 5 s | – | po tom, co ho poslední pozorovatel přestane vidět |

- **Výklad:** `T = 4 + K·nápadnost`. Nápadný hráč (+1) je rozpoznán za **2 s**, nenápadný (−1) za **8 s**
  (4 + (−4)·(−1)). V KCD1 to bylo 5–14 s.
- **Stavy hráče (krev, opilost, nahota, pach) NPC rozpozná okamžitě jen do 40 % svého dohledu**
  (`PerceivedStateRecognitionDistanceMin` 0,4) a **za hranicí dohledu nikdy** (`…Max` 1,0) [R3].
  Pro NPC se zrakem 10 to ve dne dělá 5,9 m. **Proto komentáře ke stavu jen zblízka.**
- Nápadnost zvyšují pestré a neobvyklé šaty („lidé se podívají dvakrát“) [R15] a střelba z luku [výpis R15].
  Trest na pranýři přidá nápadnost +0,4 a ubere charisma −4 na 2400 s [R5]. **I pověst se tak propisuje do vzhledu.**

### 2.3 Priorita pozornosti: koho si NPC vybere (to je „ne každý se dívá“)
NPC nesleduje všechno najednou. Každý viditelný cíl (osoba, předmět, zločin) dostane prioritu a vnímání se věnuje
těm nejvýš. Popis Warhorse: „target priority estimation, #perception“ [R3].
| Složka priority | KCD1 [R1] | KCD2 [R3] |
|---|---|---|
| hráč (`PriorBoostPlayer`) | 12 | **20** |
| mrtvý nebo bezvědomý | 25 | **25** |
| zločin: krade (`CrimeLoot`), nese mrtvolu | 12 / – | **12 / 12** |
| viditelný zločin / lidé / předměty | 6 / 2 / 0,5 | **6 / 3 / 0,5** |
| **zbraň** (`PriorWeapon`) | 8 | **6**, střelná ×4,2 (= 25) |
| **nápadnost** (`PriorConsp`, za bod) | 3 | **6** |
| charisma (`PriorCha` / `BaseCha`) | 0,3 / 10 | **0,15 / 15** |
| vzdálenost (`PriorDist` / `MeanDist`) | 2 / 5 m | **2 / 5 m** |
| opačné pohlaví (`PriorGender`) | 2 | **2** |
| přítel / nepřítel (+ bonus) | −4 / −50 | **−4 / −15 (+20)** |
| zvíře | −15 | −15 |
| skript (quest) | – | 30 |

- **Výklad:** priorita je součet složek. Jak přesně se kombinuje, ani komentář moderů neuvádí (*odhad*).
  Důležité poměry: **tasená zbraň má třetinovou váhu samotného hráče a luk v ruce víc než hráč. Jeden bod
  nápadnosti váží stejně jako zbraň. Přítel (−4) je méně zajímavý než cizí. Mrtvola nebo zloděj přebijí všechno.**
- Vedlejší důsledek: **v davu (4+) hráč z vedlejšího vnímání mizí** [R3]. Ve vsi u studny nebo na návsi se tedy
  nemají otáčet všichni.

### 2.4 Vzhled: oblečení, třída, zbroj, charisma
- **Charisma = průměr charismatu viditelných kusů oblečení**, spodní vrstvy se nepočítají [R15][R32]. Snižuje ho
  špína, krev a opotřebení: `ArmorDirtToCharismaCoef` 0,8 a `ArmorStatusToCharismaCoef` 0,6 v KCD2, 1 a 0,67
  v KCD1 [R3][R1]. Popis parametru je v tabulce zkopírovaný omylem, význam „vliv špíny / stavu na charisma“ plyne
  z názvu (*výklad*).
- **„Šaty dělají člověka“ je doložené pravidlo:** `PerceivedSocialClassImportanceThresholdRel` = 0,333.
  Když víc než třetina výstroje patří ke společenské třídě, **NPC vidí hráče jako člena té třídy**. Stejně funguje
  převlek za frakci (`PerceivedSuperfaction…` 0,333) [R3]. Převlek prohlédne jen zblízka: do třetiny svého dohledu,
  nejméně však na 1,5 m (`TrueRelationDistThresholdRel` 0,333, `MinTrueRelationDistThreshold` 1,5 m) [R3].
- **Třídy:** urozený / neurozený se dělí podle bohatství třídy, práh `HighbornWealthThreshold` = 10 [R3][R10].
  Mezi urozené KCD1 počítá šlechtice, kněze, **rychtáře (Bailiff)**, kupce, krčmáře, měšťany a důstojníky.
  Mezi neurozené počítá vesničany, **mlynáře**, kováře, kameníky, uhlíře, dřevorubce, mnichy, vojáky, **hlídače**
  a **žebráky** [R12]. Zločin proti vyšší třídě je těžší (`scalingWithSocialClass`) [R6].
- KCD1 i KCD2 zacházejí s Jindřichem hůř, když vypadá jako sedlák, než když ho mají za šlechtice [R30]. Špína ztěžuje
  přesvědčování hlavně **u stráží a u lidí vysokého postavení** [R17]. **V KCD2 ubyla jedna reakce:** v plné zbroji
  ho lidé už nepoznávají jako rytíře a jednají s ním jako s měšťanem. Hráči to kritizují. Jedno vysvětlení zní,
  že v Kutné Hoře jsou rytíři běžní [R23]. **Pro naši malou ves platí spíš chování KCD1: na urozeného se reaguje.**
- Pozdrav „pane“ vs. nic: oficiálně doložený seznam replik podle vzhledu není (*odhad*). Doložené jsou metarole
  pozdravu (`NPC_ZDRAVI_HRACE`) [R13], vnímání třídy podle šatů [R3] a lepší zacházení s urozeně vypadajícím [R30].
- Dobrá pověst se při zkoušce přičte k charismatu (`RelationshipToImpressCharisma` 0,4) [R3].
  Pod pověstí 0,5 je zkouška těžší (`SkillcheckReputationPenalty`) [R3].

### 2.5 Špína, krev a pach (KCD2 [R3], [R18])
| Parametr | Hodnota | Význam |
|---|---|---|
| `IsCleanBuffMaxDirtiness` | 0,25 | do této špíny je hráč „čistý“ |
| `PerkManlyOdourDirtinessThreshold` | 0,5 | od této špíny „mužný pach“ (bonus u žen v KCD1 [R10]) |
| **`SmellBuffDirtinessLevel`** | **0,8** | **od špíny 0,8 hráč páchne** (buff Smell, statistiky `sml`, `smi`) |
| `FullClothDirtyingOnFullSpeed` | 35 000 m | 100 % špíny po 35 km chůze plnou rychlostí (KCD1: 4 000 m) |
| `SchedulerSoilPerSecond` | 3,5·10⁻⁵ /s | samovolné špinění, tedy 100 % za ~8 herních hodin (*výklad*) |
| `HoleDiggingDirtiness` / `AddedDirtOnCarryItem` | 0,45 / 0,04 | kopání hrobu, nošení pytle |
| `ClothesBloodSoakOnMaxBleeding` | 240 s | oděv zcela zkrvavený po 4 min krvácení |
| `DreadSkillcheckBloodinessWeight` / `Dirtiness…` | 0,15 / 0,1 | **krev a špína pomáhají zastrašit** |
| `WashDirtLimitMin/Max` | 0,3 / 0,8 | kolik špíny jde smýt v potoce |

- Pach v KCD2 podle hlavního designéra Ondřeje Bittnera: „kolem tebe je kruh… vysíláš ‚jsem tady‘“. Páchnoucího
  hráče NPC odhalí i bez zraku [R18].
- Repliky: hráči hlásí, že stráže i lidé jeho zápach často komentují [R31]. Šlechtic si zacpe nos a pošle ho se umýt
  [R31b]. Mod [R13] vypíná právě komentáře ke špíně a pachu.

### 2.6 Opilost, zranění, únava
- Opilost (`dru`) mění charisma až o ±4 a nápadnost až o ±3 (KCD2 `AlcoholMaxCHAEffect` 4, `AlcoholMaxCONEffect` 3).
  Hráč je opilý od 0,32, NPC od 0,5 [R3]. Opilé NPC se snáz okrade (KCD1 `PickpocketingNPCDrunkTimeChanceMod` 0,5) [R1].
- Zranění: končetina je zdravá pod 0,6 a nad 0,8 krvácí [R3]. NPC na zraněného hráče mají vlastní komentáře [R13].
- Vyčerpání: charisma ×0,75 při nulové výdrži, lineárně od 50 % [R3][R2].

### 2.7 Zbraň v ruce
- Váha zbraně v prioritě pozornosti je 6, luk ×4,2 (kap. 2.3) [R3].
- Hráči hlásí, že **běh městem s tasenou zbraní stráže trestají** a že mluvit s lukem v ruce se bere jako přestupek
  [R25]. Pro KCD1 platí rada „nemít ve vsi se strážemi tasenou zbraň“ [R25] (hráčské postřehy, ne pravidlo Warhorse).
- Po násilí ve vsi NPC nosí zbraň [R29]. V datech je to `AngrinessArmingThreshold` = 0,67: nad tímto hněvem frakce
  si NPC všude berou zbraně [R3].

### 2.8 Vlastnictví místa (cizí dům, za pultem)
- Systémový komentář k vniknutí patří k metaroli („Vypadni, než zavolám stráž“) [R7]. Indikátor je oranžový zajíc
  s nataženou rukou: „odejdi hned“ [R19].
- Podle hráčů jde otevřít nezamčené dveře, uvidět upozornění a během pár sekund odejít bez trestu (ne vždy).
  Varování přijde i za obchodním pultem ve dne [R20].
- KCD1: majitel někdy stráž nevolá, jen „postává kolem, dokud neodejdeš“. U domu bez ikony vniknutí se tváří
  nevlídně a vyzve tě k odchodu [R20] (hráčský postřeh).
- Dlouhodobá paměť na vniknutí je `crime_longTermMemoryTrespassExpiration` = 7200 s, tedy 2 herní hodiny
  (*výklad* jednotky) [R6].
- Kdo byl viděn poblíž místa zločinu, toho NPC podezírají, i když nic neudělal [R20].

### 2.9 Pověst: globální, ve vsi, osobní
| Parametr (KCD2 [R3]) | Hodnota | Význam |
|---|---|---|
| rozsah | 0–1, výchozí 0,5 (`DefaultRelationship` [R1]) | Starší dokumentace uvádí −1…1 a „pod 0 útočí“ [R9]. Číselné prahy níže jsou v rozsahu 0–1. |
| prahy ikon | **0,2 / 0,4 / 0,6 / 0,8** | nepřátelská / chladná / neutrální / přátelská / velmi přátelská |
| `LocalHeroInfamousReputationThreshold` | 0,6 (KCD1 0,7) | nad prahem „místní hrdina“, pod ním „nechvalně známý“ |
| `NPCRepWeight` / `FactionRepWeight` / `SuperFactionRepWeight` | **5 / 3 / 1** | výsledná pověst je vážený medián: osobní, ves, kraj |
| `ReputationPropagationTime` + `BiasTime` | **3 h ± 0,5 h** | za jak dlouho se osobní zkušenost propíše do vsi (herní čas) |
| `ReputationPropagationCoefCap` | 0,15 | nejvýš kolik se propíše najednou |
| `ReputationSpatialPropagationDistance` / `…Prapagation` | 400 m / 0,25 | čtvrtina změny dojde do sousedních vsí do 400 m |
| `IndulgencePriceFactor` | 720 | odpustek (smíření) stojí 720 × zlepšení pověsti |

- Každé NPC má **osobní** pověst k hráči a frakce (ves) má průměr osobních pověstí. Změna frakční pověsti se rozpíše
  do osobních [R9]. Pověst sama od sebe neopadá. Opadá jen hněv. Obojí smaže odpustek nebo vězení [R9].
- Ve vsi se pověst dělí na skupiny podle obyvatel (vojáci, vesničané / lamači, obchodníci jen v Ratajích). Ves má
  plnou pověst, když hráče podporuje **většina každé skupiny**. Obchodník začíná na 50. Nízká pověst u ratajských
  vojáků znamená časté zastavování a prohledávání [R16].
- Cejch v KCD2: obchodníci s hráčem neobchodují, lidé se mu vyhýbají a zisk dobré pověsti je poloviční, dokud se
  rána nezahojí [R21].

---

## 3. Typy reakcí podle role a stavu

### 3.1 Co dělá KCD (doložené)
| Reakce | Kdo a kdy | Zdroj |
|---|---|---|
| ignoruje | přítel je méně zajímavý (−4), v davu 4+ hráče nevnímá, za hranicí dohledu stav nepozná | [R3] |
| pozdrav | metarole `NPC_ZDRAVI_HRACE`, *dudeprox* „Jindřich nás přišel navštívit“. Hráči si v KCD1 stěžovali, že zdraví všichni a pořád, a vývojáři to v patchi omezili | [R7][R13][R24] |
| komentář ke stavu | opilý, zraněný, nahý, páchnoucí, ale i pes a kůň hráče | [R13] |
| stížnost po vrážení | „NPC si stěžují, když do nich vrazíš“ (mod na ztlumení) | [R14] |
| sledování / postávání | majitel u domu postává, dokud hráč neodejde | [R20] |
| varování a vykázání | komentář k vniknutí, oranžový zajíc | [R7][R19] |
| hlášení stráži | svědek zločinu běží za strážným (žlutý zajíc s rohem) a strážný pak hráče zatkne | [R19] |
| útěk, zamykání | na poplach NPC utíkají a zamykají dveře | [Z9 v reserse_postavy] |
| obchodník | metarole vítání v obchodě, repliky při velkém nákupu (nad 20 % ceny zboží), smlouvání podle pověsti a podezřelosti zboží | [R13][R3][R16] |
| prohledání stráží | při nízké pověsti u vojáků | [R16] |

### 3.2 Rozdíly podle role
- **Sedlák při práci:** soustředěný, okolí moc nevnímá. V KCD sedláci v lijáku dál zametají [Z12 v reserse_postavy].
  Podle naší současné logiky (soustředění 0,8 → šance pohledu ×0,2) ho hráč vyruší hlavně zblízka.
  KCD má okamžité zjištění do 2,5 m [R3].
- **Dítě:** v KCD2 děti **nejsou vůbec**. Vývojáři uvádějí náročnost a hodnocení věkové přístupnosti [R26].
  Nemáme pro ně model, proto ho zatím nedělat. Kdyby přibylo: zvědavost 0,9, strach 0,6, mluvnost 0,2 (*odhad*).
- **Stráž:** roli v zločinu má `soldier` [R10]. Nízká pověst = zastavuje a prohledává [R16]. Hráče špinavého
  a zakrváceného přesvědčí hůř [R17]. Tasenou zbraň trestá [R25].
- **Kněz:** v KCD1 patří k urozeným (`Priest`) [R12]. Na nečistotu reaguje jako vyšší třída [R17] (*odhad*).
  Mši a modlitby má v rozvrhu (viz reserse_postavy).
- **Žebrák:** neurozený (`Beggar`) [R12]. Jak oslovuje hráče, KCD dokumentace neuvádí (*odhad*: prosí o almužnu
  urozeně oblečeného, sedláka nechá být).
- **Obchodník:** vítá v obchodě, komentuje velký nákup, při nízké pověsti nesmlouvá, s cejchovaným neobchoduje
  [R13][R3][R16][R21].

---

## 4. Vzdálenosti a časy (shrnutí pro data)
| Co | KCD2 | Zdroj | Pro nás (`postavy.json`) |
|---|---|---|---|
| zorné pole | 90–100° | [R3] | 100° vnější kužel, vnitřní 40–100 % podle nervozity |
| okamžité zjištění | 2,5 m | [R3] | 2,5 m (všimne si i soustředěný) |
| dohled ve dne | 2,5 + 1,35·(zrak−1), max 50 m | [R3][R11] | podle role 12–22 m (*odhad* zraku 8–15) |
| dohled v noci | nejvýš ½ | [R3] | ×0,5, s pochodní u hráče ×1 (*odhad*) |
| stav hráče pozná | do 40 % dohledu | [R3] | 0,4·dohled (5–9 m) |
| rozpoznání | 2–8 s podle nápadnosti | [R3] | 2–8 s, za hranicí dohledu −0,5/s |
| zapomene, když zmizí | 4 s | [R3] | 4 s |
| pohled na hráče | neuvedeno | – | stávající 3–6 s, pak 4–9 s jinam |
| cooldown repliky | per sekvence v herním čase, −1 = jednou | [R8] | čísla níže (*odhad*) |
| počet replik za minutu ve vsi | neuvedeno; hráči si v KCD1 stěžovali na přemíru pozdravů | [R24] | max. 4 za minutu na celou ves (*odhad*) |
| nervozita | opadne za ~2,4 herní hodiny, šíří se do 10 m, odvážní ½ | [R3] | `nervozita` |
| hněv vsi | opadne za ~1,5 dne, nad 0,67 nosí zbraně, projeví se po 12 h | [R3] | `hnev_vsi` |
| šíření pověsti do vsi | 3 h ± 0,5 h | [R3] | 3 herní hodiny |

Výpočet poklesu (*výklad*): Warhorse u nervozity píše „1e-5 = pokles 1→0 asi za den“, takže 1e-4 ≈ 2,4 h.
U hněvu „1e-6 = asi 12 dní“, takže 8e-6 ≈ 1,5 dne [R3].

---

## 5. Paměť NPC
- **Osobní pověst** každého NPC se uloží a sama neopadá. Do vsi se propíše za 3 h [R9][R3].
- **Informace o zločinu** se šíří frakcí. Platnost je `InformationExpirationBase` 1 den × modifikátor zločinu
  z `crime.xml` (napadení má `expiration="5"`, tedy ~5 dní, *výklad*). Šíří se jednou za den
  (`InformationBroadcastPeriod`), ale ne NPC do 30 m od hráče (`…IgnoreRadius`). Čerstvá zpráva se šíří po 0,3 min.
  Stejná informace se po 30 s bere jako nová [R3][R6].
- **Kradené zboží** se „zapomíná“ podle ceny (0,015 herní h na decigroš) a vzdálenosti. Do 600 m od místa krádeže
  je podezření nejvyšší, nad 1800 m nejnižší [R3].
- **Hledaný** (wanted) se drží asi 7 herních dní [R22]. Podle hráčů stráž zapomene asi po týdnu, nebo za pár dní
  (nejednotné) [R21].
- **Poznání tváře** jako samostatný systém KCD nemá. Pozná se rozpoznáním (kap. 2.2) a skutečnou frakcí zblízka
  (kap. 2.4). Hráči ale hlásí, že **okradený tě pozná i po dlouhé době a spustí poplach** [R21]. Osobní paměť je
  vázaná na duši NPC, ne na obličej.
- **Pomoc** zvedá osobní i skupinovou pověst (úkoly, obrana před lapky) a změna se rozšíří [R16]. Jak se liší
  repliky při vysoké pověsti, není doložené. Hráči v KCD1 hlásí, že je lidé ignorují i s pověstí 50–100 [výpis R24].

---

## 6. Návrh pro `pravidla/svet/postavy.json`

**Zásady:** rozšiřuje stávající formát, `zvedavost` a `soustredeni` zůstávají. Všechna čísla jsou v datech, v kódu
žádná (pravidlo „záplatování zakázáno“). Pořadí reakcí je pevné a první platná vyhrává, jako priority témat
v KCD [R8]. Stávající vzorec `zvedavost × (1 − soustredeni)` zůstává jako poslední řádek tabulky („jen pohled“).

### 6.1 Vnímání (nová sekce)
```json
"vnimani": {
  "_popis": "reserse_reakce_kcd2.md kap. 2 a 4 (KCD2 rpg_param, Warhorse 14. 1. 2025)",
  "zorne_pole_st": 100.0,
  "vnitrni_kuzel": [0.4, 1.0],
  "_vnitrni_kuzel": "podil zorneho pole: klidna postava 0.4, s nervozitou 1 az plne (PerceptionInnerCone)",
  "hned_m": 2.5,
  "dohled_strop_m": 50.0,
  "noc_dohled": 0.5,
  "pochoden_noc_dohled": 1.0,
  "stav_pozna_podil": 0.4,
  "rozpoznani_s": {"zaklad": 4.0, "napadny": -2.0, "nenapadny": -4.0},
  "_rozpoznani_s": "T = zaklad + koef*napadnost (napadnost -1..1): 2 s napadny, 8 s nenapadny",
  "zapomene_s": 4.0,
  "pokles_mimo_dohled_za_s": 0.5,
  "dav_lidi": 4,
  "dav_m": 3.0,
  "pozornost": {"hrac": 1.0, "zbran_v_ruce": 0.3, "luk_v_ruce": 1.25, "napadnost": 0.3,
                "pritel": -0.2, "cizi_pohlavi": 0.1, "mrtvy": 1.25, "kradez": 0.6},
  "_pozornost": "vahy z KCD2 PerceptionPrior* vydelene PriorBoostPlayer 20 (zbran 6/20, luk 6*4.2/20, napadnost 6/20 za bod, pritel -4/20, mrtvy 25/20, kradez 12/20)",
  "nervozita": {"sireni_m": 10.0, "sireni_podil": 0.1, "pokles_h": 2.4, "odvazny_podil": 0.5},
  "hnev_vsi": {"pokles_dni": 1.5, "zbrane_od": 0.67, "projevi_se_h": 12.0},
  "repliky": {"ves_max_za_min": 4, "ves_odstup_s": 12.0, "postava_odstup_s": 45.0,
              "pozdrav_znovu_h": 2.0, "stav_znovu_h": 1.0, "dosah_m": 8.0},
  "_repliky": "odstup = cooldown sekvence (KCD Dialog System); cisla *odhad*: KCD1 mel pozdravu prilis (forum), proto pozdrav jedne postavy nejvys za 2 herni hodiny"
}
```
Rozhodnutí postavy při vstupu hráče do dohledu (*výklad* KCD, převedeno na náš model):
1. `dohled_m = hned_m + (zrak_m − hned_m) · (noc ? noc_dohled : 1)`; hráč s pochodní v noci → `pochoden_noc_dohled`.
2. Hráč musí být ve vnitřním kuželu (`zorne_pole_st · vnitrni_kuzel` podle nervozity) nebo blíž než `hned_m`.
3. Když je hráč v hloučku `dav_lidi` (4+ lidé do `dav_m`), postavy, které nejsou přímo u něj, ho nevnímají.
4. Rozpoznání roste po dobu `T` s, mimo dohled klesá. Při 100 % se vyhodnotí tabulka reakcí (6.5).
5. Šance pouhého pohledu = `clamp(zvedavost·(1−soustredeni) + pozornost·(1 − 0,5·soustredeni), 0, 1)`.
   Kód z ní pak vybere klip a dobu pohledu jako dnes.

### 6.2 Povaha role (rozšíření `role`)
Hodnoty 0–1, *odhad* podle KCD tříd [R12] a historie vsi 1393. `trida`: `nizka` nebo `vyssi`, podle `HighbornWealthThreshold`.
| Role | zvědavost | ostražitost | úcta | strach | mluvnost | zrak_m | třída | poznámka |
|---|---|---|---|---|---|---|---|---|
| `sedlak` | 0,30 | 0,40 | 0,60 | 0,40 | 0,35 | 16 | nízká | stávající zvědavost |
| `selka` | 0,45 | 0,45 | 0,60 | 0,55 | 0,55 | 15 | nízká | víc mluví, víc se bojí krve |
| `rychtar` | 0,70 | 0,75 | 0,45 | 0,20 | 0,60 | 20 | vyšší | KCD Bailiff je urozený [R12]; vyptává se cizích |
| `lamac` | 0,15 | 0,25 | 0,40 | 0,30 | 0,20 | 14 | nízká | hluk a prach, soustředěný |
| `celedin` | 0,20 | 0,30 | 0,70 | 0,50 | 0,25 | 16 | nízká | spěchá, uhýbá |
| `dvorka` (děvečka) | 0,50 | 0,35 | 0,80 | 0,65 | 0,40 | 15 | nízká | stydlivá, sklopí oči |
| `mlynar` | 0,35 | 0,60 | 0,50 | 0,30 | 0,50 | 15 | nízká | KCD Miller je neurozený [R12]; hlídá obilí; `obchodnik: true` |
| `straz` (nová) | 0,50 | 0,90 | 0,30 | 0,10 | 0,30 | 22 | nízká | `zlocin_role: "vojak"` (KCD `soldier` [R10]) |

```json
"sedlak":  {"nazev": "sedlák",  "zvedavost": 0.3,  "ostrazitost": 0.4,  "ucta": 0.6,  "strach": 0.4,  "mluvnost": 0.35, "zrak_m": 16.0, "trida": "nizka"},
"selka":   {"nazev": "selka",   "zvedavost": 0.45, "ostrazitost": 0.45, "ucta": 0.6,  "strach": 0.55, "mluvnost": 0.55, "zrak_m": 15.0, "trida": "nizka"},
"rychtar": {"nazev": "rychtář", "zvedavost": 0.7,  "ostrazitost": 0.75, "ucta": 0.45, "strach": 0.2,  "mluvnost": 0.6,  "zrak_m": 20.0, "trida": "vyssi", "privola_ho": true},
"lamac":   {"nazev": "lamač kamene", "zvedavost": 0.15, "ostrazitost": 0.25, "ucta": 0.4, "strach": 0.3, "mluvnost": 0.2, "zrak_m": 14.0, "trida": "nizka"},
"celedin": {"nazev": "čeledín", "zvedavost": 0.2,  "ostrazitost": 0.3,  "ucta": 0.7,  "strach": 0.5,  "mluvnost": 0.25, "zrak_m": 16.0, "trida": "nizka"},
"dvorka":  {"nazev": "děvečka na tvrzi", "zvedavost": 0.5, "ostrazitost": 0.35, "ucta": 0.8, "strach": 0.65, "mluvnost": 0.4, "zrak_m": 15.0, "trida": "nizka"},
"mlynar":  {"nazev": "mlynář",  "zvedavost": 0.35, "ostrazitost": 0.6,  "ucta": 0.5,  "strach": 0.3,  "mluvnost": 0.5,  "zrak_m": 15.0, "trida": "nizka", "obchodnik": true},
"straz":   {"nazev": "stráž",   "zvedavost": 0.5,  "ostrazitost": 0.9,  "ucta": 0.3,  "strach": 0.1,  "mluvnost": 0.3,  "zrak_m": 22.0, "trida": "nizka", "zlocin_role": "vojak"}
```
Význam: **ostražitost** = jak brzy reaguje na podezřelé (noc, zbraň, cizí dům) a jak široký má vnitřní kužel
bez nervozity. **Úcta** = jak silně reaguje na urozený vzhled (zastaví, kývne, uhne). **Strach** = práh útěku
a ustoupení. **Mluvnost** = šance, že z platné reakce řekne repliku, místo aby jen gestikulovala.
`strach` stráže 0,1 odpovídá `courage` duše a `NervousnessCourageousWeight` 0,5 [R3][R7].

### 6.3 Soustředění činnosti (doplnit do `cinnosti`)
Stávající hodnoty nechat: `zahon` 0,8, `prace_lom` 0,9, `nosi` 0,85, `mleti` 0,7, `hovor` 0,6, `rano` 0,3,
`odpocinek` 0,2, `dohled` 0,0. Pro nové činnosti z reserse_postavy (*odhad*):
`kovani` 0,9, `pytle` 0,85, `stipani` 0,85, `krmeni` 0,6, `voda` 0,5, `cepovani` 0,5, `lavice` 0,15, `mse` 0,95
(v kostele nereaguje), `straz_brana` 0,0 a `straz_obchuzka` 0,1 (dívat se je jeho práce, chování nese ostražitost).
Soustředění nikdy neruší `hned_m`: do 2,5 m si všimne každý [R3].

### 6.4 Hráč (vstupy reakcí; zatím jen pověst a vzhled, dovednosti později)
```json
"hrac_dojem": {
  "_popis": "co z hrace postava vidi (KCD2: charisma = prumer viditelnych kusu, trida podle 1/3 vystroje, stav jen do 0.4 dohledu)",
  "vzhled": {
    "sedlacky": {"trida": 0.0, "napadnost": -0.3},
    "mestsky":  {"trida": 0.5, "napadnost": 0.0},
    "pansky":   {"trida": 1.0, "napadnost": 0.4},
    "zbroj":    {"trida": 0.8, "napadnost": 0.6},
    "kosile":   {"trida": 0.0, "napadnost": 0.8, "stav": "nahy"}
  },
  "trida_podil_vystroje": 0.333,
  "cistota": {"cisty_do": 0.25, "spinavy_od": 0.5, "smrdi_od": 0.8, "krev_vidi_od": 0.3,
              "trida_za_spinu": -0.8, "_trida_za_spinu": "ArmorDirtToCharismaCoef 0.8: spina snizuje dojem tridy"},
  "zbran": {"zadna": 0.0, "u_pasu": 0.1, "v_ruce": 0.3, "luk_v_ruce": 1.25},
  "noc_bez_svetla_napadnost": 0.3,
  "povest": {"vychozi": 0.5, "prahy": [0.2, 0.4, 0.6, 0.8],
             "_prahy": "KCD2 ikony: nepratelska / chladna / neutralni / pratelska / vrela",
             "vaha_osobni": 5, "vaha_ves": 3, "vaha_kraj": 1, "sireni_h": [2.5, 3.5], "sireni_max": 0.15}
}
```
- `trida_vnimana = vzhled.trida + cistota.trida_za_spinu · max(0, spina − cisty_do)`, oříznuto na 0–1.
  Urozený, ale zablácený je tak „pán v nesnázích“ (*odhad* podle `ArmorDirtToCharismaCoef`).
- Paměť jednotlivce (doplnit k `obyvatele` za běhu, ne do dat):
  `pamet: [{"druh": "kradez|napadeni|vniknuti|pomoc", "sila": 0–1, "kdy_h": …}]`.
  Platnost (*výklad* `crime.xml`): `kradez` 1 den, `napadeni` 5 dní, `vniknuti` 2 h, `pomoc` bez konce
  (pověst neopadá [R9]).

### 6.5 Tabulka reakcí (první platná vyhrává)
`p` = pověst ve vsi (vážený medián), `t` = vnímaná třída, `d` = vzdálenost, `D` = dohled postavy.
Klipy jsou z `UAL1/UAL2` (seznam v reserse_postavy kap. 3.1).
| # | Podmínka | Kdo | Reakce | Klip UAL | Replika (klíč) |
|---|---|---|---|---|---|
| 1 | útok nebo mrtvola na dohled | strach ≥ 0,4 | útěk domů, zavřít dveře, nervozita +1 | `Hit_Knockback` → `Sprint_Loop` → `Interact` | `utek` |
| 1b | totéž | `straz` | tasit, jít k hráči | `Sword_Idle` / `Idle_Shield_Loop` | `straz_stuj` |
| 2 | zbraň v ruce a d ≤ 8 m | strach ≥ 0,5 | ustoupit o 3 m, sledovat 4–8 s | `Walk_Loop` (couvá) → `Idle_FoldArms_Loop` | `zbran` |
| 2b | zbraň v ruce a d ≤ 10 m | `straz` | varovat, po 5 s jít k hráči | `Idle_No_Loop` | `straz_zbran` |
| 3 | hráč v domě postavy nebo za jejím pultem | majitel | varovat, pak po 5 s volat (*odhad*; hráči uvádějí „pár sekund“ [R20]) | `Idle_No_Loop` → `Idle_Rail_Call` | `vniknuti_1` → `vniknuti_2` |
| 3b | hráč v cizím domě | soused s ostražitostí ≥ 0,5 | zavolat rychtáře nebo stráž, ukazovat | `Idle_Rail_Call` | `volani` |
| 4 | v paměti `kradez`/`napadeni` a d ≤ 0,4·D | každý | poznat, volat rychtáře, nervozita +0,5 | `Idle_Rail_Call` | `poznal_zlodeje` |
| 5 | p < 0,2 | každý | nepozdraví, obejde hráče obloukem, pohled 1–2 s | `Walk_Loop` | `odvraceni` (mluvnost × 0,5) |
| 6 | noc, hráč bez světla, d ≤ D | ostražitost ≥ 0,5 | zastavit, ptát se „kdo tam“ | `Idle_Lantern_Loop` (má-li lucernu) / `Idle_Loop` | `noc` / `straz_noc` |
| 7 | krev ≥ 0,3 a d ≤ 0,4·D | každý | úlek, strach ≥ 0,5 ustoupí | `Hit_Knockback` → `Idle_Loop` | `krev` |
| 8 | smrdí a d ≤ 3 m (pachový kruh [R18]) | každý mimo soustředění ≥ 0,85 | odvrátit hlavu, komentář | `Idle_No_Loop` | `smrad` |
| 9 | opilý nebo nahý a d ≤ 0,4·D | mluvnost ≥ 0,3 | komentář, krátký pohled | `Idle_FoldArms_Loop` | `opily` / `nahy` |
| 10 | t ≥ 0,7, p ≥ 0,4, d ≤ 5 m, úcta ≥ 0,5 | každý mimo soustředění ≥ 0,85 | zastavit práci, kývnout (úklona), uhnout z cesty `uhyb_hrac_m` | `Yes` | `pozdrav_pan` |
| 11 | obchodník, hráč stojí ≤ 3 m déle než 2 s | `mlynar` | nabídnout zboží | `Idle_Talking_Loop` | `nabidka_mlynar` |
| 12 | `pomoc` v paměti nebo p ≥ 0,8, d ≤ 5 m | mluvnost ≥ 0,3 | vřelý pozdrav | `Yes` | `pozdrav_vrely` |
| 13 | 0,4 ≤ p, d ≤ 5 m, náhoda < mluvnost × (1 − soustředění) | každý | běžný pozdrav (podle denní doby) | `Yes` | `pozdrav` / `pozdrav_vecer` |
| 14 | 0,2 ≤ p < 0,4, d ≤ 5 m | mluvnost ≥ 0,4 | nevrlé zamručení | `Idle_FoldArms_Loop` | `nevrly` |
| 15 | jinak | každý | jen pohled (šance z 6.1 bod 5), 3–6 s | LookAt hlavy | – |

Pravidla tabulky:
- **Cooldowny:** pozdrav (10, 12, 13) stejné postavy nejvýš jednou za `pozdrav_znovu_h` = 2 herní hodiny (7,5 min).
  Komentář ke stavu (7–9) jednou za `stav_znovu_h` = 1 herní hodinu. Jakákoli replika postavy nejdřív po 45 s.
  Celá ves nejvýš 4 repliky za minutu a mezi dvěma replikami aspoň 12 s (*odhad*).
- Řádky 1–4 cooldown nemají, jde o bezpečnost.
- Čeledín při práci (`nosi` 0,85) se dostane jen k řádkům 1–4. Lamač (0,9) stejně a navíc k 8 („pozor, kámen“
  místo pozdravu).
- Řádek 10 je jediný, kde postava kvůli hráči přeruší činnost. Vrátí se po 2–3 s.

### 6.6 Repliky (česky, archaizující, bez novověkých tvarů)
Nepoužívat: „Pochválen buď Ježíš Kristus“ (rozšířilo se až po odpustku Sixta V. z roku 1587 [R27]),
„ahoj“, „milostpane“, „pane vrchní“ a podobně. Lidové pozdravy s Bohem („pozdrav Pánbůh“, „pomáhej Pánbůh“,
„dej Pánbůh dobrý den“, z něhož zbylo „dobrý den“) jsou doložené jako staré [R28]. Repliky jsou moderní čeština
s dobovým slovníkem, stejně jako český dabing KCD (*odhad*). Starou češtinu by nikdo nerozuměl.
```json
"repliky": {
  "pozdrav":        ["Pomáhej Bůh.", "Dej Bůh dobrý den.", "Pozdrav Bůh."],
  "pozdrav_vecer":  ["Dej Bůh dobrý večer.", "Dobrou noc dej Bůh."],
  "pozdrav_pan":    ["Pozdrav Bůh, urozený pane.", "Dej Bůh dobrý den, milostivý pane.", "Pokorně se klaním, pane."],
  "pozdrav_vrely":  ["Bůh vám zaplať, žes nám pomohl!", "Rád tě vidím, příteli.", "Ať se ti daří, dobrý člověče."],
  "nevrly":         ["Hm.", "Jdi si po svém.", "Co zas?"],
  "odvraceni":      ["S tebou mluvit nebudu.", "Táhni, odkuds přišel.", "Lotr jeden."],
  "krev":           ["Hospodine, vždyť krvácíš!", "Kdo tě tak zřídil?", "Pro Bůh, krev!"],
  "smrad":          ["Fuj, táhne z tebe jak z chlíva.", "Umyj se, než přijdeš mezi lidi.", "Smrdíš jak kozel."],
  "opily":          ["Ten se v krčmě nešetřil.", "Hle, opilec.", "Vyspi se z toho, chlape."],
  "nahy":           ["Styď se, chlape!", "Kde máš šaty, nešťastníku?"],
  "zbran":          ["Schovej to železo, ať není zle.", "Co máš za lubem s tím mečem?"],
  "vniknuti_1":     ["Co tu pohledáváš? Ven z mého stavení!", "Kdo tě sem zval?"],
  "vniknuti_2":     ["Ven, nebo zavolám rychtáře!", "Zloděj! Lidé, zloděj ve stavení!"],
  "volani":         ["Rychtáři! Pojďte sem!", "Biřici, sem!"],
  "poznal_zlodeje": ["To je on, ten, co kradl!", "Tebe znám, lotře!"],
  "utek":           ["Pomoc! Vraždí!", "Lidé, utečte!", "Bože, smiluj se!"],
  "noc":            ["Kdo tam? Ukaž se!", "Kdo se tu plíží po tmě?"],
  "nabidka_mlynar": ["Mouky by bylo, pane, čerstvě semleté.", "Potřebuješ mouku? Za groš ti nasypu."],
  "lamac":          ["Pozor, padá kamení!", "Nepleť se tu, ať tě kámen nezavalí."],
  "celedin":        ["S dovolením, nesu.", "Uhněte, pane, je to těžké."],
  "dvorka":         ["Pane…", "Dej Bůh dobrý den.", "Jdu, jdu, paní volá."],
  "rychtar":        ["Kdo jsi a co ve vsi hledáš?", "Ve vsi je klid, pane. Ať tak zůstane."],
  "straz_stuj":     ["Stůj!", "Ani hnout!"],
  "straz_zbran":    ["Meč do pochvy, hned!", "Schovej zbraň, nebo půjdeš do klády."],
  "straz_noc":      ["Stůj! Kdo jsi a kam jdeš po tmě?", "Ukaž se ke světlu!"],
  "straz":          ["Jdi s Bohem.", "Ať je klid."]
}
```
Role si mohou repliku přepsat vlastním klíčem: `lamac` místo `pozdrav`, `celedin` při `nosi`, `rychtar` u cizího
s p < 0,6. Je to stejný princip jako v KCD, kde vlastní monolog s vyšší prioritou přebije systémový [R7].
„Groš“ odpovídá době: pražský groš se razí od roku 1300. „Klády“ jsou dobový trest (kláda = pouta).

---

## 7. Napojení na stávající kód (jen popis, nic neměněno)
- `scripts/lide.gd` ř. 399–405: dnešní šanci pohledu nahradit vzorcem z 6.1 bod 5. Všechny vstupy číst z dat
  (`vnimani`, `role`, `cinnosti`, `hrac_dojem`).
- Tabulka 6.5 jako pole záznamů `{"id", "kdo", "podminka", "reakce", "klip", "replika", "cooldown"}` v `postavy.json`.
  Podmínky omezit na pevný seznam klíčů (`d_m`, `p`, `t`, `noc`, `zbran`, `krev`, `smrdi`, `opily`, `v_dome`,
  `pamet`, `soustredeni`). Žádné výrazy v kódu.
- Test (vrstva hlídačů v `docs/pipeline.md`): každá role musí mít všech pět vlastností a každý klíč repliky musí
  existovat. Každý klip musí být v `UAL1/UAL2`. Pořadí reakcí: řádky bezpečnosti (1–4) před pozdravy.

---

## Shrnutí v 10 bodech
1. **KCD2 má vnímání v oficiálních tabulkách** (Warhorse, `rpg_param` a statistiky duše) [R3][R4]. Čísla jsou
   převzatelná, časy v herním čase převádíme 1 : 1 (KCD 15×, my 16×).
2. **Ne každý se dívá:** NPC vybírá cíl podle priority. Hráč 20, zbraň 6, luk 25, nápadnost 6 za bod, přítel −4,
   mrtvola 25. V hloučku 4+ lidí je hráč pro vedlejší vnímání neviditelný [R3].
3. **Zorné pole 90–100°**, klidné NPC vnímá jen vnitřní kužel (40 %), nervózní celý. Do 2,5 m si všimne každý [R3].
4. **Dohled = 2,5 + 1,35·(zrak−1) m**, nejvýš 50 m, v noci nejvýš polovina. Pro nás 12–22 m podle role [R3][R11].
5. **Rozpoznání trvá 2–8 s** podle nápadnosti (výchozí 4 s). Stav hráče (krev, opilost, nahota, pach) pozná jen do
   40 % dohledu, proto komentáře jen zblízka [R3].
6. **Šaty dělají člověka doloženě:** víc než třetina výstroje určí vnímanou třídu. Charisma je průměr viditelného
   oblečení, srážejí ho špína a krev. Na urozeného se v malé vsi reaguje (KCD1), v KCD2 se to ve městě ztratilo
   [R3][R15][R23].
7. **Pach od špíny 0,8, čistý do 0,25.** Pach je kruh kolem hráče, který ho prozradí i bez zraku. Krev a špína
   pomáhají zastrašit [R3][R18].
8. **Pověst 0–1 s prahy 0,2/0,4/0,6/0,8.** Osobní × ves × kraj v poměru 5 : 3 : 1, do vsi se propíše za 3 h a sama
   neopadá. Nervozita opadá za ~2,4 h, hněv vsi za ~1,5 dne a nad 0,67 lidé nosí zbraně [R3][R9].
9. **Repliky jsou monology s cooldownem v herním čase** a s metarolemi (pozdrav, vítání v obchodě, komentář ke stavu,
   vniknutí). V KCD1 jich bylo příliš, proto u nás pozdrav jedné postavy jen jednou za 2 h a celá ves nejvýš
   4 repliky za minutu [R7][R8][R13][R24].
10. **Návrh pro `postavy.json`:** `vnimani` (globální čísla), u role pět vlastností + `zrak_m` + `trida`, u činnosti
    `soustredeni`, `hrac_dojem` (vzhled, čistota, zbraň, pověst), tabulka 15 reakcí v pevném pořadí s klipy UAL
    a dobové repliky bez „Pochválen buď“ (to je až z roku 1587).

---

## Zdroje
- [R1] Nexus Mods Wiki: RPG params in KCD (úplný seznam s výchozími hodnotami, patch 1.4), https://wiki.nexusmods.com/index.php/RPG_params_in_KCD ; archiv https://web.archive.org/web/20250518235219/https://wiki.nexusmods.com/index.php/RPG_params_in_KCD
- [R2] Xylozi: [Tutorial] Tweaking RPG Parameters (komentáře k parametrům, #perception), https://forums.nexusmods.com/topic/6409661-tutorial-tweaking-rpg-parameters/ ; archiv https://web.archive.org/web/20250802084239/https://forums.nexusmods.com/topic/6409661-tutorial-tweaking-rpg-parameters/
- [R3] Warhorse Studios: KCD2 Modding – RPG Constants/Params (export 14. 1. 2025, popis + jednotky), https://warhorse.youtrack.cloud/articles/KM-A-20 (čteno přes API https://warhorse.youtrack.cloud/api/articles/KM-A-20?fields=content)
- [R4] Warhorse Studios: KCD2 Modding – Stats and skills (odvozené statistiky `charisma`, `vib`, `con`, `noi`, `drt`, `sml`, `bld`, `brn`), https://warhorse.youtrack.cloud/articles/KM-A-21
- [R5] Warhorse Studios: Modifying RPG parameters and NPC stats (buff pranýře `charisma-4,con+0.4`, 2400 s), https://warhorse.youtrack.cloud/articles/KM-A-84/Modifying-RPG-parameters-and-NPC-stats
- [R6] Warhorse Studios: Crime (`crime.xml` expiration/fine/jail/scalingWithSocialClass, `crime_longTermMemoryTrespassExpiration` 7200), https://warhorse.youtrack.cloud/articles/KM-A-27
- [R7] Nexus Mods Wiki: NPCs, Souls, Roles, Metaroles, Characters, Brains Documentation (tabulka soul, KOMENTAR_NA_JINDRU, trespass komentáře, npc_daycycle), https://wiki.nexusmods.com/index.php/NPCs,_Souls,_Roles,_Metaroles,_Characters,_Brains_Documentation
- [R8] Nexus Mods Wiki: Dialog System Documentation (typy Greeting/InGame monolog, cooldown sekvence, priority), https://wiki.nexusmods.com/index.php/Dialog_System_Documentation
- [R9] Nexus Mods Wiki: Factions, Superfactions Documentation (osobní a frakční pověst, hněv opadá, pověst ne), https://wiki.nexusmods.com/index.php/Factions,_Superfactions_Documentation
- [R10] Nexus Mods Wiki: Buffs in KCD (Lowborn/Highborn, VersusSoldier, Night, LocalHero, ManlyOdour, Drunkenness), https://wiki.nexusmods.com/index.php/Buffs_in_KCD
- [R11] Let's Play with Fire Wiki (fireundubh): Stats – vzorce ViewRadius, FieldOfView, Visibility, Conspicuousness, https://wiki.fireundubh.com/kingdomcome/stats ; archiv https://web.archive.org/web/20250823151640/https://wiki.fireundubh.com/kingdomcome/stats
- [R12] Let's Play with Fire Wiki: Social Classes (Highborn/Lowborn, 421 duší), https://wiki.fireundubh.com/kingdomcome/social-classes ; archiv https://web.archive.org/web/20250824041052/https://wiki.fireundubh.com/kingdomcome/social-classes
- [R13] Nexus Mods KCD2: NPC Reactions (metarole NPC_ZDRAVI_HRACE, NPC_VITA_HRACE_V_OBCHODE; komentáře opilý/zraněný/nahý/páchnoucí, pes, kůň), https://www.nexusmods.com/kingdomcomedeliverance2/mods/1118 ; archiv https://web.archive.org/web/20250720195852/https://www.nexusmods.com/kingdomcomedeliverance2/mods/1118
- [R14] Nexus Mods KCD1: NPCs complain less when bumped, https://www.nexusmods.com/kingdomcomedeliverance/mods/525 ; fórum: NPCs No Complaints + No Greetings, https://forum.kingdomcomerpg.com/t/rls-npcs-no-complaints-1-1-no-greetings-v1-update-1-6-x/59681
- [R15] KCD Wiki (wiki.gg): Character Stats (charisma = průměr viditelného oblečení, nápadnost, viditelnost, hluk), https://kingdomcomedeliverance.wiki.gg/wiki/Character_Stats ; výpis vyhledávače k nápadnosti (luk, kabátec 46→27), https://www.powerpyx.com/kingdom-come-deliverance-how-to-level-up-all-stats-skills/ , https://segmentnext.com/2018/02/21/kingdom-come-deliverance-stealth
- [R16] KCD Wiki (wiki.gg): Reputation (skupiny ve vsi, obchodník 50, prohledávání stráží), https://kingdomcomedeliverance.wiki.gg/wiki/Reputation
- [R17] Gamer Guides KCD1: Appearance matters (špína ztěžuje přesvědčení stráží a vysokého postavení), https://www.gamerguides.com/kingdom-come-deliverance/introduction/useful-gameplay-tips/appearance-matters
- [R18] PC Gamer: KCD2 body-odour broadcasting, https://www.pcgamer.com/games/rpg/ugh-kingdom-come-deliverance-2-has-a-body-odour-broadcasting-system-where-your-stink-can-alert-nearby-npcs/ ; GamesRadar (O. Bittner), https://www.gamesradar.com/games/rpg/kingdom-come-deliverance-2-trades-skyrim-stealth-archers-for-stinky-smelly-archers-you-can-get-so-filthy-that-npcs-catch-you-broadcasting-body-odor-so-wash-your-hands-kids/
- [R19] Deltia's Gaming: KCD2 Behavior Indicators, https://deltiasgaming.com/kingdom-come-deliverance-2-behavior-indicators-explained/ ; GameRant: hare icons, https://gamerant.com/kingdom-come-deliverance-2-all-behaviour-indicators-explained-hare-bunny/
- [R20] Steam diskuse KCD2/KCD1 o vniknutí a podezření (hráčské postřehy z výpisu vyhledávače), https://steamcommunity.com/app/1771300/discussions/0/601896014188651543 , https://steamcommunity.com/app/1771300/discussions/0/601895917151375439 , https://steamcommunity.com/app/379430/discussions/0/4150581887537763694 , https://steamcommunity.com/app/379430/discussions/0/2566438616663658288
- [R20b] Deltia's Gaming: Crime and Reputation Explained (pochodeň v noci), https://deltiasgaming.com/?p=134932
- [R21] PC Gamer: branded a criminal, https://www.pcgamer.com/games/rpg/i-messed-up-so-bad-in-kingdom-come-deliverance-2-that-i-was-literally-branded-a-criminal-and-hours-later-im-still-shunned-by-society/ ; Prima Games: Branded, https://primagames.com/tips/kingdom-come-deliverance-2-branded-and-other-punishments-effects ; fórum: jak dlouho stráže zapomínají, https://forum.kingdomcomerpg.com/t/how-long-before-guards-forget-that-you-murdered-someone/69647 ; Steam https://steamcommunity.com/app/1771300/discussions/0/601895505111380640
- [R22] GamerBlurb: Wanted Status and Crime Explained KCD2 (7 dní), https://gamerblurb.com/articles/wanted-status-and-crime-explained-kcd2-kingdom-come-deliverance-2
- [R23] Gamewave: KCD2 – hráči rozděleni po odebrání reakce na vzhled (rytíř ve zbroji), https://gamewave.fr/kingdom-come-deliverance-2/kingdom-come-deliverance-2-les-joueurs-divises-apres-la-suppression-d-une-fonctionnalite-immersive/
- [R24] Fórum KCD: Constant greetings ruining immersion, https://forum.kingdomcomerpg.com/t/constant-greetings-ruining-imersion/49294 ; Mod request: no NPC greetings, https://forum.kingdomcomerpg.com/t/mod-request-no-npc-greetings/52531 ; Steam (pověst 50–100 a stejně ignorují), https://steamcommunity.com/app/379430/discussions/0/1642038749331747502
- [R25] Steam KCD2/KCD1: tasená zbraň ve městě (hráčské postřehy), https://steamcommunity.com/app/1771300/discussions/0/732500746974584107 , https://steamcommunity.com/app/1771300/discussions/0/600771424734428346 , https://steamcommunity.com/app/379430/discussions/0/4939856028585081707
- [R26] ScalaCube: KCD2 dev explains lack of children, https://scalacube.com/blog/news/kingdom-come-deliverance-2-dev-explains-games-lack-of-children ; Automaton, https://automaton-media.com/articles/newsjp/kingdomcome-deliverance-2-20250419-335768/
- [R27] Wikipedia: Laudetur Jesus Christus (odpustek Sixta V. 1587), https://en.wikipedia.org/wiki/Laudetur_Jesus_Christus
- [R28] Dějiny lidové kultury (pozdravy „pozdrav pánbůh“, „pomáhej pánbůh“, „dej pánbůh dobrý den“), https://www.iumeni.cz/books/part/dejiny-lidova-kultura.pdf ; Karlíková H.: pozdravy se jménem Boha (zdařbůh, pozdrav tě bůh), https://digilib.phil.muni.cz/_flysystem/fedora/pdf/138234.pdf
- [R29] Wccftech: KCD2 dev talks about dynamic NPC routines (Ziegler: po násilí zůstávají doma, nosí zbraň), https://wccftech.com/kingdom-come-deliverance-2-dev-talks-about-dynamic-npc-routines-and-emergent-storytelling-for-side-quests/amp/
- [R30] GameStar: KCD2 Ruf verbessern (sedlák vs. šlechtic, pověst po regionech), https://www.gamestar.de/artikel/kingdom-come-2-ruf-verbessern-guide,3426275.html ; Destructoid (pověst v menu, může být záporná), https://vip-develop.destructoid.com/?p=1016557
- [R31] Nerdburglars: Henry smells bad (stráže a NPC komentují zápach), https://nerdburglars.net/question/why-does-henry-smell-bad-and-ruin-sneaking-even-after-washing-everything/ ; [R31b] Gfinity: šlechtic si zacpe nos, https://www.gfinityesports.com/article/kcd-2s-henry-is-exactly-how-i-like-my-rpg-men%E2%80%94raw-unhinged-scruffy
- [R32] Sportskeeda: Charisma in KCD2 explained (průměr viditelných kusů), https://sportskeeda.com/esports/charisma-kingdom-come-deliverance-2-explained
- [Z9], [Z12] = zdroje z `docs/rozpracovane/reserse_postavy_kcd2.md` (RPG Codex: útěk a zamykání; fórum KCD: zametání v dešti).
