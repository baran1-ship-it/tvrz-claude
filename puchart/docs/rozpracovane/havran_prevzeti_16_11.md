# Co převzít z Havrana (rozbor 16. 11., větev claude/new-session-0dtk58, stav e857909)

Míša 16. 11.: „podívej se, co všechno vyřešil Havran a co by se ti hodilo“. Až po vydání APK.

| Havran (scripts/…) | Puchart | Priorita | Poznámka |
|---|---|---|---|
| `zvirata.gd` + `pravidla/svet/zvirata.json` (dosah/viditelnost, houpání kostí nohou, útěk před hráčem, spánek podle hodiny, rozestup) | jen json | P1 | kostra pro zvěř v lese; nové pole stanoviště ve volné přírodě (z masek stanovišť / les.gd), útěk 20–40 m, LOD animace pro mnoho kusů |
| `ruchy.gd` + `zvuky/prostredi`, `zvuky/zvirata` (smyčky podle místa a hodiny, potok, rybník, hlasy) | ne | P1 | Míša u Havrana: v lese jen kukačka a datel, žádné vrány/sovy ve dne, v noci žáby; body toků z `voda_hra.json`; licence ověřit v `zvuky/seznam.txt` |
| `kvalita.gd` (měří snímky, ubírá kvalitu podle GPU/CPU) | ne | P1 | prahy do `rozpocty.json` |
| `voda.gd` (vlnky a čvachtání hráče ve vodě) | ne | P2 | brody, potoky |
| `kun_zivy.gd` (dech, ocas, uši, pastva – SkeletonModifier3D) | ne | P2 | kůň u kovárny/ve stáji; celá jízda `kun.gd` později |
| `lide.gd`, `anim_ual.gd`, `nohy_ik.gd`, `uchop.gd`, `vzhled.gd` | ne | P2 | krok F (postavy); známé chyby: lide_zasek, přestavba oděvů 15. 11., výkon (`vykon_postavy_puchart_15_11.md`) |
| `planovac.gd` (jeden rozpočet snímku) | částečně (`bunky_kolem.gd`) | P2 | záseky louky |
| `tools/textury_predmetu.py` (sdílené textury, ETC2 211 → 87 MB) | ? | P2 | velikost dat |
| `sber.gd` (byliny, houby) | ne | P2 | pozor na létající hřiby (LOD terénu) |
| `obchod.json` (kupec, groše) | ne | P3 | |
| `diag.gd` zpráva o minulém pádu | vlastní deník | P3 | |
| MSAA 2× na Vulkanu (main.gd) | – | ne | odporuje pravidlu „nikdy MSAA“ – jen po měření |

Zvířata v Havranovi: jen domácí (slepice CC-BY-NC, ovce CC-BY, prase CC-BY-NC-ND, kůň CC-BY) – pro Puchart bez omezení jen ovce a kůň. Divoká zvěř, ptáci ani ryby nejsou (ryby = jen kruhy na hladině). Hlad/žízeň/únava nemá ani jedna hra.
Balík modeláře Zvirata_Les (Disk, 16. 11.): zamítnuto (Míša: „moc se modelář nepředvedl“) – po APK hledat realistické CC0/CC-BY modely našich druhů s kostrou a klipy chůze/běhu, náhledy Míše na výběr, modelář dodělá.
