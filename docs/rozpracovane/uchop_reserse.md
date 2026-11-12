# Úchopy předmětů – rešerše (12. 11., Míša: „ani jeden úchop ještě není správně… načti si to na internetu“)

Chyba procesu: do 12. 11. dělány z hlavy (pevný úhel přikroucení prstů 50°, palec dodán dodatečně). Porušeno pravidlo
CLAUDE.md „nejdřív se podívat do světa“. Zdroje a co z nich plyne:

| Zdroj | Postup | Převzato |
|---|---|---|
| [asset-tooling PR #390 – Ranger grip poses](https://github.com/moritzbrantner/asset-tooling/pull/390) | prst se ohýbá kloub po kloubu od kořene, dokud článek nedosáhne násady (poloměr + půl tloušťky prstu) nebo limitu kloubu; palec přes obalený ukazovák, konec ohnutý kolem; póza jen prstů (15 kostí) přehrávaná přes klip těla, vlastní prsty té ruky; násada musí vést **napříč dlaní** (štít: z osy podél prstů přetočen napříč) | `uchop.gd _res` – řešená póza místo pevného úhlu; palec cíl na ukazovák |
| [deadnight PR #507 – grips solved from sockets](https://github.com/Ryubara/deadnight/pull/507) | úchop řešený ze soketů na zbrani, test v každém stavu a snímku: část ruky > 2 mm v předmětu nebo dotyk > 5 mm mimo = chyba; IK druhé ruky na úchop (ne zápěstí) | `test_drzeni` 2 mm / 5 mm; druhá ruka IK na bod dlaně |
| [sasori issue #9 – props with grip and finger poses](https://github.com/alokdidde/sasori/issues/9) | soket předmětu na ruce, předvolba prstů jako vrstva s vahou; test bez průniku pro násady 2,5–4 cm v klidu i v celé chůzi; druhá ruka do 1 cm | test přes všechny klipy činnosti |
| [Houman Creates – UE5 pickup + grip poses](https://houmancreates.com/tutorials/realistic-pickup-control-rig/) | IK zápěstí k předmětu + póza prstů pro každý předmět (Pose Asset, Layered Blend per Bone) | póza prstů pro každý předmět (cache) |
| [Godot fórum – attaching items across many animations](https://forum.godotengine.org/t/best-practice-for-attaching-weapons-items-to-a-characters-hand-across-many-animations-godot-4/141270) | Mixamo dávky mají jiný roll kosti ruky (až 130°) → jeden offset nesedí; normalizovat kostru | ověřit u klipů Mixamo (mereni_ruky.gd) |

Anatomie (rozsah kloubů prstů, běžné hodnoty ROM): MCP ~90°, PIP ~100–110°, DIP ~80° → `drzeni._reseni.klouby_st`.
Tloušťka násad: z modelu (vrcholy u bodu úchopu) – kladivo r 12 mm, kamenické kladivo 13 mm, perlík 23 mm (Blender, 12. 11.).
