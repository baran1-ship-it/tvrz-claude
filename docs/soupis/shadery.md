# Soupis čísel a pravidel v shaderech (`shaders/`)

Zdroj: čtení `shaders/*.gdshader`, `*.gdshaderinc` a míst, kde je nastavuje kód (`scripts/svet.gd`, `scripts/louka.gd`,
`scripts/voda.gd`, `scripts/daylight.gd`, `scripts/lide.gd`, `scripts/koryto.gd`, `blender/export_game.py`). Nic se neměnilo.
Sloupec „tabulka“: 2 = POVRCHY, 3 = TŘÍDY (vykreslování), 4 = MATERIÁLY.
Pozn.: `p` = světové xz v metrech, `dd = length(VERTEX)` = vzdálenost od kamery (m). `p / X` = dlaždice X m.

## Co znamenají masky (kdo zapisuje)

| maska | význam | zapisuje |
|---|---|---|
| teren COLOR.r | pole (plodina; 0 = žádná) | `blender/export_game.py:101` (atribut `pole`) |
| teren COLOR.g | míra trávy (0 hlína, ~0,85 louka) | `export_game.py:101` (`grass`); `svet.gd:_stare_cesticky` (CESTICKY_PRYC → louka); `koryto.gd:263` výplň (0, 0.85, 0, 1) |
| teren COLOR.b | les (kryti) | `export_game.py:101` (`les`) |
| teren COLOR.a | 1 = běžná zem; 0,5–1 bahno u rybníka/příkopu; <0,5 dno potoka (oblázky) | `koryto.gd:215` (`0,5 − 0,5·dno`) |
| CUSTOM0 (teren) | (lat / okraj hlíny se znaménkem, s podél osy m, jetost kolejí op.x, okraj m `ok`) | `svet.gd:6896 _cesta_v`, zápis `svet.gd:6994`; mimo cestu (9,0,0,0) |
| CUSTOM1 (teren) | (tráva hřbetu, bahno, abs(od středu koleje)/2, 7 = platné) | `svet.gd:6908`; mimo cestu (0,0,1,0) → `w<6` → rd=0 |
| `stanoviste` RGBA | R jehličnaté, G listnaté koruny, B skály, A pěšina = 0,5 + znaménková vzdálenost od osy / 6 m; mřížka `stan_k` (2 m) | `svet.gd:8439 _stanoviste`, rect z `data.trava_kraj` |
| stebla INSTANCE_CUSTOM (z_custom) | x = druh + 16·q + hash (fract), yzw = pata v soustavě buňky | `louka.gd` rozsev |
| stebla INSTANCE_CUSTOM (staré) | r suchost, g odstín/prah trsu, b buňka atlasu (i+0,5)/6, a = 1 | multimesh |
| kvety INSTANCE_CUSTOM | r barva (0/.25/.5/.75), g hash prahu; z_custom: x = barva + hash, yzw pata | `louka.gd` |
| impostor INSTANCE_CUSTOM | xyz pata vůči uzlu (half float!), w = round(měřítko·256) + otočení/2π | `svet.gd` impostory |
| textura COLOR.r | odstín kusu (0,8 + 0,2·rnd) – jen UV materiály | `export_game.py:103` |
| textura COLOR.b | semeno kusu (rnd) – pestrost tint↔tint2, výřez dřeva, stékance | `export_game.py:103` |
| voda COLOR | potok: R pěna, G peřej, BA směr toku; nádrž: R·4 = hloubka m | `blender/kraj.py:1012`, `scripts/nadrz.gd` |
| reka COLOR.r | hloubka = R·4 m | `tools/reka_bake.gd` |
| reka UV2 | flowmap/distmap s okrajem `i_uv2_sides` | Waterways, `svet.gd:960` |

---

## zem.gdshader (terén: hlína, cesta, louka, pole, les, pěšina, břeh, lom, skála, dálka)

### Uniformy

| soubor:řádek | hodnota | význam | kdo nastavuje / používá | tabulka |
|---|---|---|---|---|
| zem:4–11 | samplery hlina_a/n, louka_a/n, letecky_a, louka_dal_a, obili_a, oranice_a | fotky povrchů (aniso mipmap, repeat) | svet.gd:755–764 (hlina = `obrazky/cesta/cesta_atlas_a/n.jpg` atlas 2×2) | 4 |
| zem:14–15 | pudy_a/pudy_n (pole textur) | vrstvy: 0 udusaná pěšina (nepoužitá), 1 listí, 2 jehličí, 3 písek s jehličím, 4 hrabanka s mechem, 5 oblázky, 6 bahno, 7 skála s lišejníkem, 8 pískovec | svet.gd:10208–10209 | 2/4 |
| zem:16 | pudy_k[9] | kalibrace odrazivosti každé vrstvy | svet.gd:10210 | 4 |
| zem:17 | pudy_m = 2.2 | dlaždice lesních půd 2,2 m (mech ×1,3 → 1,69 m) | svet.gd:10211 (2.2) | 4 |
| zem:20–21 | stanoviste; stan_rect = (−250, −250, 1152, 1602) | maska stanoviště a její obdélník (x0, z0, šířka, výška) | svet.gd:10212–10214 (z data.trava_kraj) | 2 |
| zem:22 | sum | šumová textura (všechny okraje) | svet.gd:798 | 2 |
| zem:25–26 | zrno; zrno_m = 0.8 | zrno trávy (RGB normála, A jas) 0,8 m blízko, ×6 = 4,8 m dál | nenastavuje se (výchozí) | 4 |
| zem:29 | barva_louky = (0.08, 0.10, 0.02) | barva louky z dálky (lineárně) | svet.gd:776 → BARVA_LOUKY (0.145, 0.235, 0.02) svet.gd:7 | 4 |
| zem:30 | barva_lesa = (0.040, 0.070, 0.024) | barva lesa z dálky | svet.gd:788 → BARVA_LESA (0.062, 0.095, 0.015) svet.gd:8 | 4 |
| zem:31 | hlina_m = 2.17 | měřítko hlíny – **shader ho nepoužívá** (ve kódu natvrdo p/2.0) | svet.gd:795 → _size("pesina") = 2.0 | 4 |
| zem:32 | louka_m = 2.0 | louka Grass004, dlaždice 2 m | svet.gd:796 (_size louka = 2.0) | 4 |
| zem:33 | letecky_m = 15.0 | letecký snímek louky (skvrny jasu) 15 m | svet.gd:797 (15) | 4 |
| zem:34 | louka_dal_m = 2.0 | dálková louka Grass001; v dálce ×4 = 8 m | svet.gd:762 (2.0) | 4 |
| zem:36 | hlina_k = 1.0 | kalibrace jasu hlíny | svet.gd:767 a :7280 → 0.64 | 4 |
| zem:37 | lom_rect = 0 | lom x0, z0, x1, z1 | svet.gd:777 → (100, LOM_Z.x−16 = 890, 180, LOM_Z.y+40 = 1015) | 2 |
| zem:38 | lom_y = −1000 | výška dna lomu | svet.gd:787 (výška terénu u stěny z 930/970 + 12 m) | 2 |
| zem:39 | lom_pata[16] | x paty lomové stěny po 5 m od lom_rect.y+16 | svet.gd:779–782 | 2 |
| zem:40 | lom_cerstve = 0 | z0, z1 lámané části (lešení) | svet.gd:778 → LESENI_Z (911, 950.5) | 2 |
| zem:41 | ves_rovna = true | stará rovná náves s kolejemi z ručního vzorce | svet.gd:785 `not VES_OBLOUK` – **jen uvnitř `if TRZISTE` (false)** → zůstává true | 2 |
| zem:42 | trziste = (0, 0, 1, 0) | tržiště: počátek x, z, směr u | svet.gd:784 (jen když TRZISTE; TRZISTE = false, svet.gd:8995) | 2 |
| zem:43 | trziste_r = (0, −1, 0, −1) | u od, u do, v od, v do | svet.gd:786 (TRZ_R = Rect2(−2, 6.5, 24, 12)) – nenastaví se | 2 |
| zem:44–45 | louka_k, louka_dal_k = (1,1,1) | kalibrace po kanálech na barvu atlasu trávy | svet.gd:789–793 (atlas/fotka ×0,95) | 4 |
| zem:46–47 | obili_k, oranice_k = 1.0 | kalibrace | svet.gd:768–771 (cíl 0.20 / 0.10 ÷ průměr fotky) | 4 |
| zem:48–49 | obili_m = 2.0, oranice_m = 3.0 | dlaždice plodin | svet.gd:765, 794 (2.0 / 3.0) | 4 |
| zem:50 | ves = (470, 830) | střed návsi (lány, výjimka pískovce) | nenastavuje se (ruční číslo) | 2 |
| zem:53 | stan_k = 2.0 | krok mřížky stanoviště (m) | svet.gd:10213 (data.trava_kraj.k = 2.0) | 2 |
| zem:55–56 | VES_AU = (0.76193, 0.64764), VES_AV kolmo | osa návsi (blender/vesnice.py AXIS) – const | ruční; svet.gd:7365 VES_D = (0.7620, 0.6476) | 2 |
| zem:58 | HON = 125.0 | velikost buňky Voronoi honů (m) | const | 2 |

