# Pro chat, který hru programuje

Tady je, co hra potřebuje, aby příběh šel hrát. Seřazeno tak, aby šlo začít hned a postavy přišly později.

## 1. Co jde udělat hned (bez postav)
Kapitola 1 se dá skoro celá odehrát s tím, co hra už umí:
- **Deník úkolů** (svitek): název úkolu, aktuální krok, splněné kroky.
- **Spouštěče** kroků:
  - `vstup_do_oblasti` (hráč dojde k bráně, ke hrobce, do Doubravy),
  - `predmet_v_inventari` (prsten, dopis, listina),
  - `predmet_polozen_v_oblasti` (2 louče u márů, džbán u Báry, dokumenty na stole),
  - `ohen_hori` (krb, louče na ochozech),
  - `cas` (noc/den, konkrétní datum),
  - `zasahy_lukem` (terč),
  - `stav_brany` (most nahoře/dole, mříž).
- **Příznaky (flagy):** slovník `jméno → hodnota` v uložené hře. Úkoly je čtou i zapisují.
- **Text na obrazovce:** dopisy a listiny se čtou jako svitek (D-H1-dopis).
- **Kalendář:** datum + roční období. Kapitola posune datum.
- **Náhradní řešení bez NPC:** vzkazy na dveřích, dopisy na stole, hlas z ochozu jako titulky.

## 2. Postavy a rozhovory
- Postava stojí na místě nebo chodí mezi 2–3 body podle denní doby (Ludmila: kuchyně ↔ spíž, Ota: brána ↔ strážnice).
- **Rozhovor:** okno ve stylu svitku, text postavy + 1–4 volby. Volba může nastavit příznak, dát/vzít předmět, posunout úkol.
- Formát dialogů je v `dialogy/` (MLUVČÍ: text, číslované volby, za šipkou příznaky).
- Nejdůležitější postavy podle pořadí: **Ota, Ludmila, Vítek, rychtář Bílek, Kostka, Martin, Bára, Eliška, Vojtěch**.
- Vítek jako **společník**: chodí za hráčem, nosí louč, umí otevřít branku zevnitř.

## 3. Souboj
- Luk už je. Přidat: nepřítel se blíží, střílí, padá. Zásahy, život hráče.
- Boj zblízka: sek, bod, kryt (stačí jednoduché, KCD-styl až později).
- Obležení: vlny nepřátel s žebříky ke zdem, oheň na bráně, hašení vodou ze sudů.
- Číslo `obrana_body` a tabulka spojenců z `hlavni_pribeh.md` určí počet útočníků.

## 4. Potřeby a zásoby (už rozpracované v PRIBEH.md)
Hlad, únava, špína; spíž, dřevník, sýpka počítané z položených předmětů. Peníze v groších a kopách.

## Nová místa (podle toho, kdy je příběh potřebuje)
| Priorita | Místo | Kap. |
|---|---|---|
| 1 | hrobka u kostelíka sv. Jiljí (ruina už je), šibenice u rozcestí | 1 |
| 2 | mlýn na Bystřici, městečko Lipník (stačí náměstí, fara, lékárna, notář, trh) | 2 |
| 2 | krypta pod kostelíkem, lapkovský tábor v Liščí soutěsce | 2 |
| 3 | ves Zálesí, uhlířské Spáleniště, poustevna | 2–3 |
| 3 | podzemní chodba Doubrava → Lhota → sklep tvrze | 2–5 |
| 4 | tvrz Kamenec (noční vloupání) | 3 |
| 4 | podzemí Pusté skály, odpadní šachta | 2–5 |

## Předměty příběhu
| ID | Předmět | Kde |
|---|---|---|
| `prsten_havran` | pečetní prsten, havran s ulomeným zobákem | otcova truhla |
| `dopis_otce` | dopis Janovi (čitelný text) | otcova truhla |
| `listina_mlyn` | darovací listina s pravou pečetí | otcova truhla |
| `upis_kostka` | padělaný dlužní úpis | od Kostky |
| `dzban_vino` | džbán s usazeninou oměje | kuchyně |
| `razidlo_lipove` | padělané razidlo (lipová kostka) | Martinova truhla |
| `sip_rudy` | lapkovský šíp s rudým pírkem | most |
| `hadr_bily` | znamení mlynáře | mlýn |
| `svitek_simon` | Šimonův svitek se jmény | brašna u Prokopa |
| `prsten_lipe` | prsten pana Ješka s lipovými listy | od Zbyňka |
| `dopis_vartenberka` | dopis Kostkovi o útoku | Kamenec |
| `kniha_vyplat` | platby „B. V.“ | Kamenec |
| `konik_ohoraly` | ohořelý dřevěný koník | oběšenec v Doubravě |
| `mec_otce` | otcův meč | Tomáš (D7) |
| `zvon` | zvon sv. Jiljí | zakopaný (U1) |
| `dopis_anezka` | dopisy z dutého dubu (víc kusů) | dutý dub u božích muk |
| `musle` | dopis s mořskou mušlí | kap. 6 |

## Seznam příznaků
**Hlavní:** `ch1_prijezd`, `ch1_bdeni`, `podezreni_jed`, `ch1_pohreb`, `ma_prsten`, `ma_dopis`, `ma_pravou_listinu`,
`ch1_tutorial`, `urok_havel`, `kostka_postoj`, `kostka_nenavist`, `vi_padelek`, `vi_jed`, `podezrely_martin`, `martin`,
`dluh`, `zalesi_pomoc`, `nabidka_lipe`, `priznani_martina`, `dopis_vartenberka`, `kniha_vyplat`, `vi_o_spiknuti`,
`urok_jiri`, `strana`, `obrana_body`, `kostka_zajat`, `obrana`, `ota_nalada`, `ves_nalada`.
**Lapkové:** `L_most`, `L_soutezka`, `hanzlik`, `kunes`, `L_past`, `L_sachta`, `pusta_skala`, `busek`, `kaspar`,
`vojtech_vernost`, `lapkove_konec`.
**Milostivé léto:** `M_mrtvy`, `M_dukazy`, `M_prokop_stopa`, `ma_svitek`, `prokop_nalezen`, `slib_prokopovi`, `prokop`,
`sup_nepritel`, `konrad`, `ondrej_ocisten`, `leto_konec`.
**Láska:** `eliska_naklonnost`, `eliska_zachranena`, `eliska_polibek`, `svatba`,
`anezka_potkana`, `anezka_dopisy`, `vi_plany_kamence`, `anezka_noc`, `anezka_zavrena`, `anezka_utek`, `anezka`, `jesek_nalada`, `laska`.
Polibky se ukazují, víc ne – noc řeší zatmívačka a střih na ráno.
**Doubrava:** `D_kovar`, `D_noc`, `vi_o_paleni`, `bara`, `D_poustevnik`, `vi_o_otci`, `D_rychtar`, `chodba`, `tomas`.
