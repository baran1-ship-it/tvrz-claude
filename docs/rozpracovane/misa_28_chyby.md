# Míša 28. 10. – chyby z tabletu (0.97) → pravidlo + kontrola v testu

Míša: „Nelep jen díry, chce to podle tabulek, ať to má smysl.“ Každý řádek = příčina v datech/pravidlu,
oprava v jednom místě (tabulka nebo generátor) a nová kontrola v testu smyslu / zasazení. Ne výjimka v kódu.

| # | Co Míša viděla (místo) | Příčina (zjištěno) | Pravidlo / tabulka | Kontrola v testu | Stav |
|---|---|---|---|---|---|
| 1 | Bílé pásy místo vody: odtok rybníka, náhon a lednice mlýna (484,875; 339,888; 535,889) | `kraj.toky_voda` nedávala barvy proudu; shader `voda` (tekoucí) čte R jako pěnu, export dal R≈0,9 → celá hladina pěna | hladina toku má barvy proudu jako Bystřice (R pěna, G peřej, B/A směr) – `kraj._toky_proud` | test smyslu --po: tekoucí hladina s průměrnou pěnou > 0,3 = chyba | opraveno v generátoru, čeká export |
| 2 | Řeka skoro bez vody, lom (189,922) „zničený“ hlubokým zářezem | na tabletu starý balík z_reka (27. 10. 11:23, před přesunem Bystřice): hra schovala hladinu z exportu a kreslila starou; brod u lomu bral dno podle staré hladiny (−8,3 místo −4,5) → vykopal 4 m zářez přes lom | předpečený potok jen se stejným `reka_otisk` (svet.json z exportu = reka.json z pečení); dno brodu podle viditelné vody jen do `pasma.test.brod_odchylka_max_m` | hra: nesedící otisk → voda z exportu; brod mimo odchylku = varování | opraveno v kódu (hra), otisk zapíše příští export |
| 2b | Příkop málo vody (−30,27) | profil příkopu beze změny (dno −3,6, hladina −2,75 → voda ~5 m z 11 m šířky, bahnité svahy) | potřebuje rozhodnutí: hladina příkopu výš? | | ptám se Míši |
| 3 | Potůčky k mlýnu, odtok a nový rybník bez koryta a břehů, „voda v trávě“ | terén okolí má síť po 5 m (ves 2 m) – koryto 1–1,5 m v ní neexistuje, hladina zahrabaná; břehový povrch (hlína, štěrk) měla jen Bystřice | `toky_tvar.pas_jemny_m` (jemný terén 1 m u všech toků a rybníků, `kraj._teren_u_vody`), `toky_tvar.breh_hlina_m` (holá hlína a štěrk u vody) | (doplnit) test smyslu: dno toku pod hladinou ve výsledné síti | opraveno v generátoru, čeká export |
| 4 | Tráva a strom v hostinci (−63,930) | | vnitřek budov = zákaz rostlin (obrys z dat) | zasazení: rostlina uvnitř obrysu stavby | |
| 5 | Tráva a strom ve vratech a vstupech ve vsi (391,758; 422,792), tráva v záhonech (403,753), strom uprostřed cesty (440,804) | | průchod vrat a záhon = užívání (sešlap / obdělávání) v `druhy.json` | zasazení: rostlina v průchodu / záhonu / na ose cesty | |
| 6 | Hnědá kláda přes cestu a plot (454,842) | | | předmět přes cestu / plot | |
| 7 | Hřiby létají (504,901; 346,909) | | | předmět nad zemí | |
| 8 | Hranice dřeva s černými plochami (331,902) | | | | |
| 9 | Z kopce dohled „až do nevidim“ (−137,576) – mělo být plné, krátký dohled | mapa výhledu / hustota lesa (úkol noc 21:15 nedotažen) | hustota a podrost podle stanoviště, dohled z vyhlídek | test dohledu z míst | |
| 10 | Do mlýna se nedá dostat, dveře nefungují | systém dveří (pohyb.gd) hledá křídla jen pod uzlem Tvrz, mlýn je samostatný díl | dveře mlýna jako dveře domů (záznam pohybu), `voda.json mlyn.dil.dvere_otevrene` | | opraveno v kódu |
| 11 | Venku u mlýna dřevo, špalek, pytle z modelu – pryč, dáme svoje | | `mlyn.dil.vynechat_uzly` = Mlyn_Doplnky | | opraveno v kódu |
| 12 | Spustit kolo a mletí | kolo se točí pořád | stavidlo (páka) pouští vodu na kolo → kolo, čeřník a kámen; mletí obilí na mouku | | další |
