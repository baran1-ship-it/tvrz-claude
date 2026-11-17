# Rešerše dvou PDF od Míši (17. 11.)

Míša 17. 11.: „mrkni zase, malá rešerše, nastuduj, případně se podívej na dané věci na internetu, třeba se bude něco hodit“.

- **PDF A** – „Jaké 3D hry lidé tvoří s AI“ (5 stran, 9 projektů): `7b746af0-3D-hry-s-AI.pdf`
- **PDF B** – „Herní grafika Čína / Japonsko / Indie“ (4 strany, 8 ukázek): `e605a770-Herni-grafika-Cina-Japonsko-Indie.pdf`

Nic se neimplementovalo, Godot se nespouštěl a nic se nestahovalo. Obě PDF jsem přečetl celá, odkazy z nich prošel přes
internet a srovnal je s kódem (`hra/scripts`, `hra/shaders`, `pravidla/svet`, `nastroje`, `docs`). Čísla z cizích projektů
jsou **jejich** měření. Pro tablet je všechno **NEOVERENO**.

**Celkový dojem:** obě PDF jsou spíš přehled projektů a obrázků než technický návod. Většinu technik, které v nich jsou
(impostory, dithered LOD, stínová tělesa, HLOD, předehřátí shaderů, datově řízený svět, procedurální Blender, autotest
tras, tráva u paty zdí, povrch podle mapy vegetace), Puchart už má (tabulka v kap. 3). Nové jsou hlavně **postupy
kontroly a výroby**: regulátor kvality s hysterezí, mřížka dosažitelnosti, kontrola materiálu ve třech světlech,
vrstvení materiálů s maskami a vlastní skeny povrchů.

---

## 0. Shrnutí: nejlepší kandidáti (seřazeno podle poměru přínos / pracnost)

| # | Kandidát | Odkud | Verdikt | Přínos | Pracnost | Kde |
|---|---|---|---|---|---|---|
| 1 | **Regulátor detailu podle p75 snímků s hysterezí** („automatika v extrému“ ze ZÁVĚRU §0, dosud nenapsaná). Halcyon: zasáhne, když p75 přeleze práh; jeden dlouhý snímek ignoruje; zpět jen po klidné době. U nás ubírá **detail**, nikdy rozlišení | A s. 3, Halcyon | **ANO** | vysoký (teplo, dlouhé sezení) | S–M | nový `hra/scripts/regulator.gd`, `rozpocty.json` nový klíč `automatika`, panel v `diag.gd` |
| 2 | **Mřížka dosažitelnosti a uzavření světa** (`--reach`, `--check`): fyzikální průchod mřížkou bodů najde místa, kde hráč uvízne, kam se nedostane a kudy uteče ze světa | A s. 1, Alchemists of Prague | **ANO** | vysoký pro hlídače | M | `hra/scripts/test_pruchod.gd` (nový režim), `nastroje/hlidaci.sh`, `docs/chyby.md` |
| 3 | **Kontrola nového materiálu ve třech světlech** (ráno / poledne / večer, plus interiér s loučí) dřív, než jde do hry | A s. 4, Second Take (devlog) | **ANO** | střední (méně „černých/bílých“ chyb, např. č. 107, 230) | S | `PUCHART_FOTO` + `den.gd`, hlídač scén, krok „test ve stejném světle“ v modelovém filtru |
| 4 | **Stíny mraků po krajině** (sdílený šum oblohy, posun podle větru) | doplněk k B s. 2 (krajina za plného světla) a Genshin/WW praxi | **MOŽNÁ** (nejdřív reference z KCD) | střední (krajina mezi velkými momenty „žije“) | S | `zem.gdshader` (9 → 10 vzorkovačů), `listi.gdshader`, `sky.gdshader` (`cloud_offset`), `den.json` |
| 5 | **Vrstvení materiálů**: sdílené dlaždicové textury + levné masky opotřebení (AO, ohlazené hrany, gradient shora dolů). U nás masky v **barvě vrcholů** (0 vzorkovačů) místo 512px textur | B s. 2, NOSTALGIC TRAIN (CGWORLD) | **MOŽNÁ → ANO** po pokusu na jedné stavbě | střední–vysoký („opotřebení ukazuje používání“) | M | `blender/` (zapečení do COLOR), `zdivo.gdshader`, `textura.gdshader`, `hrad_vzhled.json` |
| 6 | **Vlastní skeny povrchů z Potštátska** (droba, břidlice, zdivo zříceniny Puchartu, ohlazené dřevo) telefonem, RealityScan Mobile zdarma i komerčně | B s. 3, Unleash the Avatar | **MOŽNÁ** (potřebuje Míšu v terénu) | vysoký pro „podle reference“ | M + focení | `nastroje/droba_tex.py`, `blender/skaly_scan/`, `pravidla/svet/skaly.json zdroj` |
| 7 | **Ohýbání trávy kolem hráče a koně** (pozice do uniformu, posun ve vertex shaderu) | doplněk k B s. 4 (pěšina v trávě), běžné v mobilních hrách | **MOŽNÁ** (reference z KCD, cena na Adrenu změřit) | nízký–střední | S | `stebla.gdshader`, `louka.gd`, `byliny.gd` |
| 8 | **AI modely drobných předmětů** (TRELLIS.2 MIT, placené Tripo) jen přes modelový filtr; **Hunyuan3D ne** (licence vylučuje EU) | A s. 4 a B s. 1, 4 (Tripo, Rodin) | **MOŽNÁ**, nízká priorita | nízký–střední | M | `nastroje/` (decimace, LOD), katalog předmětů, `docs/zakazka_modelar.md` |

