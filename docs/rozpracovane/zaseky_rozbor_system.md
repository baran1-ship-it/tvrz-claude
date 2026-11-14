# Záseky: rozbor příčin a návrh systému (14. 11., nezávislý subagent)

Postup: jen čtení repa a zdrojů Godotu 4.4.1-stable z GitHubu. Nic jsem nespouštěl. **[kód]** = ověřeno ve zdroji,
**[data]** = údaj z `docs/mereni_verze.md`, **[úvaha]** = můj odhad, který nikdo neměřil.

## 0. Nové ověřené fakty (mění výklad dosavadních měření)
- **F1 [kód] „shadery +0“ nic nedokazuje.** V GLES3 vrací `get_pipeline_compilations` vždy 0 (`drivers/gles3/rasterizer_scene_gles3.h:775`,
  `rasterizer_canvas_gles3.h:383`). Proto je závěr „kompilace shaderů vyvrácena (naměřeno)“ chybný (`mereni_verze.md:442`,
  `misa_28_chyby.md` ř. 159). Správně: **NEZMĚŘENO**.
- **F2 [kód] Čas GPU se na tabletu změřit nedá.** `capture_timestamp` volá `glQueryCounter` jen pro desktopové GL
  (`drivers/gles3/storage/utilities.cpp:328`). Funguje jen čas CPU: `viewport_get_measured_render_time_cpu` a `get_frame_setup_time_cpu`.
- **F3 [kód] Co je ve „kreslení+čekání“** (`diag.gd:189` měří od konce diag `_process` po 1. krok fyziky dalšího snímku).
  Patří do toho tohle: časovače, tweeny a `_flush_delete_queue`, tedy všechny `queue_free` (`scene_tree.cpp`, `process()`).
  Dál `RenderingServer.sync` a `draw`, tj. nahrání MultiMeshů (`_update_dirty_multimeshes`), ořez, stín a volání kreslení.
  Ovladač sestaví program při prvním kreslení, i to padne sem. Pak `eglSwapBuffers`, který Android volá až po `GodotLib.step()`
  (`GodotRenderer.java:61`). Tam se čeká, dokud GPU nemá místo ve frontě snímků. Nakonec spánek `Engine.max_fps`.
- **F4 [kód] Postupné plnění louky nefunguje, jak komentář tvrdí** (`louka.gd:1003-1006`). Plnění probíhá s
  `visible_instance_count = 0`, takže `_update_dirty_multimeshes` nahraje 0 B a příznaky změn smaže (`mesh_storage.cpp:2170-2177`).
  Při odkrytí buňky (`louka.gd:551-555`, `_viditelne`) označí `_multimesh_set_visible_instances` jako změněné všechny instance
  (`mesh_storage.cpp:2124-2140`). **Celá buňka se tedy nahraje v jediném snímku, a to právě ve „kreslení+čekání“.** Uzly nepřibudou
  a VRAM se nezmění (buffer vznikl už při `instance_count`). To přesně odpovídá podpisu záseků.
  `_viditelne` navíc každé 4 snímky mění počet kreslených instancí u každé buňky (`louka.gd:625`). Každé zvýšení znovu nahraje
  úseky po 512 instancích do bufferu, který GPU možná ještě čte.
- **F5 [kód] Úlohy s nízkou prioritou běží nejvýš ve 2 vláknech** (`worker_thread_pool.cpp:769`, poměr 0,3 × jádra).
  Údaj „vlákna 6“ je délka fronty, ne počet souběžných vláken. Kupy (`louka.gd:645-648`) VLAKEN neomezuje.
- **F6 [kód] Swappy je ve 4.4.1 jen pro Vulkan.** `enable_frame_pacing` (`project.godot`) na Compatibility nic nedělá.

## 1. Hypotézy
### a) Snímky 40–110 ms (podpis: skripty 5–15, nové uzly 0, VRAM ±0, „kreslení+čekání“ 30–102)
Detektor bere jen snímek nad 40 ms, který je zároveň ≥ 1,6× delší než klouzavý průměr (`diag.gd:229-235`). Jde tedy o
**náhlé události**, ne o trvale drahý pohled.

