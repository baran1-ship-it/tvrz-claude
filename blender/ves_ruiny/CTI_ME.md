# Zdroj zaniklé vsi (Míšin model z Disku, `vesnice_ruiny.zip`, 15. 11.)

Míša 15. 11.: „mám novou vesnici ruin, mrkni, myslím, že je lepší“. Popis modelu: `NAVOD_VES.md`.

- Hotové díly: `modely/ruiny_ves/ves_*.glb` + `ves_*_lod1.glb` (mimo git, do hry balíkem `z_ruiny_ves`:
  `python3 tools/vydani.py 0.NN --jen …,z_ruiny_ves`). `ves_celek.glb` se do hry nedává – jen z něj je rozvržení.
- Zdroj (`vesnice_ruiny.py` + `_ruiny.py`, `_stavba.py`, `tesar.py`, `_spolecne.py`) potřebuje `foto/` (fotky textur, v gitu
  nejsou) a vytváří `.blend` a `.glb` (v gitu nejsou).
- Ve hře: `lokace.json ruiny zanikla_ves` – `dily` [soubor, x, z, natočení °] v rámci vsi (z uzlů `Ves_*` celku: Blender
  (x, y) → Godot (x, −y), natočení stejné), `pudorysy` (zdi a průchody dílů z kolizí `-convcolonly`), `vypustene` (díly
  na svahu nad `plochy.json teren stavba_max_sklon`); Blender `kraj.MISTA ruiny_ves_N` rovinka pod každým dílem
  (poloměr `rovina_k` × půlúhlopříčka zdí), `ruiny.zanikla_ves` jen porost a název; hra `svet._ruiny_ves_dil`; test `ruiny_ves`.
- Rozvržení a pořadí rovin vybrané výpočtem (sklon půdorysů z `tools/krok_b/vysky.json`, odchylka rohů z `fort.land`
  s rovinami): ves (302, 349), natočení −113°, nejhorší roh 0,25 m.