### Logika – okraje, hlína, cesta

| soubor:řádek | hodnota | význam | kdo nastavuje / používá | tabulka |
|---|---|---|---|---|
| zem:101–102 | šum p·0.03 (33 m), p·0.13+0.21 (7,7 m) | n1, nf – velký a střední šum okrajů | – | 2 |
| zem:105 | (n1−0,5)·0.8 + (nf−0,5)·0.45; tlumení 0.7·smoothstep(0.55, 0.85, COLOR.g) | nepravidelný okraj cest/dvorů, uprostřed louky skoro nepůsobí | – | 2 |
| zem:107–108 | šum p·0.9+0.43 (1,1 m) ×0.35 | jemné zuby okraje hlíny | – | 2 |
| zem:109 | gm = smoothstep(0.35, 0.6, COLOR.g·0.9 + gn) | váha trávy z barvy vrcholu | – | 2 |
| zem:111–113 | **obdélník nádvoří (−27.6, −16.6)–(18.5, 17.4)**, pás u zdi 1,5–3,2 m, gm × (1 − 0.9) | nádvoří tvrze = udusaná hlína (ruční souřadnice) | ruční | 2 |
| zem:114–118 | trziste/trziste_r, přechod smoothstep(−1.5, 1.5) + šum ×3 / ×0.8 | tržiště = hlína | (neaktivní, TRZISTE=false) | 2 |
| zem:120 | atl(hlina_a, **p / 2.0**, 0) × hlina_k × (1.06, 1.0, 0.91) × mix(0.82, 1.12, nf) | hlína: dlaždice 0 atlasu, 2 m natvrdo; vlhčí/sušší místa | – | 2/4 |
| zem:121 | odbarvení 25 % (luma 0.3/0.55/0.15) | suchý prach, méně do ruda (Míša 0.65) | – | 4 |
| zem:122 | atln(hlina_n, p/2.0, 0) | normála hlíny 2 m | – | 4 |
| zem:89 | fract(uv)·0.99 + 0.005 | okraj 0,5 % dlaždice v atlasu (bez švů) | – | 4 |
| zem:125 | rd = 1 − smoothstep(0.88, 1.1, abs(c0.x) + šum) jen když CUSTOM1.w > 6 | váha cesty z dat (okraj hlíny ~1,0 ±) | CUSTOM0/1 ze svet._cesta_v | 2 |
| zem:128–149 | **stará náves (ves_rovna)**: vu ∈ (−97, 57) od `ves` podél VES_AU; osa v = 2.5·sin(u/23) + 1.2·sin(u/9+1); pás lat < 6 m | **ručně kreslená cesta návsi** (koleje, hřbet) místo dat; konec u rybníčku (POND 74 ± 14) | ruční; podmínka rd<0.01, gm<0.98 | 2 |
| zem:137 | rozchod roz = 0.7 ±0.35·n1 ±0.15·nf (→ 1,4 m mezi kolejemi) | koleje návsi | ruční | 2 |
| zem:138 | koleje šířka smoothstep(0.08, 0.26); úseky smoothstep(0.3, 0.6) | koleje návsi | – | 2 |
| zem:141–142 | hřbet lat < 0.2–0.5 m, ×0.6 | travnatý střed návsi | – | 2 |
| zem:144 | zarůstání od 2–3 m od osy | okraj návsi | – | 2 |
| zem:145 | koleje tmavší ×(1 − 0.22) | – | – | 2/4 |
| zem:147 | gm ≥ stred·0.75, kraj·0.7 | tráva v návsi | – | 2 |
| zem:160–161 | atlas cest 2×2: 0 forrest_sand_01 (2 m) prach, 1 dry_mud_field_001 (3 m), 2 rocky_trail (2 m), 3 aerial_ground_rock (20 m) | povrch cesty (KCD2) | svet.gd:7278 | 2/4 |
| zem:165 | kol = rw·(1 − smoothstep(0.1, 0.42, dk)) | koleje z dat (jetost CUSTOM0.z, vzdálenost CUSTOM1.z) | data | 2 |
| zem:166–169 | p/2.0; p/3.0+0.21; p/2.0+0.37; p/20.0; mac ÷ (0.212, 0.141, 0.100) | dlaždice atlasu cesty v metrech; průměr dlaždice 3 lineárně (sRGB 127,105,89) | – | 4 |
| zem:170 | vlhke = šum p·0.17 (5,9 m)·0.6 + p·0.5 (2 m)·0.4 | vlhká místa cesty | – | 2 |
| zem:173 | stopy smoothstep(0.62, 0.78) šum p·0.21 × smoothstep(0.4, 0.7) p·0.05 | tmavé skvrny stop | – | 2 |
| zem:174 | kopyta = 0.0 | mrtvá proměnná | – | – |
| zem:176–177 | xk = s·0.021 + 7.7; sin(xk), sin(2.31xk+1.7), sin(5.13xk+0.4); smoothstep(0.2, 0.6) | kamenité úseky podél cesty (~300 m perioda) – „stejný vzorec“ jako svet.cesta_useky | duplicita se svet.gd | 2 |
| zem:181–182 | plo = šum p·0.045 (22 m)·0.65 + p·0.13·0.35; udus smoothstep(0.48, 0.62) | velké plochy udusané hlíny 4–12 m | – | 2 |
| zem:183 | tm = max(kol·0.3, stopy·0.2, sucho·0.25, udus·0.62) | míra tmavé hlíny | – | 2 |
| zem:184 | sterk smoothstep(0.58, 0.7) šum p·0.09 | štěrková místa | – | 2 |
| zem:185 | km = kmn·… + šum p·0.33 smoothstep(0.62, 0.8)·0.5 + sterk·0.7 | kamení | – | 2 |
| zem:186 | sand × (1 + 0.1·(1−udus)); mud × 0.9 | – | – | 4 |
| zem:188 | clamp(mac, 0.6, 1.45), síla 0.85 | velké skvrny jasu (KCD2 světlá 2× tmavší) | – | 4 |
| zem:189 | × hlina_k × (1.06, 1.0, 0.91) | barevný posun (cíl R/G 1,16, B/G 0,80) | – | 4 |
| zem:192 | normála kolejí 40 % k rovině | koleje hladší | – | 4 |
| zem:193 | vlh = kol·0.25 + sucho·0.12 | vlhkost kolejí | → ROUGHNESS | 2 |
| zem:195 | gm = smoothstep(0.42, 0.6, CUSTOM1.x + (0.42 − jas písku)·0.9 + šum) | height blend tráva/hlína na cestě | data | 2 |
| zem:198 | louže: smoothstep(0.2, 0.3, 0.18·bm + 0.1·smoothstep(0.4, 0.8, bm) + šum)·0.8 | louže z bahna (CUSTOM1.y) | data | 2 |
| zem:356 | louže: col × (0.62, 0.6, 0.55) + 0.012; mokro = lz·1.4 | tmavší bahno, ne „černé díry“ | – | 4 |