| # | hypotéza | stav | pro / proti |
|---|---|---|---|
| A1 | nahrání celé buňky louky při odkrytí (F4) | **podezření (silné)** | pro: mechanismus [kód] F4; v řádcích záseků vždy „louka hotové/kupy ve vláknech“; „bez trávy“ měla záseků > 40 ms 2 proti 45 u „vše“ (0.9996) a 4 proti 9 (0.9997) [data, ovšem zkreslené pořadím variant]. Proti: objem buňky je jen ~0,4 MB [úvaha] → vadí spíš synchronizace s GPU než přenos |
| A2 | časté malé nahrávání při změně `visible_instance_count` (F4) | podezření | [kód]; dopad na Adreno nikdo neměřil |
| A3 | první vykreslení kombinace materiálu (sestavení v ovladači) | **podezření, NEZMĚŘENO** (F1) | pro: 1. průchod je horší než 2. (0.999995, 0.999996) [data] |
| A4 | odkrytí buňky rostlin, kdy se naráz zobrazí 10–50 MMI (`svet.gd:3636-3637`) | podezření | buffery jdou nahoru už v `_rost_dil` (`svet.gd:3566`); odkrytí přidá jen volání kreslení |
| A5 | `queue_free` buněk a kolizí zpracované ve `_flush_delete_queue` (F3) | podezření (slabé) | `louka.gd:549,621,653`, `svet.gd:3601`; nikdo neměřil |
| A6 | tlak GPU fronty (GPU ≈ 30 ms a víc → občas dlouhé čekání ve swapu) | podezření | průměrně skr 3–8 + cpuR 6–10 ms při snímku 20–35 ms [data 0.9995] → zbytek připadá na GPU [úvaha] |
| A7 | teplo jako trvalý stav | **naměřený vliv** na základní úroveň | teplota (headroom) 0,89 po 15 min (0.99995) [data]; Míša: tablet je pořád horký. Teplo všechno zpomalí ~1,3–2× [úvaha], ale samo nevytvoří skok o 1,6× |
| A8 | fyzika hráče na ConcavePolygon hostince | **potvrzená příčina** (jen u záseků v hostinci) | 28,3 ms (move_and_slide 16,5 + schod 11,7) [data] |
| A9 | drahý pohled (kreslení, stín slunce) | naměřený vliv na **p50/p95**, ne na skoky | les bez stínu slunce p95 85 → 42 (0.99996); ves-vjezd 42 ms při 692 kresleních proti 27 ms při 562 [data] |

### b) Zamrznutí na několik sekund (2,4–6 s, FPS ~9)
| # | hypotéza | stav | důkaz |
|---|---|---|---|
| B1 | první sestavení programů | **naměřený vliv** (na novou instalaci) | ves-dvory 2,9 s nastalo v 1. trase, ve 2. trase téže verze už ne (0.999997) [data]. F1 ale vyvrací i potvrzení přes „shadery“ |
| B2 | blokující čekání na vlákno | dřív **potvrzená a ověřená oprava** (`diag.faze`, 5e04eda) | nová místa NEPROVĚŘENA |
| B3 | tlak na paměť (zram, lmkd) | podezření | volnou RAM u špiček nikdo nezapsal; do 0.99998 se četla špatně |
| B4 | změny automatické kvality | ověřená oprava | 0.99998 |

## 2. Chybějící měření (vše doplnit do `_detektor`, `diag.gd:220-275`)
1. **Rozpad „kreslení+čekání“.** V `setup` napojit `RenderingServer.frame_pre_draw` a `frame_post_draw` (oba běží v hlavním
   vlákně). Do `_sn_ted` zapsat razítka `pred`, `po` a do řádku vypsat tři části:
   - „před kreslením“ = `pred` − konec diag: mazání, časovače, sync,
   - „kreslení CPU“ = `po` − `pred`: nahrávání, sestavení, volání kreslení,
   - „swap/GPU“ = začátek dalšího snímku − `po`.
   Tím se oddělí A1–A5 (CPU) od A6–A7 (GPU).
