# Krčma do L – Odkaz Havrana (Čechy 1393)

Vesnická krčma s dvorem. Hlavní dům je přízemní a roubený. Vedle stojí samostatné křídlo: dole kamenná stáj, nahoře pokojíky pro hosty a nocležna. Mezi domem a křídlem jsou vrata do dvora.
Pevné vybavení je v modelu. **Stoly, židle, sudy, nádobí a lampy jsou z vaší hry.**

Měřítko je 1 jednotka = 1 m, osa Y nahoru. **Počátek je na terénu**, ulice je na **+Z** (v Blenderu −Y). Podlaha domu je +0,45, patro křídla +2,85.

## Soubory
- `krcma_L.glb` – celý díl, textury 1024 jsou vložené
- `krcma_L_lod1.glb` – LOD1 pro dálku
- `krcma_L.blend`, `krcma_L.py` (+ `_stavba.py`, `tesar.py`, `_spolecne.py`) – zdroj (`python krcma_L.py --norender`)

## Dispozice
| Místnost | Kde (Godot x, z) | Co v ní je |
|---|---|---|
| Šenkovna 7 × 8 m | x −8 … −1 | hliněná pec se zápecím, výčepní pult, ležení na sudy, police na džbány, lavice podél stěn |
| Síň | x −1 … 2,2, z +4 … 0 | vchod z ulice, dveře do dvora |
| Černá kuchyně | x −1 … 2,2, z 0 … −4 | ohniště na hliněném stupni, žebřík na půdu; dým odchází dymníkem v hřebeni |
| Jizba hospodského | x 2,2 … 7, z +4 … −0,5 | vlastní pec, postel, lavice |
| Komůrka šenkýřky | x 2,2 … 4,4, z −0,5 … −4 | postel, dveře hned u kuchyně a výčepu |
| Komora | x 4,4 … 7, z −0,5 … −4 | ležení na sudy, poklop do sklepa |
| Stáj (křídlo dole) | x 10,4 … 15,6 | jesle a žebřiny, 3 přepážky (4 koně), sláma, žebřík na seník |
| Pokojíky 1–3 (křídlo nahoře) | podél pavlače | postel a lavice; **pokoj 1 = spaní hráče** |
| Nocležna | sever křídla | 5 slamníků pro formany |
| Seník | východ křídla | sláma, dvířka na seno |

Ze dvora se na pavlač jde po venkovních schodech. Vedou podél křídla a dvůr nekříží.

## Dveře (počátek v pantu, otáčí se kolem Y)
Každé dveře mají v extras `otevreni_deg` (100) a `otevira_se` (dovnitř/ven). Výška průchodu je asi 1,95 m (hráč 1,76).
- Dům: `Vchod`, `Dvur`, `Senkovna`, `Jizba`, `Senkyrka`, `Komora`
- Křídlo: `Pokoj1–3`, `Noclezna`, `Vrata_Staj1–2`
- Vrata do dvora: `Vrata_L`, `Vrata_P`

## Značky pro hru (Godot x, y, z)
| Uzel | Poloha |
|---|---|
| `KrcmaL_Spani_Hrac` | (11,30; 3,45; −0,55) – postel v pokojíku 1 |
| `KrcmaL_Hospodsky_stani` | (−3,60; 0,45; 0,30) |
| `KrcmaL_Senkyrka_stani` | (−2,05; 0,45; −0,30) – za výčepem |
| `KrcmaL_Ohen_Kuchyne` | (−0,15; 1,10; −3,05) – světlo a oheň |
| `KrcmaL_Pec_Senkovna` | (−2,00; 1,45; −2,60) |
| `KrcmaL_Svetlo_Senkovna` | (−4,50; 2,60; 0,00) – lampa nebo louč |
| `KrcmaL_Kour_Dymnik` | (0,60; 8,41; 0,00) – kouř z dymníku |

## Vložení do Godotu
1. `krcma_L.glb` dej na rovný terén. Dvůr je hlína bez modelu podlahy, s výjimkou stáje.
2. Kamenné části (podezdívka, stáj) mají saze, mech a vlhko v barvě vrcholů. Godot to obvykle zapne sám, jinak zapni v materiálu `M_ZdivoKamen` „Vertex Color → Use as Albedo“.
3. `KrcmaL_Interier_skupina` (vybavení a značky) jde vypnout, když je hráč venku. Stejně dál `KrcmaL_Exterier_skupina`.
4. Kolize: 80 kvádrů s příponou `-convcolonly`. Pokrývají stěny s průchody, podlahy, strop, pece, výčep, postele, pavlač, schody, plot a vrata.
5. LOD1 dej na stejné místo. Visibility Range: hlavní díl 0–70 m, LOD1 od 65 m.

## Výkon
- Celý díl má ≈ 172 000 trojúhelníků:
  - roubení ≈ 60 000
  - šindel ≈ 48 000
  - krov 19 000
  - kámen 27 000
  - dvůr 12 000
  - vybavení 10 000
- Na tablet: interiérovou skupinu vypínat, Visibility Range a occlusion culling.

## Historie
- Trojdílný dům (světnice, síň s černou kuchyní, komora) odpovídá archeologii vesnic 14. století (Svídna, Pfaffenschlag).
- Kouř z černé kuchyně odchází **dymníkem** v hřebeni, komín na vsi v roce 1393 ještě nebyl.
- Krčma měla od vrchnosti právo čepovat. Pivo se často vozilo z města kvůli mílovému právu, proto je tu komora se sudy a sklepem.
- Pokojíky pro hosty nad stájí jsou volnost ve stylu KCD. Běžný pocestný spal na slámě v nocležně nebo na seníku.
