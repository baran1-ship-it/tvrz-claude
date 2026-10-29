# Míša 0.992 (29. 10. odpoledne) – 20 snímků + záznam měření

| # | Co | Kde | Kontrola / postup |
|---|----|-----|----------|
| 1 | Sekání (FPS 10–30, záseky kreslení 40–100 ms skoro všude, 605 ms u mlýna) | celá mapa; nejhůř les u rybníka za tvrzí (-155,-209) FPS 10, ves (406,833) | měření A/B, rostliny + stíny (krok: LOD/impostor, rozsah stínů) |
| 2 | Sud ve vědru v kovárně (káď z katalogu = necky se sudem) | kovárna (-15.6, 13.2) | **opraveno**: z lokace.json kovarna_tvrz pryč |
| 3 | Postava drží ruce, jako by něco nesla (má se přirozeně hýbat) | most (0,19) | **opraveno**: postavy.json činnost „nosi“ měla chůzi Walk_Carry_Loop bez neseného předmětu → Walk_Loop |
| 4 | Postava zase šla přes zeď | tvrz, ves | test `vztahy_hra` nově kontroluje každý úsek chůze paprskem (`zed|postava`); lide.gd `_volno`: spojka mezi osami cest jen bez zdi |
| 5 | V příkopu chybí voda (suché dno, kameny) | příkop (-24,19) | voda_v_korytu příkop |
| 6 | Rybník za tvrzí levituje (hladina nad břehem, sráz) | (-156,-148) | hladina vs. terén na obvodu |
| 7 | Napojení přítoku / odtoku rybníka: plochá deska štěrku do vody (potřetí!) | (-129,-165) | **data**: přítok končil 2 m uvnitř rybníka (koryto a hladina toku pod hladinou rybníka = deska); `toky_meandry` nově ořízne osu na hraně vody (`kraj.ryb_polomer`), `toky_hladina` drží konec na hladině rybníka; `kraj.voda_tvar` břeh lesního rybníka ne pod hladinou, náspy toku i u rybníka mimo vodu. Čeká na export. |
| 8 | Slepice nehýbou nohama | dvory | Míšiny modely s kostrou (modely/zvirata, Sketchfab); bez klipu chůze → zvirata.gd houpe kosti nohou (zvirata.json nohy) |
| 9 | Ovce a prase jen „rastry“ (zmenšení zničilo texturu) | košár, chlívky | nahrazeno Míšinými modely (ovce ap-school, prase kenchoo) s vlastní texturou |
| 10 | Za rychtou není plot (košár: plůtky jen kus) | (406,833) | plot stál, ale 0,7 m plůtek zmizel v 0,7 m louce (snímek f112) → ohrada je spasená: `louka.gd _nizka` uvnitř a 1 m kolem jen nízká tráva (`zvirata.json seslapano_m`); hlavní příčina: automatické LOD importu mazalo tenké pruty od ~12 m → `predmety.gd` plůtek ohrad `lod_bias` (test `ohrady`), snímek f116 celý plot ✓ |
| 11 | Potok furt jak vybagrovaný – rovné úseky, ostré lomy; má mít přirozené zatáčky a meandry | (371,892), (446,921), (503,872), mlýn (573,893) | osa toků: meandry (křivolakost, poloměry), ne lomená čára |
| 12 | U mlýna neteče všude voda (suché úseky náhonu/koryta) | mlýn (588–616, 893–919) | **data**: náhon začínal 0,87 m nad hladinou potoka (voda do něj nemohla) → `toky_hladina` jez u vtoku náhonu (bod toku pevný v hladině náhonu); lednice (odpad z kola) končila 1,4 m od potoka → `kraj.py` ji dovede do osy toku. Čeká na export. |
| 13 | Černý balvan ve vzduchu u rychty | (420,819) | test `visici` ve vsi nic nad 0,6 m nenašel; na snímku f110 u (432,821) tmavý předmět na zemi – po vydání ověřit |
| 14 | Váček/hroudy na louce (hnědý předmět) | (446,921) | ? |