2. **Události snímku**, každá jako čítač: buňky louky odkryté v tomto snímku a jejich bajty (instance × stride), přírůstek
   instancí ve `_viditelne`, odkryté buňky rostlin, `queue_free` louky, rostlin a kolizí, počet nových klíčů `_pred_videno`
   (vlastní čítač prvních kombinací místo F1).
3. Volání kreslení a primitiva (`RENDERING_INFO_TOTAL_*`), poslední teplotu z `kvalita.gd`, délky 3 předchozích snímků.
4. Do hlavičky logu obnovovací frekvenci obrazovky (`DisplayServer.screen_get_refresh_rate()`) a `OS.get_processor_count()`.
5. U špiček nad 1 s volnou RAM z `/proc/meminfo` (měřič už existuje).

## 3. Návrh systému (od největšího očekávaného účinku)
1. **Jeden plánovač snímku**, který vlastní všechno streamování: buňky louky, kupy, rostliny, kolize, LOD postav a přepnutí
   vnitřku. Rozpočet na snímek má tři meze z `rozpocty.json`: čas, bajty nahrávání a počet nových kreslených instancí.
   Dnes jsou rozpočty roztříštěné: louka 4 ms vlastní (`louka.gd:958`), plánovač 2 ms, a `rozpocty.json` „ostatni“ je
   `zapojeno: false`. Mazání se rozpočtuje stejně jako stavba.
   *Ověření:* varianta `bez_streamovani` (louka a rostliny postavené předem na krátkém úseku, pak se nic nemění) proti „vše“.
   Měří se počet záseků a nový rozpad, ne p50.
2. **Louka s pevnými předalokovanými MultiMeshi (pool).** Celý buffer jedním `multimesh_set_buffer` (glBufferData = nové
   úložiště, ovladač nečeká na GPU). Odkrývat až snímek po nahrání. `visible_instance_count` pevný pro každou úroveň,
   hustotu podle vzdálenosti řeší jen shader podle hashe (už to umí). Pryč `_plnit` po instancích i změny počtu ve `_viditelne`.
   *Ověření:* varianty `louka_set_buffer` a `louka_bez_viditelne` proti „vše“.
3. **Sestavení předem jako přejímka, ne pocit.** Vlastní čítač prvních kombinací (bod 2.2) v řádku záseku. Trasu jezdit
   dvakrát po instalaci a porovnat 1. průchod se 2.
4. **Pravidla vrhání stínu podle třídy dílu:** stavby a stínová tělesa stromů ano, rostliny, předměty a tráva ne. Bez
   vlastních čísel v kódu. Měřený přínos dá varianta „stiny“ (les p95 −43 ms).
5. **Pevných 30 FPS a tepelná rezerva.** Cíl je, aby CPU kreslení + skripty + fyzika zabraly ≤ 20 ms a zbytek byla rezerva.
   Nejméně dvě rostlinná a travní vlákna, protože rozsev v GDScriptu běží trvale (1,2–2,2 s na buňku na PC,
   `predani.md`) a hřeje. *Ověření:* varianta `vlakna_1`, sledovat teplotu a p95 po 15 min.
6. **Hostinec:** kolize z konvexních dílů místo ConcavePolygon (A8, potvrzeno).

Tráva GPU nahrazuje jen vrstvu 0 (`trava_gpu.gd:4`), takže A/B z 0.999997 streamování neizoluje. Navíc se porovnávalo jen p50,
ne počet záseků.

## 4. Výsledky (14. 11. večer, pomocník – diag, louka, test)
**Ověřeno ve zdroji Godot 4.4.1-stable [kód]:**
- `frame_pre_draw` vysílá `RenderingServerDefault::draw()` na začátku (hlavní vlákno; po `_process`, mazání `queue_free`,
  časovačích, `RenderingServer.sync`), `frame_post_draw` konec `_draw` → `_run_post_draw_steps` (bez vlákna kreslení
  synchronně, `rendering_server_default.cpp:197,410`). Mezi nimi `RSG::scene->update()` → `update_dirty_resources` →
  `_update_dirty_multimeshes` (nahrání MultiMeshů), ořez, kreslení; na PC i swap (`gl_end_frame`), na Androidu je
  `eglSwapBuffers` až po kroku enginu → spadne do „swap/GPU“ spolu se spánkem `max_fps`.
