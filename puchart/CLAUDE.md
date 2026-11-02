# Puchart 1393 – pravidla pro každou session

Složka `puchart/` v repu `tvrz-claude` (Míša 29. 10.: „ve starém si udělej složku“). Nová hra na skutečném terénu Potštátska
se zkušenostmi a materiály z Odkazu Havrana (větev `claude/new-session-0dtk58`). Podklad: PDF „Puchart – Oldřich, Boček
a kluk ze vsi“ 1.0 (shrnutí `docs/NAVRH_HRA_A_GRAFIKA.md`). Předání a stav: `docs/predani.md`. S Míšou česky, krátce. **Odkazy na APK: každý ve vlastním bloku kódu** (Míša 2. 11.: ne oba v jednom okně). Testovací a procházková APK mají různé balíčky (cz.puchart.test / cz.puchart.prochazka), jinak se přepíšou. **APK nevydávat, dokud Míša neschválí snímky** (Míša 2. 11.: „nejdřív chci vidět fotky“). **Herní data mimo APK** (Míša 2. 11., jako Havran): APK ~30 MB jen kód a nastavení, modely/textury/terén jako balík `.pck` po částech < 90 MB v `puchart/data/` (`nastroje/data_balik.py`, volá `export_apk.sh`), hra si ho stáhne při prvním spuštění (`hra/scripts/data.gd`, manifest `hra/data_manifest.json`); balík se přestaví jen při změně zdrojů. Data do repa pushnout dřív než APK.

## Zadání Míši (29. 10.)
- Nové repo/složka, **začátek výsekem 2×2 km**, příběh teď ne – jde o grafiku a hru.
- Pracovat **detailně s ohledem na zkušenosti z tvrze (Havran) a KCD**.
- **Hrady: nejdřív návrhy ke schválení**, styl KCD, reálné, ale neortodoxní (přesnou podobu neznáme) – **propojené a krásné**.
- Postavy později, **realističtěji** než Quaternius v Havranovi.

## Pořadí (PDF kap. 12): KRÁSA → FUNKCE → POSTAVY, kroky A–F
A podklady → B hmoty světa → C podoba krajiny → D dálka a načítání → E funkce → F lidé. Každý krok končí snímkem
a měřením; tablet měří Míša.

## Pravidla převzatá z Havrana (platí od prvního dne)
- **Data místo čísel v kódu.** Každé číslo světa je v `pravidla/svet/*.json` s popisem a zdrojem. Kód je čte.
- **Žádné záplaty.** Díl světa = záznam v datech. Pevné pořadí stavby terén → cesty → budovy → voda → vegetace → předměty;
  pozdější krok nehýbe dřívějším. Chyba = oprav záznam nebo pravidlo a postav znovu.
- **Svět se peče, tablet jen načítá** (Havran: stavba při startu 83–110 s, halda nad 1,25 GB). Nástroje v `nastroje/`,
  celá stavba `bash nastroje/postav_vse.sh`. Generované soubory nejsou v gitu (.gitignore), postup ano.
- **Tablet:** Godot 4.7.2 Compatibility (A/B test 30. 10.); nikdy MSAA, žádná kopie obrazovky v shaderu (pády Havrana 0.58–0.59), materiál
  ≤ 13 vzorkovačů (Adreno), stíny jen 40 m, rozpočty `pravidla/svet/rozpocty.json`.
- **Nezměřené číslo = NEOVERENO**, nikdy odhad vydávaný za měření. Snímek po každé změně scény si nejdřív prohlédnout sám.
- **Než se něco vytvoří, hledat hotové:** modely Havrana (`modely/nove`, větev assets, Míšin Disk „Modely“), Poly Haven,
  ambientCG, Quaternius, Kenney, Sketchfab CC0/CC-BY (autor do titulků). Z her nekopírovat, inspirace ano.
- **Historie:** značení DOLOZENO / REKONSTRUKCE / NAVRH u každého dílu (`pravidla/svet/lokace.json`, katalog
  rekonstrukcí). Rok 1393: žádné cihly ani štěrk na venkově, droba/břidlice (ne pískovec), šindel a došek.
- Dlouhé běhy Godotu na pozadí, mezitím dělat další práci (Havran „Nečekat“).
- **Test průchodu před každou APK** (`PUCHART_TEST=pruchod`, trasy z `hra/data/pruchody.json`); kritické selhání
  blokuje APK. Každá chyba nalezená člověkem = regresní test nebo trasa. Průchod nedokazuje správnou geometrii –
  vztahy most–brána–cesta, schody–podesta, dveře–otvor, sklep–výkop–vegetace kontrolovat zvlášť.
- **Kontrola přiměřená změně** (rozbor 1. 11.): drobná změna = jeden dotčený pohled/trasa; celá sada před vydáním.
- **Měření:** stejná trasa, stejná sestava (commit v panelu), výsledky ve dvou rozlišeních 3D; 30 FPS = 33,3 ms,
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
