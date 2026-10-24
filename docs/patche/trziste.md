# Tržiště před Lhotou – odloženo (Míša 0.75: „smaž a někam si ho ulož, budeme na něm dělat do budoucna“)

Stav 0.75 (vypnuto přepínačem `TRZISTE := false` v `scripts/svet.gd`; `true` ho vrátí celé):
- **Plán:** `docs/screens/trziste_plan.png` – obdélník v místním rámu u cesty od mostu: `TRZ_O` (381,7; 750,9), osa `TRZ_U`/`TRZ_V`,
  `TRZ_R` = Rect2(−2; 6,5; 24; 12). Ulička 3 m podél cesty, dvě řady po 4 stáncích (u 2/6/10/14, v 9/16).
- **Kód:** `_trziste(vb, rng)` (stánky `pristresek_maly`, zboží na pultech, zásoby za stánky, `stan_jehlan`, `kul_cedule`,
  `koryto_kone`), `_trziste_cisti` (rostliny pryč), `v_trzisti` (vzdálenost od okraje), rovina terénu `_trz_y` v `uprava_y`,
  maska hlíny v `zem.gdshader` (uniformy `trziste`, `trziste_r`), louka bez trávy (`louka.gd`).
- **Modely v katalogu stavitele** zůstávají: pristresek_maly/plachta, stan_jehlan/velky/trzni, stanek_trzni, kul_cedule,
  koryto_kone, zboží z Disku (bedny, necky, hrnce, chléb, zelenina, koberec, stůl, věšák s kůžemi…).
- **Připomínky Míši k 0.75:** stánky z dálky OK, ale celé to působí jako balík; až se vrátíme – nejdřív rozvrh (kdo prodává co,
  kde stojí vozy kupců, napajedlo), pak stavba.
