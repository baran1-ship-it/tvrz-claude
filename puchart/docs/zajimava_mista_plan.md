# Zajímavá místa ve výseku 2×2 km (Míša 15. 11. – vše schváleno)
Pravidlo: docs/historie_pravidla.md (dobová podoba, H/NAVRH smí). Předloha: KCD (místa za každým kopcem), Havran (hotové modely/skripty), pak internet. Každé místo = záznam v datech (mista.json / svet), zdroj, značka DOLOZENO/REKONSTRUKCE/NAVRH, kolize, LOD, test průchodu k místu, snímek.

1. Průzkumná štola ve stráni (Disk: Stara_stola_1393_REALISM – zmenšit, vstup v terénu) – NAVRH
2. Kříže u cest: kamenný smírčí kříž (13.–16. st., Morava) u cesty; dřevěný kříž na rozcestí; dřevěná boží muka (sloupek se stříškou) – REKONSTRUKCE/NAVRH
3. Milíř uhlířů (kouřící kupa, chýše) + smolárna/dehtárna v lese – rešerše kap. 9 (přiznaná rekonstrukce)
4. Mlýn na Veličce (Havran mlyn.glb, mlyn_kolo.gd, stavidlo/mletí) – B 1408 → už 1393
5. Malý lom na kámen hradu (lámavá stěna, odval, rumpál) – rešerše kap. 10 (rekonstrukční hypotéza)
6. Studánka s dřevěnou roubenkou pod skalou
7. Brtě (včelí úly vydlabané ve stromech) – středověké brtnictví
8. Poustevna pod skalním převisem ve skalním městě (ohniště, lůžko z chvojí) – lidová tradice (Kostelíček, H)
Pořadí: po dokončení rozpracovaných funkcí (kovadlina, seno, hrad, sklep krčmy) a hlídačích.

## Chýše do tvaru A jako zemljanky (Míša 15. 11.)
„Mezi modely byly chýše do tvaru A, líbily by se mi víc v Puchartu – mám je v lomu a u uhlíře v lese; zevnitř umazat
podlahu a postele, vykopat 2 schody do země a udělat zemljanku jako v KCD.“
- Model: domy.glb ChyseKura / ChysePrkna (Havran, NAVOD_CHYSE.md; Havran svet.gd VES_CHYSE – rozměry f/b/hw/rx).
- Použít u uhlíře (místo kuželové les_uhlir_chyse) a u lomu.
- Úpravy: odstranit podlahu a pryčny (ChyseKura/ChysePrkna_Kol_Prycna0/1 + síť), podlaha zapuštěná do země
  (~0,6–0,8 m, 2 hliněné/kamenné schody u vchodu dolů), stěny jámy hliněné, obložené kůly/proutím (KCD zemnice),
  ohniště uvnitř, terén proříznutý (díra v terénu + kolize), test průchodu dovnitř a ven.
- Předloha: KCD zemnice (uhlíři, lapkové) – najít fotky; dobová reference: zahloubené stavby (polozemnice) 13.–14. st.
- Vybavení (Míša 15. 11.): žádné postele – spalo se na zemi vlevo a vpravo na rohožích a houních (rohož z rákosí/slámy +
  vlněná houně, pevný díl modelu); proti dveřím na konci bedna (truhla z katalogu Havrana), pokud se vejde.

## Stav 16. 11. (postaveno)
Data `pravidla/svet/zajimava_mista.json` (hledání polohy, díly, terén, funkce; zdroj a značka u každého místa) →
`nastroje/zajimava_modely.py` (lesní díly modeláře do `hra/modely/les`, zemljanky `hra/modely/stavby_h/zemljanka_kura|prkna.glb`,
zkrácená štola `hra/modely/les/stola.glb`, brť) → `nastroje/zajimava_mista.py` (poloha z terénu, plošiny, zářezy, jámy, trasy
`hra/data/pruchody_zajimava.json`) → `teren_dlazdice.py` (otvory a snížená kolize z `build/zajimava_teren.json`) →
`hra/scripts/zajimava.gd` (LOD, kolize, kouř milíře a smolárny, ohně, kolo mlýna, kahany ve štole, víko kolize nad štolou).
Vše v `nastroje/postav_vse.sh`. Snímky `docs/screens/mista_*.png`, test `pruchod:zajimava_*` + `pruchod:zajimava_mista`.

| Místo | Kde (hra x, z) | Značka |
|---|---|---|
| Kříž na rozcestí | rozcestí S od Předhradí | NAVRH |
| Smírčí kříž | u vozové cesty z Kyžlířova | REKONSTRUKCE |
| Boží muka | u cesty k mlýnu | NAVRH |
| Uhlíř (milíř hořící + postavený, dřevo, nářadí, kára, zemljanka, ohniště) | les na plošině SZ | NAVRH |
| Smolárna | les ~100 m od uhlíře | NAVRH |
| Studánka | pramen přítoku Veličky na S | NAVRH |
| Brtě (borovice a dub) | kraj lesu u pěšiny | REKONSTRUKCE |
| Poustevna | pod skalami hřebene J od hradu | NAVRH |
| Lom (dno, stěna, kameny, kvádry, zemljanka) | svah nad vozovou cestou J od hradu | NAVRH |
| Průzkumná štola | strmá stráň V od vsi | NAVRH |
| Mlýn | břeh Veličky u soutoku | REKONSTRUKCE |
Přesné souřadnice: `hra/data/zajimava_mista.json`.
