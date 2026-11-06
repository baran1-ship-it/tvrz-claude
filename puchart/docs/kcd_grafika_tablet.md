# KCD grafika udržitelná na tabletu – rešerše 6. 11. 2026

## Jak dělá KCD svůj vzhled (co přenést, co ne)
- KCD2: silně upravený CryEngine 5, **SVOGI** (voxelové nepřímé světlo za běhu), simulovaná vegetace; u vesnic kvalita podle
  recenzí klesá. Zdroje: mein-mmo.de/en/a-current-hit-on-steam-proves-...-frankfurt,1239039 ; tweaktown.com/news/49267 .
- **Na tablet nepřenosné:** SVOGI/Lumen za běhu (UE5 Lumen umí jen Snapdragon 8 Gen 3+ a Arm demo „Mori“ – Adreno ve Xiaomi
  Pad 8 to v Godot Compatibility nedá).
- **Přenosné:** výsledek SVOGI = měkké nepřímé světlo a stíny v koutech → **zapéct** v Blenderu (Cycles), za běhu jen textura.

## Klíčové zjištění pro Godot 4.7 Compatibility
- Godot 4.4 docs: Compatibility **lightmapy umí zobrazit**, ale **nepéct** (péct jen Forward+/Mobile s RenderingDevice).
  → Dvě cesty: (a) péct v Godotu pod Forward+ na PC a výsledek použít v Compatibility; (b) péct v Blenderu Cycles do 2. UV
  a nasadit jako texturu (máme v rukou, nezávislé na verzi Godotu). Doporučení: **(b) Blender**, nejdřív jedna místnost.
  Zdroj: docs.godotengine.org/fr/4.4/tutorials/rendering/renderers.html , docs .../4.2/.../using_lightmap_gi.html (UV2 nutné).

## Recept „KCD vzhled na tabletu“ (seřazeno podle přínosu / ceny)
1. **Zapečené světlo** (lightmapa, 1 atlas na budovu, 512–1024 px): nepřímé světlo, AO, barevný odraz od hlíny. Největší
   rozdíl proti „hře z 90. let“ (Míša). Cena: paměť textur (~2–8 MB na hrad), za běhu nic.
2. **Méně materiálů = méně kreslení** (Unity mobile best practices, atlas pro / mobile ready): sloučit materiály staveb do
   atlasů; dnes 600–900 kreslení → cíl < 400.
3. **Bez průhlednosti a výřezů tam, kde to jde** (overdraw na mobilu nejdražší – Unity mobile guide): les a podrost jsou
   hlavní žrout (58–71 ms) → **impostory** (Godot doplněk Octahedral Impostor LOD: strom z dálky 2 trojúhelníky), méně
   překrývajících se listů nablízko.
4. **Mobilní rozpočet geometrie**: Genshin na mobilu ~0,5–0,85 M troj./snímek; my 1,4–2 M → LOD budov (už máme dálkovou
   verzi), kratší dohled detailů, zjednodušit skrytá patra.
5. **Detail v textuře, ne v geometrii** (art testy pro mobil: detail i světlo zapečené do jednoho atlasu): kameny zdí,
   spáry, šindel – výšková mapa + zapečené stínění; geometrické kameny jen nároží a ostění.
6. **Variace bez dalších vzorkovačů**: hex skládání (máme), barva kusu ve vrcholech (máme), velký šum ve světě (máme).
7. ~~Vulkan / Mobile renderer~~ – **ZAMÍTNUTO**: Míša 6. 11.: „Vulkan vždy spadl na startu“ (Havran i A/B test na Xiaomi Pad 8).
   Zůstáváme na Compatibility (OpenGL); světlo pečeme v Blenderu.

## Doporučený postup
1. Zapečené světlo: světnice paláce A + nádvoří A (Blender Cycles → UV2 → shader zdivo/textura násobí lightmapou). Snímek vs. KCD fotky.
2. Impostory lesa (úkol 11) – cíl les p95 < 40 ms.
3. Atlasy materiálů hradu – cíl < 400 kreslení.

## Zdroje
https://newsroom.arm.com/blog/key-takeaways-from-gdc-2025-arm ; https://www.gdcvault.com/play/1020691/Bringing-Console-Quality-Lighting-to ;
https://gamesbeat.com/google-levels-up-android-graphics-with-vulkan-api-in-time-for-gdc-2025/ ;
https://www.neowin.net/news/qualcomms-new-snapdragon-8-gen-3-mobile-chip-promises-240-fps-console-defying-gaming/ ;
https://blog.unity.com/pt/technology/artists-best-practices-for-mobile-game-development ; https://benlucas.artstation.com/projects/EVE2ZN ;
https://synthorian.artstation.com/projects/39KmxA ; https://godotengine.org/asset-library/asset/edit/24616 ;
https://docswell.com/s/UnityJapan/KWRPQ5-210617-unity-dojo20211mihoyozhenzhongyi
