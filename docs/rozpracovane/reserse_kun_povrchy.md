# Rešerše: kůň a jezdec v 1. osobě, povrchy pod nohou (4. 11. 2026)

Zadání: jak to dělají jiné hry (KCD1/2, RDR2, Ghost of Tsushima, Witcher 3, Zelda BotW/TotK, Mount & Blade), technika
(IK kopyt, svah, klouzání, přechody chodů) a co z toho jde v Godotu 4.4; kamera z koně; povrchy (zvuk, rychlost, prach).
Ke každému tvrzení zdroj. **nenalezeno** = zdroj jsem nenašel, nevymýšlet. **(odvozeno)** = můj přepočet ze zdroje.
Poznámka ke zdrojům: Nexus Mods, dotesports a wiki Zelda Dungeon vracely 403 – tvrzení odtud jsou jen z úryvků
vyhledávače (označeno „úryvek“). Starší rešerše: `docs/rozpracovane/reserse_potok_1osoba_kun.md` (kap. 3–4),
`docs/rozpracovane/kun_animace.md`.

---

## 1. Kůň a jezdec v hrách

### 1.1 Red Dead Redemption 2 (nejlépe zdokumentované – GDC 2021, Tobias Kleanthous, Rockstar)
Zdroj slajdů: https://gta.com.ua/img/news/making-horses-rdr2-gdc2021.pdf (text vytažen z PDF), shrnutí přednášky:
https://www.gamedeveloper.com/design/rockstar-s-quest-for-the-ultimate-video-game-horse

- **Chody:** 4 – walk, trot, canter, gallop. Každý chod má „min / ideal / max range“ rychlosti, rozsahy se překrývají;
  „Remove idea of tight coupling of gait to speed, exploit gaits for representing ‚effort‘“ (slajdy).
- **První verze (špatná):** „Discrete speeds, no range, nor variation … Stiff turns, C-shape posing … Lumpy and
  inconsistent transitions“ (slajdy) – přesně to, čemu se chceme vyhnout.
- **Přechody chodů:** jednorázové přechodové animace zavrhli („Foot cycle defines transition … Unpredictable“);
  místo nich **plynulé cykly zrychlení a zpomalení** pro každý chod: „Deceleration, more ‚collected‘, compressed legs and
  body, head up; Acceleration, extended legs and body, head down“; „Speed change independent of gait change … Deterministic
  duration“ (slajdy). Start/stop jako smyčky, „Retain AI and Player control at all times“.
- **Zrychlení/brzda v číslech:** nenalezeno (jen princip; plemena se liší „Acceleration and deceleration, Angular
  responsiveness, Preferred speed ranges per gait“ – slajdy, kap. Breeds).
- **Nejvyšší rychlost:** „Fastest horses almost 18m/s (40 mph)“ (slajdy).
- **Otáčení:** otáčení na místě kolem předních nohou („Pivot, roughly about front feet/under chest“), zatáčení s
  bočním posunem („drift“, laterální rychlost jako 3. rozměr blendu) – slajdy; „the root of the rotation is actually
  aligned with its front feet“ (gamedeveloper).
- **Svah:** „IK alone didn't deliver what we wanted“ – animace roztříděné na UP / FLAT / DOWN podle náklonu (pitch ±0,25π)
  a podle vedoucí nohy L/R, blend mezi nimi (slajdy, „4D-ish / 5D-ish“). Gamedeveloper: samotné IK na svahu nevypadalo
  dobře, protože tělo a hlava neodpovídaly sklonu.
- **Terén a povrch:** „Surface data cached: normal, positions, etc. ‚Deep‘ surface depths detected (snow, water, mud)“;
  do blackboardu se píše např. `SurfaceDepth 0.4`, `SurfaceName SNOW_LOOSE` (slajdy). „Difficult terrain ought to take its
  toll – Sell with visual, ‚feel‘ and speed changes“ a **„speed penalties“** podle terénu, nákladu a síly plemene (slajdy).
