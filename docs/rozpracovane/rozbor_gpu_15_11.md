# Rozbor GPU a záseků z Míšina průchodu mapou (15. 11. večer, verze 0.999998)

Podklad jsou snímky `docs/screens/misa_15_11_vecer/01–15.jpg` (tablet Xiaomi Pad, Adreno, GL Compatibility, 3D 75 %,
sestavení 0.999998 152bfd4e, panel zapnutý), kód (`scripts/diag.gd`, `louka.gd`, `svet.gd`, `main.gd`, `trava_gpu.gd`),
`modely/tvrz.glb` (počty trojúhelníků jsem přečetl přímo z hlavičky glTF, Godot ani Blender jsem nespouštěl), `docs/mereni_verze.md`,
historie commitů od 9. 11. (GitHub API, místní klon je mělký) a zdrojový kód Godot 4.4.1 (gles3).

Značky: **NAMĚŘENO** = číslo z panelu nebo z tabulky trasy, **POTVRZENO V KÓDU** = přečteno v našem kódu nebo ve zdroji
Godotu, **PODEZŘENÍ** = hypotéza, kterou je třeba změřit, **ODHAD** = výpočet bez měření, **NEOVĚŘENO** = tvrzení z cizího zdroje,
které jsme si nepotvrdili.

---

## 0. Co je na snímcích (přepis panelu)

| sn. | místo (x, z) | FPS | snímek / nejdelší | kreslení CPU | swap/GPU | volání / prim. | troj. odhad (tráva · stromy · terén · ostatní) | poznámka |
|---|---|---|---|---|---|---|---|---|
| 01 | 822, 215 | 25 | 65 | 14,5 | 32,0 | 188 / 1,37 M | – | potok, louka |
| 02 | 469, 1197 | 24 | 115 (před kreslením 90,7) | 12,1–18,7 | 1,6–52,0 | 419–516 / 1,17–1,58 M | 0,16 · 0,09 · **0,63** · **0,41** | **uvnitř krčmy**, panel 2,1 ms |
| 03 | 533, 1189 | 17 | 58,8 | 14,2–19,7 | 2,9–26,4 | 334 / 1,36 M | 0,31 · 0,30 · 0,46 · 0,32 | les, **panel 11,6 ms** |
| 04 | 470, 1211 | 33 | 79 | 13,9 | 49,4 | 326 / 1,27 M | – | uvnitř (tmavý krov) |
| 05 | 464, 1193 | 25 | **1196** | 39,8 | **1108,7** | 343 / 1,21 M | – | události `louka 256 kB, louka_inst 3600`, stavba 1, vlákna 6 |
| 06 | −197, 988 | 26 | 61 | 13,1 | 26,8 | 330 / 1,49 M | – | `louka 229 kB, louka_inst 3251`, louka_bunek 1 |
| 07 | −200, 1007 | 18 | 85 | 22,8 | 41,3 | 347 / 1,55 M | – | hustší les, kapradí |
| 08–10 | 73, 947 | 22–24 | 76–81 | 12,7–20,2 | 38,6–55,9 | 376–651 / 1,45–1,87 M | – | výhled z kopce |
| 11 | −82, 913 | 16 | 112 | 20,6 | 60,4 | 397 / 1,71 M | – | dům u lesa |
| 12 | −188, 554 | 25 | 69 | **22,3** | 23,6 | **686 / 1,93 M** | – | **mezi skalami**, nejvíc volání i prim. ze všech snímků |
| 13 | −54, 412 | 25 | 91 | 16,1 | 55,0 | 284 / 1,38 M | – | louka, skály v pozadí |
| 14 | 1, 177 | 38 | 58 | 17,2 | 23,3 | 569 / 1,52 M | – | tábor u stanu |
| 15 | 3, 63 | 21 | 94 | 15,4 | 69,0 | 497 / 1,83 M | – | cesta, louka po obou stranách |

Paměť na všech snímcích: VRAM 899–917 MB (textury 619, buffery 288–299), nativní halda 1858–1863 MB (max 1880), PSS ~2,95 GB,
uzlů ~29,6 tis., objektů (Performance) ~61 tis.

---

## 1. Zjištění

### Z1 – Snímek čeká hlavně na GPU, ale „swap/GPU“ není čistý čas GPU
- **NAMĚŘENO:** swap/GPU 23–69 ms je největší položka skoro každého řádku záseku, kreslení CPU 12–23 ms, skripty 4–15 ms,
  fyzika 1–8 ms. Tablet čas GPU neměří (`GPU N/A`).
- **POTVRZENO V KÓDU (Godot):** `swap/GPU` je čekání v `eglSwapBuffers`. To zahrnuje frontu 2–3 snímků v ovladači a
  zarovnání na vsync, takže to není samotná práce GPU. Hra je tedy GPU-bound, ale ne čistě: na snímku 03 panel sám stál
  11,6 ms a FPS kleslo. To odpovídá Míšině „plný panel stojí skoro 10 FPS“ a už dřívějšímu měření (`mereni_verze.md`:
  „plný panel sám 7–10 ms“).
- **POTVRZENO V KÓDU (Godot 4.4.1, `servers/rendering/renderer_viewport.cpp` ř. 911–917):** „trojúhelníky / prim.“ v panelu
  (`RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME`) = **viditelný průchod + stínový průchod + plátno (UI)**. 1,2–1,9 M je
  tedy včetně stínu slunce.
- **POTVRZENO V KÓDU (Godot 4.4.1, `drivers/gles3/rasterizer_scene_gles3.h:775`):** v Compatibility vrací
  `get_pipeline_compilations()` vždy `0`. **„shadery +0“ na tabletu nic nedokazuje** (`predani`/`mereni_verze` to už má, platí
  to i pro špičku 1196 ms níže).

### Z2 – Co znamená odhad „troj. (odhad LOD0)“ a co padá do „ostatni“
**POTVRZENO V KÓDU** `scripts/diag.gd:1003–1110`:
- Průchod stromem uzlů po 2000 uzlech za snímek (`_troj_skupiny`, ř. 1056). Pro každý `GeometryInstance3D` se zkontroluje
  `visibility_range_begin/end` vůči středu AABB a šest rovin zorného jehlanu. Trojúhelníky se počítají jako trojúhelníky sítě
  × `visible_instance_count`/`instance_count`.
