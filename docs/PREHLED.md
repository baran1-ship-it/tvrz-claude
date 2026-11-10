# PŘEHLED – Odkaz Havrana na jednom místě (10. 11. 2026, stav větve `claude/new-session-0dtk58`, commit c93248b)

Rozcestník a souhrn pro novou session i pro Míšu. Nic tu není z hlavy: každý bod odkazuje na zdroj (cesta v repu).
Kde zdroj sám říká „NEOVĚŘENO“ (na tabletu nezměřeno, snímkem neověřeno), je to tu taky. Podrobnosti vždy ve zdroji.
Pořadí čtení pro nový kontejner: `CLAUDE.md` → tento soubor → `docs/predani.md` (pasti a poučení) → poslední sekce
`docs/radce.md` → `docs/rozpracovane/misa_28_chyby.md` (otevřené řádky).

> **Ověřeno 10. 11. stavitelem:** konfliktní značky v `postavy.json` a `kun.gd` už v HEAD nejsou (`git grep` čisté,
> JSON platný); hlášení pomocníka bylo ze staršího stavu. Poučení: ve sdílené složce žádný `pull --autostash` ani `stash`.

---

## 1. Stav hry dnes

**Hra:** Godot 4.4.1, renderer GL Compatibility (OpenGL ES 3), Android tablet Xiaomi Pad 8 / Adreno 825; Čechy 1393
(tvrz, ves Lhota, hostinec, skalní město) – `docs/predani.md` úvod. Repo je jediná paměť, kontejner je dočasný.

**Verze:**
| co | hodnota | zdroj |
|---|---|---|
| poslední vydaná APK | **0.99995** (testovací, 9. 11. ráno, commit dd47f13) | `apk/OdkazHavrana-0.99995.apk`, `git log` |
| v kódu po ní | tablet 3D 75 %, vstup do budovy skryje svět hned (92abc9f) – **nevydáno, NEOVĚŘENO** | `pravidla/svet/kvalita.json` `meritko_3d` |
| podmínka dalšího vydání | Míša 9. 11.: „oprav všechno, co máš v tabulkách, a až potom se bude vydávat“ | `docs/rozpracovane/misa_28_chyby.md` konec |
| poslední funkční verze před přestavbou vsi | 0.998 = commit c2809da | `docs/predani.md` (2. 11.) |
| export světa | poslední OK 9. 11. 07:20 (ubytovna, metly); export ubytovny vpravo + sklep + krtince + stodola 7 **zatím neproběhl** (disk, fronta) | `docs/predani.md` „Voda 9. 11.“, „Stavby 9. 11.“ |

**Co je ve světě** (`docs/predani.md`, `pravidla/svet/lokace.json`, `voda.json`, `postavy.json`):
- Tvrz: palác, nádvoří, příkop s mostem, kovárna (model z Disku, CC-BY), zbrojnice, ubytovna čeledi a kuchyně (9. 11.),
  sklepení pod věží s kobkami (v datech a Blenderu, **čeká export**), korouhev ve větru (`shaders/latka.gdshader`).
- Ves Lhota v novém rámci z Blenderu (`lokace.json ves.blender_novy_ramec`), krčma U Kohouta, rybník Lhota jako díl
  (`blender/rybnik_dil.py`), ohrady z plůtků a zvířata (slepice, prasata, ovce – `pravidla/svet/zvirata.json`).
- Hostinec U Zlatého kola u hlavní cesty, lom s chýšemi a lešením, vodní mlýn na `lhota_potok` (594, 919), větrný mlýn,
  potok Bystřice s mostem a brody, rybník tvrze, zaniklá ves Doubrava, pole, les, skalní město.
- 32 obyvatel podle příběhu (dobové sady, ~7,5 tis. troj.), rozvrhy, lůžka, nábytek jako data
  (`pravidla/svet/nabytek.json`), kůň s výstrojí, tělo hráče v 1. osobě (`docs/rozpracovane/postavy_plan.md`, `docs/predani.md`).

**Co funguje (ověřeno testem nebo na tabletu):** záseky skriptů pryč (0.99995 na tabletu skripty 3–8 ms, dřív lide
692–957 ms) – `docs/mereni_verze.md` 0.99995; postavy nemají vliv na výkon (bez postav ≈ vše); voda bez „ledu“
(`voda_odraz`, test na PC); kůň přes most/brody/plavání (`kun_prekazky` OK 5. 11.); spánek vleže 32/32 (`lide_chovani`).

