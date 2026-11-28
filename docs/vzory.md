# Vzory toho, co se povedlo (pravidlo Míša 23. 11.)

Když se část hry povede (Míša pochválí, měření sedí), rozebrat, jak vznikla, a zapsat sem: co (místo, verze),
z čeho (data/pravidla – soubory a klíče), postup krok za krokem, čím ověřeno (snímky, testy, měření), na co pozor.
Podobná práce začíná přečtením vzoru.

## Seznam
- Voda v potoce (níže) – Míša 27. 11. na 0.9999999: „voda v potoce super“.
- Další kandidáti k rozboru: ves před 0.9999993 „ves byla super“ (Míša 18. 11.).

## Voda v potoce (0.9999999, pochvala Míša 27. 11.)
- **Co:** hladina Bystřice a malých toků (Hvozd vzhled), snímky `docs/screens/misa_27_11/`.
- **Z čeho:** `pravidla/svet/voda.json` – `vzhled_hvozd` (panorama odrazu, fresnel, tělo kraj/střed, alfa, vlnky, pěna),
  `potok` (osa od pramene k ústí, `min_spad`), `toky` (osa_xzy s hladinou), `toky_tvar` (koryto, jemný terén u vody);
  shadery `shaders/reka.gdshader` (pás podél osy toku, u = po proudu) a `voda.gdshader`; `scripts/koryto.gd`;
  odraz `obrazky/voda_odraz_les.jpg` (Poly Haven misty_pines, CC0, 2048×1024).
- **Postup:** 1) předloha ze světa (prohlížečový les Hvozd 18. 11.) rozložená na veličiny do JSON, ne čísla v shaderu;
  2) osa toku vždy ve směru toku a hladina jen klesá (logika „voda teče z kopce“); 3) odraz bez kopie obrazovky
  a bez druhého vykreslení (tablet): panorama + Schlick fresnel do EMISSION × globální `voda_svetlo` (v noci nesvítí);
  4) tělo vody hnědé u kraje → černozelené ve hloubce podle hloubky vrcholu, alfa 0,2 → 0,92, takže kraj splývá s dnem;
  5) jedna normálová mapa čtená dvakrát (dvě měřítka/rychlosti) + pěna ze šumu po proudu.
- **Ověřeno:** Míšiny fotky z tabletu 27. 11. (pochvala), fps „super“ (bez trávy) – měřicí trasa k verzi viz `mereni_verze.md`.
- **Pozor:** pochvala platí pro hladinu; břehy příkopu byly zubaté (chyba 27. 11. řádek 1 – drobné výmoly u čáry vody,
  bahno skokem). U nových vod: hladina z tohoto vzoru, okraj řešit profilem terénu (plynulý přechod bahno → tráva),
  nikdy ne posunem hladiny.
