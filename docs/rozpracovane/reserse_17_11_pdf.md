# Rešerše 17. 11. – dvě PDF od Míši (3D hry s AI; herní grafika Čína, Japonsko, Indie)

Zadání Míši (17. 11.): „Podívej se na to, zase malá rešerše, nastuduj, podívej se na ty věci na internetu, třeba se něco hodí.“
Zapsáno 17. 11. 2026 15:16. Hru, kód ani data jsem neměnil. Nic jsem nespouštěl ani neměřil.

Značky: **OVĚŘENO NA WEBU** = přečteno ve zdroji (stránka, README), **NEOVĚŘENO** = jen tvrzení PDF nebo zdroj chybí či si
odporuje, **U NÁS** = přečteno v našem repu. Čísla jsou převzatá ze zdrojů. Žádné jsem neměřil.

## 1. Co v PDF je

### PDF 1 – „Jaké 3D hry lidé tvoří s AI“ (5 stran, 9 projektů)
Přehled her, u kterých lze porovnat hru se záznamem vývoje:
- **Alchemists of Prague**: Godot, Android a web, Compatibility, Blender přes Python, Claude Code.
- **The Last Eagle**: Godot 4, Terrain3D podle PDF, balíky modelů a Meshy.
- **Capybara**: three.js.
- **Halcyon**: three.js a WebGL2, 43 000 skenovaných rostlin, impostory, lehčí podklady pro telefony.
- **San Francisco**: Codex a Apple Maps.
- **Wildhearth**: Godot, Blender skripty.
- **Earth Simulator**: Steam.
- **Second Take**: UE5, skutečné výšky terénu.
- **Void Explorer**: web, GPT.

Závěr PDF (str. 5): pro Havrana stojí za to porovnat Halcyon (blízké koruny, vzdálené stromy, hranice přechodu, naměřené
časy lesní procházky). Pro Puchart doporučuje pražský autotest jako stálou trasu.

### PDF 2 – „Herní grafika pro Havrana: Čína, Japonsko, Indie“ (4 strany, obrazová rešerše)
- Čínský chrám v UE od jednoho autora: Codex, Claude a modely z Tripo. Detail dlažby, rostliny ve spárách, ale jednotný
  žlutohnědý tón kamene, půdy i trávy.
- NOSTALGIC TRAIN (Japonsko, UE4): přechod vody přes kámen a trávu k první řadě stromů.
- A Taste of Home (AI modely a textury): dlouhá zídka prozradí opakování stejného dílu.
- Unleash the Avatar (Indie): skeny města Chanderi, detail u nohou a hloubka průchodů.
- Vilaayath Budha (Android, UE5): čitelná cesta, ale hladké svahy a chybí podrost. Procedurální vegetace a HLOD.
- Qiankun Seal (Čína): okraj pěšiny střídá holá místa, trávu, květy a kameny.
- Snow-Cleared Zen Forest: Tripo + ZBrush + Substance, render v UE5.

Hlavní poučení PDF je výtvarné: detail u nohou, nepravidelné přechody, střídání pokryvu a vyhnout se opakování dílů.
Technické postupy jsou hlavně v odkazech.

## 2. Tabulka – co to je a hodí se nám?

Naše meze: tablet bez MSAA, bez shaderů se screen texture, 3D pevně 75 %, Godot **4.4.1** Compatibility (GLES3). Pipeline
je Blender skripty → glb → Godot, s pravidly v datech.

