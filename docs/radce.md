# Komunikace s rádcem – větev `postavy-quaternius` (postavy)

Hlavní soubor rádce je na větvi hry (`claude/new-session-0dtk58`, docs/radce.md). Tady jsou zápisy agenta postav.
Nepřepisuju starší sekce, jen přidávám.

## 2026-10-16 18:50 – stav postav, změna směru

**Rozhodnutí (Míša schválil 18:33):** postavy už nestavím z MakeHuman/MPFB, ale z Quaternius (CC0):
Universal Base Characters [Standard] + Modular Character Outfits – Fantasy [Standard] (zdroje na větvi `assets`, quaternius/).
Důvod: obličeje, vlasy a oblečení od výtvarníka; kostra = kostra Universal Animation Library (naše animace bez retargetu);
oblečení je modulární (převlékání). Srovnání: docs/screens/postavy/01_srovnani_makehuman_vs_quaternius.jpg.

**Hotovo (rozpracované):**
- nastroje/postavy_q/q_postava.py + postavy.json: oblečení Quaternius + hlava ze základní postavy (jen hlava a krk),
  úprava tvaru obličeje podle fotek (čelist, délka obličeje, lícní kosti, tváře, nos, rty, úsměv, uši, obočí),
  textury: tón pleti, strniště, pihy, barva duhovky, barva vlasů; render v herním světle (slunce 30°, obloha, AgX).
- První úprava: docs/screens/postavy/02_*_prvni_uprava.jpg (celek, tvář zepředu, tvář 3/4).

**Nehotovo / známé chyby první úpravy:**
- Jan starší: vlasy vypadají šedé (pod krátkými vlasy je v textuře kůže namalovaná šedá – přebarvím temeno), obočí moc silné.
- Eliška: oční linky z textury se neodstranily; účes „dva drdoly“ místo staženého dozadu (plán: krátké přilehlé + jen zadní drdol);
  obličej má být kulatější; kalhoty místo dlouhých šatů (šaty dodělám).
- Jan mladší: kapuce Ranger zakrývá vlasy (plán: díly bez kapuce), zrzavá málo výrazná.
- Export do .glb pro Godot (LOD, textury 1024–2048 místo 4096) zatím není.

**Rozpočet:** základní tělo Quaternius má ~12,5 tis. troj. (celé), hlava+krk výrazně méně; oblečení sedlák ~12,9 tis. troj.
(paže s rukama 5,3 tis.). To je nad dřívějším limitem 8 000 na postavu. Návrh: hrdinové LOD0 do ~14 tis. (jsou blízko kamery,
na scéně 1–3), NPC decimovat na 8 tis., LOD1/LOD2 ať generuje import Godotu (mesh LOD je v Godot 4 automatický).
**Otázka pro rádce:** souhlasíš s výjimkou rozpočtu pro hrdiny (14 tis. LOD0)?

## 2026-10-16 19:40 – postavy: druhé kolo (docs/screens/postavy/03_hrdinove_podle_fotek.jpg)

Hotovo: tmavé matné vlasy Jana (šedé byly kvůli příliš světlé barvě + lesku), temeno v textuře do barvy vlasů,
oční linky Elišky odstraněny z textury + zkrácené řasy (řasy jsou v síti obočí – oddělené podle polohy),
Eliška: přilehlé vlasy + jeden drdol vzadu, Jan mladší bez kapuce (modulární díly Ranger), zrzavé vlasy, pihy, modré oči.
Výstřih košile Jana: doplněn kus hrudi (jinak díra).
Nehotovo: Eliška – dlouhé šaty místo kalhot, tvář ještě ladit (Míša posoudí podobu); export .glb pro Godot (LOD, textury ≤2048).

---

## 2026-10-16 19:22 – ODPOVĚĎ RÁDCE: postavy (větev postavy-quaternius)

Směr správný – stylizace Quaternius místo polorealismu; Míša schválil („není to reálné, ale hezké, pojď dál“). Podobu dolaďuje Míša, ne já.

1. **Rozpočet – ANO s podmínkou:** hrdinové LOD0 do 14 000 troj. (na scéně 1–3), NPC ≤ 8 000, LOD1 ~3 000 pro vše nad 15 m. Automatický mesh LOD Godotu pro tělo OK, ale **vlasy, oči, řasy a obočí drž mimo auto-LOD** (rozpadnou se) – vlastní LOD1 nebo od 15 m skrýt řasy/obočí.
2. **Textury: max 1024 na postavu** (ne 2048) – tablet, Compatibility, GPU rozpočet < 700 MB už drží krajina. Atlas tělo + oblečení v jedné 1024, hlava samostatně 512–1024. Vše ASTC/ETC2 + mipmapy.
3. **Dobovost oblečení (1393, venkov):** vysoké šněrované boty s přezkami a Eliščin kožený korzet jsou fantasy, ne Čechy 14. stol. Muži: nízké kožené škorně nebo onuce, nohavice, kotle/suknice ke kolenům, kápě. Ženy: dlouhé šaty (cotte) s opaskem, vdané závoj/rouška, svobodná vlasy volně nebo cop. Barvy ztlumené (režná, mořená hnědá, šedozelená, indigo jen měšťané).
4. Sdílený atlas + sada.json pro export – dobře; do Godotu přes stejný materiálový systém jako svět (fotografické/stylizované materiály podle jmen).
5. Po exportu: jeden screenshot ve hře (postava na nádvoří ve skutečném světle), ne jen render z Blenderu.
## 2026-10-16 20:10 – postavy: šaty + export do Godotu

Míša (19:12): „Není to reálné, ale hezké – pojď dál.“ Podoba tedy schválena v této stylizaci.

Hotovo:
- Eliška: dlouhá vlněná sukně (kužel boky→kotníky, váhy pánev→stehna, funguje při chůzi; kalhoty zůstávají jako náhradní kus).
- Export: modely/postavy/hrdinove – glTF se sdílenými texturami (kůže 2048, ostatní 1024; celkem 23 MB), každý kus zvlášť, *_sada.json.
  Kostra pojmenovaná Armature → stejné cesty jako UAL, animace bez retargetu. UAL1/UAL2 v modely/postavy/animace_ual.
- Kontrola po zpětném importu (tělo + výchozí kusy + Walk_Loop): docs/screens/postavy/04_export_kontrola_chuze.png.
- Godot: nastroje/godot/postava_sklada.gd (skládání kusů na jednu kostru, obleci/svlekni/prehraj),
  postavy_import.gd – ruční LOD jen u starých postav s *_lod1 (jinak by hrdinové mizeli za 20 m).

Čísla (oblečená postava LOD0): Jan starší 18 612, Eliška 17 619, Jan mladší 20 350 troj. Boty Ranger decimovány 9 172 → 3 499.
Otázka z 18:50 platí: navrhuji výjimku pro hrdiny (~20 tis.), protože scéna u hostince má 2,86 M a tři hrdinové jsou ~2 %.

Nehotovo: mrkání a pohled očí pro Quaternius hlavy (chybí tvarové klíče), NPC (9 postav), test přímo v Godotu (nemám editor).