**Naměřený výkon na tabletu** (`docs/mereni_verze.md`, ms na snímek p50/p95; cíl 33,3 ms = 30 FPS):
| verze | podmínky | výsledek |
|---|---|---|
| 0.9995 | 3D 55–70 %, panel vypnut | p50 17–24, p95 ≤ 32 na všech 7 místech – první úplná tabulka |
| 0.99992 | studený tablet | vše p50 17–34 / p95 19–39; tráva bez stínu ≈ bez trávy; VRAM 849 MB |
| 0.99993 | studený / zahřátý / auto | studený p50 17–30; zahřátý p95 55–128; auto (30 FPS) p95 37–46; VRAM 902 MB |
| **0.99995** | **3D 100 %** | vše p50 25–57 (les 57, skály 49), p95 29–122; ves/mlýn/hostinec p50 25; VRAM 930 MB; špičky 0,5–1,7 s (kreslení) |
| 0.99996 (3D 75 %) | – | **NEOVĚŘENO NA ZAŘÍZENÍ** (nevydáno) |

Závěry z měření: sekání v pozdějších variantách trasy = škrcení teplem, ne obsah (0.9996–0.99993); cena trávy na tabletu
je téměř celá stínový průchod slunce (0.99992); 3D 100 % zdražilo les a louku (0.99995) – `docs/mereni_verze.md`.

---

## 2. Otevřené chyby a úkoly

**Tabulka Míšiných chyb** `docs/rozpracovane/misa_28_chyby.md`: 87 řádků (1–88, 4+5 spojené). Strojově ze sloupce Stav:
16 řádků „čeká export“, 25 obsahuje „NEOVĚŘENO“, 6 „měřicí trasa“. Ruční třídění po oblastech (moje čtení, přibližné):
| oblast | řádky | stav |
|---|---|---|
| Voda (toky, rybníky, mlýn, příkop) | 1–3, 13, 15, 20, 25–26, 32–36, 51, 53–54, 61, 79 | opravy v datech/Blenderu hotové, **většina čeká export** (1, 3, 15, 33–36, 51, 53, 61, 79); 54 mlýn test OK |
| Terén a krajina | 9, 16, 37, 38 | 16 test OK po exportu (snímek NEOVĚŘENO), 37 čeká export, 9 výhledy otevřené |
| Stavby, předměty, zasazení | 4–8, 10–12, 14, 17, 19, 27–30, 39–40, 49, 55–56, 60/77, 64–69, 78, 80, 84–85, 87 | většina opravena testem; čeká export 39, 60/77, 67/78, 68 (krčma), 85; otevřené 49 (deska nenalezena), 80 (snímek sadu), 87 (statika jen tvrz) |
| Kůň a hráč | 18, 21–24, 41–45, 50, 62, 73 | v kódu s testy; 21–24 „ověřuji“, 50/62 sedlo snímkem NEOVĚŘENO |
| Postavy a zvířata | 46–48, 57, 59, 63, 70–71, 82–83 | 47 úchop podle klipu rozpracován, 48 krumpáč obouruč nezačat, 83 kovář NEOVĚŘENO |
| Výkon | 31, 52, 58, 72, 74–76, 81, 86, 88 | 74–75 ověřeno na tabletu; 76 opraveno (ohně bez stínu); 81/86 3D 75 % NEOVĚŘENO; 88 tráva v lese podle světla – v kódu (commit 21ba425, `pravidla/svet/les_podrost.json`), v tabulce pořád „ZADÁNÍ“ |

**Nejdůležitější teď:**
1. **Export** (ubytovna, sklep, krtince, stodola 7, odtoky za hrází, břeh Lhoty, dil kryti) – bez něj ~16 řádků visí
   na „čeká export“; potřeba ≥ 1 GB disku (`pasma.test.export_volno_mb`) – `docs/predani.md` „NEOVĚŘENO (9. 11. večer)“.
2. Po exportu znovu `kryti.bin` (louka) – `docs/predani.md` „Voda 9. 11.“ bod mlýn.
3. Tabletová měřicí trasa s 3D 75 % (ř. 81, 86) a varianty les_bez_travy / les_bez_korun (ř. 88) – `docs/mereni_verze.md`.
4. Mostní kontroly z Pucharta (`nabeh_vyska`, `nastup_mostu_v_terenu`) a statika mimo tvrz – `docs/predani.md` „Postřehy z Puchartu“.
5. Nezávislá kontrola před 0.99995 našla drobnosti (vnitřek 2 s, `_nav_nelze` navždy, čísla natvrdo) – konec `misa_28_chyby.md`.
6. Rozpory Blender × Godot otevřené: #8, #11, #13–17, #34, #35 – `docs/rozpracovane/rozpory_blender_godot.md`.
7. Hlídači z Pucharta 1–11 všichni „čeká“ – `docs/rozpracovane/hlidaci_z_pucharta.md`.

---

## 3. Plán k 1.0

