# Zdroj zříceniny kostela (Míšin model z Disku, `kostel_ruiny.zip`, 15. 11.)

Míša 15. 11.: „tohle je náhrada za náš kostel, starý smaž a dej nový a ať je taky hezky zarostlý“
(https://drive.google.com/file/d/1QCnSAcercT8DH7EjsI7O9046q-olssKt). Popis modelu: `NAVOD_KOSTEL.md`.

- Hotové modely: `modely/kostel/kostel_ruiny.glb`, `kostel_ruiny_lod1.glb` (mimo git, do hry balíkem `z_kostel`:
  `python3 tools/vydani.py 0.NN --jen …,z_kostel`). Stažení zipu: `curl -sL "https://drive.usercontent.google.com/download?id=1QCnSAcercT8DH7EjsI7O9046q-olssKt&export=download&confirm=t"`.
- Zdroj (`kostel_ruiny.py` + `_stavba.py`, `tesar.py`, `_spolecne.py`, `char_tex.py`) potřebuje `foto/` (fotky textur, v gitu nejsou –
  jako u krčmy `blender/krcma_L/stahni_foto.sh`) a vytváří `.blend` 38 MB (v gitu není).
- Ve hře: `lokace.json ruiny kostel` (model, LOD, vnitřek, dveře sakristie, `kryti_lok` klenby, `rostliny_lok`, `stavba_lok`,
  `pruchody_lok`), `svet._kostel_dil`; Blender `ruiny.kostel` jen rovina (`rovina_r_m` 22), porost a název místa.
