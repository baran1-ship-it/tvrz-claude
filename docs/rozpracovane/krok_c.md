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

## 5. Předloha KCD1/KCD2 (docs/screens/kcd1, ref_kcd2_*) – kameny, rostliny, cesty
- **Cesta (kcd1_03, kcd1_33, ref_kcd2_cesta_les):** povrch je hlína se štěrkem **v textuře** (drobné kamínky jen jako povrch, ne 3D). 3D kameny leží **na kraji** a za krajem: snosy polních kamenů u cesty a meze, větší balvany v trávě u krajnice. Hřbet mezi kolejemi travnatý, v kolejích nic. Okraj cesty = vysoká tráva s květy (vlčí mák, chrpy), kapradí a mladé smrčky v lese.
- **Louka a mez (kcd1_03):** kamenná mez / snos kamení podél cesty a polí, na ní tráva a keře; jednotlivé stromy na mezi, za nimi les jako stěna.
- **Ves (kcd1_22):** dvůr udusaný, pár kamenů u zdí a podezdívky, sudy, stůl, kůlna; tráva jen u zdí a v koutech.
- **Pravidla z toho (krok C, data):**
  - `_cesty_kameny`: 3D kamínky jen na krajích hlíny (pás kraj ± 0,5 m), hřbet a koleje 0 (povrch = textura). Rozpor s pásmy pak zmizí. Stačí upravit hodnoty rádce 18:00 (hřbet 0,4 a koleje 0,2 → 0), test a skupiny zůstanou.
  - Meze a snosy kamení podél cest a polí jako záznam v `plochy.json` (mez = pás 2–4 m na hranici lánu nebo cesty: kameny + keře + tráva + občas strom).
- **„Plné scény“ / svět jako místnosti** (Míša 26. 10. 21:00–21:10): popředí a střední plán plné (lem lesa z keřů do výšky chlapa, meze, ploty, sady), výhled do dálky jen ze skal a z věže. Úspora: co zakryje lem a terén, se nekreslí (okluzory, dosahy tříd), takže se kreslí míň než dnes s holými kmeny a prázdnou plání. Rozpočet tabletu ≤ 700 kreslení a ≤ 1,5 M troj. na záběr, měří `mapa_vyhledu` před a po.

## 6. Předloha KCD – cesty ve svahu, vodní toky, les (kcd1_05, _14, _26, _38, ref_kcd2_ves_rybnik, _louka_les)
- **Cesta ve svahu (kcd1_05):** na straně do kopce zářez (úvoz) s obnaženými kameny a hlínou ve svahu zářezu, na straně z kopce lem kamenů v trávě. Kamínky jen u krajů, ve stopě nic. → `cesty`: úvoz = svah zářezu se stanovištěm „kamenitý svah“ (kameny 0,2–0,6 m napůl v zemi), lem kamenů na dolní krajnici.
- **Příchod k bráně (kcd1_14):** ploché kameny napůl zapuštěné u krajů, štěrk ve stopě jen jako textura.
- **Potok a strouha (kcd1_26):** voda tmavá, na klidné vodě lekníny a okřehek, břeh podemletý (hlinitý stupeň), na něm vysoká tráva a rákos; podél vsi proutěný plot (`withe_fence.glb` od Míši). → malé toky: hladina s okřehkem a lekníny v klidných úsecích (spád < 1 %), břeh = stupeň 0,3–0,5 m (`toky_tvar.breh_m`), rákos a vysoká tráva v pásu 0–1,5 m od vody.
- **Rybník u vsi (ref_kcd2_ves_rybnik):** přes přítok lávka z kulatin, blátivá cesta k vodě, rákos, ploty. → přítok Lhoty pod pěšinou: lávka z kmenů (most/brod se odvodí z křížení toku a pěšiny).
- **Les (kcd1_38, ref_kcd2_louka_les):** listnatý les hustý od země (mladé stromy, keře, podrost), kmeny teprve uvnitř; okraj lesa = souvislá stěna zeleně; ve svahu obnažená půda a kameny. → potvrzuje „plné scény“: lem lesa z keřů a mladých stromů, uvnitř podrost.