- **Nepočítá LOD** (horní odhad), **nepočítá okluzi**, **nerozliší stínový průchod**: uzly `SHADOWS_ONLY` (stínová tělesa
  korun `_stin`, `_Stin` domů) se počítají, jako by byly vidět. Kvůli tomu v lese „stromy“ nadsazuje.
- Skupina (`_skupina`, ř. 1020): podle **předpony jména uzlu nebo jeho rodiče, s rozlišením velkých a malých písmen**
  (`begins_with`). `teren` = předpony `Teren`, `Nadvori`, `zaplata`. Co je pod `Tvrz` nebo `Staticky_*`, je `stavby`, pod
  `Predmety` je `predmety`. **Všechno ostatní je `ostatni`.**

**Co je v „ostatni“ (POTVRZENO V KÓDU podle jmen uzlů, velikost tam, kde jde zjistit):**

| kandidát | kde vzniká | jméno | troj. | proč „ostatni“ |
|---|---|---|---|---|
| **impostory obzoru** | `svet.gd:4570 _obzor_les` → `_impostory(..., OBZ_BUNKA 1024, 2500.0, "obzor")` ř. 4649 | `obzor_<druh>_<bx>_<bz>` | **76 550 stromů × 2 troj. = 153 tis.** (NAMĚŘENO v PC logu `build/beh/testy_15_11a1_godot.log`: „obzor: 76550“) | předpona `obzor` není v SKUPINY (`impostor` ano, `obzor` ne) |
| díly staveb | `_rybnik_dil`, `_mlyn_dil`, `_vetrak_dil`, `_kovarna_dil`, `_krcma_dil`, `_kostel_dil` (`svet.gd:9363, 10143, 10232, 10271, 10339, 10689`) | `Rybnik_dil`, `Mlyn_dil`, … `Krcma_dil` | krčma 172 tis., kovárna 65 tis. (`mereni_verze` 0.999997) + mlýn, rybník | rodič není `Tvrz` ani `Staticky_` |
| pšenice, jabloně | rozsev `svet.gd` z `modely/svet.json rostliny` | `psenice_0_*`, `psenice_2_0_*`, `jablon_*` | 24 591 + 18 875 instancí pšenice (dosah 45 m z `druhy.json`) | předpony nejsou v SKUPINY |
| postavy, koně, zvířata, tělo hráče | `lide.gd`, `kun.gd`, `zvirata.gd`, `telo.gd` | různé | ~7,5 tis. na postavu (`mereni_verze` 0.99993), do 70 m | nejsou v SKUPINY |
| řeka Waterways, hladiny | `svet._reka`, `nadrz.gd:149` | `Rybnik_hladina`, uzly řeky | – | `Rybnik_*` není ve `voda` |
| tráva GPU (prototyp) | `trava_gpu.gd:108` | bez jména pod uzlem trávy GPU | 3 prstence × 4 čtvrtiny | jen když je v Nastavení zapnutá (výchozí `false`, `trava_gpu.json`) – **NEOVĚŘENO**, jestli ji Míša nemá zapnutou |
| kopie předehřátí | `main.gd:910–940` (`Predehrati_dohrev`) | bez jména | celá síť nové kombinace (i 163 tis. terénu) na 3 snímky | jen přechodně, `extra_cull_margin 16384` |

Ze snímků: „ostatni“ 0,32 M i v lese daleko od staveb (03) a 0,41 M v krčmě (02). Stálá složka, která je vidět odevšad, je
**obzor ~0,15 M**. Zbytek dávají díly (krčma, když jsem u ní), pšenice a postavy. **PODEZŘENÍ:** obzor + díly + postavy
vysvětlí „ostatni“ beze zbytku. Ověřit to jde jen výpisem (plán K1).

**Je kresleno něco, co hráč nevidí? (Míša: „pořád mám pocit, že kreslíme něco, co nemáme“)**
1. **Terén se kreslí celý, vždy, bez LOD (POTVRZENO V KÓDU, největší položka, viz Z3).** Síť terénu o 1,4 km vzadu i za zády
   prochází vertex shaderem každý snímek (ořez pohledem je jen po celých instancích).
2. **Celý svět venku, když jsem uvnitř krčmy (NAMĚŘENO + POTVRZENO V KÓDU):** snímek 02 v krčmě má 1,17–1,58 M prim.,
   terén 0,63 M, ostatní 0,41 M, tráva 0,16 M, swap/GPU 45–52 ms. Portály (`portaly.gd`) zná jen hostinec a tvrz, krčma ne.
   `louka.vnitrek` (tráva jen do 20 m) se tedy v krčmě nezapne. Okluzor terénu (`svet.gd:8756`) leží 0,8 m pod terénem a
   zevnitř nic nezakryje. Krabice okluzorů jsou jen u domů vsi (`_domy`), u krčmy ani kovárny ne (`OKL_DOMY` vypnuto).
3. **Impostory obzoru do 2500 m bez `visibility_range` (POTVRZENO V KÓDU `svet.gd:4509–4560`):** buňky 1024 m. Celá buňka
   projde ořezem, když je kousek v záběru, a mizení dělá shader (`fade_do`), takže vrcholy a fragmenty alfa-testu se počítají
   i tam, kde nakonec nic nezbude.
4. **Stínová tělesa korun a domů** (`svet.gd:4447 _stin_koruny_mmi`, `svet.gd:7013 _Stin`) jsou `SHADOWS_ONLY`. To je
   správně, jen je panel počítá jako viditelné.
5. **Skryté uzly:** `Reka_voda`, `Skaly`, `Teren_cesta_kamen` mají `visible = false` (`svet.gd:727–737`) a nekreslí se.
   Neviditelný materiál, který by se kreslil, jsem nenašel. **Dvě úrovně LOD najednou:** stromy `_tvar`/impostor a skály
   LOD0/1/2 mají rozsahy navazující s okrajem (`visibility_range_*_margin`). Prolínání je vypnuté (`modely.json
   prolinani_dosahu false`), takže v okraji se kreslí jen jedna úroveň. Na sítích pod terénem jsou jen lemy (`_sukne`,
   Blender skirt 5–8 m) a ty jsou levné.
