# Univerzální technický manuál (Míša 3. 11., v1.0) – audit Puchartu podle části X (máme? funguje? důkaz problému?)

| část | máme | stav / důkaz | co dál |
|---|---|---|---|
| 3 buňky | terén dlaždice 250 m + 4 LOD, byliny/keře buňky s předstihem, kolize kmenů 16 m, kolize terénu kolem hráče | funguje, hranice bez děr (teren_shoda, sukně) | velikost neměnit bez důkazu |
| 4/20 logika ≠ grafika | dveře/vrata: stav v dvere.gd, kolize z dat (pohyb.json) | funguje (pruchod:vrata_funkce) | stav ukládat (až bude ukládání) |
| 5 jedna definice polohy | stavitel píše pohyb/pruchody/stavby_kontrola/clony ze stejné geometrie; terén = jedna pravda výšek (3. 11.) | funguje (teren_shoda, povrch_kolize) | – |
| 6–8 streaming | dlaždice + kolize okolí, byliny ve vlákně s rozpočtem na snímek | funguje, záseky pryč (měření L) | předstih podle rychlosti až s koněm |
| 9 .pck ≠ streaming | ano – balík jen distribuce | — | správně pojmenováno |
| 10 test paměti A→B→C→B→A | **chybí** | bez důkazu problému (VRAM ~300 MB stabilní) | zařadit: test trasy v měřicí APK |
| 12/13 skály, architektura | skaly.py z DMR, kolize = viditelná síť; hlídače geometrie, opory, povrch | funguje | – |
| 14 tři reprezentace | stromy 3 (plný/impostor/karta), hrad **2** (plný do 60 m, daleko) | hrad: zjištěno 3. 11. (daleko se nenačítal) | střední LOD hradu až s měřením |
| 15 vegetace – pořadí měření | ano (Havran poučení, PUCHART_SKRYJ izolace vrstev) | — | — |
| 16 shadery | ≤13 vzorkovačů, žádný discard v terénu (šachta řešena sítí) | — | profil shaderů A/B při podezření |
| 17 grafické profily | **chybí** (jen 3D scale) | bez důkazu potřeby | připravit až pro PC/slabší zařízení |
| 18 scény | systém scén + hlídač; rytmus cesty | další verze (docs/reference sceny_3_11) | — |
| 19 NPC úrovně | zatím nejsou NPC | — | krok F |
| 21–23 testy, regrese | rychlé (pre-commit), integrační, výkonové (scény), regrese proti dobré verzi (posledni_dobra.py) | funguje | – |
| 24 kontrola kontrol | **chybí** záměrné chyby | QA zamítnutí ukázalo riziko samoschválení | **zařadit první**: sada záměrných chyb v izolované kopii, hlídači je musí zachytit |
| 26 důkazy místo „hotovo“ | zprávy: co, proč, commit, testy | částečně | držet |
