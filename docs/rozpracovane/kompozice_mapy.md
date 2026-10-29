# Kompozice celé mapy – „plné scény“ (Míša 29. 10. večer: „udělej takhle ves, ale takhle musíme udělat celou mapu“)

Cíl: z žádného místa, kam hráč dojde pěšky nebo dojede na koni, není vidět dál, než oblast unese (kromě záměrných
výhledů). Co není vidět, se nekreslí (zakrývač u každé zábrany). Výkon i dojem z jednoho principu – svět jako
místnosti (KCD: zatáčka, remízek, stodola, mez, lem lesa).

## Výchozí stav (29. 10., `tools/mapa_vyhledu.py --krok 25`)
- Ves: 117 ze 136 bodů otevřených přes 130 m, průměrný dohled 235 m (`docs/screens/ves_dohled_pred.png`). Ves má
  8 domů 40–60 m od sebe, mezi nimi louka – není čím zavřít.
- Celá mapa: 31 z 506 bodů přes 300 m. Záznamů: 16 remízků, 5 výhledů.
- Kreslení (měření mer0995): let nad vsí 654, u chlívku 1151, mlýn 537 (rozpočet tabletu ~500).

## Mez dohledu podle oblasti (`lokace.json kompozice dohled_oblasti`)
| oblast | mez | proč |
|---|---|---|
| ves | 130 m | nejdražší pohledy (stavby, předměty) |
| les | 120 m | uvnitř plný, průhled jen světlinou/pěšinou |
| louky a pole | 200 m | okraj lesem, remízkem nebo mezí |
| cesty mezi lokacemi | 250 m | rytmus zavřeno → zavřeno → výhled |
| záměrné výhledy | bez meze | věž, Pustá skála, příjezd ke vsi/tvrzi/hostinci |

## Zábrany (každá je záznam v datech s důvodem, nikdy ruční výjimka)
- **Dvorec** (ves): dům + stodola za domem + chlév/kůlna do strany + plot dvora + sad za stodolou. Stodola zavře
  pohled napříč vsí, sad a ploty doplní. Modely: stodola a kůlna z Disku/Sketchfabu (CC-BY), jabloň, plůtky.
- **Zatáčka ulice a náves**: lípa a studna/kříž na návsi, ulice s ohybem – ze žádného bodu ulice víc než 4–6 domů.
- **Remízek** (meze, kamení, vlhko), **mez s keři** (hranice lánů, plužina), **lem lesa** (keře do výšky chlapa),
  **stromořadí u cesty**, **úvoz** (cesta ve svahu).

## Postup na každou oblast (pojistky, Míša: „bojím se miliardy chyb“)
1. Mapa dohledu oblasti → seznam otevřených bodů a směrů.
2. Návrh zábran z dat (generátor): zábrana jen tam, kde je logická (okraj pole, mez, za domem), s důvodem.
3. Test smyslu: zábrana ne na cestě, ve vodě, na svahu, ne přes záměrný výhled; každá chyba od Míši = nová kontrola.
4. Export → mapa dohledu znovu (cíl: 0 chyb v oblasti) → měření kreslení na pevných bodech (cíl ≤ 500).
5. Snímky z pevné sady záběrů (Míšina místa + pohledy do oblasti) před a po, porovnat vedle sebe, až pak vydání.

## Pořadí oblastí
1. Ves (dvorce, náves, zatáčka) – plánek Míše před stavbou.
2. Cesta tvrz – ves a okolí tvrze.
3. Mlýn, rybník Lhota, potoky.
4. Hostinec a stan, lom, skály a větrák, okraje mapy.

## Výkon (souběžně, měřeno na stejných bodech)
- Zakrývače domů (hotovo v kódu 29. 10.), zábrany dostanou zakrývač automaticky.
- Stíny: kratší dosah, stínují jen velké věci (měření: stíny −186 až −224 kreslení).
- Stavby vsi sloučit podle materiálů po dvorcích (měření: stavby −290 kreslení).
- Bez prolínání dosahů (hotovo 29. 10., `modely.json prolinani_dosahu`).
