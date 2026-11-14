# Kovárna a dům na konci návsi (Míša 14. 11.)

Zadání: „přidej do vsi jeden nový dům a k němu kovárnu… dej to někam do mezery, ať uzavíráme vesnici, ale rozumně,
ať to neopravujeme 60×“. Zdroj: Disk složka budovy `1O1VPNjyMNDCDxm4SB3nm64OKGnopwb5x`, `kovarna.zip`
(id 148Da9sHyjzBWpZO8qnjslZSLliEFsKzn, 61 MB – konektor > 10 MB nebere, `curl drive.usercontent … confirm=t`):
`kovarna.glb` (65 600 troj., textury 1024 vložené), `kovarna_lod1.glb` (116 troj.), NAVOD_KOVARNA.md, náhledy.

## Místo (plán vsi z dat: build/f_ves/plan_vsi.png)
- Konec ulice (osa končí ~ (413, 905)), západní strana naproti usedlosti 7 – ulice dnes „vybíhá do prázdna“; dům
  s kovárnou ji uzavře. Kovárna na kraji vsi k poli (oheň stranou od stavení – NAVOD „Historie“).
- Dům = náš Dum1 (selský dům, domy.glb) – v zipu je jen kovárna.

## Jak (bez záplat, jeden záznam)
1. Záznam `lokace.json ves.kovarna` {stred, natoceni, rovina_r_m, dum {typ, stred, natoceni}} – jediný zdroj
   pro Blender (rovinka terénu, cesta/pěšina k ulici) i hru.
2. Model jako díl (jako mlýn `voda.json mlyn.dil`): `res://modely/kovarna/kovarna.glb` + `kovarna_lod1.glb`,
   visibility 0–60 m / LOD1 od 55 m, kolize `-convcolonly` z modelu, značky: Ohen_bod (světlo bez stínu + částice
   + zvuk), Komin_kour, Kovar_stani, Kovadlina_misto (kovadlina z katalogu), Paka_uchop (dmýchat: páka + blend
   shape Nadech, t = 0,5 − 0,5 cos(2,5 t)).
3. Dům: další záznam v `_domy` (k 8) stejně jako chalupa mlynáře (lokace vetrak.chalupa) – zahrádka, dvůr, žebřík,
   místnosti jdou stejnou cestou.
4. Testy: zasazeni, test_smyslu (stavba ne na cestě/svahu/ve vodě), interier (tráva), duplicity, kolize_troj;
   snímky z ulice a shora před vydáním.
5. Postavy: kovář vsi (nová role) až po ověření stavby – ne v tomto kroku.

## Krčma do L (Míša 14. 11. odpoledne)
- Místo podle snímku Míši (zakroužkováno vlevo od odbočky k rybníku): `lokace.json krcma_l` střed (468,3; 813,4),
  natočení −0,7044 (+Z modelu = uliční strana k odbočce), stájové křídlo k rybníku. Studna odtud na náves vedle lípy
  (`ves.studna` 432/811). Odbočka = stará ulice, dotažena k břehu rybníka (`cesty.json pesiny k_rybniku`).
- Stará krčma U Kohouta (usedlost 0) zůstává jako obyčejná usedlost bez štítu (`ves.stara_krcma_obycejna`).
- Přestěhování postav (po ověření stavby snímkem): místa krcma_senk / krcma_obsluha / krcma_opreni / krcma →
  šenkovna (464,9; 810,5), hospodský u výčepu (465,4; 811,3), šenkýřka za výčepem (466,9; 811,8), opření venku
  u průčelí (461,4; 815,4); dveře `Pohyb_krcma_Vchod` (síň) a `Pohyb_krcma_Senkovna`; místnosti krčmy do dat
  mistnosti (šenkovna, síň, kuchyně, jizba, pokojíky); stoly a lavice z katalogu do šenkovny (nabytek.json).