**Pro náš renderer Compatibility (GLES3) nepoužitelné** (podrobně kap. 4):
- voda, která čte podklad za hladinou (Halcyon: „water pass runs after colour and depth are resolved“) = **kopie obrazovky**,
- automatické snižování rozlišení a doostření (Halcyon governor na render scale, Catmull-Rom + sharpen; v Compatibility je
  jen bilineární škálování a žádné doostření, docs 4.7) – a Míša nechce automatiku přes rozlišení,
- paralaxa (POM) dlažby (Alchemists: i se sníženým počtem kroků 6–10 FPS na Intel UHD 620),
- shader baker a ubershadery z Godotu 4.5+ – **jen Forward+/Mobile**, v Compatibility „nemá žádný účinek“ (docs 4.7),
- UE5 Lumen, Nanite, World Partition, PCG, HLOD builder, DLSS, objemové mraky, FFT oceán – jiný engine / jiná třída GPU,
- Terrain3D (The Last Eagle) – už A/B testováno 29. 10. (`docs/ab_srovnani.md`), zůstáváme u vlastních dlaždic,
- Hunyuan3D (Tencent) – licence výslovně vylučuje území EU.

---

## 1. PDF A – „Jaké 3D hry lidé tvoří s AI“

### A1. Alchemists of Prague (s. 1) – Godot 4.7.2, Compatibility, Android
Zdroje: https://github.com/msveshnikov/alchemists-of-prague , https://github.com/msveshnikov/claude-game-pipeline ,
vydání https://github.com/msveshnikov/alchemists-of-prague/releases/tag/v1.2

Nejbližší projekt k nám: stejná verze Godotu, stejný renderer na Androidu, ETC2 textury, svět z Blenderu přes headless
Python, rozmístění v JSON (`prague_layout.json`, 1 303 instancí), autotest se 70 kontrolami. Výkon: autor uvádí jen
6–10 FPS na Intel UHD 620, **měření na mobilu chybí**.

