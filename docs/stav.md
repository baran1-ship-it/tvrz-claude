# Stav projektu – Odkaz Havrana (20. 10. 2026, verze 0.56b, blok 0.57 louka)

Historie měření a starší otevřené body: docs/stav_historie.md.

## Rozpočet (Android, Xiaomi Pad 8 / Adreno 825)
- Volání kreslení: max 1500 / snímek
- Trojúhelníky: cíl 2 M / snímek, tolerance do 2,75 M, pokud FPS drží 30+
- Paměť GPU: pod 700 MB (monitor ukazuje zvlášť textury a buffery)
- Hlídání: diag.gd loguje každé 2 s do user://diag.log, varování při 1,5× rozpočtu (s pozicí hráče) do user://diag_varovani.log, panel „Měření výkonu“ v nastavení
- Skály: LOD0 ≤ 3000 troj. (0–40 m, se stínem), LOD1 ~800 (40–120 m), LOD2 ~150 (120–500 m)
- Stromy: plný model do 60 m (stín), zjednodušený tvar 55–120 m bez stínu, za 120 m nic
- Stíny: 2 kaskády, atlas 2048, vegetace (mimo stromy a skály LOD0) bez stínů
- Louka: max 3–4 volání na buňku (32 m); střední pásmo do 100 m, 1,2 trsu/m²
- Drobná vegetace: nízká 22/32/45 m, střední 50/70/95 m (podle kvality)
- Předměty: dosah podle velikosti 20 / 40 / 80 m, drobné (<0,5 m) bez stínu
- Textury: terén a modely 1024, vegetace 512, stromy a skály 1024; vše VRAM komprese + mipmapy (tools/limity_textur.py, spouští vydani.py)
- Prah LOD sítí: rendering/mesh_lod/lod_change/threshold_pixels = 4

## Známá omezení (Compatibility renderer)
- U MultiMesh je transformace instance už ve VERTEX, MODEL_MATRIX je jen uzel (střed 32m buňky louky) –
  vzdálenost pro prolínání se musí brát z polohy vrcholu, ne z MODEL_MATRIX (stebla i kvety.gdshader).
- Není HDR buffer: světlo nad 1 se ořízne před tonemapem → samostatný světelný profil (daylight.gd, `ldr`).

## 0.57 – blok LOUKA (20. 10. 2026, PC, Compatibility, kvalita 1, 1200×800)
| Místo | Kreslení | Troj. | GPU* |
|---|---|---|---|
| louka (60, 60) | 975 | 2.49 M | 892 MB |
| hostinec (-62, 881) | 956 | 2.37 M | 876 MB |
| příkop (0, -36) | 1581 | 3.14 M | 899 MB |
| skály (-80, 300) | 585 | 1.69 M | 891 MB |
| potok u mostu (222, 604) | 848 | 2.56 M | 891 MB |

*GPU na PC v kontejneru. Příkop nad rozpočtem kvůli tvrzi (LOD tvrze odložen, 0.55 už 2,99 M). Snímky docs/screens/057_*.jpg.

**Hlavní příčina děr v trávě na tabletu (od pátku):** kvalita 1 (hustota 0,7) ředila po hashi i výplň – 30 % drnu chybělo všude; na PC se testovalo stejně, ale díry se schovaly v malých snímcích. Výplň se teď kvalitou neřídí. Druhá příčina: drn_atlas je z 93 % průhledný (jednotlivé chomáče) – karta nic nekryla → vlastní atlas vějíře (tools/vejir_atlas.py).

**Louka 0.57:** drn-vějíř (3 karty 50°, 6 troj.) na každém bodě výplně 8/m² + směs podle stanoviště (pravidla_sveta.json vyplnovy_mix), pásma 0–25 m plně / 25–60 m 25 % / do 90 m pryč po čtvrtinách buňky 16 m, trsy 20–110 m, kosená louka jen do 150 m od tvrze a vsi (dál neudržovaná ×1,5 trsů ×1,3 výška), normála trav nahoru ve vertex() (vertex_lighting), paty karet neprůhledné, tmavá pata a AO jen do 40 m.

**Testy (t60/t61):** shadery, sonda, visici (0 z 98 951), kolize, stanoviste, pokryv (100 %), dira (0 skvrn ≥ 400 px na 3 místech; pixelově 8–10 %), prochod 5/5, dalka (3 výhledy) – OK. **pasmo**: 30 a 60 m na všech 3 místech v mezích; 100 m na 2 místech 0,90 a 0,77 (okraj lesa v rámečku u horizontu – barva lesa v dálce, blok 0.58).

### Otevřené
- **0.55 bez textures/ a audio/** (plamen, kouř, mraky, syntetické zvuky): opraveno v tools/pregeneruj.sh (zaklad), do hry s APK 0.56.
- Tvrz u příkopu ~3 M (síť tvrze 1,2 M) – LOD tvrze odložen (radce 18:30), Míša ověří FPS na tabletu. Portály tvrze v kódu (scripts/portaly.gd), neměřeny.
- Uzel Zivot neprozkoumán. Další: navigační síť z mapy stanovišť a trasy terénem (21:25–21:35), streamování při 12 m/s, import modelů znovu (20:30), mech/zelí, mez s kamením, kurník/meč/ovce. Impostory: otočení v polovičních datech má jen 4 kroky (w = měřítko·256) – opravit kódování.
