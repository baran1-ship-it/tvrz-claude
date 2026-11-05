# Automatická kvalita – rešerše a návrh (5. 11. 2026)

Míša: „při nestíhání RAM nebo procesoru – aby hra jela plynule – zhoršení grafiky nebo vykreslování? ve hrách to tak
bývá?“ Ano. Upřesnění Míši (po porovnání s ChatGPT): dvě úrovně (jemná / nouzová), nečekat na pád pod 30 FPS, reagovat
na trend s rezervou, rozlišit GPU × CPU.

Kód: `scripts/kvalita.gd` · data: `pravidla/svet/kvalita.json` · test: `tools/test_kvalita.gd` · volba:
Nastavení → „Kvalita: automatická / ruční“ (výchozí zatím **ruční**, než se ověří na tabletu) · měřicí trasa: varianta `auto`.

## 1. Rešerše

### Enginy
| zdroj | co dělá | prahy / hystereze / oscilace | ohřev předem |
|---|---|---|---|
| **Unreal Dynamic Resolution** ([dok.](https://dev.epicgames.com/documentation/en-us/unreal-engine/dynamic-resolution-in-unreal-engine)) | mění jen rozlišení 3D (screen percentage 50–100 %) podle času GPU | rozpočet `FrameTimeBudget` 33,3 ms, cílová rezerva GPU `TargetedGPUHeadRoomPercentage` **10 %** (tj. cíl 90 % rozpočtu; [cvar wiki ze zdroje](https://indxzero.github.io/ue544cvarwiki/articles/r.dynamicres.targetedgpuheadroompercentage)), historie N snímků (`HistorySize`: krátká = šum, dlouhá = zpoždění), `MinResolutionChangePeriod` (min. snímků mezi změnami), `ChangePercentageThreshold` (malé změny se neprovádějí – „neblikat mezi skoro stejnými“), „panika“ po `MaxConsecutiveOverbudgetGPUFrameCount` snímcích nad rozpočtem; zvlášť `CPUBoundScreenPercentage` – když stojí na CPU, rozlišení nepomůže | ne (jen čas GPU) |
| **Unreal Scalability** ([dok.](https://dev.epicgames.com/documentation/en-us/unreal-engine/scalability-reference-for-unreal-engine)) | skupiny 0–3: rozlišení, dohled, stíny, postprocess, textury, efekty, vegetace (hustota) | – (presety) | – |
| **ADPF plugin pro Unreal** ([dok.](https://developer.android.com/games/engines/unreal/unreal-adpf)) | thermal headroom → úroveň Scalability | headroom **< 0,75** úroveň 3 (plná), **0,75–0,85** 2, **0,85–0,95** 1, **> 0,95** 0; dotaz 1× za s; navíc Performance Hint (CPU frekvence) | ano – headroom je předpověď |
| **Unity Adaptive Performance** ([dok.](https://docs.unity3d.com/Packages/com.unity.adaptiveperformance@5.1/manual/user-guide.html), [simulátor](https://docs.unity3d.com/Packages/com.unity.adaptiveperformance@5.0/manual/simulator.html)) | Indexer + „scalery“ (rozlišení 0,5–1 v 9 krocích, LOD, stíny, FPS…), každý má *visual impact* a *target* (CPU / GPU / fillrate) | snižuje nejdřív scalery s **nízkým vizuálním dopadem** a s cílem = **aktuální úzké hrdlo** (CPU/GPU podle FrameTiming proti cílovému FPS); akce Decrease / Fast Decrease / Stale / Increase; **zvýšení se ignoruje, dokud druhá složka (teplo nebo výkon) snižuje**; zvlášť nastavitelné zpoždění po akci kvůli teplu a kvůli výkonu (*Thermal/Performance Action Delay*) | ano – *temperature trend* (roste/klesá) a *temperature level*, varování ThrottlingImminent |
| **Android Thermal API** ([dok.](https://developer.android.com/games/optimize/adpf/thermal)) | `PowerManager.getThermalHeadroom(prognóza s)` 0 = bez škrcení, 1,0 = začátek škrcení (SEVERE) | Google heuristika: **> 0,85** možná LIGHT „snížit, je-li to možné“, **> 0,95** možná MODERATE „snížit hned“, **> 1,0** SEVERE „snížit hned a držet“; **dotaz nejvýš 1× za 10 s** (jinak NaN); první hodnota NaN nebo 0 = API na zařízení není | ano – prognóza „za x s“ |
| **ADPF best practices** ([dok.](https://developer.android.com/games/optimize/adpf/best-practices-adpf)) | – | **jemné nezávislé kroky postupně**, ne skok mezi presety; přechody plynule, kde to jde; **volba pro hráče, výchozí zapnuto**; testovat 15+ min. Varování: Unity MegaCity – plošné zkrácení dohledu → budovy zmizely (proto u nás dohled jen nouzově a v mezích) | – |
| **Android Performance Hint** ([dok.](https://source.android.com/docs/core/perf/performance-hint-api)) | hra hlásí cílovou a skutečnou délku práce za snímek, systém podle toho nastaví frekvence CPU | – (nemění kvalitu, jen CPU frekvence) | – |
| **Godot 4.4** | `Viewport.scaling_3d_scale`, v Compatibility **jen Bilinear** (FSR 1/2 jen Forward+, [dok.](https://docs.godotengine.org/en/4.4/tutorials/3d/resolution_scaling.html)); vestavěné dynamické rozlišení **není** – návrh [godot-proposals #917](https://github.com/godotengine/godot-proposals/issues/917) otevřený od 2020: změna rozlišení zakládá nové render targety (pomalé, clayjohn: bylo by třeba měnit jen glViewport) → doplněk se dle autora „nevyplatí“; placený doplněk Tai Performance Kit (Godot 4.7, okna p95/p99, hystereze, cooldown) a Resolution Scaler v Asset Library | – | **ADPF v Godotu není** (žádný návrh ani PR nenalezen, hledáno godot-proposals „thermal“, „ADPF“, „adaptive performance“); **jde ale bez pluginu**: Godot 4.4 přidal vestavěný `AndroidRuntime` + `JavaClassWrapper` ([dok.](https://docs.godotengine.org/en/stable/tutorials/platform/android/javaclasswrapper_and_androidruntimeplugin.html)); ověřeno v naší šabloně 4.4.1 (`classes.dex` obsahuje `AndroidRuntimePlugin`) |

### Hry
| hra | co je známo | zdroj |
|---|---|---|
| **Call of Duty Mobile** (Unity, Samsung GameSDK) | stupně podle teploty Normal / NearThrottling / CloseThrottling; při rychlém růstu teploty **nejdřív cílové FPS** (60 → 57), dál dosah stínů 80 → 50, LOD vegetace 1,0 → 0,8, LOD animací 0 → 2; rozhoduje **zda teplota ještě roste** (trend); v Normal sníží úroveň CPU/GPU, až když FPS drží „chvíli“; výsledek FPS stabilnější, průměr +7 %, teplota −2 °C | [Samsung Developers](https://developer.samsung.com/galaxy-gamedev/gamedev-blog/cod.html) |
| **Game of Thrones: Kingsroad** (Netmarble) | měření: **rozlišení** má největší vliv na GPU a teplo, stíny a textury malý; dynamické rozlišení podle Thermal API + cílové FPS **postupně 60 → min. 30** a postupně zpět; headroom průměr 1,04 → 0,92, nikdy nad 1,0; FPS místo 40–56 drží 50–60 | [Android Developers](https://developer.android.com/stories/games/netmarble-got-adpf) |
| **Lineage W** (NCSoft) | bez ADPF Pixel 6 za 30 min 60 → 32 FPS, headroom 1,0 po 4 min; s ADPF drží 60 FPS pod 1,0 | [Android Developers](https://developer.android.com/stories/games/lineagew-adpf) |
| **Fortnite (mobil)** | volba „3D rozlišení: Auto“ (dynamické podle výkonu); hráči hlásí, že Auto často drží 100 % a cílí ~50 FPS – oficiální popis nenalezen | [videogamer](https://www.videogamer.com/guides/fortnite-best-mobile-settings-ios-android), [GameBench](https://blog.gamebench.net/fortnite-hits-60fps-on-android-but-comes-at-a-cost) |
| **Doom Eternal** | dynamické rozlišení s cílem FPS zvoleným hráčem; snižuje rozlišení, když „čeká pokles“; na PC p95 při cíli 60 skoro beze změny, při cíli 70 výrazně lepší (= cíl s rezervou) | [OC3D](https://overclock3d.net/reviews/software/doom-eternal-pc-performance-analysis-and-optimisation-guide/6/) |
| **Genshin Impact, Diablo Immortal** | oficiální automatika podle tepla **nenalezena**; jen ruční volby (render resolution, 30 FPS) a stížnosti na ohřev | [Blizzard fórum](https://us.forums.blizzard.com/en/diablo-immortal/t/overheating-device/12107) |

### Co z toho plyne pro nás
1. **Pořadí:** nejdřív to, co je nejméně vidět a nejvíc šetří *podle vlastního měření* (Netmarble i ADPF: profilovat
   vlastní hru, ne převzít preset). Cílové FPS je u CODM i Netmarble první páka proti teplu.
2. **Prahy s rezervou:** Unreal cílí 90 % rozpočtu, Míša 80–85 % → p95 > 0,85 × 33,3 ms nebo průměr > 0,8 × 33,3.
3. **Proti oscilaci:** okno (ne jeden snímek), N oken po sobě dolů, delší klid nahoru, prodleva po každé změně,
   zvýšení blokované, dokud teplo roste nebo je vysoko (Unity), a dvojnásobné čekání po neúspěšném zvýšení.
4. **Teplo předem:** headroom s prognózou (≥ 10 s mezi dotazy), prahy 0,75 / 0,85 / 0,95 (Unreal ADPF, Google), trend
   růstu (CODM).
5. **GPU × CPU:** Unreal i Unity berou jiný krok, když stojí na CPU (rozlišení tam nepomůže).
6. **Změna rozlišení skokem a zřídka** (Godot #917: nové render targety), jen když se kamera neotáčí.

## 2. Návrh – kroky (pravidla/svet/kvalita.json `kroky`)
Jemná úroveň má přednost (geometrie světa stejná); nouzová až po vyčerpání jemné a `nouzova_s` trvalého nedostatku.

| # | krok | úroveň | šetří | vidět | úspora |
|---|---|---|---|---|---|
| 1 | `fps_30` omezení na 30 FPS | jemná | gpu, cpu | plynulost pohybu, detail stejný | **NEOVĚŘENO** – méně práce za minutu = méně tepla (závěr 0.99991: sekání = škrcení teplem); čas snímku neubírá |
| 2 | `trava_bez_stinu` (louka.nastav_unshaded) | jemná | gpu | tráva bez stínů stromů, les zatím bělavý | **NAMĚŘENO 0.99992** p50 louka 27 → 17, les 34 → 18, tvrz-cesta 25 → 18 ms – největší. **Vypnuto v datech (`povoleno: false`)**, zapnout až po opravě barvy v lese (jiný pomocník) |
| 3 | `stiny_kratsi` stíny slunce 40 → 25 m | jemná | gpu | stín dál než 25 m zmizí | **NEOVĚŘENO**; nejbližší: 0.9996 bez stínů úplně p50 18–23 × vše 18–27 (už ohřáté) |
| 4 | `stiny_predmetu` předměty, postavy, zvířata bez vrženého stínu | jemná | gpu | malé stíny chybí | **NEOVĚŘENO** |
| 5 | `efekty` bez záře (glow) | jemná | gpu | slabší zář ohně a oblohy | **NEOVĚŘENO** |
| 6 | `3d_86` 3D × 0,86 (tablet 70 → 60 %) | jemná | gpu | mírně měkčí | **NEOVĚŘENO, spíš malá**: 0.9991 55 → 70 % FPS beze změny |
| 7 | `3d_72` 3D × 0,72 (70 → 50 %) | jemná | gpu | měkčí | **NEOVĚŘENO** |
| 8 | `trava_dosah` trsy 80 → 50 m | nouzová | gpu, cpu | dohled drobné vegetace | **NAMĚŘENO 0.9995: čas snímku beze změny** – smysl jen v nouzi a při tísni paměti (méně buněk louky) |

Pozn.: Netmarble naměřil, že rozlišení je největší páka; u nás (0.9991) to neplatí – tráva se stínovým průchodem je
brzda kreslením, ne pixely. Proto rozlišení až za stíny. Až se změří `3d_50` na tabletu, pořadí upravit v datech.

**Paměť** (`pamet`): volná RAM < 350 MB nebo VRAM > 1000 MB → navíc `trava_dosah` + `3d_72`; zpět nad 600 MB / pod
900 MB. NEOVĚŘENO (tablet 0.99992 VRAM 849 MB; v tísni zatím nezměřeno).

## 3. Řídicí smyčka (scripts/kvalita.gd)
- Okno 2,5 s skutečných délek snímků (razítka; snímky nad 1 s = načítání/pauza se nepočítají) → p95, průměr, podíl
  skriptů + fyziky (diag._skripty_us + Performance fyzika) na délce snímku: nad 0,5 = stojí na CPU.
- **Dolů:** p95 > 28,3 ms nebo průměr > 26,6 ms ve **3 oknech po sobě** (7,5 s trend) → zapne se další jemný krok,
  který šetří to, na čem hra stojí (jinak první volný jemný). Při omezení 30 FPS se rezerva změřit nedá
  (snímek ≥ 33,3 ms): dolů až p95 > 38 ms, klid = p95 ≤ 35,7 ms.
- **Nouzová:** všechny jemné zapnuté a pořád nad prahem 60 s.
- **Nahoru:** p95 < 21,6 ms (nebo drží 30 FPS) souvisle 30 s → vypne se naposledy zapnutý krok. Spadne-li do 60 s
  zpět, čekání se zdvojnásobí (až 240 s); vydrží-li, čekání se půlí. Po každé změně 4 s bez hodnocení.
- **Teplo** (Android 11+): headroom (prognóza 10 s) každých 10 s; > 0,85 snížit (1× za 30 s), > 0,95 snížit hned
  (1× za 10 s), růst > 0,15/min nad 0,65 snížit předem; > 0,75 nebo rostoucí = nezvyšovat.
- **Kamera:** změna až při otáčení < 25 °/s; snížení nejpozději po 3 s, zvýšení se při pohybu odloží.
- Změny do `diag.log` (`FAZE KVALITA + fps_30 (p95 31 / prumer 27 ms, gpu); zapnuto 1/7 …`) a na řádek FPS panelu
  (` · kvalita -1 gpu teplo 0.62`).
- **Měřicí trasa:** automatika vypnutá (pevné varianty), poslední varianta `auto` ji zapne; ve sloupci varianta
  „auto -N“ = počet kroků na konci úseku, pod tabulkou seznam změn.

## 4. Ověření
- Headless test `tools/test_kvalita.gd` (simulované časy snímků): klid nemění, jedno škubnutí nesníží, trend nad
  rezervou sníží, odklad při otáčení, CPU vybere cpu krok, nouzová až po jemných, klid zvýší, hystereze, teplo předem,
  blok zvýšení, tíseň paměti, vypnutí, volba v Nastavení.
- **NEOVĚŘENO NA TABLETU:** celé chování na zařízení, volání `getThermalHeadroom` přes AndroidRuntime (jestli
  JavaObject vrátí číslo), všechny úspory kroků 1, 3–7, prahy paměti a tepla. Ověří trasa (varianta `auto`) a 20 min hry
  s `diag.log`.
- Nezavedeno: Performance Hint API (hlášení délky práce za snímek kvůli frekvencím CPU) – přes JavaClassWrapper by
  vyžadovalo volání Javy každý snímek a id vlákna; tablet stojí na GPU, přínos malý. Případně později.
