# zena30 – žena ~30 let, dlouhý cop (pracovní verze v1, čeká na schválení)

## Co to je
- Tělo a hlava: Quaternius Universal Base Characters (CC0), obličej přemodelovaný (užší čelist, menší nos, plnější rty, tváře, zelenohnědé oči, tenčí obočí), pleť zesvětlená, bez líčení.
- Vlasy: vlastní stylizované chomáče (bez průhlednosti – na tabletu žádné míhání), pěšinka uprostřed, sčesané dozadu, silný cop do pasu s koženým řemínkem.
- Oblečení (1393, venkov): lněná košile (výstřih a rukávy od lokte), vlněné šaty (kirtle) s rukávy k loktům, lněná zástěra, kožený opasek, nízké kožené boty, vlněné punčochy. Barvy ztlumené (šedozelená vlna, režný len).
- Výška ~1,66 m (uzel `Armature` má měřítko 0,94 – animace UAL sedí beze změny).
- 26 500 trojúhelníků celkem (tělo 7,4k, vlasy 4,3k, sukně 4,3k). Nad dřívějším limitem hrdinky 14k – viz „Další kroky“.

## Proč se sukně neprořezává
- Nohy a trup pod oblečením jsou z těla vyříznuté – nemají čím propíchnout. Viditelné zůstávají jen lýtka v punčochách (od půlky holeně) a chodidla v botách.
- Sukně a zástěra visí na 24 řetězech kostí (3–4 kosti na řetěz, `sukne_00_1` … `sukne_23_4`), cop na 6 kostech (`cop_1` … `cop_6`).
- Pohyb těch kostí je **zapečený do každé animace** z jednoduché simulace látky: gravitace, tuhost tvaru, obvodové vazby a kolize s kapslemi stehen, lýtek, chodidel a dlaní (kapsle napasované na skutečné tělo). Za běhu žádná fyzika – na tabletu to nestojí výkon a vypadá to všude stejně.
- Cop visí gravitací a drží se na zádech (kolize se zády a pánví), při předklonu spadne dolů.

## Godot 4.4 (ověřeno: 4.4.1, renderer Compatibility, snímky v nahled_godot.jpg)
1. `zena30.glb` a `zena30_animace.glb` zkopírovat do `res://modely/postavy/zena30/`.
2. `zena30_animace.glb` → Import As: **Animation Library** → Reimport. Godot odřízne „_Loop“ (Walk_Loop → Walk, smyčka zapnutá).
3. Se stávajícím `postava_sklada.gd`: `slozka = res://modely/postavy/zena30`, `postava = "zena30"`, `animace = [zena30_animace]`, `vychozi_animace = "Idle_Volne_1"`. `zena30_sada.json` je připravený (vše v jednom glb, žádné svlékání).
4. **Nepoužívat pro ni UAL1/UAL2 knihovny** – v nich nejsou stopy sukně a copu (sukně by ztuhla). V `zena30_animace` je všech 87 animací (UAL1 + UAL2 + Idle_Volne_1..3) se stejnými názvy.
5. Mrkání: tvarový klíč `mrknuti` (tělo + řasy) – `postava_oci.gd` ho najde sám.
6. Stíny: na zástěře může být „shadow acne“ (pruhy) – u DirectionalLight zvednout `shadow_normal_bias` (~2).

## Výsledek testu prořezů (test_prorezu.txt)
- Čistě: stání a všechny idle, sezení (1–2 cm = dotyk), chůze s nákladem, práce u stolu, truhla, interakce, jídlo, sekání dřeva, zalévání.
- Chůze: okem čistá (test hlásí 6 cm – je přísný, počítá i nohu těsně u lemu).
- Ještě viditelné chyby: hluboký dřep a klek (Crouch, Fixing_Kneeling, Farm_PlantSeed) – kousek holeně/kolena vyleze bokem; při sezení se místy boční díl sukně přehne přes zástěru; běh – lem odlétá a noha je vidět pod ním (u běhu v sukni přirozené).
- Boj a akrobacie (Roll, Slide, Sword_*, NinjaJump, Swim, Death) v dlouhé sukni z principu nejdou – pro ni je nepoužívat, nebo jí dát kratší pracovní sukni.

## Další kroky (návrh)
1. Klek a dřep: delší náběh simulace + pořadí panelů (boční díl nesmí přes přední), pak znovu zapéct.
2. Rozpočet: LOD/decimace sukně (30 → 20 řad) a vlasů → ~18k; nebo nechat 26k jen pro detail zblízka.
3. Volitelně rozpuštěné vlasy jako druhá varianta.

## Jak znovu postavit (Blender 5.1 jako python modul)
`skripty/`: build_head.py (obličej, kůže) → build_hair.py (vlasy) → outfit.py (oblečení, params.json) → fit_caps.py (kapsle) →
rig_sim.py outfit.blend final.blend (kosti + zapečená látka, ~10 min) → clip_test.py (test) → export.py final.blend <složka>.
Licence: tělo, hlava, oči, řasy Quaternius CC0; animace Quaternius UAL1+2 CC0 (+ Idle_Volne z Tvrze); vlasy, oblečení, textury a simulace vlastní tvorba.
