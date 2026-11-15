# Puchart 1393 – zakázka modelů (15. 11. 2026)

Formát jako krčma, hájovna a kostel: glb + `_lod1.glb`, 1 m = 1, Y nahoru, počátek na terénu/podlaze,
kolize `-convcolonly` (pochozí plochy `-colonly`), mech/saze/vlhko v barvě vrcholů COLOR_0, `NAVOD_*.md`
s rozměry, značkami a materiály, náhledy. Tablet: podrobný do ~30–40 tis. troj. (drobné díly do 15 tis.),
textury 1k (výjimečně 2k), max 2–3 materiály na díl. Předloha vzhledu: KCD1/KCD2, Morava kolem 1400.
Plamen a kouř dělá hra – do modelu jen polena, uhlíky, popel a značky.

## 1) Sklep pod krčmou (do modelu krcma_L)
Pod komorou v rohu x 4,98…5,82, z −3,03…−2,16 (dnes poklop na hliněné podlaze y 0,45).
Poklop jako SAMOSTATNÝ uzel s pantem (pivot v ose pantu, otevírá se nahoru ~100°), pod ním otvor v podlaze
a strmé dřevěné schody (nebo žebřík) dolů; sklep ~3×4 m, výška ~2,1 m, lomový kámen, valená klenba nebo
trámový strop, hliněná podlaha, výklenek ve zdi, prázdný. Kolize podlahy krčmy s otvorem, schodů a sklepa.
Značky: Sklep_Poklop_Pant, Sklep_Dole, Sklep_Svetlo.

## 2) Uhlířské pracoviště (mýtina ~15×15 m)
Milíř ve 3 stavech (samostatné díly): a) postavený (kupa polen Ø ~4 m, 2 m, drn/hlína), b) hořící
(průduchy – značky Milir_Kour_N), c) rozebraný (kruh uhlí a popela, ohořelá polena); kuželová uhlířská
chýše (kůly, kůra/drn, vchod, uvnitř lůžko z chvojí a ohniště), hromada dřeva, dřevěné hrábě a lopata,
vozík na uhlí.

## 3) Smolárna / dehtárna
Jáma nebo hliněná pec na pálení smoly (nádoba v jámě překrytá hlínou, žlábek), hromada smolných
pařezů/třísek, malý přístřešek.

## 4) Studánka s roubenkou pod skálou
Kamenná obruba pramene, nízká roubená stříška (šindel), dřevěný žlábek, odtok do potůčku, šachta ~0,6 m.

## 5) Kříže a boží muka
a) kamenný smírčí kříž (~0,9 m, zvětralý, zapuštěný, mech), b) dřevěný kříž na rozcestí (~2,5 m,
zvětralý dub, příčka na plát s kolíkem, stříška), c) dřevěná boží muka (sloup se šindelovou stříškou
a výklenkem).

## 6) Krby (hezké dobové podle KCD, ne „ze skriptu“)
Počátek = střed přední hrany ohniště na podlaze, +Z do místnosti; prázdný uzel `<Model>_Krb_Ohen`
na ohništi; kolize `-colonly`; vnitřní sítě se slovem `Vnitrek`; do 15 tis. troj., max 3 materiály.
| Krb | Místo (souřadnice) | Volný prostor š × h × v | Kouř |
|---|---|---|---|
| Hrad A – síň 1. patra (`HradA_Krb_Ohen1`) | střed přední hrany (−8,68; 42,60; −1,36), yaw 98°, zeď hradby bez oken | 1,6 × 0,9 × 3,26 | komín v tloušťce hradby 1,1 m, ústí nad korunou |
| Hrad B – síň 1. patra (`HradB_Krb_Ohen1`) | východní čelo mezi okny, (57,32; 14,63; 146,25), yaw −90° | 1,8 × 0,9 × 3,9 | komín ve východním čele přes 2. patro nad střechu |
| Rychta – jizba (krb_rychta.glb) | na příčce jizba/síň vpravo od dveří jizby, (1,55; 0,30; −0,45) v souř. modelu Rychty, yaw 0 | 3,2 × 1,05 × 2,29 (krb š 1,8–2,0) | komín: otvor v záklopu 2,59–2,64, střecha nad x 1,55 y ~6,0, hřeben 8,23, vrchol komína ≥ 8,6 |
Hradní krb: kamenné ostění s konzolami, římsa, plášť do průduchu ve zdi, kozlíky, polena, osmahlá zadní stěna.
Krb Rychty: menší, lomový kámen a hlína, překlad, plášť z omítnutého proutí/hlíny, komín přes střechu.