**1.0 je brána, ne datum** (`docs/rozpracovane/plan_1_0.md`, 28. 10.) – vydává se, až platí najednou k jednomu otisku exportu:
1. matice vztahů pokrytí a úspěšnost 100 % (`tools/kontrola_vztahu.py --vydani`);
2. test smyslu, meze kroků, `zasazeni`, `voda_v_korytu`, `breh_hladky`, `site_natazene` bez chyby;
3. snímky 01–20 vedle referencí prohlédnuté rádcem a Míšou;
4. výkon za celý okruh v rozpočtu tabletu (`mapa_vyhledu`, `pamet_okruh`, test záseků);
5. každý řádek Míšiny tabulky opravený s kontrolou v testu (`tools/kontrola_tabulek.py`).

**Pořadí** (z `plan_1_0.md`, doplněno pozdějšími zdroji):
| # | úkol | zdroj | stav |
|---|---|---|---|
| 1 | Export a dočištění tabulky (vše „čeká export“) | `misa_28_chyby.md` | další krok |
| 2 | Výkon: 3D 75 % změřit, tráva bez stínového průchodu (opravit barvu v lese), les podle světla | `mereni_verze.md`, `les_podrost.json` | rozpracováno |
| 3 | Ruce, předměty v rukou, kroky bez klouzání, IK nohou (pořadí 1–8) | `docs/predani.md` „Tělo hráče a postavy 9. 11.“ | rozpracováno |
| 4 | Rozpory Blender × Godot dotáhnout (voda dílů, terasa, lom, brody jako záznamy) | `rozpory_blender_godot.md` | rozpracováno |
| 5 | Hodnoty z rešerše KCD2 do pásem (odstupy cest/stromů, břehy) | `plan_1_0.md` #6 | rešerše hotová |
| 6 | Toky a cesty plánovat společně (≤ 3 křížení na tok) | `plan_1_0.md` #7 | částečně |
| 7 | Warhorse W1–W8 (rozměry staveb, texel, stínové proxy, okluzory, kolize, výdrž) | `plan_1_0.md`, `docs/rozpracovane/warhorse_do_dat.md` | po exportu, W3 NEOVĚŘENO |
| 8 | Snímky 01–20 vedle referencí + kontrola rádce | `plan_1_0.md` #8 | – |
| 9 | Manuál otevřeného světa: souřadnice ze shaderu do dat, kontrola kontrol záměrnými chybami, poslední dobrá verze | `manual_otevreny_svet_3_11.md` | čeká |

Další sekce po 1.0 / později: vzhled postav (obličeje, zbroj), dovednosti hráče (`pravidla/svet/dovednosti.json`,
`docs/rozpracovane/navrh_skilly_menu_hrace.md`), rozhovory a hlas (`postavy_plan.md` krok 6–7).

---

## 4. Jak stavět svět

**Pipeline** (`docs/pipeline.md`, `docs/predani.md`):
`pravidla/svet/*.json` (jediný zdroj) → Blender (`blender/export_game.py`, `kraj.py`, `vesnice.py`, `fort.py`, `hospodar.py`…)
→ `tools/export.sh` (brány rc 2–11: pyflakes, test smyslu před/po, UV, protokol a meze kroků, import, otisk, datové textury)
→ `modely/*.glb`, `modely/svet.json` → Godot `scripts/svet.gd` (vkládá díly, rozsev, usazení) → `tools/vydani.py` (balíky
`data/*.pck`, APK). Kontejner bez zdrojů: opravné balíky `--jen z_svet,z_rostliny,…` (`docs/predani.md` §3).

**Pořadí vrstev** (pevné, pozdější krok nehýbe dřívějším – `CLAUDE.md`, `docs/pipeline.md` tabulka kroků):
1 terén hrubý → 2 voda → 3 cesty → 4 plošiny budov → **zámek terénu** → 5 masky → 6 stromy → 7 kryt korun → 8 podrost →
9 předměty → 10 usazení a kolize → 11 povrchy vizuální. (Pozor: `CLAUDE.md` píše terén → cesty → budovy → voda; `pipeline.md`
má vodu jako krok 2, `predani.md` 28. 10. „tvar vody až po cestách a pláckách“ – viz §8 rozpory.)
Pořadí kroků, které smí měnit terén: `pasma.test.poradi_terenu` (`pravidla/pravidla_sveta.json`), hlídá test `zamek_terenu`.

**Pravidla stavby:**
- **Záplatování zakázáno** – každý díl je záznam v datech; chyba = oprav záznam/pravidlo a postav znovu (`CLAUDE.md`).
- **Odstupy jen z `pasma`** (`pravidla/pravidla_sveta.json`), v kódu žádná vlastní čísla; nová hodnota do JSON, hra čte
  přes `Pravidla.cti` (`docs/predani.md` „Pravidla z jednoho zdroje“). Změna `pravidla_sveta.json` = nový export (otisk).
- **Povrchy A/B/C** (terén / díl / voda): po čem se chodí, je terén; díl má vlastní hranu, terén se k ní přitáhne; voda vždy
  nad A nebo B (`docs/predani.md` „POVRCHY – tři třídy“).
