# Jak se staví hry na tablet – hloubková rešerše 6. 11. 2026 (10 hledání) a co z toho plyne pro Puchart

## 1. Jak funguje grafika tabletu (Adreno = dlaždicové GPU)
- Obraz se kreslí po malých dlaždicích v rychlé paměti čipu; drahé je **přenášet data do RAM** (šířka pásma), ne počítat.
  (Arm blog „how low can you go…“; Qualcomm Game Developer Guide – kapitoly early-Z, tile-based rendering, bandwidth.)
- **Textury žerou pásmo**: Android doporučuje průměr čtení textur ~1 GB/s, špičku 3 GB/s, výpadky L1 cache < 10 %
  (developer.android.com/agi/sys-trace/texture-memory-bw). → komprese (ETC2/ASTC), mipmapy, menší rozlišení na dálku.
- Qualcomm: ETC2 pro textury bez průhlednosti, sRGB ASTC je na Adreno efektivnější než RGBA (best_practices_texture).
- **Pořadí kreslení**: neprůhledné zepředu dozadu, pak obloha, pak průhledné zezadu dopředu, UI nakonec → early-Z zahodí
  skryté pixely; studie na Adreno: −7 ms (slajdy „Jake & Tess“, Qualcomm slajdy o řazení).

## 2. Les a průhlednost – náš největší problém (les 58–71 ms)
- **Alpha test / discard (listí s výřezem) je na dlaždicových GPU nejdražší**: shader běží i pro vyříznuté pixely a může
  vypnout hierarchický Z pro celý snímek; les s discard ~2× pomalejší (Khronos fórum, cinevva „How modern engines beat
  foliage overdraw“, Unity fórum).
- Lék: (a) **těsná geometrie listů** (mesh obepíná listí, málo prázdného místa), (b) **impostory na dálku** (strom = 2
  trojúhelníky; Simplygon: vzdálené stromy jen jako impostory; Unity HLOD+impostory: 1024 impostorů ≈ 8 MB ASTC),
  (c) volitelně hloubkový předprůchod s minimálním shaderem (měřit – výsledky se liší podle GPU).

## 3. Velký svět na mobilu
- Celý svět najednou nejde → **mřížka streamovaných dílů** (80.lv rozhovor o 20 km² mobilním světě), HLOD z nejnižšího LOD
  (Epic Fortnite docs). Meta: otevřené světy cílit na ~50 % běžného počtu trojúhelníků.
- My: 2×2 km dlaždice terénu už máme; hrady mají dálkovou verzi; chybí impostory lesa a sloučené HLOD vesnice/skal.

## 4. Stabilita, teplo a plynulost
- Tablet se po 10–30 min zahřeje a sníží výkon: Lineage W na Pixelu 6 spadl z 60 na 32 FPS za 30 min; Netmarble 40↔56 FPS
  (developer.android.com stories ADPF).
- **ADPF (Thermal API)** – hra sleduje teplotní rezervu a **sama sníží kvalitu dřív**, než se čip přiškrtí; Ares 96 % stabilní FPS.
- **Swappy** (frame pacing, AGDK, OpenGL i Vulkan) – rovnoměrné snímky při pevných 30 FPS.
- Měřit **dlouhé sezení** (30 min), ne jen krátkou trasu; Google Play hlídá „slow sessions“.
- Godot: pro Android jen Compatibility nebo Mobile (Forward+ je desktopový); v Compatibility nejsou GPU částice (použít CPU);
  textury „VRAM Compressed“ (ETC2) (gtstu.com, slicker.me, bugnet – blogy). Měřit vždy na tabletu (editor 120 FPS ≠ telefon 25).

## 5. Umění pro mobil (jak to dělají jiní)
- Detail a světlo **zapečené do textury/atlasu**, málo materiálů = málo kreslení (Unity mobile best practices; art testy
  benlucas, synthorian – diffuse + jedna lightmapa 1024²).
- Alba (ustwo, Apple Arcade, otevřený svět na mobilu): jednoduché tvary + barevné přechody + dekály, od začátku hlídaný
  rozpočet textur (ustwogames.co.uk/news/the-environment-art-of-alba…).
- Genshin: zvlášť mobilní vykreslovací cesta, ~0,5–0,85 M troj./snímek.

## 6. Co z toho plyne pro Puchart (akční seznam podle dopadu)
| # | Úkol | Proč | Odhad přínosu |
|---|---|---|---|
| 1 | **Impostory lesa** + těsné listy, méně vrstev podrostu | alpha test = hlavní žrout | les 60–70 → < 40 ms |
| 2 | **Řazení kreslení** a obloha až po neprůhledných (ověřit, co dělá Godot Compatibility) | early-Z | jednotky ms |
| 3 | **Komprese textur ETC2/ASTC**, kontrola mipmap a velikostí (zdivo 1k, ne 2k) | šířka pásma | ms + paměť |
| 4 | **Zapečené světlo** (Blender) místo více světel | vzhled KCD bez ceny za běhu | vzhled |
| 5 | **Atlasy materiálů** staveb, cíl < 400 kreslení | CPU/ovladač | ms |
| 6 | **Rozpočet trojúhelníků** ~1 M/snímek (dnes 1,4–2 M) – LOD budov, skrytá patra | geometrie | ms |
| 7 | **Teplo**: měření 30 min v APK + automatické snížení kvality podle teplotní rezervy (ADPF přes Android plugin, nebo
  jednoduše podle trendu p95) | stabilita po zahřátí | plynulost |
| 8 | **Záznam pádu v aplikaci** (pro Vulkan i obecně) | diagnóza bez PC | jistota |

## Zdroje
https://developer.qualcomm.com/sites/default/files/docs/adreno-gpu/snapdragon-game-toolkit/gdg/search.html ;
https://developer.qualcomm.com/sites/default/files/docs/adreno-gpu/snapdragon-game-toolkit/gdg/gpu/best_practices_texture.html ;
https://developer.android.com/agi/sys-trace/texture-memory-bw ;
https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/how-low-can-you-go-building-low-power-low-bandwidth-arm-mali-gpus ;
https://de.slideshare.net/PhilLira1/how-we-optimized-our-game-jake-tess-finding-monsters-adventure ;
https://www.slideshare.net/QualcommDeveloperNetwork/71-snapdragongamingplatformsirdeshmukhlemoine918gg23-39583049 ;
https://app.cinevva.com/blog/2026-05-11-foliage-overdraw ; https://community.khronos.org/t/alpha-discard-is-very-slow/111004 ;
https://discussions.unity.com/t/hlod-streaming-octahedral-impostors-using-megacity-subscenes/742223 ; https://simplygon.com/blog/f2a10dde-4ca7-44e1-9ee3-eaa8286f4d4e ;
https://80.lv/articles/designing-large-scale-mobile-game-cities-production-optimization-worldbuilding-expertise ;
https://developers.meta.com/horizon/documentation/unity/po-assetstreaming/ ;
https://developer.android.com/games/optimize/adpf/best-practices-adpf ; https://developer.android.com/stories/games/netmarble-got-adpf ;
https://developer.android.com/games/optimize/power?hl=en ; https://developer.android.com/topic/performance/vitals/slow-session ;
https://gtstu.com/godot-4-optimize-android-ios/ ; https://slicker.me/godot/mobile-optimization.html ;
https://bugnet.io/blog/how-to-test-your-godot-game-on-low-end-android-phones ;
https://blog.unity.com/pt/technology/artists-best-practices-for-mobile-game-development ;
https://ustwogames.co.uk/news/the-environment-art-of-alba-a-wildlife-adventure/
