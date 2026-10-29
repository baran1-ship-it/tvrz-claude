# Soupis čísel a pravidel světa (rádce 27. 10. 10:05 krok 1, 10:10 logika)

Podklad pro návrh čtyř tabulek (1 ZASAZENÍ, 2 POVRCHY, 3 TŘÍDY, 4 MATERIÁLY). Je to jen soupis, kód se neměnil.

Ke každé položce je uvedeno:
- soubor a řádek,
- hodnota,
- význam,
- kdo ji používá,
- do které tabulky patří (1–4).

Čísla řádků platí ke commitu, v němž soupis vznikl.

## Díly soupisu

| díl | rozsah | řádků tabulek |
|---|---|---|
| [svet_a.md](soupis/svet_a.md) | `scripts/svet.gd` ř. 1–3607 | ~236 |
| [svet_b.md](soupis/svet_b.md) | `scripts/svet.gd` ř. 3600–7225 | ~285 |
| [svet_c.md](soupis/svet_c.md) | `scripts/svet.gd` ř. 7160–konec, **pořadí stavby dnes** | ~304 |
| [skripty.md](soupis/skripty.md) | ostatní skripty (louka, main, daylight, predmety, voda, nadrz, koryto, lide, ruchy, mapa, …) a co kód čte z `pravidla/*.json` | ~400 |
| [shadery.md](soupis/shadery.md) | všechny shadery, masky (COLOR, CUSTOM, UV2), měřítka v metrech, vzdálenosti od kamery, ruční souřadnice | ~380 |
| [blender.md](soupis/blender.md) | generátory v `blender/` (kraj, vesnice, fort, hostinec, …), fototextury, rozlišení, **druhá pravda** Blender × Godot | ~350 |
| [logika.md](soupis/logika.md) | **kde svět porušuje logiku fyzického světa** (20 nálezů, změřeno z dat a logů) | 20 |

Každý díl končí sekcí „Duplicity a rozpory“.

## Nejdůležitější zjištění

### A. Tabulky v `pravidla/` kód skoro nečte
- **`pravidla_sveta.json`:**
  - Čte se jen `pasma` (cesta, skupiny, budova.kmen_od_zdi_m). Doplnil ji stavitel dnes v 10:30 před pokynem 10:05.
  - Nečte se `druhy` (36 druhů), `stanoviste`, `vyplnovy_druh` ani `vyplnovy_mix`. Kód na ně odkazuje jen komentáři.
  - Kód se s tabulkou rozešel: louka má kosený mix vějíř 0,48 a byliny 0,22, JSON 0,6 a 0,1.
- **`pravidla_modelu.json`:**
  - Čte se jen `nacitani` (dosah rostlin, rozpočty plánovače).
  - Nečtou se `tridy` ani `rozpocet`.
  - Kolize (`kolize_bunka_m` 32, `kolize_davka_tvaru` …) jsou v JSON, ale kód má vlastní `KOL_BUNKA` a `KOL_DAVKA`.

### B. Stejná věc zadaná na mnoha místech různými čísly
- **Obrys tvrze a nádvoří:** asi 8 ručních obdélníků (svet, louka, life, ruchy, main, zem.gdshader), liší se až o 1,5 m. Střed tvrze je jednou (−4, 0), jindy (−4,5; 0,4).
- **„Ve vsi“:** střed (470, 830) je střed **staré** rovné návsi. Poloměry 110 / 130 / 135 / 140 / 150 m jsou v 6 souborech. lide.gd vede vesničany po staré ose, rybníček v nadrz/ruchy zůstal na staré ose.
- **Odstup rostlin od cest a pěšin:** asi 10 různých čísel (0,6–8 m) v rozsevech, jednou měřených od osy, jindy od kraje hlíny. K tomu `pasma`, vlastní vzorec v `_cesty_kere` (1,3·hw + 1,2) a pás krytí (1,3·hw + 0,5).
- **Hranice světa:** main.gd −215…860 × −215…1290, player.gd a mapa.gd −240…890 × −240…1340.
- **Profil cesty:**
  - výška: komentář říká terén + 2 cm, kód `cesta_d` dává +6 cm a hrboly;
  - koleje: tři komentáře udávají tři hloubky;
  - zářez a násyp: komentář 5 m, kód ±3 m;
  - přechod do okolí: komentář 8 m, kód 12 m.
