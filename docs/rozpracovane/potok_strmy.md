# Strmý potok (Bystřice, osa 63–75) – rozbor 14. 11. (řádek 158)

Míša: „peřina vody v trávě, z té výšky by to měl být skoro vodopád, minimálně peřeje a hodně kamenů ve vodě, zahloubit“.

## Naměřeno z dat (trava_kraj, voda.json potok.osa)
- terén osy z 1189→1122: 34,0 → 6,9 m = **sklon 0,39** (max 0,53 u bodu 65); hladina sklon 0,28–0,41
- hladina NAD původním terénem: bod 74 (285,1128) **+1,46 m**, body 66–68 +0,5…+1,0 m → voda na náspu = „peřina“
- dno 0,6 m (±33 %) pod hladinou, břeh v pásmu 0,6 m jen +0,05 m nad hladinou

## Příčina (potvrzená z kódu)
- `scripts/koryto.gd priprav` (59–107): hladina = min. terénu ±3 m, klouzavý průměr 9 bodů (~45 m) + 0,35 m – průměr
  na strmém úseku zvedá hladinu nad terén; `podlaha` (186–197) pak dosype břeh pod vodu (násep).
- `koryto.gd strop` (151–179): profil nezávislý na sklonu.
- Blender `kraj.py _river_bed` 500–518, `perej()` 524 = Perlinův šum, ne sklon; kameny `_reka_kameny` 2075–2136 taky šum;
  `svet.gd` 12614–12641 kameny s čísly natvrdo (0,13/m, bez sklonu).
- shader `reka.gdshader` 186–190 steepness podle kamery, ne světové normály.

## Návrh (rešerše: Montgomery & Buffington 1997 – step-pool nad 3–4 %, kaskáda nad 8–10 %, schody po 1–4 šířkách)
1. `voda.json potok.raz_toku` podle sklonu osy (průměr 15 m): klidny < 0,03; pereje 0,03–0,12 (dno 0,9, břeh ≥ 0,5,
   schody á 2,5 šířky, výška ≤ 0,6, 0,6 balvanu/m, pěna 0,4); kaskada > 0,12 (zářez V 1,2–2,5 m, schody á 1,5 šířky ≤ 1,2 m,
   1,2 balvanu/m, kus vodopádu u schodu > 0,5 m, pěna 0,8). Hodnoty = odhad k ověření snímkem.
2. Hladina jako stupňovitý záznam (tůně + svislé schody), na strmých úsecích bez +0,35 a průměru; pravidlo „hladina nikdy
   nad původním terénem“ – terén se zařízne, `podlaha` na strmých úsecích nesype. Blender i koryto.gd čtou týž seznam schodů.
3. Kameny: práh z balvanů přes šířku na každém schodu + hustota z pravidla (Blender i svet.gd), pryč šum a čísla v kódu.
4. Waterways: stupňovitá křivka, u schodu kus vodopádu (pás 2×4) se stejným shaderem; pěna ze sklonu ve vertex color,
   steepness ze světové normály. Mobil: bez screen texture, bez částic; ~40 balvanů a 10 vodopádů na 100 m (MultiMesh).
5. Testy: (a) hladina − dno ≥ 0,3 a ≤ pravidlo + 0,2; (b) břeh 1 m za hladinou ≥ minimum pravidla; (c) hladina nikdy nad
   původním terénem; (d) kameny/m ≥ 80 % pravidla na peřejích/kaskádě; (e) každý schod > 0,5 m má vodopád.
