# Zřícenina kostela – Odkaz Havrana (Čechy 1393)

Vesnický gotický kostel z doby kolem 1340, který vyhořel a zůstal opuštěný. Hráč do něj vejde portálem, věží nebo branou hřbitova.
Předlohy: zřícenina kostela v Přibyslavicích z KCD a skutečné české zříceniny (Branišov, Kuklov, Třebařov, Klášterní Skalice, Panenský Týnec).

Měřítko je 1 jednotka = 1 m, osa Y nahoru. **Počátek je na terénu**. Vstup (jih) je na **+Z**, oltář (východ) na **+X**. Podlaha lodi je ±0, presbytář a sakristie +0,36.

## Soubory
- `kostel_ruiny.glb` – celý díl včetně hřbitovní zdi, textury jsou vložené
- `kostel_ruiny_lod1.glb` – LOD1 pro dálku (132 trojúhelníků)
- `kostel_ruiny.blend`, `kostel_ruiny.py` (+ `_stavba.py`, `tesar.py`, `_spolecne.py`) – zdroj (`python kostel_ruiny.py --norender`)

## Co v modelu je
| Část | Kde (Godot x, z) | Poznámka |
|---|---|---|
| **Věž** | x −10,9 … −5,5 | zlomená šikmo: SZ roh 15,5 m, JV roh 7 m; dveře na západ, oblouk do lodi, kapsy po trámech ve 2 patrech, zbytky zvonových oken, ohořelý trám |
| **Loď** 10,5 × 6,8 m | x −5,5 … 5 | jižní zeď stojí (~8 m) s **profilovaným lomeným portálem** (z +4,4) a dvěma okny (jedno s kružbou, jedno rozbité); severní zeď je sesutá na val sutin; štít nad vítězným obloukem |
| **Vítězný oblouk** | x 5 … 6 | 4,2 m široký, 7,4 m vysoký, dva pískovcové schody nahoru |
| **Presbytář** | x 6 … 13,8 | pětiboký závěr. **1. pole klenby je zřícené**: jižní a západní část chybí, žebro visí od svorníku proti nebi. **Závěr je zaklenutý celý.** Pět oken: dvě celé kružby, jedno trojlistové, dvě rozbitá |
| **Sakristie** | x 6 … 9,6, z −3,3 … −6,8 | celá valená klenba, tma, úzká střílna, výklenek ve zdi |
| Hřbitov | x −17 … 20, z −11 … 12,5 | zeď 0,6 m se třemi sesutými úseky, brána z jihu, 6 dřevěných křížů a kamenný kříž |

Mobiliář je rozbitý: menza oltáře je rozlomená, křtitelnice převrácená, tři náhrobní desky s křížem (jedna prasklá). Ve zdi je sanktuář s vimperkem a mříží a sedile. Uvnitř zůstaly zbytky omítky a fresky (dva světci u vítězného oblouku, svěcené kříže, ornamentální pás). Dál jsou tu sutinové kupy, spadlé kusy žeber a kružeb, ohořelé trámy, vyvalené křídlo vrat portálu a břečťan.

## Materiály a barva vrcholů
- Zdivo je posunuté podle výškové mapy fotoskenu, takže kámen je skutečně v geometrii, ne jen v textuře. Vně je `M_ZdivoKamen` (broken_wall), uvnitř zatřené spáry `M_ZdivoInterier` a omítka `M_OmitkaKostel`.
- **Saze po požáru, mech, stékance a vlhko jsou v barvě vrcholů (COLOR_0).** Godot ji obvykle zapne sám. Když ne, zapni v materiálech `M_ZdivoKamen`, `M_ZdivoInterier`, `M_OmitkaKostel`, `M_Sut`, `M_DlazbaPolniKamen` a `M_HlinaKostel` „Vertex Color → Use as Albedo“.
- Žebra, svorníky, konzoly, kružby, portál a schody jsou z pískovce (`M_Piskovec`, `M_PiskovecMech`).
- Dřevo:
  - `M_TramOhoraly` jsou ohořelé trámy s rozpraskanou kůrou uhlíku. Textura je generovaná skriptem `char_tex.py` (`python char_tex.py foto`). Zlomené konce trámů jsou roztřepené do třísek.
  - `M_DubZvetraly` je šedohnědý zvětralý dub pro hrobové kříže. Příčka je zapuštěná na plát a drží ji dřevěný kolík.
  - `M_PrknaStara` jsou prkna vrat a dveří.