6. **Diag sám:** `_pod_krizem` (`diag.gd:208`) volá `get_instance_transform` na MultiMeshích s bufferem nastaveným přes
   `mm.buffer` (kupy `louka.gd:1316`, rostliny `svet.gd:3647`). **POTVRZENO VE ZDROJI Godot 4.4.1** (`mesh_storage.cpp
   _multimesh_make_local`): když je `buffer_set`, Godot přečte buffer z GPU (`Utilities::buffer_get_data` →
   `glMapBufferRange(GL_MAP_READ_BIT)`). Na OpenGL ES to je úplná synchronizace CPU s GPU a MultiMesh si pak drží kopii v RAM
   navždy. Běží to jen při stojící kameře 1× (od 15. 11.), ale každé měření pod křížem = zásek a paměť navíc.

### Z3 – Terén: 547 tis. trojúhelníků, jeden kus na pásmo, bez LOD
**NAMĚŘENO (hlavička `modely/tvrz.glb`, export 15. 11. 17:36):**

| síť | troj. | rozsah (m) | krok |
|---|---|---|---|
| Teren_toky | **163 440** | −250…805 × −225…990 | jemný terén u toků a rybníků (`kraj._teren_u_vody`) |
| Teren_okoli | 133 368 | −250…900 × −250…1350 | 5 m |
| Teren_reka | 99 144 | 150…905 × 138…1345 | 1 m pás řeky |
| Teren_ves | 47 460 | 310…630 × 670…990 | 2 m |
| Teren_obzor | 40 032 | −1500…2000 × −1500…2600 | 25 m |
| Teren | 29 928 | −60…60 × −55…70 | 1 m (tvrz) |
| Teren_cesta | 17 838 | cesty | – |
| Teren_most | 13 440 | 195…275 × 560…640 | 1 m |
| **celkem Teren\*** | **547 160** | | (+ `_sukne` z `koryto.gd:523`, `Teren_zaplata`, `Teren_lom_stena`) |

- **POTVRZENO V KÓDU:** `_rozdel_site` (`svet.gd:799–830`) terén **nedělí** („teren se nedeli (0.62)“). Každé pásmo je jedna
  MeshInstance s AABB přes stovky metrů, takže ořez pohledem ji nikdy nevyřadí. Import má `generate_lods=true`
  (`tvrz.glb.import`), ale hra sítě terénu za běhu přepisuje (koryto, nádrže, terasy, zámek terénu: `svet.gd:580` „každá
  úprava terénu mění mi.mesh“). Nová ArrayMesh pak LOD nemá, a i kdyby měla, u jedné obří instance je kamera uvnitř AABB, takže
  vždy LOD0.
- **NAMĚŘENO (panel):** odhad „teren“ 0,46–0,63 M, tedy prakticky všech 547 tis. v každém záběru. Stín terén nevrhá
  (`cast_shadow OFF`, `svet.gd:746`), takže se kreslí jednou, ne dvakrát. Na dlaždicové GPU (Adreno) ale vertex shader běží
  ve dvou průchodech (binning + render) – **NEOVĚŘENO** pro náš ovladač.
- Duplicitu pásem jsem nenašel: `kraj.py:2504` vynechává vnitřní obdélníky (obzor bez ACT, okolí bez NEAR/VRECT/BRECT a pásu
  řeky, buňky u vody nahrazuje Teren_toky).
- **ODHAD úspory:** dlaždice 128 m s ořezem pohledem (zorný úhel cca 1/4 kruhu) + hrubší úroveň za ~200 m → kresleno
  ~100–150 tis. místo 547 tis. (−0,4 M troj. na snímek, tedy víc než všechna tráva podle odhadu panelu).

### Z4 – Špička 1196 ms při „louka 256 kB“: nahrání samo to není
**NAMĚŘENO (snímek 05):** 1196 ms u (464, 1193): swap/GPU 1108,7, kreslení CPU 39,8, `_process` 27, fyzika 13. Události
`louka 256 kB, louka_inst 3600, louka_bunek 0`, fronta louky 41, vlákna 6, stavba 1, louka hotové 1. Snímek 06: 61 ms při
`louka 229 kB, louka_inst 3251, louka_bunek 1`.

**POTVRZENO V KÓDU (louka.gd):**
- Každá buňka a úroveň = **nový `MultiMesh.new()` + `instance_count = n`** (`louka.gd:1194–1198`). Ve zdroji Godotu
  (`_multimesh_allocate_data`) to je `glGenBuffers` + `glBufferData(…, nullptr)`, tedy **nová alokace GPU bufferu** při
  každé stavbě a přestavbě buňky. Starý se uvolní (`Planovac.zrus`). Alokace se točí dokola.
- Plnění po dávkách `PLNIT 400` přes `set_instance_transform/custom_data` (`louka.gd:1154–1175`). `buffer_set` je po alokaci
  `false`, takže zpětné čtení z GPU tu **není** (ověřeno ve zdroji). Nahraje se `glBufferSubData` po oblastech 512 instancí
  při kreslení (`_update_dirty_multimeshes`).
- Rozpočet `rozpocty.json louka_nahravani.nahrani_b_snimek = 262 144` (256 kB). **Špička měla přesně tento strop** (256 kB,
  3600 instancí × 64 B ≈ 230 kB + zaokrouhlení oblastí), takže rozpočet fungoval. Rozpočet času `snimek.louka_us 4000`,
  `rozpocet_us_tablet 6000`.
- `_viditelne` zvyšuje `visible_instance_count` i **u buněk, které se právě kreslí** (`louka.gd:768–797`). Nahrání do bufferu,
  který GPU ve frontě 2–3 snímků ještě čte.

**Proč 256 kB nemůže trvat 1,1 s (ODHAD):** i pomalá sběrnice mobilu má jednotky GB/s, takže 256 kB je řádově 0,1 ms.
Čekání na buffer v užívání (implicitní synchronizace) stojí nejvýš frontu snímků, tedy ~100 ms, ne 1 s.
**Podezření v pořadí pravděpodobnosti:**
1. **PODEZŘENÍ – sestavení shaderu/varianty při prvním kreslení** (Compatibility sestavuje program až při kreslení; čítač
   v panelu je vždy 0, viz Z1). Stejný vzor: 1. průjezd 0,5–3 s, 2. průjezd nic (`mereni_verze` 0.999997 a 0.999998).
2. **PODEZŘENÍ – tlak na paměť:** nativní halda 1858/1880 MB (98 % maxima) a PSS 2,95 GB na všech snímcích. Alokace nového
   GL bufferu nebo textury blízko stropu může v ovladači nebo v jádře spustit uvolňování paměti. Čas pak „visí“ v swapu a
   zpomalí se i fyzika a skripty (13 a 27 ms místo 4 a 11 ms na snímku 05).
