# Puchart / Moravian Battlefield – přehled (stav, plán, jak stavět a optimalizovat)

Jedno místo, odkud vedou cesty do všech podkladů (Míša 10. 11.: „máš kompletní přehled o stavu hry, plánech a o tom, jak co stavět
a optimalizovat podle všech podkladů?“). Aktualizovat při každém větším kroku.

## 1. Stav hry (10. 11.)
- **Svět:** výsek 2×2 km Potštátska z DMR 5G (1 m), dlaždice s LOD, obzor. Vegetace 1393 (biotopy, odlesnění),
  les ~60 tis. stromů z Havrana + impostory, louka a keře. Potoky v zaříznutých korytech s jemným pásem břehů.
  Cesty: údolní vozová podél Veličky, hřebenová k zadnímu hradu, pěšiny a OSM cesty, spojky a brody dnem koryta.
  Mosty dřevěné v ose cesty, bez ramp – na mostovku vede násyp cesty.
- **Hrady:** přední hrad A (plášť, palác s dispozicí – kuchyně, síň, světnice, komora, pavlač, podkroví; sklep a kobky;
  vnější branka s mostem) a zadní hrad B (věž, kamenný palác se zařízením, příčná zeď s branou, most přes průrvu
  na zděném pilíři). Zdivo podle Havrana (malta, omítka, parallax), nárožní kameny, prkenné štíty, okna s výplní
  (terčíky / blána), světlo z oken.
- **Hra:** úvod a nabídka Moravian Battlefield (erb pánů z Kunštátu), menu hráče (mapa, místa, deník), ovladač Xbox,
  procházka, mapa, vrata a dveře, měření výkonu.
- **Kontroly:** hlídači `nastroje/hlidaci.sh` – geometrie, spoje trámů, test smyslu (~50 testů), test průchodu
  (26 tras + povrch kolize), hlídač scén (rozpočty), matice vztahů, tabulka chyb, poslední dobrá verze, časy kroků.
- **Chyby:** `docs/chyby.md` – 143 řádků, 38 otevřených (většina opravená v kódu, čeká na ověření a snímek).
  Zbývá: 2 konce údolních mostů (kolize nad viditelným), 111 rohy zábradlí, 115/128 tvar skal, 116 nádvoří B,
  122 cesta u potoka, 1 a 5 starší.
- **APK:** poslední vydaná 9. 11. (7f0ca2c). Další až po dokončení seznamu chyb (Míša 9. 11.: „nevydávej, dokud
  nebude vše top“).

## 2. Plán (pořadí)
1. **Dokončit seznam chyb** (`docs/chyby.md`) → hlídači OK → snímky Míše → APK.
2. **Vzhled a výkon** – 12 kroků v `docs/reserse_github_nastroje.md` (Míša 9. 11.: „vem sám, co se nám hodí“):
   zapečené světlo (Cycles bake + xatlas), atlas textur, highp UV, gltfpack/glTF-Transform, slučování dílů,
   impostory lesu, tráva po chuncích a podle světla v lese (Havran 9. 11.), zakrývací plochy pro occlusion culling,
   terén LOD, předehřívání shaderů, headless testy, vytěžení blender-skills.
3. **Nová místa** – `docs/plan_mista.md`: ves Předhradí, krčma, mlýny, hájovna (bez dokladu), Boňkov, skalní město.
4. **Postavy a hra** (krok F, PDF kap. 12) – převzít od Havrana animace a úchopy.

## 3. Jak stavět (pravidla a podklady)
- **Pravidla projektu:** `CLAUDE.md` (data v JSON, žádné záplaty, svět se peče, nic z hlavy, stavitel/tesař,
  hlídači před APK, plný obraz 100 %).
- **Historie a vzhled 1393:** `docs/reference/detaily_hradu_1393.md`, `reserse_dispozice_palacu.md`,
  `okna_palace.md`, `tesarske_spoje.md`, `branka_ochoz.md`, `reserse_mosty_krcma.md`; kresby GC80T08
  (`docs/hrady_podle_kreseb.md`, `docs/reference/gc80t08`), kresba Dali Figely 2023 (`docs/reference/kresby`, jen KRESBA).
- **Vzhled jako KCD:** fotky `docs/reference/kcd_vzhled/` (zdi, dřevo, střechy – štít prkenný, kámen do okapu),
  `docs/kcd_grafika_tablet.md`.