- **Pokládání na terén**: jeden bod / víc bodů s náklonem / svislé s podezdívkou (`docs/predani.md` „Pokládání objektů“).
- **Mazání nahradit stanovištěm** – druh se nesází, kde nemá být (`docs/pipeline.md` zásada 4, `pravidla/svet/druhy.json`).
- **Test smyslu před exportem**: `/opt/bl/bin/python tools/test_smyslu.py` (a `--po` po exportu); každá chyba od člověka =
  nová kontrola (`CLAUDE.md`).
- **Hlídači vrstvy 0–7** (`docs/pipeline.md` „Hlídači a mapa stavby“): skripty → data (test smyslu) → UV (`tools/test_uv.py`)
  → engine (`tools/beh_chyby.txt`) → protokol (`build/protokol_stavby.json`) → zámek → invarianty (`tools/test_svet.gd`,
  `tools/test_stavby.gd`, `tools/test_voda.gd`) → mapa (`build/mapa_stavby.png`, prohlédnout před snímky) → matice vztahů
  (`pravidla/svet/vztahy.json`, `tools/kontrola_vztahu.py`) → tabulka chyb (`tools/kontrola_tabulek.py`).
- **Statika** (`blender/statika.py`, `pravidla_sveta.json statika.nese`, `statika.stity`): díl stojí na zemi nebo na
  povoleném druhu; zatím jen tvrz (68 dílů), zbývá palác, kovárna, stáj, ves, mlýn, hostinec (`docs/predani.md` ř. 87).
- **Předpečená data nesou otisk exportu** (`reka_otisk`; `kryti.bin` zatím bez otisku) – `docs/predani.md` 28. 10.
- **Rozpory Blender × Godot**: cíl „Blender staví, Godot jen vkládá díly“ – `docs/rozpracovane/rozpory_blender_godot.md`.
  Po dvou neúspěšných opravách nový rozbor příčiny (`CLAUDE.md`).
- **Nejdřív hledat hotové** (Disk „Modely“, Poly Haven, ambientCG, Quaternius, Kenney, Sketchfab CC0/CC-BY), reálie 1393
  (`CLAUDE.md`, `docs/predani.md` §4); rešerše před technikou (`docs/predani.md` „nejdřív rešerše“).

**Kde jsou data** (`pravidla/`):
| soubor | k čemu |
|---|---|
| `pravidla/pravidla_sveta.json` | druhy rozsevu, stanoviště, **pasma** (odstupy, test, meze kroků, beh), statika |
| `pravidla/pravidla_modelu.json` | třídy modelů (LOD, kolize, stín, dosah), rozpočet |
| `svet/lokace.json` | stavby, ruiny, ves (usedlosti, ulice), sklep, ubytovna, kuchyně |
| `svet/cesty.json` | osy cest, pěšiny, přechody (mosty, `najezd_m`) |
| `svet/voda.json` | Bystřice, toky, rybníky (hráz, břeh), mlýn, tvar toků |
| `svet/plochy.json`, `generovani.json` | pole, pastviny, les, lom, srážení svahů; pásma sítě terénu |
| `svet/druhy.json`, `les_podrost.json`, `trava_karty.json`, `trava_gpu.json` | rostliny podle stanoviště, tráva v lese, obrysy karet, prototyp GPU trávy (vypnut) |
| `svet/modely.json`, `nabytek.json` | katalog modelů (pata, LOD domů vsi, látka, tráva unshaded), nábytek budov |
| `svet/postavy.json`, `postavy_vzhled.json`, `zvirata.json`, `jizda.json`, `hrac.json`, `dovednosti.json` | lidé, vzhled, zvířata, kůň a tělo, výdrž, dovednosti |
| `svet/kvalita.json`, `rozpocty.json`, `mereni_trasa.json`, `sceny.json` | automatická kvalita, rozpočty načítání, měřicí trasa, dohled scén |
| `svet/prostredi.json`, `svet.json`, `vztahy.json`, `masky.md` | vítr/stíny/odraz vody, hranice světa, matice vztahů, slovník masek |
Soupis čísel natvrdo a rozporů v kódu: `docs/soupis_pravidel.md` + `docs/soupis/*.md` (stav 27. 10.).

---

## 5. Jak optimalizovat pro tablet

**Rešerše 10. 11. (Míša):** `docs/rozpracovane/reserse_10_11_optimalizace_tablet.md` (pořadí 12 kroků: měřit → špičky →
strop 30 od spuštění → tráva → stínové proxy …) a `docs/rozpracovane/reserse_10_11_github_asie.md` (2. kolo). **Pozor, oprava
z 2. kola:** podle zdrojáku 4.4.1 se jedno stínované slunce kreslí v ZÁKLADNÍM průchodu (průchodů = max(1, P + D)), ne druhým
průchodem – tvrzení „tráva se kvůli slunci kreslí dvakrát“ v `reserse_trava_godot.md` je chybné; naměřená úspora unshaded
7–16 ms platí, ale jde o něco uvnitř průchodu (čtení stínové mapy, filtr) → levnější zásahy: tráva bez čtení stínu, filtr
stínu 2 → 1. Zavedeno 10. 11.: trasa má variantu `stiny` (slunce bez stínu) místo `bez_postav`, u špiček volná paměť,
halda a VRAM. Rozhodnutí pro Míšu: strop 30 snímků od spuštění (krok 3), zkouška herního prostoru Xiaomi.