| Věc | Co to je | Hodí se? | Přínos / pracnost | Kde u nás |
|---|---|---|---|---|
| **`--reach` + `tools/seal_world.py` + `--check`** | Fyzikální mřížka dosažitelnosti: z bodu startu se „rozlévá“ po mřížce kroky postavy (kolize, sklon, schod). Výsledkem je mapa, kam se dá dojít. `seal_world` podle ní postaví hraniční zdi a `--check` potvrdí, že žádná cesta nevede ven ze světa | **ANO.** Náš test průchodu jde jen po zadaných trasách (`pruchody.json`, 1 288 řádků) a najde chybu jen tam, kudy trasa vede. Mřížka najde i to, kudy nikdo trasu nenakreslil: jámy, ze kterých se nedá vylézt, mezery mezi kolizemi staveb, místa na střechách, okraj výseku 2×2 km. Každý nález = trasa v `pruchody.json` (pravidlo „chyba = regresní test“) | vysoký / M (flood fill nad `CharacterBody3D.test_move` v mřížce 1–2 m kolem hradů a vsi, běh mimo APK v hlídačích) | `hra/scripts/test_pruchod.gd` (režim `PUCHART_TEST=dosah`), výstup `user://dosah.json` + obrázek mapy přes `nastroje/mapa.py`, `nastroje/hlidaci.sh` |
| **`--perf` sonda** | samostatný běh měření | NE – máme `mereni.gd`, trasu a varianty v `hra/data/mereni.json` | – | – |
| **`--tour` snímky z pozic** | prohlídka kamerou | NE – máme `PUCHART_FOTO`, hlídač scén, `nastroje/foto_portaly.sh` | – | – |
| **Shader dlažby ve světových souřadnicích s makro mapou** (špína, posun odstínu, louže) | dlaždice na sebe navazují bez švů, makro mapa láme opakování | Částečně máme: `zem.gdshader` (pomalý šum podél cesty), `zdivo.gdshader` hex-tiling. **Paralaxa (POM) NE** – drahá na pixel. Louže jsou v `docs/reference/reserse_dest_kcd.md` (mokrost) | – | – |
| **Mlha podle čtvrti** | každá oblast má jinou hustotu | NE – mlha je v `prostredi.json` / `den.gd`; oblasti u nás nejsou města | – | – |
| **Ptáci jako MultiMesh, animace ve vertex shaderu** | hejno bez kostí | **MOŽNÁ** později (Míša: příběh a život až po krajině). Princip je levný (0 vzorkovačů, 1 kreslení na druh) | nízký / S | `pravidla/svet/zvirata.json`, nový shader |
| **`align_to_layout.py` (OpenCV ECC)** | „nakřiví“ malovanou předlohu na render rozvržení, aby šlo porovnat pixel po pixelu | **MOŽNÁ** jako nástroj pro „rozdíl proti referenci ukázat snímkem“: zarovnat snímek ze hry na fotku KCD/reality ze stejného místa a dát vedle sebe. Jen pomůcka, ne hlídač | nízký / S | `nastroje/` (nový skript), `docs/screens/` |
| **AI předlohy (ChatGPT) se sdíleným „stylovým blokem“ v každém promptu** | jednotný styl návrhů | **NE jako zdroj** (pravidlo „nic z hlavy – vždy podle reference“: AI obrázek není doklad). Nanejvýš ilustrace návrhu hradu ke schválení, označená NAVRH | – | – |

### A2. The Last Eagle (s. 2) – Godot 4 + Terrain3D, karavany na mapě, vstup do sídel pěšky
Zdroje: https://dometgames.itch.io/the-last-eagle , video https://www.youtube.com/watch?v=lnVZ2sRpO6U ,
Reddit https://www.reddit.com/r/aigamedev/comments/1xb2oep/ (Reddit se z tohoto prostředí načíst nedal).

- **Terrain3D: NE.** Testováno 29. 10. (`docs/ab_srovnani.md`, varianta C) a `docs/reserse_github_nastroje.md` uvádí, že
  v Compatibility naráží na Texture2DArray. Vlastní dlaždice s LOD už máme (`svet.gd`, `teren_dlazdice.py`).
- **Postavy a budovy z balíčků, upravené:** platí naše pravidlo „nejdřív hledat hotové“ + modelový filtr. Nic nového.
- Hratelná verze neexistuje, nic se nedá změřit.

### A3. A Game About Capybaras Delivering Food (s. 2) – three.js, web
Zdroje: https://capybara-vibejam26.leocoout.dev/ , https://vibejam.com/
- Poučení autora: když generované rozložení města nefungovalo, terén a stavby rozmístil sám v editoru. **NE** – u nás to
  už platí: stavba z dat + Míšino pískoviště na výbavu (CLAUDE.md „Stavby bez výbavy“).

### A4. Halcyon (s. 3) – three.js / WebGL 2, atol z laseru, 43 000 rostlin
Zdroje: https://halcyon.billpwchan.art/ , https://github.com/billpwchan/halcyon

Nejtechničtější projekt v obou PDF. WebGL 2 je funkčně blízko GLES3, takže principy jsou přenositelné.