- **Havran jako laboratoř:** `docs/zkusenosti_havran.md`, `docs/pravidla_prevzeti.md`, `docs/havran_cesty_mosty_brody.md`,
  výměna postřehů `../docs/POSTREHY_pro_havrana_9_11.md`, `../docs/POSTREHY_pro_havrana_odpoved_9_11.md`.
- **Svět a data:** `pravidla/svet/*.json` (hrad_puchart, cesty_puchart, voda_hra, skaly, kontroly, sceny_pravidla…).

## 4. Jak optimalizovat (tablet Xiaomi Pad 8, Godot 4.7.2 Compatibility)
- **Závěr a rozhodnutí:** `docs/ZAVER_tablet_grafika.md` (krása i plynulost, plný obraz, automatika jen v extrémech),
  `docs/stavba_her_tablet.md`, `docs/mistri_tablet.md`, `docs/ab_srovnani.md`, `docs/godot_verze.md`.
- **Rozpočty:** `pravidla/svet/rozpocty.json`, `sceny_pravidla.json` (2,1 M troj. změřeno, výjimky s datem).
- **Pravidla Adreno:** ≤ 13 vzorkovačů, žádné MSAA, žádná kopie obrazovky, stíny 40 m, hash bez sin(), mipmapy
  a ETC2 u všech 3D textur (test `textury_3d_mipmapy`), datové masky bezztrátově, LOD 10 px na tabletu.
- **Nástroje k zavedení:** `docs/reserse_github_nastroje.md`.
- **Vulkan:** padal při startu, příčina neznámá – diagnóza plánovaná (in-app log).

## 5. Kde co je
| co | kde |
|---|---|
| předání a historie práce | `docs/predani.md` |
| chyby | `docs/chyby.md` |
| opravy 6. 11. | `docs/opravy_6_11.md` |
| stav a rešerše 6. 11. | `docs/reserse_stav_6_11.md`, `docs/srovnani_svet_6_11.md` |
| návrh hry | `docs/NAVRH_HRA_A_GRAFIKA.md` |
| stavba světa | `nastroje/postav_vse.sh` |
| hlídači | `nastroje/hlidaci.sh` |
| APK | `nastroje/export_apk.sh` |

## 6. Poznatky z rešerší Havrana 10. 11. (Optimalizace pro tablet, GitHub a asijské zdroje)
Platí i pro Puchart; co už máme, co přebíráme, co je jen hypotéza.
- **Máme:** strop 30 FPS na tabletu od spuštění (rozpocty.json snimky_max), světla bez stínu (každé bodové světlo se
  stínem přidá další průchod všem objektům v dosahu – zdroják gles3), filtr stínu slunce 1, mipmapy + ETC2, předehřívání
  shaderů, LOD 10 px.
- **Převzato teď:** nabídka a menu hráče na 10 FPS (statická obrazovka, méně tepla).
- **Do měření (krok 1 plánu):** varianty trasy – slunce bez stínu / tráva shadows_disabled / tráva unshaded / 50 % 3D;
  ke každému úseku teplo, volná paměť a snímky nad 50 ms; studený a zahřátý běh zvlášť; druhý průchod a druhé spuštění
  (kompilace vs. paměť u špiček); herní prostor Xiaomi zapnutý/vypnutý.
- **Vzhled jako KCD (podle Warhorse):** nese ho velkoplošné měkké zastínění a světlo podle denní doby → zapečené AO
  a „kolik je vidět oblohy“ do vrcholů a terénu, dvoubarevné okolní světlo (obloha/země) – posunout výš v plánu.
- **Hypotézy (A/B až po měření):** stínové proxy stromů (stín vrhá hrubý neprůhledný tvar), neprůhledný střed korun,
  depth prepass na Adrenu, méně čtení textur u skal a zdiva (zdivo má 7 vzorkovačů + parallax).
- **Úklid:** jeden dokument rozpočtů (rozpočty se v projektech rozcházejí – agent pak optimalizuje ke špatnému cíli).
- **Zkouška Herního prostoru Xiaomi (Míša 10. 11.: ano, do příští měřicí APK):** měřicí trasa 1× normálně, tablet
  vychladnout, 2× s hrou přidanou do Herního prostoru (Game Turbo) v režimu Výkon. Porovnat p95 a čas do zpomalení
  zahřátím. Pomůže-li, přidat do návodu k instalaci (i pro Havrana – stejný tablet).
