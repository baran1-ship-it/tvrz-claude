# Stav 29. 10. večer (po vydání 0.995) – Míša: „po vydání zastav všechny práce a dopiš vše do repa“

## Vydáno
- **0.995** (`tools/vydani.py 0.995 --testovaci --jen z_svet,z_rostliny,z_reka,z_katalog,z_zvirata`), export 0995c
  prošel všemi branami (test smyslu před i po).
- Opraveno a ověřeno snímky z Míšiných míst (`build/f121/*.png`, tabulka `misa_0994_chyby.md`):
  - Mlýn a, b: voda v potoce i v lednici navazuje.
  - Kanál pod mlýnem: `kraj.py` – dno toku je záznam a terén v korytě neleží pod hladinou minus hloubka.
  - Příkop a odtok rybníka.
  - Prasata (rozestup).
  - Ploty za domy (LOD).
  - Okolí po cestování se načte pod zatměním.
  - Chůze a ocásek ovcí a slepic ověřuje jen test.

## Zbývá z tabulky 0.994 (viděno na snímcích f121)
1. **Mlýn c (598, 904):** schodovitý okraj vody v místě, kde lednice vtéká do potoka. Příčina zatím nehledána.
2. **Přítok do rybníka za tvrzí (−128, −167):** kamenná stěna se svislým schodem do vody.
3. **Potok ve vsi (489, 895):**
   - Zubaté okraje koryta.
   - Velká holá zelená plocha bez trávy na místě staré usedlosti 7 (483, 886).
   - Podezření: `louka._vzorek` → `svet.v_zahrade` (staré zahrádky), nebo kryti či pěšina z Blenderu (stará ves).
   - Test je připravený v `docs/rozpracovane/ves_b/test_louka_bod.gd`. Vložit ho do `tools/test_svet.gd` a přidat
     `louka_bod` do seznamu testů. Spuštění: `TVRZ_CO=480,860,540,905 tools/beh.sh t_lb testy louka_bod`. Mřížka
     vypíše hustotu a důvody (Z zahrada, N nová zahrada, P průchod, V voda, B budova).
4. **Cesta ve vsi (413, 781):** zubaté zelené pruhy na hlíně ulice. Jde o schodovité okraje barvy terénu po přesunu
   usedlostí (maska `trava_ves`, `svet._vo_data`).
5. **Sekání (měření 0995c, PC):**
   - Ves na cestě má 1205 kreslení, z toho stavby −583 a stíny −367.
   - Další krok: slučovat stavby po dvorcích podle materiálu (ne celou ves).
   - Stíny na tabletu už mají jen 40 m; zkrácení jen se souhlasem Míši.

## Ves B (rozpracováno, NEZAPOJENO)
- Záznam: `pravidla/svet/lokace.json`
  - `ves.dvorec` – pravidla: stodola, kůlna, sad, živý plot, zeleň u stavení, lípa.
  - `ves.dvorec_zaznam` – výstup `python3 tools/ves_dvorce.py --zapis`: zrcadlení, stodoly a kůlny v novém rámci,
    96 jabloní za humny, 80 keřů bezu, lípa na návsi.
- Modely: `blender/vlastni.py` stodola, stodola_mala, kolna (katalog `predmety.py`, šindel `tools/sindel_tex.py`).
- **Úpravy kódu:** `docs/rozpracovane/ves_b/ves_b_patch.py`. Mění `vesnice.py` (stodola a kůlna jako VYBAVENI
  ve starém rámci, placka terénu, chlév pryč), `nove.py` (jabloň do STROMY, `zaznam`, NOVY_RAMEC), `veg.py`,
  `export_game.py` (svet.json `rostliny_ves_novy`), `impostory.py` (jabloň), `svet.gd` (`_ves_rostliny_novy` před
  `_plants`) a `test_smyslu.py` (kontrola dvorce).
  - Ověřeno nanečisto na kopii souborů.
  - Spuštění: `python3 docs/rozpracovane/ves_b/ves_b_patch.py`.
- **Po zapojení:**
  1. Test smyslu.
  2. Export.
  3. `/opt/bl/bin/python blender/impostory.py jablon`.
  4. Snímky vsi před a po z pevné sady.
  5. Měření kreslení A/B.
  6. Vydání s `p_stodola,p_kolna`.
- Předzahrádka (květiny) ještě není.

## Pravidla od Astry (zapsáno v `kompozice_mapy.md`)
- Zakrývače jen přes pevné tvary. Remízky a les jsou vypnuté daty (`pasma.test.okluzor_listi` false).
- Mapa dohledu odděluje pevné zakrytí a listí.
- Ves B bez domů navíc.
- Přejímka na tabletu: p95/p99, A/B okluze.

## Prostředí
- Disk: per-session limit. `git worktree` celého repa snědl místo (export 0995c nespustil) – nezakládat
  (`predani.md`).
- Předmeandrové osy toků (vstup `toky_meandry.py`): `docs/rozpracovane/ves_b/voda_old_pred_meandry.json` (dříve jen
  ve scratchpadu).
- Míša: Terrain3D teď ne, jen kdyby měření ukázalo terén jako hlavní brzdu.