### Louka, pole

| soubor:řádek | hodnota | význam | kdo nastavuje / používá | tabulka |
|---|---|---|---|---|
| zem:208 | p / letecky_m (15 m) | skvrny jasu louky | – | 4 |
| zem:211 | p / (louka_dal_m·4) = 8 m | dálková louka | – | 4 |
| zem:212 | smoothstep(**40, 140**, dd) | přechod blízká → dálková fotka louky | – | 3 |
| zem:213 | clamp(0.8 + 0.4·lum/0.35, 0.7, 1.15) | jas z leteckého snímku (LDR strop 1,15) | – | 4 |
| zem:215–216 | smoothstep(**15, 45**, dd); zrno p/0.8 → p/4.8 | zrno trsu blízko/dál (komentář říká „od 25 m“) | – | 3 |
| zem:217 | × mix(1, 0.55 + zr.a·0.9, 0.55) | síla zrna | – | 4 |
| zem:219–220 | šum p·0.022 (45 m)/p·0.05; (0.84, 0.86, 0.80) ↔ (1.10, 1.08, 0.94) | makro skvrny louky 20–50 m | stejný šum v barva_krajiny | 4 |
| zem:225 | pm = smoothstep(0.3, 0.6, COLOR.r + šum p·0.035·0.5 + nf·0.25) × (1 − rd) | oblast polí z barvy vrcholu; na cestě ne | – | 2 |
| zem:229–241 | Voronoi buňky HON = 125 m, střed 0.15 + 0.7·hash | hony | ruční (jako blender/kraj.py hon()) | 2 |
| zem:244–245 | úhel lánu 0–π, šířka w = 9–18 m | lány | – | 2 |
| zem:247 | zvlnění šum p·0.011 ×0.35 | hranice lánů | – | 2 |
| zem:250–255 | plodina hash % 4: 0 obilí (obili_m), 1 louka_dal, 2 oranice (oranice_m), 3 louka | plodiny | – | 2 |
| zem:257 | brázdy 0.92 + 0.08·sin(6·t) (perioda ~1,05 m) | brázdy | – | 2 |
| zem:258 | mez lánu smoothstep(0.03, 0.09) / (0.97, 0.995) | travnatá mez | – | 2 |
| zem:259 | mez honů 2–3,5 m | – | – | 2 |
| zem:260 | × (0.85 + 0.3·n1) | jas plodiny | – | 4 |

### Les, pěšina, břeh, lom, skála

| soubor:řádek | hodnota | význam | kdo nastavuje / používá | tabulka |
|---|---|---|---|---|
| zem:269–274 | mimo masku: les ze šumu p·0.0021 (~480 m) + p·0.011, smoothstep(0.44, 0.56); st = (0.35·l, 0.65·l, 0, 1) | lesy na obzoru (300–600 m) | ruční | 2 |
| zem:277 | les = max(COLOR.b, smoothstep(0.6, 1.0, st.r+st.g)) | půda pod korunami (krytí ≥ 0,6) | – | 2 |
| zem:282 | jehl smoothstep(0.35, 0.65, R/(R+G+0.08) + šum) | jehličí vs listí | – | 2 |
| zem:283 | skal smoothstep(0.25, 0.6, st.b) × jehl | písek s jehličím u skal | – | 2 |
| zem:285 | mech smoothstep(0.55, 0.8, (−n.z·0.6 + st.b·0.5 + šum)·0.7 + n3·0.3) | mech na severních svazích, u skal | – | 2 |
| zem:288 | up·1.3 (1,69 m) vrstva 4 | hrabanka s mechem | – | 4 |
| zem:291 | lm = smoothstep(0.25, 0.75, les + šum p·0.04·0.7 + nf·0.3) | přechod les/louka 2–4 m | – | 2 |
| zem:292 | lm × mix(1, gm, rd) | cesta lesem = hlína | – | 2 |
| zem:298 | abs(st.a − 0.5) < 0.45 | pěšina: kódování A = 0,5 + d/6 → do ±2,7 m | svet._stanoviste | 2 |
| zem:305–311 | (A − 0.5)·6 m; přepnutí lin/bez smoothstep(1.4, 1.9) | vzdálenost od osy pěšiny | – | 2 |
| zem:312 | pes = 1 − smoothstep(0.45, 0.7, lat + šum) | šířka pěšiny ~1 m (±0,45–0,7) | – | 2 |
| zem:314 | stopa |lat − 0.28| 0.1–0.24 | vyšlapané stopy | – | 2 |
| zem:315–316 | střed < 0.06–0.14 m; tráva ×0.25; stopy ×(1 − 0.08) | travnatý pruh pěšiny | – | 2 |
| zem:317 | pw = pes·(1 − 0.7·pm)·(1 − 0.3·lm) | pěšina slabší v poli a lese | – | 2 |
| zem:325 | bahno: COLOR.a ≥ 0.5, smoothstep(0.02, 0.6, (1−a)·2 + šum) | bahno u rybníka/příkopu | koryto.gd / blender | 2 |
| zem:327 | p / 2.0, vrstva 6 | dlaždice bahna 2 m | – | 4 |
| zem:331 | koryto: COLOR.a < 0.5 | dno potoka | koryto.gd:215 | 2 |
| zem:333 | p / 1.6, vrstva 5 | oblázky 1,6 m | – | 4 |
| zem:349 | pis = smoothstep(0.74, 0.6, n.y + šum) (~42–53°) | skalní stěna pískovce | – | 2 |
| zem:351 | v_lomu = obdélník lom_rect | lom | data svet.gd:777 (x 100–180 ručně) | 2 |
| zem:352 | lom_st = smoothstep(0.8, 0.6, n.y) | lomová stěna (od ~37°) | – | 2 |
| zem:360 | dno lomu do lom_y + 2…4 m; okraj ÷4 m od rect | dno lomu | – | 2 |
| zem:362–363 | (z − lom_rect.y − 16)/5, 0–14.99 | interpolace lom_pata po 5 m | – | 2 |
| zem:364 | lokr = 27.5 + 1.8·sin(0.19z+1.3) + 1.2·sin(0.47z+0.4) + 0.8·sin(1.07z) | **ručně**: udusaná plocha 23–31 m od paty (svet.lom_okraj) | duplicita se svet.gd | 2 |
| zem:365 | přechod −1.2/+0.8 m, šum ×2.5 | roztřepený okraj | – | 2 |
| zem:367 | p / 1.6 vrstva 5 | štěrk lomu (z oblázků) | – | 4 |
| zem:369 | osa kolejí 0.55·šířky rect + šum ×14 m | **ručně**: koleje v lomu | – | 2 |
| zem:370 | abs(abs(ox) − 0.7): 0.12–0.3 → rozchod 1,4 m | koleje lomu | – | 2 |
| zem:371–372 | jas ×5 clamp(0.7, 1.3); šedá (0.33, 0.32, 0.295) | štěrk lomu (barva natvrdo) | – | 4 |
| zem:373 | hlína × 1.1, 25–60 % | bláto mezi štěrkem | – | 4 |
| zem:377–380 | louže smoothstep(0.72, 0.76); col·0.45 + (0.03, 0.04, 0.05); vlh ×6, mokro ×1.6 | louže v lomu | – | 2/4 |
| zem:384 | **u_tvrze = |x + 4| < 80 a |z| < 75** (obdélník) | u tvrze není skála (val, příkop) | ruční | 2 |
| zem:385 | pískovec jen COLOR.a ≥ 0.999, mimo tvrz, **≥ 140 m od ves** | – | ruční | 2 |
| zem:388 | rula: smoothstep(0.82, 0.72, n.y + šum) (~35–44°) | mírnější strmina | – | 2 |
| zem:391 | triplanár pow(abs(n), 4) | váhy projekcí | – | 4 |
| zem:396–397 | wp / 2.6, vrstva 7 | rula/kámen s lišejníkem 2,6 m | – | 4 |
| zem:400–402 | odbarvení 35 % × (1, 1, 0.82); × (0.85 + 0.3·n1); mech (0.045, 0.05, 0.022) 25 % | šedozelená rula (Posázaví) | – | 4 |
| zem:407–411 | bloky 3.2 m vodorovně, 2.2 m svisle, posun 0.41; spáry 0.025/0.03 | **lomová stěna – bloky** | – | 4 |
| zem:413–417 | šedá × (0.98, 1, 1.02) × (0.8 + 0.4·tl); okr × (1.12, 0.98, 0.8) 40–90 % | barva lomového kamene | – | 4 |
| zem:419–422 | čerstvé plochy lom_cerstve ±1–3 m, do lom_y + 9…13 m; ×(1.1, 1.08, 1.04) 30 % | lámaná část | data | 4 |
| zem:425 | normála ×0.5 k rovině | – | – | 4 |
| zem:431–434 | pískovec wp/2.4 (fotka 1,83 m) + hrubá wp/7.3 45 % | dvě měřítka pískovce | – | 4 |
| zem:437–439 | lavice: wp.y/1.9 + šum (vrstvy 0,6–4 m) | vrstvy pískovce | – | 4 |
| zem:445 | šířka spáry 0.025–0.09 | – | – | 4 |
| zem:452 | bloky 3–10 m; pukliny 35 % otevřených | – | – | 4 |
| zem:464–469 | odbarvení 60 % × (1.08, 1, 0.86); odstíny (1.1, 0.97, 0.82)…(1.0, 0.99, 0.95), (1.06, 0.95, 0.84); lišejník (0.95, 0.97, 0.88)·1.05 55 % | barvy pískovce (Prachovské skály) | – | 4 |
| zem:470 | spára −55 %, puklina −50 %, stékance −30 % | – | – | 4 |
| zem:473 | mech (0.035, 0.05, 0.022) 60 % | mech ve spárách | – | 4 |
| zem:478 | relief dprof × 0.35 | relief lavic bez normálové mapy | – | 4 |

