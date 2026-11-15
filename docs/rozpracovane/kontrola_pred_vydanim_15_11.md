# Nezávislá kontrola před vydáním – 15. 11.

Rozsah: všechny změny od posledního vydání `f97a738` (0.999998) po `HEAD` (105 commitů, 181 souborů).
Recenzent neznal závěry stavitele. Godot ani Blender **nespouštěl**: jde o čtení kódu a dat, ověření JSON a Pythonu
a prohlídku snímků `build/f1511/*.png`. Rozlišení podle CLAUDE.md: tady jsou **podezření a důkazy z kódu a snímků**,
nic z toho není změřené na zařízení.

## Co prošlo
- Všechny změněné `pravidla/**/*.json` jdou načíst (`python json.load`), změněné `blender/*.py` a `tools/*.py`
  se přeloží (`py_compile`), `tools/*.sh` projdou kontrolou syntaxe (`bash -n`).
- Klíče, které čte nový kód, v datech existují: `lokace.ruiny` (kostel, zanikla_ves), `modely.dily_lod`,
  `nabytek.sedaky_modelu`, `rozpocty.snimek` a `kolize_dily`, `voda.rybnik_lhota` (obrys 63 bodů, `polomer_m` 16,84 =
  nejvzdálenější bod obrysu, lavka), `pasma.voda.holy_breh_padu_m`, `hrac.schody_zebrik_stupen_pod_m`,
  `plochy.lom.z/leseni_z`, `lokace.ves.stred_stare_navsi`, `lokace.krcma_l.kryti_lok`, `voda...schody_nastup`,
  `postavy.anim_strop_snimek/modif_odpojit/daleko_varianta`, `mereni_trasa.lehky_monitor/varianty_parametry`, `pocasi.strechy`.
- Bez MSAA a bez shaderu se screen texture (`pad.gdshader`, `dest.gdshader` jen průhledné blend_mix).
- V repu není soubor keystore (`git ls-files` bez .keystore/.jks/.p12). Heslo je v `tools/vydani.py:24` už dřív
  (CLAUDE.md to připouští), nový `tools/plny_instalator.py:41` ho jen čte odtud.
- Když chybí balík: `_kostel_dil` i `_ruiny_ves_dil` model kontrolují a jen vypíšou hlášku, hra se načte.
- Otočení průchodů zřícenin je v `svet.v_pruchodu_ruiny` stejné jako v `blender/kraj.py v_pruchodu_ruiny`
  (Basis(UP, a) = x cos + z sin, −x sin + z cos).
- `LOM_Z` a `LESENI_Z` se změnily z const na var a žádná statická funkce je nepoužívá. Kolize hřbitovní zdi
  (`Kostel_Kol_HrbZed52–56` v glb) jsou samostatná těla zarovnaná s osami, takže dělení `_kolize_podle_site`
  podle AABB sedí.

## Nálezy

