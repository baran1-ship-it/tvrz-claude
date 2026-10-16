# Postavy – jak se staví (Blender 5.2 jako python modul + MPFB2)

1. `char_build.py <jmeno> <pohlavi> <vek> [svaly] [vaha] [vyska]` – tělo MPFB2 (CC0), kostra game_engine (UE názvy),
   tvar obličeje z `faces.json`; prsa přes proměnné CUP/FIRM. Výstup `<jmeno>_base.blend`.
2. `head_build.py <jmeno>` – kůže (`skin_mat.py`, u ženy CC0 textura), obočí, strniště, vlasy jako slupka
   (`head_features.py`), u ženy cop + rozpuštěné, řasy (Mindfront CC0), barva očí (`eye_recolor.py`).
3. `outfit.py <jmeno> <kroj>` – oblečení ze slupek těla a trubek (`clothes.py`), hladký výstřih (`cut_iso`),
   procedurální látky (`cloth_mat.py`), zakryté tělo se odstraní.
4. `char_export.py <jmeno> <kroj> <out.glb>` – decimace (tělo 11,5k, oblečení 12,5k), zapečení 2K textur
   (barva, normal, ORM), sloučení do uzlů telo/obleceni/kapuce/vlasy(/cop/rozpustene), export glb.
5. Animace: `retarget.py` (Quaternius UAL1+2 CC0 -> kostra MPFB), `custom_anims.py` (otočky, louč, luk, ležení),
   `posture_fix.py` (srovnání sklonu páteře/hlavy po retargetu), `anim_export.py` -> animace.glb.
6. Kontrola: `glb_check.py <postava.glb> <animace.glb> <out.jpg> anim:snimek,...` (CLOSE=1 detail, NOHOOD=1 bez kapuce,
   LOOSE=1 žena s rozpuštěnými vlasy).
Celý běh: `run_final.sh` (stavba všech tří postav).