| Věc | Co to je | Hodí se? | Přínos / pracnost | Kde u nás |
|---|---|---|---|---|
| **Regulátor podle p75 s hysterezí** | „snižuje, když 75. percentil času snímku přeleze 19,5 ms; jeden dlouhý snímek ignoruje; zpět až po klidné době“. Měření autora (les, Apple, 4K): p50 16,7 ms, p95 17,6 ms, nad 20 ms 1,1 % snímků | **ANO – ale pákou je detail, ne rozlišení** (Míša 6. 11.: automatika jen v extrému, ubírá detail; 3D 75 % pevně). Stupně z dat: 1) dohled podrostu a louky, 2) hustota vzdáleného listí / dosah LOD, 3) stíny (40 → 25 m). Práh např. p75 > 40 ms po 10 s (mezicíl p95 40 ms), návrat po 60 s pod 30 ms. Hráč to vidí v panelu, měření (`mereni.gd`) regulátor vypíná, aby čísla byla poctivá | **vysoký / S–M**. Riziko: změna dosahů = přestavba buněk = zásek → stupně měnit jen přes `visibility_range` a hustotu, ne přestavbou; řádek záseků v měření | nový `hra/scripts/regulator.gd`, `pravidla/svet/rozpocty.json` klíč `automatika` (prahy, stupně, zdroj = ZÁVĚR §0 + Halcyon), `diag.gd` (panel), `mereni.gd` (vypnout při měření). Teplo z Androidu (ADPF) nepovinné – stačí časy snímků |
| **Dithered LOD pásma + hemi-oktaedrické impostory** | plný strom zblízka, dál impostor | NE – máme (`impostor.gdshader` atlas 8×8 hemi-oktaedrický, `les.gd` časované prolnutí) | – | – |
| **Stínová tělesa jen ve stínovém průchodu** | levná síť jen pro stín | NE – máme (`SHADOWS_ONLY` v `ves.gd`, `les.gd`, `predmety.gd`, `hlavni.gd`) | – | – |
| **Povrch podle mapy vegetace, ne podle výšky; útesy triplanárně; opad pod zapojenými korunami** | – | NE – máme (`zem.gdshader` masky stanovišť + zápoj → opad 17. 11., `skala.gdshader` triplanár) | – | – |
| **Všechny shadery přeložené a textury nahrané před setmělou úvodní obrazovkou** | – | NE – máme `predehrati.gd` (Godot docs 4.7 to pro Compatibility doporučují jako jedinou cestu) | – | – |
| **HD textury nahrávané po částech přes několik snímků** | místo jednoho velkého nahrání | **MOŽNÁ** – jen pokud měření ukáže zásek při prvním zobrazení velké textury, který předehřátí nezachytí | nízký / M | `predehrati.gd`, `data.gd` |
| **Lehčí sada podkladů pro telefony** | mobil dostává méně | NE – už stavíme jen pro tablet (Tablet_1K textury, `rozpocty.json textury_px`) | – | – |
| **Voda: FFT, vzdálenostní pole pobřeží (jump flood), lom podle hloubky** | – | Vzdálenostní pole břehu **MOŽNÁ** (zapéct offline do barvy vrcholu koryta → pěna a průzračnost u břehu bez vzorkovače). FFT a čtení podkladu **NE** (kopie obrazovky). Pozn.: `voda.gdshader` už má „u břehu do ztracena (barva vrcholu)“, takže přínos malý | nízký / S | `nastroje/koryta.py`, `voda.gdshader` |
| **Rozmístění podle sítě a 1 m lidaru** | – | NE – máme DMR a vlastní rozmístění | – | – |

Poznámka z PDF A s. 5 („Pro vzdálené lesy v Havranovi: porovnej blízké koruny, vzdálené stromy a hranici přechodu“):
u nás se dá přímo porovnat **hranice přechodu** strom → impostor snímkem z `PUCHART_FOTO` proti galerii Halcyonu.
Je to úkol na snímek, ne na kód.

### A5. San Francisco – The Game (s. 3) – Codex, 3D data Apple Maps
Zdroje: https://sf.thijs.gg/ , https://x.com/cdngdev/status/2091987797376979258
- **NE.** Data Apple Maps se pro nás nedají použít (licence, rok 1393). Reálný podklad už máme (DMR, ČÚZK).

### A6. Wildhearth (s. 4) – Godot, Claude psal skripty pro 3D modely v Blenderu
Zdroje: https://promptgoblin.itch.io/wildhearth , https://www.youtube.com/watch?v=sQUGbjVs-Tg
- **NE** – stejný postup už děláme (`blender/`, `nastroje/`). Nízkopolygonový styl neodpovídá cíli „realisticky jako KCD“.

### A7. Earth Simulator (s. 4) – Steam
Zdroj: https://store.steampowered.com/app/4932460/Earth_Simulator/
- **NE** – AI na mechaniky, modely, textury a zvuky bez uvedení nástroje; jiný žánr. Nic konkrétního k převzetí.

### A8. Second Take (s. 4) – UE5, létající ostrovy z reálného terénu u Koločavy
Zdroje: https://atlas-house.itch.io/second-take ,
https://atlas-house.itch.io/second-take/devlog/1782124/second-take-the-making-of

