# Zadání pro modeláře: tváře 32 vesničanů (Míša 13. 11.)

Technicky (nutné)
- Základ Quaternius Universal Base Characters jako zena30. Síť hlavy NEPŘESTAVOVAT – stejný počet a pořadí vrcholů
  (váhy kostí, mrkání q_oci.py, UV atlasu).
- Dodat jako deformaci stylem tools/zena30/face.py (OPS: střed, poloměr, posun/měřítko) pro každou postavu, nebo tvarový
  klíč na původní síti.
- Pleť jen úprava barvy (vrásky, opálení, ruměnec, strniště); atlas postavy 512 px.
- Vousy a vlasy stylizované chomáče jako zena30, bez průhlednosti (tablet), vlasy + vousy do ~1 500 troj.

Postavy: 32 lidí, role a věk v tools/postavy_q/postavy.json (rychtář, kovář, hostinský, stráž, pastýř, ponocný,
mlynář, sedláci, chalupníci, pacholek; kuchařka, šenkýřka, selky, pasačka, bába, dívka; hoch). Každý na první pohled
jiný (nos, čelist, lícní kosti, oči, obočí, věk); venkovní práce = opálení a vrásky.
Inspirace KCD (docs/reference/kcd_13_11/), nic nekopírovat.
Dodat: skript/data deformací pro každou postavu, náhled zepředu a z profilu, licence zdrojů.
