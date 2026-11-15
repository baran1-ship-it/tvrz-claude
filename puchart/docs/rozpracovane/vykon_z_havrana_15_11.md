# Výkon: co si vzít z Havranova rozboru GPU (15. 11.)

Zdroj: Havran `docs/rozpracovane/rozbor_gpu_15_11.md` (větev claude/new-session-0dtk58), Míša 15. 11.: „Havran jede na grafiku,
možná se ti bude něco hodit“. Porovnání s Puchartem (kód 15. 11.):

| Havran zjištění | Puchart | Akce |
|---|---|---|
| Terén jedna obří síť na pásmo, bez LOD (547 tis. troj. stále) | **už dlaždice + LOD** (`scripts/svet.gd` _lod, visibility_range) | nic – ověřit jen počet troj. terénu v panelu |
| Uvnitř krčmy se kreslí celý venkovní svět (1,2–1,6 M prim.) | **totéž** – vnitřky mají jen `vnitrek_do_m`, venkovní svět (les, louka, terén, hrad) se uvnitř kreslí dál | **P1:** režim „uvnitř“ (hráč pod střechou celku/domu: zkrátit dohled louky/lesa/dálky, nebo okluzory zdí krčmy/hájovny/domů) – data `rozpocty.json uvnitr`, měřit snímkem v krčmě |
| Nové MultiMeshe při každé přestavbě buňky (alokace GPU bufferu dokola, špička 1,2 s) | `bunky_kolem.gd`, `byliny.gd`, `les.gd`, `louka.gd` dělají `MultiMesh.new()` za hry | **P2:** pevná zásoba MultiMeshů (kruh slotů), přestavba = přepis bufferu; ověřit na trase řádkem záseků |
| Diag čte buffer MultiMeshe z GPU (`get_instance_transform` na `mm.buffer`) = synchronizace CPU–GPU | Puchart diag to nedělá | nic |
| Plný panel stojí 7–11 ms | panel Puchartu také prochází strom? | **P3:** změřit cenu panelu (zapnutý/vypnutý), drahé části jen na požádání |
| „shadery +0“ v Compatibility nic nedokazuje (`get_pipeline_compilations` vždy 0) | platí i pro Puchart | do docs/kcd_grafika_tablet.md poznámka |
| Impostory obzoru v buňkách 1024 m bez visibility_range | Puchart les dálky – zkontrolovat buňky a `visibility_range_end` | **P4:** kontrola les.gd dálky |
| Stínová tělesa (`SHADOWS_ONLY`) panel počítá jako viditelná | Puchart má `_Daleko_Stin` u domů | panel: oddělit viditelné/stín (`get_render_info TYPE_VISIBLE/TYPE_SHADOW`) |

Pořadí: po dokončení funkcí a hlídačů, před vydáním APK měřit P1 a P3 (rychlé), P2 a P4 podle výsledku.
