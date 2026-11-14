# Hájovna – Odkaz Havrana (Čechy 1393)

Roubená chalupa panského hajného v lese a kolem ní jeho pracovní dvorek. Pevné vybavení je v modelu.
**Luky, nože, kůže na zemi, nádobí a zvěř jsou z vaší hry.**

Měřítko je 1 jednotka = 1 m, osa Y nahoru. **Počátek je na terénu uprostřed domu**, vchod je na **+Z**. Podlaha jizby je +0,45.

## Soubory
- `hajovna.glb`, `hajovna_lod1.glb`, `hajovna.blend`
- `hajovna.py` (+ `_stavba.py`, `tesar.py`, `_spolecne.py`)

## Co v ní je
| Část | Kde (Godot x, z) | Obsah |
|---|---|---|
| Jizba 5 × 6 m | x −4,5 … 0,6 | hliněná pec, postel (spaní hráče), lavice, police, kolíky na luk, toulec a plášť |
| Síň | x 0,6 … 4,5, vpředu | vchod, ohniště u pece, dým jde dymníkem v hřebeni, žebřík na půdu |
| Komora | x 0,6 … 4,5, vzadu | police, bidlo s háky na sušení masa |
| Přístřešek | západ, pod přetaženou střechou | dva rámy s napnutými kůžemi, srovnané dříví |
| Šibenice na zvěř | (2,6; 6,3) | dva sloupy, břevno s provazem a hákem, stůl na vyvrhování, špalek |
| Psí kotec | x 5,2 … 8, vpravo od domu | plot z prutů propletených mezi nestejnými kůly, bouda, korýtko |
| Kůlna | za domem | dříví pod pultovou stříškou |
| Okolí | | proutěný plot kolem dvorku, třetí rám s kůží, parohy na štítku nad oknem, lavice u stěny |

## Dveře (počátek v pantu, kolem Y)
`Hajovna_Dvere_Vchod` (dovnitř), `Hajovna_Dvere_Jizba` (ven), `Hajovna_Dvere_Komora` (ven). Extras: `otevreni_deg`, `otevira_se`.

## Značky (Godot x, y, z)
| Uzel | Poloha |
|---|---|
| `Hajovna_Spani_Hrac` | (−3,30; 1,05; −2,25) |
| `Hajovna_Hajny_stani` | (−1,50; 0,45; 0,50) |
| `Hajovna_Ohen_Sin` | (1,45; 1,05; −2,00) – světlo a oheň |
| `Hajovna_Kour_Dymnik` | (2,60; 7,16; 0,00) |
| `Hajovna_Pes` | (6,35; 0,05; −0,95) – místo pro psa |
| `Hajovna_Zver_hak` | (2,60; 1,45; 6,30) – sem pověsit srnu nebo kance |

## Vložení
1. Polož na rovné místo v lese. Model nemá terén, dvorek je udusaná hlína tvého terénu.
2. Podezdívka (kámen ze skenu) má mech v barvě vrcholů, případně zapni „Vertex Color → Use as Albedo“.
3. Kolize: 40 kvádrů `-convcolonly` (stěny, pec, postel, ohniště, ploty, kotec, šibenice, stůl, kůlna, sloupy přístřešku).
4. `Hajovna_Interier_skupina` jde zvenku vypnout. LOD1 dej na stejné místo, Visibility Range 0–60 m a od 55 m.

## Výkon
- Celkem ≈ 132 000 trojúhelníků. Z toho okolí 84 000: proutěné ploty (každý prut je samostatně proplétaný), kůže, dříví a šibenice.
- Kdyby to na tabletu bylo moc, nejvíc ušetří vypnutí proutěného plotu kolem dvorku. Je v `Hajovna_Okoli` a dá se oddělit v .blend.

## Historie
- **Hajní** jsou v Čechách doloženi ve 14. století. Majestas Carolina (1355) počítá s hajnými a lovčími, kteří hlídají panské lesy a prodávají dřevo. Zákoník sice neprošel, ale úřad hajného existoval.
- **Kůže na rámech, šibenice na zvěř a pes:** hajný chránil les a zvěř před pytláky a pro pána obstarával zvěřinu. Odpovídá to tábořištím hajných v KCD.
- **Paroží na štítku** jako trofej je spíš dnešní zvyk než doložená věc z roku 1393, je tu kvůli atmosféře. Můžeš ho vypustit.
