# Návrhy dvojhradu Puchart – kolo 1 (29. 10. 2026)

Zadání Míši: návrhy ke schválení, styl KCD, reálné, ale neortodoxní – „propojené a krásné“, „vymakaná verze, můžeš i
více, dle málo známé reality a KCD“. Data: `pravidla/svet/hrady_navrhy.json`, stavitel: `blender/hrady.py` (stavebnice
Havrana `blender/havran/`), terénní úpravy: `nastroje/teren_upravy.py`.

## Z čeho vycházím (DOLOZENO)
- **Plán lokality, Archeologický atlas** (Tomášek a kol. 2015), zaměřený na DMR 5G (`nastroje/plan_atlas.py`,
  `plan_prekryv.py`): jádro předního hradu ~37 × 27 m na vrcholu ostrohu (434 m n. m.); na S **dvojitý val s příkopem**;
  na spojnici zbytek zdiva (hra 40, 33); **zadní hrad o 47 m níž na východním úbočí** (387 m) – hranolová věž B
  (~8 × 8 m), hranolová zeď C, zdi na SZ, **skalní příkopy** na JV.
- **Fotky ruiny** (turistika.cz, natreku, veruce, vyraznavylet, atlas): zdivo z plochých šedohnědých břidlic/drob na
  vápennou maltu, vysoké zbytky zdi s otvory, skalní výchozy s deskovitou odlučností, úvozové cesty.
  → materiál `castle_wall_slates` (Poly Haven) sedí na fotky 1:1.
- **Kresebná rekonstrukce** (vyraznavylet.cz): přední hrad s palácem a věžemi, cesta po hřebeni, k zadnímu hradu
  dřevěný most přes průrvu.

## Co je NÁVRH (podle KCD a dobových hradů Moravy)
Výšky věží a zdí, střechy (šindel), palác s kamenným omítnutým přízemím a hrázděným vyloženým patrem, kryté dřevěné
ochozy, hurdice na věži, branská věž s mostem přes příkop, budovy na nádvoří. Inspirace: KCD Rataje (měřítko, omítky,
dřevěné ochozy), Talmberk (věž nad údolím), Pirkštejn; Helfštýn a Starý Jičín (Morava, 14. stol.).

## Varianty
| # | název | myšlenka | silná stránka | slabina |
|---|---|---|---|---|
| 1 | **Hřebenová hradba** | kamenná hradba s krytým ochozem po úbočí z jádra A dolů do B, uprostřed branská věž na doloženém zbytku zdi | jedna dlouhá silueta po hřebeni, jasná obrana, hráč chodí po ochozu mezi hrady | nejvíc kamene = nejdražší na trojúhelníky |
| 2 | **Most přes průrvu** | podle kresby: cesta po úbočí bez zdi, k B dřevěný most na kozách; přední hrad s druhou věží | nejvěrnější dostupné rekonstrukci, lehká, výrazná dřevěná konstrukce | hrady méně propojené |
| 3 | **Předhradí na sedle** | mezi hrady palisáda s hospodářským dvorem (stáj, kovárna, sýpka), brány do obou hradů | nejvíc života a herních funkcí (zásobování, PDF kap. 3) | palisáda méně „krásná“ než kámen |
| 4 | **Krytá chodba po skalách** | krytá dřevěná chodba na kamenných pilířích se schodišti sestupuje 47 m do B; B jako vysoká věž s hurdicí | nejdramatičtější, jedinečná (KCD efekt „wow“), využívá skutečné převýšení | nejméně doložitelná |

## Snímky (stejné pohledy pro všechny varianty)
dron SZ, vyhlídka na protějším svahu (NAVRH: paseka nad Kouteckým potokem), dron JV, pastvina pod zadním hradem,
nádvoří A, spojnice, val a most na S. Soubory `docs/screens/hrad_<n>_*.jpg`.

## Známé nedostatky kola 1 (opraví se po výběru varianty)
- Vzdálené stromy jako zkřížené karty vypadají do ~80 m jako krabice → impostory (krok D). Pro snímky jsou plné
  stromy do 110 m.
- Paseka kolem hradů je holá (chybí tráva a byliny Havrana – louka.gd).
- Detail: okna jen v kamenném patře, chybí komíny, pavlače, studna, praporce, vybavení nádvoří.
- Trojúhelníky 300–360 tis. na návrh (bez LOD) – herní verze potřebuje LOD a slučování podle materiálu.
