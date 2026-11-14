# Jabloně do sadu – Odkaz Havrana (Čechy 1393)

Tři staré vysokokmenné jabloně selského sadu. Každá vypadá jinak, takže když je střídáš a natáčíš, sad nebude působit jako kopie.

| Model | Popis | Rozměr (šířka × výška) | Trojúhelníky |
|---|---|---|---|
| `jablon_1` | stará rozložitá, tlustý kmen s dutinou, široká nízká koruna, převislé větve | 8,8 × 6,8 m | 25 900 |
| `jablon_2` | středně stará, vzpřímenější, vyšší kmen, užší koruna | 7,3 × 7,4 m | 23 800 |
| `jablon_3` | nakloněná, na jedné straně ulomená kosterní větev (suchý pahýl), asymetrická koruna | 8,0 × 6,4 m | 23 700 |

Ke každé je `*_daleko.glb` (3 zkřížené karty, 6 trojúhelníků) pro velkou vzdálenost, stejně jako u ostatních stromů hry.

## Co na nich je
- **Kmen:**
  - krátký, 1,35–1,75 m do rozvětvení, zkroucený, s boulemi a kořenovými náběhy
  - kůra ze skenu šedé šupinaté kůry s lišejníkem (Poly Haven „Jolcham Oak Bark“)
- **Kosterní větve:** 4–5 hlavních s kolínkovitými zalomeními, jak jabloně rostou po řezu a pod tíhou plodů.
- **Mladé větve:** hnědočervená hladká kůra ze skenu kůry třešně (stejná čeleď jako jabloň).
- **Řezné pahýly** po prořezávání mají viditelný řez dřevem. Na kosterních větvích jsou **vlky**, tedy svislé rovné výhony.
- **Listí:**
  - karty větévek složené z fotoskenu skutečných listů, upravené do vejčitého tvaru jabloně
  - část listů otočená šedavým rubem, sem tam žloutnoucí list
- **Jablka:**
  - ve hře je léto, proto jsou zelenožlutá s červeným líčkem
  - část je namalovaná přímo v kartách listí (levné, je jich hodně), 40–55 je 3D ve spodní a střední koruně
- **Spadaná jablka:** samostatný uzel `jablon_N_spadana`, 14–22 kusů, část nahnědlá a nahnilá. Ve hře je můžeš skrýt nebo z nich udělat sbíratelné předměty.

## Pro Godot (stejné jako ostatní stromy, viz POZNAMKY_GODOT.txt)
- Materiály:
  - `game_jablon_N_listi` – alpha scissor, oboustranný, doporučeno zapnout Back Lighting
  - `game_jablon_N_kura` a `game_jablon_N_kura_mlada`
  - `game_jablon_N_rez`
  - `game_jablon_N_jablka`
- Světlo koruny je v barvě vrcholů (COLOR_0): vnější a horní část je světlejší, nitro tmavší. Nech zapnuté „Vertex Color → Use as Albedo“.
- Pivot je u paty kmene. Kořenové náběhy jdou 25 cm pod zem, tak strom zapusť na terén (y = 0).
- Kolize: jen kmen, válec o poloměru asi 0,3 m a výšce 1,8 m. Koruna je nad hlavou hráče, její spodní okraj je ve výšce 1,25–2,1 m.
- Do sadu dej stromy asi 8–10 m od sebe, každý natočený jinak a se škálou 0,85–1,15. Sady se ve 14. století sázely volně, ne v pravidelných řadách.

## Soubory
- `out/jablon_1..3.glb`, `out/jablon_1..3_daleko.glb`
- `jablon_geo.py` – generátor (`python3 jablon_geo.py 1|2|3`)
- `atlas_jablon.py` – atlas listí; `far.py` – vzdálená verze (`python3 far.py jablon_N`)
- `atlas/` a `out/` – textury
- `foto/` není v zipu: zdrojové skeny z Poly Haven si generátor stahuje sám.

## Historie
- Jabloně se v Čechách pěstovaly ve vrcholném středověku hlavně v klášterních, panských a farních zahradách. Na selských dvorech byly vysokokmeny v trávě, pod nimi se páslo a kosilo.
- Staré odrůdy měly menší plody, 5–8 cm, často s červeným líčkem nebo žíháním. Velké lesklé jablko dnešního typu by sem nepatřilo.