- **Překážky:** predikce dráhy („Forward integration of controller to produce path. Navmesh and physics casts to
  validate“), u hráče „casting solution“ (slajdy); při zjištěné srážce kůň boční složkou uhne, ale ztlumili to, aby hráč
  „can still barrel straight into a tree“ (gamedeveloper).
- **Útes:** hrany útesů ručně označené, kůň zastaví před hranou podle vzdálenosti, rychlosti a fáze kroku („Translation To
  Goal, Foot or ‚Beat‘ Cycle, Orientation To Goal ++ MARKUP!“ – slajdy; gamedeveloper).
- **Jezdec:** jezdec se řídí dvěma vrstvami dat z lokomoce koně, „No 1-1 requirement for horse and rider“; synchronizace
  přes „rhythm sync tags“/fázi; „Canter & Gallop are three-beat gaits, intervals between front foot strikes are irregular“ →
  více stop tagů (slajdy).
- **Rozsah:** ~6300 motions, ~2500 motion types, ~210 archetypů; ~3k animací koní ve 23 stylech, 19 plemen (slajdy).
- **Osobnost:** ocas/hlava vrstvené („layered head and tail shakes, stamina and agitation“), únava a zranění mění pohyb
  (slajdy „WELLBEING … Performance impaired“).
- **Voda:** kůň umí plavat, v hluboké vodě se může utopit; brodění mělkou vodou bez ztráty výdrže, plavání výdrž bere
  (fanouškovské průvodce, přesná hloubka nenalezena): https://www.pushsquare.com/guides/red-dead-redemption-2-how-to-clean-and-brush-your-horse ,
  https://steamcommunity.com/app/1174180/discussions/0/5532118063949031483
- **Zvuk kopyt:** zvukaři nahráli kopyta na různých površích a studovali přenos váhy v chodu (které kroky dopadají
  tvrději); rytmus je pro pocit z jízdy klíčový – článek Guardian citovaný ve shrnutí vyhledávání (přímý odkaz se
  nepodařilo otevřít); studentská analýza: https://charlieasound.myblog.arts.ac.uk/2023/11/06/sound-design-in-red-dead-redemption-2-a-comprehensive-analysis-and-review-of-cujo-sounds-insights/
- **Stopy kopyt / prach:** technický popis nenalezen.

