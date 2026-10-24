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
Zdroj: Disk, `rybnik_lhota_v2.zip` → `rybnik.glb` + `NAVOD.md`. Díl 60×60 m, hladina y=0, okraj dílu y=+0,30 m; terén tůně,
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
