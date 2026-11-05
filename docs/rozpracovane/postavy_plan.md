# Postavy – rozbor a plán „vymazlení“ (5. 11., pomocník)

Míša: „vymazlit postavy ve hře – animace, vzhled i chování; částečně už to máš, ale chce to promyslet“.
Tato fáze je jen **rozbor a plán**: Godot jsem nespouštěl, kód jsem neměnil. Všechna čísla výkonu na tabletu jsou
**NEOVĚŘENO** (žádné měření postav na tabletu neexistuje: v 0.9993 byl krok „bez života“ omezen na 30 FPS, a tak
není srovnatelný; viz `docs/mereni_verze.md` ř. 25).

Navazuje na starší rešerše: `reserse_postavy_kcd2.md` (rozvrhy, smart objects, UAL, LOD), `reserse_reakce_kcd2.md`
(vnímání a reakce), `odevy_zdroje.md` (oděvy a zbroj), `disk_inventura.md` (Disk). Tady je to, co v nich chybí:
stav po 0.99–0.9997, konkrétní chyby a pořadí práce.

---

## 1. Současný stav

### 1.1 Kdo je ve světě (`pravidla/svet/postavy.json`, `obyvatele`)
14 obyvatel, 7 rolí:

| role | počet | domov / práce | rozvrh (od hodiny → činnost) |
|---|---|---|---|
| rychtář (Ondřej) | 1 | dům 5 | 6 dveře, 7 dohled na návsi, 11 jídlo, 13 hovor, 18 dohled u dveří, 21 spí |
| sedlák | 3 | domy 1, 2, 4 | 4,5 ráno, 5,5 záhon, 11,5 jídlo, 12,5 záhon, 17,5 hovor na návsi, 19,5 dveře, 20,5 spí |
| selka | 3 | domy 2, 3, 6 | podobně, jídlo 10,5 a 18,5 |
| lamač / kameník | 3 | chýše 20–21 u lomu, `lom_stena_1/2`, `lom_spalek` | 5,5 práce, 12 odpočinek, 13 práce, 18,5 hovor u dveří, 20 spí |
| čeledín (Matěj) | 1 | nádvoří, staje | nosí (obchůzka studna–staje–kovárna–brána–palác), 12 odpočinek u studny |
| děvečka (Kateřina) | 1 | nádvoří, palác | nosí, 11,5 hovor |
| mlynář | 2 | vodní mlýn, větrník | mletí, 12 odpočinek |

**Nikdo není:** v hostinci (hostinský, hosté), v kovárně na tvrzi (kovárna z Disku stojí, `nadvori_kovarna` je jen
zastávka čeledína), na stráži u brány tvrze, u zvířat (pastýř, pasačka husí), pán/paní tvrze, kněz, děti, staří lidé.
V noci jsou všichni doma (`noc_doma: true`) – ves je od 21 h prázdná.

### 1.2 Co postavy umí (`scripts/lide.gd`, 585 ř.)
- **Rozvrh po hodinách** (`_blok` ř. 269, `_novy_blok` ř. 326): blok → činnost → místo (bod, ulice, dveře/zahrada
  domu, dveře dílu, lokace).
- **Chůze po síti cest** (AStar2D z os cest, `_graf` ř. 159), spojky bez zdí (`_volno` ř. 196), poslední úsek z bodu
  bez zdi (`_volny_bod` ř. 297). Rozjezd a brzdění, otáčení max. 180 °/s, čekání, když hráč stojí v cestě
  (`uhyb_hrac_m`).
- **Činnost na místě**: střídání klipů po `obmena_s`, natočení podle `yaw_st` místa. Čeledín chodí obchůzku.
- **Hlava a krk** sledují hráče (LookAtModifier3D na `neck_01` a `Head`, `_hlava` ř. 72), jinak hledí 6 m vpřed.
- **Vnímání a reakce** podle KCD2 (zorné pole, dohled podle role, noc, rozpoznání 4 s, zapomenutí; tabulka reakcí
  `_reakce` ř. 352): pozdrav / nevrlý / odvrácení / jen pohled; **replika jako Label3D nad hlavou** (`_rekni` ř. 392),
  klip `Yes` (kývnutí) jen když postava stojí.
- **LOD AI**: mimo dosah se nepočítá, při změně bloku se přesune rovnou na místo.
- **LOD animací** (ř. 578–585): do 25 m a jen 8 nejbližších každý snímek, do 45 m 10 fps, dál póza stojí.
- **Nemají:** rozhovor s hráčem (v `scripts/` není žádný dialog), předměty v rukou, sezení na lavici, otáčení na místě,
  rozhovor dvou postav k sobě, reakci na počasí, odlišné chování v neděli, zvuk (kroky, hlas).

### 1.3 Animace (Quaternius Universal Animation Library 1 + 2 Standard, CC0)
`modely/postavy/anim/UAL1.glb`, `UAL2.glb` (jen kostra + klipy, `tools/ual_anim_jen.py`), knihovna sdílená všemi
postavami (`scripts/anim_ual.gd`, cache podle cesty ke kostře – klipy jsou v paměti jednou).

| používá se | kde |
|---|---|
| `Idle_Loop`, `Idle_FoldArms_Loop`, `Walk_Loop` | všichni |
| `Farm_Harvest`, `Farm_PlantSeed`, `Farm_Watering` | záhon (sedlák, selka) |
| `Idle_Talking_Loop` | hovor |
| `TreeChopping_Loop`, `Fixing_Kneeling` | lom |
| `Sitting_Idle_Loop` | odpočinek (lom, čeledín) |
| `Interact` | nošení, mletí |
| `Yes` | pozdrav |
| hráč (`scripts/telo.gd`): `Jog_Fwd_Loop`, `Sprint_Loop`, `Jump_*`, `Interact`, `PickUp_Table`, `Chest_Open`, `Consume`, `ClimbUp_1m`, `Idle_Torch_Loop`, `Idle_Lantern_Loop`, `Driving_Loop` | |

