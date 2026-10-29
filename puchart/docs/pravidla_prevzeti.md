# Pravidla a tabulky převzaté z Havrana

Míša 29. 10.: „Pozor, má to nějaká pravidla a tabulky, víš o tom?“ – ano. Havran má systém **tabulek pravidel + hlídačů**
(`docs/havran/pipeline.md`, `navrh_tabulek.md`, `soupis_pravidel.md`). Puchart ho přebírá celý, ne jen myšlenku.
Převzaté soubory nesou v `popis` předponu „PŘEVZATO Z HAVRANA“ a `"puchart_zapojeno": false`, dokud je kód Puchartu nečte.
Zapojení = přepnout na `true` + test, který pravidlo ověřuje (vrstvy hlídačů níže).

## Tabulky

| soubor | co obsahuje | v Puchartu | co upravit pro Oderské vrchy | zapojeno |
|---|---|---|---|---|
| `pravidla/pravidla_sveta.json` | rozsev: 24 sloupců podle CryEngine/KCD (stanoviště, výška, sklon, hustota, kolize, stín, zánik, ohyb…), 29 stanovišť, **ochranná pásma** (cesta, budova, voda, skála, plot, díl, test) | převzato 1:1 | `vyska_m` jsou výšky světa Havrana (údolí do 25 m) → přepočítat na Puchart (y −57 až +153 m); smrk/jedle výš (Oderské vrchy 450–550 m n. m.), pískovcové stanoviště → droba | ne (krok C) |
| `pravidla/pravidla_modelu.json` | třídy modelů: troj. LOD0/1/2, přepnutí LOD (m i px), textury px, alfa, stín, kolize, rozpočet GPU | převzato 1:1 | nic (tablet je stejný) | ne (krok C) |
| `pravidla/svet/druhy.json` | druhy rostlin s historickou kontrolou (historicky = roste v Čechách 1393, zdroj Pladias, Chytrý) | převzato | doplnit horské druhy (jedle hojněji, javor klen, jasan v roklích), odebrat pískovcové | ne |
| `pravidla/svet/vztahy.json` | **matice vztahů** 17 druhů (terén, voda, cesta, budova, plot, strom, keř, bylina, kámen, předmět, posun, hráč, kůň, postava, světlo, LOD, kolize) = 153 dvojic: smysl, estetika, výkon, návrh, testy | převzato | dvojice „skála\|hrad“ a „hrad\|hrad“ (dvojhrad, spojnice) přidat; testy přejmenovat na testy Puchartu | ne |
| `pravidla/svet/masky.md` | slovník masek (jedna definice každé masky) | převzato | maska výseku Puchartu: R louka, G les, B skála, A břeh (`stanoviste.py`) – sjednotit názvy se slovníkem | částečně |
| `pravidla/svet/modely.json` | katalog modelů Havrana (rostliny, předměty, stavby; třída, pata, LOD) | převzato | jen modely, které Puchart použije; cesty k souborům = větev assets / balíky | ne |
| `pravidla/svet/cesty.json` | typy cest a pěšin, pásma; **bez os Havrana** | typy převzaty | osy cest výseku (krok B, plánovač sklonu jako `krok_b/astar.py`, vozová ≤ 12,5 %) | ne |
| `pravidla/svet/{hrac,jizda,postavy,zvirata,dovednosti,prostredi}.json` | ovládání, jízda, NPC, zvířata, dovednosti, prostředí | převzato | prostředí = léto 1393 | ne |
| `pravidla/svet/svet.json, teren.json, plochy.json, pudy.json, lokace.json, voda.json, rozpocty.json, zdroje_dat.json` | **nové pro Puchart** | – | – | ano |

## Hlídači (vrstvy z Havrana `pipeline.md`, „Hlídači a mapa stavby“)

| vrstva | Havran | Puchart | stav |
|---|---|---|---|
| 0 skripty | pyflakes, `--check-only` | totéž | zatím ručně |
| 1 data | `test_smyslu.py` před exportem | `nastroje/test_smyslu.py` (kopie v `docs/havran/` k převodu) | k převodu |
| 2 engine | `beh.sh` + chyby Godotu | totéž | k převodu |
| 3 protokol | kdo změnil terén | pečení je v pořadí nástrojů → protokol = log `postav_vse.sh` | k převodu |
| 4 zámek terénu | hash výšek | hash `vysek.r16` po kroku B (budovy, cesty) | k převodu |
| 5 invarianty světa | `test_svet.gd` | totéž | k převodu |
| 6 mapa | `build/mapa_stavby.png` | `nahled_terenu.py` umí vrstvy – rozšířit o chyby | základ hotový |
| 6b matice vztahů | `kontrola_vztahu.py` – dvojice bez testu = nevydá se | kopie v `docs/havran/` | k převodu |
| 7 tabulka chyb | `kontrola_tabulek.py` – chyba od člověka bez kontroly = nevydá se | `docs/chyby.md` + kopie skriptu | tabulka založena |

Pravidlo z PDF kap. 12 platí totéž: „Existující název testu není důkaz pokrytí: test musí pravidlo skutečně ověřit.“
