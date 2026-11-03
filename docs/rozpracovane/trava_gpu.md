# Tráva na GPU (Míša 3. 11.: „makej, ať to stojí za to, ale bacha na výkon“)

## Proč (změřeno, ne odhad)
- Dnes `louka.gd` rozsévá buňku 32 m za běhu v GDScriptu: 1,2–2,2 s/buňka na PC (99 % `_rozsej`,
  `_vzorek` ~65 µs × 16 000). Test `trava_dorust`: krok 1800/1800, cval 1190/1800, trysk 1185/1800 snímků pozdě.
- Předpečení trsů: 1885 buněk × 230 kB = 430 MB – ne.

## Návrh
1. **Pečení hustoty (jednou po exportu, Godot headless, test `louka_pec`)**: mřížka 0,5 m přes plochu masek trávy,
   v každém bodě přesně dnešní pravidla (`louka._vzorek` + práh, krytí shora, nádvoří, pás cest, divokost) →
   `modely/louka/hustota.bin`: hlavička (x0, z0, krok, nx, nz) + R8 hustota (0 = nic), R8 divokost/nízká, R16 výška (cm).
   Pravidla zůstávají na jednom místě (GDScript), shader je jen čte → žádný druhý zdroj pravdy.
2. **Kreslení**: pevné MultiMeshe kolem kamery (prstence: 0–20 m krok 0,36 m, 20–60 m řidší, 60–110 m kupy),
   jednotková transformace, poloha trsu = přichycená mřížka kolem kamery + `INSTANCE_ID` → světová buňka → hash
   (jitter, druh, výška). Výška a hustota z textur (vertex shader). Hustota < hash → trs nulové velikosti (bez fragmentů).
   Žádná práce CPU na trs, žádné čekání na vlákna → tráva je všude hned (krok i trysk).
3. **Bez druhého systému**: stávající `louka.gd` zůstane přepínatelná (Nastavení / `pravidla`) do ověření A/B na
   tabletu; po schválení se rozsev za běhu smaže.

## Výkon (rozpočet, měří se na stejné trase)
- Vertex: N instancí × vrcholy trsu; dnes kreslíme podobný počet (hash ořez). Cíl: louka ≤ dnešní (3–6 ms/snímek
  na tabletu, 0.9995), p95 trasy ne horší než 0.9995 „vše“. VRAM textur ≤ 40 MB.
- Mobilní GPU: čtení textur ve vertex shaderu je v GLES3 v pořádku; žádný screen texture, žádné MSAA.

## Přijetí
- `trava_dorust` projde (krok, cval, trysk: 0 snímků pozdě do 20 m).
- `bylina_velikost`, `nizka_trava`, `louka_bod`, `ves_maska` projdou.
- Snímky na 6 místech (louka u tvrze, cesta, ves, mlýn, les, rybník) proti 0.9996 – posoudím sám, pak nezávislý kontrolor.
- Měřicí trasa na tabletu (Míša) – zápis do `docs/mereni_verze.md`.
