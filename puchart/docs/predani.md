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

## Hotovo 29. 10. večer (skutečná podoba místa)
- Biotopy AOPK + PPV + DMP 1G → stanoviště 1393 a 60 362 stromů (`docs/reference_mista.md`, `historie_vegetace.json`).
- Les ve hře: LOD0 do 22 m, vlastní LOD1 (30 % karet), karty dál; PC 1,83 M troj., 301 kreslení, VRAM 315 MB (tablet NEOVERENO).
- Godot/Terrain3D: `docs/godot_verze.md`.

## Hotovo 29. 10. noc (hrady, A/B)
- Plán atlasu zaměřen na DMR (`plan_atlas.py`, `plan_prekryv.py`): zadní hrad 47 m pod předním na V úbočí.
- Terénní úpravy valů a příkopů (`teren_upravy.py`, před pečením). Vyhlídka na protějším svahu (paseka).
- 4 návrhy hradu (`blender/hrady.py`, `hrady_navrhy.json`, `docs/hrady_navrhy.md`, snímky `docs/screens/hrad_*.jpg`).
- Terén ve hře ze souboru výšek ve vláknech (2,7 s na PC), sdílené textury stromů, byliny u hráče.
- A/B srovnání: měřicí trasa (`hra/scripts/mereni.gd`), APK B (4.7.2) a C (Terrain3D) – `docs/ab_srovnani.md`.
  Úspory APK: staré stromy zblízka LOD1, normály stromů 256, pole normál půdy 512, výšky r16z (roviny bajtů + zstd),
  bez auto-LOD a stínových sítí u modelů s vlastním LOD. Limit GitHubu 100 MB/soubor.

## Další krok
1. Les pod 1,5 M troj. (impostory skupin / menší LOD0 kmenů), modely javor/jasan/habr/jilm, podrost a kameny z droby.
2. Návrhy hradů (`docs/hrady_zadani.md`) – ke schválení Míšou před stavbou.
3. Cesty výseku (plánovač sklonu), Boňkov (dvorce jako ves B Havrana), mlýny na Veličce.
4. Převést hlídače (test smyslu, matice vztahů, tabulka chyb) do `nastroje/`.

## Nový kontejner
`bash nastroje/postav_vse.sh` (Godot 4.4.1: `curl -L https://github.com/godotengine/godot/releases/download/4.4.1-stable/Godot_v4.4.1-stable_linux.x86_64.zip`).