**Rozpočty** (zdroje se liší – viz §8): `docs/stav.md` „Rozpočet“: ≤ 1500 kreslení, troj. 2 M (tolerance 2,75 M), GPU < 700 MB;
`docs/predani.md` §4: ≤ 2,5 M troj., APK < 100 MB; ZÁVĚR tablet (větev `origin/ccr-f2d32673-9fi7m5`
`docs/ZAVER_tablet_grafika.md` §4): troj. ≤ 1,2 M, kreslení < 400, textury ≤ 300 MB, RAM ≤ 1,2 GB; rešerše
`reports/Otevřený svět Godot Android.md`: kreslení < ~500 (strop 700). Naměřeno 0.99995: kreslení 266–528, troj. 1,1–1,8 M,
**VRAM 930 MB (nad 700)**. Rozhodnutí Míši 6. 11. „krása i plynulost“: výkon u příčiny, automatika jen v extrému.

**Seřazeno podle naměřeného / očekávaného přínosu:**
| # | opatření | přínos (zdroj) | stav |
|---|---|---|---|
| 1 | Tráva bez stínového průchodu slunce (unshaded, 2 složky světla) | **naměřeno** p50 −7 až −16 ms (tvrz/louka/les), méně tepla – `mereni_verze.md` 0.99992 | v kódu, `modely.json trava_unshaded.tablet` **false**: barva v lese mimo 10 % (`predani.md` „Tráva unshaded“), stín korun +~7 ms (podezření) |
| 2 | Teplo: automatika s 30 FPS | **naměřeno** zahřátý p95 37–46 místo 77–118 – `mereni_verze.md` 0.99993 | zavedeno, `kvalita.json vychozi.tablet` true; teplo API NEOVĚŘENO na Pad 8 |
| 3 | Světla ohně bez stínu na tabletu | **naměřeno** ves 27–38 ms místo p95 78 – `kvalita.json stiny_svetel` | zavedeno (0/0/0) |
| 4 | Záseky skriptů: A* postav s rozpočtem, průchod předmětů vnitřku 1 ms | **ověřeno na tabletu** skr 3–8 ms – `mereni_verze.md` 0.99995 | zavedeno |
| 5 | Rozlišení 3D tablet 75 % (pevně, za běhu neměnit – zásek 1,36 s) | 3D 100 % zdražilo les na p50 57 – `mereni_verze.md` 0.99995, `CLAUDE.md` | v datech, **NEOVĚŘENO NA ZAŘÍZENÍ** |
| 6 | Les podle světla (tráva jen na mýtinách a u pěšin) | očekávaný (KCD) – `les_podrost.json`, ř. 86/88 | v kódu (21ba425), měření NEOVĚŘENO |
| 7 | Předehřátí shaderů + keš `glProgramBinary` | po předehřátí 0–19 sestavení na PC – `predani.md` „Záseky při prvním příjezdu“ | zavedeno; špičky 0,5–4 s na tabletu **nevysvětlené** (podezření ovladač Adreno) |
| 8 | Kolize: konvexní díly místo trimesh, jednoduché tvary | rybník 30–40 ms → 0,5 ms – `predani.md` 0.97 | zavedeno; W5 pro stavby čeká |
| 9 | LOD domů vsi (podrobný/střední/daleko), impostory stromů buňka 1024 m, domy do 75 m | úbytek kreslení – `stav.md` 26. 10., `predani.md` 2. 11. | zavedeno |
| 10 | Textury: ETC2, ořez horních mip (`tools/textury_tablet.py`), limity 1024/512 (`tools/limity_textur.py`), datové textury bez komprese (`tools/kontrola_datovych_textur.py`) | 1769 → 458 MB na disku – `stav.md` 0.58 | zavedeno; po reimportu vždy znovu (past 0.98) |
| 11 | Okluze terénem (occlusion culling) | jen 0–46 kreslení – `stav.md` „MAPA VÝHLEDŮ“ | zapnuta (`project.godot`), přínos malý |
| 12 | Stíny slunce 1 kaskáda 40 m, vegetace bez stínu, postavy stín do 15 m | `stav.md` 0.58, `postavy_plan.md` | zavedeno |
| 13 | Nikdy MSAA, žádná screen texture, předměty < 0,5 m bez stínu | pády 0.58–0.59 – `CLAUDE.md`, `stav.md` | pravidlo |
| — | **Nepomohlo (naměřeno):** tráva do 50 m (0.9995), ořez karet (0.9999, v šumu), tráva GPU (0.9998) | `mereni_verze.md` | nerozšiřovat |

