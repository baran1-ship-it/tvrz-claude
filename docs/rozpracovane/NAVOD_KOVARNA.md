# Kovárna – Odkaz Havrana (Čechy 1393)

Otevřená vesnická kovárna ve stylu KCD. Obsahuje budovu, kamennou výheň s ohništěm pod klenbou a komín.
Vpravo od výhně je měch na kozách s pákou. **Vybavení v ní není**: kovadlina, nářadí, necky a stůl jsou
z vaší hry. Pro jejich umístění jsou připravené značky.

Měřítko je 1 jednotka = 1 m, osa Y nahoru. **Počátek** je střed kovárny na úrovni terénu. Udusaná podlaha
je ve výšce +0,05 a k přední hraně se svažuje na 0. Otevřená přední strana míří na **+Z** (v Blenderu na −Y).

## Soubory
- `kovarna.glb` – celý díl pro Godot, textury 1024 jsou vložené
- `kovarna_lod1.glb` – LOD1 pro pohled z dálky (116 trojúhelníků)
- `kovarna.blend`, `kovarna.py` (+ `tesar.py`, `_spolecne.py`) – zdroj a generátor (`python kovarna.py --norender`)

## Rozměry
| Co | Kde / kolik |
|---|---|
| Kovárna | 6,0 × 4,8 m (sloupy x −3 … +3, z −2,4 … +2,4), hřeben 5,5 m, sklon střechy 45° |
| Přístřešek na kování koní | na východě (+x) x 3,25 … 6,3, z −0,8 … +2,1, pultová střecha 20°, dlažba z polního kamene v hlíně, uvazovací břevno s kruhy |
| Výheň | x −2,10 … −0,30, z −2,13 … −1,00, plotna 0,88 (0,83 nad podlahou), ohniště 0,62 × 0,54 m, hluboké 12 cm |
| Klenba nad ohništěm | rozpětí 1,2 m, vrchol 1,85; vpředu otevřená, z boku (strana měchu) otvor 0,55 × 0,54 m |
| Komín | za zadní stěnou, x −1,70 … −0,70, vršek 5,65, kamenná deska na čtyřech kamenech |
| Měch | dlouhý 1,5 m, široký až 0,9 m, na kozách; dmyšna vede z boku do ohniště |

## Měch a páka (animace)
- `Kovarna_Paka`: počátek je v čepu. Otáčí se kolem osy `Vector3(0.469, 0, 0.883)`.
- `Kovarna_Mech`: má blend shape **`Nadech`**. Hodnota 0 je stlačený měch (vydechl do ohně), 1 je nadechnutý.
- Kovář stažením rukojeti dolů zvedne horní desku a měch se nadechne. Po puštění závaží na desce měch stlačí a fouká do ohně.
- Rukojeť visí vpravo vpředu od výhně ve výšce 1,8–2,1 m nad podlahou, kovář na ni sahá pravou rukou. Při stažení klesne asi o 0,2 m.

Obojí se animuje jedním parametrem `t` (0 … 1):

```gdscript
const OSA_PAKY := Vector3(0.469, 0.0, 0.883)
const UHEL_PAKY := 0.278   # rad, plné stažení

func nastav_mech(t: float) -> void:
	$Kovarna_Paka.transform.basis = Basis(OSA_PAKY.normalized(), UHEL_PAKY * t)
	$Kovarna_Mech.set("blend_shapes/Nadech", t)

# pumpování: t = 0.5 - 0.5 * cos(cas * 2.5)   (asi 0,4 s na jeden tah)
```

Řetěz mezi pákou a měchem je součástí `Kovarna_Mech` a s blend shape se posouvá.

## Značky pro hru (Godot x, y, z)
| Uzel | Poloha | K čemu |
|---|---|---|
| `Kovarna_Ohen_bod` | (−1,19; 0,95; −1,65) | světlo, částice ohně, zvuk |
| `Kovarna_Paka_uchop` | (−0,45; 1,95; −0,80) | interakce „dmýchat“ |
| `Kovarna_Kovar_stani` | (−1,10; 0,05; −0,50) | kde stojí kovář u ohně |
| `Kovarna_Kovadlina_misto` | (−0,95; 0,05; +0,30) | doporučené místo pro vaši kovadlinu |
| `Kovarna_Komin_kour` | (−1,20; 6,00; −2,96) | kouř z komína |

