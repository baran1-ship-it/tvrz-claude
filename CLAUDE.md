# Odkaz Havrana – pravidla pro každou session

Předání a podrobnosti: `docs/predani.md` (přečíst na začátku). Rádce píše do `docs/radce.md` (před čtením `git pull`).
S Míšou česky.

## Nečekat (Míša 25. 10.: „pravidlo navždy, ať nečekáme jak blbci… všude“)
- Nic dlouhého neběží v popředí a nikdy se nečeká se založenýma rukama. Godot (testy, focení, vydání) jen přes
  `tools/beh.sh … ` na pozadí (`run_in_background`), na výsledek upozorní oznámení – žádný `sleep`, žádné dotazování.
- Během běhu se dělá další práce: další úprava, poznámka rádci, příprava vydání, commit. Co na výsledku nezávisí, nečeká.
- Nezávislé věci najednou (paralelní volání nástrojů, víc úprav v jednom kroku).
- Testovat jen lehce (snímek opraveného místa + test, který se ho týká); celou sadu ne, zbytek dělá Míša na tabletu.
- Když něco spadne: příčinu opravit hned a zapsat do `docs/predani.md`, ať se neopakuje – ne jen pustit znovu.
- Míše psát krátce, co se děje, a nečekat na potvrzení u věcí, které už zadala.
- Míša 28. 10.: když něco běží, hned dělat další bod plánu (seznam v odpovědi „co ještě dle plánu“, tabulka
  `docs/rozpracovane/misa_28_chyby.md`, úkoly) – nikdy nekončit tah jen „čekám na výsledek“, dokud je v plánu práce.

## Jeden agent, úkol po úkolu (Míša 23. 11., po limitu vyčerpaném 4 pomocníky za hodinu)
- Práci dělá hlavní agent sám, úkol po úkolu, a každý výsledek si sám zkontroluje (snímek + test toho místa).
  Žádné týmy pomocníků na běžnou práci: každý si znovu načítá kód a podklady (až 5× dražší), šlapou si do souborů.
- Pomocník (subagent) jen na: nezávislou kontrolu před vydáním (nezná závěry stavitele) a rozsáhlé hledání
  v mnoha souborech, kde stačí závěr. Nanejvýš jeden najednou.
- Testy s mírou: po každé změně `tools/rychle.sh` + testy dotčené skupiny; celá sada a export až na konci větší části.
- **Vzory toho, co se povedlo** (`docs/vzory.md`): když Míša něco pochválí nebo se část povede (ves, voda Hvozd…),
  rozebrat, jak vznikla (data, pravidla, postup, snímky), a zapsat jako vzor. Podobná práce začíná přečtením vzoru.

## Regrese a měření verzí (Míša 2. 11.: „příště nemusím já hledat, co rozbilo hru“)
- Každé vydání: Míša projede **Nastavení → Měřicí trasa** (`pravidla/svet/mereni_trasa.json`), tabulka se zapíše do
  `docs/mereni_verze.md` k verzi a commitu. Bez záznamu je výkon verze NEOVĚŘENO NA ZAŘÍZENÍ.
- Při regresi: poslední dobrá a první špatná verze z `mereni_verze.md` → rozdíl commitů → hypotézy → izolovaný test
  (varianta trasy s vypnutou skupinou) → teprve oprava. Rozlišovat podezření / naměřený vliv / potvrzenou příčinu /
  ověřenou opravu; hypotézu nikdy nevydávat jako opravu.
- Po dvou neúspěšných opravách téže chyby žádný třetí pokus: nový rozbor příčiny (typicky rozpor Blender × Godot,
  `docs/rozpracovane/rozpory_blender_godot.md`).
- Před vydáním nezávislá kontrola změn a snímků samostatným subagentem (nezná závěry stavitele).

## Další stálá pravidla
- **Záplatování zakázáno** (Míša 27. 10.; rádce 09:55 PRAVIDLA ZASAZENÍ): každý díl (cesta, budova, voda, skála) je
  záznam v datech; stavba v pevném pořadí terén → cesty → budovy → voda → vegetace → předměty, pozdější krok nehýbe
  dřívějším; odstupy jen z `pravidla/pravidla_sveta.json` `pasma`, v kódu žádná vlastní čísla; test `zasazeni` musí
  projít před vydáním. Chyba = oprav záznam nebo pravidlo a postav znovu, ne další výjimka.
- **Test smyslu před exportem** (rádce 27. 10. 20:50, Míša „už nechci vidět cestu pod mostem, levitující trávu…“):
  `/opt/bl/bin/python tools/test_smyslu.py` musí projít, jinak se export nespouští. Povrch a rostliny podle užívání
  a stanoviště (`pravidla/svet/druhy.json`), nic živého ve vodě, stavby ne ve vodě/na cestě/svahu, cesta přes vodu jen
  s přechodem. Každá nová chyba, kterou najde člověk = nová kontrola v testu, ne jen oprava.
- **Hlídači a mapa stavby** (Míša 28. 10.): postup v `docs/pipeline.md` „Hlídači a mapa stavby“ – každá změna světa projde
  vrstvami 0–7, před snímky se prohlédne `build/mapa_stavby.png`, chyba od člověka = řádek tabulky s kontrolou v testu.