## 7) Pece a kamna
Značky: `Pec_Usti` (střed spodní hrany ústí, +Z ven), `Pec_Kour`. Chalupy jsou kouřové jizby bez komína.
| Pec | Místo (souřadnice modelu domy.glb: x napříč, z podél, y od terénu) | Volno š × h × v |
|---|---|---|
| Dum1 – jizba | těleso x −3,36…−1,88, z 0,85…2,76; ústí (−2,62; 0,94; 2,22) čelem +z; podlaha 0,30, záklop 2,59 | 1,6 × 2,1 × 2,29 |
| Dum2 – jizba | těleso x −2,86…−1,65, z 1,04…2,95; ústí (−2,255; 0,89; 2,41) +z; podlaha 0,25, záklop 2,54 | 1,4 × 2,1 × 2,29 |
| Rychta – jizba | těleso x −3,65…−2,35, z −0,41…1,50; ústí (−3,00; 0,94; 0,97) +z; podlaha 0,30, záklop 2,59 | 1,5 × 2,1 × 2,29 |
| Krčma – pec šenkovny | kolize x −2,75…−1,10, y 0,45…2,05, z −3,90…−1,15 | obal |
| Krčma – pec jizby | x 2,20…3,55, z −0,40…0,95 | obal |
| Hájovna – pec | x −0,95…0,50, z −2,90…−1,15 | – |
| Hrad A – kachlová kamna (světnice 1. p.) | střed (−7,60; 42,60; 0,96), sokl 1,4 × 1,4, výška 2,22, topeniště ze síně (−7,75; 42,60; −0,13) | – |
| Hrad A – ohniště černé kuchyně | 2,2 × 1,6 × 0,5, střed (−4,98; 39,10; 3,42), dýmník-jehlan 2,6 × 2,6 od y 41,1 | – |
Chalupní pec: hliněná klenutá pec na kamenné podezdívce, ústí s čelem, plotna/předpecí s hrncem
a trojnožkou, začouzené okolí ústí a strop, lavice kolem, zápecí. Hradní kamna: kachle 14. st.
(miskové/nádobkové) v hliněném plášti. Ohniště černé kuchyně: vyvýšené kamenné, dýmník, trojnožka a kotel.
Snímky současného stavu: docs/screens/pec_stav_*.jpg.

## 8) Seno (předloha docs/reference/seno/kcd1_seno_staj_misa_15_11.jpg)
Fotorealistické suché luční seno, bledé slámově béžovo-šedé, matné; hustá spleť tenkých zvlněných stébel,
hrubé chomáče, rozpadlé okraje, tmavý stín uvnitř (AO v COLOR_0). Bez kolize.
a) do jeslí: délka 4,2 m, hloubka 0,6 m, spodek 1,3 m nad podlahou, kupa do ~2,2 m, stébla mezi příčkami
(po 0,14 m) ven; b) kupa na zemi ~2,5 × 1,8 × 1,2 m (+ vidle zvlášť); c) seno na půdu ~3 × 2 × 0,4–0,7 m
a rozházený chomáč 0,5 m. Do ~12 tis. troj. na díl, karty s alfou (alpha scissor), textury 1k, 1 materiál, LOD1.
