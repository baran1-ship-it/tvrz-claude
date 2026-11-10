# Předání – jediný vstup nového stavitele (20. 10. 2026, po vydání 0.58)

> **Stav 29. 10. večer (po 0.995, práce zastavena Míšou):** `docs/rozpracovane/stav_29_10_vecer.md` – co je vydáno, co zbývá, ves B (připravený patch), testy.


Projekt: Godot 4.4.1 hra „Odkaz Havrana“ (Čechy 1393: tvrz, ves, hostinec, skalní město; Android tablet Xiaomi Pad 8,
renderer Compatibility). Pracovní větev `claude/new-session-0dtk58`. **Repo je jediná paměť** – kontejner je dočasný.

## 1. Prostředí (nový kontejner, ~20 min)
```
bash tools/prostredi.sh        # Godot 4.4.1 + šablony Android, Blender 4.2 jako modul (/opt/bl/bin/python, bpy), Android SDK, pip, Waterways textury
bash tools/stahni_zdroje.sh    # herní data z balíků data/*.pck do modely/ a .godot/imported/ (jako je stahuje tablet)
bash tools/pregeneruj.sh       # textures/ + audio/ (procedurální – BEZ NICH APK nemá oheň ani zvuky), kryti.bin, potok, portály
python3 tools/vydani.py 0.NN   # vydání (jen na „VYDEJ“ od Míši)
```
**Po vydání vždy poslat Míše odkaz na APK ke zkopírování** (Míša 28. 10.: „zapamatuj si to“), v samostatném bloku kódu:
`https://github.com/baran1-ship-it/tvrz-claude/raw/claude/new-session-0dtk58/apk/OdkazHavrana-0.NN.apk`
Poznámky ke kontejneru: jeden běh Godotu ~4,5 GB RAM (kontejner 15 GB) → měřit/fotit po jednom. Na PC se pole textur půd
(`pudy_a` v zem.gdshader – listí, jehličí, oblázky, bahno, skála) kreslí bíle/žlutě (ETC2), na tabletu je v pořádku.
`godot --import` je bezpečný (soubory bez zdroje nechá).

## 2. Podpisový klíč (stejný navždy, od 0.55)
`tvrz_release.keystore`, alias `havran`, heslo jako v tools/vydani.py, SHA-256
`df68e8c320a8400576d37ba94229ed22cbb95db6785fca9e6721240872546065`. **Je u Míši na Google Disku** (do repa ho bezpečnostní
kontrola agenta nepustí). Nový kontejner: požádat Míšu o soubor → `/root/keys/tvrz_release.keystore`, ověřit `sha256sum`.
Bez něj nejde vydat aktualizaci přes nainstalovanou hru (nutná odinstalace = ztráta uložených her).

## 3. Zdroje dat
- **Hotová data** (vše, co hra potřebuje): balíky `data/*.pck.NNN` + `data_manifest.json` v repu → `tools/stahni_zdroje.sh`.
- **Zdrojové soubory** (jen když se mění model/textura): geometrie a rozmístění = `blender/*.py` (`blender/export_game.py` →
  modely/), fotky textur = Poly Haven / ambientCG (`blender/textures.py`, `pregeneruj.sh pudy`), rostliny a předměty z Poly
  Haven (`blender/predmety.py`), **Míšovy modely = Google Disk, složka „Modely“**
  (https://drive.google.com/drive/folders/1LIf8CIdMUVgmgOiszmP1E567PpmUbi-b), postavy = větev `assets` (quaternius/, modely/nove).
- Vydání v kontejneru bez zdrojových souborů: `vydani.py` balíky bez zdrojů nechá z minula (vypíše je); změněná data
  bez zdroje → opravný balík `python3 tools/vydani.py 0.NN --jen z_<nazev>` (hra ho načte poslední s přepisem, data.gd).
  Aktuálně v manifestu: `z_reka` (potok 0.55), `z_textury` (ETC2 bez horních mip úrovní, tools/textury_tablet.py +
  tools/pck_textury.gd; originály v build/ctex_zaloha jen v kontejneru).

## 4. Pravidla
- Komunikace s rádcem jen přes `docs/radce.md`: pull → přečíst od poslední sekce „RÁDCE → NOVÝ STAVITEL“ dolů + kapitoly,
  na které se odkazuje → práce → jeden krátký zápis na blok (čísla a příčiny) → commit, push.
- Kompasy: **Charakter krajiny** (17:00, Český ráj nahoře / Posázaví dole), **Jednotný vzhled** (18:50, pět pravidel povrchů),
  **Pravidlo řízení** (18:55: pravidla před opravami, celek před seznamem, audit existujícího), **Tráva a křoví** (07:30).
- Hospodaření (18:15): jeden hlavní + max. jeden agent, snímky jen 5 stálých míst (louka, hostinec, příkop, skály, potok),
  dotazy jen na rozhodnutí. Řešit příčiny, ne ladit čísla. Rozpočet u příčiny, **nikdy globální zředění trávy**.
- Tablet: ≤ 2,5 M troj. (vodítko, ne zeď – 18:30), ≤ 1500 kreslení, GPU < 700 MB, APK < 100 MB.
- Reálie 1393 (žádný štěrk ani cihly na venkově, smrk jen nahoře a v boru). Míšovy modely se nemažou, adaptují; cizí modely
  jen s licencí (CC0/CC-BY, autor do titulků). Vydání jen na výslovné „VYDEJ“, odkaz v bloku kódu:
  `https://github.com/baran1-ship-it/tvrz-claude/raw/claude/new-session-0dtk58/apk/OdkazHavrana-0.NN.apk`
- Commity končí řádky Co-Authored-By / Claude-Session (systémová připomínka).

## 5. Klíčové soubory
- `scripts/svet.gd` – stavba světa: koryto a nádrže (`_koryto_terenu`), usazení skal, `_na_zem`, `_stanoviste` (maska
  R jehl./G listn. korun/B skály/A pěšiny), `_krajina` (kameny, keře, výchozy, zářez potoka, příkop), `smi_tu_byt`, `_pudy`.
- `scripts/koryto.gd` (zářez údolí potoka: nárazový/vnitřní břeh, `strop`, `hrana`), `scripts/nadrz.gd` (rybník, příkop).
- `scripts/louka.gd` (louka ve vláknech, 4 vrstvy, drn 6/m², vysoká tráva v zářezu), `scripts/predmety.gd` + `scripts/portaly.gd`
  (místnosti s portály: hostinec, tvrz). `shaders/zem.gdshader` (terén, půdy, pěšiny `pes_lat`, cesta návsí, skála na strminách).
- Měření: `TVRZ_MERENI="jmeno;x,z,tx,tz;soubor.png"` (nebo `x,y,z,cx,cy,cz`), `TVRZ_ROZPAD=1`; testy `TVRZ_TEST=...` (dev_test.gd).
- Starší nástroje (mapa, UI, zvuky z nahrávek, snímky.py, testy) v `tools/stare/`.

## 6. Stav a další krok
- Vydáno **0.61**; **připraveno 0.62** (lidé, cesty, tráva pod vozem/na nádvoří, obzor, most) – vydat `vydani.py 0.62 --jen z_textury,z_postavy`.
- Pravidla z pádů 0.58–0.59 (radce.md): na tabletu **MSAA nikdy**, žádná kopie obrazovky v shaderech, změna kreslení = 3 min RAM na tabletu; při pádu nejdřív porovnat poslední dobrou a první špatnou verzi.
- Otevřené (radce.md hlášení 0.61): stromy plácačky (nové modely), příkop nedodělaný, dálka-obzor, terasy, cesty jako součin vlivů.
- Rozpočet a otevřené body: `docs/stav.md` (historie `docs/stav_historie.md`).

## Past: katalog předmětů v balíku svet (0.73)
`modely/predmety.json` (katalog) je v balíku `svet`, který se v kontejneru nepřestavuje (jen importy bez zdrojů). Nový předmět
(`blender/predmety.py build …`) má vlastní balík `p_<id>`, ale bez nového katalogu ho tablet nezná a nepoloží (0.71/0.72:
stany v lomu chyběly). Proto při každém novém předmětu vydávat s `--jen …,z_katalog,p_<id>` (opravný balík jen s katalogem).

## Zadání 0.76: nový návesní rybník Lhota (Míša 24. 10., schváleno)
Zdroj: Disk, `rybnik_lhota_v3.zip` (blender/rybnik_dil.py, balík z_rybnik) → `rybnik.glb` + `NAVOD.md`. Díl 60×60 m, hladina y=0, okraj dílu y=+0,30 m; terén tůně,
hladina, prací lávka, dlabanka, vrše, sušák, kameny, lekníny.
1. Odstranit současný návesní rybníček: hladinu, vyhloubení v `nadrz.gd` (větev kruh, POND) a rákos `_rybnik_breh` pro tento rybník.
2. Díl do středu bývalého rybníka (~525, 879); okraj y=+0,30 napojit na terén Lhoty, terén hry pod dílem snížit min. o 0,5 m.
3. `Rybnik_Teren-col`: material_override = materiál terénu (zem.gdshader – aktivní materiál, viz past 19:10); barva vrcholů
   R=0, G=tráva, B=0, A=1 louka / 0,5–1 bahno; UV a tangenty.
4. `Rybnik_Voda`: material_override = voda.gdshader, hloubka_vrcholu=true, okrehek=1 (barva vrcholů R*4 = hloubka).
5. Tráva (louka) i na díl podle G; rákos + orobinec (rakos_1/2, orobinec_1/2) v pásu 0,3 m ve vodě až 1,2 m na břehu,
   volné napajedlo a okolí lávky; vrby hlavaté/olše z modelů hry.
6. Kolize z přípon `-col` (terén, lávka, kameny, dlabanka). Screenshoty z lávky a přes hladinu do docs/screens.
Další v 0.76: lezení po žebřících (FUNKCE 1, radce 18:00).

## Pravidlo testování (Míša 25. 10.)
Testovat **jen lehce** – aby bylo jisté, že úpravy prošly (snímek opraveného místa + test, který se ho týká, minuty).
Celou sadu (hodina) ne po každé změně; zbytek testuje Míša na tabletu.

## Nečekat – pravidlo navždy (Míša 25. 10.)
Platí všude, viz `CLAUDE.md`: dlouhé běhy jen na pozadí přes `tools/beh.sh`, mezitím dělat další práci, žádné čekání naprázdno.

## Spouštění Godotu: jen `tools/beh.sh` (Míša 25. 10. „nastav si systém ať nemáš faily“)
Vše, co pouští Godot (testy, focení, vydání), jde přes `tools/beh.sh <jméno> foto|testy|cmd …`, na pozadí, a čeká se na oznámení.
- Zámek `/tmp/godot_beh.lock` bere jen beh.sh – nikdy ho neobalovat dalším `flock` ani `timeout` (0.80: vnější limit 900 s zabil focení, které potřebuje ~15 min).
- Limit je uvnitř (`BEH_LIMIT`, výchozí 2400 s; focení nejvýš 4 snímky). Na konci vždy jeden řádek `BEH <jméno>: OK | CHYBA | LIMIT`. U focení navíc kontrola, že snímky existují.
- Jeden test: `TVRZ_BODY="x,z;…" tools/beh.sh jm testy bod` (log Godotu `build/beh/jm_godot.log`); `bod` vypíše i všechny sítě nad bodem a jejich výšku – co zakrývá co.
- `beh.sh` před `foto`/`testy` prověří změněné skripty (`--check-only`, 2 s/soubor) – chyba typu `step()` v GDScriptu (jen shader) skončí hned.
- Zabíjet jen `pgrep -x godot` / `kill PID` – `pkill -f` i `pgrep -f vzor` najdou i vlastní shell (exit 144).
- Log je v `build/beh/<jméno>.log`. Když je zámek obsazený, `/tmp/godot_beh.kdo` říká kým.

## Pokládání objektů na terén (Míša 25. 10.) – tři skupiny
1. **Jeden bod** (sud, kámen, nářadí): nejnižší bod terénu pod celým půdorysem (hustý vzorek 5×5, `svet.pata_lom`), nic nevisí.
2. **Víc bodů s náklonem** (vůz, trakař, napajedlo, lavice venku): `svet.polozit_na_body` = place_on_points – výška pod
   KAŽDÝM opěrným bodem (kolo, noha, špalek), poloha = průměr zásahů, náklon (pitch + roll) z roviny bodů, yaw zůstává;
   záznam vybavení nese `"up"` (predmety.gd naklopí). Pohyblivý vůz později VehicleBody3D + VehicleWheel3D.
3. **Svislé s podezdívkou** (budovy, chýše, ploty, hradby): place_building – nikdy nenaklánět, jen yaw; podlaha 0,1 m nad
   NEJVYŠŠÍM bodem půdorysu (4 rohy + střed); svah větší než podezdívka = varování v logu → srovnat terén (`dum_teren`,
   plynule do 1,8 m, aby splynul s okolím – ne jen pod objektem) nebo budovu přesunout. Test `stavby_na_zemi`.
Svět se staví před fyzikou: místo raycastu výška z trojúhelníků terénní sítě (`vyska_lom`, `_chyse_na_sit`).
Když něco visí, smí se dosypat zem pod něj – ale s přechodem do okolí, ne hrbol jen pod objektem.

## Testy: dvě sady (rádce 17:50, Míša „2/3 času testy“)
Na PC je jen softwarové vykreslování (llvmpipe, snímek 1–3 s), takže každý test, který simuluje chůzi nebo měří čas
s renderem, trvá desítky minut a stejně nic neříká o tabletu.
- **Rychlé** – `bash tools/rychle_testy.sh "<testy>" [log]`: `godot --headless`, jen výpočet nad daty a fyzika bez
  renderu (stavby_na_zemi, lom_na_zemi, vratka, dvere_domu, lezeni, interier, stanoviste, briza, rybnik_ves…).
  Watchdog 5 min = CHYBA, ne čekání. Celá dávka ~2 min.
- **Tablet** – výkon, paměť, FPS, chůze s renderem, snímky měření: na PC nespouštět, testuje Míša na tabletu.
  Snímek z PC (`TVRZ_MERENI`) jen když je potřeba vidět opravené místo, max 2–3 pohledy.
- Cíl: cyklus oprava → test → vydání ≤ 15 min.

## Pravidlo: nejdřív rešerše, nic z hlavy (Míša 25. 10.)
Před každou novou technikou (cesty, voda, vegetace, stavby…) dohledat, jak to dělají KCD2 / CryEngine a jiné hry
a nástroje (dokumentace enginu, GDC, Polycount, 80.lv), a v radce.md napsat, z čeho řešení vychází.
Cesty 0.80: CryEngine road = spline nad terénem s height-blend okrajem; BeamNG road spline = podklad + vrstvy
opotřebení (koleje) + přechodové pásy, terén pod cestou zapuštěný; masky v barvě vrcholů potřebují hustou síť.

## Cesty – poučení 0.80 → 0.81 (Míša: „rozvalený beton s texturou cesty“)
Fotky KCD2 (17 ks, Míša 25. 10.): cesta je **součást terénu** – stejná výška jako okolí, žádná hrana; široká 4–8 m
(náves víc); okraj rozbitý, jazyky hlíny do trávy, u okraje nízká řídká tráva; povrch = mnoho jemných stop kol a kopyt
přes celou šíři, kamínky, světlá prašná hlína; koleje nejsou hlavní věc.
Chyba 0.79–0.80: pás cesty měl vlastní výšku (z osy Blender pásu) + zapuštěný terén + srážka okraje → deska nad/pod terénem.
Teď: `cesta_y` = původní terén (trojúhelníky `_ter_tri`) + 2–7 cm, ke kraji 0; terén se nezapouští; šířka ×1,1 (1,4–3,6 m půl),
náves 2,6–3,6; louka 2 m za okrajem (`cesta_kraj`) jen nízká tráva.
Past: cesta jen 2–7 cm nad terénem = z-fighting (šedé plochy přes cestu, 16/24bit hloubka) → terén pod sítí cesty o 30 cm
níž (ke kraji sítě 0), výška cesty z původního terénu. Hrubý pás Teren_cesta (kolize + dálka) přepočten na `cesta_y`. Past 2: `visibility_range` se měří ke středu AABB – síť přes celý kraj
(Teren_cesta) se kreslí i u nohou → viditelný pás 20 cm pod cestou, kolize zvlášť z meta `kolize_sit` (na výšce cesty). Past 3 (GDScript): `(dict[k] as PackedByteArray)[i] = v` píše do KOPIE (Packed* jsou hodnoty) –
psát `dict[k][i] = v`. Kvůli tomu nebyly cesty nikdy v kryti (v lese na nich tráva); log „osy cest v kryti 12/12“ to hlídá.

## Cesty 0.82 – barvy podle rozboru fotek (Míša: „jen šedá a hnědá, analyzuj fotky, najdi jiné zdroje“)
Rozbor 16 fotek KCD2 (výřez cesty): průměr ~125/108/88, R/G 1,16, B/G 0,80, sytost 0,31, světlá místa 2–2,5× tmavších.
Naše 0.81 (dry_ground_rocks): 182/157/124, rozptyl jen 1,4×, sytost textury 0,47 (do oranžova).
Výběr z 30 textur Poly Haven podle těchto čísel + pohledem: atlas `obrazky/cesta/cesta_atlas_a/n.jpg` 2×2:
forrest_sand_01 (prach, 2 m), dry_mud_field_001 (utlačená tmavá hlína: koleje, stopy, vlhká místa, 3 m),
rocky_trail (kamenité úseky, 2 m), aerial_ground_rock (velké skvrny, 20 m). Výšky stejných textur
`cesta_atlas_disp.png` (256 px/dlaždice) → geometrie povrchu (`cesta_disp`). Úseky (`cesta_useky`): koleje ~40 %,
výmoly s kalužemi, kamenité úseky. Dírа k hostinci: pás bez středního sloupce a řídké řádky (25 m) → osa z krajů + skok.

## 0.83 – hlášení Míši k 0.82 (tablet)
- Cesty „jak uhrabané, v rastru se táhnou čárky“: šum stop natažený podél cesty (sp*0,02 × lat*2,6) + jemný reliéf
  z výškové mapy v síti po 0,4 m podél = podélné rýhy. Pryč: stopy jen izotropní skvrny, reliéf z výšek zmenšených na
  8 px/dlaždici (~0,5 m hrboly). Pravidlo: nic nenatahovat podél osy; detail menší než rozteč sítě jen v normálové mapě.
- Žebřík „kliknu a hodí mě vedle“: start shora na t = 1,0 → _lez hned vystoupil na sestup. Start 0,96, výstup nahoře jen
  s páčkou nahoru. Test lezeni teď zkouší i klik shora bez páčky.
- Záhony: hlávky zelí na místech starých zahrádek (Blender) ležely v trávě vedle nových záhonů → s novými domy vypnuto.
- Cesta od padacího mostu začínala vedle mostu nad příkopem → osa až od z 33.

## 0.84 – hlášení k 0.83 („blízko, ale první část od tvrze zvláštní rastr, kolejiště to kazí“)
- Úsek od mostu a hlavní cesta se překrývaly (dvě sítě přes sebe = z-fighting a jiné skvrny) → osy se na koncích spojí v jednu.
- Koleje: 3–5 cm, měkký profil ~0,8 m, téměř bez tmavé textury (KCD2: mělké, široké, přerušované). Skvrny (vlhká místa,
  stopy) jen jemně (tm max 0,25). Pravidlo: na cestě nic tmavého a ostrého v pruzích.

## 0.84 – ves (hlášení Míši k 0.83)
- Domy na dohled: podrobný vnějšek do 130 m (dřív 60 m, dál hrubý obal = hnědá krabice).
- Hnědé stodoly: `_ves_site_vyrez` vynechal prázdné povrchy a override materiálů zůstaly na starých indexech → stodoly
  s holým exportním materiálem. Past: po přestavbě ArrayMesh vždy přenést override podle povrchu, ne podle indexu.
- Stodoly mají vrata: `_stodoly_vrata` vyřízne křídla (materiál dvere, shluky 0,25 m, 1,15–1,5 × 2,1–2,6 m, páry pantů
  2,6–3,1 m) jako Pohyb_stodola_*, zavřená, otevírají se ven, kolize křídla. GDScript: lambda kopíruje Packed pole – Array.
- Vrata a branky do dvorů „ze čtverečků“: drevo_plot = fotka 13 prken, s prohozeným UV napříč → `_prkna_tram` jako most.
- Rychta: trám nad schody do komory (M_RoubeniVnitrni, výška hlavy, bez kolize) pryč; terén u zdí jen dolů (příkop ve svahu).
- Záhony: hlína bez šumu „otesání“ (šachovnice na síti 8 cm) – blender/predmety.py, balíky p_zahon_*.
- Náves: terén pod cestou se snižuje jen pod plochou bez trávy (jinak tráva níž a cesta jako deska).

## 0.85 – hlášení k 0.84 (napojení, lemy, záhony)
- Cesty podle použití místa (Míša „každý kousek dle použití“): brod a břeh (do 9 m od vody) bahno + hlubší koleje
  (tvar sítě, o.x až 1,5, hloubka + 3 cm v bahně); zatáčky širší (+25 %); hostinec, brána, lom široká udusaná plocha (+90 %).
- `_cesty_napoj`: konec osy do 14 m od jiné osy se prodlouží do ní (+1,5 m), konec 13 cm pod povrchem – žádné slepé
  hranaté konce (lom × hlavní, ves × odbočka). Cesta od mostu začíná na konci pevného mostu (z 28,5).
- Pěšiny 4 a 6 (most, lom) se už nekreslí do textury terénu – byly druhou zvlněnou cestou vedle (vlnka ±8 m).
- „Lemy“ (rovný zelený pás bez trávy podél cest): za okrajem hlíny v pásu kryti 2 teď normální louka na výšce cesty.
- Zelený rastr u záhonů: buňky starých zahrádek blokovaly trávu → mezi novými záhony nízká sešlapaná tráva (`_nizka`),
  pod záhony nic (`v_nove_zahrade`).
- Kopec před hospodou 66 % (terén pod osou), břehy u brodu 34 %: `_cesty_profil` – klouzavý průměr 16 m, sklon ≤ 14 %
  (vpřed i vzad, průměr), zářez/násep ≤ 3 m s přechodem 8 m (úvoz), ke koncům os 0. Posune terén, výšku cesty (cesta_y dl)
  i mřížku `_vyska` (`_cesty_vys_mrizka`). Mřížka os `_cesty_mriz` s okrajem 12 m (přechod).
- Vrata stodol: prkna jsou samostatné díly → shluky přes společné vrcholy + dotyk obálek (+3 cm), ne buňky vrcholů.
- Keře podél cest (`_cesty_kere`): skupiny 1,5–4 m za okrajem, úseky ~35 % délky, každá strana jinak, ne ve vsi.

## 0.86 – záseky „na vteřinku“ (Míša)
Panel drží špičku jen 0,5 s → zásek > 300 ms se dřív na fotce skoro nikdy neobjevil. Teď řádek „záseky:“ (poslední 3:
délka, místo, skripty a nejdražší, fyzika, CPU kreslení, nové uzly, materiály, čas od startu) + zápis ZASEK do logu.
Rozpad říká příčinu: kreslení velké a materiály > 0 = sestavení shaderu (doplnit předehřátí), skripty = který systém,
nové uzly = stavba buněk. Na PC nejde změřit (llvmpipe 1–3 s/snímek).

## POVRCHY – tři třídy (rádce 15:20, závazné pro vše od teď; Míša „guláš, jen se záplatuje“)
- **A) TERÉN** = výšková mapa + `zem.gdshader` s vrstvami podle masky: louka, pole, les, dvůr, náves, **cesty a pěšiny**,
  břehy, dno brodu, plocha lomu, úvoz, suť. Tvar se **zapíše do výšky terénu** (profil cesty/koryta/terasy), síť terénu
  se zjemní jen tam, kde je profil. Vzhled = vrstva v `zem.gdshader` (atlas hlíny `cesta_atlas_a/n` pro všechnu ušlapanou
  zem). Tráva, rozsev, kolize i kryti čtou tutéž masku. **Žádná samostatná síť pro nic, po čem se chodí.**
