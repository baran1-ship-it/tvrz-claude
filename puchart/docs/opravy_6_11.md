# Seznam oprav z tabletu 6. 11. (Míša, 40 fotek) – pořadí práce

Stav: APK 1602529 vydána 6. 11.; chyby 108–123 v docs/chyby.md. Nic z toho zatím neopraveno (limit).
Pravidlo: každý bod podle reference (Havran větev claude/new-session-0dtk58, KCD fotky docs/reference/kcd_vzhled, GC80T08),
po opravě snímek ze stejného místa jako Míšina fotka.

## 1. Cesty a mosty (největší dojem, Havran má hotové)
- **119/123 Kamenitá cesta podle Havrana** – vozová cesta údolím i hřebenem: kameny, štěrk, bláto jen místy, ne souvislé koleje.
  Zdroj: Havran pravidla/svet/cesty.json + blender (najít `cesta`/`kameny` na větvi), textura `stony_dirt_path` (Havran textures.py „hlina“).
  Kód: nastroje/cesty.py (maska_koleje → slabší, kamenitý povrch), hra/shaders/zem.gdshader.
- **123 Boční hrb hřebenové cesty** – srovnat příčný sklon (zářez do svahu, násyp na straně rokle), test smyslu na příčný sklon.
- **122 Cesta nad terénem u potoka** – koryto pod cestou / cesta ve stejném terénu (cesty.py vs koryta.py pořadí).
- **120 Mosty přes Veličku jen dřevěné** (Havran Most_potok): bez kamenných opěr a schodů, dřevěné prahy na břehu, nájezd hlinou.
  Osa mostu v ose cesty: cestu vést kolmo k toku v místě mostu (raději upravit cestu než šikmý most). Kód blender/voda.py VH mosty.
- **121 Brody podle Havrana**: bez křoví (stavby_vegetace: pás bez porostu), oblázky, mělká voda, vyjeté nájezdy.
- **108 Cesta k vnější brance A rovně v ose mostu** (cesty_puchart.json konec cesty = začátek most_vnejsi).
- **113 Cesta po hřebeni k dolnímu hradu** až k mostu přes průrvu.
- **114 Nájezd mostu B**: zásyp hlínou + dřevěná nástupní plošina, ne kamenné stupně na svahu.

## 2. Hrad A
- **109 Vnější hradba vlevo od vstupu nízká** – výška po valu (hradba_val vyska).
- **110 Vrata branky zespodu v hlíně** – práh vs terén (teren_upravy u branky).
- **112 Střechy přes hradbu** – na straně v hradbě přesah jen ke koruně (strecha_sedlova: okap na straně hradby 0), pultová stříška přes korunu.
- **111 Zábradlí a ochozy** – rohy ochoz2 (prkna přes sebe, křížení madel), doplňovač zábradlí; odstraní výjimku spojů (strop 32, výjimka do 20. 11.).
- Světlo v interiérech: síň/sál tmavé – víc světel, okna.

## 3. Hrad B
- **116 Přední nádvoří plné schodů** – schody štítu a ochozu přesunout podél zdí, jedno schodiště na ochoz.
- **117 Levá budova (štít) širší až k příčné zdi s branou** – bez díry mezi nimi.
- **115 Skála u brány a nároží** – hranatá skála (skaly.py stena jemněji), omítka B po čtvercích (zdivo kryti B, šum větší), okno ve skále.
- **118 Dveře a okna všude, světla** (štít, palác B, věžička A).
- Palác B obytný jako palác A (dispozice, pavlač) – z původního plánu.

## 4. Výkon (měření z tabletu 6. 11.)
- Les p95 64,6 ms, voda 54,3 ms (cíl 40) – optimalizace lesu (úkol 11), voda jemný pás kratší dosah.
