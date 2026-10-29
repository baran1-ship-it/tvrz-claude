# Míša 0.994 (29. 10. večer) – 17 snímků + záznam měření

Míša: „podívej se pořádně na ty fotky, to je furt dokola“. Pravidlo od teď: každá oprava se ověří snímkem **z Míšiny
polohy a směru** (HUD: x, z, výška, pohled; J = +z, S = −z, V = +x, Z = −x), ne z vlastního místa, a snímek se porovná
s jejím vedle sebe.

| # | Co | Kde (Míšin snímek) | Kontrola / postup |
|---|----|-----|----------|
| 1 | Příkop: v části chybí voda (suchý výběžek dna/břehu) | (-27, 27) výška -1,8, pohled SV | snímek f117 z její polohy potvrdil: na mírném břehu pruh 1,2 m hloubky skoro průhledné vody (dno prosvítá = „chybí voda“) → `voda.json stojata_melko_m` 0,3 (shader `melko_m`) |
| 2 | Rybník za tvrzí: napojení přítoku „peklo“ – koryto končí hranou/schodem a šedou deskou před tmavou vodou | (-128, -167) výška -1,9, pohled S (shora) | snímek; břeh rybníka u přítoku (pravidlo břehu z 0.993 zvedlo okraj) |
| 3 | Rybník za tvrzí: odtok / hráz | (-171, -162) pohled SV | snímek z její polohy |
| 4 | Prasata se navzájem prolínají | chlívek (412, 802) | rozestup podle velikosti zvířete (prase 1,5 m, ne 0,8 m) |
| 5 | Ovce a slepice nechodí, „sáňkují“ | košár (402, 829), dvůr (434, 901) | test `zvirata_chuze` (otočení kostí nohou za chůze) |
| 6 | Ovce má nepřirozeně zvednutý ocásek | košár | klidová póza ocasu z dat |
| 7 | U některých domů chybí zadní ploty – nejdou projít, kolize tam je, ale nejsou vidět | ves (404, 827) a jinde | stejná příčina jako plůtky košáru: automatické LOD tenkých plotů ve světě (tvrz.glb) |
| 8 | Mlýn: napojení vody pořád stejná chyba (náhon, potok, lednice: šedé desky, schody, suchý štěrk) | (589, 892), (583, 886), (598, 904), (613, 921) | snímek f117 potvrdil šedou desku: hladina potoka v dílu mlýna pod dnem koryta modelu (na výtoku o 0,4 m), osa ujetá o 0,3–0,8 m, za dílem lom 90° → osa a hladina v dílu = koryto modelu + 0,25 m (`mlyn.dil.potok_hladina_m`), oblouk 6 m na obou koncích (`potok_napojeni_m`), hladina za dílem plynule v pásu napojení. Čeká na export a snímky f118. |
| 9 | Potok ve vsi: zubaté okraje koryta, voda se rozlévá přes louku | (489, 895), (505, 871) | lhota_potok na náspu (toky_hladina: 52 bodů, až 1,23 m) |
| 10 | Holé fleky a zubaté zelené pruhy na cestě ve vsi | (413, 781) | maska povrchu vsi |
| 11 | Sekání: 20–40 FPS, záseky kreslení 50–130 ms ve vsi a u mlýna (let), jeden 791 ms u (463, 914) | záznam měření | rozbor kreslení |
| 12 | **Břeh pod mlýnem u odtoku ve vzduchu** (Míša: „posílala jsem 3×“) – šedé stupně/desky nad korytem u lednice a potoka | (598, 904) pohled JV, (613, 921) | snímek z její polohy, výška terénu dílu mlýna vs. břeh toku; kontrola v testu `visici`/`breh_toku` pro díl mlýna |
| 13 | Po rychlém cestování (i při chůzi) se oblast dokresluje před očima – zelené kopce, tráva doroste až potom | kdekoli | `main.fast_travel`: pod zatměním `louka.nacti_okoli()` a čekání na `okoli_hotove()` (max `hrac.json cestovani_cekat_max_s`); při chůzi předstih načítání 4 → 8 s |