### Dálka, výstup

| soubor:řádek | hodnota | význam | kdo nastavuje / používá | tabulka |
|---|---|---|---|---|
| zem:489 | far = smoothstep(**70, 100**, dd) × (1 − 0.6·sk − 0.35·pis) | od 70 m prolínání, od 100 m jen barva krajiny (KCD e_TerrainDetailMaterialsViewDistZ = 100) | – | 3 |
| zem:493 | × (1 − 0.3·pm) × (1 − pes) × (1 − rd·(1−gm)) | pole, pěšina a cesta zůstávají vidět i za 100 m | – | 3 |
| zem:497 | strm < 0.8 | vlastní tečný rámec na strmině | – | 4 |
| zem:505 | ROUGHNESS = max(0.95 − 0.05·vlh·(1−gm) − 0.2·mokro, **0.55**) | drsnost země 0,95; vlhké koleje jen −0,05; minimum 0,55 | – | 4 |
| zem:506 | normála louky = mix(louka_n p/2 m, zrno, 0.6) | – | – | 4 |
| zem:509 | nl.b < 0.4 → rovná normála | pojistka proti rozbitému vzorku (sníh) | – | 4 |
| zem:511 | SPECULAR = (0.5 − 0.35·sk)·(1 − 0.6·mokro) | 0,5 země, 0,15 skála | – | 4 |
| zem:52 (kom.) | „na Adrenu má materiál jen 13 vzorkovačů“ | zákaz dalšího sampleru | – | 4 |

---

## barva_krajiny.gdshaderinc (společná barva dálky)

| soubor:řádek | hodnota | význam | kdo nastavuje / používá | tabulka |
|---|---|---|---|---|
| barva_krajiny:5 | n1 = šum p·0.03 | jas lesa | zem:491, stebla:160 | 3/4 |
| barva_krajiny:6 | mk = šum p·0.022·0.65 + p·0.05·0.35 | makro skvrny (stejné jako zem:219) | – | 4 |
| barva_krajiny:7 | louka × mix(0.85, 1.12, mk); les × (0.8 + 0.4·n1); les = smoothstep(0.2, 0.6, max(les_v, R+G)) | barva krajiny z dálky (louka vs. les) | barva_louky/lesa ze svet.gd | 4 |

## projekce.gdshaderinc (světové UV v metrech)

| soubor:řádek | hodnota | význam | kdo nastavuje / používá | tabulka |
|---|---|---|---|---|
| projekce:4 | abs(n.y) > 0.7 → uv = xz | vodorovná plocha (~45°) | zdivo, textura (svet=true) | 4 |
| projekce:9–11 | uv = (podél zdi, výška) | svislá plocha | – | 4 |
| projekce:14 | uv += (d·0.37, d·0.61) | posun podle roviny (každá stěna jiný výřez) | – | 4 |

---

## stebla.gdshader (trsy trávy, drn, vějíř, kupy)

| soubor:řádek | hodnota | význam | kdo nastavuje / používá | tabulka |
|---|---|---|---|---|
| stebla:8 | render_mode … vertex_lighting, **alpha_to_coverage_and_one**, specular_disabled | bez discard (early-Z), alfa jako pokrytí MSAA | (na tabletu nikdy MSAA – viz rozpory) | 3/4 |
| stebla:10 | atlas | atlas trsů 3×2 (`obrazky/trava_atlas.png`) | louka.gd:1389, 1448, 1529, 1577 | 4 |
| stebla:11 | vitr = 1.0 | síla větru | louka.gd:1530 (0.4), :1578 | 3 |
| stebla:14–16 | fade_od = −1, fade_do = 100000, fade_sirka = 14 | pásmo viditelnosti (náběh fade_od…+12 m, mizení fade_do−14…fade_do) | louka.gd:946–948 (_mat_pas) | 3 |
| stebla:17 | prah = 0.5 | alfa nůžky | louka.gd:1454 (0.4) | 4 |
| stebla:21–22 | z_custom = false, hustota = 1.0 | offline rozsev | louka.gd:137–139 (true, hustota) | 3 |
| stebla:23 | hust_od = 20 | od 20 m řídne | louka.gd:130 (vějíř 15) | 3 |
| stebla:26 | hust_zbytek = 0.0 | zbytek hustoty na hust_do | louka.gd:132 (vějíř 0.25) | 3 |
| stebla:27 | vejir = false | – | louka.gd:134 | 3 |
| stebla:28 | shora_mizi = false | kupy mizí při pohledu shora | louka.gd:141 | 3 |
| stebla:29 | jas = 1.0 | – | louka.gd:138 (0.85) | 4 |
| stebla:31 | svetlo = (1,1,1) | světlo unshaded varianty (tablet) | louka.gd:1494 | 4 |
| stebla:32 | hust_konec = 1e6 | od hust_konec do +30 m → 0 | louka.gd:133 (vějíř 40) | 3 |
| stebla:33 | hust_do = 130 | konec řídnutí | louka.gd:128 (trs 80 tablet / 110 PC), :131 (vějíř 40) | 3 |
| stebla:35–36 | sloupce 3, radky 2 | mřížka atlasu | louka.gd:1450–1451 | 4 |
| stebla:37–39 | rezim 0; vyska_od 0.15, vyska_do 0.3 | grass_pack výšky (m) | louka.gd:1449–1453 | 4 |
| stebla:42–43 | teren_od = 40, teren_do = 80 | trs dostává barvu krajiny 40→80 m | louka.gd:150–151: trs 40–80, vysoká 40–80, drn 20–40, vějíř 30–70, kupa 0–1 | 3 |
| stebla:45 | stan_rect = (−250, −250, 1152, 1602) | jako zem | louka.gd:153 (kopíruje ze zem) | 2 |
| stebla:47–48 | barva_louky/lesa (0.08, 0.10, 0.02)/(0.040, 0.070, 0.024) | jako zem | louka.gd:153 (kopíruje ze zem) | 4 |
| stebla:69 | navíc = 1 + 0.1·q | neudržovaná louka ×1,3 | louka.gd _nacti | 3 |
| stebla:74–75 | dal = smoothstep(hust_od, hust_do, d); ×1.1 | hustota podle vzdálenosti (2D) | – | 3 |
| stebla:77–79 | výška karty podle druhu: 0.36, 0.5, 0.6, 0.82, 0.6, 0.28, 0.55, 0.32 m | výšky trsů (druh 0–7) | ruční tabulka | 4 |
| stebla:84 | měřítko × 0.75–1.25; mizí zmenšením (hu − hs)/0.1; v dálce ×1.6 | trs v dálce větší | – | 3 |
| stebla:86 | výška ×0.85–1.15 | – | – | 4 |
| stebla:88 | suchost druh 4 = 0.1, jinak 0–0.15 | – | – | 4 |
| stebla:99–101 | fade_do − fade_sirka … fade_do; fade_od … fade_od + **12** | pásmo (3D vzdálenost) | – | 3 |
| stebla:104 | t = TIME·1.6 + x·0.21 + z·0.17 | vítr – rychlost a fáze | – | 3 |
| stebla:106 | k = výška²·0.09·vitr; byliny (buňka 3–4) ×0.4 | amplituda větru 9 cm | – | 3 |
| stebla:107–108 | x: sin·0.7 + sin(2.3t)·0.3; z: cos(0.8t)·0.6 | směr větru natvrdo (převážně +x) | – | 3 |
| stebla:111 | normála 75 % nahoru | – | – | 4 |
| stebla:119–121 | Bayer 4×4, 8 %; prah trsu fract(g·13.71 + 0.37) | rozpad po trsech | stejné v kvety | 3 |
| stebla:124 | shora mizí smoothstep(0.35, 0.6, vy) | kupy shora | – | 3 |
| stebla:127 | okraj buňky 0.01/0.02/0.99/0.995 | bez prosakování mipmap | – | 4 |
| stebla:137 | alfa × (1 + mip·0.3) | pokrytí v mipmapách | – | 4 |
| stebla:139 | ALPHA_ANTIALIASING_EDGE = prah·0.8 | – | – | 4 |
| stebla:144 | grass_pack → (0.75, 0.95, 0.35)·l 55 %, ×0.8 | přebarvení do louky | – | 4 |
| stebla:148–149 | suchá (1.5, 1.3, 0.55)·l; jas 0.88–1.12 | – | – | 4 |
| stebla:154 | blizko = 1 − smoothstep(**30, 40**, d) | tmavá pata jen do 40 m | – | 3 |
| stebla:155 | vějíř ×0.75; pata 0.75→1.0 (√výška) | – | – | 4 |
| stebla:167–168 | AO 0.8–1.0, AO_LIGHT_AFFECT 0.5 | – | – | 4 |
| stebla:169 | ROUGHNESS = 0.9 | – | – | 4 |
| stebla:170 | BACKLIGHT × (0.9, 1.0, 0.6) × (0.15 + 0.35·výška) | prosvítání | – | 4 |

