# Krok C – zasazení (rozpracováno při exportu 0.97, zapojit po vydání)

Výchozí stav: test `zasazeni` po zámku terénu (export 15:01) hlásí 11 343 chyb.

## 1. Kamínky na cestách – rozpor dvou pravidel (≈ 9 000 z 9 102 „bylin v pásmu“)
- `pasma.skupiny.popis`: „nízké byliny … a kamínky jen mimo jízdní pás (0)“.
- Rádce 18:00 bod 3 (`svet._cesty_kameny`): kamínky 5–20 cm jako modely na cestě (kraje 1,5/m², hřbet 0,4, koleje 0,2) – hra je tam klade záměrně.
- Návrh: nová skupina `povrch_cesty` = [`kamen_maly`] s odstupem `-inf` (patří na hlínu). Větší kameny (`kamen_zula`, `kamen_piskovec`, `kamen_droba`, 0,4–1,4 m) přidat do skupiny `balvan` → mimo pás a ker_od_m. Na hlíně jich je z Blenderu ~30, to je pak skutečná chyba.
- Byliny na hlíně přímo z Blenderu: `divoka_trava` 77, `grass_medium` 28, kopřivy 20, pampelišky 9, keře 10, smrk 3 (data Blenderu). Hra je má odstranit v `_cesty_rostliny`. Co zůstane, přidávají až rozsevy hry po něm → rozsevy volat přes `smi_tu_byt` s pásmem cest (místo mazání stanoviště, pipeline zásada 4).

## 2. Visí stromy a keře (≈ 600)
- Rostliny na skalách a balvanech: test je už vynechává (jejich kolize se načítá jen kolem hráče).
- Kolize terénu se teď staví z hotové sítě (zámek). Zbytek ověřit po exportu 0.97: `_na_zem` posouvá jen rostliny mimo pás ±0,25 m, test hlásí nad 0,30 m.

## 3. Nad cestou (32 vozová, 25 pěšina) – vypsat, co to je (kolize objektu nad osou cesty).

## 4. Míšovy poznámky z 0.95 (data, ne záplaty)
- Hlína kolem kupeckého stanu: dvůr stanu jako plocha `udusano` v `lokace.json` (jako placek hostince), ne zelený čtverec.
- Strom u prvního domu vpravo moc velký: druh a velikost z tabulky (`modely.json` třída), ne ručně.
- Cestička k rybníku moc široká a jiná textura: šířka v `cesty.json` `pesiny_odvozene` podle tabulky pásem pěšin; povrch stejný jako u pěšin.
- Rastr bylin u (415, 917): rozsev bez mřížky (zjistit, který rozsev).
- Šířka cestiček 0,75 m natvrdo v `_cesty_tvar` → `cesty.json`.
