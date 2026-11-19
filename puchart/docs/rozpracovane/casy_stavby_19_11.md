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