- **B) DÍL** = model s vlastní hranou (rybník, stěna lomu, mlýn, tvrz, domy, most); terén A se k hraně **přitáhne**
  (přechod 3–5 m, bez schodu > 0,15 m). Uvnitř hrany platí díl, mimo ni A. Díl nikdy nepřekrývá A ve stejné výšce.
- **C) VODA** = hladina vždy nad A nebo dnem B (rybník, potok, náhon, lednice, **kaluž = voda v prohlubni A**, profil < −0,15).
- **Test `povrchy`** (místo visici / stavby_na_zemi / lom_na_zemi / nizka_trava): 1) žádná pochozí síť mimo A/B,
  2) obvod každého B bez schodu, 3) tráva/rozsev na výšce A nebo B, 4) jedna maska pro shader, louku i kolizi, 5) C nad A/B.
- Technika cest v A (0.89): trojúhelníky terénu u cest se rozdělí (krok ~0,7 m), výška = terén + `cesta_d` (profil,
  koleje, val, výmoly, vyrovnaný sklon); hrany k nerozděleným trojúhelníkům lineárně (bez trhlin). Údaje cesty jdou
  do vrcholů terénu jako `CUSTOM0` (lat/okraj, s, koleje, okraj) a `CUSTOM1` (tráva, bahno, kolej, příznak 7) –
  Compatibility je umí (ověřeno), žádný nový sampler (zem.gdshader má 13).

### Měření času snímku (K0, 26. 10.)
- `Performance.TIME_PHYSICS_PROCESS` / `TIME_PROCESS` jsou v 4.4 **maxima za poslední sekundu** (main.cpp, publikace 1× za s),
  fyzika = jeden krok, ne součet kroků. Pro zásek a testy nepoužívat – diag má razítka snímku (`physics_frame`,
  `process_frame`, konec diag `_process`) v `_sn` (fyzika, kroku, process, kreslení, celkem).
- `dt` v `_process` snímku N = délka snímku N−1 → příčinu brát z uzavřeného snímku, ne z hodnot aktuálního.
- Měřič nesmí v záseku číst RAM ani skládat celý log; zásek = řádek do kruhu, soubor ve vlákně max 2×/s.
- Cesty v terénu A: hledání osy jen v buňce 4 m, dělení 1 m → stavba 94 s → 18 s.

### Noční práce (Míša 27. 10.: „večer se domluvíme a ty se na to vykašleš“)
- Stavitel běží jen v tahu: když tah skončí a nic na pozadí neběží, nic ho neprobudí (přes den ho budila oznámení
  z dlouhých běhů na pozadí). **Před koncem tahu u dlouhé práce vždy naplánovat probuzení** (`send_later` po 30–60 min
  se stavem a dalším krokem), opakovat, dokud práce není hotová. Nikdy neslíbit „přes noc“ bez naplánovaného probuzení.

### Ulice vsi (Míša 27. 10.: „dálnice, břuch, rovná“)
- `vw` u os cest je **půlšířka** (hw), ne šířka – ulice měla 2,4–5,6 = až 11 m široká. Ves: hw 1,25–1,9.
- Osa ulice (ves_oblouk.gd `osa_ulice`) se klikatí podle domů (stočí se k vzdálenějšímu štítu), do půdorysů nevjede.
- Rovnost/klikatost ulice ověřit **snímkem shora**, z fotek ze země se to nepozná (Míša to z nich nepoznala).
- Vždy nejdřív nahlédnout do referencí (docs/screens/kcd1/ves_*.jpg), nic z hlavy.
- Focení: jeden snímek vsi ≈ 4 min (svět se staví znovu) → 6 snímků přes `BEH_LIMIT=1500` spadlo (obl5). Počítat 5 min/snímek.
- Cesta = terén (CUSTOM0/1 ve vrcholech, `_cesty_do_terenu`); `_cesty_site_stavba` a `_cesty_dal_kusy` se nevolají.
  Za 70–100 m kreslí zem.gdshader jen barvu krajiny (`far`) → cesty zdálky mizely (Míša 27. 10. ulice vsi). Opraveno
  výjimkou pro hlínu cesty (`rd * (1 - gm)`), jako u pěšin. Nejdřív zjistit, CO se kreslí (snímek bez louky
  TVRZ_LOUKA_VYP=0,1,2,3,4), pak opravovat – ne hádat.
- GDScript: `(dict[k] as PackedInt32Array).append(x)` slovník NEZMĚNÍ (Packed* = hodnota, kopie). Do slovníku Array.
  (ves_oblouk uprav_y: 0 bodů srovnáno, test ves_ulice to odhalil.)

### Pravidla z jednoho zdroje (krok A, 27. 10.)
- Lokace, cesty, voda a globální údaje jsou v `pravidla/svet/*.json`. Čte je Blender (`kraj.py` `_svet()`) i Godot (`scripts/pravidla.gd`).
- Nová hodnota světa jde do JSON, ne do kódu. Hra ji čte přes `Pravidla.cti(soubor, klíč…)`, takže test `pravidla_cteni` ví, co se čte.
- `pravidla.gd` je bez `class_name` a skripty ho načítají přes `const Pravidla := preload("res://scripts/pravidla.gd")`. `godot --check-only` nezná globální třídy, dokud editor neobnoví cache (Parse Error „Pravidla not declared“).
- Osy cest Godot už neskládá z barvy pásu `Teren_cesta`, bere je z `cesty.json`:
  - `pulsirka_m` je šířka před rozšířením u křižovatek a udusaných míst;
  - `hra_od_bodu` je místo, odkud hra osu kreslí.
- Osa potoka je v `voda.json` (dřív `modely/reka/osa.json`).
- Vydání se nečeká na doplňkové snímky (Míša 27. 10.: „nebudeme čekat na jednu fotku 20 minut“). Fotit jen to, co ověřuje změnu, a vydání pustit hned. Kamera ve foto režimu má y absolutně, u hostince (terén ~43 m) dát y nad terén.
- `build/z_textury.pck` je zdroj opravného balíku textur, `vydani.py --jen z_textury` ho čte. Při úklidu disku ho **nemazat** (27. 10. kvůli tomu spadlo vydání 0.96). Obnoví se spojením částí: `cat data/z_textury-<md5>.pck.000 .001 > build/z_textury.pck`.

### Export světa v kontejneru bez zdrojů (krok B, 27. 10.)
- GDScript: totéž platí pro lambdy – zachycené `Packed*` pole je kopie. Union-find a podobné věci psát bez lambd a s `Array` ve slovníku (0.97 kameny rybníka: první verze vracela 0 dílů).
- Kameny, prkna a jiné „díly“ z modelu: kolize = konvexní obal **každého souvislého kusu** (`svet._konvexni_dily`), nikdy jedna konkávní síť (Rybnik_Kameny 11 840 troj. = 30–40 ms fyziky na tabletu).
- `blender/export_game.py` v čistém kontejneru:
  - dveře hostince (`medieval_door_pack.glb`) – když balíček v `TVRZ_EXT` není, bere `hostinec.py` křídla z `blender/dvere_kridla.json` (vytažená z exportu 0.96); textury dveří z klonu `tvrz-modely-git/textury`;
  - textura `sindel` není na Poly Haven (ručně přidaná) – obnovena z `modely/textury/sindel_*` (Godot `get_image`) do `tex_cache` + `meta_2k.json`;
  - osa cesty musí mít body nejvýš po 6 m – most hledá `kraj._bridge` jako bod osy do 6 m od potoka (trasa z plánovače měla přes potok mezeru 26 m → `bridge() = None`).
- Výsledek exportu jde do opravného balíku `python3 tools/vydani.py 0.NN --jen …,z_svet` (tvrz.glb, svet.json, portaly.json); balík `svet` se v kontejneru nepřestaví.
  - modely `modely/nove/*.glb` bere `nove.py` z gitu (origin/main); jediný, který v gitu není, je `borovice` (Míšův `pine_tree.glb` na Disku, složka Modely) → stáhnout přes Google Drive `download_file_content` (výstup se uloží do souboru, base64 → `blender/tex_cache/nove/borovice.glb`);
  - `tex_cache/smrk_vetev.png` a karty listnáčů (`*_karta.png`, `briza_kura.png`) se generují: `/opt/bl/bin/python blender/trees.py` a `blender/listnace.py` (přes beh.sh cmd).
  - rostliny Poly Haven (`tex_cache/models`) se stahují `textures.fetch_models()`; dřív export chybějící model jen vypsal a pokračoval (0.97: ze `svet.json` tiše zmizelo 76 druhů, 34 000 kusů – chyceno porovnáním se zálohou, nevydáno). Teď `veg.load_library` skončí chybou. **Po každém exportu porovnat počty v `svet.json` se zálohou** (rostliny, kolize, vybavení).
- **Řetězení běhů za dlouhým exportem:** `beh.sh` čeká na zámek nejvýš 30 min, pak skončí „zamek obsazeny“. A `cmd … | tail && další` pustí další krok i po chybě, protože se bere výsledek `tail`. 0.97: testy běžely nad neimportovanými daty. Navazující kroky patří do **jednoho skriptu s `set -e` v jednom `beh.sh cmd`**, testy uvnitř přes `bash tools/rychle_testy.sh` (zámek už drží beh). Spustit až po oznámení, že export doběhl.

## 27. 10. večer – poučení
- **Blender bpy: odkaz na vrstvu dat po založení další vrstvy neplatí.** `uvl = me.uv_layers.new()` a pak `me.color_attributes.new()` → `uvl.data` ukazuje do uvolněné paměti, zápis tiše poškodí síť a pád (segfault) přijde až později (`normals_split_custom_set`, `validate`). Vrstvy založit všechny, pak odkazy vzít jménem. Stejně tak `poly.use_smooth` / `material_index` při iteraci (realokace atributů) – nastavit až po smyčce `foreach_set`.
- **Foto atlasu v Blenderu:** `scene.reset()` nastavuje AgX + kontrastní look → normály a barvy posunuté (listy černé). Pro data: view_transform Raw (normála) / Standard (barva), look None.
- **Úloha na pozadí bez `timeout` = 30 min** a pak ji harness zabije (po_d přišel o snímky). Dlouhé běhy vždy s `timeout` až 7200000.
- **`pkill -f` se vzorem, který je i v příkazu samotném, zabije vlastní shell** (znovu 27. 10.). Zabíjet podle PID z `ps`.
- **strom2.py** (jabloň/lípa/dub z fotek, ambientCG + Poly Haven): kvalita kupovaného modelu procedurálně nejde (Míša: kmen válec / „břicho“) → stromy od modeláře nebo stažené; strom2.py zůstává jako nástroj (atlas větviček z fotoskenů je použitelný).
- **Telo hrace (27. 10. noc):** `scripts/telo.gd`. Animace `modely/postavy/anim/UAL1.glb`, `UAL2.glb` vznikly z Disku (Postavy, „Universal Animation Library [Standard].zip“ a „… 2 …“, CC0, Quaternius) skriptem `tools/ual_anim_jen.py`, ktery nechava jen kostru a klipy (2,8 MB misto 7,6 MB). Stazeni: `curl -sL "https://drive.usercontent.google.com/download?id=<id>&export=download&confirm=t"` (id: UAL1 1vLumbwIQSTImVsr0ce5masfvYqZtZ-aa, UAL2 1u1LB5XRAtgjyh-ofv9f_rAIDC-tfd318). Do hry jdou balikem z_postavy (modely/ je mimo git).
- **Scratchpad: soubor `nt.py` zakryl modul Pythonu `nt`** (import os -> spustil se muj skript). Pomocne skripty nikdy nepojmenovavat jako moduly standardni knihovny (nt, os, json, time…).
- **`|| true` v bráně = žádná brána** (Astra 22:00): `tools/export.sh` polykal chybu exportu i testu po exportu, takže „prošly“ i rozbité běhy. Brána musí končit nenulovým kódem a zanechat stav (`build/export_stav.json`), který čte i balení (`tools/vydani.py` bez stavu OK a stejného md5 `svet.json` nebalí). Při psaní jakékoli kontroly: chybějící podklad = chyba, ne varování; neznámá hodnota = chyba, ne „přeskočit“.
- **Kontrola křížení podle průsečíku a ID**, ne podle vzdálenosti od začátku úseku. Přesná kontrola hned našla cestu od lomu 60 m korytem Bystřice (po rozšíření řeky 16:35 nikdo cesty nepřepočítal) → při změně šířky/osy vody vždy pustit test smyslu (`koryto`, `brod`).
- **Pořadí vegetace ve hře** (svet.gd, řetězec po `_uvnitr`): krok 0 katalog (druhy.json `pouzit`) → 6a stromy → 5+7 masky a kryt (`_stanoviste`, bez rozsevu) → 6b doplnění lesa (čte kryt) → vstup kroku 8 (`_vstup_druhu`, druhy.json `vyjma`) → 8 podrost (`_krajina` první) → 10 usazení, `_kmeny` naposled. Nový rozsev se zařadí do svého kroku a ptá se `druh_smi_hra`, nemaže se nic „na konci“.
- **Odpojená kolekce Vegetace** (zrychlení exportu): v ní jsou i sítě, které nejsou instance knihovny (`Rakos`) a patří do `tvrz.glb` – před odpojením se přelinkují do scény, jinak `select_set` spadne (export I 27. 10., rc 139; brána exportu to poprvé zachytila).
- **Šum masky povrchu ≥ 1,5–3 kroky sítě** (`kraj.sum_m`, `_KROK_SITE`) – pojistka proti aliasingu; zelený rastr ve vsi to podle měření NEBYLO (extrémy masky stejné před i po). Nejdřív měřit, pak tvrdit příčinu.
- **Blender export padal až při ukončení** (rc 139 po řádku „export hotov“) – proto kdysi `|| true`. Řešení: `os._exit(0)` po zápisu (`export_game.py`), brána pak pozná skutečnou chybu.
- **Importér Godotu odřízne `_Loop` z názvu klipu** (UAL `Idle_Loop` → `Idle`, nastaví smyčku). Kód hledal `Idle_Loop` → tělo v T-póze bez chyby. `telo.gd` jména vrací a hlásí chybějící klipy; u koně je v modelu překlep `1 Ilde`.
- **Úprava přes nahrazení textu smazala sousední řádek** (`telo.gd`: kontrola klipů vložená místo `_strom()` → tělo bez stromu animací, stálo v počátku). Po náhradě bloku vždy zkontrolovat, že volání kolem zůstala; `setup` teď bez stromu vrací chybu.

## Míša 28. 10. ráno (0.97 na tabletu) – příčiny, ať se neopakují (tabulka: docs/rozpracovane/misa_28_chyby.md)
- **Předpečená data musí nést otisk zdroje.** Starý balík z_reka (potok z Waterways) přežil přesun Bystřice; hra ho
  brala jen podle existence souboru → schovala vodu exportu, brod podle staré hladiny vykopal 4 m zářez přes lom.
  Teď `reka_otisk` (svet.json ↔ reka.json). Každý další předpečený soubor: otisk exportu, jinak se nepoužije.