### 1.2 Kingdom Come: Deliverance 1 a 2 (Warhorse)
Oficiální technické podklady k jízdě jsem **nenašel** (žádná přednáška ani dokumentace modování ke koni).
- **Chody:** krok, klus, cval, trysk – „The speed of your horse determines how fast it can walk, trot, canter and
  gallop“ (https://kingdomcomedeliverance.wiki.gg/wiki/Horse). Rychlosti v m/s nenalezeny; mod Realish Warhorses počítá
  s 10 m/s jako „konzervativní trysk“, jde o předpoklad autora, ne hodnotu z hry
  (https://mods.rpghq.org/Kingdom%20Come%3A%20Deliverance%202/310288).
- **Ovládání (KCD1):** dvojí stisk Shiftu = trysk (https://forum.kingdomcomerpg.com/t/unrealistic-horse-controls-solved/62811);
  hráč si stěžuje, že z cvalu do trysku jde jen přes klus a kůň nezastaví hned po přitažení otěží (tamtéž).
  KCD2: Left Ctrl = zpomalit koně, V = pohladit (https://www.shacknews.com/article/142953/pc-keybindings-controls-kcd2).
- **Držení cesty:** „give the horse its head and begin cantering without steering“ → kůň „will stick to the path you're
  on“ (wiki.gg). KCD2 průvodce: „You don't have to turn if you ride along a path“ (úryvek,
  https://ripvvaq.pages.dev/posts/horse-guide-in-kingdom-come-deliverance-2). Hráči chtějí přepínač „auto-horse“ vypnout
  (https://forum.kingdomcomerpg.com/t/several-issues-id-like-to-see-patched-changed/56729).
- **Výdrž:** ubývá v trysku, zelený pruh jen na koni; když se kůň při nízké výdrži dál žene, shodí jezdce (wiki.gg).
  KCD2 průvodce: při nule kůň spadne do kroku a trysk znovu až od ~30 % (úryvek, https://lootlore-d2ce2.web.app/en/kingdom-come-deliverance-2/mechanics/kcd2-horse-riding-skill-guide – nízká důvěryhodnost).
- **Odvaha (courage):** kolik hluku a rozruchu kůň snese, než se splaší (wiki.gg).
- **Les:** v KCD2 se jezdec pohledem dolů skloní pod větve („looking down makes you duck under branches while riding“ –
  titulek https://www.gamesradar.com/games/rpg/kingdom-come-deliverance-2-has-another-secret-skill-and-this-one-is-an-absolute-game-changer-looking-down-makes-you-duck-under-branches-while-riding-your-horse ; text článku nedostupný).
  Hráči hlásí uvíznutí koně v keřích a na kolizích stromů (https://forum.kingdomcomerpg.com/t/bug-stucked-with-horse-in-bushes/61855;
  https://forum.kingdomcomerpg.com/t/trees-and-bushes/40249 – spíš KCD1).
- **Kamera:** jen 1. osoba; hráčům vadí houpání hlavy koně v záběru („Watching the horse's head bob up and down on the
  screen gives me a headache“), v traileru byl svět „very smooth and stable“
  (https://forum.kingdomcomerpg.com/t/a-plea-for-the-optional-3rd-person-view-when-mounted/28317).
- **Mocap:** pro KCD2 snímali skutečného koně (https://www.gamesradar.com/games/rpg/if-you-liked-red-dead-redemption-2s-ultra-realistic-horses-kingdom-come-deliverance-2-devs-also-used-a-real-horse-in-the-motion-capture-studio);
  jestli to šlo do herních animací, nepotvrzeno.
- **Voda, svah, překážky u KCD2:** nenalezeno.

### 1.3 The Witcher 3 (Klepna / Roach)
- Držený sprint = cval, dvojklik a držení = trysk; dokud se drží jen sprint, kůň sám jede po cestě a **na cestě v
  automatu výdrž neubývá** (úryvek z Nexus https://www.nexusmods.com/witcher3/mods/5513 a
  https://steamcommunity.com/app/292030/discussions/0/361787186432984012). Pustí-li hráč řízení, kůň se vrátí na „autopilota“
  (úryvek, Steam). Na rozcestí nemusí vybrat správnou větev; nejlépe funguje na souvislé cestě (úryvek, průvodce).
- Remaster zachoval sledování cesty; volba „Use New Horse Controls“ (https://primagames.com/tips/the-witcher-3-remastered-updated-horse-controls).
- Trysk bere výdrž sedla, cval ne (úryvek, https://consolepulse.com/multiplatform/the-witcher/guides/the-witcher-3-roach-gear-stamina-fear-guide);
  při vyčerpání zpomalí do cvalu (úryvek, Nexus fórum).
- Klepna zastaví před útesy, horami a vodou (úryvek, https://www.nexusmods.com/witcher3/mods/7229);
  v modovaném skriptu `exploration.ws` je `WATER_MAX_DEPTH = 1.0` jako „vanilla water depth“ (úryvek, Nexus 12084) –
  tj. vodu hlubší než ~1 m kůň odmítne (odvozeno, neověřeno ve hře).
- Strach: při plném měřáku strachu se vzepne a shodí Geralta; klapky na oči zvyšují mez (+20 až +60) (úryvek, consolepulse).
- Rychlosti v m/s: nenalezeno.

### 1.4 Zelda: Breath of the Wild / Tears of the Kingdom
- Výdrž = počet „ostruh“ (3–5 u divokých koní), každá ostruha = krátký trysk (úryvek, https://www.zeldadungeon.net/wiki/Horse_(Breath_of_the_Wild)).
- Kůň jede sám po cestách z mapy, ne po malých odbočkách; starší verze wiki: v plném trysku cestu nesleduje, novější: při
  plném poutu ano, ale ve velké rychlosti může vybočit (úryvek, tamtéž).
- „The horse you're riding will avoid trees and obstacles of its own accord“ (https://gamingbolt.com/15-new-features-that-you-may-not-know-about-the-legend-of-zelda-breath-of-the-wild/13);
  GameRant to naopak uvádí jako potřebné zlepšení (https://gamerant.com/legend-of-zelda-breath-of-the-wild-2-horse-riding-changes-needed/) – nejasné.
- Voda, svah, rychlosti: nenalezeno.

### 1.5 Ghost of Tsushima
- Krok a klus podle vychýlení páčky, L3 = trysk (opakovaný stisk nic nemění); **chybí cval** mezi klusem a tryskem a
  hráči/recenzenti to kritizují; v trysku horší řízení
  (https://www.themanequest.com/blog/2023/5/1/the-horses-in-ghost-of-tsushima-wonderful-details-and-fundamental-problems;
  https://outsidergaming.com/ghost-of-tsushima-complete-controls-guide-for-ps4/).
- Skok nelze vyvolat, kůň přeskočí sám, když je třeba (themanequest). Nasedání a sesedání bez úplného zastavení (tamtéž).
- Navigace větrem místo čáry na zemi (https://www.thesixthaxis.com/2020/05/14/ghost-of-tsushima-photo-mode-combat-armor-guiding-wind-navigation-state-of-play/).

### 1.6 Mount & Blade, Mordhau, Chivalry
- Bannerlord: staty Speed / Maneuver / Charge, převod na m/s nenalezen (https://gamersdecide.com/articles/mount-and-blade-2-bannerlord-best-horses).
- Mordhau, Chivalry: nenalezeno.

### 1.7 Skutečný kůň (pro srovnání čísel)
- Rychlosti: krok ~1,9 m/s, cval 4,4–7,5 m/s, trysk 11–13 m/s (https://en.wikipedia.org/wiki/Horse_gait); islandští koně
  krok 1,5–2,2, klus 4,5–8,6, cval 5,8–9,8, trysk 7,9–13,5 m/s (SLU, citováno v `reserse_potok_1osoba_kun.md`).
- Svislý pohyb těžiště koně v klusu průměrně 53 mm (https://madbarn.com/research/body-centre-of-mass-movement-in-the-sound-horse);
  v kroku kohoutek dvakrát za krok nahoru/dolů (https://pub.epsilon.slu.se/id/document/19909561). Amplituda hlavy/trupu
  jezdce v cm v klusu/cvalu: nenalezeno.
- Svah: lesní správa USA – koně a muly zvládnou trvalé stoupání přes 10 %, „even 20 percent“, návrh stezek 5–12 %
  (https://www.fs.usda.gov/t-d/pubs/htmlpubs/htm07232816/page08.htm). 20 % ≈ 11,3° (odvozeno). Mez, kdy kůň svah odmítne:
  nenalezeno.
- Hloubka brodu pro koně: tvrdé číslo nenalezeno; rozhoduje hloubka i proud (https://outdoors.codidact.com/q/55137;
  https://www.horsekeeping.com/horse_riding_and_mounted_training/crossingwater.htm).

---

## 2. Technika: IK kopyt, svah, klouzání, přechody

- **RDR2:** samotné IK nestačilo, svah řeší animace sklonu + IK (viz 1.1). Pohyb ze automaticky vytažených rysů animací
  místo ručních blend stromů („Problems with Blend Trees? Scaled badly …“ – slajdy). Termín „motion matching“ v přednášce
  není.
- **Motion matching (Ubisoft, For Honor GDC 2016, Simon Clavet):** https://gamedeveloper.com/programming/most-inspiring-game-animation-tech-talks-of-2016 ;
  použití na koně/čtyřnožce: nenalezeno.
- **Pánev na nejnižší nohu:** posouvat pánev jen dolů k nejnižšímu dotyku, nikdy nahoru (https://docs.vulkan.org/tutorial/latest/Advanced_glTF/Procedural_Animation_IK/04_foot_placement.html;
  https://gamedev.net/blogs/entry/2264506-matching-feet-to-terrain-using-ik).
- **Čtyřnožec:** promítat zvlášť pánev i hrudník, aby přední i zadní nohy došly na terén (Houdini Adapt to Terrain:
  https://www.sidefx.com/ja/docs/houdini/nodes/sop/kinefx--adapttoterrain.html). Náklon/klopení z normály terénu do
  aim offsetu (https://forums.unrealengine.com/t/foot-ik-for-quadruped/371250). Výpočet náklonu z rozdílu výšek předních a
  zadních kopyt: konkrétní zdroj nenalezen.
- **Kopyto:** paprsek dolů nad „domovskou“ polohou nohy, normála natočí kopyto; jen srovnat s normálou nestačí
  (https://github.com/willymcgeejr/UnityProceduralAnimation). Bez cíle kolene se noha láme do divných úhlů, IK „cuká“
  (https://forum.godotengine.org/t/how-to-implement-foot-leg-ik-in-godot-4-4/112274).
- Horse IK v UE5 (Hanger 13, 5 videí): https://80.lv/articles/check-out-free-tutorials-on-ik-solution-for-horse-locomotion-system
  (obsah jen ve videích, nepřečteno).
- **Klouzání a sync:** samotný sync neodstraní klouzání, kontakty kopyt musí být ve stejné fázi v obou klipech
  (https://forum.godotengine.org/t/blendspace-animation-transitions-look-wrong/132692).

### Co jde v Godotu 4.4
- `SkeletonModifier3D` (od 4.3): vlastní `_process_modification()`, běží **po** AnimationMixeru; potomci ve 4.4:
  LookAtModifier3D, SkeletonIK3D (zastaralý), SpringBoneSimulator3D, RetargetModifier3D… – **žádný TwoBoneIK3D**
  (https://docs.godotengine.org/en/4.4/classes/class_skeletonmodifier3d.html). Dvoukloubové IK kopyt = vlastní řešič
  (trojúhelník kyčel–koleno–kopyto, stejný princip jako `_ik_ruky` v `telo.gd`).
- Nové IK uzly (IKModifier3D, TwoBoneIK3D, FABRIK3D, CCDIK3D…) přišly až v Godotu 4.6 (https://godotengine.org/releases/4.6/;
  https://www.strayspark.studio/blog/godot-46-inverse-kinematics-procedural-animation).
- `AnimationNodeBlendSpace2D` ve 4.4: jen `sync` (bool, výchozí false – při váze 0 se klipy zastaví), `blend_mode`
  INTERPOLATED/DISCRETE/DISCRETE_CARRY; `sync_mode` ve 4.4 **není** (https://docs.godotengine.org/en/4.4/classes/class_animationnodeblendspace2d.html).
- LookAtModifier3D (4.4) se hodí na natočení hlavy koně za směrem / k cíli (tamtéž, seznam potomků).

---

## 3. Kamera z koně v 1. osobě

- **Kde je oko:** KCD – kamera předsunutá před tělo, pohled dolů působí nepřirozeně (Steam, citováno v
  `reserse_potok_1osoba_kun.md`); true-first-person (Piquet, UE4) – kamera na kosti hlavy, yaw vůči tělu ±91°
  (https://gamedeveloper.com/programming/true-first-person-camera-in-unreal-engine-4). Konkrétní výška oka nad sedlem v
  žádné hře: nenalezeno.
- **Houpání:** RDR2 má volbu „First Person Head Bobbing“ (Reduced odstraní houpání při střelbě z koně), vypínač „First
  Person Horse Riding“ (při nevolnosti jízda ve 3. osobě) a „Auto Level Camera“ (https://www.gamerevolution.com/?p=450339;
  https://gamesradar.com/best-red-dead-redemption-2-settings). KCD: hráčům je zle z houpání hlavy koně (viz 1.2).
  Star Citizen: stabilizace oka na vzdálený bod odstranila ~80 % houpání (https://kotaku.com/star-citizens-first-person-view-is-based-on-birds-1787021141).
  Xbox Accessibility Guidelines: vyhnout se opakovanému pohybu obrazu nahoru/dolů, nabídnout nastavitelnou intenzitu
  houpání (https://devdocs.xbox.com/gaming/accessibility/xbox-accessibility-guidelines/117). **Amplituda v cm v hrách:
  nenalezeno.**
- **FOV při trysku:** údaj z her s koněm nenalezen; mod Skyrim výslovně ruší změnu FOV při sprintu kvůli pohodlí
  (https://www.nexusmods.com/skyrim/mods/47086 – úryvek).
- **Tělo jezdce:** Skyrim Improved Camera – tělo a stín v 1. osobě i na koni (https://www.nexusmods.com/skyrimspecialedition/mods/93962);
  Enhanced Camera – na koni omezení úhlu kamery a nastavení proti probíjení (https://www.nexusmods.com/skyrim/mods/57859).
  KCD – ruce na otěžích, recenze zmiňuje probíjení rukou (citováno v `reserse_potok_1osoba_kun.md`).
- **Směr koně vs. pohled (RDR2):** hráčům vadí, že kamera v 1. osobě nesleduje zatáčení koně; rada nastavit ovládání
  „horse relative“ (https://steamcommunity.com/app/1174180/discussions/0/3178985258880231953 – anekdota).

---

## 4. Povrchy pro chůzi i koně

- **Detekce:** paprsek dolů + metadata/skupina kolizního těla, Area3D zóny, vrstvy kolizí
  (https://reddit.birdcat.cafe/r/godot/comments/1lb2rjy/any_way_to_make_dynamic_footsteps_in_godot_with_a); u terénu
  vzorkovat splat mapu v poloze hráče a vzít převládající kanál (https://discussions.unity.com/t/detecting-terrain-texture-for-footsteps/781388);
  Flax: paprsek → fyzikální materiál, funguje i s vrstvami terénu (https://docs.flaxengine.com/manual/physics/tutorials/footsteps.html).
  Godot: doplněk „Godot Material Footsteps“ (materiál povrchu, Terrain3D) – https://github.com/COOKIE-POLICE/godot-material-footsteps ;
  Terrain3D až 32 textur, typ z kanálů (https://github.com/TokisanGames/Terrain3D,
  https://forum.godotengine.org/t/how-can-i-make-with-a-raycast-foot-step-sounds-on-a-terain3d/143466).
  U nás je povrch v datech (osy cest, voda, atlas hlíny cest ve `svet.gd`) – stačí dotaz do dat, splat mapa netřeba.
- **Zvuk kopyt:** RDR2 nahrávky na různých površích + váha kroku (viz 1.1). Kadence: cval/trysk tříběh, krok čtyřtakt
  (RDR2 slajdy; https://en.wikipedia.org/wiki/Horse_gait).
- **Rychlost podle povrchu:** RDR2 „speed penalties“ podle terénu a hluboký povrch (sníh, voda, bláto) – slajdy. KCD2:
  perk snižuje úbytek výdrže **mimo cestu** o 5 % (úryvek, https://gameleap.com/articles/kingdom-come-deliverance-2-all-horsemanship-perks)
  → mimo cestu je jízda náročnější (odvozeno). Konkrétní násobky: nenalezeno.
- **Prach, stopy:** na mobilu jsou decaly drahé (průsvitné, sčítají se), držet je malé, krátce žijící, s dosahem
  viditelnosti (https://forums.unrealengine.com/t/dbuffer-and-mesh-decals-on-mobile-not-a-good-choice-high-shader-complexity-and-other-issues/567772;
  https://developer.unigine.com/forum/topic/5493-wagon-wheels-and-footprints/); GPU částice na mobilu otestovat, někde
  byly CPU rychlejší (https://communityforums.atmeta.com/discussions/dev-unreal/gear-vr-gpu-particles-and-horrible-performance/633424).
  Jak to řeší KCD/RDR2: nenalezeno.

---

## Co z toho porovnat s naší hrou
Přečteno: `scripts/kun.gd`, `pravidla/svet/jizda.json`, napojení zvuku v `scripts/main.gd:481` a `scripts/life.gd`
(`kopyto_sound`, `surface_at`), kamera v `scripts/player.gd`. Seřazeno podle přínosu pro hráče. Nic není změřeno ve
hře – jsou to rozdíly v kódu a hypotézy, ne potvrzené chyby.

1. **Zastavení před vodou/srázem se kontroluje jen 1,6 m před koněm, brzdná dráha je ale mnohem delší.** `kun.gd`
   bere výšku a vodu v bodě `global_position + vpred * 1.6`, `brzdeni` 4,0 m/s² → z trysku 10,5 m/s brzdná dráha
   ≈ 10,5² / (2 · 4) ≈ 13,8 m (odvozeno). V trysku tedy kůň nejspíš sjede do hluboké vody nebo přes sráz dřív, než
   zastaví. RDR2 zastavuje před útesem podle vzdálenosti, rychlosti a fáze kroku. Hypotéza k ověření snímkem/testem:
   dohled podle rychlosti (jako `cesta_dohled_za_rychlost`) a čísla do `jizda.json`.
2. **Povrch pod kopyty se neurčuje z dat světa.** `kun.gd` posílá vždy `"cesta"`, `main.gd` to přepíše na
   `life.surface_at()`, ale ta zná jen místnosti, okolí hradu (dirt/wood), ruiny (listí) a vodu – jinak všude `"grass"`.
   Na cestě, kameni, mostě, u brodu tak kopyta zní jako tráva. RDR2 i KCD mají zvuk podle povrchu; data cest a vody už
   ve `svet.gd` jsou (osy cest, `od_vody`). Totéž platí pro kroky pěšího hráče.
3. **Rychlost nezávisí na povrchu ani na hustém lese.** Zpomalení je jen na svahu (`svah_max_sin` → max. krok) a srážka
   (`is_on_wall` → rychlost × 0,5). RDR2 má „speed penalties“ podle terénu a hlubokých povrchů (bláto, voda, sníh),
   KCD2 má vyšší úbytek výdrže mimo cestu. Návrh: násobek rychlosti/výdrže podle povrchu do `jizda.json`.
4. **Tělo koně se na svahu nenaklání a kopyta nemají IK.** `kun.gd` nastavuje jen `rotation.y`. RDR2 tvrdí, že samotné
   IK nestačí – potřebuje i náklon těla/animace podle sklonu. V Godotu 4.4: náklon modelu z výšek terénu pod předními a
   zadními kopyty + vlastní dvoukloubové IK v `SkeletonModifier3D` (jako `kun_zivy.gd`); TwoBoneIK3D až ve 4.6.
5. **Překážky: kůň se nevyhne, jen se o polovinu zpomalí.** RDR2 předvídá srážku a mírně uhne bokem (záměrně slabě),
   BotW se prý stromům vyhýbá sám, KCD hráči nadávají na uvíznutí v keřích. Návrh: krátký paprsek/tvar dopředu, mírné
   boční uhnutí, a při čelním nárazu zastavení (případně vzepnutí – kůň_henry má klip Buck).
6. **Chybí klus.** Máme krok 1,7 / cval 6,5 / trysk 10,5 m/s (cval i trysk = jeden klip Gallop, tempo až × 1,6).
   RDR2 a KCD mají 4 chody; u GoT recenze kritizují chybějící mezichod. Skutečný kůň: klus 4,5–8,6 m/s, cval 4,4–7,5 m/s.
   Náš cval 6,5 m/s je v horní půlce rozsahu skutečného cvalu; v seznamu animací `kun_henry` v `jizda.json`
   `model_popis` klus uveden není (seznam končí „...“) – ověřit `_ap.get_animation_list()`, pak buď klip, retarget, nebo
   vědomě 3 chody.
7. **Voda: kůň se zastaví nad hloubkou 1,1 m a neplave, i když model má klip Swim.** Witcher 3 je na tom stejně (mez
   ~1 m), RDR2 kůň plave a plavání bere výdrž. Pro malý svět s rybníky stačí současné odmítnutí, ale bylo by dobře, aby
   kůň před vodou zpomalil plynule (souvisí s bodem 1) a ve brodu zpomalil a šplouchal (zvuk `voda` už v `life.gd` je).
8. **Houpání kamery jde přímo do oka (4 / 9 cm sinus) a nejde vypnout.** KCD hráči si stěžují na nevolnost, RDR2 má
   volbu „Reduced“ a vypínač jízdy v 1. osobě, Xbox guidelines doporučují nastavitelnou intenzitu, Star Citizen
   stabilizací ubral ~80 %. Návrh: přepínač/posuvník houpání v Nastavení; skutečné těžiště koně v klusu se hýbe ~5 cm.
   FOV se při trysku nemění (72°) – pro změnu FOV jsem doklad z her s koněm nenašel, mody ji naopak ruší kvůli pohodlí.
9. **Přechody chodů jsou skoky rychlosti s konstantním zrychlením (2,2 m/s², brzda 4,0) a jednorázový Run_Stop.**
   RDR2 zavrhl jednorázové přechody a dělá plynulé cykly zrychlení/zpomalení (při brzdění hlava nahoru, tělo
   „sebrané“). Konkrétní časy z jiných her: nenalezeno. Pro nás levná varianta: aditivní náklon hlavy/krku v
   `kun_zivy.gd` podle zrychlení.
10. **Otáčení kolem středu, bez bočního posunu.** RDR2 otáčí kolem předních nohou a zatáčí s „drift“. U nás `rotation.y`
    kolem počátku koně. Menší přínos, ale viditelné při otáčení na místě (zadek by měl opisovat oblouk).
11. **BlendSpace2D bez `sync`.** `kun.gd` nenastavuje `bs.sync` (výchozí false) a mísí Walk a Gallop s různou délkou;
    sync stejně nepomůže, pokud kontakty kopyt nejsou ve stejné fázi (fórum Godot). Hlídat klouzání kopyt na snímku při
    rychlosti mezi krokem a cvalem.
12. **Kadence zvuku kopyt v kroku:** jeden zvuk za `krok_delka_m[0]` = 1,6 m. Krok je čtyřtakt – pokud vzorek
    `kopyto_krok_*` obsahuje jen jeden úder, je zvuků 4× méně, než by mělo být. Ověřit poslechem obsahu vzorků (neověřeno).
13. **Držení cesty a výdrž sedí s KCD/W3/BotW:** cesta jen bez řízení do strany, výdrž jen v trysku, při nule do cvalu a
    trysk znovu od třetiny (KCD2 průvodce uvádí ~30 % a pád do kroku). Rozdíl: W3 na cestě v automatu výdrž nebere; BotW
    a W3 ve velké rychlosti od cesty spíš uhnou – u nás naopak po cestě i v trysku otáčivost kroku (`_po_ceste`).
14. **Prach a stopy kopyt nejsou.** Na tabletu jen malý počet CPU částic na cestě/hlíně při cvalu a trysku; decaly stop
    drahé – nejníž v pořadí.
15. **Oko jezdce:** `oci_nad_sedlem_m` 0,88 a `oci_pred_hlavou_m` 0,18 jsou podle `jizda.json` odhad („overit snimkem
    sedlo_dolu“); hodnoty z jiných her nenalezeny. Rozhled ±95° odpovídá ±91° z true-first-person (Piquet).