**Dostupné a nepoužité** (hodily by se): `Sitting_Enter`, `Sitting_Exit`, `Sitting_Talking_Loop` (hostinec,
lavice), `Walk_Carry_Loop` (vypnuto 0.992, protože postava nic nenesla), `Walk_Formal_Loop` (rychtář, stráž),
`Idle_No_Loop` (odmítnutí), `Crouch_Idle_Loop` (práce u země), `Push_Loop` (trakař, mlýnský kámen),
`Idle_Rail_Loop` / `Idle_Rail_Call` (opřený o plot, volání), `Idle_Lantern_Loop` / `Idle_Torch_Loop` (noční chůze),
`LayToIdle` (vstávání), `Consume` (jídlo venku), `PickUp_Table`, `Chest_Open`, `Hit_Knockback` (úlek).
**Nepoužívat:** `Idle_TalkingPhone_Loop`, `Pistol_*`, `Spell_*`, `Zombie_*`, `NinjaJump_*`, `Dance_Loop`.
**Chybí úplně** (už v `reserse_postavy_kcd2.md` 3.2): otočení na místě, kladivo na kovadlinu, motyka, vidle, pytel
na rameni, vědra, mávnutí, úklona, modlitba, zametání, čepování.

### 1.4 Jak postavy vypadají (`lide.gd _model` ř. 101–156)
Každá postava = **celé tělo „Superhero“** z Quaternius Universal Base Characters (z něj se kreslí jen hlava,
zbytek zahodí shader `shaders/postava_hlava.gdshader` přes `discard`) + **hotový oděv `Male_Peasant.gltf` /
`Female_Peasant.gltf`** (Modular Character Outfits – Fantasy) + vlasy (2 účesy na pohlaví) + u 60 % mužů vousy.
Barva vlasů ze 5 odstínů, měřítko 0,94–1,04.

Snímek oděvu, jak ho hra skládá (Blender, klidová póza, hlava uříznutá stejně jako shader):
`docs/screens/postavy_plan/npc_dnes_blender.jpg`. **Ve hře žádný snímek postav neexistuje** – v `build/` a
`docs/screens/` jsou jen snímky těla hráče (`build/fjizda/telo_*.png`), koně a krajiny.

Co je na tom konkrétně špatně (proč to působí moderně a hračkovitě):
1. **Ženy v kalhotách, korzetu a šněrovacích holínkách** – kostým z fantasy RPG. Vdaná žena v roce 1393 nosí
   dlouhou sukni nebo šaty až po kotníky a roušku (zavinutí) na hlavě. Na Female_Peasant nic z toho není.
2. **Muži: zapínaná halena s lesklou kovovou přezkou ve tvaru kosočtverce**, kožené návleky na předloktí,
   holínky s přezkami a vysokou manžetou – kostým, ne sedlák.
3. **Obličeje „Superhero“**: ostře řezané rysy, svalnatý krk, hrdinské proporce (a široká ramena) – každý vypadá
   jako 30letý atlet. Chybí staří, děti, hubení, shrbení lidé.
4. **Všichni stejně oblečení**: 14 obyvatel = 2 oděvy. Rychtář vypadá jako lamač, mlynář jako děvečka. Rozdíl je jen
   v barvě vlasů.
5. **Čisté, syté barvy a hladké látky** (stylizace „hand-painted“), žádná špína, prach z lomu, mouka u mlynáře.
6. **Obočí jsou šedobílá**: textura vlasů kitu je šedá, kód barví jen vlasy a vousy (`lide.gd` ř. 130–143), ale ne síť
   `Eyebrows` těla Superhero → hnědovlasý muž s bílým obočím (podezření z kódu a ze snímku v Blenderu; ve hře
   NEOVĚŘENO snímkem).
7. **Hlava jinak stínovaná než ruce**: shader hlavy má jen albedo a pevnou drsnost 0,7, bez normálové mapy;
   ruce oděvu mají plný PBR materiál (normála, drsnost) → hlava „plastová“ vedle rukou (podezření, NEOVĚŘENO).

### 1.5 Cena na tabletu (spočítáno ze souborů, na tabletu NEOVĚŘENO)
| díl | trojúhelníky | povrchy (kreslení) |
|---|---|---|
| Superhero_Male_FullBody (kreslí se jen hlava, ale skinuje se celé tělo) | 14 318 | 3 (tělo se shaderem s `discard`, oči, obočí) |
| Male_Peasant | 12 894 | 5 |
| vlasy + vousy | 1 300–2 900 + 1 034 | 1–2 |
| **muž celkem** | **≈ 29–31 tis.** | **≈ 10 + stín** |
| **žena celkem** (Superhero_Female 15 060 + Female_Peasant 13 568 + vlasy 2 900–3 300) | **≈ 31,5–32 tis.** | **≈ 9 + stín** |

- Třída `postava` v `pravidla/pravidla_modelu.json` (ř. 351) povoluje **14 000 / 3 000 troj.** (LOD0 / LOD1),
  `stin_m` 15 m. Dnešní NPC mají **2× víc** a LOD1 neexistuje. Stín vrhají všechny postavy na celý dosah
  (`lide.gd` ř. 154, `SHADOW_CASTING_SETTING_ON`), ne jen do 15 m.
- `discard` v shaderu hlavy na mobilní GPU vypíná early-z pro celý povrch těla (14 tis. troj. se skinují a rasterizují
  jen kvůli hlavě) – podezření, NEOVĚŘENO.
- Textury: 1024 px (Peasant 3×, Superhero 3×, vlasy 2×) – v pořádku s třídou (`textura_px` 1024).
- LookAtModifier3D běží u každé viditelné postavy (do 90 m) každý snímek, i když se animace neposouvá
  (podezření, NEOVĚŘENO).

### 1.6 Chyby chování, které jsou vidět (z kódu; snímkem NEOVĚŘENO)
- **Sezení ve vzduchu:** činnost `odpocinek` má `"sed": true`, ale `lide.gd` klíč `sed` nikde nečte → lamač v poledne
  hraje `Sitting_Idle_Loop` u stěny lomu bez sedátka, čeledín u studny totéž. Bez `Sitting_Enter/Exit` – z chůze
  skočí rovnou do sedu.
- **Klouzající socha 45–70 m:** postava se pohybuje i za `anim_do_m` (45 m), ale animace tam stojí → ve 45–90 m
  vidíš jedoucí ztuhlou postavu (ř. 477 `blizko` = dosah + 20 m, ř. 581 animace jen do 45 m).
- **Mizení ve dveřích:** blok `domov` / `spi` / `jidlo` postavu u dveří skryje v jednom snímku (`skryty`), dveře se
  neotevřou. Totéž ráno – postava se u dveří objeví.