**Doporučení z rešerší, dosud nezavedená** (přínos jen odhad – NEOVĚŘENO):
- Tráva: zrušit/přestavět drn (krytí 7 %), plná hustota jen do 10–12 m, discard na začátku `fragment()`, buňky trávy menší
  kvůli řazení zepředu, geometrická stébla zblízka, odstranit iluzi A2C – `docs/rozpracovane/reserse_trava_hry.md` §4,
  `reserse_trava_godot.md` §9. Měřit jako varianty trasy, ne hádat.
- Zapečené světlo z Blenderu (Cycles → UV2 → lightmapa), impostory lesa, atlasy materiálů (< 400 kreslení), profily
  kvality – `ZAVER_tablet_grafika.md` §3–4 (jiná větev).
- Stínové proxy z LOD1 (W3), okluzory staveb (W4), kolize jednoduchými tvary (W5) – `docs/rozpracovane/warhorse_do_dat.md`, `plan_1_0.md`.
- Snížit `max_lights_per_object` (8 → 4), fade visibility_range jen Disabled, animační LOD postav/zvířat, HeightMap kolize
  po dílech kolem hráče – `reports/Otevřený svět Godot Android.md` akce 3, 12, 13; `research_notes/Otevřený svět Godot Android/`.
- Souřadnice natvrdo v `zem.gdshader` (ves 470,830; nádvoří) převést na data – `manual_otevreny_svet_3_11.md` bod 16.
- Rozbor ceny lesa: varianty `les_bez_travy`, `les_bez_korun` (`pravidla/svet/mereni_trasa.json`).

**Jak měřit:** jen tablet (PC = llvmpipe, snímek 1–3 s, časy nic neříkají – `docs/predani.md` „Testy: dvě sady“). Panel
měření sám stojí 7–10 ms (0.9995). Porovnávat studené varianty; od ~5. minuty trasy měří teplo (`mereni_verze.md` 0.9997).
Rozhodovací pravidlo pixel × vrcholy: 3D 50 % ≈ bez trávy → brzdí pixely (`mereni_verze.md` 0.9998).

---

## 6. Postavy, animace, zvířata, kůň

**Postavy** (`docs/rozpracovane/postavy_plan.md`, `pravidla/svet/postavy.json`, `postavy_vzhled.json`, `scripts/lide.gd`, `vzhled.gd`):
- Stav: 32 obyvatel podle `pribeh/postavy.md`, 26 dobových sad (Quaternius přes `tools/postavy_q/`, jedna síť se 3 povrchy),
  rozvrhy po hodinách, chůze po síti cest + mřížka A* s rozpočtem, rozestup, místa u předmětů (záhony, stoly, lom),
  lůžka a spánek, hospoda (obsluha, hosté sedí čelem), hlava sleduje hráče.
- Animace: Quaternius UAL 1+2 (CC0, `modely/postavy/anim/UAL*.glb`), CMU mocap pro kováře/úder (`docs/predani.md` 9. 11.).
- Otevřené: úchop podle klipu ve všech klipech (ř. 47, `scripts/uchop.gd` rozpracován), krumpáč obouruč (ř. 48), kroky hráče
  134 % rychlosti klipu (rozhodnutí), vyhýbání v protisměru jen čekáním, LOD1 postav a výkon NEOVĚŘENO, dítě bez dětských
  proporcí, chybějící animace řemesel (`postavy_plan.md` §1.3, krok 5).
- Plán vylepšení těla podle přínosu: ruka s loučí → předměty v rukou → spánek → sezení čelem → kroky bez klouzání →
  otáčení klipem → IK nohou (vlastní, `SkeletonModifier3D`) → přechody lehání – `docs/predani.md` „Tělo hráče a postavy 9. 11.“.
- Rešerše: `reserse_postavy_kcd2.md` (rozvrhy, smart objects, §9 architektura), `reserse_reakce_kcd2.md` (vnímání, reakce),
  `odevy_zdroje.md`.

**Zvířata** (`pravidla/svet/zvirata.json`, `scripts/zvirata.gd`): slepice (spí v kurníku 20–5:30), prasata, ovce v ohradách
z pletených plůtků; modely CC-BY z Disku (prase CC-BY-NC-ND – neupravovat), nohy houpe skript; testy `ohrady`,
`nocleh_pred_zdi`, `slepice_noc` – `docs/predani.md` 29. 10. a 9. 11.

