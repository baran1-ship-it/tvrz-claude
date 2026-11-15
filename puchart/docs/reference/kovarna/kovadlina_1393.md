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

## Rozměry (Godot: Y nahoru, dráha a roh podél +X, počátek na zemi uprostřed špalku)
- Špalek: Ø ~0,96 m (nepravidelný kmen), výška 0,42 m, zaoblená horní hrana, železný pásek 0,07 m pod vrchem, 7 hřebů.
- Kovadlina: dráha 0,78 m nad zemí, šířka dráhy 0,14 m, celková délka ~1,02 m (x −0,44 … +0,58: patka 0,17 + dráha 0,52 + roh 0,33), pata 0,46 × 0,31 m,
  pas 0,22 × 0,12 m; v patce hranatý otvor pro sperhák 26 mm a kulatý průbojník Ø 17 mm; 4 kramle přes patky.
- Sperhák: x −0,37, z +0,16 (před kovadlinou), 0,33 m nad špalkem.

## Stupně a textury
| Stupeň | Trojúhelníky | Materiály / textury |
|---|---|---|
| podrobný | 15 340 | `kovadlina_zelezo` + `kovadlina_drevo`, každý albedo + normal + ORM 2048 px (3 vzorkovače na materiál) |
| střední `_stredni` | 2 812 | barva vrcholů (predmety.gd) + textury 512 |
| daleko `_daleko` | 461 | barva vrcholů + textury 256, bez pásku a kramlí |

Kolize: jeden uzel `Kovadlina_1393_kolize-convcolonly` (konvexní obal špalku, kovadliny a sperháku, 82 troj.).

## Srovnání s KCD2 (docs/screens/kovadlina_1393_srovnani_kcd2.png) – co ještě zbývá
- Tvar sedí: jeden kónický roh, pas, patka s otvory, sperhák, světlá vyleštěná dráha × tmavé boky s rzí.
- KCD2 má mohutnější svislé tělo (pas širší) a nižší, plošší špalek s kamenitě rozpraskaným povrchem;
  náš špalek je vyšší (0,42 m dle zadání 0,4–0,5) a má pásek (KCD1). Úprava = čísla v kovadlina_1393.json a znovu postavit.
