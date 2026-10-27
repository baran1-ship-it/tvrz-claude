# Zadání modelu: vodní mlýn pod rybníkem Lhota (krok B, Míša 27. 10. 10:50)

Data jsou v `pravidla/svet/voda.json` → `rybnik_lhota_voda.mlyn`: poloha (380, 925), spád 3,5 m a kolo na vrchní vodu.

## Co má model obsahovat
- **Mlýnice:** roubená nebo hrázděná, přízemní s půdou, asi 8 × 6 m. Krov sedlový se šindelem (`sindel`) nebo došky, jako ostatní stavby ve vsi. Je to vesnický mlýn kolem roku 1393, žádný zděný panský.
- **Vodní kolo na vrchní vodu:** průměr asi 3,2 m (spád 3,5 m minus volný odtok pod kolem), šířka 0,8–1,0 m, korečkové. Hřídel vede do mlýnice zdí na straně odtoku.
- **Náhon:** dřevěný žlab na kozách přivádí vodu na vrchol kola. Konec žlabu je v ose kola, asi 0,3 m nad ním. Délka podle terénu, přibližně 15 m od svahu.
- **Odpad:** kamenné koryto pod kolem, ústí zpět do odtoku.
- **Uvnitř** (stačí jednoduše): jedno složení kamenů, násypka a moučnice.
- Kolize hrubá: kvádry na stěny, kolo jako jeden válec.
- Pata modelu = podlaha mlýnice. Lic s kolem hledí do lokálního +x.

## Rozpočet
Tablet: ≤ 15 000 trojúhelníků celkem. Textury ze stávajících materiálů hry (`dub_ven`, `prkna`, `sindel`, `kamen`). Žádné vlastní 4k textury.

## Podklady
- Reálie: mlýny na vrchní vodu jsou v Čechách doložené pod rybničními hrázemi už ve 14. století, rybník slouží jako zásoba vody pro mlýn.
- Vizuálně: Kingdom Come: Deliverance 2, vesnické mlýny (Trosky, okolí Tachova). Dřevěné kolo, žlab na kozách, roubení.