## kvety.gdshader

| soubor:řádek | hodnota | význam | kdo nastavuje / používá | tabulka |
|---|---|---|---|---|
| kvety:2 | atlas 512×128, 4 barvy, posun 0.25 | – | louka.gd | 4 |
| kvety:7–8 | fade_od −1 (nepoužit), fade_do 100000 | – | louka.gd _mat_pas | 3 |
| kvety:11–13 | hustota 1, hust_od **12**, hust_do **45** | květy řídnou 12→45 m (bez zbytku) | louka.gd:137–139 (z_custom, hustota) | 3 |
| kvety:30 | měřítko 1.1–1.9 | – | – | 4 |
| kvety:39 | mizení fade_do − **10** … fade_do | – | – | 3 |
| kvety:40–41 | vítr TIME·1.6 + x·0.21 + z·0.17; ×0.03 | jako stebla | – | 3 |
| kvety:47 | Bayer 8 %, discard | – | – | 3 |
| kvety:51 | discard alfa < 0.5 | – | – | 4 |
| kvety:55–56 | ROUGHNESS 0.9, BACKLIGHT 0.25 | – | – | 4 |

## listi.gdshader (koruny stromů a keřů)

| soubor:řádek | hodnota | význam | kdo nastavuje / používá | tabulka |
|---|---|---|---|---|
| listi:6 | depth_prepass_alpha, cull_disabled, specular_disabled | – | – | 3/4 |
| listi:9 | tint = 1 | barva listí | svet.gd:3376, :10360 (TINT_LISTI) | 4 |
| listi:10 | prah = 0.5 | nůžky | svet.gd:3377 (z modelu) | 4 |
| listi:11–12 | stred = (0, 6, 0), vyska = 10 | střed a výška koruny | svet.gd:3379–3380 (bbox, 0.62 strom / 0.5 keř) | 4 |
| listi:13 | sila_vetru = 1 | – | svet.gd:3381 (strom 1, keř 0.6) | 3 |
| listi:14 | objem = 0.65 | normály od středu koruny | svet.gd:3382 (0.65 / 0.5) | 4 |
| listi:15 | vitr_smer = (0.8, 0.6) | směr větru | nenastavuje se | 3 |
| listi:22 | fáze x·0.13 + z·0.11 | – | – | 3 |
| listi:24 | kývání (sin(0.9t)·0.6 + sin(1.7t)·0.3)·h²·**0.18** | koruna ±18 % nahoře | – | 3 |
| listi:26 | chvění sin(6t)·0.025·h | – | – | 3 |
| listi:32–33 | r_kor = max(0.3·výška, 0.8); AO od 0.15·r | vnitřek tmavší | – | 4 |
| listi:34–36 | tint trsu (0.86, 0.9, 0.82)…(1.1, 1.08, 0.92), buňka 1/1.3 m | pestrost | – | 4 |
| listi:38 | od.y ≥ −0.15 | spodek koruny ne černý | – | 4 |
| listi:44 | AO 0.5–1.0 | – | – | 4 |
| listi:50 | alfa × (1 + lod·0.35) | – | – | 4 |
| listi:53–54 | BACKLIGHT 0.5, ROUGHNESS 0.85 | – | – | 4 |

## impostor.gdshader (stromy v dálce)

| soubor:řádek | hodnota | význam | kdo nastavuje / používá | tabulka |
|---|---|---|---|---|
| impostor:2,16 | atlas 8×8 hemi-oktaedr | pohledy | blender/impostory.py | 4 |
| impostor:10–11 | stred (0, 8, 0), polomer 8 | koule stromu | svet.gd:3454–3455 (meta) | 4 |
| impostor:12 | fade_od = 50 („plný strom končí na 60 m“) | náběh impostoru | svet.gd:3456 → STROM_PREP − 10 = **30 tablet / 50 PC** | 3 |
| impostor:13 | fade_do = 900 | dohled | svet.gd:3457 (dohled) | 3 |
| impostor:14 | tint = 1 | – | svet.gd:3460 TINT_LISTI | 4 |
| impostor:25–26 | w: floor/256 = měřítko, fract = otočení | – | – | – |
| impostor:40 | f.y ≤ 0.95 | – | – | 4 |
| impostor:46 | náběh fade_od…+**10** m; mizení fade_do − **60**…fade_do | – | – | 3 |
| impostor:56 | discard alfa < 0.5 | – | – | 4 |
| impostor:61–62 | listí: g − 0.8·max(r, b) 0–0.08; stín 0.55 dole → 0.85 nahoře | – | – | 4 |
| impostor:69 | ROUGHNESS 0.9 | – | – | 4 |

## zdivo.gdshader (lomové zdivo s omítkou)