**Kůň** (`scripts/kun.gd`, `pravidla/svet/jizda.json`, `zapojeno_do_hry` true): model `kun_henry` (Sketchfab henry_7,
CC-BY, 28 animací – `docs/rozpracovane/kun_animace.md`), výstroj Balt Horse (`tools/kun_vystroj.py`), sedlo jde s pózou kosti,
hříva mimo hrušku sedla, překrok do 0,45 m, plavání, rychlé cestování v sedle, ovladač (`docs/ovladani.md`). Testy
`kun_prekazky`, `tools/test_kun_klid.gd`, `test_otezi.gd`. Otevřené: snímky sedla z obou boků NEOVĚŘENO, `kun_zivy.gd`
je pro henry mrtvý (jiné kosti), výlez z vody na břeh 37° neověřen, čísla plavání odhad – `docs/predani.md` 5.–9. 11.
Rešerše: `reserse_kun_povrchy.md`, `reserse_potok_1osoba_kun.md`.

---

## 7. Pracovní postup

**Prostředí nového kontejneru** (`docs/predani.md` §1): `bash tools/prostredi.sh` → `bash tools/stahni_zdroje.sh` →
`bash tools/pregeneruj.sh` (bez textur/zvuků APK nemá oheň a zvuky). Klíč `tvrz_release.keystore` je u Míši na Disku →
`/root/keys/`, ověřit SHA-256 (`docs/predani.md` §2); nikdy do repa.

**Běhy Godotu** (`CLAUDE.md`, `docs/predani.md` „Spouštění Godotu“, „Souběžné běhy“):
- Vše přes `tools/beh.sh <jméno> foto|testy|cmd …` na pozadí, s `timeout` 7200000 (bez něj harness zabije za 30 min,
  i během čekání na zámek – stalo se 27. 10., 29. 10., 3. 11., 9. 11.).
- Testy a focení sdíleně, nejvýš 2 najednou (`pasma.test.beh_soubezne`); `cmd` (export, import, vydání) výhradně a přednostně.
  Řetěz jen s testy/focením: `BEH_SDILENE=1`. Čekání: `build/beh/cekani.log`, kdo drží: `/tmp/godot_beh.kdo`.
- Vybrané testy: `tools/beh.sh jm testy "t1,t2"` (seznam jako argument); s celým světem `TVRZ_TEST_LIMIT=1200`.
- Jeden běh ~1,1 jádra, 2,5 GB RAM; stroj 4 jádra / 15 GB (9. 11.).

**Vydání** (`docs/predani.md`, `tools/vydani.py`): jen na „VYDEJ“ od Míši; před tím export OK (`build/export_stav.json`),
`kontrola_vztahu`, `kontrola_tabulek`, `kontrola_baliku`, APK < 100 MB, nezávislá kontrola změn a snímků subagentem
(`CLAUDE.md`). Zpráva „**Vydáno 0.NN – den. měsíc hh:mm**“ (český čas) + odkaz na APK v bloku kódu (`CLAUDE.md`).
Nový předmět → balíky `z_katalog,p_<id>`; změna katalogu → nejdřív export (otisk).

**Měřicí trasa** (`pravidla/svet/mereni_trasa.json`, `scripts/mereni_trasa.gd`): Míša každé vydání projede Nastavení →
Měřicí trasa, „Zkopírovat záznam měření“, stavitel zapíše do `docs/mereni_verze.md` k verzi a commitu. Bez záznamu =
NEOVĚŘENO NA ZAŘÍZENÍ. Regrese: poslední dobrá × první špatná → rozdíl commitů → hypotézy → izolovaná varianta → oprava
(`CLAUDE.md`).

**Poučení z chyb (výběr, vše v `docs/predani.md`):**
- **Restart kontejneru:** stavba světa v headless testu > 300 s → `TVRZ_TEST_LIMIT`; `modely/` mimo git – zdroje stáhnout
  znovu; reimport vrátí textury v plné velikosti → `textury_tablet.py` vždy (past 0.98).
- **Disk:** `beh.sh` pod 800 MB nic nespustí, export chce 1 GB. Bezpečný úklid: `build/packs`, `build/OdkazHavrana.apk`,
  staré `build/f*`, velké logy `build/beh`, mesa/pip cache, `shader_cache` Godotu, sirotci `.godot/imported`; nikdy
  `data/`, `apk/`, `modely/`, `zdroje/`, `build/z_textury.pck`. `.git` 8,5 GB (volné objekty .pck) – `git gc` až s místem.
- **Zámek:** osiřelý hlídač disku držel zámek 40 min (opraveno); `pkill -f` zabije vlastní shell – zabíjet podle PID,
  úlohy přes TaskStop; čekání nikdy přes `pgrep -f <jméno>`; běžící skript v `build/beh/` nepřepisovat (bash čte průběžně).
- **Sdílená složka:** žádný `git pull`, `git stash`, `--autostash`; commitovat jen vlastní soubory (konflikt 9. 11. 18:28 –
  a stále v HEAD, viz začátek).
- **Brány:** `|| true` = žádná brána; chybějící podklad = chyba; po exportu porovnat počty v `svet.json` se zálohou;
  za běhu exportu neměnit vstupy; řetězy s `&&`, ne `;`.