| nález | soubor:řádek | závažnost | důkaz |
|---|---|---|---|
| Ve střední úrovni detailu (LOD) dílů se nepočítá barva vrcholů. Kostel nejdřív zapne `vertex_color_use_as_albedo` (mech, saze, vlhko v barvě vrcholů), ale `_dil_barva` bere jen `albedo_color` × průměr textury a střední síť barvu vrcholů nepřevezme (`cl.fill(c)`). Od 35 m (`podrobny_do_m`) do hrubého stupně proto vypadají zdi kostela a hřbitovní zídka **světle až bíle**, i když zblízka jsou tmavé. Tohle je znovu chyba z tabulky ř. 151 („bílé kostky z dálky“). | scripts/svet.gd:10539 (`_dil_barva`), 10475, 10692 | **BLOKUJE vydání** | `kostel.png`: dlouhé kvádry hřbitovní zídky (~330,420 a ~470,465) jsou ploché a bílé bez textury, zdi lodi jsou světle šedé. `kostel_zed.png`: tatáž zídka zblízka je tmavý kámen. Návrh: v `_dil_lod` násobit `c` průměrem `ARRAY_COLOR` povrchu, pokud má materiál `vertex_color_use_as_albedo`. |
| Hladina nového rybníka Lhota v2 je při nízkém pohledu **celá černá** (plocha bez kresby, působí jako díra). | snímky, materiál vody z Blenderu (rybník v2) | **BLOKUJE vydání** | `vypust.png` a `vypust_vys.png`: celá hladina za hrází je souvisle černá. `rybnik.png` (výš) je tmavá s kresbou a `hraz_shora.png` (shora) je v pořádku, takže jde o chybu závislou na úhlu (odraz pod obzorem / fresnel). Dřívější stížnost „bílá ledová plocha“ byla stejného druhu. |
| `data_manifest.json` zatím nemá balíky `z_kostel` a `z_ruiny_ves`. Starý kostelík kód nahrazuje, takže vydání bez nich = na místě kostela i Doubravy nic. | data_manifest.json; tools/vydani.py:249–254 (skupiny jen s `JEN`) | **BLOKUJE vydání** (podmínka: vydat s `z_kostel,z_ruiny_ves`) | Seznam balíků v manifestu končí `z_rybnik`. Skupiny se tvoří jen `if JEN and "z_kostel" in JEN`. Modely leží lokálně (`modely/kostel` 51 MB, `modely/ruiny_ves` 138 MB), ale jsou v .gitignore. |
| `pod_strechou` při každém volání spojuje pole `_uvnitr + _kryti` (nová alokace a kopie) a pro každý záznam dělá hloubkové porovnání `st in _uvnitr_bez_strechy`. Nová mapa střech v dešti ji volá pro každý paprsek (80 paprsků za snímek). | scripts/svet.gd:3482; scripts/pocasi.gd:321–352 | opravit brzy | V dešti každý snímek 80× `intersect_ray` + 80× kopie pole všech půdorysů. Na tabletu NEOVĚŘENO. Návrh: `_kryti` slít do `_uvnitr` jednou v `_plants` a „bez střechy“ označit třetím prvkem záznamu. |
| `_vynechat_uzly` kromě uzlu podle jména maže **každou** kolizi celou uvnitř obalu (AABB) odebrané geometrie +0,1 m. U `ChysePrkna_Interier` (celá skupina vnitřku) nebo `Mlyn_Dvur` na svahu může zmizet i kolize, kterou nikdo odebrat nechtěl (lavice, schod, kámen na dvoře). | scripts/svet.gd:10609–10645; lokace.json:3652, voda.json:5958 | opravit brzy | Heuristika podle polohy, ne záznam v datech (pravidlo „záplatování zakázáno“). Bezpečnější je kolize odebrat jménem (`*_Kol_*` v seznamu) a počty vypisovat do testu. |
| Strop kroků animace (`anim_strop_snimek` 8) je **zapnutý i ve výchozí hře**, ne jen ve variantě trasy. Když je blízko víc než 8 postav s plnou animací, část z nich dostane krok jen každý druhý snímek, což je stejná trhaná chůze, jakou opravoval 12. 11. | scripts/lide.gd:30, 2589–2621 | opravit brzy | Vliv podle dat NEOVĚŘENO. Strop by měl platit jen pro kroky `anim_daleko_fps`/`anim_dalka_fps`; plné (`krok_s = dt`) by měly zůstat bez stropu, nebo změřit trasou `bez_stropu_koster` na tabletu ještě před vydáním. |
| Odpojování modifikátorů od kostry (`modif_odpojit.zapnuto` true) je také výchozí. Postava na okraji záběru při otáčení kamery střídá `remove_child`/`add_child` (každé spustí `node_added`, kostra se znovu nastaví a sukně dostane `reset()`). | scripts/lide.gd:2748–2780 | opravit brzy | Hystereze jen `po_s` 1 s na odpojení, připojení je okamžité. Vliv NEOVĚŘENO. |
| `Planovac.krok_ruseni` a `rus_vse` přiřazují prvky fronty do typované proměnné `Node`. Když rodič uzel mezitím uvolní (bunka louky v `vypni`, `_exit_tree`), GDScript v ladicím sestavení hlásí „previously freed instance“ ještě před `is_instance_valid`. | scripts/planovac.gd:153, 168 | opravit brzy | Stačí `var n: Variant = …` / `for n: Variant in _rusit`, pak `is_instance_valid(n)`. |
| `diag._pod_krizem` na hlavním vlákně prochází všechny MultiMeshInstance3D ve stromu a až 60 000 instancí (`get_instance_transform`). Spustí se, když kamera 1 s stojí a je zapnutý panel, takže sám vyrobí zásek, který se zapíše do záseků měření. | scripts/diag.gd:208–255 | opravit brzy | Výjimka je jen `not lehky` (měřicí trasa). Při ručním měření s panelem se zásek míchá do čísel. Návrh: rozložit do více snímků, nebo spouštět jen na tlačítko. |
| `hladina()` volá pro každý dotaz kdekoli na mapě `_ryb_polomer` přes obrys (63 průsečíků úseček), bez rychlého testu vzdálenosti. Kůň se ptá každý krok fyziky. `od_vody` to samé dělá do 30 m od rybníka (i z louky při rozsevu). | scripts/svet.gd:13067, 13009, 2006–2018 | opravit brzy | Před výpočtem obrysu přidat `distance_to(stred) < polomer_m`. Cena na tabletu NEOVĚŘENO. |
| `ves_vjezd.png`: střechy blízkých domů (velký dům vlevo, stodola) jsou skoro černomodré, vzdálené střechy hnědé. | snímek | opravit brzy (ověřit) | Může to být protisvětlo. Ověřit snímkem z jiné strany. Kdyby šlo o materiál, souvisí to se změnou `_std_mokro` / `_daleko_textura`. |
| Výpusť: koryto pod výpustí je suchý štěrk bez vody, schody vedou na hráz přímo k (černé) hladině bez koruny hráze. | `vypust.png`, `vypust_vys.png` | opravit brzy (ověřit záměr) | Ověřit podle `voda.json rybnik_lhota vypust` a `test_smyslu`, jestli má odtok vést vodu. |
| Doubrava: zbytky vsi skoro nejsou vidět ve vysoké trávě, na obzoru `doubrava_vys.png` (~550,335) je světlý kvádr (možná LOD1 nebo obal). Díly LOD1 nemají konec viditelnosti (`visibility_range_end`), ves se kreslí do libovolné dálky a 55–60 m se překrývá s podrobnou sítí. | scripts/svet.gd `_ruiny_ves_dil` (LOD1 smyčka); lokace.json ruiny zanikla_ves | drobnost | `dosah_m` 60 / `lod1_od_m` 55. Hrubý stupeň bez konce je i u kostela (`Kostel_lod1`). |
| Natočení sedáků lavic v modelech (`sedaky_modelu`) je podle samotné poznámky v datech NEOVĚŘENO snímkem. Fallback výšky sedáku 0,45 je v kódu. | scripts/svet.gd:5982–6003; nabytek.json `_sedaky_modelu` | drobnost | Snímek sedící postavy na lavici u domu a u mlýna. |
| Nová čísla v kódu místo pravidel: `od_vody` +30.0, `_ryb_polomer` paprsek 200.0, sedák `r` 1.4, `+0.3`, 0.45, `pocasi._strechy` `p.y - 60.0`, `dest.gdshader` `- 0.05`, mlha `minf(…, 0.25)`, výchozí hodnoty `nastav_puchart(…20.0, 80.0)` a `_par(…).get(…, 0.6/40.0/0.5/14/60)` (zdvojují data). | svet.gd:13009, 2015, 5984, 6000; pocasi.gd:348; dest.gdshader:40; pad_vody.gd:121; louka.gd:2309; mereni_trasa.gd:174–270 | drobnost | Pravidlo „odstupy jen z pravidel, v kódu žádná vlastní čísla“. |
| `pocasi.strechy.polomer_m` se v kódu používá jako **počet buněk** (`n = 2r+1`, krok `krok_m`), ne jako metry. Funguje jen proto, že `krok_m` = 1,0. | scripts/pocasi.gd:326, 375 | drobnost | Při změně `krok_m` se poloměr v metrech změní. |
| Mokro dešťové pro StandardMaterial3D mění sdílené materiály modelů (krčma, kostel…), takže ztmavne a zaleskne se i vnitřek pod střechou (podlahy, interiér), protože mokro staveb se nerozlišuje podle krytí. | scripts/pocasi.gd:149–160, 177 | drobnost | Vnitřek dílů vyloučit podle `*_Interier_skupina`. |
| Varianty měřicí trasy `stin_filtr_1` a `dohled_kratsi` při vypnutí vracejí hodnotu z ProjectSettings (ne skutečnou předchozí) a přepisují dosahy, které hra mezitím změnila. | scripts/mereni_trasa.gd:175, 228–252 | drobnost | Ovlivní jen trasu. |