| Věc | Co to je | Hodí se? | Přínos / pracnost | Kde u nás |
|---|---|---|---|---|
| **Textury kontrolované ve třech světelných podmínkách, než jdou do hry** | každý nový povrch (útes, břidlice, drn, kámen v řece, dřevo, vápenná omítka, kachle) nejdřív na snímku ve 3 světlech | **ANO.** Naše chyby č. 107 (černé střechy ve stínu) a 230 (černé podlahy) by tím vyšly dřív. Navazuje to na nedodělek ze 17. 11. („porovnat barvu unshaded trávy v jiných denních dobách – kalibrace jen PC odpoledne“). Návrh: `PUCHART_FOTO` se třemi časy dne (ráno, poledne, podvečer) + interiér s loučí, obrázek 2×2 vedle reference | střední / **S** | `den.gd` (čas z proměnné prostředí), `nastroje/foto_portaly.sh` nebo nový `nastroje/foto_svetla.sh`, modelový filtr v CLAUDE.md („test ve stejném světle“ → „ve třech světlech“) |
| **Testovací bot proletěl každý přechod** | ověření dosažitelnosti | NE – máme test průchodu; rozšíření viz A1 (mřížka) | – | – |
| **Rodin: 512 vygenerovaných rekvizit, 360 použitých (70 %)** | AI drobné předměty | **MOŽNÁ** – viz kap. 2, bod AI modely | – | – |
| **Hlavní agent rozdělí ostrovy pomocníkům a výsledky sloučí** | souběžná práce agentů | MOŽNÁ jako způsob práce (např. hlídači po stavbách), ne změna hry | – | – |
| **Terén z AWS Terrain Tiles** | – | NE – máme přesnější DMR 5G | – | – |
| **DLSS, Lumen, objemové mraky** | – | NE (jiný engine a GPU) | – | – |

### A9. Void Explorer (s. 5) – web, OpenAI
Zdroje: https://void-explorer.openai.chatgpt.site/ , https://developers.openai.com/showcase/void-explorer
- PDF radí sledovat ovládání a kameru při výstupu a nástupu. U nás obdoba: nasednutí a sesednutí z koně (`jizda.json`).
  **NE** jako nová technika – jen připomínka, ať má jízda v testu průchodu i nasednutí/sesednutí.

### A10. PDF A s. 5 „Pro cesty a kolize v Puchartu“
„Pražský autotest přechází celé město. Stejný princip můžeš použít na jednu stálou trasu od úpatí hřebene až k bráně a
dovnitř hradu.“ → **Už máme** (`test_pruchod.gd`, trasy v `hra/data/pruchody*.json`, kritické selhání blokuje APK).
Nové je jen to, co je v A1: mřížka dosažitelnosti místo jednotlivých tras.

---

## 2. PDF B – „Herní grafika Čína / Japonsko / Indie“

### B1. Chrám v Unrealu (s. 1) – @xingbugengming, Codex + Claude + Tripo
Zdroje: https://x.com/xingbugengming/status/2120049690624635261 ,
https://blog.hyperindex.org/ai-unreal-engine-game-development/

| Věc | Co to je | Hodí se? | Přínos / pracnost | Kde u nás |
|---|---|---|---|---|
| **Suché rostliny ze spár dlažby a u paty stupňů** | vegetace tam, kam se nešlape | Většinou **máme** (`pata_zdi.json`, KCD předloha vsi: „tráva u paty zdí a plotů“). **MOŽNÁ** rozšířit na paty schodů a spáry dlažby nádvoří hradů, pokud tam dnes chybí. Nejdřív reference (KCD fotky nádvoří) | nízký / S | `pravidla/svet/pata_zdi.json`, `byliny.gd` |
| **Kámen, půda a tráva mají na přímém slunci podobný žlutohnědý tón** | jednotná barevnost scény | NE jako technika – úprava barev je v `hlavni.gd` (ACES, `adjustment`). Jen jako připomínka při kalibraci podle fotek | – | – |
| **Tripo vyrobil jednotlivé modely** | AI 3D z obrázků | viz B6 | – | – |

### B2. NOSTALGIC TRAIN (s. 2) – Tatamibeya, UE4
Zdroje: trailer https://www.youtube.com/watch?v=TILk5eoqdZY , materiály https://cgworld.jp/feature/201811-cgw244-nostal.html