| soubor:řádek | hodnota | význam | kdo nastavuje / používá | tabulka |
|---|---|---|---|---|
| zdivo:14 | kamen_m = 2.5 | dlaždice kamene (m) | svet.gd:705 (_size zdivo = 2.5) | 4 |
| zdivo:15 | omitka_m = 2.0 | dlaždice omítky | svet.gd:706 | 4 |
| zdivo:16 | kryti = 0.5 | míra omítky | svet.gd:707 (materialy.kryti) | 4 |
| zdivo:17–18 | tint 1; kamen_tint (0.72, 0.68, 0.62) | – | svet.gd:708–709 | 4 |
| zdivo:19 | spina = 1 | – | svet.gd:710 | 4 |
| zdivo:20 | hloubka = 0.05 m | hloubka spár (parallax) | nenastavuje se | 4 |
| zdivo:21 | kroky = 12 (max 24, ×1.6 šikmo) | parallax | – | 3/4 |
| zdivo:22 | h_rozsah (0.42, 0.95) | – | – | 4 |
| zdivo:47 | parallax 1 − smoothstep(**12, 25**, dist); úhel 0.12–0.45 | LOD parallaxu | – | 3 |
| zdivo:74–75 | šum uv·(0.05, 0.075) (20×13 m), uv·0.6 | skvrny omítky | – | 4 |
| zdivo:76 | lowz 0–2,2 m | kámen u paty zdi | – | 4 |
| zdivo:78–79 | cover = big + (kryti−0.5)·0.22 + 0.15 − lowz·0.24; smoothstep(0.40, 0.56) | – | – | 4 |
| zdivo:81–82 | malta ve spárách smoothstep(0.05, 0.35)·0.85 | – | – | 4 |
| zdivo:85 | spáry 0.55–1.0 | – | – | 4 |
| zdivo:88 | omítka 75 % šedá × mix(tint, (0.93, 0.9, 0.84), 0.6) | vápenná | – | 4 |
| zdivo:89–94 | tón uv·0.012 ×(0.72, 0.68, 0.6); stékance ×(0.62, 0.6, 0.55); vlhko 0.3–1.9 m ×(0.35, 0.32, 0.26) | špína | – | 4 |
| zdivo:99–100 | špína u země −0.3…1.0 m, (0.06, 0.05, 0.035) | – | – | 4 |
| zdivo:102 | ROUGHNESS z textur | – | – | 4 |
| zdivo:103 | SPECULAR 0.3 | – | – | 4 |
| zdivo:104–105 | AO 0.35–1.0, AO_LIGHT_AFFECT 0.6 | – | – | 4 |
| zdivo:108 | normála kamene ×1.4, omítky ×0.6 | – | – | 4 |

## textura.gdshader (fotografický materiál, UV v metrech)

| soubor:řádek | hodnota | význam | kdo nastavuje / používá | tabulka |
|---|---|---|---|---|
| textura:8 | velikost = 2.0 | dlaždice (m) | svet.gd:720 (_size), :1849 (trám 1.2) | 4 |
| textura:9–10 | prohodit, svet | UV vs. světová projekce | svet.gd:721–722 | 4 |
| textura:11–15 | tint, sedost 0, tint2, pestrost 0, spina_dole 0 | – | svet.gd:723–730 | 4 |
| textura:17–18 | hloubka 0; h_rozsah (0.2, 0.9) | parallax | svet.gd:747 HLOUBKA (0.008–0.07 m) | 4 |
| textura:20–24 | skvrny, antitile, radky, kus, stekance = 0 | – | svet.gd:733–744 (stekance 0.55 roubení/lata/dub_ven/sindel_hra, jinak 0.4) | 4 |
| textura:55 | parallax 1 − smoothstep(**10, 22**, d) | LOD parallaxu (10 kroků) | – | 3 |
| textura:74 | antitile: rotace (0.8, 0.6), měřítko 0.61 | – | – | 4 |
| textura:75 | šum wp.xz·0.06 (17 m) | – | – | 4 |
| textura:79 | × (0.8 + 0.4·g) dlaždice ×0.17 | – | – | 4 |
| textura:81–84 | mech n.y 0.15–0.6; (0.1, 0.16, 0.05)…(0.24, 0.3, 0.09) 90 % | – | – | 4 |
| textura:89–94 | šindel: posun 0.37/0.71, šum 0.21/0.13 | – | – | 4 |
| textura:101–113 | dřevo: měřítko (0.83, 0.77), tmavé ×(0.5, 0.47, 0.44), světlé ×(1.25, 1.18, 1.08) | – | – | 4 |
| textura:116 | šedost (g, 0.97g, 0.9g) | – | – | 4 |
| textura:118 | × tint × COLOR.r (jen UV) | – | – | 4 |
| textura:119 | špína −0.2…1.0 m (0.06, 0.05, 0.035) | – | – | 4 |
| textura:124–125 | skvrny 0.62–1.18; lišejník ×(0.85, 0.9, 0.7) | – | – | 4 |
| textura:128–135 | stékance: h = x·0.93 + z·1.07; tmavé ×(0.55, 0.5, 0.45) | – | – | 4 |
| textura:138–139 | AO 0.4–1.0, 0.5 | – | – | 4 |
| textura:141 | SPECULAR 0.35 | – | – | 4 |

## skala_detail.gdshader (skalní věže)

| soubor:řádek | hodnota | význam | kdo nastavuje / používá | tabulka |
|---|---|---|---|---|
| skala_detail:10 | detail_m = 2.0 | fotka pískovce (m) | svet.gd:3592 → _size("skala_piskovec") = 1.83 | 4 |
| skala_detail:11 | detail_prumer = 0.3 | průměrný jas fotky | svet.gd:3593 (albedo.json, výchozí 0.2) | 4 |
| skala_detail:22 | triplanár pow 4 | – | – | 4 |
| skala_detail:28 | detail 1 − smoothstep(**25, 60**, d) | LOD detailu | – | 3 |
| skala_detail:30 | jas 0.5–1.6, síla 0.7 | – | – | 4 |
| skala_detail:33 | normála detailu 40 % | – | – | 4 |
| skala_detail:34–35 | ROUGHNESS 0.92, SPECULAR 0.3 | – | – | 4 |

## voda.gdshader (příkop, rybník, potok)

| soubor:řádek | hodnota | význam | kdo nastavuje / používá | tabulka |
|---|---|---|---|---|
| voda:9–10 | **bez hint_screen_texture** (tablet Adreno spadl) | zákaz screen texture | – | 4 |
| voda:11 | deep (0.02, 0.045, 0.04) | hluboká voda | svet.gd:812, 844 → (0.08, 0.115, 0.08) | 4 |
| voda:12 | zakal (0.09, 0.11, 0.07) | kal | svet.gd:810 (tekoucí 0.1, 0.11, 0.07 / stojatá 0.13, 0.16, 0.10), :845 (0.13, 0.16, 0.11) | 4 |
| voda:13 | kalnost 0.75 | – | svet.gd:809 (0.35 / 0.82), :846 (0.82) | 4 |
| voda:14–15 | tekouci 0, okrehek 0 | – | svet.gd:807–808 | 4 |
| voda:16–17 | rip[8], hrac | vlnky, čeření u nohou (poloměr 0.22 + hloubka·0.12) | voda.gd:29, :67 | 3 |
| voda:18 | vitr = (0.8, 0.6) | směr větru | nenastavuje se | 3 |
| voda:19 | hloubka_vrcholu false (COLOR.r·4 m), jinak 10 m | – | svet.gd:813, 847 | 4 |
| voda:30–35 | tok: posun 2.857·rych; protažení 0.6/1.1; měřítka 0.3, 0.66, 0.45, 0.95 | – | – | 4 |
| voda:57–58 | poskakování pěna·0.06 + peřej·0.03 m | – | – | 3 |
| voda:62 | stojatá vlna 0.01 m | – | – | 3 |
| voda:72–73 | rych 0.8 + 1.3·peřej; fáze TIME·0.35 | – | – | 3 |
| voda:91 | stojatá: uv × 0.09 (11 m) ×1, 1.7, 4.3 | normály hladiny | – | 4 |
| voda:95 | poryvy šum p·0.025 (40 m), 0.45–0.75 | – | – | 4 |
| voda:104–108 | vlnky do 4 s, 0.55 m/s, cos(28x) | – | – | 3 |
| voda:126 | NORMAL_MAP_DEPTH 0.7 / 0.22 | – | – | 4 |
| voda:133 | okřehek šum p·0.04, 0.62–0.68 | – | – | 4 |
| voda:139 | fresnel 0.04 + 0.96·(1−cos)^5 | – | – | 4 |
| voda:140 | zákal ×(−VERTEX.z/60) | dál víc kalu (do 60 m) | – | 3 |
| voda:142 | op × smoothstep(0, 1.2, hloubka) | mělko u břehu | – | 4 |
| voda:147–148 | povrch (0.01) / okřehek (0.06, 0.1, 0.03) / (0.1, 0.18, 0.03); pěna (0.55, 0.57, 0.52) | – | – | 4 |
| voda:157 | ROUGHNESS 0.03 → 0.5 (pěna, okřehek) | – | – | 4 |
| voda:158 | SPECULAR 0.6 tekoucí / 0.35 stojatá → 0.2 | – | – | 4 |
| voda:162 | ALPHA smoothstep(0, 0.12, hl) × (0.35–1) | břeh bez hrany | – | 4 |

