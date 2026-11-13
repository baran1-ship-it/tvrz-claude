# Kování – rešerše a návrh (Míša 13. 11.: „kování je zvláštní činnost, načti si to dle internetu a KCD“)

## Jak se kove (zdroje níže)
- **Cyklus, ne smyčka jednoho klipu**: kus ohřát ve výhni do žhava → kleštěmi přenést na kovadlinu → série úderů,
  mezi sériemi kus otočit → kus chladne, zpět do výhně → opakovat → nakonec **kalit ve vodě** (KCD2: ohřev – kování –
  kalení; když kus vychladne, zpět do výhně; v polovině kus otočit a kovat druhou stranu).
- **Obě ruce pracují**: levá drží kus **kleštěmi** na kovadlině, pravá kladivo (Goodall: kovář drží železo kleštěmi a
  kove kladivem, těžší práce perlíkem).
- **Pomocník**: měchy (párové měchy = dva lidé, pomocník dmýchá, kovář kove), u těžké práce **tovaryš s perlíkem**
  (hrubé tvarování perlíkem, jemné kovář malým kladivem). Středověká výheň na dřevěné uhlí.
- **Postoj a úder**: kovadlina zhruba ve výšce kotníků prstů sevřené pěsti stojícího kováře (u jemné práce výš); úder
  **dolů, ne ven**, plný švih od hlavy (ruka, loket, rameno); široký nízký postoj, nepředklánět se nad kovadlinu.
- **Kovadlina na špalku**, vedle káď/vědro s vodou na kalení, brus.

## Stav u nás (měřeno `tools/mereni_uderu.gd`, 13. 11.)
- Činnost `kovani` = smyčka jednoho klipu (Mixamo Bash_1 výřez) + občas napít/rozhlédnout; jen kladivo v pravé ruce,
  levá prázdná, žádný kus železa, žádná výheň–kovadlina–káď.
- Úder: hlava kladiva nejníž **0,56 m** nad zemí, ~0,35 m před kovářem; horní plocha `kovarna_kovadlina` (s pařezem)
  **0,93 m** → kladivo projde 0,37 m do kovadliny. Výška kovadliny proti „kotníkům pěsti“ postavy (~0,75 m)
  **NEOVĚŘENO** – změřit kotníky ruky postavy a plochu kovadliny v modelu (rozměr z katalogu je včetně pařezu, pata „odhad“).

## Návrh (data, ne výjimky v kódu)
1. **Kontakt**: `cinnosti.kovani.kontakt` = předmět (`kovarna_kovadlina`) + bod plochy; uchop.gd zastaví hlavu kladiva na
   ploše (IK ruky), test `kontakt` (hlava v okamžiku úderu ±2 cm od plochy nad kovadlinou).
2. **Kleště a kus železa v levé ruce** (`kleste` je v katalogu): drží žhavý kus (emisivní, bez světla) na ploše kovadliny.
3. **Kroky činnosti** (`kroky`: výheň – ohřev s pohledem do ohně a dmýcháním → kovadlina – série úderů a otočení →
   zpět do výhně ×3–5 → káď – kalení s párou → brus/oddech), časy v datech; místa = předměty sady kovárny (`lokace.json`).
4. **Pomocník** (čeledín/tovaryš) dmýchá měchy u výhně, když kovář ohřívá – společná scéna (`spolecne_sceny`).
5. Klipy: hledat hotové (Mixamo: hammering, blacksmith; Quaternius) – rytmus ~1 úder/s, úder dolů.

## Zdroje
- [iforgeiron – výška kovadliny](https://www.iforgeiron.com/topic/10882-proper-anvil-height/), [Instructables – výška kovadliny](https://www.instructables.com/Anvil-Stand-Pt-2-Proper-Working-Height), [American Farriers – výška](https://www.americanfarriers.com/articles/7423-personalizing-anvil-height)
- [KCD2 kovářství (lootlevelchill)](https://lootlevelchill.com/guides/kingdom-come-deliverance-2-how-to-blacksmith/), [Beebom](https://beebom.com/how-to-craft-weapons-kingdom-come-deliverance-2/amp/), [Sportskeeda](https://sportskeeda.com/esports/blacksmithing-kingdom-come-deliverance-2-explained)
- [Goodall: The medieval blacksmith and his products (medievalists.net)](https://www.medievalists.net/2011/06/the-medieval-blacksmith-and-his-products/), [Historical Metallurgy datasheet – měchy](https://historicalmetallurgy.org/media/mxiorxzr/hmsdatasheet303.pdf), [ACOUP – Iron, Hammer-time](https://acoup.blog/2020/10/02/collections-iron-how-did-they-make-it-part-iii-hammer-time/)