- **Synchronní ves:** všechny 3 selky mají stejný rozvrh na minutu → v 10:30 odejdou z 3 zahrad naráz.
- **Gesta naprázdno:** `TreeChopping_Loop` (sekání sekerou) v lomu bez nástroje, `Farm_*` na záhonu bez motyky
  a konve, `Interact` ve mlýně do vzduchu, čeledín „nosí“ s prázdnýma rukama.
- **Hovor bez partnera:** `hovor` na návsi vybere náhodné místo skupiny `naves` → postava „mluví“ k nikomu, k sobě
  natočené nejsou.
- **Repliky jako bubliny nad hlavou** (Label3D) – komiksový prvek, v KCD2 nic takového není (hlas + titulky dole).

---

## 2. Problémy podle toho, jak moc kazí dojem

| # | problém | proč kazí dojem | kde |
|---|---|---|---|
| 1 | **Fantasy kostýmy a hrdinské obličeje, všichni stejní** | první, čeho si hráč všimne; ves 1393 vypadá jako cosplay | `lide.gd _model`, `Male/Female_Peasant.gltf` |
| 2 | **Gesta bez předmětů a sezení ve vzduchu** | „loutka“: sekání bez sekery, sed na ničem | `postavy.json cinnosti`, `lide.gd` (klíč `sed` se nečte) |
| 3 | **Ztuhlé klouzající postavy 45–90 m, mizení ve dveřích** | dálka a ves vypadají mrtvě/rozbitě | `lide.gd` ř. 477, 487, 578–585 |
| 4 | **Prázdná místa**: hostinec, kovárna, brána tvrze, pastviny, noc | svět bez života tam, kde ho hráč čeká nejvíc | `postavy.json obyvatele` |
| 5 | **Žádný rozhovor s hráčem, bubliny nad hlavou** | postava nejde oslovit; bubliny jsou z jiného žánru | `lide.gd _rekni` |
| 6 | **Cena 2× nad třídou, stín všech, `discard` hlavy** | na tabletu riziko při 8+ postavách v záběru (NEOVĚŘENO) | `pravidla_modelu.json` třída postava |
| 7 | Synchronní rozvrhy, hovor bez partnera, otočení na místě chybí | drobné, ale sčítají se v „robotičnost“ | `postavy.json role`, `lide.gd` |

---

## 3. Rešerše

### 3.1 Co už máme hotové jinde (nejdůležitější nález)
**Na větvi `main` (sloučeno 17. 10., commit `8723f11`, větev `postavy-quaternius`) leží 9 dobově oblečených NPC
a 3 hrdinové**, kteří se do současné větve `claude/new-session-0dtk58` nikdy nedostali:
- `modely/postavy/npc/npc_{sedlak,kovar,mestan,stary,mladik,selka,babka,mestka,divka}_*.gltf` + `*_sada.json`;
  košile, kotle/cotte, nohavice, škorně, opasek, kápě, rouška – šité na tělo Quaternius, **stejná kostra 65 kostí**
  (ověřeno: `npc_sedlak_telo.gltf` má klouby `root, pelvis, spine_01…` jako UAL), tělo 6 740 troj.,
  **oblečená postava ≈ 7–8 tis. troj.** (dnes 30 tis.), 2 atlasy 512 px, mrkání a pohled očí
  (`nastroje/godot/postava_oci.gd`), skládání `nastroje/godot/postava_sklada.gd`.
- Hrdinové `modely/postavy/hrdinove/{muz,kluk,zena}_*` (Jan, kluk, Eliška) (12,7–14,3 tis. troj.) – mohou být tělem hráče místo
  dnešního Male_Peasant.
- Rádce 17. 10. 08:05: „Schváleno ke sloučení… 9 NPC v rozpočtu, mrkání a pohled očí“; Míša 16. 10. 18:33 schválil
  směr „Quaternius, ne MakeHuman“ („není to reálné, ale hezké, pojď dál“).
- Snímky: `docs/screens/postavy_plan/npc_dobove_17_10_muzi.jpg`, `…_zeny.jpg` (z větve, šedé pozadí).
  Co je na nich špatně a musí se dotáhnout: sukně kotle a šaty jsou tuhé „zvony“ (při chůzi a sedu projdou nohy),
  na látce jsou černé hranaté skvrny (normály / stínování), modrá a červená jsou moc syté, obličeje jsou pořád
  „Superhero“, roušky měly díry (opraveno v `6d5bb69`). Ve světle hry je nikdo neviděl.

### 3.2 Míšin Disk (prohledán 5. 11. přes Google Drive)
Složka **Modely** (`1LIf8CIdMUVgmgOiszmP1E567PpmUbi-b`): podsložky Nové budovy, Rostliny, tržní stánky a zelenina –
žádné postavy ani animace. Složka **Postavy** (`14ni9XhJdwWaQfdyXRik0UqJIXbDa27lM`): UAL 1 a 2 Standard, Universal
Base Characters Standard, Modular Character Outfits – Fantasy Standard, `makehuman_system_assets_cc0.zip`
(oděvy a vlasy MakeHuman, CC0 – neprojité). Od 29. 10. nic nového. Z inventury: `knight.glb` (CC-BY, sanyaork,
zbroj), `arm_piece_armor.glb` (CC-BY). Nic dalšího pro vesničany.