- **GDScript pasti:** `Packed*` ve slovníku a v lambdě je kopie; `set_script` na uzlu ve stromu nevolá `_ready`;
  `Pravidla` není autoload (preload); headless MultiMesh vrací nulové transformace.

---

## 8. Rozcestník

| chci vědět | soubor |
|---|---|
| stálá pravidla session | `CLAUDE.md` |
| jak začít, prostředí, klíč, pasti a poučení | `docs/predani.md` |
| co říká rádce (poslední pokyny) | `docs/radce.md` (od konce, před čtením `git pull` – ale ve sdílené složce ne, viz §7) |
| naměřený výkon verzí na tabletu | `docs/mereni_verze.md` |
| otevřené chyby od Míši | `docs/rozpracovane/misa_28_chyby.md` (starší: `misa_099*_chyby.md`) |
| plán k 1.0 | `docs/rozpracovane/plan_1_0.md` |
| pipeline, pořadí kroků, hlídači | `docs/pipeline.md` |
| čísla natvrdo, logika světa (soupis 27. 10.) | `docs/soupis_pravidel.md`, `docs/soupis/*.md` |
| rozpory Blender × Godot | `docs/rozpracovane/rozpory_blender_godot.md` |
| hlídači z Pucharta | `docs/rozpracovane/hlidaci_z_pucharta.md` |
| manuál otevřeného světa (rozbor) | `docs/rozpracovane/manual_otevreny_svet_3_11.md` |
| grafika tablet – rozhodnutí Míši „plný obraz“ | `git show origin/ccr-f2d32673-9fi7m5:docs/ZAVER_tablet_grafika.md` |
| rešerše výkonu otevřeného světa | `reports/Otevřený svět Godot Android.md`, `research_notes/Otevřený svět Godot Android/*.md` |
| tráva (rešerše, GPU, hotová řešení) | `docs/rozpracovane/reserse_trava_hry.md`, `reserse_trava_godot.md`, `trava_gpu.md`, `trava_hotova_reseni.md` |
| mikrosekání a nástroje | `docs/rozpracovane/reserse_mikrosekani_nastroje.md` |
| automatická kvalita | `docs/rozpracovane/kvalita_auto.md`, `pravidla/svet/kvalita.json` |
| postavy | `docs/rozpracovane/postavy_plan.md`, `reserse_postavy_kcd2.md`, `reserse_reakce_kcd2.md`, `odevy_zdroje.md` |
| kůň | `docs/rozpracovane/kun_animace.md`, `reserse_kun_povrchy.md`, `pravidla/svet/jizda.json`, `docs/ovladani.md` |
| voda, potok, mlýn (rešerše) | `docs/rozpracovane/reserse_potok_1osoba_kun.md` |
| pole, vztahy, ChatGPT 1. 11. | `reserse_pole_kcd2.md`, `reserse_vztahy_kcd2.md`, `reserse_chatgpt_1_11.md` |
| Warhorse dokumentace do dat | `docs/rozpracovane/warhorse_do_dat.md` |
| dovednosti a menu hráče | `docs/rozpracovane/navrh_skilly_menu_hrace.md`, `pravidla/svet/dovednosti.json` |
| modely od Míši, inventura Disku | `docs/modely_misa.md`, `docs/rozpracovane/disk_inventura.md`, `zdroje/nahrane_misa/` |
| ovládání | `docs/ovladani.md` |
| testy | `tools/test_svet.gd`, `test_stavby.gd`, `test_voda.gd`, `test_smyslu.py`, `rychle_testy.sh`, `beh.sh` |
| mapa stavby, protokol | `tools/protokol_mapa.py` → `build/mapa_stavby.png`, `tools/protokol_blender.py` |
| historie stavu a měření do 28. 10. | `docs/stav.md`, `docs/stav_historie.md` (nepravidelně udržované) |

**Rozpory a mezery v podkladech (zjištěné při psaní):**
1. (vyřešeno, ověřeno 10. 11.) konfliktní značky v `postavy.json` a `kun.gd` – v HEAD už nejsou.
2. `CLAUDE.md` a `kvalita.json` odkazují na `docs/ZAVER_tablet_grafika.md`, který na této větvi není (jen `origin/ccr-f2d32673-9fi7m5`).
3. Rozpočty výkonu si odporují (`stav.md` 1500 kreslení / 2 M troj. / 700 MB × ZÁVĚR < 400 / 1,2 M / 300 MB × naměřená VRAM 930 MB).
4. Pořadí vody: `CLAUDE.md` terén → cesty → budovy → voda × `pipeline.md` voda jako krok 2.
5. `docs/stav.md` stojí na 28. 10. (hlavička „20. 10., 0.56b“), `docs/modely.md` má 5 bylin – nejsou aktuální; `misa_28_chyby.md` ř. 88 „ZADÁNÍ“, ač je v kódu.