- **Dosahy kreslení bez společného pravidla:**
  - terén má jen barvu krajiny od 70–100 m;
  - trsy: v kódu 40–80 m, v JSON „od 80 m“, dohled trsů 80 / 110 / 130 m na třech místech;
  - impostor: shader od 50 m, kód 30 m;
  - `STROM_DOHLED` 120 m je konec tvaru stromu, ne stromů (impostory jdou do 900 m);
  - stíny: daylight 4 kaskády na 110 m, main je přepíše na 40 / 60 / 80 m.
- **Zapuštění paty rostlin:** liší se skoro u každého druhu (−0,02 až −0,8 m), práh „visí“ je všude 0,25 m.

### C. Pořadí stavby dnes porušuje „pozdější krok nehýbe dřívějším“ (podrobně svet_c.md)
- Keře u cest, kamínky na cestách a kompozice vsi se sázejí **až po** `_na_povrch`, `_pesiny_volne` a `_kmeny`. Tyto kontroly se jich netýkají: keře u rybníka visí a stromy z kompozice nemají kolizi kmene.
- `_cesty_rostliny` posouvá výšku rostlin podle profilu cesty až po `_na_zem`.
- **Mazání proti sázení:**
  - vrbu hlavatou sázejí tři kroky a v ř. 10262 se smaže celá, pak ji kompozice vsi přidá zpátky;
  - šípek sázejí tři kroky a pak se smaže.
- **Mrtvé druhy:** `grass_medium_02` a `dandelion_01` se nekreslí. Asi 60 % porostu u paty hradeb a část zeleně u zdí ve vsi je neviditelná.
- Maska stanoviště podle komentáře vzniká „po všech úpravách“, ve skutečnosti uprostřed rozsevů. Stromy z pozdějších kroků v ní chybí.

### D. Blender = druhá pravda (podrobně blender.md)
- **Cesty:** Godot skládá osy cest zpětně z barvy pásu `Teren_cesta` a šířku počítá jinak. Blenderský pás pak skryje a přidá cesty, které Blender nezná.
- **Ves:** natvrdo v Godotu, `VES_STARE` je ručně opsaná poloha a rozměry 7 chalup (krčma chybí). Změna seedu ve vesnice.py to rozejde.
- **Maska pole:** počítá se podle **staré** vsi. Kolem nových domů k = 0, 1, 6, 7 zůstává pole až ke zdi (domněnka, ověřit snímkem). Pole pokrývá i celý lom.
- **Hony a lány:** zapsané dvakrát, v `kraj.py` i v `zem.gdshader`.
- **Materiály:** bump, rough_add, dirt_low a moss z Blenderu se do hry nepřenášejí.
- **Chybějící podklady:** `tex_cache/meta_2k.json` se skutečnými rozměry fotek v repu není, bez něj nejde ověřit měřítko vzoru (tabulka 4). Fotka `sindel` v seznamu `ASSETS` chybí.

### E. Shadery kreslí z ručních souřadnic místo z dat (podrobně shadery.md)
- Stará rovná náves se **pořád kreslí**. `ves_rovna` se nastavuje jen uvnitř `if TRZISTE:` (svet.gd:785) a TRZISTE je false.
- `hlina_m` shader nečte, hlína je natvrdo `p / 2.0`. Parametr `je_cesta` v shaderu neexistuje.
- Ruční obdélníky v shaderu: nádvoří, tržiště, „u tvrze“ 80×75, „ve vsi“ 140 m, okraj lomu (kopie `lom_okraj`), hony.
- Vítr: směr natvrdo, u trávy jiný než u listí a vody.
- Řeka: podmínka `VERTEX.z < 50` platí vždy.
- Zem je u limitu 13 vzorkovačů (Adreno), nová textura musí jinou nahradit.

### F. Porušení stálých pravidel (CLAUDE.md)
- **MSAA:** main.gd:97–98 zapne MSAA 2× od startu na Vulkanu, tedy i na tabletu. Nastavení kvality ho pak vypne.
- **Primitiva:** pohyb.gd kreslí řetěz jako TorusMesh a lana jako CylinderMesh.
- **Stebla:** `alpha_to_coverage_and_one` počítá s MSAA, které tablet nemá.
- **Mrtvý kód:** trava.gd, mesh_batch.gd, props.gd, fort.gd, palace.gd a `_ves_grass` (za `return`) nikdo nevolá.

