# Lovec (Hvozd) – postava s pořádným úchopem nástrojů

Postava pro survival hru Hvozd (web, three.js). Je tady i pro Havrana: stejná kostra jako
`animace_ual/` (Quaternius Universal Animation Library), takže animace z UAL na ni sedí bez retargetu.

## Soubory

| soubor | co to je |
|---|---|
| `lovec.glb` | postava se skinem (kostra UE/Quaternius, 65 kostí včetně prstů), oblečená: košile s dlouhým rukávem, manšestrové kalhoty, kožené boty; textury 2K JPEG |
| `lovec_animace_three.json` | sada animací pro web (formát `THREE.AnimationClip.toJSON`), názvy odpovídají kódu hry – viz tabulka níže |
| `../../../nastroje/hvozd_lovec/oblect_postavu.py` | Blender 4.2 skript, který postavu oblékne (rovné řezy rovinami v pase, u krku, na zápěstích a kotnících; látky Poly Haven) |
| `../../../nastroje/hvozd_lovec/animace_prevod.html` | stránka, která sestaví sadu animací: klipy UAL přímo, luk převedený ze staré postavy podle směrů kostí |
| `../../../nastroje/hvozd_lovec/uchop_nastroje.js` | výňatek: usazení nástroje do pěsti |

## Zdroje a licence (vše CC0)
- Tělo: Quaternius **Universal Base Characters [Standard]** – `Superhero_Male_FullBody` (CC0).
- Animace: Quaternius **Universal Animation Library 1 + 2 [Standard]** (CC0).
- Látky: Poly Haven `knitted_fleece` (košile), `ribbed_corduroy` (kalhoty), `brown_leather` (boty) – CC0.
- Animace luku: vlastní (z `animace.glb`), převedené na tuto kostru.

## Animace (název ve hře ← zdroj)
stani ← Idle_Loop · chuze ← Walk_Loop · beh ← Jog_Fwd_Loop · skrceni ← Crouch_Idle_Loop · skrceni_chuze ← Crouch_Fwd_Loop ·
zvednout_ze_zeme ← Farm_Harvest · louc_stani ← Idle_Torch_Loop (louč v levé ruce) · jidlo_piti ← Consume · smrt ← Death01 ·
zasah ← Hit_Chest · **kaceni ← TreeChopping_Loop** · mec_stani ← Sword_Idle · mec_utok ← Sword_Attack · hod ← OverhandThrow ·
zvednout_stul ← PickUp_Table · klecet ← Fixing_Kneeling · luk_napnout / luk_mirit / luk_vystrel ← vlastní (převod).

## Jak se dělá úchop (rešerše a postup)
Hry to dělají takhle (Unreal sockety, Lyra „anim layers“ pro každou zbraň, GDC přednášky o FP animaci):
1. **Prsty sevře animace**, ne kód. Pěst je autorská póza animátora (u nás z UAL – `TreeChopping_Loop`, `Idle_Torch_Loop`).
   Procedurální ohýbání prstů jsme zkoušeli a vypadalo špatně – to byla slepá ulička.
2. **Nástroj sedí v „socketu“ v pěsti**: střed = mezi linií kloubů (index_01–pinky_01) a prostředními články prstů (middle_02, ring_02);
   osa topůrka = od malíčku k ukazováčku, mírně šikmo k zápěstí; ostří ve směru kloubů. Viz `uchop_nastroje.js`.
3. **Klidová póza = zmrazený snímek animace sekání** (TreeChopping v 0,45 s – pěst před hrudí); seknutí přehraje nápřah (0,6 s → konec)
   a úder (0 → 0,45 s). Při švihu se tělo vůči kameře nepřesouvá, aby byl vidět skutečný pohyb ruky.
4. Měřené úhly prstů při úchopu válce ~35 mm (pro případ, že by animace chyběla): kořenový kloub ~55°, prostřední ~75°, koncový ~45°,
   prsteník a malíček o 5–10° víc (Shimawaki 2019, PMC6339738).

## Převod animací luku na novou kostru
Klidové pózy obou koster se liší (A-póza vs. jiné osy kostí), takže kopírování rotací nejde. Převod: pro každý snímek se
v pořadí od kořene natočí každá kost tak, aby její směr (kost → dítě) ve světě odpovídal staré postavě; u ruky se navíc
srovná příčná osa kloubů (ukazováček − malíček). Postava se předtím otočí podle směru špiček nohou.

## Pro Godot
`lovec.glb` jde rovnou do Godotu 4 (kostra stejná jako `animace_ual/UAL*_Standard.glb`). Animace pro Godot ber přímo z UAL glb,
JSON je jen pro web.
