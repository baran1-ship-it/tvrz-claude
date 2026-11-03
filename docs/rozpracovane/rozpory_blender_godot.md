# Rozpory Blender × Godot (soupis 2. 11. večer, Míša: „Blender píše starou vesnici a Godot novou… zkontrolovat, jestli tam a nejen tam nemáme rozpor“)

Soupis ze čtení kódu (svet.gd S, ves_oblouk.gd VO, louka.gd L; blender kraj.py, vesnice.py, export_game.py). Řádky
k 2. 11. Detail každého bodu: místo, co mění, z jakého záznamu, co dělá Blender, proč riziko.

## Hlavní příčina
Blender peče barvu terénu (G), masku trávy a výšky ve STARÉM rozložení vsi (`vesnice.layout`, `ves_paths`, `_pads`).
Godot pak každou z těchto věcí přenáší do nového rámce zvlášť a vlastním pravidlem (`_vo_data`, `_vo_teren`, `_vo_sit`,
`_vo_scena`). Jedna věc tak má dvě nebo tři pravidla.

## Riziko vysoké
1. **Stará náves.**
   - Godot ořízne jen osu cesty (`_vo_stara_naves` S:41, natvrdo obdélník kolem (470, 830)). Barvu G a masku staré návsi
     mimo půdorysy usedlostí nic nepřebarví → holé hnědé pásy bez trsů.
   - `lokace.ves.stred_stare_navsi` existuje, ale nečte se.
2. **Šířka ulice, tři pravidla:**
   - `vo.pulsirka`/`ulice_pas` (barva + maska);
   - `cesta_ok` se šumem ±0,5 m a rozšířením `_cesty_opotrebeni` (hlína v shaderu, trsy, rostliny, ploty, vybavení);
   - `ves_cesta` m<60 (rostliny).
3. **Toky a usedlosti.** Toky na starém místě usedlosti (teď tam tečou) a na novém (netečou): výšku opravuje
   `_breh_toku_y`, barvu ani masku nic.
4. **Krčma natvrdo ve starém rámci.** `CESTA_UDUSANO` (S:6914) je natvrdo (461, 779) = starý střed krčmy. Nová krčma
   (369, 760) udusaný plac nemá.
5. **Stará místa jako louka.** Maska 200 natvrdo, barva louky = průměr prvních 200 vrcholů s g>0,8 (skvrna).
6. **Okraj mřížky.** `trava_ves` končí na x≈350, nový půdorys k=0 sahá na 337 → v pásu nesedí barva a maska (NEOVĚŘENO).
7. **Terén pod domem.** Podstava staré chalupy (`pad_adjust`) + nový dům (`dum_teren`, `DUM_MER` natvrdo) → dvě rovinky
   vedle sebe.
8. **Okraj stavby.**
   - Blender: `_in_building` 1,6 / `okraj_stavby` 1,0–2,2 kolem starého obrysu chalupy.
   - Louka: `_v_budove` prah 0,4 kolem obrysu nového domu.
   - V samotném Blenderu: maska = okraj², barva okraj¹.

## Riziko střední
9. Půdorys usedlosti: okraje v VO:21 opsané natvrdo z `_homestead_green`.
10. `_vo_sit`/`_vo_scena`: díl na hranici půdorysu jede celý, nebo zůstane.
11. `_ves_site_vyrez`: ploty podle `cesta_ok`, ne podle pulsirky.
12. Výška ulice: `uprav_y` (příčně) + `_cesty_profil` (podélně, ±0,25 natvrdo) dvěma pravidly.
13. Terén pod cestou: Blender `flatten`/`road_y` (přechod 6 m) + Godot profil (12 m) → dvojí zářez.
14. Koryto toku: vzorec opsaný z `kraj.voda_tvar` do `koryto_toku_y` (drobné rozdíly smin/max).
15. Hráz rybníka: `kraj._hraz` + `_ryb_hraz_toky`, `ryb_teren` × `ryb_mrizka` záměrně jinak.
16. Terasa (`_terasa_terenu`, natvrdo obdélník): jen ve hře, barva G ani maska se nepřepočítají.
17. Lom: `LOM_Z`/`LESENI_Z` opsané z `plochy.json`, pata se hledá ve hře.
    Brod: Blender 0,12 m, Godot 0,45 m.
18. Vrata: `_teren_pod_vraty` posouvá vrata i terén.
19. Holý břeh toku, tři šířky: `breh_hlina_m` 0,9 / `dno_toku_m` 0,6 / `breh_m` 0,3.
20. `_stare_cesticky`: barva přepsána na louku, maska ne (NEOVĚŘENO).
21. Vybavení se po úpravách terénu znovu neusazuje (kromě posunutých).
22. Díl mlýna: tráva podle G dílu, mimo díl podle masky → šev.

## Riziko nízké
23. `_zamek_terenu`: kontrola, opravuje výšky, ne masku.
24. Druhé vyhloubení Bystřice.
25. Záplaty s barvou natvrdo.
26. `_ves_maska_ulice`: mrtvá větev.
27. Stará zahrada natvrdo.
28. `VES_STARE`: kopie lokace.json natvrdo.
29. `_na_zem`: (470, 830) natvrdo.
30. Rostliny u cest: další použití `cesta_ok`.