| věc | co to je (ověřeno) | hodí se nám? | proč | konkrétní další krok + zdroj |
|---|---|---|---|---|
| **Alchemists of Prague – `--reach` sonda** | **OVĚŘENO NA WEBU:** fyzikální sonda po mřížce buněk najde dosažitelná místa a `tools/seal_world.py` podle ní staví hraniční zdi. README neuvádí licenci kódu. Godot 4.7.2, Blender 5.2 | **ano** (princip) | Řeší naši otevřenou otázku z bodu 16 (misa_17_11): na kolik oddělených částí se rozpadá síť chůze, která se dosud neměřila. Pomůže i u předmětů a staveb mimo dosah | Test hry: komponenty grafu `lide._g` (počet, velikost, poloha) + mřížka dosažitelnosti od brány vsi a tvrze. Výsledek do testu jako mez z `pasma`. Kód nepřebírat (není licence), jen postup. https://github.com/msveshnikov/alchemists-of-prague |
| Alchemists – autotest se 70 kontrolami a snímky | **OVĚŘENO NA WEBU:** `--autotest` (náměstí, inventář, boj, domy, obchod, noc, uložení, průchod světem), zvlášť sonda `--perf` | možná | Máme měřicí trasu a testy hry. Nové je jen „průchod celým světem s kontrolou“ v jednom běhu | Žádný nový nástroj. Případně přidat do trasy kontrolu „hráč došel do cíle úseku“ (zaseknutí = chyba). Zdroj výše |
| Alchemists – výkon na Androidu | **OVĚŘENO NA WEBU:** Compatibility, ETC2, na Intel UHD 620 jen 6–10 FPS. Čísla z Androidu nejsou | ne | Není vzor výkonu. NPC jen do ~105 m, bez LOD a impostorů. My máme `postavy.json dosah_m` 70 a LOD animací | – |
| Alchemists – ptáci MultiMesh s animací v shaderu | **OVĚŘENO NA WEBU:** jeden MultiMesh na druh, křídla a hlava se hýbou ve vertex shaderu | možná | Levná zvířata v dálce (ptáci, stádo) bez kostry | Až po měření ceny `zvirata.gd` na trase. Viz řádek VAT |
| **claude-game-pipeline** (plugin Claude Code) | **OVĚŘENO NA WEBU:** MIT. Pracovní postup od předlohy z ChatGPT přes Blender a Godot po vydání. `align_to_layout.py` (OpenCV ECC) přetáhne malbu na render rozvržení | možná (málo) | LOD, optimalizaci ani mobil neřeší. Náš postup s pravidly a testy je dál. Hodí se jen ECC zarovnání snímku na předlohu | Případně jen ke srovnání snímků s předlohami (bejcek, kcd), ne jako postup stavby. https://github.com/msveshnikov/claude-game-pipeline |
| **Halcyon – vegetace** | **OVĚŘENO NA WEBU:** MIT (kód, assety mají vlastní licence). Instancing, blízko geometrie s **ditherovanými pásmy LOD**, dál **hemi-oktaedrické impostory**, stínová tělesa jen pro stín. `flora.mjs` peče atlasy a LOD rostlin skriptem | **ano** (potvrzení směru) | **U NÁS** už je totéž: hemi-oktaedrické impostory 8×8 (`blender/impostory.py`), stínová tělesa `SHADOWS_ONLY`, plán K13 (časované prolínání) a vlastní mezistupně stromů. Halcyon má **LOD stupně pečené skriptem**, my u stromů jen LOD0 a impostor + automatické LOD Godotu | Dokončit z rozboru GPU K13: vlastní LOD1/LOD2 stromů v Blenderu (decimace a méně karet listí). https://github.com/billpwchan/halcyon |
| Halcyon – měření | **OVĚŘENO NA WEBU:** po 30 s na pohled p50, p95 a % snímků nad 20 ms (všechny pohledy p50 16,7 ms, p95 ≤ 17,6 ms, PC Apple silicon v Chrome) | **ano** | Měřicí trasa vypisuje špičky. Tabulka po úsecích s p95 a „% snímků nad 33,3 ms“ (zásek pro náš cíl 30 FPS) by verze srovnala lépe než průměrné FPS. **U NÁS:** p95 už počítá `scripts/kvalita.gd`, trasa je NEOVĚŘENO | Doplnit do tabulky trasy sloupce p95 a „nad 33,3 ms %“ (mez do `mereni_trasa.json`). Zdroj výše |
| Halcyon – governor snižuje rozlišení | **OVĚŘENO NA WEBU:** při p75 nad 19,5 ms sníží měřítko vykreslení | **ne** | Odporuje pravidlu z CLAUDE.md: rozlišení za běhu neměnit (zásek 1,36 s), pevně 75 % | – |
| Halcyon – KTX2, postupné načítání HD textur | **OVĚŘENO NA WEBU:** glTF + KTX2, HD textury se dotahují po snímcích | ne | Godot 4.4 nemá streamování textur. Kompresi už máme (`import_etc2_astc=true`, **U NÁS** 1 126 importů s `compress/mode=2`) | – |
| **Terrain3D** (Godot plugin) | **OVĚŘENO NA WEBU:** MIT, GDExtension, LOD terénu až 10 stupňů. „Compatibility (GLES3) plně podporováno od Terrain3D 1.0 a Godot 4.4“. Android „hlášeno, že funguje, stále trochu experimentální“, „některá mobilní zařízení plně nepodporují texture arrays“ | **ne** | Terén staví Blender a ve stejném kroku stehuje cesty, vodu a pásma. Testy smyslu a zasazení čtou glb. Terrain3D by tuto pipeline rozbil. **U NÁS** už běží vlastní řešení K4 (dlaždice 128 m s LOD, `pravidla/svet/teren_dlazdice.json`, převzato z Pucharta). Zda poslední vydání Terrain3D běží na 4.4.1 je NEOVĚŘENO | – (jen jako srovnání, kdyby K4 selhalo). https://terrain3d.readthedocs.io/en/latest/docs/platforms.html |
| **Octahedral impostor pluginy pro Godot 4** | **OVĚŘENO NA WEBU:** `godot-imposter` (MIT, ověřeno na Godot 4.5 beta, renderer neuveden, komprese textur „v plánu“). `Octahedral Impostor LOD` (licence nejasná: v katalogu „Proprietary“, jinde „vlastní, s uvedením autora“; Forward+ a Mobile, Compatibility neuvedeno) | **ne** | Impostory pečeme sami v Blenderu a máme je pod kontrolou dat. Pluginy nemají ověřené GLES3. Druhý má nejasnou licenci | – https://github.com/zhangjt93/godot-imposter , https://godotengine.org/asset-library/asset/5528 |
| **VAT – vertex animation textures** (antzGames plugin, OpenVAT) | **OVĚŘENO NA WEBU:** antzGames MIT, **vyžaduje Godot 4.5+**, „funguje na všech rendererech“, test v Compatibility 2 000 instancí 354/536 FPS (stín zap./vyp., PC RX 9060 XT). Síť < 8 192 vrcholů, bez míchání stop, textury EXR a PNG bezeztrátově bez mipmap. OpenVAT je Blender add-on (výstup EXR + JSON) | **možná** (technika, ne plugin) | Plugin na 4.4.1 nepoběží. Shader se dá napsat sám (čtení textury ve vertex shaderu GLES3 umí). Hodil by se na vzdálené postavy (25–70 m) a zvířata jako MultiMesh bez kostry. **Ale:** sady oděvů jsou zvláštní sítě, takže by šlo o jednu síť na variantu postavy a ruční sloučení. U NÁS trasa 0.99995: „postavy bez vlivu“, hostinec 17. 11. „lidé 11 ms“ | Nejdřív změřit, kolik stojí kostry a animace postav za 25 m (varianta trasy). Teprve při naměřené ceně prototyp VAT pro jednu postavu v Blenderu. https://github.com/antzGames/Godot_Vertex_Animation_Textures_Plugin , https://extensions.blender.org/add-ons/openvat/ |
| **HLOD** (Vilaayath Budha: World Partition + HLOD v UE5; Godot „Visibility ranges (HLOD)“) | **OVĚŘENO NA WEBU:** studio uvádí jen „World Partition s HLOD“ a „PCG pro hustou vegetaci“, bez čísel. Godot 4.4 má visibility ranges s `visibility_parent` (HLOD). Prolínání jen alfou, režimy fade Self a Dependency jen ve Forward+ (v Compatibility se chovají jako vypnuté) | **možná** | Vzdálenou ves a tvrz by šlo za ~150 m nahradit jednou sloučenou zjednodušenou sítí na blok, pečenou v Blenderu (méně volání kreslení). **PODEZŘENÍ:** mohlo by to odstranit i „domy zdálky černé“ (bod 5), pokud je příčinou automatické LOD (podobně jako u rybníka a domu 6 v 0.997). Příčina bodu 5 není rozebraná. Prolínání alfou na tabletu nechceme, přepnutí jen ditherem v našem shaderu (K13) | Nejdřív rozbor bodu 5 (snímek z 06 a 07 s vypnutým `generate_lods` u domů). Potom případně Blender krok „hlod_ves“ (sloučení domů bloku, LOD2, jeden materiál nebo atlas) jako záznam v datech. https://docs.godotengine.org/en/4.4/tutorials/3d/visibility_ranges.html , https://www.offlinehumanstudios.com/post/vilaayath-budha-epic-megagrant |
| **NOSTALGIC TRAIN – vrstvené materiály** (dynamic material layering) | **OVĚŘENO NA WEBU** (CGWORLD): sdílená knihovna dlaždicových textur pro celý projekt. Každý model má jen masky TGA ≤ 512 px (3 masky, 4 vrstvy) a šum v míchání. Cíl: „vysoké rozlišení při malé paměti“, vhodné pro otevřené světy s úzkou pamětí. Vegetaci a vodu článek nepopisuje | **možná** | **U NÁS** VRAM ~900 MB, z toho textury 619 MB (rozbor GPU 15. 11.), a pád po ~44 min s vysokou pamětí. Sdílené textury a malé masky jsou přímá cesta k menší VRAM. Tablet umí jednoduchý shader s maskou. Není jisté, že pád způsobují textury (NEOVĚŘENO) | Nejdřív výpis: 30 největších textur ve VRAM (rozměr, kdo je používá, duplicitní obsah). Pak pravidlo v datech „unikátní textura budovy max N px, jinak sdílená knihovna + maska“. https://cgworld.jp/feature/201811-cgw244-nostal.html |
| NOSTALGIC TRAIN, Qiankun Seal, Unleash the Avatar – výtvarné poučení (přechod voda/kámen/tráva, střídání pokryvu u pěšin, detail u nohou) | Obrazové předlohy, ne technika | **ano** (jako předloha pro pravidla) | Sedí na naše pravidla stanoviště (`pravidla/svet/druhy.json`, `les_podrost.json houstina.pesiny`). Míšin bod 8 chce víc houštin | Do pravidel podrostu pěšin přidat střídání (holé místo, tráva, květy, kámen) jako pásmo v datech a kontrolu v testu smyslu. Snímky: viz odkazy v PDF (Steam 4876710, cgworld) |
| A Taste of Home – opakování dílu zídky | Hra přiznává generativní AI pro modely a textury (Steam). Poučení: dlouhá zídka z jednoho dílu je vidět | ano (poučení) | Naše zídky a ploty se skládají z dílů. Pravidlo variace (natočení, výběr z ≥ 2 variant, barva vrcholů) jako záznam | Kontrola v testu: žádné ≥ N stejných dílů za sebou beze změny (N do `pasma`). https://store.steampowered.com/app/4161930/ |
| **Tripo** (AI modely z obrázků) | **OVĚŘENO NA WEBU** (Tripo cookbook): H3.1 dá ~2 mil. ploch za ~1 min, retopologie na 150 000 troj., 4K textura, dokončení v ZBrushi a Substance. **Licence bezplatné úrovně si zdroje odporují:** blog Tripo uvádí CC BY 4.0 i pro komerční užití, srovnávače „nekomerční“, NEOVĚŘENO. Placené plány od ~16–20 USD/měs. (podle srovnávačů, NEOVĚŘENO) | **ne** (teď) / možná u jednotlivé rekvizity | 150 tis. troj. na jeden předmět je pro tablet řádově moc (naše stromy LOD0 ~7–12 tis.). Potřebuje ruční ZBrush a Substance. Cloud, nejasná licence. Pravidlo „nejdřív hledat hotové“ (Poly Haven, ambientCG, Kenney, Quaternius) je levnější a čisté. Sady oděvů postav (díry v hrudníku, bod 10) neřeší, to je chyba napasování a vah, ne zdroje modelu | Nepoužívat. Případně jedna rekvizita jako pokus s retopem na rozpočet z `rozpocty.json` a CC BY uvedením. Napřed ověřit podmínky na tripo3d.ai. https://developers.tripo3d.com/zh/cookbook/heritage-digital-restoration , https://www.tripo3d.ai/blog/commercial-use-ai-3d-models |
| Rodin / Meshy (Second Take, The Last Eagle) | **OVĚŘENO NA WEBU** (deník Second Take): z 512 generací drobností Rodin ponecháno 360 po renderu a kontrole. Meshy u The Last Eagle jen podle PDF (NEOVĚŘENO, Reddit nešel načíst) | ne | Stejné důvody jako Tripo. 152 z 512 výstupů (~30 %) šlo do koše | – https://atlas-house.itch.io/second-take/devlog/1782124/second-take-the-making-of |
| Second Take – skutečné výšky terénu | **OVĚŘENO NA WEBU:** AWS Open Data Terrain Tiles, převod Pythonem (NumPy, Pillow). UE5, DLSS, 300 000+ kusů trávy | možná (nízká priorita) | Terén pro tvrz s reálným reliéfem české krajiny by šlo vzít z otevřených výškových dat. Licence českých dat (ČÚZK DMR) je NEOVĚŘENO. Náš terén je dán pravidly a daty, změna by znamenala přestavbu všeho. DLSS a Lumen na tabletu nejsou | Nic teď. Případně jen jako předloha tvaru svahů |
| The Last Eagle | **OVĚŘENO NA WEBU** (itch.io): Blender + Godot, sólo vývoj, hra zatím nevydaná, technika neuvedena. Terrain3D a balíky modelů jen podle PDF a Redditu (NEOVĚŘENO) | ne (není co převzít) | Ukazuje stejný postup jako naše pravidlo: balíky a úpravy místo generování. Není hratelná verze ani čísla | Sledovat devlog kvůli davům v ulicích. https://dometgames.itch.io/the-last-eagle |
| Chrám v UE (Codex + Claude + Tripo, hyperindex blog) | **OVĚŘENO NA WEBU:** Claude stavěl whitebox a světlo, Tripo budovy a postavy, Codex ovládání, animace z Mixamo a Fab. Licence článek neuvádí | ne | UE, Lumen, Nanite. Poučení o „jednotném žlutohnědém tónu“ = kontrola barevné odlišnosti povrchů ve snímku | Do kontroly snímků před vydáním: rozliší se kámen, půda a tráva i na přímém slunci? https://blog.hyperindex.org/ai-unreal-engine-game-development/ |
| Unleash the Avatar – skeny Chanderi | **OVĚŘENO NA WEBU** (Digit): povolení ASI naskenovat celé město. Generativní AI se podle studia na assety nepoužívá. „9 dní snímání, 6 měsíců čištění“ v článku není (NEOVĚŘENO, možná ve videu) | ne (sken) / ano (poučení) | Vlastní fotogrammetrie je mimo naše možnosti. Skenované CC0 kameny a textury už bereme z Poly Havenu a ambientCG | – https://www.digit.in/features/gaming/unleash-the-avatar-hands-on-varun-mayyas-myth-soaked-action-rpg-calls-upon-its-avatar-form.html/amp/ |
| Capybara (three.js), San Francisco (Apple Maps), Void Explorer (web), Earth Simulator (Steam), Wildhearth (Godot) | Webové a PC projekty. U Wildhearth jen „Claude psal Blender skripty“ (z PDF, technika neověřena) | ne | Jiný engine nebo platforma, nebo nic konkrétního k převzetí | – |

