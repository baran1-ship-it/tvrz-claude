# Puchart 1393 – pravidla pro každou session

Složka `puchart/` v repu `tvrz-claude` (Míša 29. 10.: „ve starém si udělej složku“). Nová hra na skutečném terénu Potštátska
se zkušenostmi a materiály z Odkazu Havrana (větev `claude/new-session-0dtk58`). Podklad: PDF „Puchart – Oldřich, Boček
a kluk ze vsi“ 1.0 (shrnutí `docs/NAVRH_HRA_A_GRAFIKA.md`). Předání a stav: `docs/predani.md`. S Míšou česky, krátce. **Vydává se jen jedna APK – testovací** (měření, pak naběhne hlavní nabídka jako v Havranovi – Příběh / Pískoviště, Míša 12. 11.; Míša 2. 11.: „šetřeme, vždy jen jedna“); odkaz ve vlastním bloku kódu. Testovací a procházková APK mají různé balíčky (cz.puchart.test / cz.puchart.prochazka), jinak se přepíšou. **APK nevydávat, dokud Míša neschválí snímky** (Míša 2. 11.: „nejdřív chci vidět fotky“). **Herní data mimo APK** (Míša 2. 11., jako Havran): APK ~30 MB jen kód a nastavení, modely/textury/terén jako balík `.pck` po částech < 90 MB v `puchart/data/` (`nastroje/data_balik.py`, volá `export_apk.sh`), hra si ho stáhne při prvním spuštění (`hra/scripts/data.gd`, manifest `hra/data_manifest.json`); balík se přestaví jen při změně zdrojů. Data do repa pushnout dřív než APK.

## Zadání Míši (29. 10.)
- Nové repo/složka, **začátek výsekem 2×2 km**, příběh teď ne – jde o grafiku a hru.
- Pracovat **detailně s ohledem na zkušenosti z tvrze (Havran) a KCD**.
- **Hrady: nejdřív návrhy ke schválení**, styl KCD, reálné, ale neortodoxní (přesnou podobu neznáme) – **propojené a krásné**.
- Postavy později, **realističtěji** než Quaternius v Havranovi.

## Pořadí (PDF kap. 12): KRÁSA → FUNKCE → POSTAVY, kroky A–F
A podklady → B hmoty světa → C podoba krajiny → D dálka a načítání → E funkce → F lidé. Každý krok končí snímkem
a měřením; tablet měří Míša.

## Pravidla převzatá z Havrana (platí od prvního dne)
- **Havran je laboratoř, Puchart bere jen odzkoušené a posouvá to výš** (Míša 3. 11.): hotové řešení z Havrana převzít
  (studna, pásma u zdí, cesty, hlídače), ověřit našimi hlídači a jeho chyby opravit u zdroje – ne vymýšlet znovu.
- **Data místo čísel v kódu.** Každé číslo světa je v `pravidla/svet/*.json` s popisem a zdrojem. Kód je čte.
- **Žádné záplaty.** Díl světa = záznam v datech. Pevné pořadí stavby terén → cesty → budovy → voda → vegetace → předměty;
  pozdější krok nehýbe dřívějším. Chyba = oprav záznam nebo pravidlo a postav znovu.
- **Svět se peče, tablet jen načítá** (Havran: stavba při startu 83–110 s, halda nad 1,25 GB). Nástroje v `nastroje/`,
  celá stavba `bash nastroje/postav_vse.sh`. Generované soubory nejsou v gitu (.gitignore), postup ano.
- **Tablet:** Godot 4.7.2 Compatibility (A/B test 30. 10.; Vulkan/Mobile renderer v Havranovi (Godot 4.4) vždy spadl při vstupu do hry, příčina nezjištěna – zatím Compatibility, diagnóza v docs/kcd_grafika_tablet.md); nikdy MSAA, žádná kopie obrazovky v shaderu (pády Havrana 0.58–0.59), materiál
  ≤ 13 vzorkovačů (Adreno), stíny jen 40 m, rozpočty `pravidla/svet/rozpocty.json`.
- **Krása i plynulost** (Míša 6. 11.; 12. 11.: „100 % je zbytečných, potřebujeme 75“): 3D výchozí 75 % (rozpocty.json obraz_3d), rozlišení si pak nastavuje hráč (Nastavení → Obraz 3D, ukládá se); výkon u příčiny. Automatika (snížení detailu,
  ne rozlišení) jen v extrémních situacích (teplo, dlouhý pokles FPS), po zchladnutí zpět. Závěr: docs/ZAVER_tablet_grafika.md.
- **Nezměřené číslo = NEOVERENO**, nikdy odhad vydávaný za měření. Snímek po každé změně scény si nejdřív prohlédnout sám.
- **Nic z hlavy – vždy podle reference** (Míša 3. 11.: „platí jako pravidlo pro všechno“): před úpravou vzhledu najít
  fotky (Havran `docs/screens/ref_kcd2_*`, `docs/screens/reference/kcd1/`, `docs/reference/` zde) a do dat zapsat `zdroj`
  (kterou fotkou se pravidlo řídí). Rozdíl proti referenci ukázat snímkem ze hry.
