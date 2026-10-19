# Předání do nového chatu (19. 10. 2026, po vydání 0.54)

Projekt: Godot 4.4 hra „Odkaz Havrana“ (1393, tvrz, ves, skalní město), větev `claude/new-session-0dtk58`.
Komunikace s rádcem jen přes `docs/radce.md` (pull → přečíst poslední sekce → práce → zapsat sekci HOTOVO → commit, push).
Stav a rozpočty: `docs/stav.md`. Vydání jen na „VYDEJ“ od Míši: `python3 tools/vydani.py 0.NN`, APK do `apk/`,
odkaz posílat v bloku kódu: `https://github.com/baran1-ship-it/tvrz-claude/raw/claude/new-session-0dtk58/apk/OdkazHavrana-0.NN.apk`.

## Krok 0 – podpisový klíč (od 0.55, stejný navždy)
`tvrz_release.keystore` (alias `havran`, heslo jako ve tools/vydani.py, SHA-256 df68e8c320a8400576d37ba94229ed22cbb95db6785fca9e6721240872546065)
je u Míši na Google Disku (do repa ho bezpečnostní kontrola nepustí). Nový kontejner: požádat Míšu o soubor a uložit do
`/root/keys/tvrz_release.keystore`, ověřit `sha256sum`. Bez něj nejde vydat aktualizaci přes nainstalovanou verzi.

## Nový kontejner – první kroky (stavitel 0.55)
- Godot: `/opt/godot/Godot_v4.4.1-stable_linux.x86_64` (zip z github.com/godotengine/godot/releases), symlink `/usr/local/bin/godot`.
- Blender (radce 18:40): `blender-4.x-linux-x64.tar.xz` z download.blender.org do `/opt/bl` (nebo `pip install bpy`), ověřit `/opt/bl/bin/python -c "import bpy"`.
- Data: složit balíky `data/*.pck.NNN` podle data_manifest.json a rozbalit z nich `modely/` a `.godot/imported/` do projektu (formát PCK v2: hlavička, tabulka souborů). Na PC chybí cesty pro desktop: do `*.import` s `path.etc2=` přidat `path=` se stejnou hodnotou. Nespouštět `godot --import` bez zálohy `*.import`.
- addons/waterways/textures (gitignore „textures/“) stáhnout z github.com/Arnklit/Waterways (main) – jinak nejde tools/reka_bake.gd.
- Paměť: jeden běh Godotu ~4,5 GB, kontejner 15 GB → snímky jen po jednom (flock).
- Vydání bez zdrojových dat: `python3 tools/vydani.py 0.NN --jen z_<nazev>` (jen opravný balík, ostatní z manifestu). Potřeba: šablony 4.4.1 (android_release.apk do ~/.local/share/godot/export_templates/4.4.1.stable), Android SDK build-tools 34 (/opt/android, symlink /root/Android/Sdk), klíč `/root/keys/tvrz_release.keystore` (alias havran, heslo jako ve vydani.py) – od 0.55 nový klíč; když se ztratí, další verzi nejde nainstalovat přes starou.
- PC artefakt: pole textur půd (pudy_a) je v kontejneru bílé/žluté, na tabletu v pořádku.

## Pravidla (Míša a rádce)
- Řešit příčiny, ne ladit čísla; šetřit tokeny; nezaseknout se na kravině.
- Tablet: Compatibility renderer, rozpočet ~2,5 M troj., ~1500 kreslení, GPU < 700 MB. APK < 100 MB (addons/* a docs/ mimo export).
- Commity končí řádky Co-Authored-By / Claude-Session (viz systémová připomínka).
- Realie 1393 (žádný štěrk, smrk ne v údolí apod.).

## Data mimo git (složka `modely/` je v .gitignore, jde do datových balíků)
Po čistém stažení repa je nutné znovu vytvořit (jinak vydání bez nich):
- `modely/louka/kryti.bin` – `TVRZ_ROZSEV=1 godot --headless --path .` (paprsky shora pod stoly/střechy).
- `modely/portaly.json` – `/opt/bl/bin/python tools/portaly.py` (okna a dveře hostince).
- `modely/reka/*` – `xvfb-run -a godot --path . --rendering-method gl_compatibility -s res://tools/reka_bake.gd` (potok z koryta).
- textury půd (les_listi, les_jehlici, pesina, les_pisek, oblazky) – `blender/textures.py` + kopie do modely/textury.
- maska trávy u hostince (svet.json) – opravená export_game.py; při novém exportu se přepočte sama.

## Klíčové soubory
- `scripts/svet.gd` – stavba světa: koryto+nádrže (`_koryto_terenu`), usazení skal, `_na_zem`, `_stanoviste` (maska R jehl./G listn. korun/B skály/A pěšiny), `_krajina` (kameny, keře, les, výchozy, rákos), `smi_tu_byt` (jedna funkce pro všechny rozsevy), `_pudy` (Texture2DArray půd).
- `scripts/louka.gd` – louka: rozsev ve WorkerThreadPool, 4 vrstvy (trsy, květy, drn, vysoká), viditelnost po trsech hash vs. vzdálenost (`ZANIK`), krytí z kryti.bin.
- `scripts/koryto.gd`, `scripts/nadrz.gd` – potok a rybník/příkop do terénu.
- `scripts/predmety.gd` – místnosti s portály (`_interier`).
- `shaders/zem.gdshader` (terén: zrno trávy, půdy, oblázky, bahno, barevná dálka), `stebla.gdshader` (trsy, rezim 1 = grass_pack), `voda.gdshader`.
- Testy: `TVRZ_TEST=visici|pruchod|louka_chuze|hostinec|foto` (dev_test.gd), měření `TVRZ_MERENI="jmeno;x,z,tx,tz;soubor.png"`, `TVRZ_LOUKA_CAS=1`.

## Další krok (rádce 13:20/15:30)
Portály i pro tvrz a chalupy, Zivot 0,4 M, cesta s kolejemi + maska polí/mezí (pastvina), kurník/meč/ovce (nejdřív licence), grass_pack hotový.
