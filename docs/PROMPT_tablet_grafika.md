# Univerzální prompt: hra na tablet – světlo, modely, zobrazení (z Havrana, 27. 11. 2026)

Vložit na začátek nové hry (CLAUDE.md nebo první zpráva). Platí pro Godot 4.x Compatibility (GL ES 3) na Android tabletu;
pro jiný engine stejné zásady, jiné názvy.

```
Stavíš 3D hru pro Android tablet. Cíl: hezká a plynulá zároveň. Pracuj podle těchto pravidel a drž se jich i bez připomínání.

## 0. Cíl a rozpočty (měř, neodhaduj)
- 30 FPS = 33,3 ms na snímek. Snímek nad 40 ms je zásek = chyba, ne šum. Měř p95/p99 a % snímků nad 33,4 ms, ne průměr.
- Rozpočet na snímek: do ~1,2 M trojúhelníků, do ~400–600 kreslení (draw calls), textury ve VRAM do ~300–700 MB,
  RAM procesu do ~1,2 GB (tablet má reálně ~2 GB volné; pád bývá nedostatek paměti, ne GPU).
- Každá nová vrstva světa (import modelu, vegetace, voda, světla) má rozpočet a měření DŘÍV, než jde do vydání.
- Nezměřené číslo piš jako NEOVĚŘENO. Hypotézu nikdy nevydávej za opravu.
- Od začátku udělej ve hře panel měření (FPS, nejdelší snímek, záseky > 40 ms s rozpadem: skripty/fyzika/kreslení/GPU,
  počet kreslení, trojúhelníky, VRAM, RAM) a „měřicí trasu“ (stejná cesta světem, varianty s vypnutou jednou vrstvou),
  výsledek zapisuj k verzi. Při zhoršení porovnej poslední dobrou a první špatnou verzi.

## 1. Zobrazení a nastavení
- Renderer Compatibility (GL ES 3). Žádné MSAA, žádné shadery čtoucí screen texture (refrakce, SSR, blur pozadí).
- 3D rozlišení pevně (např. 75–100 %, rozhodnout měřením), za běhu ho NEMĚNIT (přepnutí = zásek). Výkon hledej u příčiny.
- Automatické snížení kvality jen v extrému (přehřátí, dlouhý pokles FPS): ubírá detail (dohled trávy, stíny, LOD),
  ne rozlišení; po zchladnutí vrací.
- Pořadí kreslení: neprůhledné zepředu dozadu → obloha → průhledné. Průhlednosti (BLEND) co nejméně.

## 2. Světlo
- Jedno směrové slunce se stíny: 1 kaskáda, dosah ~40 m, rozumné rozlišení mapy. Žádné další stínící světla.
- Bodová světla (krby, louče) bez stínů, malý dosah, málo najednou – v Compatibility každé světlo = další průchod objektů.
  Vzdálená světla vypínat podle vzdálenosti.
- Nepřímé světlo a měkké stíny předpočítat: lightmapy z Blenderu (Cycles → UV2), barvy vrcholů, nebo okolní světlo
  z oblohy. Interiéry nesmí být černé: vlastní ambient/okolní světlo pro vnitřek.
- Mlha a barva oblohy spojují dálku s blízkem (levná krása); denní doba = změna barvy slunce, oblohy, mlhy.
- Po každé změně materiálu nebo světla snímek ráno/poledne/večer a interiér v noci.

## 3. Modely
- Než něco vymodeluješ, hledej hotové (CC0/CC-BY: Poly Haven, ambientCG, Quaternius, Kenney, Sketchfab; autora do titulků).
  Vždy modely, ne primitiva (krabice, válce).
- Každý import projde tabulkou: počet trojúhelníků, LOD (2–3 úrovně, poslední úroveň pro dálku), hrubá kolize
  (jednoduché tvary, nikdy trimesh celého modelu), materiály sloučené (atlas), textury ≤ 1–2 K.
- Postava s kostrou: ~8–12 tis. trojúhelníků. Při zjednodušování (decimate) nezmenšuj oči, obličej a ruce stejně jako
  oblečení – oči pak zmizí. Oči, vlasy (alfa MASK/scissor, ne BLEND) zkontroluj snímkem zblízka.
- Alfa: MASK (ořez) místo BLEND všude, kde to jde (vlasy, listí, plot, postroj). Exportér glTF z Blenderu často dá BLEND –
  ověř alphaMode v souboru.
- Kostry z různých programů mají jiné osy (3ds Max / UE = Z nahoru, cm). Svislici a směr vpřed počítej z transformací
  rodičů, ne „Y = nahoru“ natvrdo. Animace z jiné kostry: stejné jméno kostí, stejná klidová póza a osy, jinak postava
  leží nebo má ruce jinde.
- Jedna dlouhá animační stopa rozdělená na klipy: čas = snímek / fps (ověř, jestli stopa začíná snímkem 0 nebo 1), konec
  smyčky vyber podle nejmenšího rozdílu póz první × poslední snímek – jinak postava v každé smyčce „blikne“.
- Kořenová kost s posunem v klidové póze (snímek 0) posune vše, co se měří z klidu (sedlo, ruce) – srovnej s 1. snímkem klipu.

## 4. Vegetace a terén
- Tráva a listí: ne „discard“ na celé obrazovce. Geometrická stébla bez alfy, nebo karty s ořezem a malým překryvem;
  hustota a dosah podle rozpočtu, MultiMesh po buňkách, stavba buněk mimo hlavní vlákno.
- Stromy: LOD + impostor (plochý obraz) na dálku. Les z dálky = hmota, ne tisíce stromů.
- Terén po dlaždicích s LOD; švy mezi dlaždicemi/sítěmi různé hustoty musí mít stejnou výšku (jinak čáry a díry).
- Povrch (hlína/tráva/cesta) z jednoho systému dat (barva vrcholů nebo maska) – dva systémy vedle sebe dělají na hranici pruhy.
- Nic živého ve vodě, stavby ne na cestě/svahu/ve vodě, rostliny ne ve vzduchu ani v budovách – na to automatické testy.

## 5. Záseky (nejvíc vidět na tabletu)
- Shadery předehrát při načítání (první zobrazení materiálu = zásek). Částice taky.
- Nic velkého nevytvářet v hlavním vlákně za hry: buffery, MultiMeshe, kolize, načítání modelů – po dávkách nebo ve vlákně.
- Vlákna nesdílí měnitelný stav (pády). Načítání scén na pozadí (ResourceLoader threaded).
- Každý zásek > 40 ms zapsat s rozpadem (co ho způsobilo) a opravit příčinu.

## 6. Data a balíky (aby tablet dostal, co vidíš na PC)
- Po změně modelu ověř, že engine opravdu přeimportoval (Godot u .gltf hlídá jen text .gltf, ne .bin a textury –
  smazat cache importu a importovat znovu). Jinak testuješ stará data.
- Balík pro tablet ověř podle obsahu (jsou v něm animace, textury, všechny modely?), ne podle toho, že se sestavil.
  Testy na PC běží z cache importů a chybějící soubor v balíku nepoznají.
- Podpisový klíč nikdy do repozitáře.

## 7. Postup práce
- Nejdřív se podívej, jak to dělají hotové hry (KCD, Genshin na mobilu, …) a hotové postupy; ne z hlavy.
- Po každé změně scény udělej snímek a sám se na něj podívej, než ho pošleš nebo vydáš.
- Po změně: rychlé testy + testy dotčené části; celá sada před větším vydáním. Dlouhé běhy na pozadí, mezitím jiná práce.
- Chyba od člověka = oprava příčiny + nová automatická kontrola, ať se nevrátí. Po dvou neúspěšných opravách stejné chyby
  žádný třetí pokus naslepo: nový rozbor příčiny a izolovaný test.
- Žádné záplaty: každý díl světa je záznam v datech, čísla v pravidlech (JSON), ne roztroušená v kódu.
- Před vydáním nezávislá kontrola změn a snímků. Každé vydání: verze, čas, co se změnilo, co je NEOVĚŘENO na zařízení.
```