- **Stavím jako stavitel, tesař, truhlář a kovář** (Míša 3. 11.): každý dřevěný/kovový/kamenný díl podle doložené řemeslné praxe (docs/reference/): tesařské spoje (čep a dlab, plátování, osedlání, kolíky) – trámy se nikde neprostupují „jako vrostlé“; vlákna podél dílu, čela s letokruhy; kování a hřeby jak je kovář dělal; schody, ochozy a vstupy podle toho, jak se na hradech skutečně chodilo (např. patro brány portálkem z ochozu – docs/reference/branka_ochoz.md). Před stavbou objektu nejdřív rešerše, pak Havran jako základ, pak teprve kód.
- **Pořadí při stavbě čehokoli (Míša 10. 11., pravidlo):** nic jen z hlavy – 1) nejdřív Havran (kód, data, modely, předměty),
  2) pak KCD (fotky docs/reference/kcd_vzhled, kcd2), 3) pak internet (reálné fotky, prameny); teprve potom stavět.
- **Chyba v prvku, který mají i jiné stavby, se opravuje všude** (Míša 10. 11., pravidlo): zábradlí, schody, okna, dveře,
  ochozy, střechy… – oprava ve společné funkci nebo kontrola na všech stavbách obou hradů (a test, který to hlídá všude).
- **Než se něco vytvoří, hledat hotové:** modely Havrana (`modely/nove`, větev assets, Míšin Disk „Modely“), Poly Haven,
  ambientCG, Quaternius, Kenney, Sketchfab CC0/CC-BY (autor do titulků). Z her nekopírovat, inspirace ano.
- **Historie:** značení DOLOZENO / REKONSTRUKCE / NAVRH u každého dílu (`pravidla/svet/lokace.json`, katalog
  rekonstrukcí). Rok 1393: žádné cihly ani štěrk na venkově, droba/břidlice (ne pískovec), šindel a došek.
- Dlouhé běhy Godotu na pozadí, mezitím dělat další práci (Havran „Nečekat“).
- **Hlídači před každou APK** (`bash nastroje/hlidaci.sh`, volá ho `export_apk.sh`): geometrie (nic nevisí), test smyslu,
  test průchodu, hlídač scén, matice vztahů (`vztahy.json` testy_puchart), tabulka chyb. Selhání = APK se nestaví.
  Každá chyba od Míši = řádek v `docs/chyby.md` + test, který ji hlídá (smysl:/pruchod:). Po přestavbě vždy import Godotu.
- **Test průchodu před každou APK** (`PUCHART_TEST=pruchod`, trasy z `hra/data/pruchody.json`); kritické selhání
  blokuje APK. Každá chyba nalezená člověkem = regresní test nebo trasa. Průchod nedokazuje správnou geometrii –
  vztahy most–brána–cesta, schody–podesta, dveře–otvor, sklep–výkop–vegetace kontrolovat zvlášť.
- **Kontrola přiměřená změně** (rozbor 1. 11.): drobná změna = jeden dotčený pohled/trasa; celá sada před vydáním.
- **Měření:** stejná trasa, stejná sestava (commit v panelu), měření je nástroj vývoje – měří, co je potřeba zjistit (Míša 12. 11.), nemění nastavení hráče a po konci ho vrátí; teď trasa v 75 % + varianty vrstev lesa (hra/data/mereni.json); 30 FPS = 33,3 ms,
  p95 40 ms je mezicíl. Halda je debug metrika, ne PSS.
- **Modelový filtr** pro každý cizí model: licence a historická vhodnost → měřítko/orientace → materiály → LOD + kolize →
  interakce → test ve stejném světle → katalog. Jeden kvalitní model na konstrukční typ.

## KCD jako měřítko (princip, ne kopie)
- Věci stojí tam, kde dávají praktický smysl (PDF kap. 5). Hrad je výrazný, krajina mezi velkými momenty klidná.
- Vesnice obydlená cestami, zvuky, stopami práce. Opotřebení ukazuje používání, ne plošný rozpad.
- Les z dálky = koruny, ne fotka opadu; kopec v 300 m má barvu toho, co na něm roste.

## Souřadnice
S-JTSK (EPSG:5514) → hra: `x = X − pocatek.X`, `z = −(Y − pocatek.Y)`, `y = H − pocatek.H`; počátek = přední hrad
(`pravidla/svet/svet.json`). Hra: x východ, z jih, y nahoru.

## Snímek
`cd hra && PUCHART_FOTO="x,z,nad_terenem,cil_x,cil_z,cil_nad;soubor.png" xvfb-run -s "-screen 0 1600x1000x24" godot --rendering-driver opengl3 --resolution 1600x1000`