### 3.3 Hotové zdroje mimo Disk
| zdroj | co | licence | pro nás |
|---|---|---|---|
| Quaternius UAL 1/2 **Pro / Source** ([UAL2](https://quaternius.com/packs/universalanimationlibrary2.html), [itch](https://quaternius.itch.io/universal-animation-library)) | Standard je „60–70 %“ balíku; Pro přidává farmaření, rybaření, emoce, 8směrnou chůzi | CC0 | **stejná kostra, bez retargetu**; přesný seznam klipů Pro na webu není (NEOVĚŘENO – ověřit v animviewer), cena jen v obrázku |
| Quaternius Modular Character Outfits **Source** ([itch](https://quaternius.itch.io/modular-character-outfits-fantasy)) | 12 oděvů (rytíř, šlechtic…) | CC0 | podle `odevy_zdroje.md` ~20 USD; jen jako polotovar (fantasy) |
| Kevin Iglesias – Human Crafting Animations Free ([gumroad](https://keviniglesias.gumroad.com/l/human-crafting-animations-free), [itch](https://kevdev.itch.io/human-villager-animations)) | kladivo, pila, krumpáč, vědra… | licence NEOVĚŘENA (Unity Asset Store / vlastní) | kandidát na chybějící řemesla; nutný retarget na UAL |
| Mixamo | stovky klipů (práce, sezení, gesta) | Adobe: použití ve hře zdarma, **ale ne šíření samotných souborů** ([fórum Adobe](https://community.adobe.com/t5/mixamo-discussions/mixamo-characters-for-commercial-games/td-p/11815020)) | **riziko:** naše repo ukládá balíky dat na veřejný GitHub (`data/*.pck`, odkaz na APK) – surový klip by šlo vytáhnout; retarget Mixamo → UAL kostra nutný. Doporučuji jen když nic CC0 nesedí a po souhlasu Míši |
| Sketchfab CC-BY, rigged, ke stažení (API dotaz 5. 11.) | „Virtual model linen / wool tunic Svend / Revna“ (chambersu1996, 31–43 tis. troj.), „Old Village Granny“ (Imagineis, 617 troj.), „Girl with clothes. Worker set“ (cattleya, 2,5 tis.) | CC-BY (autor do titulků) | lněná a vlněná tunika jsou dobově nejblíž; jiná kostra → přenos vah na UAL, redukce; stažení potřebuje přihlášení |
| Sketchfab oděvy a zbroj | seznam v `odevy_zdroje.md` C (bascinet, kettle hat, gambeson, coif, tunika…) | CC-BY | pro stráž a hráče |
| Kenney, KayKit, Quaternius LowPoly RPG / Ultimate Modular | kostičkové, jiná kostra | CC0 | **nesedí** k realistickému světu |
| Synty, CGTrader „Medieval Villagers“, Fab | hotové vesnice NPC | placené, vlastní licence | **nesmíme** bez koupě a licence |

### 3.4 Jak to dělá KCD2 (shrnutí, podrobně ve starších rešerších)
- Každé NPC má denní rozvrh, který běží i daleko od hráče; v KCD2 se rozvrhy mění podle událostí (část vyvolá
  hráč) ([wccftech](https://wccftech.com/kingdom-come-deliverance-2-dev-talks-about-dynamic-npc-routines-and-emergent-storytelling-for-side-quests/),
  [GDC shrnutí KCD1](https://gamedev.net/news/5526-supporting-thousands-of-npcs-in-kingdom-come-deliverance-kingdom-come/)).
  Činnost = smart area se sloty, kde je animace i předmět (`reserse_postavy_kcd2.md` 1.1).
- Animace z motion capture včetně dialogů a „background events“ hraných herci
  ([Warhorse, Lead Animator](https://www.welcometothejungle.com/cs/articles/lead-animator-z-warhorse-diky-motion-capture-mame-ve-hre-realisticke-animace)).
  To nemáme – proto **předmět v ruce a správné místo** dělají víc než lepší klip.
- Oblečení podle stavu a role (sedlák, měšťan, stráž, šlechta) a hráč je hodnocen podle oblečení, špíny a krve
  (`reserse_reakce_kcd2.md` 2.4–2.5). Počet variant oděvů ani animací Warhorse nezveřejnil (nenalezeno).
- Žádné bubliny nad hlavou: krátké hlasové „barks“ s titulkem dole.

### 3.5 Davy v Godotu a na mobilu
- Godot neodkládá výpočet kostry mimo obraz sám; vypnout AnimationPlayer u vzdálených / neviditelných postav
  pomáhá nejvíc (uživatel: z ~36 FPS na 200+ jednotek), dál nahradit jednoduchým modelem nebo billboardem
  ([fórum Godot](https://forum.godotengine.org/t/performance-of-crowds-of-animated-rigged-characters-in-3d/130409)).
  To u nás už dělá ruční `advance` (MANUAL) – chybí vypnout LookAt a stín v dálce.
- Snížit frekvenci animace podle vzdálenosti
  ([návod](https://uhiyamalab-gatsby.pages.dev/en/notes/godot/3d-skeletal-animation)) – máme (10 fps 25–45 m).
- Pro 14–25 postav **impostory ani VAT nepotřebujeme** (MultiMesh nemá culling; `reserse_postavy_kcd2.md` 6.1) –
  přínos je v tom, aby jedna postava byla levná (méně troj., méně povrchů, stín jen zblízka).

---

## 4. Plán po krocích (seřazeno podle přínosu)

Každý krok: co → zdroj → cena na tabletu (odhad = NEOVĚŘENO) → ověření. Pořadí stavby a hlídači podle CLAUDE.md
(záznam v datech, test, snímek a vlastní kontrola snímku).

### Krok 0 – první snímek postav ve hře (podklad, ½ dne)
- **Co:** 5 stálých záběrů postav (náves 10:00, zahrada, lom v poledne, nádvoří, mlýn) přes `--write-movie` /
  `TVRZ_MERENI`; do `docs/screens/postavy_plan/hra_*.jpg`. Do měřicí trasy varianta **„bez lidí“** (skupina
  `lide` v `main._ab_skupiny`) bez omezení 30 FPS.
- **Proč první:** dnes žádný snímek ani měření postav neexistuje – nevíme, jestli sezení ve vzduchu, šedé obočí a
  klouzání opravdu vidět (všechno výše je z kódu).
- **Ověření:** snímky prohlédnuté stavitelem; řádek v `mereni_verze.md`.

### Krok 1 – dobové oblečení a levnější tělo (největší přínos pro vzhled i výkon)
- **Co:** převzít z `main` sady `modely/postavy/npc/*` + `postava_sklada.gd` + `postava_oci.gd`; v `postavy.json`
  každému obyvateli `sada` (rychtář = `npc_mestan` ztlumený, sedláci `npc_sedlak` / `npc_stary` / `npc_mladik`,
  lamači `npc_kovar` s kápí, selky `npc_selka` / `npc_babka`, děvečka `npc_divka`), barvy látek jako data (len,
  vlna nebarvená, hnědá, ztlumená modř). `lide.gd _model` čte sadu místo Superhero + Peasant.
- **Dotáhnout před vydáním:** sukně kotle a šaty – tuhé zvony → rozdělit spodní okraj na 2 díly s vahami stehen
  (nebo kratší kotle po kolena u mužů, u žen šaty s vahou na pánev + stehna 50/50); černé hranaté skvrny na látce
  (normály po exportu, ve hře zkontrolovat); syté barvy −30 %.
- **Zdroj:** vlastní, už schválené 17. 10. (Quaternius CC0 + šité oděvy); nic nového se nestahuje.
- **Cena:** ≈ 7–8 tis. troj. místo 30 tis., méně povrchů (2 atlasy), bez `discard` (NEOVĚŘENO, změří krok 0).
- **Ověření:** snímek 5 postav na návsi ve světle hry vedle KCD2 reference (`docs/screens/ref_kcd2_ves_ulice.jpg`);
  test třídy `postava` (≤ 14 000 troj. LOD0) – nový řádek v testu modelů; `tools/kontrola_baliku.py` (sady
  v balíku `z_postavy`, `modely/` je mimo git).
- **Pozor:** `modely/` je v `.gitignore` této větve → soubory z `main` vytáhnout `git show origin/main:<cesta>`,
  do hry jen přes balík.

### Krok 2 – předměty v rukou a místa činností (největší přínos pro „ne loutka“)
- **Co:** `cinnosti` dostanou `predmet` (BoneAttachment3D na `hand_r` / `hand_l`, stejně jako `telo.gd` ruka_r) a
  činnost se váže na místo s předmětem: lom – `krumpac` / `kladivo_kamenicke` (místo „sekyry“ z `TreeChopping_Loop`),
  záhon – `hrabe` / `vedro` (konev), čeledín – `vedro` při chůzi + `Walk_Carry_Loop` zpátky (s předmětem), mlynář –
  `pytel_mouky` na rameni (klip chybí → `Walk_Carry_Loop`), večer `lucerna` s `Idle_Lantern_Loop` (horní polovina přes
  filtr kostí jako u hráče).
- **Zdroj:** katalog `modely/predmety.json` už má `krumpac, kladivo, kladivo_kamenicke, lopata, hrabe, vidle, kosa,
  vedro, vedro_drevene, pytel_mouky, pytel_obili, lucerna, louc, dzban` (z Poly Haven / Disku / vlastní).
- **Cena:** +1 povrch na postavu, sdílená síť (NEOVĚŘENO).
- **Ověření:** snímek lamače a sedláka zblízka; test: každá činnost s klipem práce má `predmet` (kontrola v
  `tools/kontrola_tabulek.py` nebo `test_smyslu`).

### Krok 3 – opravy chování, které je vidět (levné, jen kód + data)
1. **Sezení jen na sedátku:** `odpocinek` a `hovor` vsedě jen na místech s lavicí/špalkem (místo s `sedadlo` →
   výška a natočení z položeného předmětu; logika sezení hráče je v `predmety.gd` ř. 387–401); přechod
   `Sitting_Enter` → `Sitting_Idle_Loop` / `Sitting_Talking_Loop` → `Sitting_Exit`. Bez sedátka → stání
   (`Idle_Rail_Loop` opřený, `Crouch_Idle_Loop`).
2. **Dálka bez klouzání:** v 45–70 m při chůzi animace 5 fps (ne póza); stín a LookAt vypnout za `stin_m` / 25 m;
   za 70 m skrýt (dnes až 90 m). Čísla jen v `postavy.json` / `pravidla_modelu.json`.
3. **Dveře:** skrýt/objevit až po otevření dveří domu (`Pohyb_*`, jako hráč) nebo jen mimo záběr.
4. **Rozptyl rozvrhu:** každý obyvatel `posun_min` ±20 min (seed podle id) – selky neodcházejí naráz.
5. **Hovor ve dvojici:** `hovor` rezervuje místo pro 2–3 postavy (sloty kolem bodu, natočení k sobě), střídání
   `Idle_Talking_Loop` / `Yes` / `Idle_No_Loop` / `Idle_FoldArms_Loop`; kdo nemá partnera, jde jinam.
6. **Otočení na místě:** při rozdílu > 60° pomalá otočka s `Walk_Loop` na 0,3 m/s (dokud nebude klip).
7. **Šedé obočí:** barva vlasů i na síť obočí (u sad z kroku 1 zkontrolovat totéž).
- **Cena:** zanedbatelná. **Ověření:** snímky z kroku 0 znovu; test `vztahy_hra` doplnit „postava v sedu má pod
  pánví předmět“ a „postava v pohybu 45–70 m má běžící animaci“.

### Krok 4 – chybějící lidé (data)
- **Co:** kovář na tvrzi (`kovarna_tvrz`: kladivo + `Fixing_Kneeling`/`Interact` u kovadliny), hostinský + 2–3 hosté
  vsedě (`Sitting_Talking_Loop`, `Consume`) v hostinci večer, stráž u brány (`Walk_Formal_Loop`, kopí, obchůzka po
  hradbě), pastýř/pasačka u ovcí, 1–2 děti (hrdina „kluk“ z `main`, měřítko), stařec na lavici před domem,
  večer ponocný s lucernou.
- **Zdroj:** sady z kroku 1, předměty z katalogu, zbroj stráže z `odevy_zdroje.md` (topfhelm/klobouk CC0,
  Sketchfab kettle hat CC-BY).
- **Cena:** +6–8 postav; rozpočet `plne_max` 8 nechat (NEOVĚŘENO – rozhodne měření kroku 0).
- **Ověření:** test pokrytí rozvrhu 24 h a existence míst (`reserse_postavy_kcd2.md` 9 bod 7), snímek hostince
  večer.

### Krok 5 – nové animace řemesel
- **Co:** kladivo na kovadlinu, motyka, pytel na rameni, vědra, mávnutí, úklona, modlitba.
- **Zdroj podle pořadí:** (a) UAL Pro/Source (CC0, stejná kostra – nejdřív ověřit seznam v
  [animviewer](https://quaternius.com/animviewer.html)); (b) úprava existujících klipů v Blenderu (kladivo z
  `TreeChopping_Loop` s menším rozmachem); (c) Kevin Iglesias crafting (po ověření licence, retarget); (d) Mixamo
  jen se souhlasem Míši (licence – viz 3.3).
- **Cena:** klip ~20–60 kB, knihovna sdílená. **Ověření:** snímek každého klipu s předmětem; `anim_ual.gd` hlásí
  chybějící klipy.

### Krok 6 – rozhovor s hráčem a hlas
- **Co:** oslovení postavy (tlačítko jako u předmětů) → krátký rozhovor z JSON (pozdrav, práce, cesta, zvěsti), titulky
  dole místo bublin; bubliny jen jako volba. Případně krátké hlasové „barks“.
- **Rádce 21:51:** logika akcí a rozhovorů až pod Míšiným dohledem → nejdřív otázka 3.

### Krok 7 – oblečení podle stavu a počasí, špína
- Prach z lomu, mouka u mlynáře, bláto na nohavicích (detail textura / barva vrcholů), plášť a kápě v dešti,
  v zimě kožich; sváteční oděv v neděli. Až po kroku 1–4.

---

## 5. Otázky pro Míšu
1. **Styl postav:** pokračovat ve stylizovaných postavách Quaternius s dobově přešitým oblečením (9 NPC ze 17. 10.,
   snímky `docs/screens/postavy_plan/npc_dobove_17_10_*.jpg`), nebo zkusit realističtější obličeje (MakeHuman CC0,
   16. 10. zamítnuto)? A mají se změkčit „hrdinské“ obličeje a postavy (starší, hubenější, shrbení lidé)?
2. **Nákup:** smím koupit Quaternius UAL Pro/Source (a Outfits Source)? Jsou CC0, na stejné kostře; cena NEOVĚŘENA
   (Outfits Source podle starší rešerše ~20 USD). Mixamo nechci bez tvého souhlasu (soubory by byly v balíku dat
   na veřejném GitHubu).
3. **Repliky:** bubliny nad hlavou nechat, nebo titulky dole jako v KCD2 (a případně krátké hlasy)? A smím začít
   rozhovory s postavami, nebo to chceš vést sama (rádce 21:51)?
4. **Kdo má ve světě přibýt** a v jakém pořadí: kovář, hostinský a hosté, stráž, pastýř, děti, pán tvrze, kněz,
   ponocný? Má ves žít i v noci (hostinec, ponocný s lucernou)?
5. **Hráč:** má hráč dostat tělo hrdiny Jana z větve `main` (dobové oblečení), nebo zůstat sedlák Quaternius, dokud
   není menu oblékání hotové?

## Rozhodnutí Míši (5. 11.)
1. Styl: **dobové** postavy (základ ze 17. 10., větev `main`), a když se najdou lepší dobové modely, tak ty.
2. Zdroje: **jen zdarma** (Quaternius Pro se nekupuje). Mixamo ano – hra je zdarma pro všechny („my za to peníze
   nevybíráme, takže vše je dostupné všem“); autory a zdroje uvést v titulcích.
3. Mluvení **jako v KCD2**: titulky dole (bez bublin), rozhovory s postavami.
4. Přibýt má **všechno, co jde**: kovář, hostinský a hosté, stráž, pastýř, děti, pán tvrze, ponocný; ves žije i v noci.
5. Hráč: tělo **mladého** hrdiny.
6. **Denní režim (Míša 5. 11.):** každá postava má **domov a postel** (záznam v datech: dům, postel), v noci spí v posteli;
   úplný denní režim (vstávání, jídlo, práce, hospoda, návrat, spánek). V noci chodí **jen stráže** (ponocný, stráž
   tvrze). Později: hrdina může spícího vzbudit.
   Kde se spí (Míša 5. 11.): postele jsou i v **chatrčích v lomu** (lamači) a v **lese u uhlíře**; **mlynáři** mají své
   ve mlýně; **hospoda** má **nájemní postele** (hosté, pocestní). Každé místo spánku = záznam v datech (budova, postel).

---

## Vzhled a animace – provedení (5. 11., pomocník vzhledu)
**Postup stavby (opakovatelný):** `tools/postavy_q/` = přenesená linka z `main` (17. 10.) s cestami z proměnných.
- `postavy.json` – sady: `npc_<jméno>` = jeden obyvatel (24 sad: 17 mužů vč. hocha, 7 žen vč. pasačky), `hrac` = mladý hrdina;
  barvy v `_barvy` (lineární RGB): len bílý/režný, nebarvená vlna šedá/bílá/hnědá/tmavá, ořech, boryt (modř), mořena (červeň),
  rezeda (žluť), olivová (boryt+rezeda).
- `sestav.sh [sada…]` (na pozadí; `Q_NAHLED=0` bez náhledu Cycles, `Q_PROC` souběh) → `modely/postavy/npc/<sada>_cela.gltf`
  + `textury/` (2 atlasy 512: hlava, tělo+oděv), zapíše trojúhelníky do `pravidla/svet/postavy_vzhled.json` `troj`.
  Zdroje z větve `assets` (`quaternius/`); dvě chybějící normálové mapy se doplní z `modely/postavy`. Blender modul potřebuje
  `opencv-python-headless` (sestav.sh doinstaluje). Hrdina: `q_postava.py -- hrac` + `q_export2.py -- hrac … modely/postavy/hrdina`.
- Opravy proti 17. 10.: **sukně** kotle/cotte váhy shora z těla, dolů roste podíl stehen (strana podle x, uprostřed přechod),
  lýtka ne (`q_obleceni._skirt_leg_weights`); **košile** pod svrchním šatem jen ve výstřihu a u krátkého rukávu
  (`_trim_under`) – příčina černých skvrn podle rozboru: prosvítající košile se zapečenou tmavou AO (hypotéza, ověřit snímkem);
  **tváře** měkčí (`mekkost`: rozmazaná kopie textury v obličeji, normálová mapa hlavy ze 40–80 % k rovině), štíhlejší krk
  (`krk`); **obočí** bez vlastní barvy = vlasy ×0,85 a šediny.
- **Jedna síť se 3 povrchy** na postavu (hlava, vlasy+obočí s alfa výřezem MASK, tělo+oděv) místo ~15 dílů; oči pevně na
  kosti Head (bez pohledu očí), mrkání zůstává jako morph (zatím ho nic nespouští).
- Hra: `scripts/vzhled.gd` (výběr sady: obyvatel.vzhled → `obyvatele[id]` → `podle_role[role]` → záložní podle pohlaví),
  `lide.gd _model_o` (bez sady starý model Superhero+Peasant). Tělo hráče `telo.gd` → `modely/postavy/hrdina/hrac_cela.gltf`,
  kreslí se jen povrch těla+oděvu, celá postava vrhá stín (SHADOWS_ONLY).
- **Animace:** Mixamo bez přihlášení nejde (API 403 „Api Key is required“). Použito **CMU Graphics Lab Motion Capture Database**
  (volné pro jakékoli použití, poděkování NSF EIA-0196217): `stahni_cmu.sh` + `anim_cmu.py` → `modely/postavy/anim/UAL_prace.glb`
  (Prace_Zametani_Loop, Prace_Kovar_Loop, Prace_Pila_Loop, Prace_Uklid_Loop, Prace_Sbirani_Loop, Piti, Piti_Unavene,
  Hovor_Gesta_Loop, Hovor_Gesta2_Loop, Ceka_Loop, Mavani, Otocka); `anim_ual.gd` je načte k UAL1/2. Motyka a kopání v CMU
  není → TreeChopping_Loop / Prace_Sbirani_Loop; nošení, sezení: UAL (Walk_Carry_Loop, Sitting_*).
- Lepší dobové modely zdarma (Sketchfab API 5. 11.): „Medieval poor woman“ (carmenpaloma, CC-BY, 52 tis. ploch, bez kostry),
  „Virtual model linen/wool tunic Svend/Revna“ (chambersu1996, CC-BY, 31–43 tis.), „Old Village Granny“ (Imagineis, 617),
  „Girl with clothes. Worker set“ (cattleya, 2,5 tis.) – stažení vyžaduje přihlášení, rozpočet 3–6× nad třídou nebo
  kostičkový styl → náhrada se nedělá. Quaternius/Kenney/Poly Pizza/OpenGameArt: low-poly, nesedí ke světu.
- Vydání: nové soubory jsou v `modely/postavy/npc/`, `modely/postavy/hrdina/`, `modely/postavy/anim/UAL_prace.glb` →
  balík **`z_postavy`** (`tools/vydani.py`, glob `modely/postavy/**` gltf/glb/png/bin); `pravidla/svet/postavy_vzhled.json` jde v APK.

---

## Chování – provedení (5. 11., pomocník chování; vzhledu se nedotýká)
Kód `scripts/lide.gd`, data `pravidla/svet/postavy.json`, test `tools/test_svet.gd` `lide_chovani`
(`tools/beh.sh … testy lide_chovani`, ~3 min), rychlé snímky jedné postavy bez světa `tools/foto_postava.gd` (14 s).
- **Předměty v rukou** (krok 2): `cinnosti.*.v_rukou` (klip → `{r|l: id z katalogu}`, `"*"` = ostatní klipy a chůze),
  model `modely/predmety/<id>.glb` na `BoneAttachment3D` `hand_r/l`; úchop a natočení v `drzeni` (ladí se snímky
  `build/fpost/`, NEOVĚŘENO dokud není snímek). Lom: krumpáč (TreeChopping), kamenická palice (Fixing_Kneeling); záhon:
  dřevěné vědro (Watering), srp (Harvest), košík v levé (PlantSeed, snímek z odvrácené strany – NEOVĚŘENO); čeledín a děvečka: vědro při nošení. Motyka ani konev
  v katalogu nejsou (díra). Test: klip s nářadím bez předmětu = chyba; krumpáč opravdu na kosti ruky.
- **Sezení** (krok 3.1): klíč `sed` se čte – sedí jen na sedáku z `vybaveni` světa (`sedani.sedaky`, výška sedáku =
  `rozmer[1]` katalogu v toleranci výšky klipu), rezervace míst (lavice po `sirka_mista_m`), `Sitting_Enter/Exit`; bez sedáku
  stojí (`klipy_bez_sedu`). Test 5. 11.: sedí lamač 1, kameník, mlynář u větrníku; stojí lamač 2, čeledín u studny, mlynář
  (žádný sedák do 25 m – díra: položit lavici záznamem do vybavení, ne v kódu).
- **Dálka** (krok 3.2): za `anim_do_m` animace dál `anim_dalka_fps` (4 fps) až do dosahu – žádná ztuhlá klouzající póza;
  LookAt hlavy jen do `hlava_do_m`. Test: postava v 55 m animace běží.
- **Stín** (krok 5): jen do `stin_m` třídy `postava` v `pravidla_modelu.json` (15 m). Test: 8 m stín ano, 55 m ne.
  Úspora na tabletu NEOVĚŘENO (měřicí trasa).
- **Hovor** (krok 3.5): `hovor.skupina` – místo s sloty po kruhu (`hovor_skupina`), čelem ke středu, nový jde ke skupině,
  kde někdo čeká. Test 17:50: 7 lidí → 2 trojice + 1 sám (lichý počet).
- **Rozptyl rozvrhu** (krok 3.4): `rozvrh_rozptyl.rozptyl_min` 15 → tři selky −10 / 0 / +10 min.
- **Dveře a spánek** (Míša 5. 11., bod 6): skrytá činnost končí u dveří (dům vsi = bod před dveřmi, jinde nejbližší
  `Pohyb_dvere*`; čeledín → dveře 12 nádvoří, děvečka → dveře 7 paláce, ne uprostřed nádvoří), postava otevře pohyblivé
  dveře (`pohyb.gd` skupina), vejde `dovnitr_m`, zmizí a dveře, které otevřela, zavře; ráno vyjde od vnitřku dveří.
  Vstupní dveře domů vsi jsou ve hře výchozí otevřené (svet.gd `init`), takže se zavírají jen dveře, které byly zavřené.
  Spánek v posteli: `obyvatele.*.spanek` = záznam (budova, postel); leží v klipu `LayToIdle` v čase 0 (UAL nemá spánek).
  Lamači chodí 18:30 do hospody (dveře hostince `Pohyb_dvere1`), uvnitř jsou skrytí (sezení v šenku = díra, portály).
  **Díry spánku (5. 11.):** ve hře je postel jen 4× nájemní v hostinci (`pouziti` bed, zapečené v modelu). Záznam
  `postel` v rychtě (`svet.json` vybavení 434, 834 – stará rychta) hra po stavbě nových domů nemá (test `lide_chovani`). V domech 1–4, 6, 30, chýších u lomu, mlýně a ve stájích/paláci tvrze postel není; katalog má jen
  `postel` = gotická panská postel (400 grošů) – do chalupy 1393 se nehodí, nepokládal jsem ji. Chybí model lůžka/slamníku
  (hledat hotový: Poly Haven, Sketchfab CC0/CC-BY). Uhlíř ani hosté/pocestní nejsou postavy. Noční stráže nejsou (krok 4).
- **Snímky 5. 11.** (`tools/foto_postava.gd`, dobový vzhled od pomocníka vzhledu): `docs/screens/postavy_po/ruka_*.jpg`
  (krumpáč nad hlavou za konec topůrka, palice při klečení, vědro za ucho při chůzi, naklopené dřevěné vědro při zalévání,
  srp při sklizni), `sed_bok.jpg` (stolička 0,44 m), `sed_lavice.jpg` (lavice 0,475 m) – pánev na sedáku, `postel.jpg`
  (ležení v posteli z katalogu: při `nad_postel_m` 0,55 ~15 cm nad matrací → 0,40, NEOVĚŘENO novým snímkem).
  Snímky „před“ ve světě: jen `docs/screens/postavy_pred/naves_1778.jpg` (selka sama na cestě mezi poli, starý vzhled);
  ostatní před-snímky se nepodařily (výměna souborů a plný disk, viz `predani.md` past 5. 11.).

---

## Nábytek a další postavy – provedení (5. 11. večer, pomocník chování; Míša „vytvoř i ty ostatní osoby; v chalupách postele, v hospodě postele, stoly a lavice“)
**Hledání hotového lůžka (zapsáno, kde se hledalo):** Míšin Disk Modely (prohledán přes Drive: složky Nové budovy, Rostliny,
stánek, zelenina, stan – žádné lůžko); Poly Haven (API: jen `GothicBed_01` = už `postel`, `old_bed_frame` kovová nemocniční,
`vintage_day_bed` 19. st.); Sketchfab CC-BY „Medieval Bed“ (AndriiTiazhkorob 3,4 tis.), „straw bed“ (turusaki), „lit de paille“
(caton.laubergiste), „Wooden Bed“ (toAflame) – stažení jen s přihlášením (API 401) a stylizované; Quaternius/Kenney nízkopolygonové
nebo moderní. Nejbližší hotové je **naše lidové lůžko z hostince** (`blender/vesnice.cot_bed`) → podle něj vlastní modely
v `blender/vlastni.py` (`cot_bed`, `straw_pallet`): rám z dubových fošen na nohách, čelo u hlavy, prkna, slamník (režné plátno),
podhlavnice, vlněná houně přes nohy. Katalog (`blender/predmety.py build lozko lozko_uzke slamnik`):
`lozko` 1,32 × 1,97 m (mist 2, manželé), `lozko_uzke` 0,98 × 1,97 (1), `slamnik` 0,94 × 1,92 × 0,27 (na pryčnu chýše, na zem),
6,7 / 6,2 / 2,1 tis. troj., textury 1k. Hlava na −z předmětu. Stoly a lavice: v katalogu už jsou (`stul_hospoda`,
`lavice_selska`, `stul_selsky`) a v hostinci stojí (síň 2 stoly, 4 lavice, 2 stoličky; šenk 2 stoly, 4 lavice; venku 2 stoly).
**Rozmístění = data** `pravidla/svet/nabytek.json` (konstanta `DUM_VYB` přesunuta z `svet.gd` do dat):
- `domy` podle typu modelu: Dum1/Dum2/Rychta lůžko v koutě jizby mezi pecí a štítem (polohy z kolizí `Kol_Pec`, `Kol_Stena*`
  v `modely/ves/domy.glb`; ovčí kůže z toho místa pryč, vědro v Dum2 a kolébka v rychtě posunuty); chýše (lom i uhlíři)
  slamník na každé pryčně (`Kol_Prycna`, 0,38 m). Tím mají lůžko domy 1–7 a 30, chýše 20–21 obou druhů.
- `mlyn` (rámec `voda.json mlyn.dil`): lůžko v jizbě za pecí. `svet` (tvrz, kolize `modely/svet.json`): gotická postel
  pána a paní v ložnici patra paláce, úzké lůžko děvečky (přízemí paláce, západní místnost), slamník čeledína (síň paláce
  u jižní zdi – stáj má všechny boxy s koňmi), 2 úzká lůžka stráží ve zbrojnici, úzké lůžko kováře v kovárně.
  `zapecene`: 4 lůžka v modelu hostince (`hostinec.py LUZKA`) – jen do seznamu lůžek.
- Hra: `svet._ves_domy` + `_nabytek_budov` → `data.vybaveni` a `data.postele` (`{id, budova, p, yaw, mist}`);
  `lide._postel` bere lůžko budovy a rezervuje místo natrvalo v pořadí obyvatel (`postel:i:k`), manželé vedle sebe
  (`spani.rozestup_m`), výška kořene podle druhu lůžka `spani.nad_postel_m`.
**Sezení v hospodě:** činnost `hospoda` = sed (Sitting_Talking/Idle) v síni hostince; vnitřní místo `mista.hostinec_sin`
(`dvere` Pohyb_dvere1, `venku`/`vnitrek` z modelu, `mistnost` = sedáky jen v síni). `lide._cesta_pruchod`: k vnitřnímu
místu po síti ke dveřím, dveřmi dovnitř (otevře, za sebou zavře), ven zase dveřmi. Venkovní činnost bere jen sedák mimo
všechny místnosti (dřív mohla sednout na lavici v jizbě přes zeď).
**Nové postavy (15, data `postavy.json obyvatele` + `role`):** kovář Václav (kovadlina, `Prace_Kovar_Loop` s kladivem),
strážný Zikmund (u brány s kopím), noční strážný Mareš (20:30–5:30 obchůzka nádvoří s lucernou), pán Jan z Lhoty a paní
Eliška (dohled, procházka po nádvoří `Walk_Formal_Loop`), hostinský Kunc (obsluha v síni do 23 h) a hostinská Machna
(u krbu v síni), pocestní Pešek a Bušek (nájemní lůžka v pokoji hostince; ve dne venku u stolů a na návsi, večer v síni),
ponocný Habart (21–5:30 obchůzka návsi s lucernou, ve dne spí; dům 7) a pastýř Řehoř (u košáru za rychtou, dům 7),
hoch Vítek (dům 4, záhon a hra na návsi), pasačka Ludmila (dům 3, s ovcemi), uhlíř Ondráček a pomocník Kuba (chýše ChyseKura 20,
sekání dřeva na placu – **milíř ve světě není = díra**). Vzhled: sady pomocníka vzhledu podle role, uhlíři a pocestní záložní sada.
**Díry / NEOVĚŘENO:** světlo lucerny v noci (jen model v ruce), milíř, schody do patra (pán, paní, hostinský a hosté se do
lůžka v patře přenesou od dveří), výkon 29 postav na tabletu (měřicí trasa), poloha předmětů v rukou nových postav do snímků.