| Věc | Co to je | Hodí se? | Přínos / pracnost | Kde u nás |
|---|---|---|---|---|
| **Dynamic Material Layering** (podle The Order: 1886) | Sdílené dlaždicové základy (prkna, kov, omítka, beton) pro celý projekt + na každý model 3 malé masky ≤ 512 px (AO, ohlazené hrany, gradient shora dolů) ze Substance Smart Masks. 4 vrstvy na materiál, do přechodu přimíchaný šum (kontrast, měřítko), barva vrstvy přes overlay. 15 masek na celý projekt | **MOŽNÁ → ANO po pokusu.** Úspora paměti i detail „opotřebení tam, kde se používá“ (KCD princip). **Úprava pro náš limit 13 vzorkovačů:** masky nedávat do textur, ale **zapéct do barvy vrcholů** v Blenderu (R = AO, G = hrany/ošlapání, B = stékání shora) → 0 vzorkovačů navíc. Vrstvy jen 2–3 (např. kámen + omítka + mech/špína), s hex-tilingem, který `zdivo.gdshader` už má. Pozor: `zdivo` má 7 vzorkovačů, další vrstva s normálou = +2 | střední–vysoký / M (jedna stavba jako pokus, pak společná funkce pro všechny – pravidlo „prvek, který mají i jiné stavby“) | `blender/` (zapečení masek do COLOR_0), `zdivo.gdshader`, `textura.gdshader`, `pravidla/svet/hrad_vzhled.json`, `barvy_vrcholu.json` (pozor na převod sRGB) |
| **Přechod voda → kámen → tráva → první řada stromů** (PDF s. 2: „pro Havran je přenositelný hlavně nepravidelný přechod vody přes kámen a trávu“) | kompozice břehu | Máme `koryto_kameny.py`, `koryta.py`, `voda.gdshader` (břeh do ztracena). **MOŽNÁ** jen snímková kontrola břehů proti této fotce (odkrytý balvan na jedné straně, stín stromu na druhé) | nízký / S | `nastroje/koryto_kameny.py`, `pravidla/svet/voda.json` |

### B3. A Taste of Home (s. 2) – KuroGameMaker, generativní AI na modely a textury
Zdroje: https://store.steampowered.com/app/4161930/ (AI prohlášení: „3D modely a jejich textury“),
trailer https://www.youtube.com/watch?v=8xbLgImZBNI
- PDF: „dlouhá zídka prozradí opakování stejného dílu“. **NE jako technika** – naše stavby, ploty a palisády se staví
  procedurou z dat a hex-tiling řeší opakování textury. Jen připomínka: u dlouhých plotů a zídek kontrolovat snímkem,
  jestli se neopakuje stejný díl.

### B4. Unleash the Avatar (s. 3) – Aeos Games, skeny města Chanderi
Zdroje: https://www.youtube.com/watch?v=X4yG8I2YNs4 , https://www.aeoscompany.com/#games ,
https://www.digit.in/features/gaming/unleash-the-avatar-hands-on-varun-mayyas-myth-soaked-action-rpg-calls-upon-its-avatar-form.html/amp/

Studio skenuje vlastní povrchy (drolící se vápenná omítka, sluncem rozpálený kámen, ohlazené dřevo). AI na assety
nepoužívá, jen na nápady a interní nástroje. Optimalizace: profilování, rozpočty textur, stíny jen u vybraných světel.