`Kovarna_Zhar` je žhavé uhlí s vlastním svícením (emission). Při zapálení ho zapněte, při vyhasnutí vypněte.
Pod ním je pořád vyhaslé uhlí a popel, takže ohniště není prázdné. Ve hře na `Kovarna_Ohen_bod` patří
OmniLight3D (oranžové, dosah asi 4 m) a pro plamen částice.

## Vložení do Godotu
1. `kovarna.glb` přetáhni do scény a polož ho na rovný terén. Podlaha je o 5 cm výš než okolí.
2. LOD: `kovarna_lod1.glb` dej na stejné místo. Visibility Range nastav na 0–60 m u hlavního dílu a od 55 m u LOD1.
3. **Kámen (výheň, zeď, komín, podezdívka, dlažba) má saze a prach v barvě vrcholů** (glTF COLOR_0, násobí texturu).
   Godot ji při importu glTF zapíná sám (Vertex Color → Use as Albedo). Pokud by kámen ve hře vypadal čistě
   a světle, zapni to ručně v materiálech `M_ZdivoKamen`, `M_DlazbaPolniKamen` a `M_PlotnaVyhne`.
4. Kolize jsou kvádry s příponou `-convcolonly`, Godot je převede sám. Kryjí výheň, kamennou zeď, komín,
   stěny, parapet, sloupy, měch, podlahu, přístřešek a břevno. Páka kolizi nemá, visí nad hlavou.

## Konstrukce (co je na ní řemeslného)
- **Rám:**
  - Prahy jsou na kamenné podezdívce a v rozích přeplátované s přesahem.
  - Volné sloupy (přední rohy a přístřešek) jsou zapuštěné do země, jak se na vsi běžně stavělo. Zbytek stojí na prazích na podezdívce.
  - Sloupy, pozednice, pásky a vazné trámy jsou otesané. Trámy jsou prohnuté a místy mají zbytky kůry (oblinu). Spoje drží dřevěné kolíky.
  - Přední pozednice nese 6 m bez sloupu uprostřed. Podepírají ji pásky a je stažená železnými pásy s nýty.
- **Stěny:**
  - Svislá prkna, některá s kůrou na hraně (krajinky), jsou nestejně široká a lehce křivá.
  - Spáry kryjí lišty na kolících, ale některé lišty chybí.
  - Okénko na západě má dřevěnou mříž a otevřenou okenici na kovaných závěsech.
- **Krov:**
  - Krokve jsou z křivých odkorněných kuláčů se zbytky kůry, hambalky jsou na kolících.
  - Na latích leží šindel. Na severní straně je víc mechu, kolem komína je šindel začouzený.
  - Ve štítech jsou průduchy pro kouř.
- **Výheň:**
  - Kámen je fotosken skutečné lomové zdi (Poly Haven „Broken Wall“, CC0). Reliéf kamenů a spár je podle jeho výškové
    mapy vytvarovaný přímo v geometrii, takže kámen v síti sedí přesně na kámen na fotce. Stejně jsou
    udělané zeď, komín a podezdívka, dlažba přístřešku je sken polního kamene v hlíně.
  - Saze jsou v barvě vrcholů: v klenbě černé, ve spárách tmavší, nad obloukem a z bočního otvoru chochol, dole prach.
  - Kouř odchází klenbou do kamenného komína za zadní zdí.
- **Saze uvnitř:** dřevo kolem výhně je černé a dál od ní šedé od prachu a sazí.

## Výkon
- Celý díl má ≈ 65 600 trojúhelníků:
  - zeď, komín, podezdívka a výheň ≈ 26 000
  - dlažba 4 000
  - šindel 13 400
  - konstrukce 17 700
  - měch, páka, uhlí a podlaha 4 200
- LOD1 má 116 trojúhelníků.
- Na tabletu doporučuji Visibility Range a stín od světla ohně jen v blízkosti.

## Historie a co je volnější
- **Výheň ve výšce stolu, měch na páce a dmyšna z boku** odpovídají vyobrazením kováren
  z 15. století, například v Mendelově domovní knize (od roku 1425). Měch ovládaný vahadlem s pákou
  v dosahu kováře u ohně je na dobových dřevořezech běžný.
- **Kamenný komín** je volnost ve stylu KCD. Na vsi kolem roku 1400 odcházel kouř spíš střechou
  a kamenné komíny se v Čechách na vesnici šířily až později. U kovárny, která kvůli ohni stávala
  stranou od ostatních stavení, je ale kamenná požární zeď věrohodná.
- Šindel místo došků je pro kovárnu rozumný kvůli jiskrám.
