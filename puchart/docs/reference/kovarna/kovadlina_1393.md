# Kovadlina 1393 (nová, čistá – bez meče a nářadí)

Míša 15. 11.: „kovadlinu chci novou, ale musí být vymazlená, krásný fotorealistický model … já chci čistou“,
„podívej se na KCD“, „opravdu fotorealistická, je to doplněk, který je vidět“. Nahrazuje Havranovu
`kovarna_kovadlina.glb` (měla na sobě meč).

## Předlohy (zdroj)
| Soubor | Co z něj |
|---|---|
| `kcd2_kovadlina_misa_15_11.jpg` (KCD2, **závazná**) | jeden kónický roh vpravo, pas, široká pata, plochá dráha s ostrou hranou, krátká hranatá patka s otvory, nízký široký špalek ~1 m, sperhák vedle kovadliny; dráha světlejší a lesklejší, boky tmavé okuje s jemnou rzí |
| `kcd1_kovar_trziste.jpg` (KCD1, z Havrana `docs/reference/kcd_13_11/kovar_kcd1.jpg`) | dubový špalek stažený železným páskem u horní hrany, sperhák ve špalku |
| `mendel_1425_kovar_fol47r.jpg` (Hausbuch der Mendelschen Zwölfbrüderstiftung, Nürnberg ~1425, Amb. 317.2° fol. 47r, public domain) | kovadlina na kulatém špalku, dráha ve výšce kovářova zápěstí, špalek ~2× širší než kovadlina |
| Worcester Art Museum (Higgins Armory) – kovadlina 14. st. (inv. 2014.1031), kovadlina 1400–1500 s otvorem pro sperhák | kovaná svářková kovadlina, otvor pro sperhák; rozměry na webu nejsou (NEOVERENO) |

Historie: REKONSTRUKCE/NAVRH – jednorohá kovadlina s patkou je v obrazech doložena až v 15. st.; roku 1393
byla běžnější špalková bez rohu. Tvar podle KCD2 na výslovné přání Míši.

## Soubory
- Zdroj: `blender/kovadlina.py` (`/opt/bl/bin/python blender/kovadlina.py . [--tex DIR]`), čísla a zdroje `pravidla/svet/kovadlina_1393.json`.
- Výstup (generovaný, `hra/modely/` je v .gitignore): `hra/modely/predmety_h/kovadlina_1393.glb` (podrobný),
  `kovadlina_1393_stredni.glb`, `kovadlina_1393_daleko.glb`; licence `hra/modely/predmety_h/LICENCE_kovadlina_1393.txt`.
- Snímky z Godotu: `docs/screens/kovadlina_1393_*.png` (srovnání s KCD2: `kovadlina_1393_srovnani_kcd2.png`).

## Rozměry (Godot: Y nahoru, dráha a roh podél +X, počátek na zemi uprostřed špalku) – 2. kolo 15. 11.
- Špalek: Ø ~1,1 m (poloměr 0,55, nepravidelný otlučený obrys), výška 0,32 m, zaoblená hrana 5 cm, **bez pásku** (pasek false);
  povrch z high-poly (síť trhlin voronoi F2−F1 v pokřivených souřadnicích jen místy, hrbolky fbm) zapečený do normály a AO –
  drsný, kamenitě rozpraskaný jako KCD2; šedohnědý, letokruhy tlumené.
- Kovadlina: dráha 0,78 m nad zemí (tělo 0,47 m – vyšší kvůli nižšímu špalku), šířka dráhy 0,15 m, dráha 0,58 + patka 0,17 + roh 0,36 m;
  pata 0,58 × 0,34 m sedí celou plochou (oblouk mezi patkami jen 12 mm), pas 0,40 × 0,15 m, boky skoro svislé; kramle vynechány (v KCD2 nejsou).
- Sperhák: x −0,45, z +0,20, 0,40 m nad špalkem.
- Barvy (3. kolo, Míša 15. 11.): dráha tmavší šedá ocel (sRGB 0,40–0,46, drsnost 0,5–0,62, kov 0,3), lesk (drsnost 0,36) jen v pruhu
  7 cm uprostřed dráhy, kde se kove – ve hře na odpoledním světle byla dráha 2. kola bílá; boky hnědé okuje s jemným zrnem, 28 otluků hran.
- Špalek (3. kolo): tmavé ohlazené dubové dřevo (tmavohnědé až černošedé od sazí), letokruhy na čele, okolí kovadliny začouzené se šupinkami
  okují – 2. kolo působilo jako světlý kámen (barvy čela byly zadané lineárně 0,40 = sRGB 0,67).
- High-poly voxel 2 mm (`high_voxel_m`; 1,6 mm potřebovalo ~2,2 GB paměti a při souběžných bězích Godotu ho zabíjel nedostatek paměti).

## Osazení ve hře
- `pravidla/svet/funkce.json` kovadlina: model + `_stredni` (od 8 m) + `_daleko` (od 22 m, do 60 m), značka `Kovarna_Kovadlina_misto`,
  natočení bokem dráhy (model −Z) ke značce `Kovarna_Kovar_stani` – kovář stojí mezi výhní a kovadlinou, roh má po levé ruce (KCD2).
- `hra/scripts/funkce.gd` `osad_kovadliny()` (volá `zacni`), kolize z uzlu `*-convcolonly`. Test `kovadlina_osazena` (PUCHART_JEN=kovadlina).
- Stavba: glb jsou v .gitignore – `nastroje/postav_vse.sh` je zatím nestaví (viz předání), ručně
  `/opt/bl/bin/python blender/kovadlina.py .` (~45 min, Cycles CPU) a import Godotu.

## Stupně a textury
| Stupeň | Trojúhelníky | Materiály / textury |
|---|---|---|
| podrobný | 16 160 | `kovadlina_zelezo` + `kovadlina_drevo`, každý albedo + normal + ORM 2048 px (3 vzorkovače na materiál) |
| střední `_stredni` | 2 716 | barva vrcholů + textury 512 |
| daleko `_daleko` | 462 | barva vrcholů + textury 256 |

Kolize: jeden uzel `Kovadlina_1393_kolize-convcolonly` (konvexní obal špalku, kovadliny a sperháku, 84 troj.).

## Srovnání s KCD2 (docs/screens/kovadlina_1393_srovnani_kcd2.png)
- 1. kolo: tvar sedí, ale tělo štíhlé (londýnský tvar), špalek vysoký s páskem, dráha modrá, boky černé.
- 2. kolo: mohutné svislé tělo se širokým pasem, pata přímo na špalku, nízký široký rozpraskaný špalek bez pásku – ale špalek světlý jako kámen
  a dráha ve hře bílá.
- 3. kolo: tmavý začouzený dubový špalek, tmavší dráha s úzkým pruhem lesku, jemné zrno okují. Zbývá: na přímém odpoledním slunci v otevřené
  kovárně jsou boky rezavě oranžovější než v KCD2 (tam teplé šero výhně).