3. **PODEZŘENÍ – vytížené procesory:** 6 vláken louky (`VLAKEN = clamp(jader−2, 3, 6)`, `louka.gd:39`) staví buňky současně
   s hlavním vláknem a s vláknem ovladače GL. Na snímku 05 „vlákna 6“. Proti tomu: vlákna 6 jsou i na běžných snímcích.
4. **PODEZŘENÍ (slabé) – implicitní synchronizace** při nahrávání do bufferu v užívání (výš).

**Rešerše (zdroje):**
- Zdroj Godot 4.4.1 `drivers/gles3/storage/mesh_storage.cpp` (`_multimesh_allocate_data`, `_multimesh_make_local`,
  `_multimesh_set_buffer` = `glBufferData` celého bufferu, `_update_dirty_multimeshes`: nad 32 změněnými oblastmi nebo nad
  polovinou kreslených oblastí nahraje celý viditelný rozsah jedním `glBufferSubData`) a `drivers/gles3/storage/utilities.cpp`
  (`buffer_get_data` = `glMapBufferRange` READ) – **POTVRZENO** čtením zdroje
  (https://github.com/godotengine/godot/blob/4.4.1-stable/drivers/gles3/storage/mesh_storage.cpp).
- Qualcomm developer fórum: dlaždicové GPU/ovladače Adreno mají potíže s často aktualizovanými VBO přes
  `glBufferSubData` i `glBufferData`. Doporučený obchvat je **kruh bufferů** (ovladač s bufferem skončí, než se znovu použije)
  – https://developer.qualcomm.com/comment/7777, https://developer.qualcomm.com/comment/6594 – **NEOVĚŘENO** (staré příspěvky,
  jiné ovladače).
- OpenGL wiki „Buffer Object Streaming“ (orphaning `glBufferData(NULL)`, kruh bufferů, `glMapBufferRange` s
  `UNSYNCHRONIZED`) – https://www.khronos.org/opengl/wiki/Buffer_Object_Streaming. Mozilla bug 1598380: orphaning přes
  `glBufferData` na Adreno nefunguje spolehlivě – https://bugzilla.mozilla.org/show_bug.cgi?id=1598380 – **NEOVĚŘENO** na našem
  tabletu.
