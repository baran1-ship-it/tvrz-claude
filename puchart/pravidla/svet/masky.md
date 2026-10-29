# Slovník masek – dnešní stav (krok A, Astra 27. 10. 10:55 bod 5)

Tento slovník popisuje dnešní obsazení kanálů. Nový význam masky se nejdřív zapíše sem a teprve potom do kódu. Shader má číst masku podle jména. Převod jméno → kanál bude v kroku D-data.

Podklady:
- `docs/soupis/shadery.md` (kap. „Co znamenají masky“),
- `docs/soupis/blender.md` (export barev vrcholů),
- `scripts/svet.gd` (`_cesta_v`, `_stanoviste`),
- `scripts/koryto.gd`.

Verze formátu: **1** (27. 10.).

## Terén (`Teren*`, zem.gdshader)

| jméno masky | kanál | rozsah | výchozí | význam | zapisuje | čte |
|---|---|---|---|---|---|---|
| pole | COLOR.r | 0 / 1 | 0 | lán (plodinu, meze a hony počítá shader) | `blender/export_game.py:101` (atribut `pole` z `kraj.field_strip`) | zem.gdshader (hony, lány); svet.gd stanoviště |
| trava | COLOR.g | 0..1 | 0,85 louka | 0 = hlína (cesta, dvůr), 0,85 = louka; pás cesty v Blenderu 0,08 / 0,3 / 0,8 | export_game.py (`grass`); svet.gd `_stare_cesticky` (staré cestičky → louka); koryto.gd výplň (0, 0,85, 0, 1) | zem.gdshader `gm`; louka.gd (přes data, ne barvu) |
| les | COLOR.b | 0..1 | 0 | les pod korunami (lesní půda, hrabanka) | export_game.py (`les` z `kraj.forest`) | zem.gdshader (max s `stanoviste` R+G) |
| dno_bahno | COLOR.a | 0..1 | 1 | 1 = běžná zem; 0,5–1 bahno u rybníka a příkopu; < 0,5 dno potoka (oblázky) | koryto.gd:215 (`0,5 − 0,5·dno`), nádrže | zem.gdshader `bahno`, dno |
| cesta_poloha | CUSTOM0 (RGBA float) | x: lat / okraj (±), y: s podél osy (m), z: jetost kolejí, w: okraj hlíny (m) | (9, 0, 0, 0) mimo cestu | kde je hlína cesty, kolej, okraj | svet.gd `_cesta_v` → `_cesta_povrch` (dělení terénu u cest) | zem.gdshader (`rd`, koleje, okraj) |
| cesta_stav | CUSTOM1 (RGBA float) | x: tráva hřbetu, y: bahno, z: abs(od středu koleje)/2, w: 7 = platné | (0, 0, 1, 0) | stav povrchu cesty (`w < 6` = žádná cesta) | svet.gd `_cesta_v` | zem.gdshader |

## Stanoviště (textura `stanoviste`, mřížka 2 m nad `trava_kraj`)

| jméno | kanál | význam | zapisuje | čte |
|---|---|---|---|---|
| jehlicnany | R | koruny jehličnanů | svet.gd `_stanoviste` (z instancí stromů, **uprostřed rozsevů** – soupis svet_c) | zem.gdshader (les), rozsevy |
| listnace | G | koruny listnáčů | totéž | totéž |
| skaly | B | skály | totéž | totéž |
| pesina | A | 0,5 + znaménková vzdálenost od osy pěšiny / 6 m | svet.gd `_pes_postav` z `pravidla/svet/cesty.json` pěšin | zem.gdshader `pes`, louka.gd, rozsevy |

## Mřížky dat (`modely/svet.json`)

| mřížka | obsah | zapisuje | čte |
|---|---|---|---|
| trava_kraj | y (int16 cm), m (hustota trávy 0..255, < 60 bez trávy), krok 2 m | Blender export; svet.gd (profil cest) | louka.gd, svet `_vyska` |
| trava_ves | totéž, krok ve vsi | Blender export; svet.gd (přesun usedlostí `_vo_data`, maska ulice `_ves_maska_ulice`) | louka.gd, svet `_vyska`, `ves_cesta` |

## Instance a ostatní

| kde | kanál | význam | zapisuje |
|---|---|---|---|
| stebla (trsy, drn) | INSTANCE_CUSTOM | x = druh + 16·q + hash, yzw = pata v soustavě buňky | louka.gd |
| květy | INSTANCE_CUSTOM | barva + hash, pata | louka.gd |
| impostor | INSTANCE_CUSTOM | xyz pata (half float), w = měřítko·256 + otočení | svet.gd impostory |
| textura (UV materiály) | COLOR.r / COLOR.b | odstín kusu / semeno kusu | export_game.py:103 |
| voda potok | COLOR | R pěna, G peřej, B/A směr toku | kraj.py:1012 |
| voda nádrž | COLOR.r | hloubka = R·4 m | nadrz.gd, tools/reka_bake.gd |
| reka | UV2 | flowmap / distmap (Waterways) | tools/reka_bake.gd |

## Známé rozpory (ze soupisu, oprava v kroku D)

- Les je dvakrát: COLOR.b z Blenderu a `stanoviste` z instancí stromů. Shader bere maximum.
- Hony a lány se počítají dvakrát, v `kraj.py` i v `zem.gdshader`.
- Louka se kóduje čtyřmi způsoby: barva, mřížka m 200, COLOR.g 0,8 a 0,85.
- Shader kreslí podle ručních souřadnic místo masky: nádvoří, starou náves (`ves_rovna` se nastavuje jen v `if TRZISTE`), tržiště, okraj lomu.
