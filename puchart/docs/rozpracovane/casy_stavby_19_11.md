# Co nejvíc zdržuje stavbu hry – statistika 17.–19. 11. 2026 (Míša 19. 11.)

Zdroj: logy export_apk.sh (hlídači, 11 běhů 17.–19. 11.), časy pomocníků (oznámení o dokončení), git log od 10. 11.

## 1. Hlídači před APK – jeden plný běh ≈ 85 min
| krok | čas | podíl |
|---|---|---|
| test průchodu + hlídač scén (souběžně) | 4 255 s ≈ 71 min | 83 % |
| geometrie (kontrola glb, Blender) | 265–295 s ≈ 4,7 min | 5,5 % |
| měření (zkrácené) | 102 s | 2 % |
| test smyslu | 18–58 s | <1 % |
| klik/dotyk/louč/ohně/mapa/nabídka/automatika (8 testů) | 8–37 s každý, ≈ 3 min | 3,5 % |
| import, skripty, spoje, tabulka chyb | do 20 s | <1 % |
| data balík + APK (po hlídačích) | několik minut | – |

Test průchodu = 128 tras + pevné testy (dosah, strom_kolize, povrch_kolize, lavice 75, žebříky 24 …) v JEDNOM procesu Godotu
na softwarovém kreslení (llvmpipe, 1–2 FPS) – stroj má 4 jádra, průchod využije ~1,1 jádra.

## 2. Ztracené běhy 17.–19. 11.
11 plných běhů, z toho 5 nevedlo k APK: 2× neprošli hlídači (lávka/lůžka 17. 11., test karty 10,62 s 17. 11.),
2× restart kontejneru uprostřed, 1× zastaveno kvůli stáji (19. 11.). ≈ 5 × 85 min ≈ 7 h čekání navíc.

## 3. Pomocníci (práce na úkolech)
Typický úkol 20–95 min (medián ≈ 55 min): výkon/houštiny 95 min, tráva Havran 90 min, hlídač dosahu 85 min, hrady 71 min,
voda/mlýn/mapa 66 min, ves 57 min, VRAM 64 min, menu 54 min, G2–G4 55 min, zdivo 19 min.
Uvnitř nich nejvíc času: přestavba terénu celým řetězem (cesty → … → dlaždice → import, ~10–20 min), snímky (každý
1–3 min, PC kreslí softwarově), dílčí trasy průchodu (1–5 min každá), čtení velkých souborů.

## 4. Snímky
Jeden snímek = spuštění celé hry (načtení světa) + 1–3 min. Na úkol 4–12 snímků → 10–30 min jen focení.

## 5. Režie
99 commitů od 10. 11., z toho 24 „průběžný stav“ (hlídač stop hooku chce commit po každé odpovědi) – málo času, ale
přerušuje práci. Restarty kontejneru (3× za 3 dny) ruší běžící hlídače.

## Návrhy (seřazeno podle úspory)
1. **Průchod rozdělit do 3 souběžných procesů** (4 jádra; trasy hradu / vsi a míst / pevné testy): 71 → ~25–30 min. Úspora
   ~45 min na každý plný běh.
2. **Přeskočit trasy, jejichž vstupy se nezměnily** (otisk dat a modelů trasy; „dobrá verze“ už existuje): u malých oprav
   běží jen dotčené trasy – plný běh jen před vydáním po větších změnách. Úspora typicky 50–70 min.
3. **Geometrie jen pro změněné glb** (otisk souboru): 4,7 min → pod 1 min při malé změně.
4. **Odolnost proti restartu kontejneru**: hlídači zapisují výsledek po každé trase a po restartu pokračují, ne od nuly.
5. **Snímky dávkou**: jeden start hry, víc poloh za sebou (dnes 1 start = 1 snímek) – 10 snímků za ~4 min místo ~20.
6. **Přestavba terénu jen od změněného kroku** (dnes často celý řetěz).
Odhad: plný běh hlídačů 85 → ~35 min, běžná oprava se snímky a vydáním z ~2,5 h na ~1 h.

## Výsledek 19. 11. – skupiny tras a otisky (návrhy 1–4, částečně 5)
Míša 19. 11.: „když upravujeme jen hrad, tak není třeba procházet celý svět“. Pravidla `pravidla/svet/hlidaci_skupiny.json`,
nástroj `nastroje/hlidaci_skupiny.py`, otisky + výsledky posledního úspěšného běhu `build/hlidaci_otisky.json`.
- Skupiny: svet (dosah, kmeny, povrch, mapa, nevylézt, cesta mezi hrady; i trasy bez skupiny), hrad_A (+ vrata), hrad_B,
  ves (domy, pavlač, půdy + pevné testy vsi), ves_venku (výstupy, topeniště; stejné vstupy jako ves, rozdělena kvůli souběhu),
  zajimava, voda (lávky, most 440). Sdílené vstupy (kód hry vč. test_pruchod.gd a hrac.gd, scéna, shadery, výšky terénu pro
  hru, kontroly_hra.json) = všechny skupiny. `HLIDACI_VSE=1` = vše znovu.
- Souběh 3 procesy Godotu (PUCHART_TRASA + PUCHART_JEN na skupinu), od nejdelší skupiny; výsledek skupiny se zapíše hned
  (restart = další běh převezme hotové); sloučení do build/pruchod.json, PRUCHOD_UPLNOST kontroluje i trasy topení/vody/míst.
- Geometrie: kontrola jen glb se změněným otiskem (glb + pravidla geometrie + skript, u modelů na terénu i vysek.r16).

| běh | celkem | průchod + scény | geometrie |
|---|---|---|---|
| dřív (1 proces) | ≈ 85 min | 4 255 s | 265–295 s |
| plný (vše znovu, 3 souběžně) | 74 min | 3 813 s | 302 s |
| bez změn (vše převzato) | 7 min | 81 s (jen scény) | 4 s |
| změna jen hrad_puchart.json (hrad_A + hrad_B) | 24 min | 1 143 s | 1 s |

Trvání skupin v plném běhu (3 souběžně): svet 2 821 s, ves 2 134 s, hrad_A 1 980 s, zajimava 1 679 s, ves_venku 940 s,
hrad_B 896 s, voda 575 s. Souběh plný běh zrychlil jen o ~7 min: llvmpipe je vázaný na CPU, se scénami běží 4 Godoty na 4 jádrech
a každý proces se zpomalí (hrad_A sám 1 143 s, v souběhu 1 980 s). Úspora je hlavně v převzetí.
NEOVERENO: souběh 2 místo 3 (možná stejně rychlý); restart uprostřed běhu (převzetí ověřeno jen během bez změn); dosah
a pevné testy vsi závisí ve skutečnosti na celém světě – při změně hradu se nepouští (rozhodnutí Míši), před vydáním velkého
updatu pustit `HLIDACI_VSE=1`.
