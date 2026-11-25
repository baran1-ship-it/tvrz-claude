# Vesničané z NPC Character Pack (Míša 25. 11.: „náhrada za muže, ať nemáme ty potrhané borce“)

Zdroj: Disk `1qW5K2xC0Ega4xWvTlq7xGVZ5r9ZBLDhL` (zip 2,6 GB, čten po kouskách – `zipremote.py`), 5 postav × 2 oděvy
(`SK_NPC_Character_0N_Full_01/02.FBX`, kostra UE4 mannequin 60 kostí, 35–88 tis. troj., textury TGA 2–4K).

## Postup (opakovatelný)
1. FBX do `zk_muz/muz<NN><VV>.fbx` (mimo `build/` – má `.gdignore`), `godot --import`.
2. `MUZ=muz0102 godot --headless -s res://zk_muz/vyvoz.gd` (kopie `tools/postavy_q/muz_vyvoz.gd`) → glb. Blender UE4
   FBX kostru nenačte (prázdné objekty bez vah); Godot ano. Tvarové klíče hlavy pryč (jinak hlava bez trojúhelníků).
3. `/opt/bl/bin/python -I tools/postavy_q/muz_npc.py <glb> <tex1k> npc_muz_<NN>[_b]`:
   - kostra na tvar UAL: head→Head, kořen root, zkrutné kosti slité do rodiče;
   - **klidová póza jako UAL** (natočení kostí ke kloubům UAL, zapečeno do sítě) a **osy kostí jako UAL** – klipy Godotu
     jsou místní rotace kostí: bez toho postava ležela (osy) a měla ruce 25 cm od těla (A-póza);
   - zmenšení po kusech (hlava a ruce 2× podíl) na ~13–15 tis. troj., textury 1K podle materiálu FBX
     (`tools/postavy_q/muz_npc.json`; ruce a oči mají materiál hlavy).
4. Výstup `modely/postavy/npc/npc_muz_*_cela.gltf` – sada jako ostatní (`scripts/vzhled.gd`), klipy UAL bez retargetu.
   Ověřeno `zk_muz/anim_test.gd`: osy 0,0° proti UAL, klouby v chůzi do 2 cm od postavy UAL.
