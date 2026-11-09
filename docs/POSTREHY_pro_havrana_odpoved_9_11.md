# Puchart → Havran: odpověď na postřehy 9. 11. (co máme lepšího a na co jsme narazili)

## Sklepy a klenby
- **Klenba z klenáků s pojistkou stropu** (`blender/puchart_hrad.py` `klenba()`): segmentová valená klenba nad obdélníkem.
  - `y_strop` = assert, že rub klenby (patka + vzepětí + 1,5× tloušťka + výstupek reliéfu) neproroste podlahou nad ní.
    Chyba spadne už ve stavbě, ne až na snímku.
  - `diry` = otvor v klenbě (hladomorna: schody otvorem). Otvor přes celý pás nad schody, jinak klenák u hrany trčí nad podlahu.
- **Sklep pod palácem a šíje** (`sklep_A`): výkop v terénu je samostatná „jáma“ (`*_jamy.npz` z teren_upravy.py).
  - Terén se kolem jámy vyhladí, jako by nebyla, a pak se jáma vrátí s ostrou hranou. Bez toho se prolákla i síť za zdí.
  - Jáma je otvor ve viditelné síti terénu. Kolize jámy jde zvlášť (síť 2 m by ji zahladila).
  - Horní stupeň šíje: nástupní plotna v úrovni skutečného dvora, 2,6 m přes okraj jámy. Dřív byla poslední schod „díra“
    a postava se zasekla.
- **Schody – hlídač nástupu a výstupu** (SCHODY → build/schody*.json, test `schody_nastup_vystup`):
  - před nástupem a za výstupem každého ramene musí být 1 m volna v šířce ramene, ne zeď ani zábradlí;
  - kolize schodů = šikmá rampa přes hrany stupňů zapuštěná do terénu, viditelné stupně kolizi nemají;
  - schody ve věži stojí na podlaze patra (`podklad`), ne na terénu.
- **Trasy průchodu přes schody:** body vždy na ose ramene a „od zdi“, pak teprve nahoru. Úhlopříčka podél schodnice
  nebo zábradlí uvízne. Po přestavbě se trasy generují ze stejné geometrie (`TR[...]` v builderu, ne ručně).

## Voda a břehy
- **Koryto zaříznuté do terénu** (`nastroje/koryta.py`):
  - hladina = dno údolnice + hloubka a po proudu nikdy nestoupá (test `hladina_nestoupa`);
  - práh nastoupá jen krátce;
  - soutok: konec přítoku dostane hladinu hlavního toku s náběhem 8 m, bez schodu na hladině.
- **Jemný pás břehů** (BREH, `blender/voda.py`):
  - síť 1 m podél osy toku na skutečném terénu + 3 cm, materiál terénu;
  - pod ním se síť dlaždic 2 m sníží, aby břeh nebyl jak pila;
  - testy `teren_hra_pod_pasem`, `teren_shoda`, `voda_v_korytu`.
- **Hladina jako jedna síť** se sdílenými vrcholy:
  - UV.y = hloubka nad terénem → shader u břehu plynule zprůhlední a zuby průsečíku zmizí;
  - jemná hladina jen blízko, dál jednoduchý pás po kusech (proti „dvoubarevné hladině“ z visibility range).
- **Mosty v ose cesty** (konce přerušené cesty = konce mostovky):
  - sklon nejvýš 10 %, aspoň 0,6 m nad hladinou;
  - dřevěné opěry z kulatin a fošen a jařma – kusy celé pod terénem se nestaví (test pod_terenem);
  - k mostovce vede jen násyp cesty v terénu, žádné rampy (testy `nastup_mostu_v_terenu`, `most_navazuje_na_cestu`).
- **Brody:** cesty jsou u toku přerušené, takže osy toků a cest se nikdy nekříží. Brod = dva konce cest na protějších
  březích do 30 m. Spojka vede dnem koryta, terén se nemění, bez kamenů (kameny navíc vypadaly jako „děs“).

## Výkon na tabletu – jak hlídáme
- **Hlídač scén** (`nastroje/viditelnost.py` + test_sceny.gd + kontrola_scen.py):
  - body podél tras hráče, typ scény podle dohledu z DMR a stromů (A uzavřená / B polootevřená / C panoramatická);
  - na každém bodě se změří trojúhelníky a kreslení;
  - rozpočet podle typu je jen ze změřeného na tabletu (2,1 M troj, p95 35,7 ms);
  - výjimka jen s důvodem, kdo schválil a do kdy; prošlé výjimky shodí test;
  - doskok = náhlá změna obrazu proti okolí na trase.
- **Poslední dobrá verze** (`posledni_dobra.py`): když hlídači projdou, uloží se výsledky s commitem. Při selhání
  vypíše, co dřív procházelo a teď ne, s `git diff <commit>` k izolaci.
- **Panel měření:** p95 z razítek snímků (ne vyhlazené delta), záseky > 40 ms, trojúhelníky, kreslení a commit sestavy.
  Na tabletu bez dotazů na čas GPU (brzdí).
- **Matice vztahů** (vztahy.json testy_puchart): každá dvojice vrstev (terén/cesta/budova/voda/hráč/kolize…) má test.
  Díra v matici = chyba.

## Animace a úchopy postav
- Zatím nemáme, postavy jsou v Puchartu až krok F. Tady je náskok na straně Havrana a převezmeme ho od vás.

## Chyby, které vás můžou potkat
1. **Hash `fract(sin(...)*43758)` na Adreno** dělá čtverce po metru. Nahradit hashem bez sinu (Hoskins), vstup `mod(p,1024)`.
2. **Tečna projekce z normály buňky reliéfu** posouvá UV o metry, výsledek jsou čtverce. Pevné osy X/Z.
3. **Textury načítané skriptem** jsou bez mipmap a komprese. Hlídač na `.import` (Puchart `textury_3d_mipmapy`).
4. **Plížení výšky** (most ↔ terén se navzájem zvedají při každé stavbě) – držet výšku z minulé stavby.
5. **Vyhlazení terénu (gauss) stahuje úzké násypy a hrany** – násypy u mostů vyjmout z vyhlazení.
6. **Komentář doprostřed řádku seznamu v Pythonu** zakomentuje zbytek. Trasa pak tiše chybí a průchod hlásí nesmysl.
7. **Neviditelné stěny:** kolizní kvádr přes celou délku (zábradlí mostu, rampa) dál, než sahá viditelný díl.
   Ladění: env `PUCHART_DBGB="x,z,y"` vypíše kvádry obsahující bod a `PUCHART_DBG` jejich původ (funkce:řádek).
8. **Wikimedia** blokuje stahování přes sdílenou proxy (429 / robot policy). Funguje jen náhled ve standardní šířce
   (500, 960 px) a slušný User-Agent, případně přes WebFetch.
9. **Výpadek `\\` v regexu kontroly tabulky:** názvy tras s čísly a minusem (`budova_palac_-3_14`) tabulka chyb neviděla.
