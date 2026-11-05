# Hrady podle kreseb GC80T08 a skutečného místa (plán 5. 11.)

Míša 5. 11.: „proč není náš hrad ani jeden podobný těmto obrázkům?“, „příkop před dolním hradem hlubší, vytesaný do skály“,
„kopec a hřeben podle nákresu a dnešního stavu, vyhodnoť těch 600 let“, „nedostavěný příkop dostavěj“, „omítka a hrázděná
patra tam být můžou, ale dle obrázku“, „maximálně čerpej ze zdrojů a skutečného místa, kde je slepé místo, podle svého“.

Podklady: `docs/reference/gc80t08/` (popis_GC80T08.txt, kresby misa_01 = B se štítovou zdí, misa_04 = A, gc_01 = celek
z údolí Kouteckého potoka, gc_03 = B, gc_10 = A, gc_00 = půdorys + řez A–A′ převýšený 2×), fotky zdiva, příkopů a hrázek.
Srovnání před přestavbou: `build/foto/kresby_vs_hra_pred.jpg`.

## Proč se hra od kreseb vzdálila (rozbor)
1. Kresby byly zdroj „KRESBA vzhled“, ale z kresby se braly jen prvky (věžička, branka, most); hmota a proporce se
   skládaly ze stavebnice a pozdější požadavky (věž s okny, patra, schody, terasy) hrad dál vzdalovaly. Nikdy se
   neudělal snímek ze stejného pohledu vedle kresby. → **Nově: každý krok = snímek ve stejném pohledu vedle kresby.**
2. Terén zůstal v dnešním stavu (DMR): zasutěné svahy, zanesené příkopy, les až ke zdem. Kresby ukazují hrady na
   holých skalních hřbetech s kolmými stěnami.

## Co změnilo 600 let (1393 → dnes) a jak to vrátit
| jev | dnes (DMR, fotky) | 1393 (kresby, text, logika) | úprava |
|---|---|---|---|
| les | vzrostlý buk/smrk až ke zdem | okolí hradu vykácené (obrana, palivo, stavební dříví) – kresby holé skály | pásmo bez lesa kolem hradů a hřebene (pastvina, nízké křoví, skály), les až dál ve svazích |
| skalní stěny | zvětralé, pod nimi suťové kužely, zarostlé | čerstvější stěny, kolmé pod hradbami (kresby) | kde DMR sklon > ~45° na hraně hřbetu: stěna zostřit, suť pod ní ubrat (objem zachovat → v suti) |
| průrva před B | zasypaná sutí a listím, mírné svahy | „hluboký do skály vylámaný příkop“ (text), kresba: kolmé stěny, skalní jehla | prohloubit o odhad zásypu, stěny kolmo do skály, dno ploché, skalní jehla stojí (kresba misa_01) |
| šíjový příkop A | „mohutný“, val zdvojený na V | hlubší, strmější, val vyšší | prohloubit + zostřit, val dosypat o zásyp |
| palác B | boční stěna sjela vcelku po V svahu, ostroh se odlamuje | ostroh širší, palác na hraně | hranu ostrohu na V obnovit podle sjeté stěny (utržený kus na půdorysu gc_00) |
| předpolí (~250 m SZ) | relikty nedostavěného příkopu s valem | rozestavěné / dostavěné opevnění předpolí | **dostavět** (Míša): příkop + val napříč hřbetem podle reliktu v DMR |
| ves Předhradí | kamenné hrázky políček v lese (~500 m) | ves „Předhradsko“ (1547 pustá) s políčky | usedlosti 14. st. (trojdílné domy) + políčka s hrázkami podle čar v DMR |

## Hrad B (zadní, dolní) podle misa_01 / gc_03
- Plášť nízký, nepravidelný mnohoúhelník **po hraně skály** (lomené úseky, mírně oblé), bez cimbuří na kresbě → koruna
  s poprsní zídkou.
- Čelo nad průrvou: **vysoký štít / donjon** (úzký vysoký hranol s pultovou střechou k nádvoří, text: donjon 8×8 nebo
  štítová zeď). Ne samostatná věž s okny po celé výšce.
- **Palác** na JV konci ostrohu (10×12 m, text), kamenný, **strmá sedlová střecha** se štítem k údolí, menší okna.
- Mezi štítem a palácem malé nádvoří s nízkou budovou (pultová střecha), brána přistavěná u štítu vlevo (text: „zbytek
  přistavěné vstupní brány“).
- **Most**: vodorovný, dlouhý, na vysokých kozách přes průrvu; nástup na zarovnané plošině hřebene ve výšce brány
  (text: kresby zde realitu zkreslují – most začíná na plošině, ne níž) → poloha podle textu, vzhled podle kresby.
- Omítka/hrázděné patro jen, je-li na kresbě (misa_01: kamenné hmoty, světlejší horní část paláce může být omítka).

## Hrad A (přední, horní) podle misa_04 / gc_10
- Jádro: **vysoké hladké zdi** lichoběžníku 35×25 m, bez cimbuří na kresbě (rovná koruna se stříškou/ochozem).
- **Palác** podél jedné strany: dlouhá budova se sedlovou střechou, vyšší než plášť; u ní nižší přístavek.
- **Jedna nárožní věžička** se stanovou střechou (vpravo na kresbě).
- **Vnější hradba** po hřebeni valu dlouhým obloukem kolem nádvoří, na konci **branka se stanovou střechou** a most.
- Text: bezvěžová brána v SV rohu, tři budovy (S čelní zeď, SZ nároží, J), suterén SZ budovy (sklep – zachovat).

## Pořadí prací
1. Terén 1393 (`pravidla/svet/teren_1393.json`): průrva B, příkop A, skalní stěny, odlesnění, sesuv B, předpolí.
2. Hrad B podle kresby → snímek vedle misa_01 → Míša.
3. Hrad A podle kresby → snímek vedle misa_04 → Míša.
4. Celek z údolí vedle gc_01.
5. Ves Předhradí, pak cesty (hlavní cesta 1393 po hřebeni přes Boňkov podle textu GC80T08, údolím stezky a brody).

Kontroly z dřívějška: švy (zdi jako jedna síť), díry u schodů a zdí, zábradlí, schody u stěn, kolize (povrch_kolize),
nic nevisí, portály.