## 3. Top 5 doporučení (přínos ÷ práce)

1. **Test dosažitelnosti a souvislosti sítě chůze** (princip `--reach` z Alchemists of Prague). Výpis komponent `lide._g`
   a mřížka dosažitelnosti od brány. Malá práce. Ověří příčinu bodu 16 (NEOVĚŘENA) a najde zabedněná místa. Mez do
   `pasma`, kontrola do testů.
2. **Měřicí trasa s p95 a „% snímků nad 33,3 ms“ po úsecích** (jako tabulka Halcyonu). Malá práce, p95 už je v
   `kvalita.gd`. Srovnání verzí v `mereni_verze.md` bude citlivé i na záseky (rybník, les za lomem, tvrz), ne jen na
   průměrné FPS.
3. **Vlastní LOD stupně pečené v Blenderu místo `generate_lods` u citlivých sítí** (Halcyon `flora.mjs`; náš K13).
   Střední práce. Automatické LOD už dvakrát rozbilo data (dům 6 v 0.997, hladina rybníka 17. 11.). Pro stromy LOD1 a LOD2
   mezi 12 tis. troj. a impostorem. Jako první krok rozboru bodu 5 (černé domy) zkusit domy bez automatického LOD
   (PODEZŘENÍ).
4. **Audit textur ve VRAM a sdílená knihovna + malé masky** (NOSTALGIC TRAIN). Nejdřív jen výpis 30 největších textur a
   duplicit (malá práce), pak pravidlo v datech (střední). Cílí na paměť: 619 MB textur a pád po ~44 min. Že pád dělají
   textury, je NEOVĚŘENO.