## Řešení (návrh): Blender vyváží ves rovnou v novém rámci, Godot nic nepřepisuje
Blender nový rámec už zčásti zná: `kraj._HUMNA` čte `novy_stred`, `nove.NOVY_RAMEC` vyváží zahumenky.
1. **`vesnice.layout()` z `novy_stred`/`novy_yaw`.** `_pads`, `okraj_stavby`, `yard_dirt`, ploty, stodoly, rostliny
   a vybavení se vyvezou na novém místě.
   - Odpadnou `_vo_data`, `_vo_sit`, `_vo_scena`, `_vo_teren`, `VES_STARE`, `_vo_stara_naves`, staré místo jako louka.
   - Řeší body 1, 3, 5, 9, 10, 28, 29.
2. **`ves_paths`/`path_dist` nahradit osou ulice** (`osa_ulice` + `pulsirka` do Pythonu, data v `lokace.ves.ulice`).
   - Barvu i masku pak počítá jedno pravidlo.
   - Godot pro hlínu a trsy bere stejnou šířku (ne `cesta_ok` s rozšířením).
   - Řeší body 2, 11, 26.
3. **Srovnání ulice a podstavu nového domu do `F.land`/`pad_adjust`.** `_zamek_terenu` zůstane jen jako kontrola
   (body 7, 12, 18).
4. **Okraj stavby z obrysu nového domu** v Blenderu i v louce, jeden záznam `pasma.budova` (bod 8).
5. **Terasa, lom a brody jako záznamy** tvarované jen Blenderem, barva a maska podle nich (body 16, 17, 19).
   `CESTA_UDUSANO` z lokace.json (bod 4).

V Godotu zůstane jen vkládání dílů (rybník, mlýn), zářez profilu cest a `_zamek_terenu` jako kontrola.
Postup: po krocích s exportem a snímky před a po (hlídači), každý krok vratný (git + `VES_OBLOUK`).

## Postup (3. 11., Míša „náprav to“)
**Krok 1 – ves v novém rámci z Blenderu** (přepínač `lokace.json ves.blender_novy_ramec`, výchozí false do ověření):
- `blender/ves_ramec.py`: přepis `ves_oblouk.gd` (usedlosti, `presun2`, `osa_ulice`, `pulsirka`, `ulice_pas`).
  Shodu os hlídá test `ves_osa` + `tools/porovnej_osu.py`.
- `vesnice.layout` → `_novy_ramec`: chalupa, stodola a kůlna každé usedlosti na novém místě.
  `ves_paths`/`path_dist` z osy ulice: hlína ulice a odbočky k vratům.
  Mřížka `trava_ves` ±140 m.
- Hra (`svet.VES_BLENDER`): `_vo_jen_ulice` (jen nové domy a srovnání ulice napříč), bez `_vo_sit`, přesunu uzlů,
  přenosu terénu, barvy a masky.
- Odstraňuje body 1, 2 (barva a maska), 3, 5, 6, 9, 10, 28.

Zbývá: krok 2 (srovnání ulice a podstava domu do `F.land`), krok 3 (okraj stavby z obrysu nového domu), krok 4
(terasa, lom, brody, `CESTA_UDUSANO` jako záznamy).

### Stav 3. 11. odpoledne (v kódu, čeká na export `retez_ves1` a ověření)
| # | rozpor | řešení | stav |
|---|---|---|---|
| 1, 3, 5, 6, 9, 10, 28 | přesun vsi ve hře (barva, maska, výška, instance, sítě) | Blender staví ves v novém rámci, hra nepřesouvá (`VES_BLENDER`) | v kódu, zapnuto |
| 2, 11 (část), 26 | šířka a hlína ulice třemi pravidly | `ves_ramec.ulice_pas` v Blenderu pro barvu i masku, hra nepřepočítává | v kódu |
| 12 | srovnání ulice napříč ve hře | `ves_ramec.uprav_y` ve `fort.land` | v kódu |
| 4 | udusaný plac krčmy na starém místě | `svet._krcma_udusano` z lokace | v kódu |
| 7 | placka staré chalupy × podezdívka nového domu | `lokace.json ves.domy_podezdivka` pro Blender placku i `DUM_MER` | v kódu |
| 22 | mlýn: dolina pod hranou dílu | `dil_dolina_vaha` v Blenderu i hře | v kódu |
| – | příkop: průhledná hladina | hloubka = max(odhad, hladina − terén) | v kódu |
| – | cesty braly výšku i s plackami budov (zacyklení) | `flatten` bez placek (pořadí terén → cesty → budovy) | v kódu |

Zbývá: 8 (okraj stavby – Blender teď podle podezdívky domu, louka `_v_budove` totéž + práh; ověřit snímkem),
11 (ploty podle `cesta_ok`), 13 (profil cest dvakrát), 14 (koryto opsaný vzorec), 15 (hráz), 16 (terasa),
17 (lom, brod), 19 (tři šířky holého břehu), 20 (staré cestičky), 21 (vybavení po úpravách terénu).