## reka.gdshader (potok Waterways)

| soubor:řádek | hodnota | význam | kdo nastavuje / používá | tabulka |
|---|---|---|---|---|
| reka:1–3 | bez hloubkové a screen textury | – | – | 4 |
| reka:20 | normal_scale 1.0 | – | svet.gd:962 (0.6) | 4 |
| reka:22 | uv_scale (1, 1, 1) | – | nenastavuje se | 4 |
| reka:23 | roughness 0.2 | – | svet.gd:963 (0.15) | 4 |
| reka:24 | edge_fade 0.25 | – | nepoužito | – |
| reka:28–35 | albedo_color, albedo_depth 10, transparency_* | z Waterways – **nepoužité** (barvu dělá melka/hluboka) | – | – |
| reka:38 | flow_speed 1.0 | – | svet.gd:961 (0.3) | 3 |
| reka:39–43 | flow_base 0, steepness 2, distance 1, pressure 1, max 4 | – | – | 3 |
| reka:46–49 | foam_color (0.9, 0.9, 0.9, 1), amount 2, steepness 2, smoothness 0.3 | – | svet.gd:964–965 (1.2; (0.7, 0.72, 0.66, 0.6)) | 4 |
| reka:52 | i_lod0_distance 50 | druhá vrstva normál do 50 m | nenastavuje se (viz rozpory) | 3 |
| reka:57 | i_uv2_sides 2 | – | svet.gd:960 (meta) | – |
| reka:112–113 | melka (0.353, 0.42, 0.227) #5A6B3A, hluboka (0.118, 0.165, 0.11) #1E2A1C | – | svet.gd:967–968 ((0.24, 0.27, 0.15), (0.06, 0.08, 0.05)) | 4 |
| reka:114 | hloubka_barvy 1.2 m | – | svet.gd:969 (1.4) | 4 |
| reka:115 | cirost 0.35 m | průhledná do této hloubky | svet.gd:970 (0.55) | 4 |
| reka:119 | kam[12] | kameny v toku | svet.gd:1000 | 2 |
| reka:136 | jen do r·3 + 0.8 m od kamene | – | – | 3 |
| reka:141–153 | věnce sin(26·od − 7t); pěna exp·18; úplav r·5 + 0.6 | – | – | 4 |
| reka:193–195 | jump (0.24, 0.208), (0.20, 0.25), (0.22, 0.27) | – | – | 4 |
| reka:237 | ALPHA smoothstep(0, cirost)·0.92 + pěna | – | – | 4 |
| reka:238 | SPECULAR 0.25 | – | – | 4 |

## sky.gdshader

| soubor:řádek | hodnota | význam | kdo nastavuje / používá | tabulka |
|---|---|---|---|---|
| sky:4–7 | zenith (0.15, 0.33, 0.64), horizon (0.7, 0.76, 0.8), ground (0.22, 0.21, 0.19), sun_tint (1, 0.86, 0.66) | barvy oblohy | daylight.gd:246–255 (podle denní doby; ground = horizont × 0.32/0.31/0.3) | 4 |
| sky:8–14 | sun_glow 0.4, cloud_lit/dark, cloud_cover 0.46, stars 0, energy 1 | – | daylight.gd:249–253 (cloud_cover se nenastavuje) | 4 |
| sky:26 | pow(up, 0.55) | gradient | – | 4 |
| sky:30 | záře pow 5 ·0.22 + pow 40 ·0.5 | – | – | 4 |
| sky:33–36 | hvězdy mřížka 190, práh 0.9965 | – | – | 4 |
| sky:40–42 | mraky uv = xz/(y + 0.14)·0.12; okraj 0.26 | – | – | 4 |
| sky:55 | disk slunce ×3, energie ≤ 4 | – | – | 4 |

## malba.gdshader, sklo.gdshader, postava_hlava.gdshader

| soubor:řádek | hodnota | význam | kdo nastavuje / používá | tabulka |
|---|---|---|---|---|
| malba:3–4 | zaklad (0.62, 0.6, 0.55), barva (0.28, 0.36, 0.42) | malovaná omítka | svet.gd:819–820 | 4 |
| malba:18 | mřížka vzoru **0.32 m** | čtyřlisty | ruční | 4 |
| malba:21–23 | okvětí 0.16 + 0.12; střed 0.05; diagonála 0.012 | – | – | 4 |
| malba:24 | opotřebení šum uv·0.3, 0.35–0.6 | – | – | 4 |
| malba:29 | ROUGHNESS 0.9 | – | – | 4 |
| sklo:11 | terčíky **0.085** UV | – | svet.gd:826 (terce) | 4 |
| sklo:16–17 | kosočtverce **0.12** UV | – | – | 4 |
| sklo:21 | sklo (0.55, 0.62, 0.42)…(0.32, 0.38, 0.22), olovo (0.05) | – | – | 4 |
| sklo:23–25 | METALLIC 0.8·olovo, ROUGHNESS 0.12–0.5, ALPHA 0.45–1 | – | – | 4 |
| postava_hlava:7 | rez = 1.45 m | pod krkem nic | lide.gd:75 | – |
| postava_hlava:19 | ROUGHNESS 0.7 | – | – | 4 |

---

## Ručně kreslené věci (souřadnice v shaderu místo dat)

| soubor:řádek | co | ruční čísla |
|---|---|---|
| zem:111–113 | obdélník nádvoří tvrze (hlína) | x −27.6…18.5, z −16.6…17.4, pás u zdi 1,5–3,2 m |
| zem:128–149 | stará rovná náves – koleje, hřbet, zarůstání | střed `ves` (470, 830), osa VES_AU, u −97…57, osa 2.5·sin(u/23) + 1.2·sin(u/9+1), pás 6 m. **Pořád zapnutá** (ves_rovna se nastaví jen při TRZISTE) |
| zem:114–118 | tržiště (obdélník podél cesty) | TRZ_O/TRZ_U/TRZ_R ze svet.gd, ale vypnuté (TRZISTE=false) – výchozí hodnoty kreslí malou plochu u (0, 0) |
| zem:176–177 | kamenité úseky cesty | sinusy s·0.021 + 7.7 (×2.31, ×5.13) – kopie vzorce svet.cesta_useky |
| zem:269–274 | lesy za okrajem mapy | šum 0.0021/0.011, práh 0.44–0.56, R/G 0.35/0.65 |
| zem:229–260 | hony a lány | HON 125 m, lány 9–18 m, 4 plodiny podle hashe (kopie blender/kraj.py hon()) |
| zem:364 | okraj udusané plochy lomu | 27.5 m + 1.8/1.2/0.8·sin – kopie svet.lom_okraj |
| zem:369–370 | koleje v lomu | 55 % šířky lom_rect, rozchod 1,4 m |
| zem:384 | „u tvrze“ (bez skály) | obdélník abs(x+4) < 80, abs(z) < 75 |
| zem:385 | bez pískovce ve vsi | 140 m od `ves` |
| svet.gd:777 | lom_rect (data, ale x natvrdo) | x 100…180 |

