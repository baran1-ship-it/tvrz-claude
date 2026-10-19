# Stav projektu – Odkaz Havrana (19. 10. 2026, verze 0.55)

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

## 0.55 (19. 10. 2026, PC, Compatibility, kvalita 1, 1200×800)
| Místo | Kreslení | Troj. | GPU* |
|---|---|---|---|
| louka (60, 60) | 988 | 2.15 M | 868 MB |
| hostinec (-62, 881) | 904 | 2.14 M | 840 MB |
| příkop (0, -36) | 1615 | 2.99 M | 873 MB |
| skály (-80, 300) | 547 | 1.01 M | 855 MB |
| potok u mostu (222, 604) | 801 | 2.01 M | 854 MB |

*GPU na PC v kontejneru je o ~300 MB vyšší než dřív (ETC2 se na PC rozbaluje), na tabletu se nemění. Příkop: 0.54 na stejném místě 2,76 M; +0,2 M kameny příkopu, drn 6/m² (louka +0,3 M). Snímky docs/screens/055_*.jpg (bílé skvrny = PC artefakt pole textur půd, na tabletu OK).

### Otevřené
- **0.55 bez textures/ a audio/** (plamen, kouř, mraky, syntetické zvuky): v kontejneru se negenerovaly; opraveno v tools/pregeneruj.sh (zaklad), do hry až dalším APK.
- Tvrz u příkopu ~3 M (síť tvrze 1,2 M) – LOD tvrze odložen (radce 18:30), Míša ověří FPS na tabletu. Portály tvrze v kódu (scripts/portaly.gd), neměřeny.
- Uzel Zivot neprozkoumán. 0.56: dálka (rozdělaná oprava: docs/rozpracovano/dalka_056.patch, neověřená), mech/zelí, mez s kamením, kurník/meč/ovce.
