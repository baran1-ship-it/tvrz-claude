# Modely od Míši – průchod `nove._import_sketchup`

Funkce (blender/nove.py): sloučení vrcholů 1 mm, normály ven, materiály podle klíčového slova na herní
fotografické materiály (UV v metrech), ostatní glb materiály bez lesku (drsnost 0,9, kov jen u kovu),
rovinná decimace 1°, strop trojúhelníků, textury ≤ 1024 (předměty 512). Ve hře svet.gd přiřadí herní
materiály podle názvu i statickým stavbám.

| Model | Soubor | Troj. před → po | Textury před → po | Materiály → herní |
|---|---|---|---|---|
| hostinec | stazene/medieval_tavern_interior.glb | 9 292 → 8 598 (stavba jen rovinné slučování; collapse na 4 000 zúžil dveře) | 8×, max 1024 → max 1024 | RoofTilesWood → sindel_hra, Wood → dub_ven, LogEdgeWeathered → drevo_rez; StoneWall (zdivo_hostinec), DarkStone, Brick, Sign, RustedMetal z glb bez lesku |