- `M_Freska` a `M_Brectan` mají průhlednost. Nastav Transparency → **Alpha Scissor** (práh 0,5) a Cull → **Disabled**.

## Dveře
`Kostel_Dvere_Sakristie` má počátek v pantu a otáčí se kolem Y. V extras je `otevreni_deg = +95`, otvírá se do sakristie. Křídlo je mírně prověšené, jako by viselo na jednom pantu. Průchod je vysoký 1,9 m.

## Značky pro hru (Godot x, y, z)
| Uzel | Poloha | Účel |
|---|---|---|
| `Kostel_Vstup_Portal` | (−3,2; 0; 6,0) | před hlavním portálem |
| `Kostel_Vstup_Vez` | (−12,2; 0; 0) | před dveřmi věže |
| `Kostel_Vstup_Brana` | (−3,2; 0; 13,5) | brána hřbitova |
| `Kostel_Oltar` | (12,65; 1,45; 0) | na menze (questový předmět, svíce) |
| `Kostel_Truhla_Sakristie` | (8,4; 0,36; −5,6) | místo pro truhlu nebo poklad |
| `Kostel_Svicka_Sanktuar` | (10,6; 1,36; −2,78) | ve výklenku sanktuáře |
| `Kostel_Strom_Lod` | (−1,6; 0,35; −2,3) | bříza nebo jasan rostoucí v lodi |
| `Kostel_Strom_Vez` | (−8,4; 0,6; −0,6) | náletová dřevina ve věži |
| `Kostel_Kerovi_Sever` | (1,0; 0,5; −6,4) | křoví na sutinovém valu |
| `Kostel_Havran_Vez` / `_Stit` / `_Klenba` | koruna věže, vrchol štítu, hřbet klenby | místa pro havrany |
| `Kostel_Svetlo_Lod` | (0; 9,5; 0) | pomocné světlo nebo mlha v lodi |

## Vložení do Godotu
1. `kostel_ruiny.glb` dej na rovný terén. Podlaha lodi a sutiny jsou součástí modelu. Okolí hřbitova je tvoje tráva.
2. Kolize:
   - 54 kvádrů s příponou `-convcolonly` pokrývá zdi s průchody, opěráky, sakristii, presbytář, schody, oltář, náhrobky, trámy a hřbitovní zeď.
   - Sutinové kupy mají hrubou síť `-colonly`, takže se po nich dá chodit.
3. `Kostel_Interier_skupina` obsahuje fresky, mříž, dveře, kameny, trámy, podlahy a značky. Vypni ji, když je hráč daleko.
4. LOD1 dej na stejné místo. Visibility Range: hlavní díl 0–90 m, LOD1 od 85 m.
5. Pro efekt „wau“ přidej do lodi `FogVolume` nebo volumetrickou mlhu. Slunce svítí z jihu skrz okna a vítězný oblouk, takže vzniknou paprsky. Na náhledech je to použité.

## Výkon
- Celý díl má ≈ 270 000 trojúhelníků. Je to hlavní lokace a většina připadá na zdivo s geometrií kamene.
- Rozpad:
  - věž ~44k
  - loď ~48k
  - presbytář ~69k
  - klenba ~25k
  - pískovec ~24k
  - hřbitovní zeď ~26k
  - zbytek do 40k
- Pro tablet, když bude potřeba:
  - `Kostel_HrbitovniZed` a `Kostel_Hrbitov` se dají vypínat zvlášť, nebo je v Blenderu zmenši modifikátorem Decimate.
  - Visibility Range a occlusion culling (zdi kostela zakrývají hodně).

## Historie (proč to tak vypadá)
- **Západní hranolová věž, obdélná loď a presbytář s pětibokým závěrem a opěráky** jsou typická česká vesnická gotika 14. století (Kuklov, Branišov).
- **Plochý dřevěný strop lodi** shořel a zůstaly po něm kapsy po trámech. Kamenná klenba presbytáře přečkala, protože nehořela. Proto stojí právě presbytář.
- **Klenba padá po kápích, žebra zůstávají.** To je skutečný způsob rozpadu žebrových kleneb, viditelný třeba v Klášterní Skalici.
- **Svěcené kříže** (12 na zdech chrámu) a **sanktuář s vimperkem** odpovídají době. Okna s kružbou o dvou lancetách s trojlistem v kruhu jsou vrcholná gotika kolem 1340.
- Lešenářské díry ve fasádě zůstaly po stavbě, stejně jako na skutečných zříceninách.