## Snímky `build/f1511`
- `kostel.png`: světlé ploché kvádry hřbitovní zídky a světlá loď z dálky (viz BLOKUJE 1). Tráva v lodi je záměr
  (bez střechy).
- `kostel_zed.png`: zblízka v pořádku (tmavé zdivo, brečťan, kříž). Nic nelevituje, v klenbě není tráva.
- `doubrava.png`, `doubrava_vys.png`: bez levitace a černých ploch. Ruina je ale v trávě skoro neviditelná a na
  obzoru je světlý kvádr.
- `vypust.png`, `vypust_vys.png`: **černá hladina** (BLOKUJE 2), suché koryto odtoku.
- `hraz_shora.png`: hladina v pořádku, lávka s pozerákem sedí, tráva po kraj vody bez rostlin ve vodě.
- `rybnik.png`: hladina tmavá, ale s kresbou. Tvar rybníka, lávka a břeh v pořádku.
- `ves_vjezd.png`: velmi tmavé střechy blízkých staveb (ověřit), jinak bez vad.

## Shrnutí
Vydání blokují **3** nálezy: (1) střední úroveň detailu bez barvy vrcholů, takže kostel je z dálky bílý
(znovu chyba ř. 151), (2) černá hladina rybníka v2 při nízkém pohledu, (3) chybějící balíky `z_kostel` a `z_ruiny_ves`
v manifestu (vydání je musí přidat). Ostatní nálezy jsou výkon v dešti a u postav (NEOVĚŘENO), heuristické mazání kolizí
a pár čísel v kódu.
