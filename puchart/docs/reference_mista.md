# Skutečná podoba místa → rok 1393 (postup KCD)

Míša 29. 10.: „Máš výhodu reálného světa a mapy – ber fotky dnešní podoby, skutečné rostliny a zalesnění s ohledem na
historii… Ber historii a podobu místa jako KCD… Když si vytáhneš všechny fotky okolí, uvidíš potoky, koryto, kameny,
skály, rostliny, hustotu – a jen je upravíš podle historie.“

## Zdroje (stažené daty, `nastroje/stahni_realne.sh`, `pravidla/svet/zdroje_dat.json`)
| zdroj | co dává | jak se použije |
|---|---|---|
| ČÚZK ortofoto 0,5 m | dnešní podoba: les, louky, pole, Boňkov, cesta údolím | reference, srovnání `docs/screens/02_*` |
| ČÚZK DMP 1G − DMR 5G | výška porostu po 1 m | **polohy a výšky stromů** = dnešní koruny (lokální maxima), doplněno do hustoty |
| AOPK mapování biotopů (2021) | 295 ploch ve výseku, typ biotopu, **poznámky mapovatelů** | stanoviště 1393 přes `historie_vegetace.json` |
| AOPK potenciální přirozená vegetace | kostřavová a biková bučina, lipová a karpatská dubohabřina | les tam, kde jsou dnes smrkové kultury a průseky |
| iNaturalist (research grade) | 150 druhů rostlin z okolí | druhy podrostu, břehů, skal; neofyty vyřazené |
| Wikimedia Commons | fotky Puchartu, Kyžlířova, Veličky, Boňkova (stahuje `fotky_commons.py`, v gitu jen seznam) | vzhled koryt, kamenů, skal, zdiva – rozbor doplním |

## Co říkají poznámky mapovatelů AOPK (přímo z dat, doslova)
- Velička: „**Kamenité koryto Veličky**“ (víckrát), „Luh u Veličky, na vyšších terasách přechází do bučiny“, „70letý porost podél **zahloubené Veličky**“, „Porost s dom. JS, KL, LP v nivě zahloubeného potoka“.
- Svahy: „Zachovalý 150letý porost na prudkém svahu, místy i **mohutnější skalní výchozy**“, „80letý porost s dom. KL na **balvanitém prudkém svahu**“, „80letá klenina na kamenitém svahu, expanduje Rubus“.
- Skály: „**Drobné kamenné moře**, málo nálet dřevin, hodně mechů“, „Kamenné moře, prakticky bez vegetace“, „mohutnější skály“ (štěrbinová vegetace silikátových skal – droba).
- Louky: „Sečená, celkem fádní louka, mladé ovocné stromy podél cesty“, „část sečená, část extenzivní pastva“.
- Dnešní nepůvodní: „Tyčkovina SM“ (smrkové kultury), průsek pod elektrickým vedením, chatky v lese.

## Převod na rok 1393 (`pravidla/svet/historie_vegetace.json`, `nastroje/stanoviste_realne.py`)
- Zůstává: suťové lesy s javorem klenem, lípou, jasanem a jilmem na balvanitých svazích (L4, 11 % výseku), luhy s olší a jasanem, kamenitá koryta, skalní výchozy a kamenná moře, louky v nivě.
- Mění se: smrkové kultury, průseky a chatky → bučina s jedlí podle PPV (BK 65 %, JD 20 %, KL, LP, SM jen vtroušený).
- Zásahy 1393 (NAVRH/REKONSTRUKCE): vykácené předpolí hradů (r ≈ 90 m, pastvina se solitéry), Boňkov s poli do sklonu 0,15 a loukami, pole na plošině SV.
- Výsledek: les 90 % (bučina 67 %, suťový les 11 %, dubohabřina 8 %), louky a pastviny 5,5 %, pole 2,5 %, koryta 1,7 %.
  Stromů 60 362 (BK 36 159, JD 11 125, KL 4 833, LP 3 606, SM 1 631, HB 994, DB 836…), z toho 11 522 přímo z dnešních korun.
  Mapa: `docs/screens/02_stanoviste_1393.png`, stromy: `02_stromy_1393.png`.