| Věc | Co to je | Hodí se? | Přínos / pracnost | Kde u nás |
|---|---|---|---|---|
| **Vlastní fotogrammetrie povrchů z místa děje** | Míša (nebo kdokoli na místě) nafotí telefonem kus zdi zříceniny Puchartu, drobu a břidlici z lomu, kámen v korytě, starý trám. **RealityScan Mobile** (Epic) je zdarma i pro komerční použití, export GLB/OBJ do telefonu; Epic smí data použít k tréninku, v aplikaci se to dá vypnout (https://www.cgchannel.com/2025/11/epic-games-releases-realityscan-mobile-1-8/). V Blenderu pak zapéct výřez na dlaždicovou texturu 1k (albedo, normála) | **MOŽNÁ.** Splňuje „vždy podle reference“ lépe než Poly Haven – je to přímo kámen Potštátska (droba/břidlice, ne pískovec). Na tablet nic nestojí (stejné 1k textury jako dnes). Nevýhoda: závisí na focení v terénu a na počasí (rovnoměrné zataženo) | vysoký pro věrnost / M + den focení | `nastroje/droba_tex.py`, `blender/skaly_scan/`, `pravidla/svet/skaly.json` a `hrad_vzhled.json` (`zdroj`: sken + datum) |
| **Stíny jen u vybraných světel** | – | NE – v Compatibility máme stíny jen od slunce do 40 m | – | – |

### B5. Vilaayath Budha (s. 3) – Offline Human Studios, UE5 na Androidu
Zdroje: https://play.google.com/store/apps/details?id=com.offlinehumanstudios.vilaayathbudha ,
https://www.offlinehumanstudios.com/post/vilaayath-budha-epic-megagrant
- Technika: procedurální vegetace (UE PCG), HLOD + World Partition streamování, reálný výškový model. Čísla (FPS,
  rozpočty, vzdálenosti) studio neuvádí.
- **NE** jako nová technika – obdobu máme: buňky a zásoba MultiMeshů (`zasoba_mm.gd`), hrubé obaly staveb jako HLOD
  (`ves.gd`, `hlavni.gd`, `mista.json obal`), DMR. PDF upozorňuje na **chybu**, kterou si u nás ohlídat snímkem:
  „zblízka hladký zelený povrch svahu, mezi kmeny chybí členitý podrost“. U nás to řeší `byliny.gd` (kapradí, mech,
  ostružiník) a nové světliny 17. 11. – kontrola snímkem lesa po změně trávy.

### B6. Qiankun Seal · Ming (s. 4) – studio Yuren, PC
Zdroj: https://store.steampowered.com/app/4876710/?l=english
- „Podél pěšiny se střídají holá místa, tráva, květy a kameny. Vzdálené svahy působí hladce.“ → **máme**
  (`pesiny_k_mistum.py`, hlína kde se chodí, byliny, LOD trávy). **NE.**

### B7. Snow-Cleared Zen Forest (s. 4) – Tripo + ZBrush + Substance, UE5
Zdroj: https://developers.tripo3d.com/zh/cookbook/heritage-digital-restoration

Postup: 1 fotka + 3–6 pohledů → Tripo H3.1 (až ~2 M ploch za minutu) → ZBrush (prsty, ozdoby) → retopologie v Tripu na
150 tis. trojúhelníků → 4K textura → Substance bake (BaseColor, Normal, Roughness, Metallic, AO) → UE5 Nanite/Lumen.

**AI 3D modely obecně – MOŽNÁ, nízká priorita:**
- **Co to je:** model z jedné nebo více fotek. Výstup je hustý (statisíce ploch) a pro tablet se musí decimovat na
  jednotky tisíc trojúhelníků, 1k textury, LOD a kolize – tedy celý náš modelový filtr.
- **Licence (rozhoduje):**
  - **Hunyuan3D 2.0 / 2.1 (Tencent): NE** – licence definuje území „worldwide, excluding the European Union, United Kingdom
    and South Korea“ (https://huggingface.co/tencent/Hunyuan3D-2/blob/main/LICENSE). Česko je v EU.
  - **TRELLIS.2 (Microsoft): MIT** (https://huggingface.co/microsoft/TRELLIS.2-4B), běží lokálně, ale potřebuje silnou
    GPU (v kontejneru ji nemáme) a výstup je hustý.
  - **Tripo:** zdroje si odporují. Blog uvádí CC BY 4.0 i pro bezplatný plán, nápověda a ToS (5.2.1) říkají, že výstupy
    bezplatných uživatelů patří Tripu a komerčně se použít nedají
    (https://www.tripo3d.ai/help/privacy-policy/how-to-use-tripo-models-commercially). Bezpečné je jen placené Tripo.
  - **Rodin (Second Take)** a **Meshy** – podmínky ověřit před použitím (Meshy zdarma = CC BY 4.0 s uvedením autora).
- **Kde by se hodil:** drobné předměty a „život“ vsi (džbány, koše, nářadí, sochy světců), kde nemáme hotový model
  z Havrana / Poly Haven / Quaternius ani od modeláře. **Nikdy** stavby a konstrukční díly (pravidlo „stavím jako tesař
  a kovář“ a KCD předlohy). Každý AI model označit v katalogu jako NAVRH, historickou vhodnost zkontrolovat proti
  referenci, autora nástroje dát do titulků.
- **Přínos / pracnost:** nízký–střední / M (decimace a LOD se dají doplnit do `nastroje/`, `glb_prebal.py`).

### B8. AI animace (zadání Míši: „AI nástroje na modely, textury a animace“)
PDF animace zmiňuje jen u chrámu (Codex pomáhal s výběrem a úpravou animací). Stav u nás: postavy přijdou z Havrana
(krok F), máme rešerši doplňků (`docs/reference/doplnky/README.md`: Moveset Free CC BY 4.0, MPFB, Rigify).
- **Video → pohyb (mocap z videa):** Move AI zdarma bez kreditů, komerčně až od placeného plánu; Plask zdarma jen
  nekomerčně; Cascadeur zdarma bez FBX exportu; Rokoko Video zdarma, podmínky nedohledané
  (https://80.lv/articles/rokoko-video-new-free-ai-motion-capture-tool/).
- **Verdikt: MOŽNÁ, až u kroku F** (postavy). Teď nic.

---

## 3. Co z PDF už Puchart má (nenavrhuji)

| Technika z PDF | Projekt | Puchart |
|---|---|---|
| Hemi-oktaedrické impostory, dithered LOD pásma | Halcyon | `hra/shaders/impostor.gdshader` (atlas 8×8), `les.gd` časované prolnutí (`stromy_modely.json lod_casove`) |
| Stínová tělesa jen ve stínu | Halcyon | `SHADOWS_ONLY` (`ves.gd`, `les.gd`, `predmety.gd`, `hlavni.gd`) |
| HLOD – vzdálená stavba jako zjednodušený tvar se skutečnou texturou | Vilaayath Budha | `ves.gd` obaly, `hlavni.gd` `_Daleko`, `mista.json obal`, střední LOD domů (č. 273) |
| Předehřátí shaderů před hrou | Halcyon | `hra/scripts/predehrati.gd` |
| Povrch podle mapy vegetace, opad pod korunami, triplanární útesy | Halcyon | `zem.gdshader`, `louka.json les.puda`, `skala.gdshader` |
| Procedurální stavby z Blender Pythonu, svět z JSON | Alchemists | `blender/`, `nastroje/`, `pravidla/svet/*.json` |
| Autotest celé trasy, snímkové prohlídky | Alchemists, Second Take | `test_pruchod.gd`, `pruchody*.json`, `PUCHART_FOTO`, hlídač scén |
| Reálný terén z výškových dat | Halcyon, Second Take, Vilaayath | DMR 5G, `teren_dlazdice.py`, `dmr_mrizka.py` |
| Opakování textur (hex-tiling) | (A Taste of Home – problém) | `zdivo.gdshader` (Mikkelsen 2022) |
| Tráva u paty zdí, hlína kde se chodí | Chrám, Qiankun Seal | `pata_zdi.json`, `pesiny_k_mistum.py`, předloha `docs/reference/kcd_ves_predloha/` |
| Zásoba MultiMeshů, buňky kolem hráče | Halcyon, Vilaayath | `zasoba_mm.gd`, `bunky_kolem.gd` |
| Dotykové ovládání | Alchemists, Vilaayath | Puchart Android (jako Havran) |

---

## 4. Nepoužitelné pro Godot 4.7 Compatibility na Adrenu

| Technika | Odkud | Proč ne |
|---|---|---|
| Voda čtoucí obraz a hloubku pod hladinou (lom, kaustiky) | Halcyon | potřebuje kopii obrazovky (pravidlo, pády Havrana 0.58–0.59) |
| Automatické snižování rozlišení, Catmull-Rom + doostření | Halcyon | Compatibility umí jen bilineární škálování, FSR a doostření jen Forward+ (https://docs.godotengine.org/en/4.7/tutorials/3d/resolution_scaling.html); Míša: automatika jen přes detail |
| Shader baker, ubershadery | (souvisí s Halcyonem – „všechny shadery před úvodem“) | jen Forward+/Mobile; v Compatibility „no effect“, doporučené je předehřátí – máme (https://docs.godotengine.org/en/4.7/tutorials/performance/pipeline_compilations.html) |
| Paralaxa (POM) dlažby | Alchemists | drahá na pixel; autor sám snižuje kroky na mobilu a má 6–10 FPS na iGPU |
| FFT oceán, CDLOD mřížka vody, simulace vlnek | Halcyon | cena na pixel a render targety; naše voda je řeka s normálovou mapou (2 vzorkovače) |
| Lumen, Nanite, World Partition, PCG, HLOD builder, DLSS, objemové mraky | Second Take, Vilaayath, Unleash, Zen Forest | Unreal / desktop GPU |
| Terrain3D | The Last Eagle | testováno 29. 10., zůstáváme u vlastních dlaždic |
| Hunyuan3D | (AI 3D obecně) | licence vylučuje EU |
| Průhledné prolínání `visibility_range` (fade) | (obecně u HLOD) | průhlednost na Adrenu – zásada „bez průhledného prolínání dosahů“ (`docs/reference/vykon_vnitrek_reserse.md` č. 24) |

---

## 5. Doporučené pořadí (po hlídačích a měření tabletu z plánu 16. 11.)
1. **Kontrola ve třech světlech** (S) – hned k dodělku trávy ze 17. 11. (barva unshaded trávy v jiných denních dobách).
2. **Regulátor detailu** (S–M) – data `rozpocty.json automatika`, nejdřív jen zápis do panelu, co by udělal (bez zásahu),
   změřit na tabletu 30 min, pak zapnout.
3. **Mřížka dosažitelnosti** (M) – nálezy převést na trasy a řádky v `docs/chyby.md`.
4. **Vrstvení s maskami v barvě vrcholů** (M) – pokus na jedné stavbě vsi, snímek proti KCD předloze.
5. **Stíny mraků, ohýbání trávy** (S) – až po referenci z KCD (pravidlo „nic z hlavy“) a měření na tabletu.
6. **Skeny povrchů a AI předměty** – podle toho, jestli Míša chce fotit v terénu; AI jen pro drobné předměty a jen
   s ověřenou licencí.