- Khronos fórum: `glBufferData` způsobuje sekání při načítání LOD terénu
  (https://community.khronos.org/t/opengl-glbufferdata-cause-stuttering-while-loading-terrain-lod/76292) – stejný vzor, jako
  máme my – **NEOVĚŘENO**.
- Dokumentace Godot MultiMesh: v Compatibility se barva a custom data balí do 16 bitů (half)
  (https://docs.godotengine.org/en/4.3/classes/class_multimesh.html). Náš model bajtů s tím počítá (`gles3_floatu_barva_custom 4`).

**Návrh opravy louky (pořadí):**
1. Nejdřív rozlišit podezření (K2): řádek záseku doplnit o „nové GL buffery v tomto snímku“ (počet `MultiMesh.new` + součet
   bajtů z `louka`, `kupy`, `rostliny`), „první kreslení kombinace“ (klíč z `_pred_videno` – jestli v tom snímku přibyla) a
   o haldu a PSS v tom snímku.
2. **Pevná zásoba MultiMeshů (kruh slotů)**: `rozpocty.json louka_sloty {"pocet": STROP, "kapacita_instanci": [vrstva 0…4]}`.
   Buňka si vezme volný slot, přepíše jeho data (`set_instance_*`, `visible_instance_count`) a při uvolnění slot vrátí.
   Žádné `MultiMesh.new()` a `glBufferData` za hry. Slot uvolněný v tomto snímku se použije až za N snímků (`odklad_snimku`,
   kvůli frontě GPU, rada Qualcomm).
3. **Přestavba úrovně bez nové alokace:** úrovně 0/1/2 (`UROVEN_OD 0/35/65`) mají jen jiný počet trsů seřazených podle hashe.
   Při přiblížení stačí doplnit chybějící trsy na konec slotu (data z vlákna) a zvýšit `visible_instance_count`. Celou buňku
   tedy znovu neposílat.
4. Nahrávat jen do **skrytých** slotů. U viditelných buněk měnit `visible_instance_count` jen směrem dolů (to nic nenahrává,
   potvrzeno ve zdroji). Zvýšení u viditelné buňky = přestavba do nového slotu a výměna.
5. Rychlý test bez kódu: `nahrani_b_snimek` 256 kB → 64 kB (jen data). Pokud špičky 1 s zůstanou, nahrání není příčina.

### Z5 – „Mezi skalami to dřív jelo bez záseků, dnes ne“
- **NAMĚŘENO (měřicí trasa, úsek skály, p50/p95 ms):** 0.99995 (3D 100 %) 44/61 → 0.99996 26/55 → 0.99997 p95 31 → 0.999995
  27 → 0.999996 23 (výrazně v šumu) → 0.999997 23 a 29 → **0.999998 27 ráno, 32 večer** (vše). Na trase je to v šumu ±5 ms,
  žádná skoková regrese. Úsek trasy ale nemusí být to místo, kde Míša chodila.
- **NAMĚŘENO (snímek 12, mezi skalami u (−188, 554)):** **686 volání a 1,93 M prim. jsou nejvíc ze všech 15 snímků**,
  kreslení CPU 22,3 ms (jinde 12–18). Tady je cena hlavně v počtu kreslených objektů, ne v GPU (swap 23,6).
- **Změny od 0.99997 (10. 11.), které se týkají skal, stromů u skal nebo podrostu** (GitHub, `scripts/svet.gd`, jen to, co je
  v sestavení 0.999998 = commit f97a738):
  - `9685aeb` 10. 11. – koruny: jádro bez alfy + **stínová tělesa korun** (`_stin_koruny_mmi`): nový MultiMesh `_stin` na
    každou buňku stromů do 40 m, tedy víc volání ve stínovém průchodu. Mezi skalami je hustý jehličnatý les (snímek 12).
  - `225738d` 10. 11. – **řídký podrost v lese (kapradí, byliny, trsy)** a lesní půda podle zápoje: víc buněk rostlin a
    volání v lese.
  - `02e1129` + `a4d04e9` 14. 11. – dosednutí rostlin a balvanů na hotový terén v datech (jiné polohy, ne počty – výkon by se
    měnit neměl).
  - `c1614be`, `dbe46a2` 15. 11. – skály smazané pěšinou berou borovici, `pasma.dosednuti.na_skale` (polohy, ne počty).
  - `c4020a2` 13. 11. – drobné a vnitřní díly tvrze do 200 m (víc kreslení u tvrze, u skal ne).
  - `0.999998`: kaskáda potoka – víc balvanů v korytu a na hranách stupňů (`voda.json schody`). Pokud skály Míšina průchodu
    leží u potoka z kopce, je to přímá změna „tam“.
- **Další podezřelí bez commitu:** teplo (Míša to odmítá jako vysvětlení – nepoužívat), plný panel (11,6 ms na snímku 03),
  `_pod_krizem` (Z2 bod 6) při zastavení mezi skalami.
- **Závěr:** podezření (ne příčina) jsou stínová tělesa korun a podrost (oba 10. 11.) a balvany kaskády (0.999998).
  Rozhodne izolovaný test: úsek trasy přesně u (−188, 554) s variantami bez podrostu, bez stínových těles a bez balvanů
  kaskády (K6).

### Z6 – Tráva: kolik stojí, jak daleko sahá, les místo trávy
**Kolik tráva stojí (NAMĚŘENO dřív, `mereni_verze.md`):**
- 0.9993: bez louky 37 → 59 FPS (≈ 27 → 17 ms, −10 ms).
- 0.9995: bez trávy −3 až −6 ms na snímek. **Tráva do 50 m (místo 80) beze změny** (cena je zblízka).
- 0.9997: bez trávy −1 až −15 ms (les −15).
- 0.99996: les bez trávy p50 38 → 29 (−9 ms), p95 85 → 65.
- **ODHAD podílu:** tráva je 3–15 ms z 25–40 ms snímku, tedy **~15–35 % času**, nejvíc v řídkém lese a na louce.
  Panelový odhad 0,16–0,31 M troj. je jen vrcholová část, cena je hlavně ve vyplňování (alfa karet zblízka, překryv).

**Současný dosah (POTVRZENO V KÓDU):**
- `modely.json trava_dosah_m.plna [PC 110, tablet 80]`. `louka.gd:25 HUST_OD 20` (do 20 m všechny trsy), `ZANIK[0] [20, 110]`
  (ve vzdálenosti 80 m zbývá podle smoothstep ještě ~25 % trsů), `UROVEN_OD [0, 35, 65]`, `UROVEN_PRO [0, 20, 50]`.
- **Za trávou ještě kupy** (`louka.gd:46 KUPY`): impostor trávy 45–280 m (buňka 64 m) a 240–650 m (buňka 128 m). Kreslí se
  tedy „tráva“ do 650 m.
- `HUST_OD`, `ZANIK`, `UROVEN_OD`, `KUPY` jsou **čísla v kódu** (porušení pravidla „odstupy jen z dat“) – přesunout do
  `rozpocty.json louka_dosahy` s hodnotami pro PC a tablet.

**ODHAD počtu trsů při plné hustotě louky (rozestup 0,36 m = 7,7 trsu/m², před `hustota` a maskou):**

| plná do / řídne do / konec | trsů | z toho do 15 m |
|---|---|---|
| 20 / 110 / 80 (dnes tablet) | ~100 tis. | 5,5 tis. |
| 20 / 80 / 80 | ~65 tis. | 5,5 tis. |
| 15 / 50 / 50 | ~27 tis. | 5,5 tis. |
| 15 / 45 / 45 (návrh Míši, KCD) | ~23 tis. | 5,5 tis. |

Zkrácení na 15/45 ubere ~75 % trsů, ale 0.9995 ukázala, že zkrácení dosahu 80 → 50 m **výkon nezměnilo**. Očekávání:
úspora hlavně ve vrcholech a v alokacích buněk (méně buněk ve vlákně a v nahrávání, menší STROP a paměť), ve vyplňování
málo. Snížení `HUST_OD` 20 → 15 ubere ~43 % trsů s plnou hustotou (pás 15–20 m), a ten je na obrazovce ještě velký. To je
pravděpodobnější úspora GPU. **NEOVĚŘENO** – musí změřit trasa.

**Vzhled (Míše se louka líbí):** v dálce má trávu nahradit barva terénu louky (`zem.gdshader`, textura louky už je pod
trsy). Před i po pořídit snímek z očí hráče na stejném místě (`--write-movie`, místa 13 a 15: (−54, 412) pohled Z,
(3, 63) pohled J) a porovnat. Pro přechod barvy použít tentýž hash/zánik jako shader trsů, žádnou novou hranu.

**Les: tráva vs. houština (POTVRZENO V KÓDU + data):**
- `les_podrost.json trava`: v plném zápoji násobek trávy `v_zapoji 0,015`, tedy pod prahem, takže v zapojeném lese louka nic
  nesází. Tráva roste tam, kde je **zápoj malý**. Míša má pravdu: naše lesy jsou řídké (zápoj okolí `okoli_od 0,55 –
  okoli_do 0,9`), takže v „lese“ je skoro plná louka. NAMĚŘENO: snímek 03 (les) tráva 0,31 M (nejvíc ze snímků) a stromy
  0,30 M.
- **ODHAD úspory náhradou trávy houštinou:** v řídkém lese je dnes louka ~plná (až ~100 tis. trsů v kruhu 80 m na tabletu,
  krát hustota a maska). Keře jako MultiMesh rostlin (`rostliny`, dosah ~100 m, 1 instance na ~10–30 m²) = stovky až tisíce
  instancí. Ty mají ale víc trojúhelníků na kus a alfa listí, takže úspora vrcholů ano, vyplňování podobné.
  Bezpečná úspora je **hustší les** (zápoj ↑ → tráva pod korunami pryč): naměřeno 0.99996 „les bez trávy“ −9 ms p50.
  Napojení na `docs/rozpracovane/sceny_kcd_15_11.md` (krok 3 houština s okluzorovým jádrem, krok 4 les jako hmota): houština
  s jádrem bez alfy navíc zakryje to, co je za ní (early-Z jako jádro korun).

### Z7 – Přepínání a periodická práce (Míša: „pořád se něco přepíná podle dosahu“)

| systém | jak často | čeho se dotýká | cena (NAMĚŘENO / ODHAD) | mlácení nebo zbytečná práce |
|---|---|---|---|---|
| **visibility_range a ořez** (Godot `RendererSceneCull`) | každý snímek | každá instance v zorném jehlanu: test rozsahu (vzdálenost ke středu AABB) + roviny | ODHAD: desítky tisíc instancí × ~0,1–0,3 µs = 1–5 ms z „kreslení CPU“ 12–23 ms (NAMĚŘENO celkem). Kresleno 4,9–5,2 tis. objektů (panel „objekty“ v 2. řádku = viditelné + stín) | **ano:** stromy a skály jsou MultiMesh **druh × buňka 24 m po celé mapě** (`svet.gd:14482–14492`), každá vlastní `visibility_range`. Stínová tělesa a `_tvar` jsou další kopie. Ořez prochází i tisíce buněk za dohledem 120 m |
| **automatický LOD sítí** (`mesh_lod_threshold 10`) | každý snímek, každý povrch | výběr indexového bufferu | ODHAD: zanedbatelné | ne |
| **louka – kruh buněk** (`louka.gd:544–700`) | každý snímek: hledání chybějící buňky v (2·5+1)² = 121 buňkách + projití `_bunky`; `_viditelne` každá buňka 1×/4 snímky; uvolnění za `_dosah + UVOLNIT 24` | vlákna (6), nové MultiMeshe, nahrání do GPU | NAMĚŘENO: skript louky až 4 ms (snímek 06 „louka 4“), nahrání až 256 kB/snímek, fronta 29–55 buněk | **ano:** přestavba úrovně při přiblížení = celá buňka znovu (nová alokace). Úroveň se volí podle místa za `PREDSTIH_S 8 s` (u koně 80 m dopředu). Při otáčení se cíl přesouvá a staví se buňky, které pak zůstanou za zády. NAMĚŘENO 0.999998: série 0,5–1,4 s „při otáčení koně“ (při 2. trase se neopakovala). Hystereze ztenčení 20 m je, pro zvýšení úrovně ne |
| **louka – počty kreslených trsů** (`_vid_nastav`) | každá buňka 1×/4 snímky | `visible_instance_count` po kvantech 256, hystereze 1 kvantum | ODHAD < 0,5 ms | malá: hystereze 1 kvantum (256 trsů) je v pásmu zániku úzká |
| **rostliny – buňky 24 m** (`svet.gd:3599–3700`) | každý snímek, nejvýš `ROST_ZA_SNIMEK`, dosah `rostliny_dosah_m 115`, uvolnění `+30` | uzly MMI z dat (`mm.buffer` = celý `glBufferData`) | NAMĚŘENO: rostliny 87–140 buněk z 3150; `plán` 0,2–0,4 ms (max 2,3) | uzly se ruší po 4 za snímek (`ruseni_za_snimek`); hystereze 30 m je dobrá |
| **kolize – dávky** (`svet.gd:3434–3590`) | změna buňky 32 m → dávka 20 tvarů za snimek | `StaticBody3D` + tvary | NAMĚŘENO: dávka 0,5–2,6 ms, aktivních 12–15 z 1711 | ne (hystereze 2 buňky) |
| **kupy** (`louka.gd:672–700, 1915–1945`) | každý 3. snímek jedno pásmo; 1 díl/snímek | nové MultiMeshe `mm.buffer` (celý buffer) | ODHAD < 0,5 ms CPU; kupy ve vláknech 0–3 | alokace jako u louky (bez kruhu slotů) |
| **postavy daleko** (`lide.gd:2584–2680`) | každý snímek: animace do 45 m plně, dál 10 fps, dosah 70 m | Skeleton, AnimationTree | NAMĚŘENO: „lide“ 1,7–3,4 ms skript | změny činnosti 1/snímek (0.999996) – v pořádku |
| **stíny – zapnutí podle dosahu** | statické: `cast_shadow` se nastaví při stavbě; slunce na tabletu ortho 40 m (`main.gd:2174–2178`) | stínová mapa 2048 | NAMĚŘENO dřív: stín slunce je v lese největší jednotlivá cena (0.99996 les p95 85 → 42) | stínová tělesa korun do 40 m = celé buňky 24 m se zapínají podle dosahu |
| **automatická kvalita** (`kvalita.gd:161`) | každý snímek měří, mění po oknech | stíny, efekty, dohled | NAMĚŘENO dřív: uplatnění kroku 37–60 ms (0.99996) | výchozí ruční. V auto hystereze (`nahoru_s` se zdvojuje) |
| **světla a částice** (`life.gd:585–640`) | `_castice_lod` 1× za `kontrola_s`; světla den/noc při změně | `process_mode` částic, `visible` světel | ODHAD < 0,1 ms; panel „světel 0–1“ | `life.gd:599` prochází všechny děti uzlu (find přes děti) – malé |
| **předehřátí za hry** (`main.gd:943–975`) | při každém novém uzlu geometrie (`_pred_novy_uzel`) | klíč kombinace, kopie na 3 snímky | ODHAD: klíč = `str(pole)` pro každý nový uzel louky a rostlin – desítky za snímek | **ano:** každá nová buňka louky a rostlin projde stavbou klíče (řetězec), i když je kombinace známá |
| **diag panel** | plný: průchod 2000 uzlů + 1500 instancí za snimek (`diag.gd:1056`), text 2×/s | celý strom 29,6 tis. uzlů | **NAMĚŘENO: 2,1–11,6 ms** („panel“ v řádku 3) | **ano:** neustále prochází celý strom, `_pod_krizem` `find_children("*", "MultiMeshInstance3D")` přes celý strom |

**Hledání přes celý strom za hry** (`find_children`/`get_nodes_in_group`, 165 výskytů v `scripts/`): většinou při stavbě.
Za hry jsem našel diag (výš). Celou inventuru výskytů v `_process` udělat v K7 – **NEOVĚŘENO**, že jinde nic není.

**Návrh sloučení (data, ne čísla v kódu):**
- Stromy a skály: buňka 24 m → **větší buňky pro statické druhy** (`rozpocty.json bunky_statickych {"strom_m": 48, "skala_m": 96}`)
  a **jedna úroveň viditelnosti na buňku** (uzel `Node3D` s `visibility_range` na rodiči a `visibility_parent` u dětí – LOD
  stromu jako skupina, ne každá MMI zvlášť). Méně instancí s vlastním rozsahem znamená méně práce ořezu a méně volání.
- Impostory obzoru: buňka 1024 → 256 m (`rozpocty.json obzor {"bunka_m": 256}`) – ořez za zády ubere ~polovinu.
  Za 2500 m `visibility_range_end`, ne jen shader.
- Louka: kruh slotů (Z4) – žádné vytváření a rušení uzlů za hry, počet uzlů stálý.

---

## 2. Plán oprav (seřazeno podle očekávaného přínosu a rizika)

Každý krok: záznam v datech → měření (varianta měřicí trasy nebo panel) → návrat. Podle CLAUDE.md nejdřív izolovaný test,
pak oprava. Hypotézu nevydávat za opravu.

| # | krok | záznam v datech | měření | návrat |
|---|---|---|---|---|
| **K1** | **Diag: co je „ostatni“ a co jde do stínu** – v plném panelu 10 největších uzlů „ostatni“ (cesta, troj.), rozdělit prim. na viditelné / stín (`viewport.get_render_info(TYPE_VISIBLE/TYPE_SHADOW)`), doplnit předpony `obzor`, `psenice`, `jablon`, `*_dil` do SKUPINY | `pravidla/svet/kontroly.json diag_skupiny` (předpony skupin z dat, ne v kódu) | snímek panelu na místech 02, 03, 12 | smazat záznam = dnešní chování |
| **K2** | **Řádek záseku rozliší příčinu 1 s špiček**: nové GL buffery v snímku (počet, bajty), přibylá kombinace předehřátí, halda/PSS v tom snímku | `rozpocty.json diag_zasek {"buffery": true, "kombinace": true}` | volná hra + trasa 1. průjezd po instalaci | vypnout příznaky |
| **K3** | **Varianty trasy na izolaci GPU** (bez nové verze kódu světa): `bez_obzoru` (Teren_obzor + impostory obzoru skryté), `teren_jen_blizko` (skryje Teren_obzor a Teren_reka/Teren_toky dál než 300 m – jen měření), `louka_15_45`, `louka_hust_15`, `bez_podrostu_lesa`, `bez_stinovych_teles` | `mereni_trasa.json varianty` | měřicí trasa p50/p95 a troj. na úseku | odebrat varianty |
| **K4** | **Terén na dlaždice s LOD (první oprava – viz níže)** | `generovani.json teren_dlazdice {"krok_m": 128, "urovne": [[0, 180, "jemna"], [160, 900, "hruba"]], "okraj_m": 20}` | trasa vše vs. 0.999998; panel „teren“ ≤ 0,2 M | `krok_m: 0` = dnešní celé sítě |
| **K5** | Louka: kruh slotů MultiMeshů, přestavba úrovně doplněním, nahrávání jen do skrytých | `rozpocty.json louka_sloty`, `louka_nahravani.nahrani_b_snimek` (první zkouška 64 kB) | test `louka_nahravani`, trasa kun-louka-otoc, řádky záseků (K2) | `louka_sloty.pocet: 0` = dnešní `MultiMesh.new` |
| **K6** | Izolace „mezi skalami“ | `mereni_trasa.json` úsek `skaly_lom` u (−188, 554) s variantami bez podrostu / bez stínových těles / bez balvanů kaskády | 3 varianty, p50/p95, volání | odebrat úsek |
| **K7** | Dosahy louky do dat + tablet 15/45 (návrh Míši), barva terénu místo trsů | `rozpocty.json louka_dosahy {"hust_od": [20, 15], "zanik_trsy": [[20,110],[15,45]], "uroven_od": [...], "kupy": [...]}`, `modely.json trava_dosah_m.plna [110, 45]` | varianta `louka_15_45` z K3 + snímky před/po z místa 13 a 15 | vrátit čísla v datech |
| **K8** | Okluzory krčmy a kovárny + portály krčmy (vnitřek: tráva do 20 m, svět za zdmi ne) | `lokace.json krcma_l.okluzor`, `pasma.budova.okluzor_*` (už existuje), `portaly.json krcma` | snímek 02 znovu: prim. uvnitř krčmy | smazat záznam |
| **K9** | Impostory obzoru: buňka 256 m, `visibility_range_end 2500` | `rozpocty.json obzor {"bunka_m": 256, "do_m": 2500}` | panel „ostatni“, trasa (výhled z kopce 08–10) | `bunka_m: 1024` |
| **K10** | Statické rostliny ve větších buňkách, LOD stromu jako skupina (`visibility_parent`) | `rozpocty.json bunky_statickych` | kreslení CPU a počet objektů v panelu, trasa les | velikosti buněk zpět |
| **K11** | Les hustší, houština místo trávy (`sceny_kcd_15_11.md` krok 3 a 4) | `les_podrost.json trava.okoli_od/do`, nový záznam houštiny v `sceny.json` | varianta `les_bez_travy` (už je) proti nové | vrátit prahy |
| **K12** | Diag `_pod_krizem` bez zpětného čtení z GPU (poloha jen z dat buněk, ne z MultiMeshe) | – (diag) | snímek panelu při stání | – |

### První navrhovaná oprava: K4 terén na dlaždice (po rychlém K3 `teren_jen_blizko`)
- **Proč:** terén je potvrzeně kreslen celý a stále (547 tis. troj., odhad panelu 0,46–0,63 M = největší skupina na všech
  snímcích), a nikdo ho ještě nezkoušel ořezávat. Tráva už měřená byla (dosah nepomohl) a stromy a stíny už ořezané jsou.
- **Jak bez záplat:** dlaždice stavět v Blenderu (`kraj.py tiles`) jako záznam `generovani.json teren_dlazdice`. Každá
  dlaždice je samostatný objekt `Teren_<pásmo>_<i>_<j>`, takže všechny úpravy terénu ve hře, které hledají `Teren*` a počítají
  ze světových souřadnic (koryto, nádrže, terasa, zámek), platí beze změny a na hranách dlaždic vyjdou stejně (stejná funkce
  polohy, žádné praskliny). Kolize zůstává z dnešních sítí (staví se před dělením, jako `_rozdel_site`). Hrubá úroveň za
  ~160–180 m = dnešní Teren_obzor 25 m rozšířený pod ACT (`visibility_range_begin`), jemná úroveň s `visibility_range_end`.
- **Riziko:** 0.60–0.61 dělení terénu ve hře dělalo „béžové plachty a pyramidy“ (`svet.gd:812`). Proto dělit v Blenderu,
  ne za běhu, a hrubou úroveň stavět z téže výškové funkce. Rozpor Blender × Godot zapsat do
  `docs/rozpracovane/rozpory_blender_godot.md`, pokud se objeví.
- **Měření:** nejdřív K3 `teren_jen_blizko` (skrytí vzdálených celých pásem jen pro měření, za 1 trasu). Pokud p50 klesne o
  > 3 ms, je to naměřený vliv terénu a K4 má smysl. Pak trasa vše 0.999998 vs. nová verze, panel „teren“.
- **Návrat:** `teren_dlazdice.krok_m: 0` → Blender vyexportuje dnešní celé sítě.

---

## 3. Co je NEOVĚŘENO a jak to ověřit
- Skutečný čas GPU – tablet ho neměří. Nejbližší náhrada jsou varianty K3 (rozdíl p50). Případně Android GPU Inspector nebo
  Snapdragon Profiler (Míša).
- Jestli je zapnutá tráva GPU v Nastavení – podívat se do `user://` configu nebo na řádek FPS.
- Jestli okluzní ořez (`use_occlusion_culling`, Embree) na Androidu v Compatibility opravdu běží – panel by mohl ukazovat
  počet okluzorů a vyřazených instancí (K1).
- Cena ořezu `visibility_range` na instanci (Z7) je odhad. Ověřit lze jen variantou K10 (méně instancí → kreslení CPU).

## Potvrzení z Pucharta (Míša 15. 11. 22:31 – Puchart session porovnal tento rozbor se svým kódem)
- Terén: Puchart má hotové dlaždice s LOD → **převzít postup, ne vymýšlet**: `origin/ccr-f2d32673-9fi7m5`
  `puchart/nastroje/teren_dlazdice.py` (pečení dlaždic t_<i>_<j>.glb s uzly LOD0..LOD3 a sukní proti škvírám, obzor.glb
  s dírou pro výsek, vše offline – „nic se nepočítá na tabletu“), pravidla `puchart/pravidla/svet/teren.json`
  (dlazdice_m 250, lod krok 2/4/8 m do 200/450/900 m, hystereze), hra `puchart/hra/scripts/svet.gd` (načtení dlaždic).
  U nás terén staví Blender (kraj.py) a hra ho upravuje (svet.gd) → dlaždicovat AŽ po herních úpravách? NE – pravidlo
  „pozdější krok nehýbe dřívějším“: herní úpravy terénu přesunout do exportu, pak dlaždice offline jako Puchart.
- Režim „uvnitř“ (pod střechou kratší dohled / zdi zakryjí): obě hry stejně → K8.
- Pevná zásoba připravených kusů (louka, les, byliny) místo nové paměti na grafice → K5, Puchart to plánuje taky.
- Panel sám 7–11 ms (u nás naměřeno 2,1–11,6 ms) → lehký monitor už je výchozí v měřicí trase.

## K13 – časované prolínání LOD místo pásma (Míša 16. 11., předloha `docs/reference/lod_casovane_prolinani/`)
- Princip: dnes (Godot visibility_range fade, stromy `_prolinani_stromu` = true, dlaždice terénu pás 40 m) se oba stupně
  kreslí PO CELOU dobu, co je kamera v pásmu (stojí-li hráč v pásmu, navždy) – na předloze 58–63 stromů 2×. Časované
  prolínání: při překročení hranice se zapíše čas, shader prolne dither za `fadeTime` (0,25 s) → 2× jen na okamžik (0–3 stromy).
- U nás: overdraw listí v pásmu byl už 0.997 naměřen jako cena (modely.json `_prolinani_stromu`). Stromy jsou v buňkách
  MultiMesh → čas přechodu po buňce (custom data/uniform instance), ne po stromu; hystereze proti kmitání na hraně.
  Totéž pro dlaždice terénu (pás 40 m) a díly (_dil_lod).
- Data: `modely.json lod_prolinani {"druh": "cas"|"pasmo", "cas_s": 0.25}`, varianta trasy pro A/B. NEOVĚŘENO – po vydání.
- **Míša 16. 11.: „my máme jen 3 druhy, tady je jich mrtě a ještě impostory“.** Změřeno z glb: naše stromy LOD0 ~11–12 tis.
  troj. (dub, buk, lípa, olše, jabloně 12 000; bříza 7,5 tis.; smrk 6,9 tis.), pak rovnou impostor (6 troj., `_daleko`)
  od 40 m (tablet, `STROM_PREP`). Předloha: 1 081 → 787 → 524 → 361 → impostor 2. Tj. náš blízký strom je ~11× těžší
  a mezi 12 tis. a impostorem není nic → ostrý skok, proto pásmo prolínání (2× kreslení). Import má `generate_lods=true`
  (automatické mezistupně Godotu uvnitř LOD0), ale ty listí karet nezjednoduší dobře (podezření, neměřeno, kolik se jich
  na tabletu reálně použije). Návrh: vlastní LOD1 ~3 tis. a LOD2 ~1 tis. (Blender decimace karet / méně karet, jako
  `trees.py` karty), impostor až dál, s časovaným prolínáním K13 → méně trojúhelníků ve 15–40 m i kratší 2× kreslení.
- **K14 tráva podle videa (Míša 16. 11. 17:57–18:02: dither mask, card cells × impostor cells).** Prolínání ditherem už
  máme (`trava_gpu.gdshader`: každý trs vlastní práh + Bayer 4×4, pásmo `fade_sirka` 14 m před `trava_dosah_m` 80 m).
  Chybí jejich druhá vrstva: za hranicí trsů „impostor cells“ = nízká síť (~10 troj./buňka) s texturou vršků trávy,
  aby za hranicí nebyl hladký terén → hranice zmizí a trsy mohou končit blíž (jejich 82,6k → 41k troj. při stejném
  vzhledu). Pozor: u nás 0.9995 zkrácení dosahu výkon na tabletu NEZMĚNILO (naměřeno) → dřív ověřit, kolik tráva stojí
  kresleníma pixely (překryv karet) a ne trojúhelníky: varianta trasy „trava_dosah 40 + vrstva vršků“ vs. 80.
