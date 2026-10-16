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
