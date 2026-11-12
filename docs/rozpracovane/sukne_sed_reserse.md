# Rešerše: dlouhá sukně při sezení a chůzi (12. 11. 2026)

Cíl: přední část sukně při sedu leží na stehnech a od kolen padá podél holení, místo „zvonu/ubrusu“.
Hledáno: dokumentace CRYENGINE, Warhorse (GDC), KawaiiPhysics (UE), Godot, fóra riggerů (Polycount, DAZ, 80.lv).

## 1. CRYENGINE / KCD

- **PRow = „pendula row“**: řada kyvadel se stejnými parametry; kloub musí mít jméno s tagem a čítači `skirt_x00_y01`
  (x = pozice po obvodu, y = řada shora). Osa X rodiče musí mířit na potomka. Pro sukni zaškrtnout **Cycle** (poslední
  kyvadlo v řadě spojené s prvním). Vodorovné vazby: **Stretch** (0,2 = ±20 % vzdálenosti z výchozí pózy),
  **Relaxation Loops** doporučeno 2–4. Svisle se sukně nenatahuje (délka = vzdálenost kloubů).
  [CRYENGINE – Attachment System Tutorial, „Simulating a Grid of Linked Joints“](https://www.cryengine.com/docs/static/engines/cryengine-5/categories/23756816/pages/29450433)
- Parametry řady: Simulation FPS (doporučeno 30–60), Mass, Gravity 9,81, Damping, **Joint Spring 0–999** (tah k
  **Spring Target** – ose vůči kloubu), **Cone Angle** výchozí 45° (0–179), Rod Length, Max Velocity (proti
  „výbuchu“ při teleportu/náhlé změně pózy). Tamtéž.
- **Kolize**: „růžové“ proxy = *lozenge* na kloubech těla (4 čísla → koule, kapsle, krabice…), „modré“ = kapsle/koule
  na kloubech sukně; růžové vždy odtlačí modré. **Projection Type**: shortvec translation, shortarc rotation,
  directed rotation (jen jedním směrem – podle roviny závěsu), translational projection. Rotace funguje **jen když
  čep kapsle leží mimo lozenge**, jinak hlášení „Capsule … starts inside of proxy“ a kolize se nevyřeší. Tamtéž.
- Číselný trik pro řetězy: kapsle o ~25 % delší než kost (překryv s potomkem) a **poloměr potomka o ~2 mm menší**,
  aby čep potomka byl po odsunutí rodiče také venku. Tamtéž.
- Pořadí: nejprve projekce z lozenge, pak ořez do kužele – **kužel má poslední slovo**; malý kužel může kapsli
  zamknout ve stehně. Tamtéž.
- Příklad kyvadla u nohy: kužel → kliping; *half-cone* plochou stranou k tělu → bez klipingu; nejlépe **kapsle na
  stehně** + kužel. Tamtéž (Pendulum_Simulation_01–04.cdf).
- CRYENGINE sám radí: sukně často **stačí skinovat**, simulovat jen konce (PRow / kyvadlo na kloubu).
  [CRYENGINE – VCloth 2.0](https://www.cryengine.com/docs/static/engines/cryengine-5/categories/23756816/pages/29799532)
- Kosti sukně se přidávají jako rozšíření kostry; stačí jeden společný kloub (obvykle pánev).
  [Attachment System Tutorial](https://www.cryengine.com/docs/static/engines/cryengine-5/categories/23756816/pages/29450433)
- Warhorse: GDC Europe 2015 „Adaptive Clothing System in KCD“ (Tomáš Barák) – procedurální přizpůsobení **vrstev**
  oblečení, aby se nepřekrývaly; o sezení nic. [GDC Vault](https://gdcvault.com/play/1022822/Adaptive-Clothing-System-in-Kingdom)
- **NEOVĚŘENO**: jména kostí sukní v KCD1/2, počet řad, zda KCD používá PRow, a zda sedící ženy mají speciální
  animace kostí sukně. Wiki/Nexus/fórum nic nedaly; zdroj by byl rozbalení `.chr/.cdf` z PAK nebo KCD2 Modding Tools
  (CryEngine Sandbox). [Nexus – KCD2 modding](https://www.nexusmods.com/kingdomcomedeliverance2/articles/79),
  [fórum KCD – CDF lze otevřít v Notepadu](https://forum.kingdomcomerpg.com/t/what-we-know-about-modding-so-far/38589?page=3)

## 2. Běžné postupy v oboru

- **Kapsle na stehně + kapsle koleno–lýtko** na každé noze, poloměr kolizí sukně se ke spodnímu lemu zmenšuje
  (křivka poloměru 1,0 v pase → 0,5 u lemu; tuhost 1,0 → 0,3). Hodnoty: Damping 0,2–0,3, Stiffness 0,1–0,2,
  Limit Angle 45–90°, vazby mezi sousedními řetězy (BoneConstraint). **Sync Bone**: kosti sukně posouvá kost stehna
  (sukně se zvedá s nohou při chůzi). [KawaiiPhysics – Tutorial Skirt](https://github.com/pafuhana1213/KawaiiPhysics/wiki/Tutorial-Skirt-en)
- Kolize kapslemi na nohou sukni nezakryjí vždy – zvětšení horní části kapsle udělá „schod“.
  [DAZ fórum](https://www.daz3d.com/forums/discussion/comment/7745636)
- UE AnimDynamics: jen rovinné a kulové limity (rovina drží kosti mimo tělo/zem); fyzikální kapsle postavy na něj
  nepůsobí. [Epic – AnimDynamics](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-blueprint-animdynamics-in-unreal-engine)
- **Póza řízená nohou (RBF)**: předpózované tvary sukně spouštěné polohou nohy, bez fyziky a kolizí.
  [80.lv – skirt rig v Maye](https://80.lv/articles/tech-artist-unveils-a-touhou-inspired-3d-skirt-rig-made-in-maya)
- **Morf/korektiva pro sed**: nasimulovat sukni v sedu a uložit jako morph target.
  [Renderosity](https://api.renderosity.com/forums/threads/2776142/print)
- Kopírovat kosti nohou do sukně = roztržení středu; doporučují hybrid (noha + vlastní kosti sukně, ručně
  animované v sedu). Hybrid fungoval na židli, ne při sezení na zemi.
  [DAZ](https://forum.daz3d.com/forums/discussion/comment/7083696/), [Polycount](https://polycount.com/discussion/comment/1021590),
  [Polycount](https://polycount.com/discussion/comment/1018663)
- Aim constraint kosti sukně na cíl + „falešná kolize“ bodovou vazbou ke kolenu a uzlem úhlu mezi.
  [blenderartists](https://blenderartists.org/t/skirt-rigging-problem/670900) (NEOVĚŘENO v detailu – jen úryvek z vyhledávání)
- Godot má vestavěný **SpringBoneSimulator3D** s kolizemi `SpringBoneCollisionCapsule3D` (výchozí radius 0,1,
  výška ≥ 2× poloměr, volba *inside*); poloměr po kloubech, stiffness/drag/gravity (gravity = rychlost, ne zrychlení).
  [Godot 4.4 – Capsule](https://docs.godotengine.org/en/4.4/classes/class_springbonecollisioncapsule3d.html),
  [SpringBoneSimulator3D](https://docs.godotengine.org/en/stable/classes/class_springbonesimulator3d.html)

## 3. Recept pro nás (návrh, NEOVĚŘENO měřením)

Odvozeno z výše uvedeného (CRY kapsle+kužel, Kawaii Sync Bone, hybrid z Polycountu); ne převzato hotové.

1. **Proxy těla** (z dat, ne čísla v kódu): kapsle stehno `thigh→calf` poloměr r_s, kapsle holeň `calf→foot` r_h
   (změřit z modelu postavy; zdroje čísla pro člověka nedávají – **NEOVĚŘENO**).
2. **Horní kost řetězu (přední/boční)**: cíl = bod na povrchu stehna: `K = koleno + n·(r_s + tl)` kde n je
   normála od osy stehna směrem k poloze řetězu po obvodu (přední řetěz → „nahoru“ od stehna v sedu). Kost
   natočit *aim* z kořene na K (ne zlomkem rotace stehna). Přední středové řetězy: K = průměr obou kolen (přemostí mezeru).
3. **Střední + dolní kost**: kloub na kolenní hraně; aim od K k `kotník + n·(r_h + tl)` průmětem do svislice, tj.
   lem padá podél holeně / ke zemi, ne vodorovně.
4. **Ořezy**: (a) projekce jako v CRY – pokud kloub sukně leží uvnitř kapsle nohy, posunout na povrch
   (shortvec); (b) výška lemu ≤ výška kolene – jinak otočit kost dolů; (c) zadní řetězy: kužel/half-cone, ať
   nejdou do sedáku (sedák + židle jako rovina).
5. **Chůze**: stejný výpočet, jen se váhou přechodu (blend aim ↔ výchozí póza podle úhlu stehna), volitelně
   lehká pružina (SpringBoneSimulator3D s kapslemi) jen na dolní kosti.
6. Ověření: snímek sedu z boku + test, že všechny klouby sukně jsou ≥ r mimo kapsle nohou.