## Duplicity a rozpory

1. **Od kdy jen barva krajiny / detail terénu:** zem 70→100 m (`zem:489`, komentář KCD 100 m); stebla výchozí 40→80 m (`stebla:42–43`), skutečně louka.gd:150: trs a vysoká 40–80, drn 20–40, vějíř 30–70, kupa 0–1; `pravidla_sveta.json` use_terrain_color_m = 80 / 40 („od této vzdálenosti“), kdežto shader na 80 m už končí přechod (začíná na 40). louka.gd čísla píše natvrdo, z JSON je nečte.
2. **Další přechody bez společného pravidla:** louka blízká→dálková 40–140 m (`zem:212`); zrno 15–45 m (`zem:215`, komentář říká „od 25 m“); tmavá pata trsu 30–40 m (`stebla:154`); hustota trsů 20→130 m výchozí / 80 tablet / 110 PC (`stebla:33`, louka.gd:128; komentář `stebla:19` „k 130 m nic“ neplatí); květy 12→45 m (`kvety:12–13`); detail skály 25–60 m (`skala_detail:28`); parallax zdivo 12–25 m vs. textura 10–22 m; zákal vody do 60 m (`voda:140`); rekа lod0 50 m.
3. **Náběh/mizení:** stebla náběh +12 m a mizení 14 m (`stebla:16, 101`), květy mizení 10 m (`kvety:39`), impostor náběh +10 m a mizení 60 m (`impostor:46`). Impostor výchozí fade_od 50 („plný strom končí na 60 m“), ale svet.gd:3456 dává STROM_PREP − 10 = 30 m na tabletu / 50 m na PC.
4. **Měřítko hlíny:** uniform `hlina_m` = 2.17 (`zem:31`), svet.gd:795 nastaví 2.0 (pesina), ale shader ho **nepoužívá** – všude natvrdo `p / 2.0` (`zem:120, 122, 166, 168, 190`), plus p/3 a p/20 pro dlaždice 1 a 3. Bahno p/2.0 (`zem:327`), oblázky p/1.6 (`zem:333, 367`), lesní půdy pudy_m 2.2 (mech 1.69 m), rula 2.6 m, pískovec v zemi 2.4 m + 7.3 m (`zem:431–434`), ale skala_detail použije skutečnou velikost fotky 1.83 m (`detail_m`). Stejná fotka pískovce má tedy na skalní věži 1,83 m a na stěně terénu 2,4 m.
5. **barva_louky / barva_lesa:** výchozí v zem i stebla (0.08, 0.10, 0.02) / (0.040, 0.070, 0.024) ≠ svet.gd:7–8 BARVA_LOUKY (0.145, 0.235, 0.02) / BARVA_LESA (0.062, 0.095, 0.015). Za běhu se přepíšou (stebla kopírují ze zem), výchozí čísla v shaderech jsou zastaralá.
6. **stan_rect** výchozí (−250, −250, 1152, 1602) je ve dvou shaderech; skutečný se počítá z data.trava_kraj.
7. **ves_rovna zůstává true:** svet.gd:785 nastavuje `ves_rovna = not VES_OBLOUK` jen uvnitř `if TRZISTE:` a TRZISTE = false (svet.gd:8995). Ves je ve výchozím stavu v oblouku (VES_OBLOUK = true, svet.gd:36), ale shader dál kreslí koleje staré rovné návsi z ručního vzorce (`zem:130`) všude, kde není cesta z dat (rd < 0,01).
8. **Tržiště s výchozími hodnotami:** trziste = (0,0,1,0), trziste_r = (0,−1,0,−1) → kolem bodu (0, 0) asi 1,5 m snížená tráva (gm × ~0,75). Leží uvnitř nádvoří, takže není vidět, ale je to zbytek.
9. **„U tvrze“ a „ve vsi“ jinak než ve svet.gd:** zem:384 obdélník abs(x+4) < 80, abs(z) < 75; svet.gd:2023 kruh o poloměru 80 m kolem (−4, 0). Ves: zem:385 140 m od (470, 830); svet.gd:2023 130 m; main.gd:1248 150/135 m. Střed `ves` (470, 830) se do shaderu nepředává, je jen výchozí hodnota.
10. **Osa návsi dvakrát:** VES_AU (0.76193, 0.64764) v `zem:55` vs. VES_D (0.7620, 0.6476) svet.gd:7365. Stejné číslo, jinak zaokrouhlené.
11. **Rozchod kolejí 1,4 m** je ve třech místech zvlášť: náves 2·0.7 (`zem:137`), lom 2·0.7 (`zem:370`), cesta z dat (CUSTOM1.z, svet.gd).
12. **Barevný posun hlíny** (1.06, 1.0, 0.91) dvakrát (`zem:120` a `zem:189`); hlina_k = 0.64 se nastavuje dvakrát (svet.gd:767 a :7280).
13. **Mrtvé parametry:** `je_cesta` (svet.gd:7274) v zem.gdshader neexistuje. `_cesty_material` duplikuje zem se stejnými hlina_a/n/k, takže nic nemění. `kopyta = 0.0` (`zem:174`), pudy vrstva 0 a `pudy_k[0]` se nepoužívají, `fw = wn2` (`zem:344`) je zbytek. V reka jsou nepoužité albedo_color/albedo_depth/transparency_*/edge_fade, v kvety fade_od.
14. **reka i_lod0_distance:** `VERTEX.z < 50` (`reka:211`). Ve view space je VERTEX.z před kamerou záporné, takže podmínka platí vždy a druhá vrstva normál se kreslí v libovolné vzdálenosti. Je to chyba převzatá z Waterways.
15. **Vítr:** stebla a kvety mají směr natvrdo (x sin, z cos·0.6; TIME·1.6, fáze 0.21/0.17), listi `vitr_smer` (0.8, 0.6), TIME·0.9, fáze 0.13/0.11, voda `vitr` (0.8, 0.6). Listi a voda svůj směr nikdo nenastavuje a stebla se směrem (0.8, 0.6) nesouhlasí, takže tráva a koruny se nehýbou stejným směrem.
16. **Drsnost/specular kamene:** zem skála SPECULAR 0.5 − 0.35 = 0.15, ROUGHNESS 0.95; skala_detail 0.92 / 0.3; zdivo z textury / 0.3; textura 0.35. Země 0.5 je výchozí specular Godotu. Tráva/listí/impostor/květy drsnost 0.9 / 0.85 / 0.9 / 0.9, malba 0.9, postava 0.7.
17. **Kalibrace pískovce:** skala_detail detail_prumer výchozí 0.3 vs. svet.gd fallback 0.2.
18. **Voda:** výchozí deep/zakal/kalnost v shaderu se liší od svet.gd (rybník/příkop (0.08, 0.115, 0.08), zakal (0.13, 0.16, 0.10) u nádrží vs. (0.13, 0.16, 0.11) u druhé větve svet.gd:845). U reka se melka/hluboka v shaderu (#5A6B3A/#1E2A1C) liší od svet.gd (0.24, 0.27, 0.15)/(0.06, 0.08, 0.05).
19. **MSAA:** stebla mají `alpha_to_coverage_and_one` („alfa jako pokrytí MSAA“, `stebla:6–8`), ale pravidlo pro tablet je nikdy MSAA. Bez MSAA se to chová jako obyčejné nůžky. Komentář ve voda:9 zmiňuje „Compatibility + MSAA 4x“ jako dřívější stav.
20. **Šum stejných frekvencí** se opakuje: p·0.03 a mk (p·0.022 / 0.05) v zem i barva_krajiny (záměrně stejné). Bayer a práh trsu fract(g·13.71 + 0.37) jsou v stebla i kvety. Hash fract(sin(dot(…, (12.9898, 78.233)))·43758.5453) je v listi, impostor a zem (lom).
21. **Počet vzorkovačů:** zem.gdshader je u limitu Adrena (13, komentář `zem:52`), každá nová textura v zemi tak musí nahradit jinou.
