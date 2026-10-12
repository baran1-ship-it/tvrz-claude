# Tvrz v Blenderu

Celá tvrz se staví skriptem (bpy), nic se nemodeluje ručně. Rozvržení odpovídá hře
(souřadnice Godotu: X východ, Y nahoru, Z jih), takže modely později sednou na stávající
navigaci, kolize a místnosti.

## Spuštění

Blender jako modul Pythonu (stačí `pip install bpy`, Python 3.13):

    python blender/build.py --views 1,2,3 --samples 48 --res 1600x900 --out build/nahledy --blend build/tvrz.blend

- `--parts` – co postavit: `terrain,fort,palace,yard` (výchozí vše)
- `--views` – čísla pohledů z `VIEWS` v `build.py` (ptačí pohled, příjezd, brána, nádvoří, síň, ložnice…)
- `--blend` – uloží scénu jako .blend (lze otevřít v Blenderu a dál upravovat)

## Fotografické textury

Materiály používají fotografické PBR textury z Poly Haven (CC0). Stáhnou se do `blender/tex_cache/`
(není v gitu) příkazem:

    python blender/textures.py 2k

Bez nich se použijí procedurální materiály.

## Soubory

- `lib.py` – stavebnice (kvádry, trámy, rotační tělesa, zdi s otvory, šindelové střechy)
  a procedurální materiály (lomové zdivo s opadávající omítkou, pískovcové kvádry, dub,
  šindel, dlažba, hlína, tráva…)
- `props.py` – vybavení: stoly, lavice, truhly, sudy z dužin, police, postel, svícny, lustr,
  pochodně, zbraně, studna, vůz, seník, napajedlo…
- `fort.py` – terén s příkopem, hradby s cimbuřím a ochozy, brána s padacím mostem, věž,
  schody na hradbu, most
- `palace.py` – palác: síň s gotickým krbem, spíž, komnata, ložnice, pavlač, krov
- `yard.py` – strážnice, vybavení nádvoří, tráva, smrkový les
- `scene.py` – obloha, slunce, kamery, render (Cycles)

Kovárna a střelnice jsou zatím vynechané.