## Co z toho plyne pro modely a materiály (dluh)
- Kameny a balvany: droba/břidlice, tmavě šedé, hranaté, s mechem (kamenná moře, sutě) – ne pískovec Havrana.
- Koryto Veličky: zahloubené, kamenité dno s oblázky a balvany, břehy s olší a jasanem, devětsil (*Petasites hybridus*), blatouch, řeřišnice hořká.
- Chybí modely: **javor klen, jasan, habr, jilm** (dnes zastoupeny lípou, olší, bukem – `stromy_modely.json`).
- Podrost bučiny: kyčelnice žláznatá (*Cardamine glanduligera* – karpatský druh!), bika bělavá, svízel vonný, pitulník, sasanka hajní, ječmenka evropská; na skalách sleziník severní a červený.

## Rostliny z iNaturalistu (okolí výseku), historická kontrola
Neofyty (zavlečené po roce 1500) se nesází. Kontrola podle běžné literatury, **ověřit v Pladias** před zapojením do `druhy.json`.

| druh | latinsky | záznamů | 1393 |
|---|---|---|---|
| orsej jarní | *Ficaria verna* | 11 | ano |
| pryšec chvojka | *Euphorbia cyparissias* | 5 | ano |
| dymnivka plná | *Corydalis solida* | 5 | ano |
| drchnička rolní | *Lysimachia arvensis* | 5 | ano |
| rozrazil perský | *Veronica persica* | 4 | NE (neofyt, po 1500) |
| křivatec žlutý | *Gagea lutea* | 4 | ano |
| rozchodník bledý | *Sedum pallidum* | 4 | ano |
| violka rolní | *Viola arvensis* | 3 | ano |
| pomněnka lesní | *Myosotis sylvatica* | 3 | ano |
| kakost smrdutý | *Geranium robertianum* | 3 | ano |
| hadinec obecný | *Echium vulgare* | 3 | ano |
| šrucha zelná | *Portulaca oleracea* | 3 | ano |
| sleziník routička | *Asplenium ruta-muraria* | 3 | ano |
| zvonek rozkladitý | *Campanula patula* | 3 | ano |
| rozrazil laločnatý | *Veronica sublobata* | 3 | ano |
| chlupáček oranžový | *Pilosella aurantiaca* | 3 | ano |
| sasanka hajní | *Anemonoides nemorosa* | 3 | ano |
| lnice květel | *Linaria vulgaris* | 2 | ano |
| čekanka obecná | *Cichorium intybus* | 2 | ano |
| heřmánek terčovitý | *Matricaria discoidea* | 2 | NE (neofyt, po 1500) |
| jitrocel kopinatý | *Plantago lanceolata* | 2 | ano |
| kostival lékařský | *Symphytum officinale* | 2 | ano |
| kuřinka červená | *Spergularia rubra* | 2 | ano |
| vlaštovičník větší | *Chelidonium majus* | 2 | ano |
| hluchavka skvrnitá | *Lamium maculatum* | 2 | ano |
| hluchavka bílá | *Lamium album* | 2 | ano |
| vratič obecný | *Tanacetum vulgare* | 2 | ano |
| česnáček lékařský | *Alliaria petiolata* | 2 | ano |
| podběl lékařský | *Tussilago farfara* | 2 | ano |
| jmelí bílé | *Viscum album* | 2 | ano |
| pryšec skvrnitý | *Euphorbia maculata* | 2 | NE (neofyt, po 1500) |
| sleziník severní | *Asplenium septentrionale* | 2 | ano |
| sleziník červený | *Asplenium trichomanes* | 2 | ano |
| hvozdík kropenatý | *Dianthus deltoides* | 2 | ano |
| milička menší | *Eragrostis minor* | 2 | NE (neofyt, po 1500) |
| heřmánkovec nevonný | *Tripleurospermum inodorum* | 2 | ano |
| křivatec rolní | *Gagea villosa* | 2 | ano |
| čistec lesní | *Stachys sylvatica* | 2 | ano |
| violka lesní | *Viola reichenbachiana* | 2 | ano |
| pitulník žlutý | *Lamium galeobdolon* | 2 | ano |
| chlupáček zední | *Pilosella officinarum* | 2 | ano |
| kohoutek luční | *Silene flos-cuculi* | 2 | ano |
| smolnička obecná | *Viscaria vulgaris* | 2 | ano |
| štírovník růžkatý | *Lotus corniculatus* | 1 | ano |
| netýkavka žláznatá | *Impatiens glandulifera* | 1 | NE (neofyt, po 1500) |
| pěťour malokvětý | *Galinsoga parviflora* | 1 | NE (neofyt, po 1500) |
| zvonek kopřivolistý | *Campanula trachelium* | 1 | ano |
| bér sivý | *Setaria pumila* | 1 | ano |
| rožec rolní | *Cerastium arvense* | 1 | ano |
| rozrazil rezekvítek | *Veronica chamaedrys* | 1 | ano |
| dvouzubec černoplodý | *Bidens frondosa* | 1 | NE (neofyt, po 1500) |
| pomněnka rolní | *Myosotis arvensis* | 1 | ano |
| netýkavka malokvětá | *Impatiens parviflora* | 1 | NE (neofyt, po 1500) |
| vrbina tečkovaná | *Lysimachia punctata* | 1 | NE (neofyt, po 1500) |
| jetel luční | *Trifolium pratense* | 1 | ano |
| kopřiva dvoudomá | *Urtica dioica* | 1 | ano |
| papratka samičí | *Athyrium filix-femina* | 1 | ano |
| sveřep měkký | *Bromus hordeaceus* | 1 | ano |
| lipnice roční | *Poa annua* | 1 | ano |
| pelyněk černobýl | *Artemisia vulgaris* | 1 | ano |
| svízel přítula | *Galium aparine* | 1 | ano |
| locika kompasová | *Lactuca serriola* | 1 | ano |
| šťavel evropský | *Oxalis stricta* | 1 | NE (neofyt, po 1500) |
| šťovík menší | *Rumex acetosella* | 1 | ano |
| jetel pochybný | *Trifolium dubium* | 1 | ano |
| chmel otáčivý | *Humulus lupulus* | 1 | ano |
| zemědým lékařský | *Fumaria officinalis* | 1 | ano |
| náprstník červený | *Digitalis purpurea* | 1 | ano |
| rozrazil potoční | *Veronica beccabunga* | 1 | ano |
| mák vlčí | *Papaver rhoeas* | 1 | ano |
| líska obecná | *Corylus avellana* | 1 | ano |
| huseníček rolní | *Arabidopsis thaliana* | 1 | ano |
| sedmikráska obecná | *Bellis perennis* | 1 | ano |
| chrpa luční | *Centaurea jacea* | 1 | ano |
| zvěšinec zední | *Cymbalaria muralis* | 1 | NE (neofyt, po 1500) |
| jetel plazivý | *Trifolium repens* | 1 | ano |
| rozrazil rolní | *Veronica arvensis* | 1 | ano |
| bika ladní | *Luzula campestris* | 1 | ano |
| violka vonná | *Viola odorata* | 1 | ano |
| vrba jíva | *Salix caprea* | 1 | ano |
| devětsil lékařský | *Petasites hybridus* | 1 | ano |
| hluchavka nachová | *Lamium purpureum* | 1 | ano |
| břečťan popínavý | *Hedera helix* | 1 | ano |
| měsíčnice roční | *Lunaria annua* | 1 | NE (neofyt, po 1500) |
| kalina obecná | *Viburnum opulus* | 1 | ano |
| sléz pižmový | *Malva moschata* | 1 | ano |
| štětka planá | *Dipsacus fullonum* | 1 | ano |
| kopretina bílá | *Leucanthemum vulgare* | 1 | ano |
| svízel vonný | *Galium odoratum* | 1 | ano |
| zběhovec plazivý | *Ajuga reptans* | 1 | ano |
| rozrazil břečťanolistý | *Veronica hederifolia* | 1 | ano |
| blatouch bahenní | *Caltha palustris* | 1 | ano |
| pryšec kolovratec | *Euphorbia helioscopia* | 1 | ano |
| vikev čtyřsemenná | *Vicia tetrasperma* | 1 | ano |
| černýš hajní | *Melampyrum nemorosum* | 1 | ano |
| jitrocel vraní nožka | *Plantago coronopus* | 1 | NE (neofyt, po 1500) |
| jitrocel větší | *Plantago major* | 1 | ano |
| pastinák setý | *Pastinaca sativa* | 1 | ano |
| pcháč oset | *Cirsium arvense* | 1 | ano |
| kyprej vrbice | *Lythrum salicaria* | 1 | ano |
| jetel zvrhlý | *Trifolium hybridum* | 1 | ano |
| ořešák královský | *Juglans regia* | 1 | ano |
| krvavec toten | *Sanguisorba officinalis* | 1 | ano |
| rozrazil lesklý | *Veronica polita* | 1 | ano |
| křen selský | *Armoracia rusticana* | 1 | ano |
| lebeda různosemenná | *Atriplex micrantha* | 1 | NE (neofyt, po 1500) |
| ostřice zaječí | *Carex leporina* | 1 | ano |
| mrkev obecná | *Daucus carota* | 1 | ano |
| bělotrn kulatohlavý | *Echinops sphaerocephalus* | 1 | NE (neofyt, po 1500) |
| turan roční | *Erigeron annuus* | 1 | NE (neofyt, po 1500) |
| kakost holubičí | *Geranium columbinum* | 1 | ano |
| kakost pyrenejský | *Geranium pyrenaicum* | 1 | ano |
| máta dlouholistá | *Mentha longifolia* | 1 | ano |
| zblochanec oddálený | *Puccinellia distans* | 1 | NE (neofyt, po 1500) |
| rozchodník bílý | *Sedum album* | 1 | ano |
| bér zelený | *Setaria viridis* | 1 | ano |
| jetel rolní | *Trifolium arvense* | 1 | ano |
| jehlice trnitá | *Ononis spinosa* | 1 | ano |
| zlatobýl obrovský | *Solidago gigantea* | 1 | NE (neofyt, po 1500) |
| pupava obecná | *Carlina vulgaris* | 1 | ano |
| slunečnice topinambur | *Helianthus tuberosus* | 1 | NE (neofyt, po 1500) |
| kroucenec zední | *Tortula muralis* | 1 | ano |
| baňatka bělavá | *Brachythecium albicans* | 1 | ano |
| krtičník hlíznatý | *Scrophularia nodosa* | 1 | ano |
| rozrazil lékařský | *Veronica officinalis* | 1 | ano |
| křivonožka vehnutá | *Campylopus introflexus* | 1 | NE (neofyt, po 1500) |
| starčkovec jestřábníkolistý | *Erechtites hieraciifolius* | 1 | NE (neofyt, po 1500) |
| řeřišnice hořká | *Cardamine amara* | 1 | ano |
| jedle bělokorá | *Abies alba* | 1 | ano |
| mochna husí | *Argentina anserina* | 1 | ano |
| zvonek broskvolistý | *Campanula persicifolia* | 1 | ano |
| útlovláska bledá | *Ditrichum pallidum* | 1 | ano |
| kručinka barvířská | *Genista tinctoria* | 1 | ano |
| třezalka rozprostřená | *Hypericum humifusum* | 1 | ano |
| bika bělavá | *Luzula luzuloides* | 1 | ano |
| mochna plazivá | *Potentilla reptans* | 1 | ano |
| škumpa orobincová | *Rhus typhina* | 1 | NE (neofyt, po 1500) |
| dub zimní | *Quercus petraea* | 1 | ano |
| pryšec sladký | *Euphorbia dulcis* | 1 | ano |
| kopretina irkutská | *Leucanthemum ircutianum* | 1 | NE (neofyt, po 1500) |
| ostřice kulkonosná | *Carex pilulifera* | 1 | ano |
| lebeda lesklá | *Atriplex sagittata* | 1 | NE (neofyt, po 1500) |
| ječmenka evropská | *Hordelymus europaeus* | 1 | ano |
| kyčelnice žláznatá | *Cardamine glanduligera* | 1 | ano |
| pastarček potoční | *Tephroseris crispa* | 1 | ano |
| křídlatka japonská | *Reynoutria japonica* | 1 | NE (neofyt, po 1500) |
| chrpa modrá | *Centaurea cyanus* | 1 | ano |
| olše lepkavá | *Alnus glutinosa* | 1 | ano |
| ptačinec velkokvětý | *Rabelera holostea* | 1 | ano |
| kostrbatec tříkoutý | *Hylocomiadelphus triquetrus* | 1 | ano |