## Logika fyzického světa: nejzávažnější (celé v [logika.md](soupis/logika.md))

| # | pravidlo | co je dnes | závažnost |
|---|---|---|---|
| 1 | voda teče z kopce | potok teče **obráceně**: směr toku se bere podle nižšího konce osy, ten je ale u pramene. Na jihu hladina stoupá o 39 m na 220 m | vysoká |
| 2 | potok má spád, mlýn u spádu | hladina rovná na 1536 m z 1935 m. 515 m teče v zářezu až 22 m hlubokém (kaňon). Mlýn ve světě není | vysoká |
| 3 | rybník: přítok výš, hráz s odtokem níž | rybník Lhota (525, 879) nemá hráz, stavidlo, přítok ani odtok. Terén klesá na Z, kde by patřila hráz | vysoká |
| 4 | vozová cesta ≤ 1:8, ne kolmo do svahu | hlavní cesta před hostincem 64 % kolmo do svahu. 41 % délky hlavní cesty je prudší než 12,5 %. Vyrovnání profilu narazilo na strop ±3 m | vysoká |
| 5 | najíždění na most | odbočka tvrz–ves u mostu 32–35 %, cesta spadne do zářezu a pak se zvedne na most | vysoká |
| 6 | brod tam, kde je koryto široké a mělké | cesta z lomu (vozy s kamenem) sjíždí k brodu (210, 853) 33 % do strže 7–8 m hluboké | vysoká |
| 7 | pole na mírných svazích | 65 % lánů je prudších než 12 %, 38 % prudších než 20 %. `field_strip` sklon nebere v úvahu | vysoká |
| 8 | les na strmém a na severu | `forest()` sklon nebere v úvahu, rovina je ze 30 % pod lesem a strmé svahy ze 43 % bez lesa | střední |
| 9–12 | ulice, pěšiny, hostinec | ulice vsi u vjezdu napříč svahem 16–39 %. PESINY 3 vede skrz dům k = 4 a končí na louce. PESINY 2 končí 32 m od hostince ve svahu 73 %. Hostinec pro vozy na plošině ve svahu 19 m | střední |
| 13–14 | kameny v poli na mezích | 39 kamenů a 11 balvanů uprostřed lánů z Blenderu, odhadem ~130 balvanů z rozsevu hry na strmých lánech (domněnka) | nízká / střední |
| 15–16 | pole za humny, lom udusaný | maska pole ze staré vsi až ke zdem nových domů a přes celý lom (domněnka) | střední / nízká |

Bez nálezu: ves leží v kotlině (ne na vrcholu), lom je zaříznutý do svahu správně. Co nejde ověřit bez hry a snímků, je na konci logika.md.

## Co z toho plyne pro tabulky (podklad pro rádce, ne návrh)
- **Tabulka 1 (zasazení):**
  - obrysy tvrze, vsi, lomu a rybníka jako **záznamy lokací** (jeden obrys, ne 8 obdélníků);
  - odstupy od osy i od kraje sjednotit na jedno měřítko (od kraje hlíny);
  - pořadí stavby: vegetace celá před `_na_povrch` a `_kmeny`;
  - mazání druhů nahradit stanovištěm (druh se nesází, kde nemá být).
- **Tabulka 2 (povrchy):** masky COLOR.r/g/b/a a CUSTOM0/1 popsané v shadery.md a blender.md. Maska pole a hony jsou dvakrát.
- **Tabulka 3 (třídy):** dosahy kreslení, stínů, trsů, impostorů a kolizí jsou dnes rozeseté po main, svet, louka, daylight a shaderech. `pravidla_modelu.json tridy` se nečte.
- **Tabulka 4 (materiály):** měřítka fotek v metrech jsou v shadery.md a blender.md. Chybí meta rozměrů fotek (`tex_cache/meta_2k.json`).
- **Logika:** potok (směr a spád), rybník (hráz, přítok, odtok), sklony vozových cest (hlavní, odbočka, lom) a pole na strmém jsou chyby **dat lokací a generátoru krajiny**, ne zasazení. Patří do záznamů a do generátoru, ne do výjimek.