- **Generátor geometrie musí mít rozlišení pro to, co kreslí.** Koryto 1–1,5 m v síti terénu po 5 m neexistuje
  (hladina zahrabaná). Jemný terén u všech toků (`toky_tvar.pas_jemny_m`).
- **Pořadí stavby i uvnitř výšky terénu:** tvar vody (`kraj.voda_tvar`) až po cestách a pláckách staveb
  (fort.land) – dřív ho plácky chalup a srovnání cest zasypaly.
- **Barvy vrcholů jsou data shaderu:** hladina bez barev proudu = R≈0,9 z exportu = celá pěna (bílé pásy).
  Test smyslu --po `hladina` a `koryto_toku` čtou výsledný glb.
- **Model z balíku = celá transformace uzlů**, ne `meshes[0].mesh` (houby obří). Sázení na zem jen zásahem u výšky
  terénu, ne první kolizí paprsku.
- **Kotvy ve světových souřadnicích se posouvají s dílem** (lano studny po posunu usedlosti vedlo přes cestu).
- Díl s vlastním modelem (mlýn): dveře pod uzel Tvrz (pohyb.gd hledá jen tam), doplňky modelu podle
  `vynechat_uzly`.
- **Disk kontejneru má pevný příděl** – hlídá ho `tools/beh.sh` (pod `beh_volno_mb` nic nespustí, pod `beh_kriticke_mb` za běhu zastaví) a export (rc 5/6).
  Neupravovat beh.sh, když běží (bash čte skript průběžně).
- Původně: (28. 10. plný: focení spadlo za 0 s, export jen tak tak prošel). Před exportem
  `df -h /`; mazat jen věci z kontejneru, které jdou vyrobit znovu: `build/ctex_zaloha` (originály textur z
  limity_textur, 1,4 GB), kopie APK a balíků v `build/`. Nikdy `data/`, `apk/`, `modely/`.
- **Čekání na jiný běh nikdy přes `pgrep -f <jméno skriptu>`** (28. 10.: čekací smyčka našla sama sebe – její vlastní
  příkaz obsahuje to jméno – a 40 min se nic nespustilo). Navazující kroky dát do jednoho skriptu za sebe; zámek beh.sh
  je řadí sám.

## Past 0.98: reimport vrátí textury v plné velikosti (APK nad 100 MB)
- `tools/textury_tablet.py` ořezává horní mip úrovně ETC2 **přímo v `.godot/imported`**. Každý reimport (havárie disku,
  smazaná `.godot`, nový kontejner) je vrátí v plné velikosti: APK 100,6 MB (GitHub odmítne > 100 MB), grafika
  1065 MB místo 620 MB, z_rostliny 245 MB místo 136 MB.
- Oprava: `vydani.py` ho spouští po importu vždy (i s `--jen`). Před pushem zkontrolovat velikost APK (< 100 MB).
- Nepushnutý commit s velkými soubory: `git reset HEAD~1 && git reflog expire --expire=now --all && git prune` (uvolní disk).

## Zdroje jen od Míši z chatu: `zdroje/nahrane_misa/` (28. 10.)
- `modely/` je mimo git (zdroje jsou na Disku), ale modely poslané přímo do chatu na Disku nejsou: horse_1, horse_2
  (= modely/kone/kun_hnedak.glb), armored_horse, balt_horse (zdroj výstroje, tools/kun_vystroj.py), leather_saddle,
  wooden_gate, withe_fence. Uloženy v `zdroje/nahrane_misa/` (`.gdignore` - Godot je neimportuje, do APK nejdou).
- Úklid disku: mazat jen build/packs, build/beh starší den, náhledy v build/ladeni a scratchpad; nikdy data/, apk/,
  modely/, zdroje/, .godot/imported (bez zdrojů nejde znovu postavit).

## Past: set_script na uzlu, který už je ve stromu (0.98, mlýn)
- Godot pak nezavolá `_ready` a nezapne `_process` → kolo mlýna stálo, mletí hlásilo „Kámen stojí“. Po `set_script`
  na uzlu ve stromu vždy `call("_ready")` + `set_process(true)` (nebo skript nastavit před `add_child`).
- Export 28. 10. odpoledne spadl na `NameError: Part` v nové funkci kraj.py: `Part` se v kraj.py importuje uvnitř funkcí
  (`from lib import Part`), ne nahoře – každá nová funkce, která staví síť, si ho importuje sama.

## Brány proti dnešním chybám (Míša 28. 10.: „dneska děláš jen chyby, na všechno máš tabulky a postupy“)
- `tools/export.sh` rc 7: pyflakes nad `blender/*.py` (nedefinovaná jména, chybějící import) – za sekundy, před
  testem smyslu a Blenderem. pyflakes se do `/opt/bl/bin/python` doinstaluje sám.
- `tools/beh.sh`: chyba enginu ze seznamu `tools/beh_chyby.txt` v logu Godotu = běh CHYBA (dřív OK a snímky
  40 min na rozbitém terénu). Nová neškodná hláška se tam nepřidává – opraví se příčina.
- Úprava sítě terénu ve hře: vzor `_upravy_terenu` (každý povrch přes SurfaceTool), ne vlastní varianta –
  `add_surface_from_arrays` s poli bez formátu rozbije vlastní kanály (Invalid array format).
- Před pushem vydání: velikost APK < 100 MB.
- Neupravovat `tools/beh.sh`, když běží (bash čte skript průběžně).
- Po exportu vždy import (teď v `tools/export.sh` rc 8): export maže `modely/rostliny` i s `.import`, bez importu
  hra ve testech a snímcích nenačte 162 modelů a textur (bílé plochy) – „No loader found“ je v `beh_chyby.txt`.
- `pkill -f <vzor>` v příkazu, jehož text vzor obsahuje, zabije i ten příkaz (28. 10. přišel o úpravy). Úlohu na
  pozadí zastavit přes TaskStop; procesy hledat `pgrep -f '[e]xport_game'` (hranatá závorka) a zabíjet zvlášť.

## 28. 10. večer – export rc 9 a testy na rozbitém stavu
- Řetěz `export; testy; foto` se středníky pustil testy i po exportu s rc 9 (meze kroků Blenderu). Import Godotu byl
  až za branami, takže testy běžely bez importovaných textur (`get_image` null, bříza 0 variant). Oprava: import
  (`limity_textur` + `godot --import` + `textury_tablet`) je v `tools/export.sh` hned po Blenderu, před testem smyslu
  po exportu a před mezemi kroků. Stav projektu je tedy konzistentní i při rc 4/9. V řetězech dávat po exportu `&&`.
- Meze kroků Blenderu (pasma.test.meze_kroku) chytily dvě skutečné chyby:
  - zaniklá ves Doubrava měla rovinu 24 m na svahu (plošina 4,2 m). Opraveno: ruiny mají `rovina_r_m` zvlášť od
    `myti_r_m`, zaniklá ves 0, protože zdi sledují svah.
  - odpad mlýna leží 2–5 m pod dnem údolí (mlýn potřebuje spád 5,3 m na 42 m, údolí odtoku ho nemá).
    `mlyn_misto.py` nově odmítá místo, kde je za dílem zářez nad `toky_tvar.zarez_max_m`
    (`mlyn.dil.odpad_za_dilem_m`). Na lhota_odtok žádné místo nevyhovuje, na lhota_potok ano (594, 919),
    rozhodnutí je zapsané v radce.md.
- Matice vztahů: vztahy.json není vstup stavby (otisk_exportu ho vynechává), meze testu vztahy_hra jsou ve vztahy.json
  `meze`, ne v pravidla_sveta (jinak by změna kontroly vyžadovala nový export).
- Plánovače dílů (mlýn, větrný mlýn) musí kontrolovat totéž co Blender a test. `mlyn_misto` počítal jen hranu dílu po
  4 m a bez `pod_dilem_m`, takže Blender pak naměřil 3,6 m nad mez. Stejně tak cesta z plánovače se nesmí vyhlazovat:
  vyhlazení serpentiny zkrátilo cestu a zvedlo sklon na 26 %. Za změnou hledej stejný vzorec v planu i v testu.
- Za běhu exportu neměň vstupy (pravidla, blender): `otisk_exportu zapis` na konci by je započítal. Data rozpracovaná
  během exportu drž v scratchpadu a použij je až po exportu.
- **pkill znovu (28. 10. večer):** `pkill -f "tools/export.sh"` zabil i vlastní příkaz (exit 144), protože jeho
  příkazová řádka ten text obsahuje. Úloha na pozadí se zastavuje jen přes TaskStop. Když něco zbyde, nejdřív
  `pgrep -af` a pak `kill <pid>` podle čísla, nikdy `pkill -f`.
- **Hledání modelů (28. 10. pšenice):** hledal jsem jen CC0 a CC-BY zahodil, pak začal modelovat sám – Míša model
  našla a poslala. Postup: hledat CC0 **i CC-BY** (Sketchfab „downloadable“ + licence, Poly Haven, Quaternius, Kenney,
  Disk), Míše poslat 2–3 kandidáty (odkaz, náhled, troj., licence); Sketchfab stahuje jen přihlášený – stáhne Míša.
  Vlastní model až když nic nesedí (CLAUDE.md „hledat hotové“).
- **Potok se po exportu musí předpéct** (28. 10., 0.99 zastavila brána otisku): hladina Bystřice v exportu se změnila,
  `modely/reka` zůstal starý. `tools/export.sh` teď při změně `reka_otisk` spustí `tools/pregeneruj.sh reka` sám, před
  zápisem otisku. Ručně: `bash tools/pregeneruj.sh reka && python3 tools/otisk_exportu.py zapis`.
- **Potoky jako kanál – skutečná příčina** (29. 10., Míša 0.99): pojistka „násep“ v `kraj.voda_tvar` (a kopie v
  `svet.gd koryto_toku_y`) zvedala terén na hladina + breh_m už od kraje vody (d >= pw), ale břeh má té výšky
  dosáhnout až na pw + breh_sirka → u každého toku svislá stěna 0,6 m u vody a plochá lavice (profil z glb:
  -0,27 m v 0,67 m, +0,30 m v 0,89 m). Teď násep jen po profilu břehu (`min(bed + allow, hl + breh_m)`). Kontrola:
  test smyslu `breh_toku` (svah > breh_max_st) a `toky_nasyp`. Profil v bodu osy: scratchpad prof.py (glb) a prof2.py (fort.land).
- **BlendSpace2D bez trojúhelníků = první snímek animace** (29. 10., kůň „ve cvalu“ na louce): když model nemá klipy
  zatáčení (_L/_R), všechny body leží na ose x = 0, prostor nemá trojúhelníky a strom nevrací nic – kostra zůstane
  v prvním snímku dlouhé animace (trysk). Body _L/_R se teď doplní rovným klipem (kun.gd _strom).
- **Balík bez podsložky** (0.99 T-póza): `glob("modely/postavy/*")` nebere `anim/`. Brána `tools/kontrola_baliku.py`
  ve vydání: každá cesta modelu z kódu musí být v balíku jako `<soubor>.import`.
- **Hladina malých toků** (0.991 „asfalt se švy“): jeden souvislý pás `voda_tok` (UV.x napříč), mělká průhledná voda
  (voda.gdshader `maly_tok`), ne čtverec na úsek.

## 29. 10. – lešení, dosah pevných předmětů, kovárna z Disku
- **Lešení v lomu:** patra byla po 1,7–1,9 m, hráč (kapsle 1,76 m) se na nižší plošinu nevešel → `postav_na_volne`
  ho postavilo o patro výš (test lezeni „nahore false“). Patra teď po 2,1 m (`blender/vlastni.py` BUILD leseni_lom*).
  Poučení: každá pochozí plocha nad jinou musí mít světlou výšku ≥ kapsle hráče + rezerva; test lezeni vypisuje,
  co je pod místem sestupu (patro, terén).
- **Pevné předměty** (lom, chalupy) měly natvrdo dosah 60 m, který přepsal rozpočet podle velikosti (drobnosti 20 m)
  → u lomu 232 kreslení navíc (f104). Smazáno; rozpočet platí pro všechny předměty.
- **Kovárna na tvrzi** z Míšina Disku (old_smithy.glb, CC-BY lucasprs51450): 7 kusů katalogu `kovarna_*`,
  rozložení = záznam `lokace.json kovarna_tvrz`, staví `hospodar.forge_interior` → svet.json vybaveni. Do hry až po
  exportu (blender/export_game.py). Soubor sady leží v `/home/user/tvrz-modely/stazene` (EXT); v nové session
  stáhnout z Disku (id 19uH8WjrH7BFVWRMzrpNpF4kFVrUoqL7J, curl drive.usercontent … confirm=t).
- **Blender bez okna:** EEVEE padá (chybí libEGL), náhledy jen Cycles; `predmety.py build` končí segfaultem až po
  zápisu (výstupy platí, kontrolovat řádky „predmet …“).
- **Zvířata a ohrady (29. 10., Míša „z klacíkových plůtků ohrady a do vsi zvířata, ale přemýšlej“):** rešerše – v českých
  vsích 14. st. nejvíc ovcí, ovce v košáru z pletených lísek, prasata v chlívku/ohrádce, drůbež volně po dvoře. Záznam
  `pravidla/svet/zvirata.json` (ohrady v rámci domu, dvory, chování), plůtky `plutek_vetve` staví `svet._ohrady`
  (do vybavení, nic nehýbe – předmět je poslední krok stavby), zvířata vodí `scripts/zvirata.gd` (chůze v mezi,
  pastva/zobání předklonem, slepice utíkají, zvuky; prasata CC0 BigSoundBank). Modely z Disku (CC-BY): slepice 3Dima,
  prase a ovce Pigcraft (AI skeny 2 M troj. → `predmety._dozmensi` po exportu se spojením vrcholů, jinak díry),
  kurník. Test `ohrady`: počet zvířat, plůtek ne na cestě (kraj cesty / ulice – **ne `ves_cesta`, to je maska bez
  trávy, i dvůr**), ne v kolizi (za domy jsou zbytky plotů staré usedlosti!), žádný strom/keř uvnitř, zvířata po 8 s
  uvnitř; výpis OHRADA_KANDIDAT pro výběr místa. Směr hlavy modelu `vpred_st` změřen z pohledu shora.
- **Vydání po změně katalogu předmětů:** `blender/predmety.py` a `modely/predmety.json` jsou vstupy otisku exportu
  (vesnice.py čte katalog) → po stavbě nových předmětů (kovárna, zvířata, plůtky) nejdřív `tools/export.sh`, pak
  `vydani.py`; jinak brána „otisk exportu nesedí“ (29. 10. 0.992 – ztráta jednoho kola).

- **Meandry a pevná místa (29. 10.):** `tools/krok_b/toky_meandry.py` vyhlazuje osu – u pevných bodů (díl mlýna, brody, mosty) musí zůstat původní osa (váha = útlum meandru), jinak koryto dílu mlýna ujede (bylo 1,34 m). Nástroj se pouští vždy z os před meandry (git `voda.json` před 29. 10. odpoledne), ne opakovaně nad už zvlněnými. Osa toku do lesního rybníka končí na hraně vody (`kraj.ryb_polomer`), ne uvnitř – jinak „deska štěrku do vody“.
- **Síť chůze postav (29. 10.):** spojky mezi osami cest (`spoj_m`) jen bez zdi (`lide.gd _volno`); osy samotné se neořezávají (most, schody – paprsek nad terénem by narazil na mostovku a síť se rozpadla, postavy pak šly přímo). Test `vztahy_hra` `zed|postava` kontroluje každý úsek.
- **Zvířata s kostrou (29. 10.):** `modely/zvirata/<druh>.glb` přímo (bez Blenderu, prase CC-BY-NC-ND se nesmí upravovat), balík `z_zvirata` ve `vydani.py --jen`; nohy houpe `zvirata.gd` podle `zvirata.json nohy`. Pomocník při pokusech přepsal `modely/predmety/{slepice,prase,ovce}.glb` – položky z katalogu vyřazeny.
- **Fronta Godotu a limit pozadí (29. 10.):** úloha puštěná přes `run_in_background` bez `timeout` má limit 30 min *od spuštění*, i když jen čeká na zámek `beh.sh` – víc úloh ve frontě se pozabíjí uprostřed (fotky f110 bez posledního snímku). Víc kroků za sebou = jeden řetězový skript (`build/beh/retez_*.sh`) s `timeout` 7200000, pořadí pevné.
- **Meandry a mez zářezu (29. 10.):** `toky_meandry` vlnu zmenší, kde by koryto zařízla do svahu přes mez kroku voda (`pasma.test.meze_kroku`, minus `breh_m`); tok s původní křivolakostí ≥ `krivolakost_max` (tvrz_potok) se nevlní. Hladina tvrzového rybníka −6,4 (při −7,0 zářez horního břehu 4,2 m); nízký břeh drží hráz. Po změně os vždy `tools/protokol_blender.py` (MEZ PREKROCENA = rc 9 exportu) – za minutu, ne až po 25 min exportu.
- **29. 10. export 0995c: málo místa (356 MB)** – `git worktree add` celého repa (7 GB .git, modely) snědl místo. Pracovní
  strom pro souběžnou práci nezakládat; souběžnou práci dělat ve stejném stromu až po startu exportu jen v souborech,
  které export nečte, nebo počkat. Úklid: staré `build/f1xx` snímky a stažené balíky ve scratchpadu.
- **2. 11. testy po restartu kontejneru:** stavba světa v headless testu přesáhla 300 s (watchdog `rychle_testy.sh`
  ještě před testem). Limit je teď v proměnné `TVRZ_TEST_LIMIT` (výchozí 300); po restartu kontejneru pouštět
  s `TVRZ_TEST_LIMIT=1200`.
- **2. 11. export 0996 spadl:** `nove._extract` hledal `jablon.glb` jen v tex_cache, zdrojích a `origin/main`. Stromy v3
  ze `strom2.py` leží lokálně v `modely/nove/` (modely nejsou v gitu) – teď se berou i odtud. Nový strom v3 do
  `nove.STROMY` = nejdřív `strom2.py <druh>`.
- **Střední LOD domů vsi (2. 11.):** `blender/ves_domy_lod.py` peče z `modely/ves/domy.glb` soubor
  `modely/ves/domy_stredni.glb` (stejná síť, barva v barvách vrcholů, 1 materiál). Po každé změně domy.glb spustit
  znovu, balík z_ves ho bere sám. Atlas přes smart_project nefunguje (tisíce šindelů = černý atlas). Vzdálenosti
  `pravidla/svet/modely.json ves_domy_lod`. Spouštět přes `/opt/bl/bin/python` (bpy modul), ne `blender -b -P`
  (tam chybí cesta k `vlastni`); totéž `blender/predmety.py build …`.
- **Fronta Godotu (2. 11.):** víc samostatně zařazených `tools/beh.sh` čeká na zámek nejvýš 30 min. Export zařazený za
  dvě focení spadl na „zamek obsazeny“. Navazující kroky dávat do jednoho řetězu (`build/beh/retez_*.sh`) za sebou,
  ne jako samostatné úlohy, a export nikdy nezařazovat za víc než jeden běh.
- **Poslední funkční verze před přestavbou vsi (2. 11.):** 0.998 = commit `c2809daae67df5fe68487f0aeb643c0812da444c` (tag v0.998 jen lokálně, push tagů
  proxy nepovolí). Přestavba vsi do jednoho zdroje dat (`docs/rozpracovane/rozpory_blender_godot.md`) jde za
  přepínačem v datech. Návrat: přepínač, nebo `git checkout c2809daae67df5fe68487f0aeb643c0812da444c -- <soubory>`.
