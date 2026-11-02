# Rešerše ChatGPT 1. 11. (Míša poslala 20 snímků) – co z ní bereme pro Havrana

Zdroj: snímky obrazovky z ChatGPT (viditelnost a kompozice, sektory viditelnosti, filtr modelů, knihovny, pluginy).
Jsou to doporučení, ne ověřená fakta. Každé tvrzení z nich se ověří, než se podle něj změní kód.

## 1. Viditelnost: tři stupně jistoty zakrytí (shoda s Astrou 29. 10.)
- **Jisté zakrytí** (skála, hřeben, plná zeď, terén): objekty celé za ním se smí vyřadit. Máme zakrývač terénu a zdí
  domů.
- **Částečné zakrytí** (hustý remízek, skupina stromů): vzdálené objekty jen zjednodušit, nevyřazovat. Remízky a les
  mají zakrývače vypnuté (`pasma.test.okluzor_listi` false).
- **Nejisté zakrytí** (větve, řídké listí, tráva): standardní LOD a ořez záběrem kamery.
- **Poznatek k ověření:** automatické pečení zakrývačů v Godotu nezahrnuje MultiMeshInstance3D ani průhledné
  materiály. U nás to nevadí, protože zakrývače stavíme ručně (`svet._okluzory`) a stromy zakrývat nemají. Platí to ale
  i obráceně: jako zakrytý objekt se MultiMesh testuje celým AABB buňky, takže velká buňka se zakryje špatně
  (Astra: dělit prostorově).

## 2. Sektory viditelnosti (doplněk LOD)
- LOD odpovídá na otázku „jak detailní model potřebuji?“. Sektor viditelnosti odpovídá na otázku „potřebuji to teď
  vůbec kreslit?“.
- Před hráčem: plné LOD a aktivní objekty. Za remízkem: zjednodušení. Za skalním hřbetem: vyřazení. Mimo záběr:
  nekreslit, stav zachovat. Daleko: jen datová simulace NPC a zvířat, minimální fyzika.
- Postup bez přestavby krajiny:
  1. Mapa výhledů z cest a herních míst (`tools/mapa_vyhledu.py`, opravená 29. 10.).
  2. Změřit, co je odkud vidět.
  3. Vyhodnotit stávající stromy a remízky jako clony.
  4. Doplnit vegetaci jen tam, kde odpovídá krajině a nezakryje orientační body.
  5. **Načítání a LOD skupin podle skutečné viditelnosti.** Tohle je zásadní bod a zatím nemáme.
  6. Test na tabletu na stejné trase.

## 3. Hlídač dlouhých průhledů (NOVÉ – zavést)
- Nezakrývat každou dlouhou cestu stromy, ale označit místa, odkud je současně vidět několik drahých celků (ves, mlýn,
  tvrz, velký les).
- Takové místo dostane výkonový profil. Pořadí řešení: nejdřív lepší LOD, vyřazení zakryté geometrie a úspornější
  materiály, teprve pak přirozená vegetační clona.
- Některé výhledy zachovat za každou cenu (příjezd ke vsi a tvrzi, věž, Pustá skála).
- **Úkol:** rozšířit `mapa_vyhledu.py` o seznam drahých celků v dohledu z každého bodu (stavby z lokace.json,
  díly, ves) a o pořadí míst podle počtu drahých celků. Výstup porovnat s měřením kreslení na stejných bodech.

## 4. Filtr modelů (rozšířit stávající katalog `blender/predmety.py`)
Před přidáním modelu do hry:
1. Licence a historická vhodnost (druhy.json, test druhů).
2. Normalizace velikosti, orientace a měřítka (katalog: rozmer, zem0).
3. Kontrola a úprava materiálů.
4. LOD a jednoduché kolize (`DILY kolize`, `_kbox`).
5. Interakční třída.
6. Test v jednotné scéně se stejným osvětlením (náhled .png v katalogu).
7. Zápis do katalogu.

Pravidlo: jeden kvalitní model pro jeden konstrukční typ, další jen s odlišným vzhledem nebo funkcí. Žádných pět sudů
z různých her v jedné místnosti. U zbraní a příběhových předmětů víc rozmanitosti.

## 5. Knihovny modelů (k pravidlu „nejdřív hledat hotové“ v CLAUDE.md)
| Knihovna | Licence |
|---|---|
| Poly Haven | CC0 |
| BlenderKit | asi polovina zdarma, licence podle assetu |
| CGTrader Free | různé licence |
| 3DAssets.dev Medieval | deklarované bezplatné GLB |
| 3D Valley | katalog CC0 |
| Smithsonian 3D | vybrané CC0, muzejní skeny |
| Fab | různé licence |
| itch.io Medieval | různé licence |

U každého modelu ověřit licenci a autora zapsat do titulků. „Free download“ neznamená volné použití ve hře.

## 6. Pluginy (jen v oddělených zkušebních projektech, přijmout jen když prokazatelně pomohou)
- **Rigger** (kostry včetně koní a čtyřnožců, přenos animací): nejzajímavější pro zvířata a koně. Vyzkoušet zvlášť.
- **ProtonScatter:** rozmísťování s negativními oblastmi. Máme vlastní rozmísťování z dat, jen pro porovnání.
- **Building Tools** (Blender): geometrie budov. Správnost staveb dál hlídají naše pravidla.
- **LimboAI** (chování NPC), Dialogue Manager, SaveKit, Phantom Camera, PankuConsole: až podle potřeby, s kontrolou
  výkonu.
- **Terrain3D 1.1** deklaruje podporu mobilů. Jen samostatný experiment, ne náhrada (Míša: teď ne).
- **Upozornění:**
  - Blender 4.2 v cloudu vs. doplňky jen pro Blender 5 (Retarget KBS-DEV).
  - Jolt je v Godotu integrovaný, otestovat dostupný backend, ne starou GDExtension.
- **Oficiální demo Godotu** pro okluzi a LOD: srovnávací měření (Asset Library).

## 7. Priorita (ChatGPT, shoda s manuálem)
Malá kompletní hratelná oblast se všemi systémy (tvrz, okolní les, mlýn, pár NPC), která drží 30 FPS na Xiaomi.
Teprve potom rozšiřovat. Svoboda a interaktivita (okna, sezení, mlýn, vědro, vrata, oheň) mají přednost před
fotorealismem.
