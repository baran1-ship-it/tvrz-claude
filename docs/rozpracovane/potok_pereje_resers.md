# Potok na svahu: peřeje a vodopády – rešerše (14. 11. 2026 21:26)

Úloha: řeka 10 m široká, 70 m dlouhá, spád 27 m (sklon 39 %), dnes jeden „peřinový“ pás Waterways.
Cíl: peřeje až vodopády, hodně kamenů, bez záseků (GL Compatibility, bez MSAA, bez SCREEN/DEPTH_TEXTURE, GPU je úzké hrdlo).
Čísla nákladů níže jsou ODHAD z rešerše, NEOVĚŘENO NA ZAŘÍZENÍ (ověřit Měřicí trasou).

## 1. Jak to vypadá ve skutečnosti (pravidla dat)
- Při sklonu nad ~2–3 % vzniká stupeň–tůň (step-pool); průměrné sklony jednotek: peřej 2,9 %, kaskáda 5,5 %, stupeň 17,3 %. Náš 39 % je nad tím → **kaskáda/stupně s malými vodopády**, ne souvislý proud. [3]
- Rozestup tůní průměrně **2–4 šířky koryta**, s velkým rozptylem; rozestup klesá se sklonem. [3][4]
- Abrahams 1995: stupně se ustálí na **(H/L)/S = 1–2** (H výška stupně, L rozestup). [5] Pro S = 0,39 a L = 10–15 m → H ≈ 4–6 m na stupeň, 27 m spádu ≈ **5–6 stupňů** (každý pár metrů stupeň + plochá tůň). Strmé úseky → L blíž 1 šířce.
- Výška stupně ≈ velikost největších balvanů (H ≈ D100) [4] → **balvany leží na hraně stupně (koruně)** jako příčný řádek, menší kameny v tůni a po stranách; tůň pod stupněm je vymletá (hlubší, tmavší).
- Bílá voda: na hraně a pod pádem (provzdušnění), v tůni se rozpadá po proudu; v klidné části tůně skoro žádná.

## 2. Techniky – seřazeno podle vhodnosti pro nás
1. **Rozložit pás na stupně: tůně (vodorovné plochy) + krátké pády (svislé pásy)** – jako Naughty Dog (spline nástroj, flow + pěna z prahování) a RiME/Season (více jednoduchých sítí místo jedné). [6][7][8] Tůně jako jedna sloučená síť, pády druhá. **+1 draw call**, žádná nová průhledná vrstva.
2. **Pád = posuvné UV (scrolling) po pásu, natažené UV pro zrychlení**, maska pěny z šedé textury s tvrdým prahem. [9][10] 1–2 vzorky textury, levný shader.
3. **Pěna z vertex color** (zapéct v Blenderu: hrana stupně, okolí kamenů, pata pádu) místo počítání ve shaderu; případně pěna podle sklonu normály (Waterways to umí – „foam on steep angles“). [11][12] 0 draw callů navíc.
4. **Tůně neprůhledné** (tmavá voda, barva hloubky z vertex color) – bez DEPTH_TEXTURE stejně nejde měkký okraj; ušetří blending celé plochy. Průhledný jen pád a pěnový lem.
5. **Mlha/sprška = 2–4 kartičky (billboard/MultiMesh) u paty každého pádu**, ne částice. Polycount: přechod na panner sítě snížil částice z ~1000 na ~100. [13] GPUParticles v Compatibility jsou nespolehlivé (zdroje se rozcházejí: zmizí × spadnou na CPU) → nanejvýš CPUParticles3D, desítky kusů. [14][15] **1 draw call** (MultiMesh).
6. **Kameny přes MultiMesh** z modelů (Poly Haven/Quaternius), řádky na korunách stupňů z dat – **1–3 draw cally**.
7. **Visibility range**: pády, pěna a mlha zhasnout od ~40–60 m, fade mode **Disabled** (alfa fade vynutí průhledné vykreslení; dither je levnější než blending). [16]

