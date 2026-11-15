# Zaniklá ves – Odkaz Havrana (Čechy 1393)

Středověká ves opuštěná desítky let. Dřevo shnilo a zbyly jen kamenné zdi zarostlé drnem. Kolem nich jsou valy ze sesutého kamení a hlíny, rozvaliny pecí, studna, sklep v mezi a suché zídky polí. **Nejsou tu stromy, keře ani tráva jako vegetace.** Valy mají jen texturu drnu a zbytek si osázíš sám.

Předlohou jsou archeologicky zkoumané zaniklé vsi Pfaffenschlag u Slavonic, Mstěnice, Konůvky a Bystřec:
- trojdílný dům: jizba, síň a komora; komora bývala celá kamenná a dochovala se nejvýš
- kamenné podezdívky pod roubením
- pec v koutě jizby u příčky
- domy stojí štítem k protáhlé návsi

Měřítko je 1 jednotka = 1 m, osa Y nahoru. Každý díl má **počátek uprostřed na terénu**. Zdi i valy jdou 0,35 m pod nulu, takže se dají posadit i do mírného svahu.

## Soubory
- `ves_celek.glb` je celá ves (cca 100 × 80 m) a k ní `ves_celek_lod1.glb`.
- Jednotlivé díly ke stavění vlastních vsí:

| Soubor | Co to je | Trojúhelníky |
|---|---|---|
| `ves_dum3.glb` | velký trojdílný dům 18,5 × 7,1 m: jizba s pecí a lavicí, síň s dveřmi na obě strany, kamenná komora se zdmi do 3 m a dvěma střílnami, sesutý strop jako kupa | ~37k |
| `ves_dum2.glb` | menší dvojdílný dům 11,6 × 6,6 m (jizba + síň), skoro celý zarostlý | ~18k |
| `ves_usedlost.glb` | usedlost do L: dům, kamenná komora, chlév a stáj s rozlomeným kamenným korytem, dvůr, dvorní zeď a brána s kamennými patkami | ~45k |
| `ves_stodola.glb` | stodola 15 × 9 m, jen nízké prahy pod drnem a průjezd skrz | ~15k |
| `ves_studna.glb` | studna s pobořenou kamennou obrubou, šachta 3,6 m, dole tmavá voda | ~9k |
| `ves_sklep.glb` | sklep zapuštěný do meze: kamenné čelo, půlkruhový vchod, valená klenba 4,6 m dovnitř, zadní část zasypaná | ~25k |
| `ves_zidka_rovna.glb`, `ves_zidka_roh.glb` | suchá kamenná zídka meze (8 m rovná, roh 5 + 5 m) | ~5k |
| `ves_snos.glb` | snos: kupa kamení vybraného z polí | ~6k |

Ke každému dílu je `_lod1.glb` (krabice zdí).

## Materiály
- Zdivo `M_ZdivoVes` a zídky `M_ZidkaNasucho` mají kámen posunutý v geometrii podle fotoskenu.
- Valy používají tři materiály:
  - drn `M_DrnVal`
  - sesutá hlína s kamínky `M_SutZemina`
  - vypálená hlína pece `M_PecVypalenaHlina`
- **Mech, lišejník, vlhko u země a vyschlá tráva na hřbetech valů jsou v barvě vrcholů (COLOR_0).** Když je Godot nezobrazí, zapni v těchto materiálech „Vertex Color → Use as Albedo“.
- Drn valů je laděný k zelené trávě. Pokud máš terén jiného odstínu, uprav Albedo color u `M_DrnVal`. Kraje valů jdou 5 cm pod nulu, takže zapadnou do terénu.

## Kolize
- Zdi mají kvádry `-convcolonly`. Kvádry jsou jen tam, kde je zeď vyšší než 0,3 m, takže dveřní otvory a rozpadlá místa zůstanou průchozí.
- Valy mají hrubou síť `-colonly` (krok 0,5 m), po které se dá chodit.
- Sklep má kolize stěn, stropu i čela, dovnitř se dá vejít.

## Studna a terén
Šachta jde pod nulu. Když terén pod studnou neuděláš děravý (Terrain3D: nástroj Hole, poloměr 0,6 m), uvidíš do šachty jen terén. Druhá možnost je posadit studnu do mírné prohlubně.

## Značky (uzly)
- `Ves_*_Vstup` – před vchody
- `Ves_D3*_Dum3_Pec` – nad pecí
- `Ves_D3*_Dum3_Skrys_Komora` – úkryt v komoře
- `Ves_Sk_Sklep_Poklad` – místo pro truhlu ve sklepě
- `Ves_St_Studna_Dno` – dno studny
- `Ves_U1_Usedlost_Brana` a `Ves_U1_Usedlost_Dvur` – brána a dvůr usedlosti
- `Ves_Naves_Stred`, `Ves_Cesta_Zapad`, `Ves_Cesta_Vychod` – osa návsi, kudy vést cestu

## Rozvržení celku (Godot x, z)
Náves vede po ose x a cesta po z ≈ 0.
- **Sever (z < 0):**
  - dva velké domy (x −24 a +33)
  - malý dům (x −5)
  - usedlost (x +13)
  - za domy stodola a zídky polí
- **Jih (z > 0):**
  - velký dům (x −11)
  - dva malé domy (x −31 a +8)
  - stodola (x +28)
  - zídky
- **Na návsi** je studna (x 3).
- **Na západním konci** je sklep v mezi (x −47).
- **V polích** jsou tři snosy.

## Výkon
Celá ves má asi 320 000 trojúhelníků. Je to hodně, protože kámen je v geometrii.
- Na tablet nastav pro každý díl Visibility Range:
  - díly: 0–60 m
  - LOD1: od 55 m
- Zídky a snosy můžeš vypínat dřív (35 m).
