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
| 10 | Za rychtou není plot (košár: plůtky jen kus) | (406,833) | snímek košáru zblízka |
| 11 | Potok furt jak vybagrovaný – rovné úseky, ostré lomy; má mít přirozené zatáčky a meandry | (371,892), (446,921), (503,872), mlýn (573,893) | osa toků: meandry (křivolakost, poloměry), ne lomená čára |
| 12 | U mlýna neteče všude voda (suché úseky náhonu/koryta) | mlýn (588–616, 893–919) | voda v korytu po celé délce |
| 13 | Černý balvan ve vzduchu u rychty | (420,819) | visici |
| 14 | Váček/hroudy na louce (hnědý předmět) | (446,921) | ? |
