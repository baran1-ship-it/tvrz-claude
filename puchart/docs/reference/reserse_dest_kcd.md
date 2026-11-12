# Rešerše: déšť v Kingdom Come: Deliverance 1 a 2 → co z toho pro Puchart

Rešerše z 12. 11. 2026. Cíl: Godot 4.7.2 Compatibility, tablet Xiaomi Pad 8 (Adreno).
Značení: **DOLOZENO** = oficiální zdroj (patch notes, dokumentace CryEngine/Godot), **HRÁČI** = shodné výpovědi
hráčů (fórum, Steam), **NEOVERENO** = nenašla jsem žádný zdroj, nebo jen jeden nespolehlivý.

## 1. Kdy a jak často prší

| Otázka | Zjištění | Stav |
|---|---|---|
| Délka herního dne KCD1 | Čas běží 15× rychleji než skutečný: 1 herní hodina = 4 min, **24 h = 96 min (1 h 36 min)**. Zdroje: [Steam KCD1 „Day/Night Cycle“](https://steamcommunity.com/app/379430/discussions/0/1640916564848700959) („KCD time is 15x faster than IRL… Every 4min IRL is 1hr in game“), [fórum Timescale 1:1](https://forum.kingdomcomerpg.com/t/timescale-1-1/42922) („A time scale of 15:1“). | HRÁČI (shodné, konzolové proměnné `t_scale`) |
| Délka herního dne KCD2 | Stejně: výchozích 15 herních minut za 1 skutečnou minutu (popis módu [Nexus KCD2 mod 1277](https://www.nexusmods.com/kingdomcomedeliverance2/mods/1277), viděno jen ve výsledku vyhledávání, stránka vrací 403). | HRÁČI |
| Jak často prší | Oficiální čísla nejsou. Hráči KCD1 píšou „prší skoro každý den“ ([fórum 57450](https://forum.kingdomcomerpg.com/t/lack-of-weather-diversity-and-rain-while-sunny/57450)), ale jiní za 100 h „nikdy neviděli opravdový déšť“ (myslí tím tmavou bouři, [Steam KCD1](https://steamcommunity.com/app/379430/discussions/0/1760230682466075902)). U KCD2 se stěžují, že prší příliš často („Waaaay too much rain“, [Steam KCD2](https://steamcommunity.com/app/1771300/discussions/0/669453176279186404)). | **NEOVERENO** (počet herních dní mezi dešti nikde) |
| Jak dlouho prší | Oficiální čísla nejsou. Extrémy byly chyby: v KCD1 po patchi 1.03/1.3 pršelo „7 herních dní / 10 h“ ([fórum 38668](https://forum.kingdomcomerpg.com/t/it-s-been-raining-for-almost-7-game-days-now-and-nearly-10-hours/38668)), v KCD2 po vydání déšť trval 5 s, pak přestal a zase začal ([Steam KCD2](https://steamcommunity.com/app/1771300/discussions/0/600771313357889454)). Day‑1 patch KCD2 opravoval „rain never starting at high framerates“ a chyby délky a síly deště ([Sportskeeda, day‑1 patch notes](https://www.sportskeeda.com/esports/kingdom-come-deliverance-2-day-1-patch-notes-provided), jen ve výsledku vyhledávání). Patch 1.2: „Fixed weather continuity“ ([Dexerto 1.2](https://www.dexerto.com/gaming/kingdom-come-deliverance-2-1-2-patch-notes-3161815/)). | Délka **NEOVERENO**; že délka a síla deště jsou parametry systému, je DOLOŽENO |
| Den i noc | Prší i v noci. Hráči si stěžují, že noční déšť „je hrůza, není nic vidět“ ([Steam KCD2](https://steamcommunity.com/app/1771300/discussions/0/601895662819293998)). Pršelo i za jasné noční oblohy (chyba KCD1, [fórum 38668](https://forum.kingdomcomerpg.com/t/it-s-been-raining-for-almost-7-game-days-now-and-nearly-10-hours/38668)). | HRÁČI |
| Náhoda nebo skript | Obojí. Volný svět má **pravděpodobnosti** počasí: mód „Stormy Skies“ píše, že „nemění vanilla pravděpodobnosti bouřek“, a jiný modder je měnil, aby bylo víc lijáků ([Nexus KCD1 1982, příspěvky](https://nexusmods.com/kingdomcomedeliverance/mods/1982?tab=posts), jen ve výsledku vyhledávání). Příběhové scény počasí nastavují skriptem: patch 1.9 KCD1 „Fixed weather during cutscene in which player fights Runt first, so it now rains again“ ([patch 1.9](https://consolepcgaming.com/?p=29662)). | DOLOŽENO (skript), HRÁČI/módy (pravděpodobnosti) |
| Přechody | Konkrétní fáze (zatažení → mrholení → liják → doznívání) nikde nepopisují. Známá chyba obou dílů: déšť za slunce a bez mraků („Cloudiness seems to have no effect on the chance of rain“, [Steam KCD1](https://steamcommunity.com/app/379430/discussions/0/1760230682466075902)). Skutečná bouře má tmavé mraky a „mid-day can turn to night“ (tamtéž). | Fáze **NEOVERENO**; nesoulad oblohy a deště = známá vada, nekopírovat |
| Bouřky, blesky | Ano: hrom a blesky, bouřka je samostatný stav. Mód, který vypíná déšť, píše „Thunder and lightning … will still happen if it's storming“ ([Nexus KCD1 93](https://www.nexusmods.com/kingdomcomedeliverance/mods/93)). Patch 1.2 KCD2: „Removed lightning underground and indoors during a storm“ ([Dexerto](https://www.dexerto.com/gaming/kingdom-come-deliverance-2-1-2-patch-notes-3161815/)). Hráči hlásí blesky bez bouře a blikání světla při bouři ([Steam KCD2](https://steamcommunity.com/app/1771300/discussions/0/601895828709184385)). | DOLOŽENO |

## 2. Jak déšť vypadá a co dělá ve hře

- **Kapky:** v KCD2 je to stejný efekt jako v KCD1 (CryEngine): závoj kolem kamery, hráči mu říkají „filtr přes kameru“ a „vypadá jako PNG“. Jeden popisuje „3 tvary jako americký míč kolem pohledu, které se točí s tebou“, tedy texturovaná tělesa kolem kamery, ne jednotlivé částice ([Steam KCD2](https://steamcommunity.com/app/1771300/discussions/0/601895662819293998), [Steam KCD2](https://steamcommunity.com/app/1771300/discussions/0/600771313357889454)). Podle hráče déšť v KCD1 hodně snižoval výkon a v KCD2 je zjednodušený (tamtéž). HRÁČI.
- **Kritika:** velká vlna stížností na déšť v KCD2 (Reddit: „by far the biggest letdown“), ale „mokré povrchy a tvořící se louže vypadají hezky“ ([ScalaCube](https://scalacube.com/blog/news/kingdom-come-deliverance-2-players-are-not-happy-about-the-games-rain), [GamePro](https://www.gamepro.de/artikel/kingdom-come-deliverance-2-fans-enttaeuscht-von-regen,3428308.html), [OpenCritic/GameRant](https://opencritic.com/news/12745/kingdom-come-deliverance-2-players-arent-happy-about-the-games-rain)). Na PS4 v KCD1 měl déšť vzhled „rozstříhaného papíru“ ([fórum 50047](https://forum.kingdomcomerpg.com/t/frequent-rains/50047)).
- **Dohlednost a mlha:** v noci za deště je vidět velmi málo (viz výše). Volumetrická mlha v KCD1 je jen na PC Ultra / `e_VolumetricFog=1`. Video [VolumetricFog ON/OFF (Rain)](https://www.youtube.com/watch?v=ADv75ifo9ks) a [fórum 57450](https://forum.kingdomcomerpg.com/t/lack-of-weather-diversity-and-rain-while-sunny/57450) (moderátor/hráč MattP598). HRÁČI.
- **Mokré povrchy a louže (CryEngine Rain entity, DOLOŽENO):** parametry `Amount`, `DiffuseDarkening` („how dark the puddles and rain are“), `PuddlesAmount` (hloubka a jas loužích podle normály povrchu a masky), `PuddlesMaskAmount`, `PuddlesRippleAmount` (kroužky v loužích), `SplashesAmount` (dopady), `RainDropsAmount/Speed/Lighting`, `Radius`, a **okluze**: nemokne pod střechou, „handling object occlusion and applying a wet effect to all affected areas“ ([CryEngine V – Environment Entities](https://cryengine.com/docs/static/engines/cryengine-5/categories/23756816/pages/29796935), [CryEngine V – Effects Components](https://cryengine.com/docs/static/engines/cryengine-5/categories/23756816/pages/44966055)). Že KCD používá právě tuto entitu, nikde přímo nepíšou (**NEOVERENO**), ale `r_Rain 0/1` funguje v KCD1 i KCD2 ([Steam KCD2](https://steamcommunity.com/app/1771300/discussions/0/601895662819293998)).
- **Louže rostou s deštěm a voda teče z kopce** (alfa KCD1, video moderátora Warhorse): [fórum 25891](https://forum.kingdomcomerpg.com/t/weather-effects-in-kingdom-come-deliverance/25891). DOLOŽENO pro alfu, pro vydanou hru NEOVERENO.
- **Kapky na vodě:** v KCD1 bylo vidět „rain hitting water“ ([fórum 38668](https://forum.kingdomcomerpg.com/t/it-s-been-raining-for-almost-7-game-days-now-and-nearly-10-hours/38668)). Při lijáku v KCD2 hráč „při pohledu dolů nevidí žádné šplouchání“ ([Steam KCD2](https://steamcommunity.com/app/1771300/discussions/0/601895828709184385)). HRÁČI.
- **Mokré postavy:** v KCD2 déšť nesmyje krev ani špínu z oblečení ([Steam KCD2](https://steamcommunity.com/app/1771300/discussions/0/601895917151378452)). Lesk mokré kůže nebo zbroje nikde doložený není (NEOVERENO, spíš chybí).
- **Zvuk:** hrom a zvuk deště hráči chválí („the sound effects are top notch“, „the thunder is awesome“). Uvnitř má být déšť tlumený nebo neslyšný: hotfix 1.5.2 (12/2025) „Fixed rain incorrectly being heard in several interiors“ ([mp1st 1.5.2](https://mp1st.com/title-updates-and-patches/kingdom-come-deliverance-2-hotfix-1-5-2-applies-improvements-via-update-1-052)). Hráči si oblíbili kovárnu za bouřky („Maximum comfy“). DOLOŽENO.
- **Déšť uvnitř = chyba**, opravovaná opakovaně (Trosky 1.3, stodola Zhelejov 1.2, kláštery 1.5.2, déšť v inventáři 1.2): [dsogaming 1.3](https://www.dsogaming.com/patches/kingdom-come-deliverance-2-patch-1-3-released-detailed/), [Dexerto 1.2](https://www.dexerto.com/gaming/kingdom-come-deliverance-2-1-2-patch-notes-3161815/). Ponaučení: okluze (střechy, interiéry) je nutná.
- **Hratelnost:**
  - Louče v KCD1 za deště hoří dál („A torch still works in the rain“, [fórum 38668](https://forum.kingdomcomerpg.com/t/it-s-been-raining-for-almost-7-game-days-now-and-nearly-10-hours/38668)). HRÁČI. Pro KCD2 je to **NEOVERENO**: weby tvrdící „déšť zhasne louč za 2 min“ jsou SEO bez zdroje.
  - Zhášení ohňů deštěm je jen přání hráčů ([fórum 61625](https://forum.kingdomcomerpg.com/t/a-quick-list-of-thatd-be-cool/61625)), NEOVERENO.
  - NPC: od patche 1.9 KCD1 „Many NPCs will now take cover from rain under roofs or trees“ ([patch 1.9](https://consolepcgaming.com/?p=29662)). DOLOŽENO. V KCD2 to podle hráčů moc nefunguje ([Steam KCD2](https://steamcommunity.com/app/1771300/discussions/0/601895917151378452)).
  - Za deště hůř vidí hráč, ale podle hráčů možná ne AI ([Steam KCD2](https://steamcommunity.com/app/1771300/discussions/0/601895828709184385)). NEOVERENO.

## 3. Videa a obrázky s deštěm

Názvy videí jsou z výsledků vyhledávání na YouTube (12. 11. 2026), obsah jsem neviděla.

**KCD1**
- https://www.youtube.com/watch?v=jGX_Az9R92I „KCD (water & weather effects ultra quality)“: bouře s mlhou na PC Ultra.
- https://www.youtube.com/watch?v=ADv75ifo9ks „KCD: VolumetricFog ON/OFF (Rain)“: srovnání mlhy za deště.
- https://www.youtube.com/watch?v=otuL1ZgpHwY „Immersive Rain Details – KCD“: detaily louží a mokrých povrchů.
- https://www.youtube.com/watch?v=NDN8uNQ2n-Q „KCD: Rain Effects Showcase“.
- https://www.youtube.com/watch?v=o5vNTNJM-RM „KCD 4K … Ultra Graphics Rain Walk“.
- https://www.youtube.com/watch?v=ZhBYSIlYljc „KCD rain“, https://www.youtube.com/watch?v=hC_C3Fx4LrQ „Beta Rain effect“, https://www.youtube.com/watch?v=DMXTJAK6hNw „Storm Improvement?“, https://www.youtube.com/watch?v=J1N43L1lm1A (PS4 déšť), https://www.youtube.com/watch?v=mw2BKDeKqrc (výkon za deště, GTX 1060).
- https://www.youtube.com/watch?v=RSRdRv1MtpY „The Art of Rain in KCD | Walk Through Thunderstorm“.

**KCD2**
- https://www.youtube.com/watch?v=td8hyBu5NBg „Sunny vs Storm Weather Comparison [4K] | Suchdol“: nejlepší srovnání stejného místa za slunce a za bouře (barva oblohy, světlo, mokrost).
- https://www.youtube.com/watch?v=20885uvB3Hs „Thunderstorm on a Medieval Farm (4K)“: statek, venkov, nejbližší atmosféře Puchartu.
- https://www.youtube.com/watch?v=y79X-oE0uLo a https://www.youtube.com/watch?v=KElXxKDXOwA: bouře a liják na hradě Trosky (hrad, nádvoří).
- https://www.youtube.com/watch?v=HPpmCab8JdE „Rain & Thunder in a Tower Room“: déšť zevnitř věže, tlumený zvuk.
- https://www.youtube.com/watch?v=9mCNCOVjzmA „Blacksmith, Rain and Thunder Ambience“: déšť z kovárny pod střechou.
- https://www.youtube.com/watch?v=T-EVONqawOg (Kutná Hora za bouře), https://www.youtube.com/watch?v=fFCK09Lvk3w (liják na venkově), https://www.youtube.com/watch?v=s_v3zI_T4YE (zataženo s deštěm, Ultra), https://www.youtube.com/watch?v=5q1cpKqZ83I (vzdálené hromy), https://www.youtube.com/watch?v=Hl5fhxe3rKk (hodinová smyčka zvuku), https://www.youtube.com/watch?v=_f3BtgKuRfQ (déšť v táboře ráno).
- Kritika: https://www.youtube.com/watch?v=me8AgXntxAA „The rain in KCD2 is… bad“, https://www.youtube.com/watch?v=Kzwii44ztzY „KCD2 it won't stop raining“.
- Módy s porovnávacími obrázky: [KCD2 mod 707 (nastavitelný déšť)](https://nexusmods.com/kingdomcomedeliverance2/mods/707), [KCD2 mod 1711 (Better Rain port)](https://nexusmods.com/kingdomcomedeliverance2/mods/1711), [KCD1 mod 1410 (méně viditelný déšť v noci)](https://nexusmods.com/kingdomcomedeliverance/mods/1410), [KCD1 mod 1982 Stormy Skies](https://www.nexusmods.com/kingdomcomedeliverance/mods/1982).
- Pro srovnání stejná technika v Crysis 3: https://www.youtube.com/watch?v=_e8NJ1l58lg.
- Jednotlivé statické screenshoty deště jsem dohledanými URL nedoložila (NEOVERENO). Nejrychlejší cesta: snímek z videa td8hyBu5NBg nebo 20885uvB3Hs.

## 4. Technika pro mobil (Godot 4.7.2 Compatibility, Adreno)

- **Kapky jako válec nebo obal kolem kamery se shaderem** (posouvaná textura čar, 2–3 vrstvy v různé hloubce) dělá i CryEngine/KCD (viz „americké míče kolem pohledu“). Na mobilu je to nejlevnější: několik desítek trojúhelníků, jedno kreslení, cena = průhledné pixely na obrazovce. Godot upozorňuje, že mobilní GPU (dlaždicové) trpí přepisováním pixelů (overdraw) a fill-rate. Doporučuje co nejméně průhledných objektů a co nejjednodušší shadery ([Godot – GPU optimization](https://docs.godotengine.org/en/stable/tutorials/performance/gpu_optimization.html), [Optimizing 3D](https://docs.godotengine.org/en/stable/tutorials/performance/optimizing_3d_performance.html)). Proto: max. 2 vrstvy, tenké čáry, `unshaded`, bez čtení hloubky, alfa nízká.
- **GPU částice:** Compatibility je umí (v tabulce rendererů chybí jen trails a SDF kolize, [Godot – renderers](https://docs.godotengine.org/en/stable/tutorials/rendering/renderers.html)). Pro déšť stačí řádově stovky krátkých čar kolem kamery, žádné kolize. Dopady na zem udělat buď pár částic jen v okruhu ~10 m, nebo vůbec ne, a místo nich kroužky v loužích shaderem.
- **Mokrost jako jeden globální parametr:** Godot má *global shader uniforms* dostupné ve všech typech shaderů a doporučuje je přesně pro „environmental effects that affect many objects“ ([Godot – shading language, Global uniforms](https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/shading_language.html)). Např. `mokrost` 0–1: albedo × (1 − 0,3·m) (tmavší), roughness × (1 − 0,6·m) (lesklejší), louže maskou podle normály nahoru a šumu. Odpovídá parametrům CryEngine `DiffuseDarkening` a `PuddlesAmount`. Mokrost musí po dešti pomalu klesat (schnutí).
- **Okluze (nepršet pod střechou a v interiéru):** nejlevnější je zóna (Area3D) „pod střechou / uvnitř“, která vypne závoj a ztlumí zvuk. Mapa okluze shora jako v CryEngine je na mobil zbytečná. KCD tu chybovalo opakovaně (viz výše).
- **Hotová řešení (zkontrolovat licenci v repu):**
  - [TCA Weather System](https://github.com/kS222138/TCA_Weather_System/): MIT, Godot 4.6+, déšť a částice „mobile-friendly culling“, `TerrainWetness` se schnutím, signál `rain_intensity_changed`. Podpora Compatibility v README neuvedená (NEOVERENO).
  - [Weather FX Free](https://github.com/Spyridon-Pikoulas/godot-weather-fx-free): Forward+/Mobile/**Compatibility**, Godot 4.3–4.7, závoj kolem kamery ukotvený ve světě, dopady, `fade_in()/stop()`. Licence **CC‑BY‑4.0** (nutné uvést autora), není CC0/MIT ([Asset Library](https://godotengine.org/asset-library/asset/edit/24427)).
  - [Rain Drop (floor effect)](https://godotshaders.com/shader/rain-drop-floor-effect/): CC0/MIT, kroužky na zemi. [Rain puddles with ripples](https://godotshaders.com/shader/rain-puddles-with-ripples-and-reflection/): CC0, ale je to post‑process na celou obrazovku, na mobil spíš ne. [Rain and Snow with Parallax](https://godotshaders.com/shader/rain-and-snow-with-parallax-scrolling-effect/): MIT, 2D canvas overlay.
- **Zvuk:**
  - [OpenGameArt „Rain loopable“](https://opengameart.org/content/rain-loopable): **CC0**, 4 smyčky po 25–45 s.
  - [OpenGameArt „Rain on window loop“](https://opengameart.org/content/rain-on-window-loop): CC0 podle vyhledávání, k použití uvnitř.
  - Freesound CC0 (licenci ověřit na stránce): [486270 déšť na střechu + louže](https://freesound.org/people/craigsmith/sounds/486270), [788147 liják](https://freesound.org/people/YouMightLikeThis/sounds/788147/).
  - Sonniss GDC bundle: royalty‑free, bez uvedení autora, nesmí se šířit jako samostatné zvuky. Není to CC0 ([GameFromScratch 2024](https://gamefromscratch.com/sonniss-27-5gb-sound-effect-giveaway-at-gdc-2024/)).
  - Kenney: zvuk deště v jeho balíčcích jsem nenašla (NEOVERENO).
  - Uvnitř hrát stejnou smyčku tlumenou (low‑pass na audio busu) a hlasitější kapání ze střechy.

## 5. Doporučení pro Puchart

**Co z KCD je doložené:**
- Herní den trvá 96 min (15:1).
- Prší ve dne i v noci.
- Počasí je v otevřeném světě náhodné s pravděpodobnostmi a v příběhových scénách nastavené skriptem.
- Bouřka s hromem a blesky je samostatný stav.
- Uvnitř déšť nemá být vidět a má být tlumeně slyšet.
- NPC se schovávají pod střechy a stromy.
- Mokré povrchy tmavnou a lesknou se, louže mají kroužky (parametry CryEngine).
- Louče v KCD1 za deště nezhasínají.

**Co doložené není:** jak často prší (počet dní mezi dešti) a jak dlouho. Žádná oficiální čísla neexistují. Hráči KCD1/2 si stěžují spíš na **příliš častý** déšť a na déšť za jasné oblohy. Návrh uživatelky (méně často) tedy jde správným směrem.

**Návrh pravidel (vlastní, ne převzato z KCD):**
- **Četnost:** v průměru **jednou za ~4 herní dny**. Náhodně, ale s pojistkami: aspoň 2 dny sucho po dešti, nejvýš 6 dní bez deště. Bouřka asi u každého 3. deště. Příběh může déšť vynutit nebo zakázat.
- **Délka:** **1–4 herní hodiny** (při 15:1 zhruba 4–16 min skutečného času), nikdy celý den. Bouřka kratší: 0,5–1,5 h lijáku.
- **Kdy:** kdykoli, i v noci. V noci jen slabší závoj a víc tmavé mlhy, aby bylo vidět (kritika KCD).
- **Průběh** (celkem vždy 1 plynulá křivka `intenzita` 0–1):
  1. Zatahování 20–40 herních min: obloha šedne, slunce slábne, zvedá se vítr. Déšť nesmí začít za jasné oblohy, to byla chyba KCD.
  2. Mrholení 10–20 min.
  3. Déšť nebo liják (vrchol). U bouřky blesky po 20–60 s, hrom se zpožděním podle vzdálenosti.
  4. Doznívání 15–30 min.
  5. Vyjasnění. Mokrost klesá ještě 1–2 herní hodiny, louže mizí poslední.
- **Vzhled:** 2 vrstvy závoje kolem kamery se shaderem, žádné částice nebo jen pár dopadů blízko. Globální `mokrost` pro všechny materiály (tmavší a lesklejší povrchy, louže na rovině), mlha hustší podle intenzity. Okluze přes zóny pod střechou a uvnitř.
- **Zvuk:** venku smyčka podle intenzity (slabý a silný déšť prolínat), uvnitř tlumená, hrom samostatně.
- **Hratelnost:** louče nechat hořet jako v KCD1. Otevřené ohně za lijáku můžou volitelně ztlumit plamen; zhasínání není doložené.
