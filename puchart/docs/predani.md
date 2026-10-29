# Předání – Puchart (stav 29. 10. 2026 večer)

## Hotovo (krok A podklady + základ D)
- Poloha: přední hrad N 49.611560 E 17.682476 (OSM ruins, atlas). Výsek 2×2 km (`svet.json`), obzor 10×9 km.
- DMR 5G: 31 mapových listů (`zdroje_dat.json`), hustota 0,076–0,09 bodu/m² (TIN klíčové body → efektivně ~3,6 m).
  Snímky: `docs/screens/00_*.png` (přehled, toky, ostroh, obzor).
- Toky z terénu (D8, `toky.py`): OSM leží 15 m vedle dna → osy z terénu, jména z OSM. `voda.json` v souřadnicích hry.
- Maska stanovišť (`stanoviste.py`, pravidla z Havrana plochy.json): louka 48 %, les 47 %, skála 2 %, břeh 3 %.
- Pečené dlaždice 250 m, LOD 2/4/8/16 m se sukní, obzor 40 m; kolize HeightMapShape3D jen kolem hráče.
- Godot 4.4.1 Compatibility projekt `hra/`: shader terénu (pole textur, 4 vzorkovače), panel měření, prozatímní hráč.
  Snímek `docs/screens/01_louka_k_hradu.png`: PC 33 kreslení, 0,36 M troj. (tablet NEOVERENO).
- Pravidla a tabulky Havrana převzaty (`docs/pravidla_prevzeti.md`), tabulka chyb `docs/chyby.md`.

## Další krok
1. Les (stromy Havrana: buk, jedle, dub, lípa, olše, vrba s _daleko verzemi) podle masky – chyba #1.
2. Návrhy hradů (`docs/hrady_zadani.md`) – ke schválení Míšou před stavbou.
3. Cesty výseku (plánovač sklonu), Boňkov (dvorce jako ves B Havrana), mlýny na Veličce.
4. Převést hlídače (test smyslu, matice vztahů, tabulka chyb) do `nastroje/`.

## Nový kontejner
`bash nastroje/postav_vse.sh` (Godot 4.4.1: `curl -L https://github.com/godotengine/godot/releases/download/4.4.1-stable/Godot_v4.4.1-stable_linux.x86_64.zip`).
