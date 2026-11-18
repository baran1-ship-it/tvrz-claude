# Voda a přízemní mlha podle Míšina lesa „Hvozd“ – návod (Puchart i Havran)

Míša 18. 11.: les 100×100 m v prohlížeči (three.js r128, artefakt „Hvozd“) má hezčí vodu než naše hry.
Rozbor kódu: **žádný skutečný odraz scény, žádná kopie obrazovky** – jde to i v Godotu Compatibility na tabletu.

## Jak to dělá Hvozd
1. **Odraz = panoramatická fotka lesa.** Obloha je equirect fotka mlhavého lesa (`sky.jpg`, Poly Haven CC0).
   Voda z ní čte barvu podle odraženého vektoru pohledu (`reflect(-V, n)`, `y = abs(y)`, převod na UV
   `u = atan(z, x)/2π + 0.5`, `v = asin(y)/π + 0.5`). Kmeny a světlá obloha ve vodě jsou tedy z fotky.
2. **Fresnel** `0.03 + 0.97·(1 − max(dot(V, n), 0))^5` – zpříma vidět tělo vody, šikmo odraz (`refl·0.8`).
3. **Tmavé tělo:** u kraje hnědé `(0.08, 0.065, 0.04)`, ke středu černozelené `(0.015, 0.024, 0.019)` (lineárně).
4. **Vlnky:** jedna normálová mapa 256² (generovaná šumem, protažená po proudu ×2,5), čtená **dvakrát** s různým
   měřítkem a rychlostí (`uv.x·0.8 − t·0.45` a `uv.x·1.9 − t·0.8`), sečtené 0,55/0,45, sklon normály ×0,6.
5. **Pěna** ze šumu (fbm, 4 oktávy) po proudu, silnější u kraje. **Průhlednost** u kraje 0,2 → uprostřed 0,92.
6. **Přízemní mlha:** ~40 průsvitných obláčků (sprite 7–13 × 2–3,4 m, neprůhlednost 0,25–0,5, bez zápisu hloubky),
   24 z nich podél potoka 0,5–1,3 m nad terénem, pomalu se posouvají.

## Převod do Godotu (Compatibility, tablet)
- `voda.gdshader`: přidat `uniform sampler2D panorama : source_color, filter_linear, repeat_enable;` (equirect fotka
  lesa, 2048×1024, ETC2), v `fragment()` spočítat `vec3 R = reflect(-VIEW_world, N_world); R.y = abs(R.y);`
  → UV podle vzorce výše → `refl = texture(panorama, uv).rgb`. ALBEDO/EMISSION: `mix(telo, refl*0.8, fresnel)`.
  Pozor: Compatibility nemá SSR – odraz dávat do EMISSION (nebo ALBEDO s nízkou drsností), ne spoléhat na SPECULAR.
- Vzorkovače: panorama + normálová (2× čtená) = +1 až +2 proti dnešku, pod limitem 13 (Adreno).
- Panoramu vybrat podle lesa hry (listnatý/smíšený, mlhavý; Poly Haven CC0, zapsat do CREDITS), ne obecnou oblohu.
- Barvy těla a meze do dat (`voda_hra.json`), se `zdroj: Hvozd 18. 11.`; denní doba: panoramu násobit barvou okolí
  (jinak bude v noci voda svítit).
- Mlha: MultiMesh billboardů (jeden materiál, `depth_draw_never`, `unshaded`, alfa), rozmístění podél os potoků
  z dat, dosah ~60 m; opatrně s překryvem (overdraw) – měřit na tabletu.

## Kontrola
Snímek vody ze stejných míst před/po (mlýn, Velička, lávka) + měření trasy „voda“ na tabletu.
