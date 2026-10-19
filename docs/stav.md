# Stav projektu – Odkaz Havrana (19. 10. 2026, verze 0.55, připravena 0.56)

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

## 0.56 – připraveno (19. 10. 2026, PC, Compatibility, kvalita 1, 1200×800)
| Místo | Kreslení | Troj. | GPU* |
|---|---|---|---|
| louka (60, 60) | 912 | 2.05 M | 880 MB |
| hostinec (-62, 881) | 910 | 1.99 M | 852 MB |
| příkop (0, -36) | 1519 | 2.80 M | 886 MB |
| skály (-80, 300) | 540 | 1.03 M | 867 MB |
| potok u mostu (222, 604) | 761 | 1.90 M | 866 MB |

*GPU na PC v kontejneru (ETC2 se rozbaluje), na tabletu nižší. Proti 0.55: louka −0,10 M, příkop −0,19 M (méně kamení na kosené louce, pěšiny volné, skály pryč z pěšin), kreslení všude níž. Příkop 1519 volání = na hraně 1500 (tvrz, LOD tvrze odložen). Snímky docs/screens/056_*.jpg (bílé skvrny = PC artefakt pole textur půd).

**Testy světa** (`TVRZ_TEST=svet`, tools/test_svet.gd) – všech 6 zelených:
| Test | Výsledek |
|---|---|
| sonda | OK (díry u mostu zalepené, zbývají 3 body na okraji – pod prahem) |
| visici | 0 z 98 390 instancí (2 873 zapuštěných) |
| kolize | měkké s kolizí 0, stromy bez kmene 0 z 12 342 |
| stanoviste | v kosené louce 0 smrků, kamení, výchozů |
| dalka | kopec 300 m: jas 0,70 / 0,73, odstín 6° / 0° |
| prochod | tvrz–ves 866 m, tvrz–Doubrava 214 m, tvrz–skály–hostinec 858 m, břeh potoka 168 m, brána 37 m |

### Otevřené
- **0.55 bez textures/ a audio/** (plamen, kouř, mraky, syntetické zvuky): opraveno v tools/pregeneruj.sh (zaklad), do hry s APK 0.56.
- Tvrz u příkopu ~3 M (síť tvrze 1,2 M) – LOD tvrze odložen (radce 18:30), Míša ověří FPS na tabletu. Portály tvrze v kódu (scripts/portaly.gd), neměřeny.
- Uzel Zivot neprozkoumán. Další: navigační síť z mapy stanovišť a trasy terénem (21:25–21:35), streamování při 12 m/s, import modelů znovu (20:30), mech/zelí, mez s kamením, kurník/meč/ovce. Impostory: otočení v polovičních datech má jen 4 kroky (w = měřítko·256) – opravit kódování.
