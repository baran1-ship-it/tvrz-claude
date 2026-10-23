# Modely od Míši – průchod `nove._import_sketchup`

Funkce (blender/nove.py): sloučení vrcholů 1 mm, normály ven, materiály podle klíčového slova na herní
fotografické materiály (UV v metrech), ostatní glb materiály bez lesku (drsnost 0,9, kov jen u kovu),
rovinná decimace 1°, strop trojúhelníků, textury ≤ 1024 (předměty 512). Ve hře svet.gd přiřadí herní
materiály podle názvu i statickým stavbám.

| Model | Soubor | Troj. před → po | Textury před → po | Materiály → herní |
|---|---|---|---|---|
| hostinec | stazene/medieval_tavern_interior.glb | 9 292 → 8 598 (stavba jen rovinné slučování; collapse na 4 000 zúžil dveře) | 8×, max 1024 → max 1024 | RoofTilesWood → sindel_hra, Wood → dub_ven, LogEdgeWeathered → drevo_rez; StoneWall (zdivo_hostinec), DarkStone, Brick, Sign, RustedMetal z glb bez lesku |

## Disk – stav 23. 10. 2026 21:40 (rádce)
- **Postavy/**: `Universal Base Characters[Standard].zip` (Quaternius CC0), `Modular Character Outfits - Fantasy[Standard].zip` (Quaternius CC0 – dobovou vhodnost každého kusu posoudit, „Fantasy“ je jen název balíku), `makehuman_system_assets_cc0.zip` (280 MB). **Chybí:** Quaternius *Universal Animation Library 1 + 2* (Standard, CC0) – klipy idle/chůze/běh/sezení/práce, kompatibilní s Base Characters → stáhnout pro POSTAVY.
- **horse.glb** (55 MB, 22. 10.): ověřit, zda má kostru a animace; velikost napovídá fotosken bez rigu → model pro stáj; pro jízdu (FUNKCE) rigovaný kůň (Quaternius Animals CC0).
- **Keře**: `bush.glb`, `tall_bush.glb`, `3d_bush_-_01.glb` (51 MB fotosken) – 23. 10. ráno, v 0.71.
- **Zvěř**: nic – Quaternius Animals pack (CC0, s animacemi) až ve FUNKCI/POSTAVÁCH.