- **Nový skript a `Pravidla` (2. 11.):** `Pravidla` není autoload. Nový skript musí mít
  `const Pravidla := preload("res://scripts/pravidla.gd")` (jinak Parse Error a celý skript se nenačte – měřicí trasa).
- **Ves v novém rámci z Blenderu (3. 11.):** `lokace.json ves.blender_novy_ramec` true = Blender (`blender/ves_ramec.py`)
  staví ves rovnou na novém místě, hra (`svet.VES_BLENDER`) nic nepřesouvá. Zkouška bez změny záznamu:
  `TVRZ_VES_BLENDER=1`. Záznamy v `pravidla/` nikdy dočasně neupravovat kvůli testu (hlídač to zastaví).
  Zacyklení `_pads → land → flatten → land(pads)` = porušené pořadí terén → cesty → budovy: cesty (`flatten`,
  `road_y`) berou terén vždy bez placek budov (`land_fn(x, z, False, False)`).
- **Vybavení po úpravách terénu (3. 11., rozpor #21):** předmět do 0,6 m nad terénem si drží výšku nad zemí
  (`_vybaveni_nad_zaznam` před úpravami, `_vybaveni_na_teren` po `_zamek_terenu`). Výšky předmětů v datech počítat
  vůči terénu z Blenderu, hra je po úpravách terénu posadí sama.
- **Díl s vlastním terénem a tok (3. 11., mlýn pošesté):** pás napojení (`pasma.dil.napojeni_m`) patří dílu. Tok se
  v něm prolne do terénu dílu celý (koryto, dolina, násyp) až po tvarování vody, a jen v Blenderu. Hra pás
  nepřepisuje, protože prolnutí není idempotentní. Tok musí z dílu vytékat kolmo od hrany, ne souběžně 2–3 m od ní:
  jinak buď stěna, nebo schod. Ověřovat rychle bez exportu výpočtem z `fort.land`: obvod dílu, příčný profil, hloubka.
- **Krok stavby přesunutý z Godotu do Blenderu (3. 11.):** protokol stavby (`tools/protokol_blender.py`) chce pro každý
  krok Blenderu mez v `pasma.test.meze_kroku`, jinak export spadne v kroku 9. Nový krok = hned i mez s důvodem.
  Po pádu v testech po exportu stačí `tools/export.sh --jen-po` (bez nové stavby Blenderu).

## Řetěz testů na pozadí: timeout (3. 11.)
- `retez_ves4` (export 20 min + celá sada + fotky) zabil limit pozadí 30 min (výchozí `timeout` Bash na pozadí). Export i testy
  doběhly, fotky ne. Dlouhé řetězy pouštět vždy s `timeout: 7200000`.
- Vybrané testy: `tools/beh.sh <jm> testy "test1,test2"` – seznam jako ARGUMENT. `TVRZ_TEST_JEN` v prostředí rychle_testy.sh
  přepíše prázdným `$1` → poběží celá sada vč. paměti (3. 11. t_v5: 80 min, řetěz zabit limitem 2 h). Export a testy pouštět
  jako dva samostatné úkoly na pozadí, ne jeden řetěz.
- Zámek Godota (3. 11.): hlídač disku v `beh.sh` zdědil fd 9 se zámkem; když hlavní běh skončil nestandardně, osiřelý
  hlídač držel zámek 40 min a vydání padlo na „zámek obsazený“. Hlídač teď fd 9 zavře a končí s rodičem. Visí-li zámek:
  `cat /tmp/godot_beh.kdo` a `pgrep -fa beh.sh`, osiřelý proces ukončit.
- Disk 3. 11. večer: 783 MB volných, vydání i focení odmítnuty (mez `beh_volno_mb` 800). Uvolněno bez rizika: staré složky
  snímků `build/f11*–f13*`, `build/ladeni`, velké logy `build/beh/*_godot.log` kromě posledního celého běhu (matice čte
  `t_vse4_godot.log`), `build/OdkazHavrana.apk` (vznikne znovu). `.git` 8,5 GB (5,6 GB volných objektů = díly .pck) a
  `data/` 2,7 GB (staré díly balíků) jsou hlavní žrouti – úklid starých dílů mimo manifest až samostatně a s kontrolou.

## Louka: proč tráva roste pozdě (3. 11. večer, změřeno testy trava_dorust a louka_profil)
- Buňka louky 32 m se rozsévá za běhu v GDScriptu trs po trsu: 1,2–2,2 s na buňku na PC (tablet pomaleji), 99 % času
  `_rozsej` (16 000 volání `_vzorek` ~65 µs, `cesta_trava` ~45 µs). Převod do MultiMesh jen ~10 ms.
- Test trava_dorust (krok 1,7 / cval 6,5 / trysk 10,5 m/s, buňka do 20 m bez správné úrovně = pozdě): 1800/1800,
  1190/1800, 1185/1800 snímků pozdě. Vynechání dotazů na stavby a víc vláken nestačí (potřeba ~7× rychleji).
- Předpečení buněk: 1885 buněk × ~230 kB = 430 MB – neúnosné. Řešení: tráva na GPU (pevná síť instancí kolem
  kamery, poloha/výška/hustota v shaderu z textur hustoty, výšky a „bez trávy“ upečených v Blenderu). Viz
  docs/rozpracovane/trava_gpu.md.
- Vydání 0.9997 (3. 11.): `vydani.py` odmítl – změna `pravidla/pravidla_sveta.json` (nové klíče pro hru: pasma.bylina,
  test.trava_dorust_m) mění otisk vstupů exportu, i když je Blender nečte. Každá změna pravidla_sveta.json = nový export
  před vydáním (20 min) – počítat s tím předem, nebo klíče jen pro hru dávat do souboru mimo otisk.
- Disk (4. 11.): volno klesá s každým vydáním (`.git` 8,5 GB, z toho ~5,7 GB volných objektů = díly .pck starých vydání).
  Rychlý úklid bez rizika: `/root/.cache/mesa_shader_cache`, `/root/.cache/pip`, `build/packs/*.pck` (mezivýsledek vydání, ~300 MB, kopie jsou v data/; `build/z_textury.pck` ne), logy `build/beh/*.log` > 1 MB kromě
  posledního celého běhu, staré složky snímků `build/f*`. Trvalé řešení (git gc / LFS pro data) až samostatně.
- Otisk exportu 4. 11.: nový model koně `modely/kone/kun_henry*` (ruční, ne z Blenderu) změnil otisk výstupů – vstupy
  beze změny, proto jen `python3 tools/otisk_exportu.py zapis` (bez nového exportu). Při ručně přidaném modelu stejně.

## Rybník Lhota 0.9998 – kameny, přítok, odtok (4. 11., Míša „kameny pořád levitují“)
- **Kameny – potvrzená příčina (změřeno):** kameny jsou součást modelu dílu (`Rybnik_Kameny`, 97 kusů, v modelu všechny
  zapuštěné 0–0,6 m), ale hra terén dílu mění (`_ryb_hraz_toky`: hráz a koryta toků přes `koryto_toku_y`). Odtok
  `lhota_odtok` (hladina 1,79, rybník 3,35) vede od výpusti **podél hráze uvnitř dílu** (místně x ≈ −14, z −1…31) →
  koryto a dolina snížily břeh až o 2,28 m, 49 kamenů viselo. Dřívější opravy řešily kolizi a pás vody, ne tohle.
- Oprava ve hře (pravidlo, ne výjimka): rozpor #21 platí i pro díly – volný kus dílu na terénu dílu se posune o změnu
  terénu pod svým spodkem (`svet._ryb_kameny_na_teren`, souvislé kusy `_souvisle_kusy`). Test `rybnik_dil`.
- **Zbývá v datech (export):** hráz `voda.json rybnik_lhota.hraz.smer_osy` je rovnoběžná s odtokem (hráz má být napříč
  proudu) a plánovač odtoku (`tools/krok_b/odtok_mimo_ves.py`) nezná čtverec dílu – musí ho mít jako zakázanou plochu
  kromě výtoku kolmo od hráze (stejné pravidlo jako mlýn 3. 11.). Přítok `lhota_potok`: hladina naplánovaná na terénu
  světa bez dílu (vysky.json) – na okraji dílu (+0,30 = 3,65) teče 4,7 (voda nad zemí), uvnitř dílu valem 4,5–5,0
  zářez 1,3–1,6 m (val, „tunel“, schodovité břehy). `toky_hladina.py` musí brát terén dílu (okraj +0,30, val) jako terén.
- **Val přes potok (555, 886) – potvrzeno měřením (`bod`):** `Teren_toky` 4,74 nad terénem dílu 4,35. `ryb_teren` terén
  světa pod dílem snížil, ale `_koryta_naposled` (`koryto_toku_y`, násyp toku mimo kruh rybníka) ho zvedl zpět nad díl.
  Oprava: v `_koryta_naposled` uvnitř čtverce dílu po korytu znovu `ryb_teren` (pod dílem platí díl, povrchy B).
- Terén dílu po `_ryb_hraz_toky`: normály se nepřepočítávaly (svahy koryt svítily jako rovina) a kolize zůstala
  z modelu (hráč nad korytem přítoku 0,4–1,4 m ve vzduchu, (552, 882) síť 3,39 / kolize 4,83) – obojí opraveno.
- **Přítok končí před hladinou (536, 884) – data/Blender:** pás `Toky_voda` končí podle kruhu `voda_polomer_m` 12 m
  (`kraj.toky_voda.v_nadrzi`), skutečný okraj `Rybnik_Voda` dílu je v tom směru 11,3–11,6 m → ~0,5 m koryta bez vody
  (terén dílu 3,03, tráva). Oprava v exportu: obrys hladiny dílu z modelu (mnohoúhelník jako `ryb_obrys`) a konec pásu
  `hladina_presah_m` uvnitř něj. Test `rybnik_dil` (okraj hladiny, „bez vody nad osou“) to hlídá.
- Disk: `rybnik_bod` 3× CHYBA (762 MB < 800). Bezpečně uvolnitelné navíc: staré `test_*.png` v
  `~/.local/share/godot/app_userdata/Odkaz Havrana/` (vytvoří je testy znovu, 19 MB) a `shader_cache` tamtéž (168 MB,
  Godot ji postaví znovu – první běh pomalejší).
- **Kůň 0.9998: sedlo na zádi, jezdec v dřepu, ovladač** (4. 11., pomocník): (1) `kun.gd` měřil kohoutek a hřbet ze VŠECH sítí
  vč. skrytého westernového sedla Saddle1 (hruška 17,9 proti kohoutku 15,9 jedn.) → kůň o 12 % menší (kohoutek 1,40 m
  místo 1,58); bod sedla nad kostí BN_Spine_01 a sedlo Balt kotvené středem obalu (= třmeny, 16–24 cm před sedadlem,
  kus otočený o 180°) → sedadlo ~0,3 m vzad. Teď `jizda.json kun.mereni_bez_siti` a bod sedla = sedadlo skrytého sedla
  modelu (`sedadlo_sit`, `kun.gd _sedadlo`), sedlo výstroje kotvené svým sedadlem. Rozbor glb bez Godotu:
  přímo z glTF (uzly, inverseBindMatrices, JOINTS_0/WEIGHTS_0, numpy) – za sekundy, bez zámku Godota. (2) Driving_Loop je sed na židli (stehna vodorovně); natočení kolem
  místních os kostí nohy nesrovnalo → `telo.gd _nohy_v_sedle` natočí stehno/lýtko na směr v soustavě koně
  (`telo.sed_v_sedle`), pánev i svisle na sedlo. (3) `pad.gd` nastavoval `fly_up` (ostruha) jen v letu → na ovladači
  žádný cval/trysk/sesednutí; mapování v `docs/ovladani.md`. Test `telo_zaber` hlídá pánev, nohy dolů a sedlo před půlkou trupu.
- Disk 4. 11. večer znovu pod 800 MB při souběhu pomocníků (beh.sh odmítá) – `build/OdkazHavrana.apk` a `build/packs` po vydání smazat hned.

### Disk 4. 11. večer (762 MB volno, všechny běhy padly)
`~/.local/share/godot/app_userdata/Odkaz Havrana/data` = staré stažené balíky hry (*.pck, 2 GB, do 28. 10.) – na PC je
hra nepotřebuje (běží z res://); smazáno se svolením Míši → +2 GB. Při nedostatku místa uklidit nejdřív tady
(a `git count-objects -vH`: 5,9 GB volných objektů – `git gc` až při dostatku místa, potřebuje místo na nový balík).

### Kontrola před 0.9999 (nezávislý kontrolor, 4. 11.) – známé věci k opravě
- `svet.gd _kus_body` volá `surface_get_arrays` pro každý kus kamenů rybníka znovu (97×) – zbytečné při načtení (NEOVĚŘENO měřením);
  kopírování pole vrcholů při posunu kamenů opraveno (posuny po povrchu najednou).
- `_opreny_o_predmet`: úhel oříznut na 35°, dotyk vychází 0,45–0,6 délky místo `pasma.predmet` 0,85 – žebřík přečnívá hranici.
- Varianta trasy `louka_un` (tráva unshaded): na PC pořád skoro černá i se správným `svetlo` (0,43) – příčina mimo `svetlo`, nehledáno
  (měření jen výkonu); barvu řešit, až měření ukáže přínos.

### Most přes Bystřici (5. 11., Míša 0.99991: „cesta na most nevede; tráva na mostě“) – tabulka misa_28_chyby ř. 39–40
- **Osa cesty × most:** most z `kraj.bridge` je rovný a dlouhý podle šířky koryta (53 m); osa `odbocka_ves` byla rovná jen 27 m.
  Pravidlo je teď záznam přechodu (`najezd_m`, `oblouk_m`, `krok_m`) a `tools/krok_b/most_napojeni.py` (pak vždy `cesty_sklon.py`).
  Hra čte `najezd_m` místo konstanty. Kontroly: test smyslu `most`, hra `most`.
- **Síť z Blenderu má identickou transformaci** (vrcholy ve světových souřadnicích). AABB šikmé stavby je tedy obdélník
  ve světě, ne její pudorys. Pudorys brát ze sítě v její vlastní soustavě (hlavní osa vrcholů, jako `_najezdy_mostu`).
  Stejný problém mají `_u_mostu`/`_u_mostu_jen` (jen víc vylučují, nevadí).
- **`modely/louka/kryti.bin` je z 27. 10. bez otisku** – nezná rozšířenou Bystřici ani novou ves (3. 11.). Přepéct
  `tools/pregeneruj.sh kryti` (Godot, beh.sh) a dát mu otisk exportu jako `reka_otisk`; do té doby jsou mosty v krytí jen z modelu za běhu.

## Vlajky a prapory ve větru (5. 11., pomocník; Míša „vlajky a prapory jsou statické“)
- `shaders/latka.gdshader`: vlání jen ve vertex shaderu (postup „flag shader“ – GDQuest Flag shader 3D / godotshaders Waving flag,
  místo šumové textury dvě sinusovky): posun úměrný vzdálenosti od žerdi, vlna po délce + třepotání, fáze z polohy předmětu,
  normála natočená podle sklonu vlny. Data `pravidla/svet/modely.json` `latka` (druh podle předpony: prapor_, vlajka_, korouhev_),
  směr větru `prostredi.json vitr.smer_listi_voda` (i natočení korouhve v `svet._erb_tvrze`).
- Žerď zjištěna z geometrie (`blender/vlastni.py _grid_cloth`, ověřeno na `korouhev_havran.glb`): glTF obrací V → UV.y = 0 nahoře,
  UV.x = 0 u žerdi korouhve. Osa posunu = normála látky v Godotu (Blender −Y = Godot +Z).
- `predmety.gd _latka_mat`: povrch s materiálem jménem modelu dostane ShaderMaterial (1 na model, textura z původního). Dosah a LOD beze změny.
- Nový shader není v předehřátí shaderů (`main.gd`) – první zobrazení korouhve může cuknout (NEOVĚŘENO na tabletu); doplnit tam.
- Ověřeno snímky PC 5. 11. (`docs/screens/latka_korouhev_1/2.jpg` – stejný pohled s odstupem ~3 min, látka jinak prohnutá;
  `latka_prapor_vlajka.jpg` – prapor a vlajka položené na nádvoří jen pro snímek). Amplitudy NEOVĚŘENO na tabletu.
- Viděno při tom (není opraveno): žerď korouhve stojí ~0,5 m vedle železné tyče s makovicí – glb je vystředěný podle obalu
  (žerď v modelu x ≈ −0,58), `svet._erb_tvrze` klade počátek modelu na vrchol věže. Oprava v datech/modelu, ne posunem v kódu.

## Záseky při prvním příjezdu (5. 11., Míša 0.99991: most 4104 ms, lom 1074 ms „kreslení+čekání“) – pomocník shadery
- **Měřidlo:** `tools/beh.sh <jm> cmd bash tools/mereni_prvni.sh <prázdná složka>` – hra s `TVRZ_PRVNI=1`, Mesa bez keše,
  `LD_PRELOAD=build/glcount.so` (`tools/glcount.c` počítá `glLinkProgram` = sestavení programu, s `GLCOUNT_POPIS=1` i definice
  varianty). Teleport kostel → most → lom, 20 snímků + otočka v 8 směrech. Časy snímků na llvmpipe NEJSOU tabletové
  (llvmpipe si sám překládá varianty při kreslení, snímek 1–3 s) – rozhoduje **počet sestavených programů po předehřátí**.
- **Naměřeno (PC, studená keš, 0.99991 + předehřátí):** předehřátí 483 programů; po něm první cizí místo (kostel) 19
  (z toho 3 HUD 2D), most 0, lom 2. Zbylé programy jsou nové *verze* (jiný kód materiálu: instancované StandardMaterial3D
  s DO_SIDE_CHECK/alpha scissor, stébla s vertex lighting), ne varianty světel. Hypotéza „předehřátí svítí všesměrovým
  světlem od 1. snímku“ VYVRÁCENA měřením (2 snímky bez světel: stále 14 u kostela, 2 u lomu) – změna vrácena.
  Které uzly to jsou, NEZJIŠTĚNO (`Material.get_shader_rid` v GDScriptu není; seznam „kombinací“ v logu je hrubý – klíč podle
  RID materiálu, ne shaderu). Po 1. sestavení je keš uloží, podruhé se nesestavují (níže).
- **Teplá keš (PC, stejná složka user:// podruhé):** předehřátí 0 sestavení (vše `glProgramBinary` z keše), kostel/most/lom 0.
- Most u Bystřice 0 programů a lom 2 (podezření z hrubého seznamu: kámen pískovec, sazenice borovice) → **4 s u mostu shadery
  z PC nevysvětlují** (podezření jinde: ovladač Adreno si překládá při změně stavu, paměť/zram, OS; NEOVĚŘENO).
- **Keš shaderů je zapnutá** (Godot 4.4 GLES3 `rendering/shader_compiler/shader_cache/enabled` výchozí true, `shader_gles3.cpp`
  ukládá `glGetProgramBinary` do `user://shader_cache` i na Androidu, i za hry sestavené varianty). diag.log po předehřátí
  píše „kes shaderu N souboru X MB“ – na tabletu ověřit, že 2. spuštění téže verze má předehřátí výrazně kratší.
- Shadery bez uzlu ve světě při startu (látka vlajek `latka.gdshader` z `predmety._latka_mat`, cokoli z `res://shaders`) se
  předehřívají jednou jako mesh i MultiMesh (`main._pred_shadery`), jen když je svět sám nepoužívá (studený start PC: 533
  programů místo 483 za načítací obrazovkou; nevadí po 1. spuštění, keš).

### Kůň 0.99991: sesednout, most, voda, „neviditelné stěny“, cestování (5. 11., pomocník)
- **Most (potvrzená příčina):** hlídaná dráha koně (`kun.gd`) brala výšku z mřížky výšek louky `svet._vyska` (2 m). Ta pod
  mostovkou zná dno zářezu Bystřice, takže po ose cesty `odbocka_ves` (ta leží šikmo k mostovce) hlásila „sráz“ na
  (216, 594) – kůň zastavil na mostě / před ním (test `kun_prekazky`: „kontrola do 0.99991 stál by po 21,6 m“). Po přímé ose
  mostovky to náhodou prošlo – **hlídat povrch z fyziky**, ne z mřížky: `kun.prekazka` = paprsky shora po `draha_krok_m`
  (mostovka, podlahy, terén), sráz = pokles mezi body nad `sraz_m`.
- **Voda:** dřív `od_vody < -hloubka_max_m` = zastavit (rybník tvrze: „stál by po 8 m“). Teď voda není překážka: `svet.hladina(x, z)`
  (Bystřice z koryta, nádrže, malé toky, rybníky), brod zpomalí, od `plavat_od_m` kůň plave (klip Swim, kopyta
  `plavani_ponor_m` pod hladinou). Čísla `jizda.json kun._voda` (část odhad – NEOVĚŘENO zdrojem).
- **Rychlé cestování na koni:** `fast_travel` posunul jen hráče, `kun.gd` ho dalším krokem fyziky vrátil do sedla na starém
  místě. Teď `kun.premisti` (volné místo pro trup koně), jezdec zůstává v sedle.
- **Sesednout na dotyku:** tlačítko „Sesednout“ nad ostruhou jen ve stání (`hud.gd _btn_sesednout`), na ovladači nápověda Y.
- **„Jakoby stěna, ale nic tam nebylo“ (dvě potvrzené příčiny):** (a) válec nohou koně od kopyt narážel na každý kámen
  s kvádrem z exportu (`kamen_maly` v trávě 0,2–0,6 m, hrany koryta) – kůň neměl krok jako hráč. Teď `kun._prekroc`
  (krok přes překážku do `jizda.json kun.krok_pres_m` 0,45 m). **Nepoužívat SeparationRayShape3D** pod nohama: paprsek
  propadal mezerami mezi prkny mostovky a kůň na mostě stál (zkoušeno 5. 11.). (b) kvádr exportu kamene, který pozdější
  krok smazal (−26,5; 126,6), zůstal = kolize bez modelu; teď `svet._kolize_kamenu_bez_zaznamu` (krok 10, 9 kvádrů pryč).
  Síť 30 m × 8 směrů: 0 kolizí bez modelu, 130 nízkých překážek kůň překročí (dřív stál).
- Test `kun_prekazky` (`tools/test_svet.gd`, čísla `jizda.json test_prekazky`) – most (osa mostovky i po cestě),
  brody, Bystřice, plavání, cestování, síť bodů po mapě (kolize bez viditelného modelu = chyba, `KUN_STENA`).
  Pozor: síť dlouho běží (TVRZ_TEST_LIMIT 2400); xvfb snímky jízdy jen krátce před místem (snímek 1–3 s, fyzika ≤ 8 kroků/snímek).
- **Kontrola 5. 11. (nezávislý kontrolor) – opraveno:** překrok jen při čelním nárazu (`prekrok_celne_min`) a nejvýš
  jednou za `prekrok_odstup_m` (dřív kůň poskakoval podél obrubníku); povrch dráhy a hloubka koulí `povrch_koule_r_m`
  (paprsek prošel mezerou mezi prkny → „sráz“/„plavání“ na mostě); cestování na koni: bez volného místa hráč sesedne
  a cestuje sám, body ve vodě se přeskočí, tolerance na svah; tlačítko Sesednout sesedá až při puštění prstu uvnitř,
  60 px nad ostruhou, s lukem mimo kruh napínání; kvádr kolize patří kameni jen při shodě středu a rozměru
  (`pravidla_sveta.json pasma.kolize_kamene`, výpis `KOLIZE_KAMEN`); `svet.hladina` čte pravidla jednou; čísla v `jizda.json`.

- **Export 5. 11. rc 11 (datové textury):** Godot při `--import` přepnul `reka_dist/reka_flow` zpět na VRAM (ETC2), protože
  `.import` měl `detect_3d/compress_to=1` a `.import` v `modely/` nejsou v gitu (ruční oprava z 0.9997 se ztratila).
  Oprava: `tools/datove_textury_import.py` v `export.sh` před importem nastaví `compress/mode=0` i `detect_3d/compress_to=0`.
  Ověření po opravách z kontroly (5. 11. 14:00, `kun_prekazky` OK): most po ose i po cestě oběma směry projel, brody
  a 3 místa Bystřice projel, rybník tvrze plaval, cestování na koni v cíli v sedle; síť 0 kolizí bez modelu, 141 překročí;
  `KOLIZE_KAMEN` 20 kvádrů kamenů 0,6–1,1 m smazaných se svým kamenem (316 přiřazených), žádný plot/studna.
  Pozor: test dřív nepoznal neprojetou jízdu (lambda `jed` měnila kopii `ok`) – opraveno (`chyby_jizdy`).
  Neověřeno: výlez plavajícího koně na břeh 37° (Bystřice (270, 1094), `kun.gd` kopyta na dně → netlačit dolů).
- **Korouhev – žerď mimo tyč (opraveno 5. 11.):** `svet._erb_tvrze` posune model o střed žerdi zjištěný ze sítě
  (`_zerd_modelu`, materiál `dub_tyc`), žerď teď stojí na makovici věže (`docs/screens/korouhev_zerd_opravena.jpg`).

## Past 5. 11. (pomocník postav): ztracené úpravy výměnou souborů a přepsaný běžící skript
- Pro snímky „před úpravou“ jsem na dobu startu Godotu vyměnil `lide.gd` a `postavy.json` za staré verze a zpět je vracel
  z kopie. Současně jsem přepsal `build/beh/postavy_pred.sh`, který už běžel: **bash čte skript průběžně**, starý běh
  vykonal část nového textu, udělal výměnu podruhé a kopie „nových“ souborů přepsal starými → úpravy ztraceny (obnoveny
  z rozhovoru). Pravidla: **běžící skript v `build/beh/` nikdy nepřepisovat** (nový soubor s jiným jménem); pracovní
  soubory **nikdy nevyměňovat** kvůli běhu – snímek „před“ jen z commitu před úpravou (nebo před první úpravou), rozpracované
  věci průběžně commitovat.
- Disk 5. 11. odpoledne znovu pod 300 MB při souběhu pomocníků (běh postav zastaven hlídačem). Uklizeno podle seznamu výše
  (staré `build/f*`, `shader_cache` Godotu, velké logy). Velký žrout je i sdílený scratchpad (`src` 420 MB jiného pomocníka).

## Tráva unshaded v lese – nový rozbor příčiny (5. 11., pomocník; po 2 neúspěšných opravách)
Stínovaná tráva (vertex_lighting + mapa stínů slunce) je v lese tmavá, unshaded (`TVRZ_UNSHADED`, tablet) byla
bělavá a bez stínu. Pokusy 1 (`stin_korun` 0,55 přes masku `stanoviste`) a 2 (`barva_x` po kanálech) selhaly.
- **Potvrzeno měřením (f160, `louka.diag_unshaded`, řádky `UNDIAG`):** textura `stanoviste` i `stan_rect` v unshaded
  materiálech byly správně (všech 24 materiálů vč. kopií `_mat_cache`, trs/drn/vysoká/vějíř/kupa/květy). Maska R/G ale
  vracela **0 na všech měřených místech lesa** (190,884; 179,895; 212,274), kde stínovaná tráva je 2–6× tmavší.
  Příčiny: (a) pravidlo zápoje v `_stanoviste` nuluje krytí v řídkém lese (je to maska pro povrch půdy, ne pro stín),
  (b) poloměr koruny z koule impostoru je u listnáčů 2–3× menší než model (dub_stary 3,4 m × 11,4 m z glb),
  (c) maska vzniká před `_les_hustsi`, `_lesni_plast` a vsí – část stromů v ní vůbec není (11 272 × 18 919 stromů),
  (d) stín nepadá pod korunu, ale posunutý od slunce (odpoledne elevace 22°, posun ~15 m).
- **Potvrzeno:** model světla byl „slunce+okolí × (1−0,55·maska)“; stínovaná tráva ve stínu dostává jen okolí (oblohu).
- **Oprava:** `svet._koruny_stin()` (po všech krocích sázení) – maska krytí všemi stromy, poloměr/výška koruny z modelů
  (`modely.json trava_unshaded.koruny`, `tools/koruny_rozmery.py`); `stebla.gdshader` unshaded: světlo = `svetlo` (okolí)
  + `slunce` × (1 − `stin_korun` × krytí v místě `w + stin_posun`), posun = směr ke slunci × výšky korun z
  `vysky_korun` (3 výšky – spodek, střed, vrch korun; stín za nízkého slunce je dlouhý pruh). Okolí = obloha (zenit/horizont `sky.gdshader` lineárně, váha `obloha_zenit`) × energie oblohy ×
  ambient_light_energy; slunce = barva × energie × Lambert s obalem (`obal` = ROUGHNESS, diffuse_lambert_wrap). Každá
  složka kalibrovaná zvlášť (`slunce_x`, `okoli_x`) – čísla a jejich původ v `modely.json _trava_unshaded`.
- Měření: dvojice `st_*`/`un_*` v jednom běhu (`main._mereni`, kamera z výšky terénu `svet._teren_y`), porovnání
  `tools/trava_unshaded_porovnani.py` (bloky 20 px, slunce/stín podle Otsu). Kalibrace v lineárním prostoru před
  tonemapem: ACES (Godot, white 1,6) invertovaný numericky – ve stínu je odezva ACES téměř nulová (pata křivky), proto
  odhady z poměrů sRGB selhávaly.
- **Pasti tohoto rozboru (zapsáno, ať se neopakují):** (1) `run_in_background` bez `timeout` končí po 30 min – focení
  s čekáním na zámek dát `timeout` 7200000; (2) `_ground_hi` (paprsek shora) v lese trefí korunu → kamera v listí
  a dvojice snímků nesouhlasí; pro dvojice brát `svet._teren_y`; (3) `beh.sh` kontroluje všechny změněné .gd – parse
  chyba v cizím rozpracovaném souboru (tools/test_svet.gd ř. 5813 `var ic :=` bez typu) zastaví všechny běhy (opraveno
  na `var ic: int =`); (4) disk pod 800 MB – úklid podle seznamu výše.

## Nábytek a lůžka jako data, další postavy (5. 11. večer, pomocník chování)
- Vybavení domů vsi už není v kódu (`DUM_VYB` pryč): `pravidla/svet/nabytek.json` (`domy` podle typu modelu, `mlyn`,
  `svet` = tvrz, `zapecene` = lůžka v modelu hostince). Změna nábytku = úprava záznamu, ne kódu. Svět z nich dělá
  `data.vybaveni` a seznam lůžek `data.postele` (lide.gd spánek). Nové modely `lozko`, `lozko_uzke`, `slamnik`
  (`blender/vlastni.py`, `predmety.py build …`) → do vydání balíky **`z_katalog`, `p_lozko`, `p_lozko_uzke`, `p_slamnik`**.
- Vnitřní místa postav (`postavy.json mista` s `dvere`/`venku`/`vnitrek`/`mistnost`): postava jde dveřmi, sedá jen na sedák
  v té místnosti; venkovní činnost jen na sedák mimo místnosti. Test `lide_chovani` bod 8: lůžka a sedáky na podlaze, pod
  stropem, bez kolize, dojití od dveří (mřížka 0,25 m). Postup a díry: `docs/rozpracovane/postavy_plan.md` „Nábytek a další postavy“.
- **Disk 5. 11. večer:** v `.godot/imported` bylo 1 109 souborů (788 MB), na které neodkazuje žádný `.import` ani
  importovaná scéna (staré verze textur/modelů po přejmenování) – smazány (cache, Godot je případně přeimportuje).
  Seznam vznikne skriptem: odkazy z `*.import` + jména v `.godot/imported/*.scn|res` + uid_cache; zbytek = sirotci.

## Automatická kvalita (5. 11., pomocník; Míša „při nestíhání zhoršení grafiky, ať hra jede plynule“)
Rešerše a návrh: `docs/rozpracovane/kvalita_auto.md`. `scripts/kvalita.gd` (uzel `Kvalita` v main), data
`pravidla/svet/kvalita.json` (kroky jemná/nouzová, co šetří gpu/cpu, prahy, okna, teplo, paměť). Volba Nastavení →
„Kvalita: automatická / ruční“ (výchozí zatím ruční všude – zapnout `vychozi.tablet` po ověření na tabletu; PC vždy ruční kvůli snímkům). `main.apply_quality()` na konci volá
`kvalita.zaklad()` (ruční nastavení = základ), `apply_fyzika()` bere `kvalita.max_fps()`. Měřicí trasa ji vypne, varianta
`auto` zapne. Krok `trava_bez_stinu` je `povoleno: false` – zapnout až po opravě barvy unshaded trávy v lese.
Test: `tools/beh.sh kvalita cmd godot --headless --path . -s res://tools/test_kvalita.gd` (bez světa, sekundy).
Teplo: `getThermalHeadroom` přes vestavěný `AndroidRuntime` (Godot 4.4) – NEOVĚŘENO na tabletu (zda JavaObject vrátí číslo;
při selhání se teplo vypne a zapíše do diag.log „KVALITA teplo: … nedostupne“).
- Stav 5. 11. 22:30: `lide_chovani` **OK, 0 chyb** (běh kopi_test2, `build/beh/kopi_test2_godot.log`): 32 obyvatel, 32 lůžek,
  0 děr, nábytek 47 kusů / 38 dojití / 5 v patře. Výška ležení na lůžku/slamníku upravena podle snímku (postava ležela v matraci), ověřeno snímky
  `docs/screens/postavy_po/lozko_34b_5_11.jpg`, `slamnik_bok2_5_11.jpg` (běh luzko_foto4). Kopí stráže svisle hrotem nahoru, pata u země (`drzeni.kopi` spočteno z os ruky, snímek
  `docs/screens/postavy_po/ruka_kopi_straz_5_11.jpg`).
- **Výsledek (f165, PC, odpoledne 15,5 h; `docs/screens/trava_un_f165_*.jpg`, vlevo stínovaná, vpravo unshaded; dřívější
  kroky `trava_un_f162_*`, `trava_un_f164_*`):** louka na slunci m1 (55,65) průměr po kanálech R 0 % / G 0 % / B +2 %
  (ověřená oprava). Les: už tmavý se stíny korun na správné straně (ne bělavý), ale průměry mimo 10 %: les4 (−4,500)
  R +48 / G +49 / B −15 % (velmi tmavé hodnoty, sRGB 6/23/10 × 9/34/9), sad m2 (60,420) R −52 / G −18 / B −21 %
  (stín z masky širší než skutečný – koruny sadu řidší než krytí, chybí sluneční skvrny; stín do tyrkysova, okolí má málo R).
  `tablet` zůstává false. Zbývá: (1) hustota korun `stin_korun` < 1 nebo menší poloměr pro sad/ovocné stromy (porovnat
  pohled shora `shora` – f164 −16/−11/−14 %); (2) poměr R:G okolí ve stínu (měřit čisté stínové plochy, ne Otsu);
  (3) jiné denní doby a tablet NEOVĚŘENO; (4) maska `_koruny_stin` +215 ms při stavbě na PC (tablet NEOVĚŘENO).
- f164 skončil `CHYBA rc=1` kvůli cizí chybě (`modely/predmety/lozko.glb` bez loaderu), snímky se pořídily.

## Rybník Lhota a okolí – nový rozbor příčin (6. 11., Míša snímky misa_6_11/19–31, práce zastavena kvůli limitu)
- **Rákos a orobinec u rybníka – potvrzeno (log):** `_rybnik_breh_dil` končil „rybnik Lhota: chybi druh rakos_1_0“ →
  u rybníka 0 vodních rostlin. Blender rákos nesází (návesní rybníček vyřazen), klíč v `data.rostliny` chyběl. Oprava:
  model v katalogu → klíč založit (měřítko 1). Test `rybnik_dil` nově vyžaduje ≥ 50 rákosu/orobince v dílu.
- **Holý hnědý pás – naměřeno z modelu:** `Rybnik_Teren-col` má G (tráva) v poloměru 7–11 m = 0–0,5 (bahno), tj. pás
  ~3–4 m od 0 do +0,45 m nad hladinou; louka k tomu přidává `0.85*smoothstep(0.12, 0.4, výška nad hladinou)` a
  `od_vody < holy_breh_m` → bez trsů. Rešerše v `pasma.voda` říká mokrý okraj 0,2–0,5 m, tráva k vodě. Další krok:
  G dílu ve hře přepočítat pravidlem z výšky nad hladinou (holý jen do `holy_breh_m`), ne z modelu; mez louky stejně.
- **Rovný vodní pás nad terénem, skalní koryto nad zemí (21, 22) – podezření, čísla z dat:** dvě výškové autority.
  Díl má pevný okraj +0,30 (3,65) dokola, `ryb_teren` stahuje svět v pásu 6 m na tuto výšku; přítok `lhota_potok`
  má hladinu z Blenderu (vysky.json bez dílu): na hraně dílu 4,70 (o 1 m nad okrajem dílu), uvnitř 4,12 → 3,46 na 4 m
  a pak 3,37 plochý až k vodě. `_ryb_hraz_toky` koryto jen snižuje (min), takže voda nad nižším terénem dílu zůstane
  ve vzduchu; násyp toku (břeh ≥ hladina + breh_m) mimo díl zůstane jako val nad stáhnutým okolím → strmé svahy =
  skála v zem.gdshader. Oprava jen v exportu (rozpor Blender × Godot, zapsat do rozpory_blender_godot.md): terén dílu
  a pás napojení staví Blender jako u mlýna (3. 11.), `toky_hladina.py` bere terén dílu jako terén, hra jen vkládá.
  Míša rozhodne hráz (`voda.json rybnik_lhota.hraz.smer_osy` je souběžná s odtokem).
- **Mlýn a náhon (23):** totéž – hladký terén dílu mlýna bez trsů (`louka _vzorek`: tráva z G terénu dílu), ostré
  břehy náhonu z modelu. Neřešeno.
- **Mlýn, dva žebříky (24–25) – podezření:** model `mlyn.glb` má schody na půdu (`Mlyn_Kol_Schody` u x 1,58 z −2,75,
  hra z nich dělá kvádry schodů) a hra navíc staví `Mlyn_zebrik` z `voda.json mlyn.dil.zebrik` (x 0,37). Další krok:
  ověřit, zda jsou schody v modelu pochozí na půdu; pokud ano, záznam `zebrik` z voda.json odstranit (export, voda.json
  je v otisku), test „dva výstupy na stejnou podlahu do 3 m“.
- **Hostinec tráva uvnitř (30–31), plůtek kůly vodorovně (26, 602,931), deska na mostě (12), domek bez hlíny pod
  podlahou (19, 447,924) – nezačato.** Kryti.bin u hostince pokrývá jen část půdorysu (x −76..−58, z 917..937, děravě);
  louka má půdorys z AABB `Staticky_*` (`_v_budove`); test `interier` měří jen `_vzorek`, ne skutečné trsy a
  rostliny (`_plants`). Test `stavby_na_zemi` bere jen 8 bodů obvodu domů v `_domy` – stodoly/sýpky vsi z Blenderu
  v něm možná nejsou.
- Beh: `rychle_testy.sh` watchdog 300 s nestačí (stavba světa 275 s) → `TVRZ_TEST_LIMIT=700`.

## Postavy 0.99993 (6. 11., pomocnik postav; Misa r. 46-48, 57, 59) - stav pri setreni limitu
- **Spanek na luzku (r. 59, potvrzena pricina z kodu):** `_do_postele` hral klip lezeni s tempem 0 a prolinanim; prolinani
  v AnimationPlayer ubyva s casem x speed_scale, pri 0 se nedokonci -> postava zustala v poze chuze/stani na matraci.
  Oprava `lide._klip`: tempo 0 = bez prolinani. Test `lide_chovani` 7b (z chuze do postele: klip spani, hlava a panev
  v jedne vysce). Overeno testem (beh lide_nav: lezi 32 z 32). Snimek ve hre v noci NEOVERENO (setreni).
- **Chuze pres zed a postel (r. 46):** pricina - `_volno`/test `zed|postava` meri paprsky nad mrizkou vysek louky
  (`_vyska`), ne nad podlahou; na nadvori a v budovach sly pod zdi a pres postel; schod hrace 0,45 m pusti postavu na
  luzko. Nova mrizka chuze `lide._nav_cesta` (A* po 0,3 m, podlaha fyzikou, schod 0,28, kvadr postavy, data
  `postavy.json graf.mrizka`) v `_cesta` a obchuzkach; test `lide_chovani` 7c (obchuzky nadvori, paprsky nad podlahou).
  Test (beh lide_nav) CHYBA 10: mrizka nenasla cestu mezi misty nadvori ke brane (-3,14) (3 selhani) -> nouzova
  cesta pres sit cest za branou (0,28.5) jde zdi (`Svet/Kolize`); kovarna->staje narazi do predmetu. Dalsi krok: vypsat
  bunky kolem nadvori_brana (zavrene vrata/mriz? misto v kolizi?), nouzi nevracet primku. Nezapojeno: `_cesta_pruchod` uvnitr budov (body `uvnitr` rovne), vykon na tabletu NEOVERENO.
- **Nezacato (zbyva):** predmety v rukou podle klipu (r. 47: rezimy drzeni visi / svisle / obe ruce - kopi pri chuzi,
  vedro za ucho, krumpac obouruc; DIAG poloh rukou v `build/beh/fp1.log`), lom (r. 48: `lom_stena_1/2` lezi ~8 m za
  patou steny = nahore v trave; misto z geometrie steny - paprsek z dna k `Teren*` se strmou normalou, 0,8 m od lice;
  kamenik ke `kovadlina_spalek`), hospoda (r. 57: obsluha jako obchuzka sudy-stoly-krb s dzbanem, hoste sed + korbel).

### Kůň 0.99993: házení hlavou, vzpínání, sedlo (6. 11., pomocník, řádek 50 tabulky)
- **Vzpínání a házení hlavou (potvrzeno rozborem glb a testem):** `kun.gd` pouštěl klip `Run_Stop` (smyk se vzepjetím:
  trup +30°, hlava +0,7 m) při každém zpomalení z > 5 m/s k nule – pod jezdcem každé puštění páčky i výpadek palce
  na dotyku; požadavek se opakoval každý snímek brzdění. Teď `jizda.json kun.zastaveni_*` (pod jezdcem ne, volný kůň
  jednou). Pastva „6 Eat“ volného koně běžela dál po nasednutí → pod jezdcem se jednorázový klip ukončí. Houpání jezdce
  skákalo (přepnutí délky kroku/amplitudy mezi krokem a cvalem) → vlastní fáze `_houp_f`, plynulá amplituda.
- **Překrok / sestup:** tělo (kolize) skočí, vzhled (model, sedlo, jezdec) dobíhá `prekrok_vyrovnani_ms` (`_vyr_y`);
  totéž svislý skok nad sklon podlahy (`prekrok_skok_nad_m`, přichycení floor_snap při sestupu z kamene).
- **`kun_zivy.gd` je pro kun_henry mrtvý:** kosti v `kun.zivy.kosti` (Hips, Spine1, Neck_…) model nemá (má BN_*) – dech,
  ocas, uši, pastva se nedějí. Nepřejmenováno (přidalo by pohyb hlavy) – rozhodnout zvlášť.
- **Sedlo zapuštěné z boku:** sedadlo koně (obal Saddle1) bylo 5 cm vedle osy hřbetu → napříč na kost `sedlo_kost`; síť
  sedla Balt Horse je v glb natočená o −15,1° kolem svislé (rovina souměrnosti, median 0,2 mm), hra ji dávala jen
  o 180° → šikmo. `vystroj.sedlo_otoceni_st` 15,1. Test průrazu (`tools/test_kun_klid.gd`, radiální průřez trupu) dál
  hlásí nesouměrnost (levý bok hlouběji) – možná metrika (čabraka u břicha), možná podélný sklon sedla (neměřen).
  **Zbývá:** snímky sedla z obou boků (`--write-movie`) neudělány (šetření limitu 6. 11.) – NEOVĚŘENO SNÍMKEM.
- Test `tools/beh.sh kunklid cmd godot --headless --path . -s res://tools/test_kun_klid.gd` (bez světa, ~1 min;
  `TVRZ_KLID_STARE=1` = staré chování pro srovnání): staré 6 hození hlavou / 3 vzpínání / 4 skoky očí za 56 s.

### Ubytovna, kuchyně, lůžka pryč ze síně (Míša 6. 11., řádky 64–66 tabulky, pomocník 9. 11.)
- **Ubytovna služebnictva** (snímky `docs/screens/misa_6_11/42–43`: z nádvoří k bráně je „vlevo“ jihovýchodní kout):
  záznam `pravidla/svet/lokace.json ubytovna_tvrz` → `blender/hospodar.py quarters` (stejná stavba jako zbrojnice:
  omítnuté zdi, kamenné ostění dveří, 2 okna s mříží, prkenná podlaha 0,04, pultová šindelová střecha; zadní a východní
  stěna = hradby; střecha má kolizi, aby `svet.tvrz_kryti` věděl o střeše bez dalšího natvrdo čísla). Pohyblivé dveře
  `kit.doorway` (jméno `Pohyb_dvereN` podle pořadí stavby), místnost `ubytovna` s názvem z dat (`mistnosti.title`;
  `svet._info` nově předává title i tvrzi), portály v `scripts/portaly.gd` ze záznamu, `yard.BLOCKED` = půdorys (bez
  dlažby, slámy, rostlin), kupka sena posunuta před ubytovnu na z 7,4.
- **Kuchyně** = bývalá spíž (snímek 45): `lokace.json kuchyne_tvrz` → `palace.kitchen_hearth` (ohniště s chlebovou pecí
  `vesnice.hearth` jako v chalupách – hotové z našich dílů, kapuce/digestoř a průduch v rohu přes komnatu nad střechu,
  kouř), dveře do síně `kit.doorway vnitrni` v příčce (pohyblivé). Místnost `spiz` přejmenována na `kuchyne` (export,
  portály). Vybavení: props (sudy, police se zásobami, pytle, byliny) + katalog v `nabytek.json svet` (`stul_selsky`,
  `kotlik_trojnozka` nad ohněm, hrnce, miska, bochník, nože). Hledáno hotové: katalog `modely/predmety.json` (kotlík,
  ohniště, stůl, hrnce – použito), ohniště s pecí z `vesnice.py`; vlastní jen kapuce a průduch (jednoduché tvary).
- **Lůžka:** síň bez lůžek (`nabytek.json bez_luzek: ["sin"]`, hlídá `svet.luzka_bez_luzek` – push_error při stavbě –
  a test `lide_chovani` bod 8). Ubytovna: purkrabí, písař, páže, strážný (+ noční na směny), čeledín; kuchyně: kuchařka
  Ludmila (úzké lůžko u ohně) a děvečka Kateřina (slamník u dveří) – v tvrzi spávala kuchyňská čeleď u ohniště, ženy mimo
  mužskou ubytovnu; kovář zůstává u výhně. `postavy.json`: místa `tvrz_ubytovna`, `tvrz_kuchyne_dvor` (spánek –
  nejbližší dveře), `tvrz_kuchyne` (kuchařka vaří: činnost `vareni`, dveře `Pohyb_dvere8` ze dvora).
- **Past (pro pomocníka lide.gd):** `lide._mistnost_u` bere `pos` místnosti jako střed; místnosti tvrze (export
  `ROOMS`) mají `pos` = roh (svet._info je dělá jako AABB od rohu) → pro tvrz vrací špatnou místnost. Test bez lůžek
  proto počítá vlastní funkcí `svet.luzka_bez_luzek`.
- **Disk 9. 11.:** 847 MB volných < `export_volno_mb` 1000 → smazány jen stažené zipy ambientCG v
  `blender/tex_cache/listy/zip/` (Leaf001–003, LeafSet009, LeafSet010, ~250 MB), jejichž obsah je rozbalený vedle
  (`listy/<jméno>/`); zipy L001–L024 (nerozbalené) zůstaly. Další úklid: viz výše (mesa cache, build/packs).
- **Náhled bez Godotu:** `blender/scene.sky` padá v Blenderu 4.2 (`MULTIPLE_SCATTERING` není) a Eevee nemá EGL →
  rychlý náhled Cycles 10 vzorků bez terénu (`build.build(["fort","palace","yard"])`, ~3 min) – pohledy 19–21 v `build.py`.
- **Ověřeno 9. 11.:** export `tools/export.sh` OK (test smyslu před i po, 1348 s); dveře `Pohyb_dvere9` = kuchyně↔síň,
  `Pohyb_dvere14` = ubytovna (dveře 10–13 posunuty o 1, nikdo se na ně jménem neodkazuje). Test `lide_chovani`
  (běh ub_t): 9 obyvatel tvrze má lůžko (ubytovna 5 + noční na směny, kuchyně 2, kovárna 1), nábytek 48 kusů / 40 dojití
  od dveří, žádná chyba lůžek ani síně; zbylých 9 chyb = chůze ke bráně `nadvori_brana` (známé, pomocník lide.gd).
  `stavby_na_zemi` OK. Snímky `docs/screens/ubytovna_9_11/` (ub_ven 10 h, ub_noc 22 h – spící na lůžku, kuchyne 10 h –
  Ludmila vaří u kotlíku, sin_zapad – síň bez lůžek, zavřené dveře do kuchyně). Vydání: `--jen z_svet,z_rostliny`
  (export změnil svet.json, tvrz.glb a rostliny/divoka_trava.glb).
- **NEOVĚŘENO:** dveře ubytovny na snímku ub_ven černý otvor (křídlo otevřené postavou, nebo chybí – ověřit ve hře);
  světlý pruh na střeše ubytovny u okapu (pozednice?); zvuk kroků v ubytovně kamenný (life.gd WOOD_FLOOR ji nezná – life.gd
  jen jiný pomocník); výkon na tabletu (+1 oheň s pochodní v kuchyni, +1 louč v ubytovně).
- **Disk 9. 11.:** po exportu ubytovny zbylo 946 MB. Smazáno: 287 sirotků v `.godot/imported` (143 MB, stejný skript jako 5. 11.,
  `.md5` ponechány) a `blender/tex_cache/models/pine_tree_01/pine_tree_01.bin` (949 MB; model je ve `veg.py SKIP`,
  nikde se nepoužívá, Poly Haven ho `textures.py` případně stáhne znovu). Export potřebuje ≥ 1 GB volna.

### Výkon 9. 11.: záseky lide a predmety, světla bez stínů, plný obraz (pomocník, řádky 74–76)
- **lide (r. 74, POTVRZENO na PC):** A* mřížky chůze (`lide._nav_cesta`) běžel synchronně. Test `lide_zasek` (všechny
  postavy změní blok v jednom snímku v 6:01 a 18:01, prázdná paměť mřížky): PC před 843–974 ms v jednom snímku – skoro
  celé jedna cesta: purkrabí (11,8) → `nadvori_brana` (-3,14), 14 463 sond, cesta neexistuje → `_nav_nouze` (rovně).
  Oprava (jen mřížka/_cesta/_process): rozpočet `postavy.json graf.mrizka` `sondy_snimek` 48 / `cas_ms_snimek` 2 (čas od
  první sondy snímku), kontrolní body na začátku, v každé buňce A* a v přímé/zkracovací kontrole `_nav_volno`; stav A*
  `_nav_rozpr`, hotové úseky `_nav_hotove` (maže se, když nikdo nečeká), neprůchozí dvojice buněk `_nav_nelze` trvale.
  Požadavek `c.ceka` (`_pozadej` / `_dopocitej`), čekající postava stojí (Idle), fronta `_nav_fronta` se střídá.
  Po: nejdelší snímek 9,2 ms (z toho 5–8 ms změna bloku 32 postav bez hledání), cesty za 1–25 snímků, purkrabí 572.
  Cesty s rozpočtem = bez rozpočtu (6/7, sedmá jiná kvůli mezitím otevřeným dveřím, bez nárazu).
  **Zbývá:** k bráně nádvoří (-3,14) mřížka cestu nenajde (test lide_chovani 7c CHYBA 9 – už před touto změnou).
  Testy s celým světem: `TVRZ_TEST_LIMIT=1200` (stavba ~4 min, výchozích 300 s nestačí).
- **predmety (r. 75, NAMĚŘENO na PC):** ne svícny – `_vnitrek_krok`. Režim vnitřku přeskakoval při otáčení (okno v záběru /
  mimo), každá změna odkryla celý svět a začala průchod 20 000 uzlů; čas jen po 64 uzlech. `rozpocty.json predmety_vnitrek`
  (1 ms, kontrola po 8 uzlech, zúžení až po 2 s stálé změny). Test `predmety_cas`: 4,47 → 1,07–1,75 ms nejdelší (jeden běh 5,03 ms, nevysvětleno), průměr 1,18 → 0,29–0,30.
- **Světla ohně na tabletu bez stínu** (`kvalita.json stiny_svetel`), **3D 100 %** (`kvalita.json meritko_3d`, tablet
  1,0 ve všech kvalitách), **automatika** až po 10 oknech (25 s) nad 33,3 ms (`dolu_*_podil` 1,0) nebo teplem.
  Měřicí trasa: vše / bez_postav / vše / auto. Vše NEOVĚŘENO NA TABLETU.
- Disk 9. 11.: 390 MB volných → úklid podle seznamu (build/packs, APK, mesa a shader cache, staré logy, npm cache,
  shader_cache ve scratchpadu) → 856 MB. `/root/tmpl_x` (73 MB, rozbalená šablona 21. 10.) agent smazat nesměl.

## Míša 6. 11., řádky 49, 55, 56, 60, 62, 67–69 (pomocník 9. 11.)
- **Sedlo (r. 62, nový rozbor po 2 opravách):** potvrzená příčina z testu – sedlo bylo usazené v klidové póze na uzlu koně,
  animace posouvají trup napříč o 4–6 cm (osa trupu v pózách 0,036 / −0,012 / −0,003, sedlo pevně 0,052). Natočení 15°
  (glb) bylo správně, příčinu neřešilo. `kun.gd _sedlo_s_kosti`: sedlo i bod sedla jezdce jdou s pózou kosti `sedlo_kost`
  proti klidu; `jizda.json kun.sedlo_napric` (osa trupu). Test `test_kun_klid` „sedlo napric“ ≤ 5 mm ve stání/kroku/cvalu.
  Snímky bez světa: `tools/foto_sedlo.gd` (render, 15 s) → `docs/screens/sedlo_9_11/`. Starý radiální průraz pořád hlásí
  hloubky 0,1–0,5 m (čabraka a podbřišník kolem břicha – metrika, ne chyba); skok očí jezdce max 0,053 m (mez 0,06).
- **Sada `tools/test_stavby.gd`** (vedle test_svet.gd, ten patří jinému pomocníkovi): spouští ji dev_test.gd po test_svet
  se stejným `TVRZ_TEST_JEN`: `co_je` (diagnostika `TVRZ_BODY`, `TVRZ_CO_JE_KRATCE=1` = jen povrchy nad bodem), `klobouky`,
  `schody`, `zebriky_jeden`, `opreny_o_zed`, `dil_na_teren`. **Past:** headless (dummy renderer) vrací u MultiMesh
  transformace instancí nulové – rostliny, houby a předměty v MultiMesh test bez renderu nevidí (klobouky, deska).
- **Mlýn – dva žebříky (r. 55):** model má vlastní žebřík v síni (Mlyn_Interier), hra přidávala katalogový; záznam
  `voda.json mlyn.dil.zebrik` teď na žebříku modelu, `zebrik_v_modelu`.
- **„Plůtek“ u mlýna (r. 56):** obruba cesty `Mlyn_Cesta` z modelu zapadlá pod terén modelu (mřížka 1 m) – rozpor uvnitř
  modelu z Disku. `mlyn.dil.na_teren_dilu` + `pasma.dil_na_teren`, `svet.gd _dil_kusy_na_teren` (jen nahoru).
- **Metla (r. 68):** kus `"o_zed"` v `nabytek.json domy` a `o_zed` v záznamu exportu (`blender/vesnice.py _put`) = opřený
  o zeď (`pasma.predmet.o_zed_uhel_st`). Metla v krčmě (svet.json) až po exportu.
- **Schody větrného mlýna (r. 69):** 56° klín → stupeň 0,13 m < poloměr kapsle 0,28 → svah nad floor_max_angle; chůze
  nefunguje ani nahoru. Schody nad `hrac.json schody_zebrik_nad_st` = žebříkové schody (záznam použití jako žebřík).
- **Past 9. 11. (export zabitý nástrojem):** `tools/beh.sh … export.sh` pouštěný přes Bash `run_in_background` bez
  `timeout` skončil po 30 min (výchozí limit nástroje, počítá i čekání na zámek) uprostřed Blenderu – nic se nezapsalo,
  `build/export_stav.json` zůstal BEZI. Export a dlouhé běhy: vždy `timeout` 7200000 (max), BEH_LIMIT=7000.
- **Export 9. 11. 07:20 OK** (`tools/export.sh`, test smyslu před i po, 1557 s): svet.json má 12 záznamů `o_zed` (metly,
  hrábě/vidle/lopata), tvrz.glb s úpravou hospodar.py (vrch zdi ubytovny pod střechou). Vydání: `--jen z_svet,z_rostliny`.
  Test `opreny_o_zed` po exportu NEOVĚŘEN (zámek Godotu 30 min obsazený jiným pomocníkem); před exportem 8/9 OK.
- **Nevyřešeno:** r. 49 deska (na 310,719 není – PC i TVRZ_MOBIL snímek), r. 60 stodola usedlosti 7 (445,914) – podezření
  rozpor #21 (vybavení dvorce se po úpravě terénu u toku neusazuje; stodoly/kůlny nejsou v `_domy` ani v `stavby_na_zemi`),
  sonda terénu pod stodolou nestihnuta; r. 67 klobouky – místo neznámé (snímek bez HUD), MultiMesh headless nevidět.

### Postavy 9. 11.: brána, rozestup, lom, hospoda, záhony (pomocník lide.gd, řádky 46–48, 57, 63, 71)
- **Brána nádvoří (ř. 46/63, POTVRZENO z dat):** `postavy.json mista.nadvori_brana` (-3,14) leželo uvnitř západní zdi
  brány (kolize stred (−2,55; 13,25), 1,9 × 7,5 m → x −3,5..−1,6, z 9,5..17). Mřížka cestu nenašla, `_nav_nouze`
  vrátila rovnou čáru ze sítě cest za mostem (0; 28,5) → nosiči vědra šli pod padacím mostem a zdí (snímek misa_6_11/41).
  Teď (0; 7,8) před mříží na straně nádvoří. `lide._mistnost_u` nebyla příčinou, ale je opravená (bere `svet.info.rooms`:
  tvrz AABB od rohu, ves/hostinec střed + inv).
- **Bez nouzové čáry:** `_nav_nouze` vrací prázdnou cestu (`_nav_bez`), celý výsledek `_cesta` je prázdný (i když selže
  jen úsek k síti) → postava stojí a dělá činnost na místě; další blok / bod obchůzky zkusí znovu.
- **Rozestup (`postavy.json rozestup`):** cíl do `misto_m` od cíle jiné postavy se posune (kruh, průchozí buňka);
  při chůzi postava čeká za postavou před sebou (kužel 60°, `chuze_m`, nejvýš `cekani_max_s`; na toho, kdo čeká na ni,
  nečeká). Obchůzka začíná místem bloku (dřív všichni od prvního bodu).
- **Místa u předmětů (`u_predmetu`):** záhon = nejbližší `zahon_*` k bodu zahrady, střed delší strany + `od_m`, rezervace
  (sedlák a selka u různých záhonů); hospoda = čelo stolu (`mista.hostinec_stul_N`: `u_predmetu`, `mistnost`, `poradi`).
  Nová činnost `obsluha_hostinec` (obchůzka místo obsluhy ↔ stoly) pro hostinského (9–12, 13–16, 17,5–23) a šenkýřku.
- **Lom (ř. 48):** `mista.lom_stena_z` (955, 962 – mimo lešení z 911–950,5; pod podlahou lešení nad hlavou místo není)
  → líc stěny paprskem z dna lomu (pata `svet.lom_stena_x` + `lom.hledat_m`, výška `ruce_m`, k západu; viditelná stěna
  ≠ pata sítě terénu – první pokus s `od_paty_m` dal skálu mimo dosah), `od_steny_m` před lícem, volno nad hlavou
  `volno_nad_m`, průchozí buňka (posuny `posun_z_m`), čelem ke stěně. Snímky `docs/screens/postavy_9_11/lom1d.jpg`, `lom2d.jpg`.
- **Testy:** `lide_chovani` 7c nově hlásí nenalezenou cestu; `_mista_prace` (každé místo s `p` má do `cil_m` průchozí
  buňku, lom: paprsek z výšky rukou do `dosah_m` narazí do skály, záhon: do `od_m` od okraje a dva lidé ≥ `misto_m`,
  obsluha hostince, rozestup tří cílů); nový test `interier_trsy` (skutečné instance MultiMeshů Louka/Rostliny v půdorysu
  místností u hostince a tvrze). `lide_zasek` (lid6) po opravě brány: nejdelší snímek s rozpočtem 5,1–5,8 ms (před 9,2; purkrabí už cestu najde,
  761 sond místo 16 188).
- **Tráva v hostinci (ř. 57):** na PC (lid2) `interier_trsy` 169 093 instancí v okolí, 0 v místnostech; Blender rostliny
  `svet.json rostliny` v půdorysu místností hostince 0. Na tabletu NEOVĚŘENO – pokud tam tráva je, příčina mimo současná
  data (starý balík louka / svět?).
- **Nezačato:** úchop podle klipu (ř. 47: kopí při chůzi, vědro, košík; krumpáč obouruč).
- **Snímky** `docs/screens/postavy_9_11/`: brana_purkrabi (7,5 h u mříže), nosi/nosi2 (vědra na nádvoří, dva vedle sebe ~0,6 m),
  hospoda_sin1 (10 h hostinský u čela stolu), hospoda_sin2 (19,5 h hosté sedí, šenkýřka mezi stoly), zahon/zahon_b (sedlák
  a selka u různých záhonů), lom1d/lom2d. Vydání: jen kód a `pravidla/svet/postavy.json` (žádný datový balík).
- **NEOVĚŘENO:** vyhýbání v protisměru (jen čekání, po `cekani_max_s` projdou sebou); postava bez cesty stojí na místě
  minulé činnosti (může vypadat jako „nic nedělá“); výkon na tabletu; tráva v hostinci na tabletu.

### Stavby, předměty, rostliny 9. 11. odpoledne (pomocník; řádky 60/77, 67/78, 80, 49, 56, staré řádky, hříva, slepice)
- **Stodola 7 na patkách (ř. 60/77, POTVRZENO z dat):** v exportu leží terén pod stodolou usedlosti 7 (445,914) 0,3–1,9 m
  pod její výškou (`trava_ves` ze svet.json proti `p.y` stodoly; ostatní stodoly a kůlny 0,00–0,05). Příčina: placka
  stavby (`vesnice._pads`, krok budovy) se počítá z terénu bez vody, pak `kraj.voda_tvar` (krok voda, až po stavbách)
  stáhne dolinu odtoku Lhoty (pas 21 m od osy) pod profil hladina + 0,3 + 0,25 × vzdálenost – stodola stála 4 m od osy
  (koryto + břeh 3,3 m), profil 1 m pod plackou. Pravidlo: pozdější krok nehýbe dřívějším → `kraj.stavba_dolina_vaha`
  a `svet.stavba_dolina_vaha` (váha doliny 0 v placce, k 1 za `pasma.budova.placka_prechod_m`), placka + přechod nesmí
  do koryta a břehu: `tools/ves_dvorce.py` (volba stodoly `u_toku` před sklonem) → usedlost 7 malá stodola zrcadleně
  (446,9; 902,7), kůlna (444,2; 910,8); test smyslu `dvorec` (pudorys v záznamu `stavby`, 6. pole); hra test
  `stavby_vse_na_zemi` (tools/test_stavby.gd: spodek každé pevné stavby katalogu ≤ `pasma.budova.na_zemi_m` nad terénem).
  **Platí až po exportu** (Blender: placka, poloha stodoly). `pasma.budova.placka_okraj_m/prechod_m` čte i Blender
  (dřív 0,6 a 2,5 natvrdo ve `vesnice.py`).
- **Slepice ve zdi (kontrola 9. 11.):** nocleh dvora bez kurníku ležel přesně v líci zdi (`-hw`); teď
  `zvirata.json nocleh_od_zdi_m` před lícem. Test `nocleh_pred_zdi` (koule těla 0,2 m bez kolize zdi).
- **Hříva v hrušce sedla (kontrola 9. 11.):** `kun.gd _hriva_pred_sedlem` – trojúhelníky hřívy (`jizda.json kun.hriva_sit`)
  za přední hranou hrušky sedla vystroje minus `hriva_pred_hruskou_m` se při načtení vynechají; test `test_kun_klid`
  „hriva v sedle“ (vrcholy hřívy v obalu hrušky v pózách stání/krok/cval), `TVRZ_HRIVA_CELA=1` = stav před opravou.

- **Večer 9. 11. (další pomocník staveb, předchozí zanikl při restartu):**
  - **Krtince = „hnědé klobouky“ / „černá placka“ (ř. 67/78, POTVRZENO):** `blender/vesnice.py molehills` stavěl 25 polokoulí
    z hlíny 0,7–1,2 × 0,19 m do sítě `Vesnice` (jedna přesně na 505,898 ze snímku 07). Nalezeno novým nástrojem:
    `co_je` s pixely – bod `x,z,ox,oz,vyska_oka,px,py[,px,py…]` (podíl šířky/výšky snímku) → paprsek z kamery proti
    trojúhelníkům všech sítí i instancí MultiMesh (s renderem), vypíše nejbližší zásahy s bodem a materiálem. Krtince pryč
    (nerovnosti patří terénu), kontrola `test_smyslu.py --po` **krtinec** (`pasma.test.krtinec_*`, souvislé kusy sítě
    s materiálem hlíny ≤ 2 m a ≥ 0,1 m vysoké). Dnešní export: 25 chyb → **po exportu musí být 0**.
  - **Podezdívka stodol a kůlny (ř. 77):** model (`blender/vlastni.py stodola, kolna`) stál na patkách s mezerou 0,25 m
    i na rovině. Teď souvislá podezdívka (`pasma.budova.podezdivka_*`), kůlna vpředu dál sloupy na patkách. Přestavba:
    `cd blender && /opt/bl/bin/python predmety.py build stodola stodola_mala kolna` (segfault na konci = normální) a
    `/opt/bl/bin/python -I blender/lod_barvy.py modely/predmety/{stodola,stodola_mala,kolna}.glb`, pak `--import`.
    Modely jsou mimo git (`modely/` v .gitignore) – katalog je vstup otisku exportu → **export**, vydání `z_katalog` + p_*.
  - **Listí jabloní (ř. 80):** listí stromů a keřů shaderem `listi` podle `pasma.skupiny` (strom/ker), ne jen `LISTNACE`;
    LOD materiál s příponou `.001` se páruje bez ní (jablon_daleko zůstával BLEND).
  - **Slepice ve zdi (kontrola):** zmizet u holé zdi (i 0,45 m před lícem) je nesmysl → každý dvůr se slepicemi má kurník
    (`zvirata.json dvory.kurnik`), test `nocleh_pred_zdi`: 5 v kurníku, 0 u zdi (OK).
  - **Hříva v sedle:** `test_kun_klid` „hriva v sedle“ OK ve stání/kroku/cvalu, snímek `docs/screens/stavby_9_11/hriva_krok_levy.jpg`.
  - **Zámek Godotu:** testovací/fotící řetěz `cmd bash build/beh/….sh` pouštět s `BEH_SDILENE=1` (viz „Souběžné běhy Godotu“);
    při rc 3 (zámek obsazený) opakovat ve smyčce na pozadí.
  - **Po exportu 9. 11. 18:07 (ověřeno 10. 11.):** `test_smyslu --po` souhrn OK, `krtinec` 0 (před 25); hra (stav3):
    `stavby_vse_na_zemi` 0 chyb (stodola 7 už ne 1,27 m), `zasazeni` 0, `mlyn`, `most`, `slepice_noc`, `schody`,
    `zebriky_jeden`, `opreny_o_zed`, `dil_na_teren`, `nocleh_pred_zdi` OK; `site_natazene` 36 (viz tabulka ř. 28 – podezření
    na dlouhé plochy prken/šindele 17,8 m, ne natažení). Snímky po exportu (krtinec, sad, stodola 7) NEOVĚŘENO – běh
    `build/beh/stav4.sh` nespuštěn: disk 790 MB < 800 MB (úklid čeká na schválení).
  - **Pozor na „Rozpracovane: prubezny stav“ commity:** jiný pomocník commituje `git add -A` i cizí rozpracované soubory.

### Tělo hráče a postavy 9. 11. (pomocník animací; ř. 47, 59, 73, 82, 83, 85, lom a hospoda z kontroly snímků)
Míša 9. 11.: „animace postav a hlavně hráče maximálně dokonale, KCD kvalita“. Rešerše: KCD/KCD2 = skutečná první osoba
(celé tělo, kamera v hlavě, ruce a nesený předmět v záběru, mocap); Godot 4.4: `SkeletonModifier3D` (vlastní modifikátor
po animaci, před `BoneAttachment3D`), `LookAtModifier3D` (už u postav), IK nohou ve 4.4 není hotové (SkeletonIK3D zastaralé)
→ vlastní dvoukloubová IK v modifikátoru. Pořadí vylepšení podle přínosu: (1) ruka s loučí v záběru (ř. 73),
(2) předměty v rukou podle dat ve všech klipech (ř. 47, 83), (3) spánek vleže (ř. 59, 85), (4) sezení čelem ke stolu (ř. 82),
(5) kroky bez klouzání – body prolnutí a tempo z naměřené rychlosti klipů (`test_klipy_chuze`), (6) otáčení na místě
klipem `Otocka` místo smyku, (7) chodidla na terén/schody (IK nohou v modifikátoru), (8) přechody lehání/vstávání.

- **Stav 9. 11. večer (druhý pomocník těla):** ověřeno během telo_v1: `lide_chovani` OK (sed u stolu čelem, obsluha ≥ 0,6 m
  od sedáku), `spanek_hra` – 4/4 spáči v ubytovně leží; zbylé chyby „stojí nad lůžkem“ = lůžka ubytovny z nových pravidel
  stojí na nádvoří, dokud neproběhne export ubytovny (zdi z exportu 07:14). Snímek hospody `build/ftelo2/hospoda1.png`.
- **Kovář „křeč“ (ř. 83) – příčina:** `Prace_Kovar_Loop` bylo CMU 62_07 „hammering a nail“ (předklon, ruka se hýbe o 5 cm).
  Teď CMU 79_01 „chopping wood“ (úder obouruč shora) s perlíkem; stejný úder `Prace_Uder_Loop` pro krumpáč (lom) a sekeru –
  `TreeChopping_Loop` z UAL je sek JEDNOU rukou (ruce 0,94–1,23 m od sebe), druhá ruka na topůrko nedosáhne. Index CMU:
  `github.com/una-dinosauria/cmu-mocap` `cmu-mocap-index-text.txt` (79_04 digging – kandidát na kopání).
- **Obouruční nástroj:** mocap CMU nemá natočení dlaní → nástroj podle zápěstí měl při úderu hlavu nahoru. `uchop.gd`:
  násada vede přes obě ruce klipu, ostří (`drzeni.<id>.ostri_osa`) v rovině švihu. V 79_01 je pravá ruka horní.
- **Otěže (ř. 86) – příčina:** síť uzdečky je skinovaná, vrcholy v soustavě vazby, ne kostry → pás u udidla prázdný.
  Oprava přes Skin (klid kosti × inverzní vazba); rychlý test `tools/test_otezi.gd` (bez světa, s diagnostikou).
- **Stav 10. 11. 03:20:** `test_drzeni` – obouruční nástroje pořád druhá ruka 0,25–0,34 m od násady (IK druhé ruky v
  `uchop._ik` zjevně nepůsobí ani tam, kde je cíl v dosahu – NEVYŘEŠENO; reakce Yes/FoldArms s obouručním nástrojem
  nemají smysl → vyřadit reakce, když drží obouruční nástroj). Snímky `build/fdrz3/` (18:07, před orientací podle paží).
  `test_otezi` viz tabulka ř. 86. Běhy stojí na disku (787 MB < 800); můj log telo_v6 (47 MB smyčky chyb) zabalen gzip.
- **Louč (ř. 73):** při natažení se vysune rameno (`_ik_ruky`, `jizda.json telo.klicni_kost`), `test_telo_poza` 0 chyb.
- **Kroky bez klouzání:** NPC `chuze_klip_m_s` z měření (Walk 0,98, Carry 0,66; dřív 1,2/1,0 = klouzání 22/52 %).
  **Hráč NEOVĚŘENO / rozhodnutí:** chůze hráče 2,3 m/s × klip 0,98 m/s (134 %) – buď pomalejší chůze, nebo jiný klip.
- Nástroje: Blender rozbor klipu bez Godotu (poloha rukou a hlavy po snímcích) – rychlé ověření mocapu před importem.

### Ubytovna dopředu a sklepení pod věží (Míša 9. 11., r. 84 + zadání „sklepy jako Puchart“)
- **Ubytovna** prodloužena dopředu (`lokace.json ubytovna_tvrz zf` 9,0 → 7,0, místnost 6,8 × 6,4 m), přední řada lůžek
  u přední zdi: kovář, Ludmila, Kateřina (kuchyně a kovárna bez lůžek). Kupka sena na (12,5; 3,2). Hlídač
  `nabytek.json bez_luzek: [sin, kuchyne]` + `bez_luzek_budovy: [tvrz_kovarna, tvrz_kuchyne]` → `svet.luzka_bez_luzek`.
- **Sklepení pod věží** (`lokace.json sklep_tvrz`, `blender/sklep.py`, úpravy `fort.tower`): podle Puchartu
  (`puchart_hrad.sklep_A`) postup, ne kód – sklep se sudy a pytli pod věží (strop z trámů pod podlahou přízemí), průchod
  základem věže do klenuté chodby pod stájí se 3 kobkami (2 dveře s mříží, 1 dřevěné, kruh s řetězem), louče se světlem.
  Vstup: ve věži pod prvním ramenem schodu do patra (otvor v podlaze, zábradlí do místnosti), z podesty dolů na jih,
  14 stupňů 0,20/0,24 m. Světlá výška nad schody 2,12 m ≥ `pasma.budova.svetla_vyska_m` 2,0 (nové pásmo) – hlídá
  `sklep.kontrola` (chyba exportu), stejně jako „otvor v terénu jen v půdorysu věže“ (`otvor_terenu`, Teren i Nadvori
  vynechají plochy, které do něj zasahují; nad chodbou zem zůstává). Pod ramenem nahoru vypnutá plná kolize
  (`stairs(pod=False)`), základ věže už není plný kvádr. Dveře kobek `Pohyb_sklep_kobkaN` (lide.gd je nebere jako dveře domu).
  Místnosti `sklep` a `kobky` s názvem, portály (otvor schodů do `vez0`, průchod) → zavřená místnost (svět dál skrytý).
  Sudy, pytle, bedna, vědro = katalog v `nabytek.json svet` (budova `tvrz_sklep`). Test `sklep` (test_svet.gd): trasa
  dolů i nahoru po 0,2 m (podlaha bez díry, světlá výška), zem nad chodbou, kolize klenby = viditelná, hráč na schodech
  nepropadne. Náhledy Blender (Cycles) prohlédnuty: chodba, kobka, sklep, schody shora i zdola, přízemí věže.

## Voda 9. 11. – nový rozbor příčin (pomocník vody, řádky 51, 53, 54, 61, 79; Míša „kolikrát jsme to řešili“)
- **Bílý „led“ (r. 61, 79) – POTVRZENÁ příčina (izolovaný test `tools/foto_voda.gd`, hladina bez světa se skutečnou
  oblohou hry):** GL Compatibility nemá SSR ani odrazové sondy, engine odráží jen oblohu; stojatá voda ROUGHNESS 0,03 +
  fresnel → 1 při nízkém pohledu = celá hladina barvou obzoru. Naměřeno: jas hladiny / jas obzoru **1,00** (stará) →
  **0,56–0,61** (nová, ráno/poledne/odpoledne). Oprava: `voda.gdshader` – odražený paprsek pod `prostredi.json
  voda_odraz.obzor_okoli_st` (12°) odráží okolí (břeh, stromy; `okoli_rgb` jako ALBEDO, osvětlené enginem – v noci
  tmavne), nad ním obloha (SPECULAR × viditelnost nebe). `svet.voda_odraz()` nastaví všem vodám. Test `voda_odraz`
  (beh.sh … cmd xvfb-run … -s res://tools/foto_voda.gd, 20 s, bez zámku světa). Okřehek bez odrazu je teď zelený
  (dřív šedé skvrny) – NEOVĚŘENO na tabletu, jestli nepůsobí křiklavě (rybník tvrze, materiál `rybnik` okrehek 1).
- **Voda nad terénem, hliněný sráz (r. 61, 79) – POTVRZENÁ příčina (data):** odtoky byly naplánované po terénu bez
  rybníků: `lhota_odtok` začínal uprostřed hráze 1,56 m pod hladinou a 16 m vedl podél ní, `tvrz_odtok` 0,3 m od osy
  hráze 1,34 m pod hladinou. Blender (`kraj.voda_tvar` výpust) i hra (`_ryb_hraz_toky`) hráz prokopaly korytem i
  dolinou → díra v hrázi 145–185° (rybník tvrze) a příkop podél hráze (Lhota); hladina visela 0,5–1,6 m nad terénem
  (měřeno: profil `tvrz.glb` a test `breh_nadrzi` na exportu 07:20: visí až 1,64 m u (−168, −165)). Oprava:
  `tools/krok_b/odtok_za_hrazi.py --zapis` (osa začíná za vzdušnou patou hráze: −20 bodů Lhota, −8 tvrz), hráz se
  odtokem nikde nepřerušuje (kraj.py, svet.gd). Hladina rybníka tvrze po vrstevnici terénu (`kraj.ryb_hladina_r`: dřív
  přes korunu hráze na vzdušný svah). Testy: smysl `odtok_za_hrazi`, `breh_nadrze` (fort.land po obvodu – před
  opravou CHYBA prorva 0,16–0,39 m u výpusti, po OK); hra `breh_nadrzi` (`tools/test_voda.gd`, třetí sada v dev_test).
  **Platí až po exportu** (Blender terén) – na exportu 07:20 test hry pořád hlásí rybník tvrze.
- **Díl Lhota ve svahu, holý pás (r. 51, 79) – POTVRZENO měřením:** model má pevný okraj +0,30, svět na hraně čtverce
  −2…+4 m; `ryb_teren` stahoval svět v pásu 6 m na okraj (srázy 30–35°), model holý do +0,2 m (pás 3–4 m), louka bez
  trsů do +0,4 m nad hladinou. Teď `voda.json rybnik_lhota.breh`: model jen `model_m` 2 m od vody, dál svět omezený
  svahem 1:4 nahoru a `nasyp_svah` dolů, hrana dílu = svět (pás napojení se nepoužije), tráva a bahno podle vzdálenosti
  od vody (`svet.ryb_od_vody`, chamfer na mřížce vrcholů modelu 171×171) – holý jen `holy_breh_m`. Test hry
  `breh_nadrzi` na Lhotě: 176 bodů obvodu bez srázu a visení (mimo ústí přítoku).
- **Přítok končí před hladinou (r. 53, (536, 884)):** pás `Toky_voda` končil na kruhu 12 m, voda modelu 11,3–11,6 m.
  `rybnik_lhota.tok_konec_polomer_m` 11, hra pás v hladině dílu odřízne. Skalní koryto nad terénem = pás napojení
  (viz výše) – po změně hrana dílu = svět s korytem z Blenderu. Ověřit po exportu (test `rybnik_dil`).
- **Mlýn r. 54 – tráva bez trsů: POTVRZENÁ příčina (kryti.bin dekódován):** offline krytí louky (`louka._zasah`, paprsky
  shora → `modely/louka/kryti.bin`) bralo jako terén jen `Teren*`, `Nadvori`, `Rybnik_Teren`; paprsek na `Mlyn_Teren-col`
  = „střecha“ → celý díl mlýna (~40 × 40 m) zakrytý, trsy 0 (zůstala jen hladká zem; stejná chyba jako Rybnik_Teren 0.78).
  Oprava: seznam sítí terénu v datech `pravidla_sveta.json pasma.dil.teren_site` (+ Mlyn_Teren), nový `kryti.bin`
  (`TVRZ_ROZSEV=1`, balík `louka` – **po každém exportu se stavbami znovu**), test `dil_kryti` (bod trávy dílu zakrytý,
  ač nad ním je jen terén = chyba). Lhota v testu taky.
- **Mlýn r. 54 – ostré hrany břehu:** `_mlyn_teren_koryto` snižovalo jen vrcholy do 0,3 m od vody → sráz po 1 m mřížce
  modelu (koryto modelu má stěny 42°) a skála zem.gdshader. Teď břeh toku v dílu nejvýš `hladina + breh_m + tan(breh_max_st)·d`
  (`svet.breh_toku_max_y`, totéž `kraj.breh_toku_max_y` na hraně dílu v `mlyn_pad`, aby hrana dílu a pás napojení
  navázaly), kolize `Mlyn_Teren` se přestaví z upravené sítě (dřív zůstávala původní). Test `mlyn` měří sklon břehu
  v dílu (`MLYN breh_sraz`).
- **Pás napojení dílu – suché koryto (`voda_v_korytu` (585–587, 894), (627–629, 922–924)):** prolnutí k hraně dílu bralo
  výšku nejbližšího bodu hrany = břeh dílu (tok nevytéká kolmo) → v `kraj.voda_tvar` v pásu napojení uvnitř vody
  `h = min(h, bed)` (dno je záznam). Platí po exportu. Body u jezu (vtok náhonu, (623–625, 922)) test `voda_v_korytu`
  vynechává jako test smyslu a `dil_okraj` (jez = stavba).
- **Oprava 9. 11. 16:10 (Míša):** ubytovna ne dopředu, ale doprava – `ubytovna_tvrz` zf zpět 9,0, x0 6,2, `mistnosti`
  (komora čeledi x 6,8–9,6 s vlastními dveřmi: Ludmila, Kateřina, budova `tvrz_ubytovna_zeny`; čeledník x 10,2–17:
  muži vč. kováře), příčka x 9,6–10,2 (bývalá západní zeď), koryto pro koně na (7,1; 7,6), kupka sena zpět (14; 7,4).
  Náhled Blender prohlédnut (2 dveře, nároží, schodiště na hradbu volné).
- **NEOVĚŘENO (9. 11. večer):** export ubytovny + sklepa neproběhl – disk 959 MB < `export_volno_mb` 1000 a fronta
  zámku Godota (8 běhů). Smazat nepoužívané zipy `blender/tex_cache/listy/zip/L0*.zip` (nikde se nečtou, ~230 MB)
  mi bezpečnostní kontrola nedovolila – rozhodne člověk. Pak jednou `tools/beh.sh export_sk cmd bash tools/export.sh`,
  testy `sklep,lide_chovani,zasazeni,stavby_na_zemi` a snímky ubytovny (zvenku dveře, uvnitř) a sklepa ve hře.
- **Klenba sklepa (Míša 9. 11.):** trámy pryč, sklep pod věží má valenou klenbu (osa sever–jih, vrchol −0,45 pod
  kamennou podlahou přízemí, vzepětí 1,3; `sklep_tvrz.sklep.klenba`). Nad schody dolů výseč od `rez_x` −25,2: hrana
  klenby 2,01 m nad podlahou sklepa (`sklep.kontrola` ji hlídá vůči `svetla_vyska_m`), nad hranou zeď až pod podlahu
  přízemí, pod hranou kamenný pas (jen u ramene, u paty schodů se tudy chodí). Kolize všech kleneb (sklep, chodba,
  kobky) = deska nad každou ploškou oblouku (`sklep._klenba`). Test `sklep` kontroluje i kolizi v hřebeni klenby sklepa.
- **Hlídač statiky (ř. 87):** `blender/statika.py` – stavitelé zapisují nosné díly (`statika.dil(jméno, druh, roh, roh, dx)`,
  dutiny sklepa `statika.dutina`), `export_game.main` po stavbě volá `statika.kontrola(fort.land)`; pravidla
  `pravidla_sveta.json statika.nese` (co smí ležet na čem) a `tolerance_m`. Díl stojí na zemi, když je spodek u terénu
  a není nad dutinou; jinak potřebuje pod sebou / kolem sebe (vetknutí) díl povoleného druhu. Pokryto: tvrz (68 dílů).
  Zbývá: palác, kovárna/zbrojnice, stáj, ves, mlýn, hostinec (zapsat díly v jejich stavitelích).

## Souběžné běhy Godotu (9. 11. 18:30, Míša: „5 pomocníků čeká na jeden Godot“)
- `tools/beh.sh` testy a foto běží sdíleně, nejvýš `pasma.test.beh_soubezne` (2) najednou; `cmd` (export, import, vydání) výhradně a přednostně (značka `/tmp/godot_beh.vyhradne`).
- Řetěz, který jen pouští testy/focení přes `cmd bash build/beh/*.sh`: dát `BEH_SDILENE=1`, jinak zbytečně blokuje vše. Nikdy ne pro export/`--import`/vydání (píšou `.godot`).
- Čekání na zámek: `build/beh/cekani.log` (kdo, kolik s, které místo). Měřeno 9. 11. ps: jeden běh ~1,1 jádra, 2,5 GB RAM; stroj 4 jádra, 15 GB.
- **Jedna pracovní složka pro všechny pomocníky:** `git pull` nedělat (není co stahovat, všichni commitují tady), nikdy
  `--autostash`/`git stash` – rozpracované soubory jiných pomocníků se při vrácení slijí s konfliktními značkami
  (9. 11. 18:28: `kun.gd` a `postavy.json` se značkami <<<<<<< v commitu, rozbitý parse pro všechny). Commitovat jen
  vlastní soubory/hunky (`git apply --cached` s vybranými hunky).
  Přesná příčina 18:28 (pomocník les ř. 88): `git stash && git pull && git stash pop` ve chvíli, kdy průběžný snímek
  právě vše commitnul → `stash` neměl co uložit, `pop` vybalil **cizí starou skrýš** `10a07b8` (z 0.99993) a průběžný
  snímek a72a540 ji commitnul (postavy.json −2745 řádků, `lide.gd` padal na `sondy_snimek`). Opraveno f85ba5a + 3f14ef6 (oba soubory
  = a2c3bea; 20c8ecf sám obsahoval konfliktní značky). Skrýš `stash@{0}` je cizí, nesahat.

## Postřehy z Puchartu 9. 11. (celé: větev ccr-f2d32673-9fi7m5 `docs/POSTREHY_pro_havrana_9_11.md`)
- [hotovo] 1. hlídač `tools/kontrola_datovych_textur.py` (export krok 11) hlídá i obráceně: textura mimo `datove_textury.txt` bez mipmap / VRAM komprese = chyba. Stav 9. 11.: jediná taková `cesta_atlas_disp.png` je datová (čte ji jen CPU v `svet._disp_nacti`) → zapsána do seznamu.
- [hotovo, ověřit snímkem] 2. `zem.gdshader`: hash se sinem (čtverce po metru na Adreno) → `hash12/hash11` (Hoskins, mod 1024) u lomové stěny a vrstev skal. Zbývá `impostor.gdshader` (ve vertexu, highp – nižší riziko) a `listi.gdshader` (místní souřadnice – nízké riziko); GDScript na CPU (louka.gd, svet.gd) je v double, netýká se.
- 3.–4. projekce textur: pevné osy X/Z nebo světový triplanar, ne tečna z normály buňky; jeden materiál s hladkými normálami místo odstínů po malých plochách. Ověřit u `zem.gdshader` a skal, když se objeví čtverce/pixely.
- 5.–6. mosty: na most vede násyp cesty v terénu (žádné rampy/klíny jako záplata); násypy u mostů nevyhlazovat; výšku mostu držet z minulé stavby. Máme test `most` v test_smyslu (osa po mostovce); chybí obdoba Puchartových `nastup_mostu_v_terenu`, `nabeh_vyska`, `most_navazuje_na_cestu`. **ZBÝVÁ** (pomocník vody 9. 11. nestihl): do test_smyslu – (a) `nabeh_vyska`: `kraj.road_y` na konci mostovky (br[4]) = `kraj.deck_y` ± 0,1 m a podél nájezdu (`prechody.najezd_m`) sklon ≤ `pasma.cesta.vozova.podelny_max`; (b) `nastup_mostu_v_terenu`: terén po `kraj.flatten` na konci mostovky do 0,15 m pod povrchem cesty (násyp v terénu, žádný klín – hra `svet.najezd_y` dnes zvedá terén sama = záplata, sjednotit do Blenderu); (c) `most_navazuje_na_cestu` = dnešní kontrola `most` (osa na mostovce). Výšku mostovky (`deck_y`) zapsat do `cesty.json` záznamu mostu, ať se mezi stavbami neplíží.
- 7. štíty střech prkenné, kámen jen do okapu (KCD), prkenný štít s kolizí; nároží z nárožních kamenů – pro hospodar.py / fort (ubytovna, kovárna) a hlídač statiky ř. 87.
- 8. Python: komentář `#` doprostřed řádku seznamu zakomentuje zbytek řádku – komentář jen na konec.
- [hotovo] 9. `export.sh krok` zapisuje trvání do `build/beh/kroky_casy.log`; čekání na zámek `build/beh/cekani.log`; import jen při exportu.
- 10. k rešerši: gltfpack / glTF-Transform (zmenšení glb), xatlas + Cycles bake bez obrazovky (LightmapGI v Compatibility zapéct nejde), octahedral impostory (ověřit licenci), Terrain3D v Compatibility nejde.
- **Puchart bod 7 (štíty, nároží):** pravidlo zapsáno do `pravidla_sveta.json statika.stity` (kámen jen do okapu, štít
  nad okapem prkenný s kolizí, nároží z nárožních kamenů). Ubytovna má nároží `fort.quoins` (OK), ale boční zdi pod
  pultem (ubytovna, zbrojnice, kovárna) jsou kamenné až pod střechu – zbývá předělat na kámen do okapu + prkenný
  štít a zapnout kontrolu ve `statika.py`. Bod 8 (komentář jen na konec řádku): v sklep.py/statika.py/fort.py dodrženo.

## Tráva v lese podle světla (ř. 88 a 86, 10. 11., pomocník les; KCD `docs/screens/misa_9_11/18_kcd_les.png`)
- **Pravidlo** `pravidla/svet/les_podrost.json` (bez exportu – rozsev louky je za běhu):
  - zápoj = koruny VŠECH stromů po všech krocích sázení (`svet._koruny_stin`, poloměr z modelu) rozmazané přes
    `prechod_m` (plynulý přechod) × zápoj okolí (`okoli_m`, `okoli_od` 0,55 – `okoli_do` 0,9: samotný strom a řídký háj
    nejsou les) → `svet.zapoj_v`; `louka._svetlo_lesa`: pod `zapoj_od` tráva podle louky, v plném zápoji × `v_zapoji`
    0,015 (pod prahem rozsevu – žádný drn, vějíř ani trs louky), pruh světla u pěšin, skály `skaly_*`.
  - `podrost`: pod zápojem řídké kapradí, byliny a nízké trsy z atlasu trávy (`na_m2` 0,35 × zápoj) – místo trávy.
  - `puda`: `svet._puda_zapoj` doplní zápoj do kopie textury stanoviště pro `zem.gdshader` (lesní půda – listí,
    jehličí, písek, hrabanka s mechem, přechody šumem – plynule tam, kde louka ubírá trávu; prahy `les_od/les_do` z dat).
    Data masky `svet.stanoviste` se nemění.
- **Potvrzená příčina „tráva v lese všude“** (test `les_trava` před změnou): louka brala zápoj z masky stanoviště R+G
  (krok 5+7, jen stromy 6a) – 83 % bodů pod korunou mělo R+G < 0,6, v lesích měřicí trasy R+G = 0.
- **Druhý pokus (koordinátor 10. 11., lesA):** první verze (okolí 0,25–0,45, bez přechodu) brala řídký háj lesA jako les
  → holá hnědá „placka“ s ostrou hranou. Rozbor bodů v testu: háj má koruna 1,0 / okolí 0,56–0,59 → teď zápoj 0,05–0,19
  (tráva zůstává), les u (185, 888) okolí 0,70 → zápoj 0,84.
- **Test `les_trava` OK** (les_po4, 10. 11.): plný zápoj 8 101 bodů, hustota 0,013 (max 0,04), nad prahem rozsevu 0,0 %
  (max 10 %).
- **Měřeno na PC (xvfb; časy NEOVĚŘENO NA ZAŘÍZENÍ)**, snímky `build/les88/pred_les*.png` / `po3_les*.png` (prohlédnuto:
  lesA háj s trávou a plynulým přechodem, lesB pod korunami lesní půda a podrost, lesC beze změny – okraj háje):
  instance louky lesA 269 086 → 238 624, lesB 227 178 → 211 955, lesC 324 807 → 288 646 (−7 až −11 %); kreslení beze
  změny (436 / 688 / 449). Vypnutí louky ubere 60–76 kreslení, vypnutí stromů a keřů 164–295 → **na místech trasy jsou
  dražší stromy než tráva** (místa trasy jsou hlavně háj, kde tráva podle pravidla zůstává). Test, 9 buněk 96×96 m:
  les 161 432 → 145 437, kůň-les-mimo 134 475 → 128 246, kůň-les 171 082 → 155 567.
- **Měřicí trasa:** varianty `les_bez_travy` / `les_bez_korun` (Míša na tabletu: co v lese stojí víc; 6 průchodů ~20 min).
- **Focení lesa padá na LIMIT:** 3 snímky + `TVRZ_MERENI_AB=louka,rostliny` = 1935 s ve volném stroji, 2997 s při
  souběhu (zátěž 8–9 na 4 jádrech) → `BEH_LIMIT=4000` (beh.sh 0abd746 limit podle počtu snímků).
- Mezi „před“ (9. 11.) a „po“ proběhl export tvrze 9. 11. 18:00 (les se neměnil – NEOVĚŘENO).

## Disk pod 800 MB (10. 11. ráno) – příčina a úklid
- Stav: 741 MB volno, `beh.sh` nic nespustil, tři pomocníci stáli. Příčina: `.git` 11 GB, z toho **7 GB volných (loose)
  objektů** z častých commitů snímků a binárek; `git gc` nejde (potřebuje místo na nový pack).
- Úklid stavitel: `git prune-packed && git prune` (jen nedosažitelné objekty starší 2 týdnů), smazány staré pomocné složky
  snímků `build/f*` (vč. `build/ftelo2` – snímky hospody a louče od těla jsou pryč, pořídit znovu `telo_v3.sh`) a logy
  `build/beh` starší 1 dne > 200 kB → 928 MB.
- Aby se neopakovalo: snímky do repa jen JPG (ne PNG), pomocné snímky do `build/` a po prohlédnutí smazat;
  větší rezervu dá jen `git gc` – navrhnout Míšovi novou session (čerstvý klon má pack bez loose objektů).
- 10. 11. 04:10: `les_foto_po` (3 snímky) i `stav4` padly na LIMIT 2400 s – při 2 souběžných bězích a exportu trvá snímek
  9–15 min. Oprava: `beh.sh foto` bere limit `pasma.test.beh_limit_foto_zaklad_s + beh_limit_foto_snimek_s × počet`.
- **Snímky ze hry 10. 11.** (export 9. 11. 17:47, `docs/screens/sklep_10_11/`): chodba s klenbou a dveřmi kobek, kobka
  (dveře s nabídkou Otevřít), schody shora i zdola (klenba sklepa, pas výseče, sudy) – v pořádku. `sklep_klenba` tmavý,
  podlaha šedá (textura dlažby na PC). Ubytovna `ub_ven` – záběr míjí budovu (kamera k bráně), `ub_muzi/ub_zeny` ve 22 h
  téměř černé (jen louč) – **zopakovat ve 12 h a s kamerou na x 6–17**. Pozor: `TVRZ_MERENI` se 6 čísly bere y jako
  PATY hráče (oko +1,62) – ve sklepě y −2,8.
- **NEOVĚŘENO:** test `sklep` (10. 11.: watchdog – headless `fast_travel` visel na Tweenu → test bez něj, commit
  653847f; pak běh zastavila chyba parsování `scripts/otezi.gd` jiného pomocníka a rozbitý `tools/beh.sh` ř. 89).
  Nový export (voda dae7764, krtince 5261fa5, pravidla_sveta) čeká na disk ≥ 1000 MB (10. 11. 04:59: 947 MB).
- 10. 11. ~05:00: export potřebuje `export_volno_mb` 1000, bylo 944. Smazán osiřelý import cache v `.godot/imported`
  (908 souborů, 83 MB – zdrojový `.import` už neexistuje, hlavně smazané snímky z `build/`) → 1,1 GB. Příčina:
  `build/` nemá `.gdignore`, takže Godot importuje každý pomocný snímek. Zavedeno `build/.gdignore` (grep: nic nenačítá `res://build` přes load, jen FileAccess) –
  Godot pomocné snímky už neimportuje.