5. **HLOD vzdálené vsi a tvrze** (Godot visibility ranges + sloučený blok z Blenderu; Vilaayath Budha). Větší práce. Méně
   volání kreslení v dálce a možná i konec „černých domů“, ale až po rozboru bodu 5 a po K4. Pořadí: rozbor → měření →
   prototyp jednoho bloku.

Mimo top 5: VAT pro vzdálené postavy a zvířata, až když trasa naměří cenu postav za 25 m. Plugin chce Godot 4.5, takže
vlastní shader. Tripo, Rodin, Meshy a Terrain3D teď nepoužívat (rozpočet trojúhelníků, licence, rozbití pipeline).

## Porovnání s rozborem Pucharta (Míša poslala snímek 17. 11. 15:31)
Puchart ze stejných PDF vybral navíc (u nás zatím nezapsáno):
- **Kontrola nového materiálu ve třech světlech** (ráno, poledne, večer + interiér s loučí) – hodí se nám hned: černé domy zdálky (ř. 5) a černé listí (ř. 3) by takový snímek odhalil dřív. → snímky `foto` ve 3 hodinách jako součást kontroly změny materiálu.
- **AI modely jen na drobné předměty:** TRELLIS.2 – podle Pucharta zdarma i pro hru (NEOVĚŘENO námi); Hunyuan3D v EU podle licence nesmíme.
- Stíny mraků přes krajinu, opotřebení staveb (špína bez textur navíc), ohyb trávy kolem hráče – možná, po fotkách z KCD a měření.
- Automatické ubírání detailu při zahřátí – u nás už je (`kvalita.gd`, jen v extrému, rozlišení nemění).