- Nahrání MultiMeshe (`mesh_storage.cpp:2124-2200`): data jdou do GPU až při kreslení a jen oblasti po 512 instancích do
  `visible_instance_count`; zvýšení počtu označí nové instance za změněné; nad 32 změněnými oblastmi nebo nad polovinou
  kreslených se nahraje všech prvních ⌈n/512⌉ oblastí. Snížení nenahrává nic. Každá změna počtu bez `MultiMesh.custom_aabb`
  přepočítá AABB přes všechny kreslené instance (`_multimesh_re_create_aabb`). Řádek instance = 16 floatů (64 B).

**Změněno:**
- `scripts/diag.gd`: řádek záseku má rozpad „kreslení+čekání“ (před kreslením / kreslení CPU / swap/GPU), odebrané uzly
  (počet uzlů před + přidané − teď), 3 předchozí snímky, volání kreslení a primitiva, události snímku (`diag.udalost(klic, n)`,
  klíč na `_B` = bajty). Hlavička logu (`diag.log`, `zaseky.log`, schránka): obnovovací frekvence obrazovky, jádra, model.
- `scripts/louka.gd` (commit se dostal do f12c4ca4 souběžné session): při plnění skryté buňky roste `visible_instance_count`
  s naplněným počtem → nahrání se rozloží do snímků plnění, odkrytí nenahrává nic; `MultiMesh.custom_aabb` (bez přepočtu
  AABB); `_viditelne` mění počet jen po kvantech (nahoru zaokrouhlit, instance navíc shader srazí podle hashe – vzhled
  stejný), dolů s hysterezí; každé zvýšení (plnění i `_viditelne`) v rozpočtu bajtů na snímek (model ovladače `_model_b`);
  hráč uvnitř budovy: vzdálená buňka se skryje uzlem, počty zůstanou (dřív 0 a po odchodu nahrání všech buněk naráz).
  Čísla: `pravidla/svet/rozpocty.json` `louka_nahravani` (rozpočet 256 kB = úvaha).
- Test `louka_nahravani` (`tools/test_svet.gd`): jízda cvalem přes louku `pasma.test.louka_nahravani_s`, největší nahrání
  za snímek ≤ rozpočet a postavila se aspoň jedna buňka. **PC headless 14. 11. 21:12: OK** – 1800 snímků, nejvíc
  256 kB/snímek (rozpočet 256 kB), průměr 8,9 kB, nejvíc 4000 instancí a 1 buňka za snímek, postaveno 19 buněk.
  Ve stejném běhu `interier` OK, `louka_bod` OK, `trava_dorust` CHYBA jen v trysku (873/1801 pozdě u (-7, 416)) – **padal
  už před změnou** (plna_sada 11:26: 570/1793 na tomtéž místě); vypsané pozdní buňky mají „ceka true, stavba 0“ = čekají na
  rozsev ve vlákně, ne na plnění/rozpočet bajtů. Vliv rozpočtu na trysk tím není vyloučen (NEOVĚŘENO), jen není vidět.

**NEOVĚŘENO NA ZAŘÍZENÍ:** zda tím zmizí záseky 40–110 ms (A1/A2 jsou dál podezření, ne potvrzená příčina); velikost
rozpočtu 256 kB; cena navíc kreslených (sražených) instancí z kvantování (≤ ~2 kvanta na MultiMesh); kupy (`_mm`,
`mm.buffer` = celé `glBufferData` v jednom snímku) se nezměnily. Ověření: trasa s novým řádkem záseku – u záseků dívat se
na „kreslení CPU“ a `louka_B`.

**Pro svet.gd (rostliny, nedělal jsem – souběžná session):** v `_rost_krok` (~ř. 3636) hned za smyčkou
`for m: Node3D in _rost_uzly[bb]: m.visible = true` (odkrytí buňky rostlin):
```
var dg_r: Object = Engine.get_meta("diag", null)
if dg_r:
	dg_r.udalost("rost_bunek", 1)
	dg_r.udalost("rost_mmi", (_rost_uzly[bb] as Array).size())
```
