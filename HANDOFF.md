# Tvrz – předávka do nového sezení

Projekt Godot 4.4.1 (Forward+), Android APK. Hra: průchozí tvrz (brána, nádvoří, hodovní síň s krbem,
spíž, komnata, ložnice, strážnice, kovárna, střelnice s lukem, věž, ochozy), denní doba, ohně, zvuky,
dotykové ovládání + Xbox ovladač.

## Struktura
- scripts/ – veškerý kód. Svět se staví při startu kódem (fort.gd, palace.gd, yard.gd, terrain.gd,
  flora.gd, props.gd, mesh_batch.gd). Hra: main.gd, player.gd, life.gd, bow.gd, hud.gd, pad.gd, daylight.gd.
- tools/gen_tex.py, tools/gen_snd.py – vygenerují textures/ a audio/ (nejsou v ZIPu, spusť je).
- tools/test.sh – automatický test (navigační síť, bot obejde 16 míst, luk, interakce, dotyk).
  TVRZ_TEST=pad … – test ovladače. tools/pshots.sh – snímky z pohledu hráče (xvfb + Vulkan lavapipe).
- export_presets.cfg – Android, arm64. Klíč pro podpis je potřeba vytvořit znovu (keystore/release).
- Textury se importují jako lossy WebP (1024 px barvy, 512 px normály/ORM), aby APK bylo < 30 MB.

## Hlášené chyby z tabletu (Xiaomi Pad 8), zatím neopravené
1. Luk se napne, ale nevystřelí (v testu se simulovaným dotykem střílí).
2. Kroky zní jako stroj (syntetické zvuky) – nahradit skutečnými nahrávkami.
3. Kamenná deska ve vchodech budov – sokl palace.gd (bb "stone" přes celou fasádu) vede přes dveře.
4. Trhaný obraz při chůzi – nejspíš fyzika 60 Hz vs. displej 120+ Hz; zapnout physics interpolation
   nebo vyhlazovat kameru v _process.
5. Vodorovné čárkované pruhy přes obraz ve stejné výšce – artefakt vykreslování na Adreno
   (vyzkoušet bez FSR, bez SSAO, případně renderer "mobile").
6. Úzké dveře v ložnici; jednou propadnutí do tmy (do zdi) – zkontrolovat kolize a step-up.

## Plán dál (domluveno s Míšou)
Zachovat rozvržení tvrze, ale modelovat části v Blenderu skriptem (bpy) – skutečné tvary, zkosené
trámy, nepravidelné zdivo; zapéct světlo (lightmapy/AO); fotografické CC0 textury, pokud je Míša dodá.
Začít bránou a kusem hradby, poslat snímky ke schválení, pak zbytek. APK > 30 MB doručovat
přes GitHub Releases v repozitáři baran1-ship-it/tvrz-claude.
Pravidlo: do Míšova projektu s GPT nezasahovat. Komunikace česky, tykání, stručně.
