# Rešerše terénu: odpovídá hra skutečným datům? (11. 11.)

Míša 11. 11.: „podrobnou rešerši celé krajiny, jestli je opravdu podle reálných dat – výškopis a polohopis… nepřidala se
někde cestička nebo hlína pro dorovnání nájezdu na most… podoba kopce, reálné místo má strmější svahy… ověř, jak to staví
Blender a Godot“. Skript rozboru: scratchpad `teren/rozbor.py` (výsledky níže jsou změřené, ne odhad).

## Řetězec stavby terénu
1. `dmr_mrizka.py` – body ČÚZK DMR 5G (LAZ) → mřížka 1 m (lineární TIN).
2. `teren_upravy.py` – plošiny, příkopy, útes ostrohu B, průrva (pravidla/svet/hrad_puchart.json `teren`).
3. `koryta.py` – koryta potoků zaříznutá do terénu.
4. `cesty.py` – zářezy a násypy cest (cesty_puchart.json).
5. `teren_dlazdice.py` – Gaussovo vyhlazení σ 1,5 m, kolize `vysek.r16`, viditelná síť `vysek_sit.r16`, obzor.
6. Godot `svet.gd` – síť z `vysek_sit.r16` po 2 m (do 200 m), 4 m (do 450), 8 m (do 900), 16 m dál; mimo výsek obzor 40 m.
   Godot ani Blender výšky už nemění (Blender stavby jen posazuje na terén).

## 1. Výškopis – shoda se skutečnými body DMR 5G (287 939 bodů ve výseku, 1 bod / 14 m²)
| krok | medián odchylky | 95 % | bodů > 0,5 m | bodů > 2 m |
|---|---|---|---|---|
| mřížka 1 m | 0,03 m | 0,13 m | 398 | 14 |
| + úpravy u hradů | 0,03 | 0,13 | 767 | 274 |
| + koryta | 0,03 | 0,13 | 1 761 | 369 |
| + cesty | 0,03 | 0,15 | 3 057 | 905 |
| ve hře (viditelná síť) | 0,09 | 0,43 | 11 018 | 972 |

Převod je věrný; změny jsou soustředěné na místa níže.

## 2. Co se do terénu přidalo nebo ubralo (oblasti nad 0,3 m)
**Úpravy u hradů** (záměrné, REKONSTRUKCE 1393 podle kreseb GC80T08 a náčrtu Míši): 7 000 m², výkop 21 000 m³ –
útes ostrohu B (x 51, z 142: až −13 m sutě pryč, stěny), příkop A prohloubený o ~4 m (zanesení za 600 let), plošiny bran.

**Koryta potoků**: 25 000 m², výkop 20 600 m³, hloubka většinou 1–2 m, místy až 6,6 m (x −539, z −703).

**Cesty** – tady jsou přidané věci, které v datech nejsou:
- **Násyp až 4,2 m** na rekonstruované cestě od Kyžlířova (`hlavni_kyzlirov`, REKONSTRUKCE – trasa je návrh)
  u x −86, z −329: 2 100 m², +4 250 m³ hlíny. Další násypy 2–3 m u hradu: x 0 z −73 (nástup vnějšího mostu),
  x 25 z 65 a x 42 z 101 (hřebenová), x 134 z 524 (údolní II/440).
- **Úvoz až 5,4 m** na cestě k hájovně (`hajovna`) u x −60, z 736: 4 450 m², −11 000 m³. Dnešní cesta leží na svém
  tělese v DMR; zářez vzniká vyrovnáním podélného sklonu (max 12,5 %). Ve skutečnosti tam tak hluboký úvoz není.
- Cesta po ostrohu x −87, z −692: 5 200 m² ±1,5 m (příčné srovnání jízdního pásu).

**Vyhlazení σ 1,5 m**: 60 000 m² se změnou nad 0,5 m, typicky −0,5 až −1 m na hranách a hřbítcích (zaoblí ostré lomy).

## 3. Sklony svahů – je hra plošší než skutečnost?
| | p50 | p90 | p99 | plocha nad 30° | nad 40° |
|---|---|---|---|---|---|
| DMR mřížka 1 m | 13,9° | 32,3° | 42,8° | 14,3 % | 1,8 % |
| hra blízko (síť 2 m) | 14,0° | 32,0° | 41,7° | 13,7 % | 1,5 % |
| hra 200–450 m (4 m) | 13,9° | 31,8° | 40,9° | 13,4 % | 1,3 % |
| hra 450–900 m (8 m) | 13,8° | 31,4° | 39,7° | 12,7 % | 0,9 % |
| hra nad 900 m (16 m) | 13,7° | 30,7° | 37,9° | 11,4 % | 0,5 % |
| obzor DMR 10 m | 5,7° | 19,8° | 32,9° | 2,4 % | – |
| obzor ve hře (40 m) | 5,5° | 17,6° | 30,8° | 1,3 % | – |

Řezy přes hrady (±200 m): hrad A Z–V DMR max 39°, hra 55°; S–J 42° / 53°; hrad B 49° / 70° (útesy a příkopy 1393).

**Závěr:** zblízka je hra stejně strmá jako data (u hradů strmější – rekonstrukce). Svahy se zplošťují **v dálce**:
nad 450 m mizí nejstrmější místa (nad 40°: 1,8 % → 0,5 %), obzor za výsekem má síť 40 m a převýšení v okně 200 m
o ~13 % menší (p90 66 → 57 m). Dále **samotné DMR 5G je zobecněné** (1 bod na 14 m², ČÚZK – klíčové body TIN): skalní
hrany, stěny a lomy menší než ~4 m v něm nejsou, takže skutečné skalnaté svahy jsou strmější, než ukazuje jakýkoli model
z DMR 5G. Hustší veřejná data reliéfu bez vegetace ČÚZK nevydává (DMP 1G je povrch včetně staveb a vegetace).

## Návrh oprav (čeká na Míšu)
1. **Cesty bez umělých násypů a úvozů, kde nejsou doložené:** u cest NAVRH/REKONSTRUKCE držet terén DMR (násyp/zářez
   max ~0,5 m, jen srovnání jízdního pásu) – zejména násyp 4,2 m u x −86 z −329 a úvoz 5,4 m k hájovně.
   Násypy u nástupů mostů ponechat jen tam, kde je doložený (hrad_puchart.json).
2. **Dálka věrněji:** LOD sítě ve 450–900 m a za 900 m s krokem podle křivosti (hřbety a hrany ponechat), obzor z 10m
   mřížky DMR s krokem 20 m na hřbetech místo 40 m všude. Cena trojúhelníků změřit na tabletu.
3. **Vyhlazení σ 1,5 m jen tam, kde je potřeba** (proti „schodům“ interpolace v rovině), ne na hranách svahů a skal.
4. **Ověření pohledem:** snímek ze hry ze stejného místa a s ohniskem jako reálná fotka (docs/reference) – rozdíl dojmu
   (výška stromů, ohnisko 70°, chybějící skalní výchozy) od rozdílu tvaru.
