# Měření verzí na tabletu (Xiaomi Pad 8)

Každé vydání: Nastavení → Měřicí trasa (7 míst × 8 variant, `pravidla/svet/mereni_trasa.json`). Míša pošle fotku
tabulky, stavitel ji sem přepíše. Hodnoty jsou ms na snímek (p50 / p95 / max), záseky = snímky nad 40 ms.
Varianty: vše (1. průchod), 2. průchod, 3D 70 %, bez stínů / trávy / stromů / staveb / předmětů.

## Historie před měřicí trasou (z `docs/radce.md`, panel na tabletu)
| verze | datum | stav |
|---|---|---|
| 0.57–0.63 | 21.–23. 10. | mikrosekání, louka 15–18 FPS (výplň trávy) |
| 0.67–0.74 | 23.–24. 10. | sekání žádné, špiček 0/30, nejdelší 22–44 ms – **poslední dobrá** |
| 0.75–0.88 | 24.–26. 10. | velké záseky: trimesh kolize dílů, ves a hostinec bez LOD, cesty jako síť (rádce 2. 11. 19:50) |
| 0.997–0.999 | 2. 11. | 17–32 FPS, kreslení+čekání 45–110 ms souvisle, zásek 3,3 s u (13, 42) |

## Záznamy měřicí trasy
| verze | commit | datum | místo | varianta | p50 | p95 | max | záseky | kreslení | troj M | poznámka |
|---|---|---|---|---|---|---|---|---|---|---|---|
