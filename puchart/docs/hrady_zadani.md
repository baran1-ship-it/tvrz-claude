# Hrady – zadání návrhů (před stavbou ke schválení Míšou)

Míša 29. 10.: „Až budeš stavět hrad, chci vidět návrhy. Drž se stylu KCD a reálné – nemáme přesnou podobu, takže nemusíme
být ortodoxní – a uděláme je **propojené a krásné**.“

## Co víme (DOLOZENO – atlas [2], DMR 5G)
- Dvojice samostatných, plně funkčních hradů na ostrohu nad soutokem Veličky a Kouteckého potoka.
- **Přední hrad** (439 m n. m.): větší plocha, mohutný val a okružní příkop (na DMR 5G je vidět oblouk příkopu na SZ),
  v čele plošiny věž = hlavní obranná stavba, za její zdí palác, několik budov.
- **Zadní hrad** (~406–411 m, o ~30 m níž po hřebeni k JV): lichoběžník, skalní průrva, **hranolová věž**, palác.
- Spojnice vedla po úbočí hřebene. Nikdy nezkoumáno archeologicky.

## Co si dovolíme (NAVRH – přiznaná volná rekonstrukce)
- **Propojení:** spojnice jako krytá dřevěná chodba / ochoz na kamenné zdi po úbočí, s branou na obou koncích
  (ne rovná třída – tvar podle úbočí, PDF kap. 6). Hráč projde z jednoho hradu do druhého bez sestupu do údolí.
- Výrazná silueta z údolí: vysoká věž předního hradu, hranolová věž zadního, střechy v různých výškách po hřebeni.
- Hrady udržované a obydlené (KCD Rataje, Pirkštejn – lidské měřítko): omítka místy, šindel, pavlače, dřevěné
  nástavby, hospodářské přístavky, ne zřícenina ani pohádkový zámek (PDF kap. 5 „Co nevytvářet“).

## Návrhy, které připravím (každý: půdorys nad DMR, pohled z údolí, z nádvoří, ze spojnice)
1. **„Strážný hřbet“** – přední hrad s okrouhlým plášťem? NE: věž v čele hranolová (podloženo jen u zadního), přední
   s mohutnou čtverhrannou věží nad příkopem, spojnice jako krytá hradba s ochozem.
2. **„Dvě koruny“** – oba hrady s palácem a věží, spojnice dřevěný krytý most přes skalní sedlo + parkán.
3. **„Hospodářský dvůr“** – mezi hrady předhradí se stájemi a kovárnou na úbočí (hospodářství PDF kap. 3–4).
Varianty se liší propojením a siluetou, ne historickou jistotou. Míša vybere nebo zkombinuje.

## Postup (PDF kap. 6 + stavebnice Havrana)
1. Nad DMR zakreslit známé (příkop, val, plošiny, skála) s mírou jistoty → `pravidla/svet/hrady.json`.
2. Hmoty v metrech (šedé), projít hráčem, ověřit zásobovací cestu a spojnici.
3. Střechy a hmoty paláců, silueta z údolí i z dvora → **snímky návrhů Míše**.
4. Po schválení: místnosti a úseky k načítání, pak portály, trámy, omítka, vrata, mobiliář.
Stavebnice: Havran `blender/kit.py`, `fort.py`, `palace.py` (lomové zdivo, kvádrová nároží, šindel, ochozy, dveře na pantu).
