# Tváře 34 vesničanů (všechna npc_* z tools/postavy_q/postavy.json)

Podle docs/rozpracovane/zadani_tvare.md:
- Základ Quaternius Universal Base Characters (CC0), síť hlavy beze změny (stejné vrcholy, pořadí, UV, váhy) – jen posuny.
- Posuny: `OPS` v `data/<id>_data.json` (střed, poloměr, posun nebo ["scale", f]) – stejný formát jako zena30/face.py,
  symetrické v X. Vznikají z 22 posuvníků (`posuvniky`) přes `face2.build_ops` vůči landmarkům (oči, nos, brada), takže
  jdou použít na ženský i mužský základ. Aplikace: `face2.apply(obj, OPS)` na tělo, oči i obočí.
- Pleť jen barvou, atlas 512 px (`tex/<id>_kuze.png`): tón, opálení, ruměnec, kruhy pod očima, vrásky (čelo, mezi obočím,
  vějíře, nosoretní rýha, koutky, krk), stařecké skvrny, pihy, strniště, vlasy pod čepicí. Hodnoty vek/kruhy/opaleni/rumenec
  převzaté z postavy.json (tvar).
- Vlasy + vousy: stylizované, bez průhlednosti, jedna síť `<id>_vlasy`, max 1 450 troj. (čepice s nepravidelnou vlasovou
  linií, chomáče od pěšinky, drdol / cop / dlouhé vlasy; vousy plné, krátké, bradka, knír; strniště jen v textuře).
  Váhy Head, níž neck_01 a spine_03 (cop, dlouhé vlasy).
- Obočí: tloušťka, výška, sklon (`oboci`), barva podle vlasů (šediví s věkem). Oči: barva duhovky (`oci`).
- Mrkání: tvarový klíč `mrknuti` (q_oci.add_blink) na těle a řasách.
- Každý jiný: posuvníky vybrané tak, aby byly co nejdál od už vybraných stejného pohlaví; role přidávají rysy
  (kovář: široká čelist a obočí, hostinský/šenkýřka/kuchařka: plnější, stráž: brada vpřed, ponocný/staří: hubení, zahnutý nos;
  děti: kratší obličej, větší oči). Věk z postavy.json (vek 0..1 → ~24–70 let), děti podle výšky.

Soubory
- `tvare_glb.zip` – <id>.glb pro každého (kostra Armature = UAL, tělo, oči, obočí, vlasy; T-póza, bez oblečení).
  Ověřeno: načtení v Godotu 4.4.1, Compatibility (tvare_godot.png).
- `tvare_data.zip` – tvare_spec.json (návrh všech) + <id>_data.json (OPS, pleť, vlasy, vousy, počty troj.) + tex/ (pleť 512, oči).
- `tvare_skripty.zip` – gen_spec.py (návrh), tvar.py (stavba jedné postavy: `python3 -I tvar.py -- npc_kovar render`),
  batch.sh (všichni), lmk.py, face2.py, skin2.py, hair2.py, sheet.py + common.py, cloth.py, q_oci.py, tex_gen.py ze zena30.
  Pevné cesty /home/claude/... upravit (common.py UBC = Quaternius, tvar.py OUT).
- Náhledy zepředu a z profilu: tvare_1.jpg, tvare_2.jpg, tvare_3.jpg.

Licence: tělo, hlava, oči, obočí Quaternius CC0; posuny, textury pleti, vlasy, vousy a skripty vlastní tvorba (volně pro Tvrz).
Inspirace KCD jen obecně (věk, opálení, vrásky podle práce), nic nekopírováno.
