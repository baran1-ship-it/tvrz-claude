# Poučení z Havrana (měřeno na Xiaomi Pad 8, verze do 0.995)

| téma | co se stalo v Havranovi | co z toho plyne pro Puchart |
|---|---|---|
| Načítání | svět se stavěl při startu: koryto 36 s, rostliny 27 s, svět 83 s, hra 110 s | vše péct (`nastroje/`), tablet jen načítá; cíl < 20 s |
| Paměť | halda 1,26–1,45 GB, PSS 2,2–2,4 GB (cíl 1,25) | dlaždice + uvolňování, žádné kopie dat ve skriptech |
| Kreslení | ves 1205, hostinec 1000–1248; stín slunce 337–471, domy vsi 420 | stíny 40 m, slučování po dvorcích podle materiálu, impostory za 100 m |
| Okluze | terénní okluze ušetřila 0–46 kreslení – drahé pohledy jsou přímo vidět | úspora z kompozice (PDF kap. 8) a LOD, ne z okluze |
| Pády | 0.58–0.59: MSAA a shader s kopií obrazovky | nikdy MSAA, žádná screen texture |
| Shadery | Adreno: max ~13 vzorkovačů v materiálu | pole textur (Texture2DArray) |
| PC vs tablet | ETC2 pole textur se na PC kreslí bíle/žlutě | na PC snímky ověřovat i bezeztrátově (chyba #1 v `chyby.md` ověřena takto) |
| Záplaty | výjimky v kódu se hromadily (zem.gdshader s ručními souřadnicemi vsi, lomu, tržiště) | data + pořadí kroků, zámek terénu, shader nečte ruční souřadnice |
| Čísla | „nejdelší snímek“ lhal (vyhlazené delta), počítadlo záseků k ničemu při 20–30 FPS | panel měří razítka, N/A místo 0 (`hra/scripts/diag.gd`) |
| Testy | celá sada hodinu, na PC software render | rychlé testy nad daty headless; výkon jen tablet |
| Vzhled | rostliny „plácačky“, levitující tráva, cesta pod mostem | test smyslu před exportem, matice vztahů |
| Hodnocení | Míša chce KCD | reference KCD1/KCD2 u každého rozhodnutí vzhledu |
