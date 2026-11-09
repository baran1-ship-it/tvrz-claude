# Havran: cesty, mosty, brody – co převzít (rozbor 9. 11. z větve claude/new-session-0dtk58)

## Kamenitá vozová cesta
- Data `pravidla/pravidla_sveta.json` pasma.cesta.vozova: drn 2, trsy od 2, keř od 3, kmen 6 m, pricny_podil 1.0, rovne_m 0.6,
  prechod_m 5, kaminky_kraj_m 0.6, **podelny_max 0.125 / okno 20 m**, odchylka 40, napojeni 6. cesty.json: blender_sirka 3,4, pulsirka 2,5, `prechody`.
- Sklon: tools/krok_b/cesty_sklon.py – úseky nad 12,5 % přeplánuje A* (gmax), mosty/brody/napojení pevné body, jinak serpentina.
- Profil (scripts/svet.gd): `_cesty_profil` ř. 6742 (průměr ±10 bodů, sklon 0,14·0,8, zářez/násyp ±3 m, kotvy na terénu);
  `cesta_profil` ř. 6687 (hrboly, koleje 3–5 cm měkké, **výmoly/kaluže** buňky 5 m r 0,4–1 m hl. 5–12 cm); `cesta_useky` ř. 6884
  (úseky 20–90 m každý jiný: výmoly, kamenitost); `cesta_ok` zubatý okraj; `cesta_d` vyklenutí + val + relief z `cesta_atlas_disp.png`.
- Opotřebení `_cesty_opotrebeni` ř. 7093: koleje jen ~40 % délky, bahno do 15 m od vody, vymletí ve svahu > 12 %, u brodu bahno,
  širší zatáčky a křižovatky.
- Kamínky meshe `_cesty_kameny` ř. 8041: kamen_maly_1..5, 3+9·kmn na bod, jen krajnice ok..ok+0,6 m, 0,06–0,2 m (25 % 0,18–0,35 na
  kamenitých úsecích), zapuštěné 35 %.
- Shader `shaders/zem.gdshader` ř. 156–205: atlas 2×2 `obrazky/cesta/cesta_atlas_a.jpg` (forrest_sand prach, dry_mud udusaná hlína,
  rocky_trail kamení, aerial makro 20 m), kamenitost po úsecích, `udus` skvrny 4–12 m, louže `cesta_lz`, height blend okraje.
## Dřevěný most (`blender/kraj.py` ř. 1429–1479, `_bridge` ř. 843)
- **Osa mostu = směr cesty**, span = půl koryta + 1,5 m; **opěry dřevěné** (12 kulatin r 0,13 „kura“ + fošny deska_stodola po 0,25 m drží hlínu násypu);
  4 trámy 0,28×0,32 v ±0,5/±1,5; mostovka fošny napříč 0,2–0,3 × 4 m; piloty span/3,5 (2 kulatiny r 0,17 + jařmo + vzpěra);
  zábradlí sloupky po 1,9 m, 1,05 m, madlo kulatina r 0,07, střední r 0,05; deck_y = max terénu na koncích + 0,3.
- Napojení `tools/krok_b/most_napojeni.py`: osa cesty na ose mostu přes mostovku + **14 m** za konci, kubický oblouk **25 m** zpět, body po 5 m, pak znovu cesty_sklon.
- Nájezdy: násyp koruna 4,8 m, svahy 1:2,5 (kraj.flatten), ve hře `_najezdy_mostu` ř. 2819 / `najezd_y` ř. 2888 (smoothstep, boky 9 m, pod koncem 1:1,25, nikdy do vody).
- `_most_bez_stromu` ř. 5081: stromy ±7 m, keře ±4 m, tráva z mostovky pryč.
## Brod
- cesty.json prechody {druh brod, stred, polomer 6–10, tok}, vzniká automaticky v cesta_k.py (křížení osy s tokem).
- Terén `uprava_y` ř. 9301: dno 0,45 m pod hladinou, šířka 4 m, nájezdy 1:4 zaříznuté do břehu; malé toky `brod_hloubka_m`.
- Kameny `_brody` ř. 9403: mřížka 0,5 m × 5 pruhů, okraje ploché štěrk 7 cm, střed šlapáky žula/droba těsně nad hladinou.
- Cesta v brodu bez vlnění a vyrovnání (kotva), bahno a koleje; vegetace pryč (pásmo cesty), louka.gd ř. 1430 bez trsů v potoce.
## Kroky portu do Puchartu (pořadí)
1. Data `prechody` + vozova parametry; spojit udoli_440_* přes přechody. 2. Osa cesty přes most (most_napojeni) + A* sklon 12,5 %.
3. Brody (detekce, terén, kotva). 4. Profil cesty (kotvy, výmoly, koleje 40 %, kanály masek). 5. Shader atlas + louže (limit vzorkovačů!).
6. Kamínky a štěrk brodů jako meshe. 7. Most dřevěný z kulatin, nájezd = násyp terénu. 8. Vegetace u mostů a brodů. 9. Testy smyslu.