Odhad celkem: ~5–7 draw callů (tůně, pády, pěna, mlha, kameny) místo 1; **na pixel max. 2 průhledné vrstvy** (pád + mlha).

## 3. Pasti na mobilu
- Průhledné nemají early-Z → největší zdroj překreslení; kreslit odzadu dopředu, depth test zap., depth write vyp. [1][2]
- Blending, discard (alpha test) i „může být průhledné“ vypínají skrývání neviditelných ploch (HSR) na tile GPU. [1][17] Arm 2025: víc alpha-testu = méně zakrývačů pro HSR Mali. [18] Starší rada PowerVR: alpha blend místo alpha test. → **Pády blend, ale úzké sítě těsně na tvar** (neprůhledné jádro + tenký průhledný okraj), velké plochy neprůhledné.
- Overdraw = průměrný počet kreseb pixelu; velké kartičky mlhy blízko kamery jsou nejdražší (zaberou celou obrazovku). [17]
- Řazení průhledných: překrývající se pády/mlha v jednom objektu se neřadí → držet vrstvy oddělené a malé.
- Nic s SCREEN_TEXTURE (lom), nic s DEPTH_TEXTURE (měkký okraj) – v souladu s pravidly tabletu.

## Zdroje
1. Vulkan Guide – TBR best practices: https://docs.vulkan.org/guide/latest/tile_based_rendering_best_practices.html
2. Arm – Console quality rendering on mobile: https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/console-quality-game-rendering-on-mobile
3. Kanály / jednotky toku (UCANR): https://ccfruitandnuts.ucanr.edu/sites/default/files/2013-04/164518.pdf
4. Step-pool geometrie (Andrews Forest, OSU): https://andrewsforest.oregonstate.edu/sites/default/files/lter/pubs/pdf/pub1449.pdf ; Molnar (IAHS): https://iahs.info/uploads/dms/14527.44-302-307-38-325-Molnar.pdf
5. Abrahams 1995 / Comiti 2007: https://www.umt.edu/wilcox/documents/publications/comiti-etal2007-jhydrol.pdf ; https://flore.unifi.it/bitstream/2158/256208/1/ESP1590.pdf
6. GDC 2012 Water Technology of Uncharted: https://gdcvault.com/play/1015517/Water-Technology-of ; https://www.slideshare.net/slideshow/water-technologyofunchartedgdc2012/12977478
7. RiME stylized VFX: https://realtimevfx.com/t/talk-video-stylized-vfx-in-rime/2503
8. Season waterfall: https://realtimevfx.com/t/how-we-made-waterfall-in-season-a-letter-to-the-future/23420
9. Stylized waterfall Unity 3/4: https://80.lv/articles/creating-a-stylized-waterfall-in-unity-part-3 ; https://80.lv/articles/creating-a-stylized-waterfall-in-unity-part-4
10. Filo sketch (vrstvy pádu): https://realtimevfx.com/t/filo-sketch-9-wip/3316/14
11. Unity nature shaders (vertex color masky): https://unity.com/blog/engine-platform/nature-shaders-with-shader-graph-in-2022-lts
12. Waterways README: https://raw.githubusercontent.com/Arnklit/Waterways/main/README.md
13. Polycount (částice 1000→100): https://polycount.com/discussion/comment/2688555
14. Godot docs částice: https://docs.godotengine.org/en/4.2/tutorials/3d/particles/index.html
15. GPU vs CPU částice low-end: https://godotforums.org/d/37279-gpuparticles-vs-cpuparticles-for-lower-end-devices
16. Godot 4.4 Visibility ranges: https://docs.godotengine.org/en/4.4/tutorials/3d/visibility_ranges.html
17. Mozilla Mobile GPUs: https://wiki.mozilla.org/Platform/GFX/MobileGPUs
18. Arm Vulkanised 2025: https://www.vulkan.org/user/pages/09.events/vulkanised-2025/T18-Pete-Harris-Arm-MobileBestPractices.pdf

Kde se hledalo a nic: GDC k BotW/Genshin/Sea of Thieves řekám – nic konkrétního; issue Waterways k vodopádům – žádné.
