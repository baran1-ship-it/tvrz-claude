# Kontrakt stavby světa – pipeline v2 (krok A, rádce 10:45, Astra 10:55 bod 4)

Kontrakt platí pro každou lokaci i pro celý svět, pro importovaný díl i generovanou lokaci. Krok A ho jen zapisuje. Zapojení do kódu (`stavba.gd`) a testy kroků jsou krok B/C.

Dnešní skutečné pořadí je v `docs/soupis/svet_c.md` („Pořadí stavby dnes“). Níže je u každého kroku uvedeno, co ho dnes dělá.

## Zásady
1. **Data jsou jediný zdroj.** Co je kde, je v `pravidla/svet/` (lokace, cesty, voda, plochy). Jak se to staví a kreslí, je v tabulkách (pasma, povrchy, tridy, materialy, druhy, modely) a v globálních souborech (svet, generovani, prostredi, rozpocty). Blender i Godot čtou totéž.
2. **Krok čte jen výstupy dřívějších kroků a nikdy je nemění.** Když pozdější krok potřebuje změnu (strom v ulici), mění se záznam nebo pravidlo a staví se znovu od kroku, kterého se změna týká.
3. **Zámek terénu po kroku 4.** Od kroku 5 nic nemění výšky terénu ani mřížky výšek.
4. **Mazání se nahrazuje stanovištěm.** Druh se nesází tam, kde nemá být, místo aby se dodatečně mazal.
5. **Každý krok má test v `rychle` sadě.** Bez průchodu se nevydává.

## Kroky

| # | krok | vstup | výstup (rozhraní) | invariant | test | dnes (svet.gd, kraj.py) |
|---|---|---|---|---|---|---|
| 1 | **terén hrubý** | generovani, plochy, lokace (režim plošina/kotlina/ostroh) | výšková síť a mřížky `trava_kraj`/`trava_ves` (y) | – | `plochy` (sklony polí a lesa) | Blender `fort.land` + `kraj.hills`; Godot `_terasa_terenu`, `_stare_cesticky`, `_prikop_zaplata` |
| 2 | **voda** | voda (osa potoka, hladiny, rybník: hráz, přítok, odtok; příkop) | koryto ve výškách, hladiny, maska dno/bahno (COLOR.a) | hladina potoka klesá k ústí, odtok níž než přítok, hladina rybníka vodorovná, min. spád jen na tekoucích úsecích | `voda` | `koryto.gd` (osa z `voda.json`), nádrže, `_najdi_brody`, `_ryb_priprav` |
| 3 | **cesty** | cesty (osy, typ, šířka, mosty, brody), pasma (sklon, zářez) | profil cesty do terénu, maska cesty (CUSTOM0/1), `cesty_osy` | podélný sklon ≤ pasma (vozová 12,5 %), příčný sklon dle pásma, nic přes dům | `cesty` | `_cesty_tvar` (osy z `cesty.json`), `_cesty_profil`, `_cesty_teren`, `_cesty_do_terenu`, `_najezdy_mostu` |
| 4 | **plošiny budov a dvorů** | lokace (budovy: půdorys, podlaha, dvůr_r, štít, vchod), pasma.budova | srovnaný terén pod budovou a dvorem, podlaha_y | rozdíl terénu pod půdorysem ≤ pasma (jinak plošina/podezdívka), dvůr k cestě | `lokace` | `_domy_vysky`, `_upravy_terenu` (dům), `_teren_pod_vraty`, Blender `stavba_pad`/`pad_adjust` |
| — | **ZÁMEK TERÉNU** | | | od teď nic nemění výšky (`_vyska`, mřížky, sítě Teren*) | `zamek` (hash výšek po kroku 4 = na konci) | dnes porušeno: `_cesty_rostliny` posouvá výšky rostlin podle profilu až po usazení, `_vo_*` a profil cesty jsou po sobě |
| 5 | **masky základní** | terén, voda, cesty, plochy, lokace | stanoviště (louka kosená/divoká, pole, les, břeh, skála, pěšina), slovník `masky.md` | jedna definice každé masky | `povrchy` (data) | `_stanoviste`, `_pes_postav`, `_pudy` (dnes uprostřed rozsevů) |
| 6 | **stromy** | masky 5, druhy, pasma | instance stromů (data) | kmen mimo pásma cest, zdí a vody | `zasazeni` (stromy) | `_skalni_mesto`, `_nove_lesy`, `_les_hustsi`, `_lesni_plast`, `_tvrz_zvencí`, kompozice lokací |
| 7 | **kryt korun** | stromy 6 | maska stínu korun | – | – | dnes v `_stanoviste` (R/G) a jen částečně |
| 8 | **podrost a keře** | masky 5 + kryt 7, druhy, pasma | instance keřů, bylin, kamení | keř/trsy mimo pásma, druh jen na svém stanovišti | `zasazeni` | `_krajina`, `_lesni_patro`, `_kere_*`, `_cesty_kere`, `_cesty_kameny`, `_rybnik_breh`, `_brody`, `_lom`, kompozice vsi |
| 9 | **předměty** | lokace (poloha), modely (katalog) | předměty a vybavení | ne v jízdním pásu, ne ve zdi | `zasazeni` (předměty) | `_static_items`, `_lom_vybaveni`, `_lom_sut`, vybavení vsi |
| 10 | **usazení + kmeny + kolize všeho z 6–9** | 6–9, terén (zamčený) | výšky pat (pata z modely.json), kolize | nic nevisí (> 0,25 m), pata podle třídy | `zasazeni` (visí, v zemi) | `_na_zem`, `_na_povrch`, `_na_povrch_skal`, `_kmeny`, `_mekke_mimo_kvadry` (dnes před částí kroků 8–9) |
| 11 | **povrchy vizuální** | masky 5, povrchy, materialy | shader terénu z masek, LOD a dosahy z tříd | shader nekreslí z ručních souřadnic | `povrchy`, `tridy`, `materialy` | zem.gdshader, `_impostory`, `_rozdel_site`, `_okluzory` |

## Rozhraní (data mezi kroky)
- **Terén:** sítě `Teren*` a mřížky `trava_kraj` a `trava_ves`. Po zámku jen ke čtení.
- **Cesty:** `cesty_osy[]` {p, y, w, k, op, dl, s0}, maska CUSTOM0/1. Typ osy (vozová / ulice_vsi / pěšina) vede k pásmu.
- **Masky:** jména podle `pravidla/svet/masky.md`. Krok 11 je čte podle jména, ne podle kanálu.
- **Instance:** `data.rostliny[model_id] = [transformace]`, `data.vybaveni`. Model a třída podle `modely.json`.
- **Kolize:** z kroku 10 po buňkách (rozpocty.kolize).

## Migrace (navrh_tabulek.md kap. 7 a 9.7)
- **A (0.95):** soubory, `pravidla.gd`, test `pravidla_cteni`, slovník masek, katalog, tento kontrakt. Bez změny vzhledu.
- **B:** zapojení kontraktu, logika krajiny (voda, cesty ≤ 12,5 %, hostinec k cestě, mlýn pod rybník), zámek terénu.
- **D-data:** masky před rozsevem.
- **C:** zasazení (pásma, stanoviště místo mazání).
- **D-vzhled, E, F:** povrchy, třídy, materiály.
