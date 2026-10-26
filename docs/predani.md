# Předání – jediný vstup nového stavitele (20. 10. 2026, po vydání 0.58)

Projekt: Godot 4.4.1 hra „Odkaz Havrana“ (Čechy 1393: tvrz, ves, hostinec, skalní město; Android tablet Xiaomi Pad 8,
renderer Compatibility). Pracovní větev `claude/new-session-0dtk58`. **Repo je jediná paměť** – kontejner je dočasný.

## 1. Prostředí (nový kontejner, ~20 min)
```
bash tools/prostredi.sh        # Godot 4.4.1 + šablony Android, Blender 4.2 jako modul (/opt/bl/bin/python, bpy), Android SDK, pip, Waterways textury
bash tools/stahni_zdroje.sh    # herní data z balíků data/*.pck do modely/ a .godot/imported/ (jako je stahuje tablet)
bash tools/pregeneruj.sh       # textures/ + audio/ (procedurální – BEZ NICH APK nemá oheň ani zvuky), kryti.bin, potok, portály
python3 tools/vydani.py 0.NN   # vydání (jen na „VYDEJ“ od Míši)
```
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