- **Godot soubory, snímky, čísla** (28. 10., radce.md 19:55): ruční úpravy .tscn/.tres/.uid jen podle pravidel tam (žádné vymyšlené uid://, po úpravě `--import`); po změně scény snímek `--write-movie` a **podívat se na něj sám, než se pošle**; nezměřené číslo = NEOVĚŘENO, nikdy odhad.
- Nejdřív se podívat do světa (KCD2 apod., rešerše), nic nedělat z hlavy.
- **Než se něco vytvoří, hledat hotové** (Míša 28. 10.): Míšin Disk (složka Modely), Poly Haven, ambientCG, Quaternius, Kenney,
  Sketchfab (CC0/CC-BY, autor do titulků), Godot Asset Library, hotové postupy her (KCD2 modding dokumentace Warhorse) –
  vlastní model, textura nebo systém až když nic nesedí (zapsat, kde se hledalo). Kopírovat z her nesmíme, inspiraci ano.
- Tablet: nikdy MSAA, žádné shadery se screen texture; vždy modely, ne primitiva.
- **Rozlišení 3D** (Míša 6. 11. „plný obraz“, `docs/ZAVER_tablet_grafika.md` §0; Míša 9. 11. po měření 0.99995
  „můžeš snížit rozlišení“): tablet pevně 75 % (`pravidla/svet/kvalita.json` `meritko_3d`), výkon se dál hledá u příčiny
  (záseky skriptů, světla, LOD, rozpočty); automatická kvalita jen v extrému (teplo, dlouhý pokles pod 33,3 ms) a ubírá
  detail, rozlišení za běhu **nemění** (zásek 1,36 s).
- Podpisový klíč nikdy do repa (záloha na Disku – oddíl „Záloha hry na Disk“).
- **Čas u zpráv a vydání** (Míša 6. 11.: „nevšiml jsem si, že jsi vydal další verzi, nemáš časy v chatu“): zprávu o vydání
  začínat „**Vydáno 0.NN – <den. měsíc> <hh:mm>**“ (český čas, `TZ=Europe/Prague date`), i v dalších zprávách uvádět,
  o jakou verzi jde.
- **Po vydání vždy odkaz na APK v samostatném bloku kódu** (Míša 28. a 29. 10.: „dej mi odkaz jako vždy a pamatuj si to“):
  ```
  https://github.com/baran1-ship-it/tvrz-claude/raw/claude/new-session-0dtk58/apk/OdkazHavrana-0.NN.apk
  ```

## Záloha hry na Disk (Míša 15. 11., stejně jako Puchart)
- Po každém velkém updatu se Míši **zeptat**, jestli udělat zálohu. Plný instalátor vytvořit až po souhlasu (nebo když o něj řekne).
- Plný instalátor = APK se VŠEMI herními daty uvnitř (preset Android bez vyloučení dat, exclude jen co hra nepotřebuje);
  ověřit, že hra data najde v sobě a stahování přeskočí; podepsat stejným klíčem jako normální APK.
- Konektor Disku nahraje jen soubory do 10 MB (ověřeno 15. 11.: 3 MB ano, 120 MB ne), SendUserFile do 400 MB → plnou APK zabalit
  do 7z po 350 MB (py7zr + multivolumefile, bez komprese, `.7z.001`, `.002`…), ověřit (testzip) a poslat části do chatu;
  Míša je uloží sám do `Havran – zálohy/<RRRR-MM-DD>`.
- Místo v kontejneru: data ~2,8 GB, plná APK + podpis + části ~3× → uklízet průběžně (nepodepsanou APK po podpisu,
  APK po zabalení, části po odeslání); před začátkem ověřit volné místo.
- Disk: složka `Havran – zálohy` id `1vD7RqXebuH6M0iGGRf0slPcMkdjvt078`, `Klíč podpisu (nemazat)` id
  `19UqHChWeoeAoSUaXjJykZVmTSrEevzR3`, keystore `tvrz_release.keystore` id `1VAHCni81ekYxURpF9KYElBfnG5LcLDSF`,
  návod `CTI_ME – jak obnovit hru.txt` id `1c47D3aNa3VlKRCp47kvUqpvaolIkznCw`.
- **Klíč podpisu:** `/root/keys/tvrz_release.keystore`, alias `havran`, otisk certifikátu SHA-256
  `C6:1B:DC:1E:35:2B:3A:DC:58:63:4A:B1:E4:C2:5C:FB:B5:FE:91:B3:BA:3D:C5:AE:18:24:06:13:3B:EC:6C:59`, sha256sum souboru
  `df68e8c320a8400576d37ba94229ed22cbb95db6785fca9e6721240872546065` (heslo v tools/vydani.py a v návodu na Disku).
  **Před každým exportem/vydáním v nové session** ověřit `keytool -list -v` otisk; chybí-li soubor, stáhnout ho z Disku (id výše)
  do `/root/keys/` a ověřit sha256sum. Klíč nikdy do repa.
